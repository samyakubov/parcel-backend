import pandas as pd
from logger_config import logger


def get_building_shareholders(bbl: str, acris_df: pd.DataFrame) -> list[str]:
    """Gets the current shareholders of a building.

    This function analyzes the transaction history of a building to determine the current shareholders.
    It does this by looking at the latest buy and sell transactions for each party.

    Args:
        bbl (str): The BBL of the building.
        acris_df (pd.DataFrame): DataFrame containing aggregated ACRIS records for the BBL.

    Returns:
        List[str]: A list of the current shareholders. Returns an empty list if no shareholders are found
            or if an error occurs.
    """
    if not bbl:
        logger.error("BBL is required to get building shareholders, but none was provided.")
        return []
    
    if acris_df.empty:
         logger.warning(
            f"--------------------No shareholder transactions found for BBL: {bbl}--------------------\n"
        )
         return []

    try:
        logger.info(f"--------------------Analyzing building shareholders for BBL: {bbl}--------------------")
        
        # Filter for relevant transactions
        mask = (
            (acris_df["doc_type"] == 'BOTH RPTT AND RETT') & 
            (acris_df["amount"] > 0) & 
            (acris_df["partytype_desc"].isin(['GRANTEE/BUYER', 'GRANTOR/SELLER']))
        )
        transactions = acris_df[mask].copy()

        if transactions.empty:
            logger.warning(
                f"--------------------No shareholder transactions found for BBL: {bbl}--------------------\n"
            )
            return []

        # Prepare for analysis
        transactions["current_owner"] = transactions["party_name"]
        transactions["buy_or_sell"] = transactions["partytype_desc"].apply(
            lambda x: 'BUY' if x == 'GRANTEE/BUYER' else 'SELL'
        )
        transactions["transaction_date"] = transactions["record_filed"]

        logger.info(
            f"Found {len(transactions)} shareholder transactions for BBL: {bbl}. Analyzing ownership status."
        )
        
        latest_per_party = transactions.groupby(
            ["current_owner", "buy_or_sell"], as_index=False
        ).transaction_date.max()
        
        buy = latest_per_party[latest_per_party["buy_or_sell"] == "BUY"]
        sell = latest_per_party[latest_per_party["buy_or_sell"] == "SELL"]

        merged = buy.merge(sell, on="current_owner", how="left", suffixes=("_buy", "_sell"))
        current_shareholders = merged[
            (merged["transaction_date_sell"].isnull())
            | (merged["transaction_date_buy"] > merged["transaction_date_sell"])
        ]

        if current_shareholders.empty:
            logger.warning(
                f"--------------------Could not determine current shareholders for BBL: {bbl} from transaction analysis--------------------\n"
            )
            return []

        shareholder_list = current_shareholders["current_owner"].tolist()
        logger.info(
            f"--------------------Successfully identified {len(shareholder_list)} current shareholders for BBL: {bbl}--------------------\n"
        )
        return shareholder_list
    except Exception as e:
        logger.error(
            f"An unexpected error occurred while retrieving building shareholders for BBL {bbl}: {e}", exc_info=True
        )
        return []
