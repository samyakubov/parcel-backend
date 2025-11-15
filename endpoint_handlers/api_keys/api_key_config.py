from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class APIKeyConfig:
    """Represents the configuration of an API key.

    Attributes:
        id (int): The unique identifier of the API key.
        key (str): The API key string.
        name (str): The name associated with the API key.
        enabled (bool): Whether the API key is enabled.
        created_at (datetime): The timestamp when the API key was created.
        updated_at (datetime): The timestamp when the API key was last updated.
        last_used_at (Optional[datetime]): The timestamp when the API key was last used.
    """
    id: int
    key: str
    name: str
    enabled: bool
    created_at: datetime
    updated_at: datetime
    last_used_at: Optional[datetime]