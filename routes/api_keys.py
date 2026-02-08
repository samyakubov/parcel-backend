from fastapi import APIRouter, Depends

from database_connector import DatabaseConnector, get_db
# Disabled imports - write operations not available in read_only mode
# from handlers.api_keys.create_key import create_key
# from handlers.api_keys.delete_key import delete_key
# from handlers.api_keys.update_key import update_key
from handlers.api_keys.list_all_keys import list_all_keys
from routes.admin import verify_admin_key
from exceptions.api_key_exceptions import (
    APIKeyNotFoundError,
    FailedToDeleteApiKeyError,
    InvalidUpdateError,
)
from schemas import (
    APIKeyListItem,
    CreateAPIKeyResponse,
    MessageResponse,
    UpdateAPIKeyRequest,
)

api_key_routes = APIRouter(prefix="/api-keys")

# Disabled: Database is in read_only mode - use DuckDB CLI to create keys manually
# @api_key_routes.get("/create-key/name={name}", dependencies=[Depends(verify_admin_key)])
# def create_api_key(name: str, db: DatabaseConnector = Depends(get_db)) -> CreateAPIKeyResponse:
#     """Creates a new API key."""
#     key_config = create_key(name, db=db)
#     return CreateAPIKeyResponse(
#         id=key_config.id,
#         key=key_config.key,
#         name=key_config.name,
#         enabled=key_config.enabled,
#         created_at=key_config.created_at.isoformat(),
#     )


@api_key_routes.get("/list-keys", response_model=list[APIKeyListItem], dependencies=[Depends(verify_admin_key)])
def list_api_keys(db: DatabaseConnector = Depends(get_db)) -> list[APIKeyListItem]:
    """Lists all API keys without exposing the actual key values.

    Args:
        db (DatabaseConnector, optional): The database connector. Defaults to Depends(get_db).

    Returns:
        list[APIKeyListItem]: A list of all API keys.
    """
    keys = list_all_keys(db=db)

    return [
        APIKeyListItem(
            id=key.id,
            name=key.name,
            enabled=key.enabled,
            created_at=key.created_at.isoformat(),
            updated_at=key.updated_at.isoformat(),
            last_used_at=key.last_used_at.isoformat() if key.last_used_at else None,
        )
        for key in keys
    ]


# Disabled: Database is in read_only mode - use DuckDB CLI to delete keys manually
# @api_key_routes.delete(
#     "/delete-key/key_id={key_id}", response_model=MessageResponse, dependencies=[Depends(verify_admin_key)]
# )
# def delete_api_key(key_id: str, db: DatabaseConnector = Depends(get_db)) -> MessageResponse:
#     """Deletes an API key by ID."""
#     success = delete_key(int(key_id), db=db)
#     if not success:
#         raise FailedToDeleteApiKeyError("Failed to delete API key")
#     return MessageResponse(message="API key deleted successfully")


# Disabled: Database is in read_only mode - use DuckDB CLI to update keys manually
# @api_key_routes.patch(
#     "/update-key/key_id={key_id}", response_model=MessageResponse, dependencies=[Depends(verify_admin_key)]
# )
# def update_api_key(
#     key_id: int, request: UpdateAPIKeyRequest, db: DatabaseConnector = Depends(get_db)
# ) -> MessageResponse:
#     """Updates API key properties (name and/or enabled status)."""
#     if request.name is None and request.enabled is None:
#         raise InvalidUpdateError("At least one field (name or enabled) must be provided")
#     success = update_key(key_id=key_id, db=db, name=request.name, enabled=request.enabled)
#     if not success:
#         raise APIKeyNotFoundError(f"API key with ID {key_id} not found")
#     return MessageResponse(message="API key updated successfully")
