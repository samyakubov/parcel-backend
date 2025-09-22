from database_connector import db


def get_zoning_details(bbl:str):
    try:
        result = db.execute_df("SELECT * FROM Zoning WHERE bbl = ?", (bbl))
        zoning = result[0] if result else None

        if not zoning:
            return None

        active_districts = [
            district for district in [
                zoning.zoning_district_1,
                zoning.zoning_district_2,
                zoning.zoning_district_3,
                zoning.zoning_district_4
            ] if district
        ]

        commercial_overlays = [
            overlay for overlay in [
                zoning.commercial_overlay_1,
                zoning.commercial_overlay_2
            ] if overlay
        ]

        special_districts = [
            district for district in [
                zoning.special_district_1,
                zoning.special_district_2,
                zoning.special_district_3
            ] if district
        ]

        return {
            'zoning_districts': active_districts,
            'commercial_overlays': commercial_overlays,
            'special_districts': special_districts,
            'limited_height_district': zoning.limited_height_district,
            'last_updated': zoning.updated_at.isoformat() if zoning.updated_at else None
        }
    except Exception as e:
        print(f"Error retrieving zoning details for BBL {bbl}: {str(e)}")
        raise