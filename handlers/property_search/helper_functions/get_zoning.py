import pandas as pd

from exceptions.property_search_exceptions import InvalidBBLError
from logger_config import logger
from schemas import Zoning


def get_zoning(bbl: str, zoning_df: pd.DataFrame) -> Zoning | None:
    """Gets the zoning information for a given BBL.

    Args:
        bbl: The BBL (Borough-Block-Lot) of the property to get zoning information for.
        zoning_df: DataFrame containing zoning data.

    Returns:
        A Zoning object containing the zoning information, or None if no information is found.

    Raises:
        InvalidBBLError: If the BBL is invalid.
    """
    if not bbl:
        raise InvalidBBLError

    logger.info(f"--------------------Processing zoning information for BBL: {bbl}--------------------")

    if zoning_df.empty:
        logger.info(f"No zoning information found for BBL: {bbl}")
        return None

    logger.info(f"Found zoning information for BBL: {bbl}")
    zoning = zoning_df.iloc[0]

    def safe_get(key):
        return zoning[key] if key in zoning else None

    active_districts = [
        district
        for district in [
            safe_get("Zoning District 1"),
            safe_get("Zoning District 2"),
            safe_get("Zoning District 3"),
            safe_get("Zoning District 4"),
        ]
        if district
    ]

    commercial_overlays = [
        overlay for overlay in [safe_get("Commercial Overlay 1"), safe_get("Commercial Overlay 2")] if overlay
    ]

    special_districts = [
        district
        for district in [
            safe_get("Special District 1"),
            safe_get("Special District 2"),
            safe_get("Special District 3"),
        ]
        if district
    ]

    zoning_data = Zoning(
        zoning_districts=active_districts,
        commercial_overlays=commercial_overlays,
        special_districts=special_districts,
        limited_height_district=safe_get("Limited Height District") or "",
        last_updated="",
    )
    logger.info(f"--------------------Successfully processed zoning information for BBL: {bbl}--------------------\n")
    return zoning_data
