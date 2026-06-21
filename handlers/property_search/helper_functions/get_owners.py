import pandas as pd

from handlers.property_search.helper_functions.get_building_shareholders import get_building_shareholders
from handlers.property_search.helper_functions.get_current_home_owner import get_current_home_owner
from handlers.property_search.helper_functions.get_previous_owners import get_previous_home_owners
from schemas import COOP_PROPERTY_TYPES, Owners


def get_owners(bbl: str, acris_df: pd.DataFrame, jobs_df: pd.DataFrame) -> tuple[Owners, bool]:
    """
    Assemble current and previous owners from ACRIS records and job filings.

    Returns (owners, is_private) where is_private=True means the property is individually
    owned — not a coop with identifiable shareholders — so last_sold data is applicable.
    """
    phone_df = _build_phone_df(jobs_df)
    prop_type = str(acris_df.iloc[0].get("prop_type") or "")
    current = []

    if prop_type in COOP_PROPERTY_TYPES:
        current = get_building_shareholders(bbl, acris_df)

    is_private = not current
    if is_private:
        current = get_current_home_owner(bbl, acris_df, phone_df)

    previous = get_previous_home_owners(bbl, acris_df, phone_df)
    return Owners(
        current_owners=current,
        previous_owners=[p for p in previous if p not in current],
    ), is_private


def _build_phone_df(jobs_df: pd.DataFrame) -> pd.DataFrame:
    if not jobs_df.empty and "ownername" in jobs_df.columns and "OwnersPhone" in jobs_df.columns:
        return jobs_df[["ownername", "OwnersPhone"]].rename(
            columns={"ownername": "owner_full_name", "OwnersPhone": "owners_phone"}
        )
    return pd.DataFrame()
