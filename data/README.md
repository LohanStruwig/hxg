# Data and provenance

- `seed/` contains the governed seed evidence register used for release 0.2.0.
- `public/` contains the frozen, schema-valid release consumed by the graph, explorer, and publication pipeline.
- `schemas/v1/` contains generated JSON Schemas.
- `cache/` stores retrieved third-party documents locally and is never committed.
- `private/graphrag/` is the optional local Microsoft GraphRAG workspace and is never committed.

Each public claim contains a short excerpt and locator for verification. Those fields are research provenance, not permission to redistribute the source.
