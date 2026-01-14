from fastapi import APIRouter, Depends

from database_connector import DatabaseConnector, get_db
from handlers.api_keys.create_key import create_key
from handlers.api_keys.delete_key import delete_key
from handlers.api_keys.list_all_keys import list_all_keys
from handlers.api_keys.update_key import update_key
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

@api_key_routes.get("/create-key/name={name}", dependencies=[Depends(verify_admin_key)])
def create_api_key(name: str, db: DatabaseConnector = Depends(get_db)) -> CreateAPIKeyResponse:
    """Creates a new API key.

    Args:
        name (str): The name of the user to create the key for.
        db (DatabaseConnector, optional): The database connector. Defaults to Depends(get_db).

    Raises:
        FailedToCreateApiKeyError: If the API key could not be created.

    Returns:
        CreateAPIKeyResponse: The new API key details.
    """
    key_config = create_key(name, db=db)

    return CreateAPIKeyResponse(
        id=key_config.id,
        key=key_config.key,
        name=key_config.name,
        enabled=key_config.enabled,
        created_at=key_config.created_at.isoformat(),
    )


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


@api_key_routes.delete(
    "/delete-key/key_id={key_id}", response_model=MessageResponse, dependencies=[Depends(verify_admin_key)]
)
def delete_api_key(key_id: str, db: DatabaseConnector = Depends(get_db)) -> MessageResponse:
    """Deletes an API key by ID.

    Args:
        key_id (str): The ID of the API key to delete.
        db (DatabaseConnector, optional): The database connector. Defaults to Depends(get_db).

    Raises:
        FailedToDeleteApiKeyError: If the API key could not be deleted.

    Returns:
        MessageResponse: A message indicating the result of the deletion.
    """
    success = delete_key(int(key_id), db=db)

    if not success:
        raise FailedToDeleteApiKeyError("Failed to delete API key")

    return MessageResponse(message="API key deleted successfully")


@api_key_routes.patch(
    "/update-key/key_id={key_id}", response_model=MessageResponse, dependencies=[Depends(verify_admin_key)]
)
def update_api_key(
    key_id: int, request: UpdateAPIKeyRequest, db: DatabaseConnector = Depends(get_db)
) -> MessageResponse:
    """Updates API key properties (name and/or enabled status).

    Args:
        key_id (int): The ID of the API key to update.
        request (UpdateAPIKeyRequest): The request body containing the new values.
        db (DatabaseConnector, optional): The database connector. Defaults to Depends(get_db).

    Raises:
        InvalidUpdateError: If the request is invalid.
        APIKeyNotFoundError: If the API key is not found.

    Returns:
        MessageResponse: A message indicating the result of the update.
    """
    if request.name is None and request.enabled is None:
        raise InvalidUpdateError("At least one field (name or enabled) must be provided")

    success = update_key(key_id=key_id, db=db, name=request.name, enabled=request.enabled)

    if not success:
        raise APIKeyNotFoundError(f"API key with ID {key_id} not found")

    return MessageResponse(message="API key updated successfully")
