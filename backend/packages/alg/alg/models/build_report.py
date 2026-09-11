"""Summary of one dataset build run."""

from pydantic import BaseModel, Field


class StageReport(BaseModel):
    """Outcome of a single pipeline stage."""

    stage: str
    produced: int = 0
    skipped: int = 0
    messages: list[str] = Field(default_factory=list)


class BuildReport(BaseModel):
    """Aggregate result of :func:`alg.entrypoints.toponym_dataset.build_toponym_dataset`."""

    built_at: str
    stages: list[StageReport] = Field(default_factory=list)
    toponyms_total: int = 0
    toponyms_by_level: dict[str, int] = Field(default_factory=dict)
    monuments_total: int = 0
    candidates_total: int = 0
    outputs: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)

    def add_stage(self, report: StageReport) -> None:
        """Append a stage report."""
        self.stages.append(report)
