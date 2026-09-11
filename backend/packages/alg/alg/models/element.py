"""Dictionary of place-name elements that signal disaster-prone terrain."""

from pydantic import BaseModel, Field

from alg.models.hazard import HazardType


class ToponymElement(BaseModel):
    """One element (morpheme) of a place name, with its terrain meaning.

    Elements carry a specificity score because "蛇抜" almost always marks a debris
    flow site while "久保" merely marks a hollow, so the two must not be weighed
    the same when screening candidates by spelling alone.
    """

    id: str
    label: str = Field(description="Human readable element name, e.g. ウメ（梅・埋）")
    surfaces: list[str] = Field(default_factory=list, description="Kanji spellings")
    readings: list[str] = Field(default_factory=list, description="Katakana readings")
    meaning: str
    hazard_types: list[HazardType] = Field(default_factory=list)
    specificity: float = Field(
        ge=0.0,
        le=1.0,
        description="How strongly the spelling alone implies disaster history",
    )
    substitution_of: str | None = Field(
        default=None,
        description="Original character when the surface is a 替字, e.g. 梅 <- 埋",
    )
    source_ids: list[str] = Field(default_factory=list)
    note: str | None = None


class ElementDictionary(BaseModel):
    """The full element dictionary as loaded from ``data/curated/elements.yaml``."""

    elements: list[ToponymElement] = Field(default_factory=list)

    def by_id(self) -> dict[str, ToponymElement]:
        """Index the dictionary by element id."""
        return {element.id: element for element in self.elements}
