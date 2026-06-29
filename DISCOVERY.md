# DISCOVERY - hr-eli-mcp (Croatia / Narodne novine)

Date: 2026-06-29. Source selection driven by Legal Data Hunter coverage data
(`worldwidelaw/legal-sources`): Croatia's `preferred_legislation_source` is `HR/OfficialGazette`
(Narodne novine), a clean, keyless, **European-ELI-native** source confirmed by live probes.

## Why Croatia

Narodne novine publishes every document on the **European ELI ontology** (`data.europa.eu/eli`),
with JSON-LD metadata, an HTML rendering with RDFa, and a sitemap for discovery. No key, no
scraping needed.

## Endpoints (keyless, Open Government Data)

| Purpose | Endpoint | Format |
|---|---|---|
| Issue listing (discovery) | `/sitemap_1_{year}_{issue}.xml` | XML sitemap |
| Document metadata | `/eli/sluzbeni/{year}/{issue}/{doc}/json-ld` | JSON-LD |
| Document full text | `/eli/sluzbeni/{year}/{issue}/{doc}/hrv/html` | HTML |
| (also) PDF / print HTML | `.../hrv/pdf`, `.../hrv/printhtml` | PDF / HTML |
| Sitemap index | `/sitemap.xml` | XML (per-issue sitemaps, 1990-present) |

- `sluzbeni` = the official ("sluzbeni dio") part of the gazette.
- 404 for a non-existent coordinate is clean.

## JSON-LD shape (flattened graph, FRBR)

- **Work** node (`@type` eli:LegalResource, `@id` = the ELI Work IRI): `eli:number`,
  `eli:date_document`, `eli:date_publication`, `eli:type_document` (an authority URI whose tail is
  e.g. `OSTALO` / `ZAKON`), `eli:passed_by`, `eli:based_on`, `eli:is_about` (EuroVoc).
- **Expression** node (`@type` eli:LegalExpression, `.../hrv`): `eli:title`, `eli:publisher`,
  `eli:language`.
- **Format** nodes (`.../hrv/html`, `.../hrv/printhtml`, `.../hrv/pdf`).

We read the title from the Expression node and the number/dates/type from the Work node.

Example probed: NN 42/2018 doc 805 (the GDPR implementation act) and NN 1/2025 doc 1.

## Citation contract (Art. 4)

- `eli_uri` = `https://narodne-novine.nn.hr/eli/sluzbeni/{year}/{issue}/{doc}` (European ELI Work).
- `human_readable_citation` = `{title} (NN {issue}/{year})`.
- `source_url` = the ELI page (resolves to the HTML rendering).

## Tools (MVP)

- `hr_list_issue(year, issue)` - parse the issue sitemap into document coordinates.
- `hr_get_act(year, issue, doc)` - JSON-LD metadata.
- `hr_get_text(year, issue, doc)` - official HTML text.

## Deferred

- **Case law / ECLI** - Croatian courts (Supreme / Constitutional / Administrative) are separate
  sources; feature 002 candidate.
- **JSON-LD / PDF text manifestations** - the MVP returns HTML; other formats could be exposed.
- **EuroVoc subjects / based_on graph** - present in JSON-LD, not surfaced as tool fields yet.

## Licence / re-use

Narodne novine is the official public gazette of Croatia. Read-only relay with attribution +
`source_url`. No key, no ToS gate for the ELI/sitemap endpoints. Distribution as a public
connector is in line with the keyless tier.
