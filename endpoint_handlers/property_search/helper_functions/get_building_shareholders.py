from database_connector import db
from logger_config import logger


def get_building_shareholders(bbl: str):
    try:
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
            logger.warning(f"No transactions found for BBL: {bbl}")
            return []

        latest_per_party = all_transactions.groupby(['current_owner', 'buy_or_sell'], as_index=False).transaction_date.max()
        buy = latest_per_party[latest_per_party['buy_or_sell'] == 'BUY']
        sell = latest_per_party[latest_per_party['buy_or_sell'] == 'SELL']

        merged = buy.merge(sell, on='current_owner', how='left', suffixes=('_buy', '_sell'))
        current_shareholders = merged[
            (merged['transaction_date_sell'].isnull()) |
            (merged['transaction_date_buy'] > merged['transaction_date_sell'])
        ]


        if current_shareholders.empty:
            logger.warning(f"No owner found for BBL: {bbl}")
            return []

        return current_shareholders['current_owner'].tolist()
    except ValueError as ve:
        logger.error(f"ValueError in get_building_shareholders: {ve}")
        return []
    except Exception as e:
        logger.error(f"Unexpected error occurred while retrieving current owner for BBL {bbl} in get_building_shareholders: {e}")
        return []