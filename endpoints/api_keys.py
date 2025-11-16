import os
from fastapi import APIRouter, Header, HTTPException, Depends
from starlette import status
from database_connector import DatabaseConnector
from database_connector import get_db
from endpoint_handlers.api_keys.create_key import create_key
from endpoint_handlers.api_keys.delete_key import delete_key
from endpoint_handlers.api_keys.exceptions import MissingAdminKeyException, InvalidAdminKeyException, FailedToCreateApiKeyException, FailedToDeleteApiKeyException
from endpoint_handlers.api_keys.list_all_keys import list_all_keys
from endpoint_handlers.api_keys.update_key import update_key
from logger_config import logger
from pydantic_models import CreateAPIKeyResponse, APIKeyListItem, MessageResponse, UpdateAPIKeyRequest

api_key_routes = APIRouter(prefix="/api-keys")


def verify_admin_key(api_key: str = Header(..., alias="X-API-Key")):
    """Verifies the request is using the admin API key.

    Args:
        api_key (str, optional): The API key from the "X-API-Key" header. 
            Defaults to Header(..., alias="X-API-Key").

    Raises:
        MissingAdminKeyException: If the admin key is not configured.
        InvalidAdminKeyException: If the provided API key is invalid.
    """
    admin_key = os.getenv("ADMIN_API_KEY")
    
    if not admin_key:
        logger.error("Admin key not configured")
        raise MissingAdminKeyException
    
    if api_key != admin_key:
        raise InvalidAdminKeyException


@api_key_routes.get("/create-key/{username}", dependencies=[Depends(verify_admin_key)])
def create_api_key(username: str, db: DatabaseConnector = Depends(get_db)):
    """Creates a new API key.

    Args:
        username (str): The name of the user to create the key for.
        db (DatabaseConnector, optional): The database connector. Defaults to Depends(get_db).

    Raises:
        FailedToCreateApiKeyException: If the API key could not be created.
        HTTPException: If an unexpected error occurs.

    Returns:
        CreateAPIKeyResponse: The new API key details.
    """
    try:
        key_config = create_key(username, db=db)
        
        return CreateAPIKeyResponse(
            id=key_config.id,
            key=key_config.key,
            name=key_config.name,
            enabled=key_config.enabled,
            created_at=key_config.created_at.isoformat()
        )
    except FailedToCreateApiKeyException:
        raise
    except Exception as e:
        logger.error(str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_key_routes.get("/list-keys", response_model=list[APIKeyListItem], dependencies=[Depends(verify_admin_key)])
def list_api_keys(db: DatabaseConnector = Depends(get_db)):
    """Lists all API keys without exposing the actual key values.

    Args:
        db (DatabaseConnector, optional): The database connector. Defaults to Depends(get_db).

    Raises:
        HTTPException: If an unexpected error occurs.

    Returns:
        list[APIKeyListItem]: A list of all API keys.
    """
    try:
        keys = list_all_keys(db=db)
        
        return [
            APIKeyListItem(
                id=key.id,
                name=key.name,
                enabled=key.enabled,
                created_at=key.created_at.isoformat(),
                updated_at=key.updated_at.isoformat(),
                last_used_at=key.last_used_at.isoformat() if key.last_used_at else None
            )
            for key in keys
        ]
    except Exception as e:
        logger.error(str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_key_routes.delete("/delete-key/{key_id}", response_model=MessageResponse, dependencies=[Depends(verify_admin_key)])
def delete_api_key(key_id: int, db: DatabaseConnector = Depends(get_db)):
    """Deletes an API key by ID.

    Args:
        key_id (int): The ID of the API key to delete.
        db (DatabaseConnector, optional): The database connector. Defaults to Depends(get_db).

    Raises:
        FailedToDeleteApiKeyException: If the API key could not be deleted.
        HTTPException: If an unexpected error occurs.

    Returns:
        MessageResponse: A message indicating the result of the deletion.
    """
    try:
        success = delete_key(key_id, db=db)
        
        if not success:
            raise FailedToDeleteApiKeyException
        
        return MessageResponse(message="API key deleted successfully")

    except Exception as e:
        logger.error(str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_key_routes.patch("/update-key/{key_id}", response_model=MessageResponse, dependencies=[Depends(verify_admin_key)])
def update_api_key(key_id: int, request: UpdateAPIKeyRequest, db: DatabaseConnector = Depends(get_db)):
    """Updates API key properties (name and/or enabled status).

    Args:
        key_id (int): The ID of the API key to update.
        request (UpdateAPIKeyRequest): The request body containing the new values.
        db (DatabaseConnector, optional): The database connector. Defaults to Depends(get_db).

    Raises:
        HTTPException: If the request is invalid or an unexpected error occurs.

    Returns:
        MessageResponse: A message indicating the result of the update.
    """
    try:
        if request.name is None and request.enabled is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
            )
        
        success = update_key(
            key_id=key_id,
            db=db,
            name=request.name,
            enabled=request.enabled
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
            )
        
        return MessageResponse(message="API key updated successfully")
    except Exception as e:
        logger.error(str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
