"""FastMCP entry point - Croatian Narodne novine tools.

Run:

    python -m hr_eli_mcp.server

Configuration via env:

- ``HR_ELI_CACHE_DIR`` (default ``~/.matematic/cache/hr-eli``)
- ``HR_ELI_AUDIT_DIR`` (default ``~/.matematic/audit``)
- ``HR_ELI_BASE_URL`` (default ``https://narodne-novine.nn.hr``)
"""

from __future__ import annotations

import os

import httpx
from fastmcp import FastMCP
from mcp.types import ToolAnnotations

from .audit import AuditLogger, hash_input, timer
from .citations import build_record, parse_issue_sitemap
from . import runtime
from .client import DEFAULT_BASE_URL, NarodneNovineClient
from .models import Act, IssueHit, IssueListResult, LawText

INSTRUCTIONS = """\
This MCP server exposes the Croatian Official Gazette, Narodne novine (narodne-novine.nn.hr). Croatia is ELI-native (European ELI ontology, data.europa.eu/eli). Documents are addressed by year + gazette issue + document number, e.g. `year=2018, issue=42, doc=805`. Every response carries a stable `eli_uri`, a `human_readable_citation` and a `source_url` (the citation contract).

## Call order

1. `hr_list_issue` - list the documents of a gazette issue by `year` + `issue` (e.g. 2018 / 42). Use this to discover the `doc` number of an act. Each item carries `eli_uri` and `source_url`.
2. `hr_get_act` - metadata for a document by `year`, `issue`, `doc`: `eli_uri` (e.g. `https://narodne-novine.nn.hr/eli/sluzbeni/2018/42/805`), title, number, dates, type.
3. `hr_get_text` - the full official HTML text of a document by the same coordinates.

## Hard constraints

- **No free-text search** - addressed by ELI coordinate (year + issue + doc), not keywords. A Croatian citation gives the issue/year (e.g. "NN 42/2018"); use `hr_list_issue` to find the `doc`. Relay the `dataset_note`.
- **ELI is the key to citability** - the ELI is the `narodne-novine.nn.hr/eli/sluzbeni/...` URL; do not invent it. It is built from the coordinates and confirmed against the document's JSON-LD.
- **Text is the official HTML** - `hr_get_text` returns the gazette's HTML rendering verbatim; do not paraphrase it as the legal text.
- **Every response has `human_readable_citation` + `source_url`** - cite both to the user.
- **Audit log JSONL** - every tool call appends to `~/.matematic/audit/hr-eli-mcp.jsonl`.

## Error iteration

Tools return a structured error with a `[code]` prefix:
- `invalid_arg` - a parameter is missing or invalid (e.g. bad year, non-positive issue or doc).
- `not_found` - no document/issue exists for those coordinates.
- `upstream_error` - a Narodne novine error (HTTP, timeout, malformed JSON-LD). Retry once before surfacing.

## Response style

- Cite as `human_readable_citation` with the ELI URL: "Zakon o ... (NN 42/2018), https://narodne-novine.nn.hr/eli/sluzbeni/2018/42/805".
- NEVER invent an ELI, a number, an issue or a year - take each from the tool output.
"""


class ToolError(Exception):
    """Structured error for hr-eli MCP tools - visible to the LLM with a [code] prefix."""

    VALID_CODES = frozenset({"invalid_arg", "not_found", "upstream_error"})

    def __init__(self, code: str, message: str):
        if code not in self.VALID_CODES:
            raise ValueError(f"Unknown ToolError code: {code}. Valid: {sorted(self.VALID_CODES)}")
        self.code = code
        super().__init__(f"[{code}] {message}")


READ_ONLY = ToolAnnotations(
    readOnlyHint=True,
    idempotentHint=True,
    destructiveHint=False,
    openWorldHint=True,
)

mcp: FastMCP = FastMCP(name="hr-eli-mcp", instructions=INSTRUCTIONS)


def _base_url() -> str:
    return os.environ.get("HR_ELI_BASE_URL", runtime.base_url("eli", DEFAULT_BASE_URL)).rstrip("/")


def _audit() -> AuditLogger:
    return AuditLogger()


def _map_upstream(exc: Exception) -> Exception:
    if isinstance(exc, httpx.HTTPStatusError) and exc.response.status_code == 404:
        return ToolError("not_found", "No document/issue found in Narodne novine for those coordinates.")
    if isinstance(exc, (httpx.HTTPStatusError, httpx.TransportError, httpx.TimeoutException)):
        return ToolError("upstream_error", f"Narodne novine error: {type(exc).__name__}: {exc}")
    return exc


def _check_year(year: int) -> None:
    if not 1990 <= year <= 2100:
        raise ToolError("invalid_arg", f"year={year} is out of range (1990..2100; coverage starts 1990).")


def _check_pos(name: str, value: int) -> None:
    if value <= 0:
        raise ToolError("invalid_arg", f"{name}={value} must be positive.")


# ---------------------------------------------------------------------------
# hr_list_issue
# ---------------------------------------------------------------------------


