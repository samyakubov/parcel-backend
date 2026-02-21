from datetime import datetime
import pandas as pd

from schemas import LastSold, MortgageRecord


def get_mortgage(
    acris_df: pd.DataFrame,
    last_sold_for: LastSold | None = None,
) -> MortgageRecord | None:
    """
    Extract mortgage lender and borrower details from property records.

    Args:
        acris_df: DataFrame containing aggregated ACRIS records.
        last_sold_for: LastSold object containing sale information, or None

    Returns:
        MortgageRecord object with 'lender' and 'borrower' fields, or None if not found
    """
    if acris_df.empty:
        return None

    mask = (acris_df["doc_type"] == 'MORTGAGE')
    df = acris_df[mask].copy()
    
    if df.empty:
        return None
        
    df = df.sort_values(by="record_filed", ascending=False)

    mortgage_records = df.to_dict("records")

    grouped_records = {}
    for record in mortgage_records:
        doc_id = record["documentid"]
        if doc_id not in grouped_records:
            grouped_records[doc_id] = []
        grouped_records[doc_id].append(record)

    sorted_doc_ids = sorted(
        grouped_records.keys(),
        key=lambda d_id: max(
            r["record_filed"] for r in grouped_records[d_id]
        ),
        reverse=True,
    )

    if last_sold_for is not None and last_sold_for.last_sold_date:
        try:
            sale_date_str = last_sold_for.last_sold_date
            if isinstance(sale_date_str, datetime):
                sale_date = sale_date_str
            else:
                sale_date = datetime.fromisoformat(str(sale_date_str).replace("Z", "+00:00"))

            near_sale_docs = []
            other_docs = []

            for doc_id in sorted_doc_ids:
                doc_date_str = grouped_records[doc_id][0]["record_filed"]
                if isinstance(doc_date_str, datetime):
                     doc_date = doc_date_str
                else:
                    doc_date = datetime.fromisoformat(str(doc_date_str).replace("Z", "+00:00"))

                diff_days = abs((doc_date - sale_date).total_seconds()) / (60 * 60 * 24)

                if diff_days <= 14:
                    near_sale_docs.append(doc_id)
                else:
                    other_docs.append(doc_id)

            sorted_doc_ids = near_sale_docs + other_docs

        except (ValueError, TypeError):
             pass

    selected_mortgage = None

    for doc_id in sorted_doc_ids:
        parties = grouped_records[doc_id]

        lenders = [p["party_name"] for p in parties if p.get("partytype_desc") == "MORTGAGEE/LENDER"]
        borrowers = [p["party_name"] for p in parties if p.get("partytype_desc") == "MORTGAGOR/BORROWER"]

        if lenders and borrowers:

            lender_name = " & ".join(sorted(list(set(lenders))))
            borrower_name = " & ".join(sorted(list(set(borrowers))))

            amount_val = parties[0].get("amount", 0.0)
            try:
                amount = float(amount_val)
            except (ValueError, TypeError):
                amount = 0.0

            selected_mortgage = MortgageRecord(lender=lender_name, borrower=borrower_name, amount=amount)
            break

    return selected_mortgage
