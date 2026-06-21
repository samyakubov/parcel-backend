import json

import pandas as pd
from langchain_core.tools import tool

from database_connector import DatabaseConnector
from handlers.property_search.helper_functions.get_complaints import get_complaints
from handlers.property_search.helper_functions.get_job_filings import get_job_filings
from handlers.property_search.helper_functions.get_last_sold import get_last_sold
from handlers.property_search.helper_functions.get_mortgage import get_mortgage
from handlers.property_search.helper_functions.get_owners import get_owners
from handlers.property_search.helper_functions.get_zoning import get_zoning
from handlers.property_search.helper_functions.standardize_address_for_database import standardize_address
from handlers.property_search.search_by_property_bbl import search_by_property_bbl
from schemas import COOP_PROPERTY_TYPES, LastSold, Violation
from services.ai.summarizer import create_summary_from_property_data


def _resolve_bbl(identifier: str, db: DatabaseConnector) -> tuple[str, pd.Series] | tuple[None, None]:
    """Return (bbl, row) from a BBL string or address string, or (None, None) if not found."""
    identifier = identifier.strip()
    cols = "bbl, prop_streetnumber, prop_streetname, prop_type"

    if identifier.isdigit() and len(identifier) == 10:
        df = db.execute_df(f"SELECT {cols} FROM aggregated_acris_records WHERE bbl = ? LIMIT 1", [identifier])
        if not df.empty:
            return identifier, df.iloc[0]
        return None, None

    std = standardize_address(identifier)
    df = db.execute_df(
        f"SELECT {cols} FROM aggregated_acris_records WHERE search_prop_address = ? LIMIT 1",
        [std],
    )
    if not df.empty:
        return df.iloc[0]["bbl"], df.iloc[0]

    # Lenient fallback: house number + street LIKE
    parts = std.strip().split(" ", 1)
    if len(parts) == 2:
        house_number, street = parts
        q = (
            f"SELECT {cols} FROM aggregated_acris_records"
            " WHERE prop_streetnumber = ? AND prop_streetname LIKE ? LIMIT 1"
        )
        df = db.execute_df(q, [house_number, f"{street.replace(' ', '%')}%"])
        if not df.empty:
            return df.iloc[0]["bbl"], df.iloc[0]

    return None, None


