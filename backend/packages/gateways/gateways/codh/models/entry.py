"""Models for the CODH historical place-name index."""

from __future__ import annotations

from pydantic import BaseModel


class HistoricalEntry(BaseModel):
    """One historical place name with the modern address it covers.

    The index gives the present-day address a historical name corresponds to,
    which is what lets a village recorded in a Meiji-era source be reported
    under the municipality a reader can look up today.
    """

    entry_id: str
    pref_code: str
    name: str
    reading: str | None = None
    #: Present-day municipality the entry is filed under.
    municipality: str | None = None
    #: Modern address the historical name covers, as printed in the source.
    modern_address: str | None = None
    lat: float | None = None
    lon: float | None = None
    #: How the coordinate was derived, for example ``centroid``.
    method: str | None = None
    #: Identifier of the matching NIHU entry, when the two were linked.
    nihu_place_id: str | None = None
