# Hospitality Experience Graph (HXG)

HXG is independent, hospitality-focused research into how connected in-room screens can connect guest comfort, property operations, and ecosystem value.

> **Release status:** `v0.1.0` is an AI-led, evidence-audited seed release produced with disclosed human governance. It is not an unattended API research run, and it does not imply Samsung sponsorship or endorsement.

The research treats Samsung as one clearly labeled, vendor-stated reference architecture. Independent guest evidence, industry economics, public standards, and competing implementation examples remain separate evidence classes.

## What is public

- A versioned evidence register with source, claim, entity, relationship, and run-manifest records.
- A reproducible Python CLI: `research`, `validate`, `build-graph`, and `build-publication`.
- GraphML and Cytoscape-compatible JSON exports.
- A static Astro/TypeScript evidence explorer with accessible table navigation.
- A deterministic eight-page LinkedIn carousel, downloadable poster, and publication copy.

Retrieved third-party documents are cached locally and gitignored. The repository publishes metadata, hashes, short supporting excerpts, locators, and derived claims—not copied source documents.

## Quick start

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -e ".[dev,research,publication]"
hxg validate
hxg build-graph
hxg build-publication
```

For a local model-backed run, copy `.env.example` to `.env`, provide an API key and a cost limit, then run:

```powershell
hxg research --mode agents --cutoff 2026-08-19 --cost-limit-usd 10
```

The public GitHub Actions workflow never executes model-backed research and never requires an API key.

## Evidence rules

- Every public relationship resolves to at least one claim and source.
- Facts, supported inferences, and modeled scenarios are separate record types.
- Vendor capabilities are labeled `vendor-stated` unless independently corroborated.
- Guest-behavior and causal claims require independent evidence.
- All publication counts are generated from the frozen run manifest.
- No source may be newer than the release cutoff.

## Repository map

```text
hxg/
├── methodology/        Research protocol, orchestration, and scoring
├── data/               Seed register, public records, and JSON schemas
├── graphs/             Canonical GraphML, JSON, SVG, and PNG outputs
├── reports/            Carousel, poster, findings, and LinkedIn copy
├── src/hxg/            CLI, schemas, validation, graph, and publication code
├── site/               Astro/TypeScript evidence explorer
├── tests/              Schemas, integrity, parity, cutoff, and determinism
└── .github/workflows/  Public validation and Pages deployment
```

## Licensing and trademarks

Code is licensed under Apache-2.0. Original documentation, structured derived data, and visuals are licensed under CC BY 4.0. Third-party content and trademarks are excluded from those grants; see [NOTICE](NOTICE.md).

Samsung and related marks belong to Samsung Electronics Co., Ltd. Their limited appearance here is solely descriptive of a reference case.
