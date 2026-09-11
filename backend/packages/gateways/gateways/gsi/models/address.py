"""Models for the GSI address search API."""

from pydantic import BaseModel


class GsiAddressHit(BaseModel):
    """A single result returned by the GSI address search endpoint."""

    title: str
    lat: float
    lon: float
    address_code: str | None = None
    data_source: str | None = None
