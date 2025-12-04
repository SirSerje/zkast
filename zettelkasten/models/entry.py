"""Entry model for Zettelkasten."""
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


class Entry(BaseModel):
    """Represents a Zettelkasten entry."""

    id: Optional[int] = None
    store_id: Optional[int] = None
    message: str = Field(..., min_length=1)
    tags: List[str] = Field(default_factory=list)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        """Pydantic configuration."""

        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None,
        }

