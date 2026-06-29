"""Offline parse tests - JSON-LD + sitemap helpers against committed fixtures."""

from __future__ import annotations

from pathlib import Path

from hr_eli_mcp.citations import (
    act_eli_uri,
    build_record,
    parse_issue_sitemap,
    parse_jsonld,
)

FIX = Path(__file__).parent / "fixtures"
BASE = "https://narodne-novine.nn.hr"


def _read(name: str) -> str:
    return (FIX / name).read_text(encoding="utf-8")


def test_act_eli_uri():
    assert act_eli_uri(2018, 42, 805) == "https://narodne-novine.nn.hr/eli/sluzbeni/2018/42/805"


def test_parse_jsonld_work_and_expression():
    meta = parse_jsonld(_read("act_2018_42_805_jsonld.json"))
    assert meta.get("work_id") == "https://narodne-novine.nn.hr/eli/sluzbeni/2018/42/805"
    assert meta.get("number")  # has a document number
    assert meta.get("date_document")  # ISO date present
    assert meta.get("title") and "podataka" in meta["title"].lower()


def test_build_record_citation():
    rec = build_record(_read("act_2018_42_805_jsonld.json"), 2018, 42, 805, BASE)
    assert rec["eli_uri"] == "https://narodne-novine.nn.hr/eli/sluzbeni/2018/42/805"
    assert rec["source_url"] == rec["eli_uri"]
    assert rec["human_readable_citation"]
    assert "(NN 42/2018)" in rec["human_readable_citation"]


def test_parse_issue_sitemap_coords():
    coords = parse_issue_sitemap(_read("sitemap_2018_42.xml"))
    assert {"year": 2018, "issue": 42, "doc": 805} in coords
    # deduped (each doc appears once even though html + eli URLs both reference it)
    docs = [c["doc"] for c in coords]
    assert len(docs) == len(set(docs))
