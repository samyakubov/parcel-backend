import pandas as pd

from schemas import BuildingCharacteristics


def get_building_characteristics(records_df: pd.DataFrame, pluto_df: pd.DataFrame) -> BuildingCharacteristics | None:
    """Builds the single building/lot characteristics section for a BBL: block/lot and
    address from the ACRIS records, everything else from the PLUTO row."""
    if records_df.empty:
        return None
    acris_row = records_df.iloc[0]

    fields = pluto_df.iloc[0].to_dict() if not pluto_df.empty else {}
    fields["prop_block"] = acris_row.get("prop_block")
    fields["prop_lot"] = acris_row.get("prop_lot")
    fields["address"] = f"{acris_row.get('prop_streetnumber')} {acris_row.get('prop_streetname')}"
    return BuildingCharacteristics(**fields)
