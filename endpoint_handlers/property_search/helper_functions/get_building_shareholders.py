from database_connector import db
from logger_config import logger


def get_building_shareholders(bbl: str):
    if not bbl:
        logger.error("BBL is required to get building shareholders, but none was provided.")
        return []
    try:
        logger.info(f"--------------------Fetching building shareholders for BBL: {bbl}--------------------")
        all_transactions = db.execute_df("""
                                        SELECT party_name as current_owner,
                                        CASE WHEN partytype_desc = 'GRANTEE/BUYER' THEN 'BUY' ELSE 'SELL' END AS buy_or_sell, record_filed AS transaction_date
                                         FROM aggregated_acris_records
                                         WHERE bbl = ? 
                                           AND doc_type = 'BOTH RPTT AND RETT' 
                                           AND amount > 0 
                                           AND partytype_desc IN ('GRANTEE/BUYER', 'GRANTOR/SELLER')
                                         """, [bbl])

        if all_transactions.empty:
            logger.warning(f"--------------------No shareholder transactions found for BBL: {bbl}--------------------\n")
            return []

        logger.info(f"Found {len(all_transactions)} shareholder transactions for BBL: {bbl}. Analyzing ownership status.")
        latest_per_party = all_transactions.groupby(['current_owner', 'buy_or_sell'], as_index=False).transaction_date.max()
        buy = latest_per_party[latest_per_party['buy_or_sell'] == 'BUY']
        sell = latest_per_party[latest_per_party['buy_or_sell'] == 'SELL']

        merged = buy.merge(sell, on='current_owner', how='left', suffixes=('_buy', '_sell'))
        current_shareholders = merged[
            (merged['transaction_date_sell'].isnull()) |
            (merged['transaction_date_buy'] > merged['transaction_date_sell'])
        ]


        if current_shareholders.empty:
            logger.warning(f"--------------------Could not determine current shareholders for BBL: {bbl} from transaction analysis--------------------\n")
            return []

        shareholder_list = current_shareholders['current_owner'].tolist()
        logger.info(f"--------------------Successfully identified {len(shareholder_list)} current shareholders for BBL: {bbl}--------------------\n")
        return shareholder_list
    except Exception as e:
        logger.error(f"An unexpected error occurred while retrieving building shareholders for BBL {bbl}: {e}", exc_info=True)
        return []
