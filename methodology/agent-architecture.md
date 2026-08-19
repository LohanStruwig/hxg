# Manager-led agent architecture

HXG follows a manager-style orchestration pattern: the manager retains responsibility and calls specialists as bounded tools. The configured discovery and extraction model is `gpt-5.6-terra`; contradiction review, citation audit, and final publication review use `gpt-5.6-sol`.

```text
Research charter
      │
      ▼
HXG manager ── budget + cutoff + tracing + publication authority
      │
      ├── source discovery
      ├── stakeholder perspectives
      ├── evidence extraction
      ├── entity resolution
      ├── GraphRAG graph/community proposal
      ├── contradiction review
      ├── citation audit
      └── publisher
      │
      ▼
Deterministic validation → frozen run manifest → graph/site/publications
```

## Specialist boundaries

- Discovery returns source candidates and metadata, not final findings.
- Perspective research separates guest, operator, IT, revenue, integrator, sustainability, privacy, and accessibility lenses.
- Extraction emits versioned schema records and preserves short locators.
- GraphRAG proposes connections; it does not bypass referential-integrity checks.
- Contradiction review is intentionally adversarial.
- Citation audit can reject any claim or relationship.
- Publisher can only use frozen, audited records and generated counts.

The model-backed workflow runs locally with secrets and an explicit cost limit. GitHub Actions never receives research credentials and executes deterministic validation and publication builds only.
