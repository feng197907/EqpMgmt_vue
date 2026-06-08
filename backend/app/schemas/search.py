"""Search Pydantic schemas.

Provides schemas for the global search API.
"""

from typing import Optional, List, Any

from pydantic import BaseModel


class SearchParams(BaseModel):
    """Schema for search request parameters."""
    q: str
    type: Optional[str] = None  # devices / documents / borrow_records — None = all


class SearchResultItem(BaseModel):
    """A single search result item."""
    id: int
    type: str   # device / document / borrow_record
    label: str
    extra: Optional[dict] = None


class SearchResult(BaseModel):
    """Schema for the aggregated search response."""
    devices: List[Any] = []
    documents: List[Any] = []
    borrow_records: List[Any] = []
