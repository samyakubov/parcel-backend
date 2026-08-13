import pandas as pd

from schemas import BuildingCharacteristics

BUILDING_CHARACTERISTICS_FIELDS = list(BuildingCharacteristics.model_fields)


def get_building_characteristics(records_df: pd.DataFrame) -> BuildingCharacteristics | None:
    """Builds the single building/lot characteristics section from columns that are
    identical across every ACRIS/PLUTO row for a given BBL (e.g. lot dimensions, block/lot)."""
    if records_df.empty:
        return None
    row = records_df.iloc[0]
    fields = {field: row.get(field) for field in BUILDING_CHARACTERISTICS_FIELDS if field != "address"}
    fields["address"] = f"{row.get('prop_streetnumber')} {row.get('prop_streetname')}"
    return BuildingCharacteristics(**fields)
