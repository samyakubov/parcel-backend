from fastapi import APIRouter, Depends

from database_connector import DatabaseConnector, get_db
from endpoint_handlers.api_keys.validate_api_key import validate_api_key
from endpoint_handlers.party_search.search_by_party_name import search_by_party_name
from pydantic_models import PartySearchResponse

party_routes = APIRouter(prefix="/party")


@party_routes.get(
    "/search",
    dependencies=[Depends(validate_api_key)],
    response_model=PartySearchResponse,
)
def search_by_name(
    last_name: str, first_name: str, db: DatabaseConnector = Depends(get_db)
) -> PartySearchResponse:
    """Searches for ACRIS records by party name.

    Args:
        last_name (str): The last name of the party.
        first_name (str): The first name of the party.
        db (DatabaseConnector, optional): The database connector. Defaults to Depends(get_db).

    Returns:
        PartySearchResponse: A response object containing the search results.
    """
    return search_by_party_name(last_name, first_name, db)
