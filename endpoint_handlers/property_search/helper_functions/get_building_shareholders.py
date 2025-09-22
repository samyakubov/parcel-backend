from database_connector import db
from logger_config import logger


def get_building_shareholders(bbl: str):
    try:
        if not bbl or not isinstance(bbl, str):
            logger.error("Invalid BBL provided. It must be a non-empty string.")
            return "Invalid BBL provided. It must be a non-empty string."

        all_transactions_query = """
                                 SELECT party_name,
                                 CASE WHEN partytype_desc = 'GRANTEE/BUYER' THEN 'BUY' ELSE 'SELL' END AS action, recordedfiled AS transaction_date
                                 FROM AcrisPropertyAggregate
                                 WHERE bbl = ? AND doc_type = 'BOTH RPTT AND RETT' AND amount > 0 AND partytype_desc IN ('GRANTEE/BUYER', 'GRANTOR/SELLER')
                                 """
        all_transactions = db.execute_df(all_transactions_query, (bbl))

        if all_transactions.empty:
            logger.warning(f"No transactions found for BBL: {bbl}")
            return []

        latest_per_party = all_transactions.groupby(['party_name', 'action'], as_index=False).transaction_date.max()
        buy = latest_per_party[latest_per_party['action'] == 'BUY']
        sell = latest_per_party[latest_per_party['action'] == 'SELL']

        current_shareholders = buy[~buy['party_name'].isin(
            sell[sell['transaction_date'] > buy.set_index('party_name').loc[sell['party_name'], 'transaction_date'].values]['party_name']
        )]

        result_df = current_shareholders[['party_name']].rename(columns={'party_name': 'current_owner'})

        if result_df.empty:
            logger.warning(f"No owner found for BBL: {bbl}")
            return []

        return result_df['current_owner'].tolist()
    except ValueError as ve:
        logger.error(f"ValueError in get_current_owner: {ve}")
        return []
    except Exception as e:
        logger.error(f"Unexpected error occurred while retrieving current owner for BBL {bbl} in get_current_owner: {e}")
        return []