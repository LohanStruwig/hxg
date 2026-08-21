# Data and provenance

- `seed/` contains the governed rights-aware register used for release 0.3.0.
- `public/` contains the frozen, schema-valid release consumed by the graph, explorer, and publication pipeline.
- `schemas/v1/` contains generated JSON Schemas.
- `cache/` stores retrieved third-party documents locally and is never committed.
- `private/graphrag/` is the optional local Microsoft GraphRAG workspace and is never committed.

`source-rights.json` records the permission basis for every public source and vendor link. Public v0.3.0 claims use paraphrase only and contain no excerpt. Link-only vendor records cannot enter evidence or model context.
