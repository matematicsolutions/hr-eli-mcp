# hr-eli-mcp

An MCP server for the Croatian **Narodne novine** official gazette (`narodne-novine.nn.hr`). It
fetches Croatian legislation with European ELI identifiers and verifiable citations.

Part of the MateMatic `eu-legal-mcp` production line - after PL, DE, AT, ES, FI, IE, NL, SE, FR,
LU, DK and CZ. Same citation contract, Narodne novine source. Croatia is ELI-native on the
European ELI ontology (`data.europa.eu/eli`), with JSON-LD metadata per document.

> **Scope.** This MVP lists the documents of a gazette issue, returns per-document metadata from
> JSON-LD, and fetches the official HTML text. Documents are addressed by year + issue + document
> number; the gazette is path-based, not keyword search. Coverage 1990-present. Language:
> Croatian. Every response carries a `dataset_note`.
>
> **Licence.** Narodne novine is the official public gazette of Croatia. This connector relays it
> read-only with attribution and a `source_url`.

## The tools

| Tool | What it does |
|---|---|
| `hr_list_issue` | List the documents of a gazette issue by year + issue (discovery). |
| `hr_get_act` | Metadata for a document by year + issue + doc number. |
| `hr_get_text` | Full official HTML text of a document. |

Every response carries the contract: `eli_uri` (the European ELI URL, e.g.
`https://narodne-novine.nn.hr/eli/sluzbeni/2018/42/805`), `human_readable_citation`
(title + `NN 42/2018`), and `source_url`.

## Install

Run it with no install step (once published to PyPI):

```bash
uvx hr-eli-mcp
```

Or from source:

```bash
cd hr-eli-mcp
pip install -e .
```

## Configure (Claude Code / any MCP client)

```json
{
  "mcpServers": {
    "hr-eli-mcp": { "command": "hr-eli-mcp" }
  }
}
```

Environment:

- `HR_ELI_BASE_URL` - default `https://narodne-novine.nn.hr`
- `HR_ELI_CACHE_DIR` - default `~/.matematic/cache/hr-eli`
- `HR_ELI_AUDIT_DIR` - default `~/.matematic/audit`

No API key. Narodne novine open data is keyless.

## Governance

- **Public data only** - read-only against Narodne novine; no client data leaves the machine.
- **Audit log** - every tool call appends one JSON line to `~/.matematic/audit/hr-eli-mcp.jsonl`.
- **Vendor-neutral** - talks only to `narodne-novine.nn.hr`; no LLM provider, no telemetry.
- **Verifiable citations** - every response is independently checkable via `source_url`.

See `CONSTITUTION.md` and `DISCOVERY.md`.

## Tests

```bash
pip install -e ".[dev]"
pytest tests/test_instructions_drift.py tests/test_parse.py -v   # offline
pytest tests/test_smoke.py -v                                    # hits live Narodne novine
```

## Licence

Apache-2.0. © Matematic Solutions / Wieslaw Mazur.
