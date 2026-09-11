"""Geocoding through the GSI address search endpoint."""

from __future__ import annotations

from typing import Any

from gateways.gsi.models.address import GsiAddressHit
from gateways.http.connections import fetch_json

ADDRESS_SEARCH_URL = "https://msearch.gsi.go.jp/address-search/AddressSearch"


def search_address(query: str, *, force: bool = False) -> list[GsiAddressHit]:
    """Look up a place name or address and return matching coordinates.

    Args:
        query: Free-form Japanese place name or address.
        force: Bypass the HTTP cache.

    Returns:
        Hits ordered as returned by the service (best match first).

    """
    payload: Any = fetch_json(ADDRESS_SEARCH_URL, params={"q": query}, force=force)
    if not isinstance(payload, list):
        return []

    hits: list[GsiAddressHit] = []
    for item in payload:
        if not isinstance(item, dict):
            continue
        geometry = item.get("geometry") or {}
        coordinates = geometry.get("coordinates") or []
        expected_length = 2
        if len(coordinates) < expected_length:
            continue
        properties = item.get("properties") or {}
        hits.append(
            GsiAddressHit(
                title=str(properties.get("title", "")),
                lon=float(coordinates[0]),
                lat=float(coordinates[1]),
                address_code=str(properties.get("addressCode") or "") or None,
                data_source=str(properties.get("dataSource") or "") or None,
            ),
        )
    return hits
