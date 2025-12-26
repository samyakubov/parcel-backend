from datetime import datetime
from database_connector import DatabaseConnector
from pydantic_models import MortgageRecord, LastSold


def get_mortgage(
    bbl: str,
    db: DatabaseConnector,
    last_sold_for: LastSold | None = None,
) -> MortgageRecord | None:
    """
    Extract mortgage lender and borrower details from property records.

    Args:
        bbl: The property's Borough-Block-Lot identifier
        db: DatabaseConnector instance
        last_sold_for: LastSold object containing sale information, or None

    Returns:
        MortgageRecord object with 'lender' and 'borrower' fields, or None if not found
    """
    # Query mortgage records for the given BBL
    query = """
            SELECT
                documentid,
                bbl,
                amount,
                partytype_desc,
                party_name,
                doc_type,
                record_filed
            FROM aggregated_acris_records
            WHERE bbl = ?
              AND doc_type = 'MORTGAGE'
            ORDER BY record_filed DESC
            """

    df = db.execute_df(query, [bbl])

    if df.empty:
        return None

    # Convert DataFrame to list of dictionaries
    mortgage_records = df.to_dict("records")

    # Group records by documentid
    grouped_records = {}
    for record in mortgage_records:
        doc_id = record["documentid"]
        if doc_id not in grouped_records:
            grouped_records[doc_id] = []
        grouped_records[doc_id].append(record)

    # Sort documents
    # Default: Sort by record_filed DESC (already somewhat sorted, but ensure per-doc max date)
    sorted_doc_ids = sorted(
        grouped_records.keys(),
        key=lambda d_id: max(
            r["record_filed"] for r in grouped_records[d_id]
        ),
        reverse=True,
    )

    # If last_sold_for is provided, prioritize mortgages close to sale date
    if last_sold_for is not None and last_sold_for.last_sold_date:
        try:
           # Handle last_sold_date whether it's a string or datetime (Pydantic model might have converted it)
            sale_date_str = last_sold_for.last_sold_date
            # Simple check if it's already a datetime object (unlikely given the model but safe)
            if isinstance(sale_date_str, datetime):
                sale_date = sale_date_str
            else:
                 # Standardize date parsing - assuming ISO format or simple YYYY-MM-DD from the model
                sale_date = datetime.fromisoformat(str(sale_date_str).replace("Z", "+00:00"))
            
            near_sale_docs = []
            other_docs = []
            
            for doc_id in sorted_doc_ids:
                 # Get the filing date of the document (use the first record's date)
                doc_date_str = grouped_records[doc_id][0]["record_filed"]
                if isinstance(doc_date_str, datetime):
                     doc_date = doc_date_str
                else:
                    doc_date = datetime.fromisoformat(str(doc_date_str).replace("Z", "+00:00"))

                # Check proximity (e.g., within 30 days) - broadened from 7 days as mortgages might file slightly apart
                diff_days = abs((doc_date - sale_date).total_seconds()) / (60 * 60 * 24)
                
                if diff_days <= 14: # Increased window slightly to be safe
                    near_sale_docs.append(doc_id)
                else:
                    other_docs.append(doc_id)
            
            # Re-order: near sale docs first, then others
            sorted_doc_ids = near_sale_docs + other_docs
            
        except (ValueError, TypeError):
             # Fallback to default sort if date parsing fails
             pass

    # improving selection logic
    selected_mortgage = None
    
    for doc_id in sorted_doc_ids:
        parties = grouped_records[doc_id]
        
        lenders = [p["party_name"] for p in parties if p.get("partytype_desc") == "MORTGAGEE/LENDER"]
        borrowers = [p["party_name"] for p in parties if p.get("partytype_desc") == "MORTGAGOR/BORROWER"]
        
        if lenders and borrowers:
            # Found a valid mortgage document with both parties
            # Join multiple parties with " & " if simpler, or just take the first one
            lender_name = " & ".join(sorted(list(set(lenders)))) # basic dedup
            borrower_name = " & ".join(sorted(list(set(borrowers))))
            
            # Extract amount (assuming all records in the document share the same amount)
            amount_val = parties[0].get("amount", 0.0)
            try:
                amount = float(amount_val)
            except (ValueError, TypeError):
                amount = 0.0

            selected_mortgage = MortgageRecord(lender=lender_name, borrower=borrower_name, amount=amount)
            break
            
    return selected_mortgage