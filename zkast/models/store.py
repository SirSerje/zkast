"""Store model for zkast."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class Store(BaseModel):
    """Represents a zkast store."""

    id: Optional[int] = None
    name: str = Field(..., min_length=1, max_length=100)
    format: str = Field(default="sqlite")
    created_at: Optional[datetime] = None

    class Config:
        """Pydantic configuration."""

        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None,
        }
