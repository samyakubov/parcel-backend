from database_connector import db


def get_zoning(bbl:str):
    try:
        result = db.execute_df("SELECT * FROM zoning WHERE bbl = ?", [bbl])
        if result.empty:
            return None


        zoning = result.iloc[0]

        active_districts = [
            district for district in [
                zoning["Zoning District 1"],
                zoning["Zoning District 2"],
                zoning["Zoning District 3"],
                zoning["Zoning District 4"]
            ] if district
        ]

        commercial_overlays = [
            overlay for overlay in [
                zoning["Commercial Overlay 1"],
                zoning["Commercial Overlay 2"]
            ] if overlay
        ]

        special_districts = [
            district for district in [
                zoning["Special District 1"],
                zoning["Special District 2"],
                zoning["Special District 3"]
            ] if district
        ]

        return {
            'zoning_districts': active_districts,
            'commercial_overlays': commercial_overlays,
            'special_districts': special_districts,
            'limited_height_district': zoning["Limited Height District"]
        }
    except Exception as e:
        print(f"Error retrieving zoning details for BBL {bbl}: {str(e)}")
        return None