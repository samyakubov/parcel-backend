from database_connector import db
from logger_config import logger

def get_zoning(bbl:str):
    if not bbl:
        logger.warning("Attempted to get zoning information without a BBL.")
        return None
    try:
        logger.info(f"Fetching zoning information for BBL: {bbl}")
        result = db.execute_df("SELECT * FROM zoning WHERE bbl = ?", [bbl])
        if result.empty:
            logger.info(f"No zoning information found for BBL: {bbl}")
            return None

        logger.info(f"Found zoning information for BBL: {bbl}. Processing...")
        zoning = result.iloc[0]

        active_districts = [
            district for district in [
                zoning.get("Zoning District 1"),
                zoning.get("Zoning District 2"),
                zoning.get("Zoning District 3"),
                zoning.get("Zoning District 4")
            ] if district
        ]

        commercial_overlays = [
            overlay for overlay in [
                zoning.get("Commercial Overlay 1"),
                zoning.get("Commercial Overlay 2")
            ] if overlay
        ]

        special_districts = [
            district for district in [
                zoning.get("Special District 1"),
                zoning.get("Special District 2"),
                zoning.get("Special District 3")
            ] if district
        ]
        
        zoning_data = {
            'zoning_districts': active_districts,
            'commercial_overlays': commercial_overlays,
            'special_districts': special_districts,
            'limited_height_district': zoning.get("Limited Height District")
        }
        logger.info(f"Successfully processed zoning information for BBL: {bbl}")
        return zoning_data

    except Exception as e:
        logger.error(f"An unexpected error occurred while retrieving zoning details for BBL {bbl}: {e}", exc_info=True)
        return None