def get_tools(db: DatabaseConnector) -> tuple[list, dict]:
    """
    Returns (tools, captured) where captured is a dict that get_full_property_card
    writes property_data into as a side channel, keeping it out of LLM context.
    """
    _captured: dict = {}

    @tool
    def resolve_property(identifier: str) -> str:
        """
        Resolve a property address or BBL to its canonical BBL.
        Always call this first before any other property tool.
        Accepts a street address (e.g. '217 STEWART ROAD') or a 10-digit BBL string.
        Returns bbl, address, and prop_type.
        """
        try:
            bbl, row = _resolve_bbl(identifier, db)
            if bbl is None:
                return f"Property not found for: {identifier}"
            return json.dumps(
                {
                    "bbl": bbl,
                    "address": f"{row['prop_streetnumber']} {row['prop_streetname']}",
                    "prop_type": str(row.get("prop_type") or "unknown"),
                }
            )
        except Exception as e:
            return f"Error resolving property: {e}"

    @tool
    def get_property_owners(bbl: str) -> str:
        """
        Get current and previous owners for a property by BBL.
        Call resolve_property first to obtain the BBL.
        """
        try:
            acris_df = db.execute_df("SELECT * FROM aggregated_acris_records WHERE bbl = ? ORDER BY documentid", [bbl])
            if acris_df.empty:
                return f"No records found for BBL {bbl}."
            jobs_df = db.execute_df('SELECT ownername, "OwnersPhone" FROM dobjobs WHERE bbl = ?', [bbl])
            result, _ = get_owners(bbl, acris_df, jobs_df)
            return json.dumps({"current_owners": result.current_owners, "previous_owners": result.previous_owners})
        except Exception as e:
            return f"Error getting owners for BBL {bbl}: {e}"

    @tool
    def get_property_last_sold(bbl: str) -> str:
        """
        Get last sold price, date, year built, and square footage for a property by BBL.
        Call resolve_property first to obtain the BBL.
        """
        try:
            acris_df = db.execute_df(
                "SELECT a.doc_type, a.amount, a.partytype_desc, a.party_name, a.record_filed, a.prop_type,"
                " p.year_built, p.lot_area, p.bldg_area"
                " FROM aggregated_acris_records a"
                " LEFT JOIN pluto_latest p ON a.bbl = p.bbl WHERE a.bbl = ? ORDER BY a.documentid",
                [bbl],
            )
            if acris_df.empty:
                return f"No records found for BBL {bbl}."

            prop_type = str(acris_df.iloc[0].get("prop_type") or "")
            if prop_type in COOP_PROPERTY_TYPES:
                return "Last sold data is not tracked for co-op properties."

            sales_df = db.execute_df("SELECT * FROM aggregated_dof_sales WHERE bbl = ?", [bbl])
            result = get_last_sold(bbl, sales_df, acris_df)
            if result is None:
                return f"No sale data found for BBL {bbl}."
            return json.dumps(result.model_dump())
        except Exception as e:
            return f"Error getting last sold for BBL {bbl}: {e}"

    @tool
    def get_property_violations(bbl: str) -> str:
        """
        Get ECB/building violations for a property by BBL.
        Call resolve_property first to obtain the BBL.
        """
        try:
            df = db.execute_df(
                """SELECT bbl, violation_status, issue_date, violation_type, description, severity,
                          penalty_amount, amount_paid, balance_due, respondent_name, house_number, street, city, zip
                   FROM aggregated_acris_violations WHERE bbl = ?""",
                [bbl],
            )
            if df.empty:
                return f"No violations found for BBL {bbl}."

            violations = [Violation(**row) for row in df.to_dict(orient="records")]
            open_count = sum(1 for v in violations if v.violation_status and "open" in v.violation_status.lower())
            return json.dumps(
                {
                    "total": len(violations),
                    "open": open_count,
                    "closed": len(violations) - open_count,
                    "violations": [v.model_dump() for v in violations[:10]],
                }
            )
        except Exception as e:
            return f"Error getting violations for BBL {bbl}: {e}"

    @tool
    def get_property_complaints(bbl: str) -> str:
        """
        Get DOB complaints for a property by BBL.
        Call resolve_property first to obtain the BBL.
        """
        try:
            row_df = db.execute_df(
                "SELECT prop_streetnumber, prop_streetname FROM aggregated_acris_records WHERE bbl = ? LIMIT 1", [bbl]
            )
            if row_df.empty:
                return f"No records found for BBL {bbl}."

            row = row_df.iloc[0]
            address = f"{row['prop_streetnumber']} {row['prop_streetname']}"
            std = standardize_address(address)
            parts = std.split(" ", 1)
            house_num = parts[0]
            street_name = parts[1] if len(parts) > 1 else ""

            complaints_df = db.execute_df(
                "SELECT * FROM dob_complaints WHERE housenumber = ? AND housestreet = ?",
                [house_num, street_name],
            )
            complaints = get_complaints(address, complaints_df)
            return json.dumps({"total": len(complaints), "complaints": complaints[:10]})
        except Exception as e:
            return f"Error getting complaints for BBL {bbl}: {e}"

    @tool
    def get_property_job_filings(bbl: str) -> str:
        """
        Get DOB job filings (building permits) for a property by BBL.
        Call resolve_property first to obtain the BBL.
        """
        try:
            jobs_df = db.execute_df("SELECT * FROM dobjobs WHERE bbl = ?", [bbl])
            filings = get_job_filings(bbl, jobs_df)
            if not filings:
                return f"No job filings found for BBL {bbl}."
            return json.dumps({"total": len(filings), "job_filings": filings[:10]})
        except Exception as e:
            return f"Error getting job filings for BBL {bbl}: {e}"

    @tool
    def get_property_zoning(bbl: str) -> str:
        """
        Get zoning districts and overlays for a property by BBL.
        Call resolve_property first to obtain the BBL.
        """
        try:
            zoning_df = db.execute_df("SELECT * FROM zoning WHERE bbl = ?", [bbl])
            result = get_zoning(bbl, zoning_df)
            if result is None:
                return f"No zoning information found for BBL {bbl}."
            return json.dumps(result.model_dump())
        except Exception as e:
            return f"Error getting zoning for BBL {bbl}: {e}"

    @tool
    def get_property_mortgage(bbl: str) -> str:
        """
        Get the most recent mortgage lender, borrower, and amount for a property by BBL.
        Call resolve_property first to obtain the BBL.
        """
        try:
            acris_df = db.execute_df(
                "SELECT doc_type, documentid, record_filed, partytype_desc, party_name, amount"
                " FROM aggregated_acris_records WHERE bbl = ? ORDER BY documentid",
                [bbl],
            )
            if acris_df.empty:
                return f"No records found for BBL {bbl}."

            # Pass the last sale date so get_mortgage biases toward mortgages near the sale
            last_sold_hint = None
            sales_df = db.execute_df(
                "SELECT sale_date FROM aggregated_dof_sales WHERE bbl = ? ORDER BY sale_date DESC LIMIT 1", [bbl]
            )
            if not sales_df.empty and sales_df.iloc[0]["sale_date"] is not None:
                last_sold_hint = LastSold(last_sold_price=0, last_sold_date=sales_df.iloc[0]["sale_date"])

            result = get_mortgage(acris_df, last_sold_hint)
            if result is None:
                return f"No mortgage records found for BBL {bbl}."
            return json.dumps(result.model_dump())
        except Exception as e:
            return f"Error getting mortgage for BBL {bbl}: {e}"

    @tool
    def get_full_property_card(bbl: str) -> str:
        """
        Fetch a complete property overview for a BBL: owners, sales, violations, complaints,
        job filings, zoning, and mortgage. Use this when the user wants a comprehensive
        property summary or to display the full property card in the UI.
        Do NOT use this for specific single-topic questions — use the targeted tools instead.
        """
        try:
            result = search_by_property_bbl(bbl, db)
            _captured["property_data"] = result
            return str(create_summary_from_property_data(result))
        except Exception as e:
            return f"Error fetching full property data for BBL {bbl}: {e}"

    return [
        resolve_property,
        get_property_owners,
        get_property_last_sold,
        get_property_violations,
        get_property_complaints,
        get_property_job_filings,
        get_property_zoning,
        get_property_mortgage,
        get_full_property_card,
    ], _captured
