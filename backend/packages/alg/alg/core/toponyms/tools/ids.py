"""Stable, URL-safe identifiers for toponym records."""

from __future__ import annotations

import hashlib

from alg.core.toponyms.tools.normalize import comparison_key
from alg.core.toponyms.tools.prefectures import pref_code
from alg.models.toponym import AdminArea


def make_toponym_id(name: str, admin: AdminArea, *, salt: str = "") -> str:
    """Build a deterministic identifier for a toponym.

    The identifier is used as a filename and as a URL segment, so it stays
    ASCII while remaining stable across rebuilds.

    Args:
        name: Place-name spelling.
        admin: Administrative context.
        salt: Extra discriminator when one place has several records.

    Returns:
        Identifier of the form ``<pref_code>-<digest>``.

    """
    code = admin.pref_code or pref_code(admin.pref) or "00"
    payload = "|".join(
        (
            comparison_key(name),
            comparison_key(admin.municipality or ""),
            comparison_key(admin.oaza or ""),
            comparison_key(admin.koaza or ""),
            salt,
        ),
    )
    digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()[:10]
    return f"{code}-{digest}"
