"""Smoke tests - require internet, hit the live Croatian Narodne novine gazette.

Run manually:

    pytest tests/test_smoke.py -v
"""

from __future__ import annotations

import pytest

from hr_eli_mcp.server import hr_get_act, hr_get_text, hr_list_issue

# NN 42/2018, doc 805 - Zakon o provedbi Opce uredbe o zastiti podataka (GDPR implementation act).
YEAR, ISSUE, DOC = 2018, 42, 805


@pytest.mark.asyncio
async def test_smoke_get_act() -> None:
    act = await hr_get_act(YEAR, ISSUE, DOC)
    assert act.eli_uri == "https://narodne-novine.nn.hr/eli/sluzbeni/2018/42/805"
    assert act.title and "podataka" in act.title.lower()
    assert act.human_readable_citation and "(NN 42/2018)" in act.human_readable_citation
    assert act.date_document and act.date_document[:4] == "2018"
    assert act.source_url and act.source_url.startswith("https://")


@pytest.mark.asyncio
async def test_smoke_get_text() -> None:
    text = await hr_get_text(YEAR, ISSUE, DOC)
    assert text.format == "html"
    assert text.content and "podataka" in text.content.lower()
    assert text.eli_uri == "https://narodne-novine.nn.hr/eli/sluzbeni/2018/42/805"
    assert text.byte_size and text.byte_size > 1000


@pytest.mark.asyncio
async def test_smoke_list_issue() -> None:
    res = await hr_list_issue(YEAR, ISSUE)
    assert res.total >= 1
    hit = next((h for h in res.items if h.doc == DOC), None)
    assert hit is not None
    assert hit.eli_uri == "https://narodne-novine.nn.hr/eli/sluzbeni/2018/42/805"
