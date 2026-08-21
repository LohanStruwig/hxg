# Manager-led agent architecture

HXG follows a manager-style orchestration pattern: the manager retains responsibility and calls specialists as bounded tools. The configured discovery and extraction model is `gpt-5.6-terra`; contradiction review, citation audit, and final publication review use `gpt-5.6-sol`.

```text
Research charter
      │
      ▼
Permission gateway ── rights record + domain + review age + fail closed
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

- Discovery returns source candidates and metadata, not final findings. Candidates remain blocked until a human-reviewed rights record approves them.
- Perspective research separates guest, operator, IT, revenue, integrator, sustainability, privacy, and accessibility lenses.
- Extraction receives only approved cached material and emits paraphrased schema records with locators.
- GraphRAG proposes connections; it does not bypass referential-integrity checks.
- Contradiction review is intentionally adversarial.
- Citation audit can reject any claim or relationship.
- Publisher can only use frozen, audited records and generated counts.

The model-backed workflow runs locally with secrets and an explicit cost limit. Vendor-link-only records cannot enter agent or GraphRAG context. GitHub Actions never receives research credentials and executes deterministic validation and publication builds only. No model-backed run was executed for v0.3.0.
