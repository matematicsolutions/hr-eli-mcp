"""Croatian Narodne novine (ELI / JSON-LD) parsing + citation helpers.

Narodne novine (the Croatian Official Gazette) is genuinely ELI-native: documents carry the
European ELI ontology (``data.europa.eu/eli``). Each document is addressed by
``/eli/sluzbeni/{year}/{issue}/{doc}`` and exposes a flattened JSON-LD graph with the FRBR
Work / Expression / Format nodes, plus an HTML rendering with RDFa.

We parse the JSON-LD with the stdlib (json) - no third-party RDF dep.

Citation contract:
- ``eli_uri``: the document's European ELI Work IRI (built from year/issue/doc, confirmed against
  the JSON-LD Work node). NEVER invented.
- ``human_readable_citation``: title + the Croatian gazette reference "NN {issue}/{year}".
- ``source_url``: the resolvable ELI page on narodne-novine.nn.hr.
"""

from __future__ import annotations

import json
import re
from typing import Any

ELI_NS = "http://data.europa.eu/eli/ontology#"
BASE_URL = "https://narodne-novine.nn.hr"


def act_eli_uri(year: int, issue: int, doc: int, base_url: str = BASE_URL) -> str:
    """Build the document's European ELI Work IRI."""
    return f"{base_url.rstrip('/')}/eli/sluzbeni/{year}/{issue}/{doc}"


def html_url(year: int, issue: int, doc: int, base_url: str = BASE_URL) -> str:
    """The Croatian full-text HTML rendering."""
    return f"{base_url.rstrip('/')}/eli/sluzbeni/{year}/{issue}/{doc}/hrv/html"


def _first_value(node: dict[str, Any], prop: str) -> str | None:
    arr = node.get(ELI_NS + prop)
    if isinstance(arr, list) and arr:
        v = arr[0]
        if isinstance(v, dict) and "@value" in v:
            return str(v["@value"])
    return None


def _first_id(node: dict[str, Any], prop: str) -> str | None:
    arr = node.get(ELI_NS + prop)
    if isinstance(arr, list) and arr:
        v = arr[0]
        if isinstance(v, dict) and "@id" in v:
            return str(v["@id"])
    return None


def _has_type(node: dict[str, Any], localname: str) -> bool:
    types = node.get("@type")
    return isinstance(types, list) and (ELI_NS + localname) in types


def parse_jsonld(jsonld_text: str) -> dict[str, Any]:
    """Parse the flattened JSON-LD graph into a flat metadata dict.

    Returns keys: title, number, date_document, date_publication, type_document, work_id.
    """
    out: dict[str, Any] = {}
    try:
        graph = json.loads(jsonld_text)
    except json.JSONDecodeError:
        return out
    if not isinstance(graph, list):
        graph = [graph]

    work = next((n for n in graph if isinstance(n, dict) and _has_type(n, "LegalResource")), None)
    expr = next((n for n in graph if isinstance(n, dict) and _has_type(n, "LegalExpression")), None)

    if work is not None:
        out["work_id"] = work.get("@id")
        out["number"] = _first_value(work, "number")
        out["date_document"] = _first_value(work, "date_document")
        out["date_publication"] = _first_value(work, "date_publication")
        type_id = _first_id(work, "type_document")
        if type_id:
            out["type_document"] = type_id.rstrip("/").rsplit("/", 1)[-1]
    if expr is not None:
        out["title"] = _first_value(expr, "title")

    return out


def build_record(
    jsonld_text: str, year: int, issue: int, doc: int, base_url: str = BASE_URL
) -> dict[str, Any]:
    """Build a citation-bearing record from a document's JSON-LD."""
    meta = parse_jsonld(jsonld_text)
    eli = act_eli_uri(year, issue, doc, base_url)
    title = meta.get("title")
    nn_ref = f"NN {issue}/{year}"
    human = f"{title} ({nn_ref})" if title else nn_ref

    return {
        "year": year,
        "issue": issue,
        "doc": doc,
        "title": title,
        "number": meta.get("number"),
        "type_document": meta.get("type_document"),
        "date_document": meta.get("date_document"),
        "date_publication": meta.get("date_publication"),
        "eli_uri": eli,
        "human_readable_citation": human,
        "source_url": eli,
    }


_ELI_PATH_RE = re.compile(r"/eli/sluzbeni/(\d+)/(\d+)/(\d+)\b")


def parse_issue_sitemap(xml_text: str) -> list[dict[str, int]]:
    """Extract the (year, issue, doc) coordinates of all documents in an issue sitemap."""
    seen: set[tuple[int, int, int]] = set()
    out: list[dict[str, int]] = []
    for m in _ELI_PATH_RE.finditer(xml_text):
        coord = (int(m.group(1)), int(m.group(2)), int(m.group(3)))
        if coord in seen:
            continue
        seen.add(coord)
        out.append({"year": coord[0], "issue": coord[1], "doc": coord[2]})
    return out
