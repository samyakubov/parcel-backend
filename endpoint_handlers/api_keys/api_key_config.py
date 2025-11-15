from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class APIKeyConfig:
    """Configuration associated with an API key"""
    id: int
    key: str
    name: str
    enabled: bool
    created_at: datetime
    updated_at: datetime
    last_used_at: Optional[datetime]