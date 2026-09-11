"""Models for the GSI natural disaster monument dataset."""

from pydantic import BaseModel


class DisasterMonument(BaseModel):
    """A single natural disaster monument (自然災害伝承碑)."""

    monument_id: str
    name: str
    erected_year: str | None = None
    address: str | None = None
    disaster_name: str | None = None
    disaster_kind: str | None = None
    lore: str | None = None
    lat: float
    lon: float
