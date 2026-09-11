"""Bibliographic sources backing every piece of evidence."""

from typing import Literal

from pydantic import BaseModel, Field

SourceType = Literal["book", "paper", "web", "gov", "db", "pdf", "monument", "news", "map"]


class Source(BaseModel):
    """A citable source: a book, paper, government page, dataset or monument."""

    id: str = Field(description="Stable identifier referenced by Evidence.source_id")
    type: SourceType
    title: str
    author: str | None = None
    year: int | None = None
    publisher: str | None = None
    url: str | None = None
    doi: str | None = None
    license: str | None = None
    accessed: str | None = Field(default=None, description="ISO date of last access")
    note: str | None = None