@mcp.tool(annotations=READ_ONLY)
async def hr_list_issue(year: int, issue: int) -> IssueListResult:
    """List the documents published in a Narodne novine gazette issue.

    Args:
        year: e.g. ``2018``.
        issue: gazette issue number, e.g. ``42`` (from a citation like "NN 42/2018").

    Returns:
        ``IssueListResult`` with ``items: list[IssueHit]`` (each carrying ``eli_uri``).
    """
    audit = _audit()
    _check_year(year)
    _check_pos("issue", issue)
    input_hash = hash_input({"year": year, "issue": issue})

    with timer() as t:
        try:
            async with NarodneNovineClient(base_url=_base_url()) as client:
                xml = await client.get_issue_sitemap(year, issue)
        except Exception as exc:
            audit.log(tool="hr_list_issue", input_hash=input_hash, output_count_or_size=0,
                      duration_ms=t.duration_ms if t.duration_ms else 0, status="error",
                      error=f"{type(exc).__name__}: {exc}")
            raise _map_upstream(exc) from exc

    base = _base_url()
    coords = parse_issue_sitemap(xml)
    items = [
        IssueHit(
            year=c["year"], issue=c["issue"], doc=c["doc"],
            eli_uri=f"{base}/eli/sluzbeni/{c['year']}/{c['issue']}/{c['doc']}",
            source_url=f"{base}/eli/sluzbeni/{c['year']}/{c['issue']}/{c['doc']}",
        )
        for c in coords
    ]
    if not items:
        raise ToolError("not_found", f"No documents found for NN {issue}/{year}.")
    result = IssueListResult(year=year, issue=issue, total=len(items), items=items)
    audit.log(tool="hr_list_issue", input_hash=input_hash, output_count_or_size=len(items),
              duration_ms=t.duration_ms, status="ok")
    return result


# ---------------------------------------------------------------------------
# hr_get_act
# ---------------------------------------------------------------------------


@mcp.tool(annotations=READ_ONLY)
async def hr_get_act(year: int, issue: int, doc: int) -> Act:
    """Fetch document metadata by ELI coordinate (year + issue + doc).

    Args:
        year: e.g. ``2018``.
        issue: gazette issue, e.g. ``42``.
        doc: document number within the issue, e.g. ``805``.

    Returns:
        ``Act`` with ``eli_uri``, ``human_readable_citation``, ``source_url``.
    """
    audit = _audit()
    _check_year(year)
    _check_pos("issue", issue)
    _check_pos("doc", doc)
    input_hash = hash_input({"year": year, "issue": issue, "doc": doc})

    with timer() as t:
        try:
            async with NarodneNovineClient(base_url=_base_url()) as client:
                jsonld = await client.get_jsonld(year, issue, doc)
        except Exception as exc:
            audit.log(tool="hr_get_act", input_hash=input_hash, output_count_or_size=0,
                      duration_ms=t.duration_ms if t.duration_ms else 0, status="error",
                      error=f"{type(exc).__name__}: {exc}")
            raise _map_upstream(exc) from exc

    act = Act.model_validate(build_record(jsonld, year, issue, doc, _base_url()))
    audit.log(tool="hr_get_act", input_hash=input_hash, output_count_or_size=1,
              duration_ms=t.duration_ms, status="ok")
    return act


# ---------------------------------------------------------------------------
# hr_get_text
# ---------------------------------------------------------------------------


@mcp.tool(annotations=READ_ONLY)
async def hr_get_text(year: int, issue: int, doc: int) -> LawText:
    """Fetch the full official HTML text of a document by ELI coordinate.

    Args:
        year: e.g. ``2018``.
        issue: gazette issue, e.g. ``42``.
        doc: document number within the issue, e.g. ``805``.

    Returns:
        ``LawText`` with the citation contract and ``content`` (official HTML).
    """
    audit = _audit()
    _check_year(year)
    _check_pos("issue", issue)
    _check_pos("doc", doc)
    input_hash = hash_input({"year": year, "issue": issue, "doc": doc})

    with timer() as t:
        try:
            async with NarodneNovineClient(base_url=_base_url()) as client:
                jsonld = await client.get_jsonld(year, issue, doc)
                html = await client.get_html(year, issue, doc)
        except Exception as exc:
            audit.log(tool="hr_get_text", input_hash=input_hash, output_count_or_size=0,
                      duration_ms=t.duration_ms if t.duration_ms else 0, status="error",
                      error=f"{type(exc).__name__}: {exc}")
            raise _map_upstream(exc) from exc

    rec = build_record(jsonld, year, issue, doc, _base_url())
    result = LawText(
        year=year,
        issue=issue,
        doc=doc,
        title=rec.get("title"),
        eli_uri=rec.get("eli_uri"),
        human_readable_citation=rec.get("human_readable_citation"),
        source_url=rec.get("source_url"),
        content=html,
        byte_size=len(html.encode("utf-8")),
    )
    audit.log(tool="hr_get_text", input_hash=input_hash, output_count_or_size=result.byte_size or 0,
              duration_ms=t.duration_ms, status="ok")
    return result


def main() -> None:
    """Run the MCP server over stdio (default for Claude Code)."""
    mcp.run()


if __name__ == "__main__":
    main()
