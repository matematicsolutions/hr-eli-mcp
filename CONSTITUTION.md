# Constitution of hr-eli-mcp

Version: 0.1.0
Date: 2026-06-29
Licence: Apache-2.0

`hr-eli-mcp` is an MCP server for the Croatian Narodne novine official gazette
(`narodne-novine.nn.hr`). It fetches Croatian legislation with European ELI citations. The MVP
covers official-gazette documents addressed by year + issue + doc; case law is a later feature.

The 4 principles below are inherited from the `eu-legal-mcp` line Constitution (Article IV).

---

## Art. 1. Public data only

Narodne novine is the official, public gazette of Croatia (Open Government Data, keyless). The
server is read-only and sends nothing beyond the requested coordinates.

## Art. 2. Mandatory audit log

Every tool call MUST append one JSON line to `~/.matematic/audit/hr-eli-mcp.jsonl`
(ts / tool / input_hash SHA-256 / output_count_or_size / duration_ms / status). Inability to write =
the tool returns an error, it does not silently skip.

## Art. 3. Vendor neutrality

No tool hardcodes an LLM provider, assumes a model, or adds commercial telemetry. The server talks
only to `narodne-novine.nn.hr` and the local filesystem. Authentication: none; own backoff + cache.

## Art. 4. ELI citations and a human-readable citation are mandatory

Every response MUST carry three fields:
- `eli_uri`: the European ELI Work IRI, built from year/issue/doc and confirmed against the
  document's JSON-LD (`https://narodne-novine.nn.hr/eli/sluzbeni/{year}/{issue}/{doc}`). NEVER
  invented. Croatia uses the European ELI ontology (`data.europa.eu/eli`).
- `human_readable_citation`: title + the Croatian gazette reference (e.g. "... (NN 42/2018)").
- `source_url`: the resolvable ELI page on narodne-novine.nn.hr.

---

## Open points

1. **Keyword search** - the gazette is path-based (year/issue/doc); discovery is per issue
   (`hr_list_issue`). Not a search API.
2. **Full text format** - `hr_get_text` returns the official HTML rendering; a JSON-LD / PDF
   manifestation also exists and could be added later.
3. **Case law** - Croatian court decisions (Supreme/Constitutional/Administrative) are a later
   feature, not in this gazette MVP.

## Ewolucja konstytucji

Changes to art. 1-4 follow SEMVER + an entry in `CHANGELOG.md` + a `pyproject.toml` bump.

First version: 2026-06-29. Author: Wieslaw Mazur / MateMatic.
