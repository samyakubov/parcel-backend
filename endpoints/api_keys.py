import os
from typing import Optional
from fastapi import APIRouter, Header, HTTPException, Depends
from pydantic import BaseModel
from starlette import status

from endpoint_handlers.api_keys.create_key import create_key
from endpoint_handlers.api_keys.delete_key import delete_key
from endpoint_handlers.api_keys.exceptions import MissingAdminKeyException, InvalidAdminKeyException, FailedToCreateApiKeyException, FailedToDeleteApiKeyException
from endpoint_handlers.api_keys.list_all_keys import list_all_keys
from endpoint_handlers.api_keys.update_key import update_key
from logger_config import logger


class CreateAPIKeyResponse(BaseModel):
    id: int
    key: str
    name: str
    enabled: bool
    created_at: str


class APIKeyListItem(BaseModel):
    id: int
    name: str
    enabled: bool
    created_at: str
    updated_at: str
    last_used_at: Optional[str]


class UpdateAPIKeyRequest(BaseModel):
    name: Optional[str] = None
    enabled: Optional[bool] = None


class MessageResponse(BaseModel):
    message: str

api_key_routes = APIRouter(prefix="/api-keys")


def verify_admin_key(api_key: str = Header(..., alias="X-API-Key")):
    """
    Verify the request is using the admin API key.
    Raises HTTPException(403) if not authorized.
    """
    admin_key = os.getenv("ADMIN_API_KEY")
    
    if not admin_key:
        logger.error("Admin key not configured")
        raise MissingAdminKeyException
    
    if api_key != admin_key:
        raise InvalidAdminKeyException


@api_key_routes.get("/create-key/{username}", dependencies=[Depends(verify_admin_key)])
def create_api_key(username: str):
    """
    Create a new API key.
    Returns the full key value - this is the only time it will be shown.
    """
    try:
        key_config = create_key(username)
        
        return CreateAPIKeyResponse(
            id=key_config.id,
            key=key_config.key,
            name=key_config.name,
            enabled=key_config.enabled,
            created_at=key_config.created_at.isoformat()
        )
    except FailedToCreateApiKeyException as e:
        raise
    except Exception as e:
        logger.error(str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_key_routes.get("/list-keys", response_model=list[APIKeyListItem], dependencies=[Depends(verify_admin_key)])
def list_api_keys():
    """
    List all API keys without exposing the actual key values.
    """
    try:
        keys = list_all_keys()
        
        # Return keys without exposing the actual key values
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
def delete_api_key(key_id: int):
    """
    Delete an API key by ID.
    """
    try:
        success = delete_key(key_id)
        
        if not success:
            raise FailedToDeleteApiKeyException
        
        return MessageResponse(message="API key deleted successfully")

    except Exception as e:
        logger.error(str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_key_routes.patch("/update-key/{key_id}", response_model=MessageResponse, dependencies=[Depends(verify_admin_key)])
def update_api_key(key_id: int, request: UpdateAPIKeyRequest):
    """
    Update API key properties (name and/or enabled status).
    """
    try:
        if request.name is None and request.enabled is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
            )
        
        success = update_key(
            key_id=key_id,
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
