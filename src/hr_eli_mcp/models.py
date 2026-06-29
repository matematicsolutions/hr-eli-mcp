"""Pydantic v2 models for the Croatian Narodne novine API + hr-eli-mcp."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

DATASET_NOTE = (
    "Narodne novine (the Croatian Official Gazette) is ELI-native (European ELI ontology, "
    "data.europa.eu/eli). Documents are addressed by year + issue + doc number "
    "(eli/sluzbeni/{year}/{issue}/{doc}); discover the documents of a gazette issue via "
    "hr_list_issue. Metadata comes from JSON-LD; full text is the official HTML rendering. "
    "There is no free-text search. Coverage 1990-present. Language: Croatian."
)


class _Tolerant(BaseModel):
    model_config = ConfigDict(extra="allow", populate_by_name=True)


class Act(_Tolerant):
    """A Croatian official-gazette document (from JSON-LD metadata)."""

    year: int | None = None
    issue: int | None = None
    doc: int | None = None
    title: str | None = None
    number: str | None = None
    type_document: str | None = None
    date_document: str | None = None
    date_publication: str | None = None

    # Citation contract (Art. 4 CONSTITUTION).
    eli_uri: str | None = None
    human_readable_citation: str | None = None
    source_url: str | None = None
    dataset_note: str = DATASET_NOTE


class LawText(_Tolerant):
    """Result of ``hr_get_text`` (official HTML rendering)."""

    year: int | None = None
    issue: int | None = None
    doc: int | None = None
    title: str | None = None
    eli_uri: str | None = None
    human_readable_citation: str | None = None
    source_url: str | None = None
    format: str = "html"
    content: str | None = None
    byte_size: int | None = None
    dataset_note: str = DATASET_NOTE


class IssueHit(_Tolerant):
    """A single document in a gazette issue listing."""

    year: int | None = None
    issue: int | None = None
    doc: int | None = None
    eli_uri: str | None = None
    source_url: str | None = None


class IssueListResult(_Tolerant):
    """Result of ``hr_list_issue``."""

    year: int
    issue: int
    total: int
    items: list[IssueHit] = Field(default_factory=list)
    dataset_note: str = DATASET_NOTE
