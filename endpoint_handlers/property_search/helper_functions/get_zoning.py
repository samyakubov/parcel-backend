from database_connector import DatabaseConnector
from exceptions.property_search_exceptions import InvalidBBLError
from logger_config import logger
from pydantic_models import Zoning


def get_zoning(bbl: str, db: DatabaseConnector) -> Zoning | None:
    """Gets the zoning information for a given BBL.

    Args:
        bbl: The BBL (Borough-Block-Lot) of the property to get zoning information for.
        db: The database connector instance.

    Returns:
        A Zoning object containing the zoning information, or None if no information is found.

    Raises:
        InvalidBBLError: If the BBL is invalid.
    """
    if not bbl:
        raise InvalidBBLError
    logger.info(f"--------------------Fetching zoning information for BBL: {bbl}--------------------")
    result = db.execute_df("SELECT * FROM zoning WHERE bbl = ?", [bbl])
    if result.empty:
        logger.info(f"No zoning information found for BBL: {bbl}")
        return None

    logger.info(f"Found zoning information for BBL: {bbl}")
    zoning = result.iloc[0]

    active_districts = [
        district
        for district in [
            zoning.get("Zoning District 1"),
            zoning.get("Zoning District 2"),
            zoning.get("Zoning District 3"),
            zoning.get("Zoning District 4"),
        ]
        if district
    ]

    commercial_overlays = [
        overlay for overlay in [zoning.get("Commercial Overlay 1"), zoning.get("Commercial Overlay 2")] if overlay
    ]

    special_districts = [
        district
        for district in [
            zoning.get("Special District 1"),
            zoning.get("Special District 2"),
            zoning.get("Special District 3"),
        ]
        if district
    ]

    zoning_data = Zoning(
        zoning_districts=active_districts,
        commercial_overlays=commercial_overlays,
        special_districts=special_districts,
        limited_height_district=zoning.get("Limited Height District", ""),
        last_updated="",
    )
    logger.info(f"--------------------Successfully processed zoning information for BBL: {bbl}--------------------\n")
    return zoning_data
