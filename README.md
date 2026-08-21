# Hospitality Experience Graph (HXG)

> **Release status:** `v0.3.0` is a deterministic, rights-aware rebuild with disclosed human governance. It is rights-clean under the project source policy; that is not legal clearance.

HXG is an independent framework for examining how connected hospitality capabilities can support guest outcomes and property-specific value questions. The six pathways are analytical propositions, not empirical guest preferences or causal findings.

## What is public

- 10 reviewed evidence source records and machine-readable rights decisions;
- 19 claims with zero public third-party excerpts;
- 30 entities and 34 evidence-linked relationships;
- four metadata-only Samsung product links outside the evidence graph;
- GraphML, browser JSON, an accessible explorer, poster, and LinkedIn carousel;
- a reproducible CLI: `research`, `validate`, `build-graph`, and `build-publication`.

Generated counts are authoritative in `data/public/run-manifest.json`.

## Source policy

Sources fail closed before HTTP access unless current records approve automated acquisition, AI processing, and public republication. Unknown, denied, missing, conflicting, or expired rights stop the source. Vendor links cannot enter cache, model context, claims, or graph relationships.

Read [SOURCE_POLICY.md](SOURCE_POLICY.md), [RIGHTS_MANIFEST.md](RIGHTS_MANIFEST.md), and [REMOVAL_REPORT.md](REMOVAL_REPORT.md).

## Local build

```bash
python -m pip install -e ".[dev,publication]"
hxg research --mode seed --cutoff 2026-08-19 --retrieve
hxg build-graph
hxg validate
hxg build-publication
cd site
npm ci
npm run check
npm run build
npm run test:e2e
```

Model-backed research is local-only and requires separate secrets and budget approval. No model-backed research run was executed for v0.3.0.

## Licensing

Code is Apache-2.0. Original HXG documentation, structured data, and visuals are CC BY 4.0. Third-party material and trademarks are excluded from those grants.

Live explorer: <https://lohanstruwig.github.io/hxg/>
