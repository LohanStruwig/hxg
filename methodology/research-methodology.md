# HXG research methodology

## Public description

HXG is **AI-led, evidence-audited research with disclosed human governance**.

That wording is deliberate. A human defines the research charter, evidence policy, budget, risk controls, and publication decision. The research pipeline performs bounded discovery, extraction, entity resolution, graph proposal, contradiction review, citation audit, and publication preparation. Deterministic Python remains authoritative for identifiers, validation, counts, and exports.

Version 0.1.0 is an interactive Codex-assisted seed audit. It demonstrates the schemas, evidence register, graph, explorer, and publication pipeline without claiming that the standalone model-backed API workflow was executed.

## Research question

How does a connected hospitality screen translate hardware, software, data, and ecosystem partnerships into a more human stay—and where can value accrue across the lifecycle?

## Scope

- Current evidence window: January 1, 2024 through August 19, 2026.
- Geography: global economic and product context; North American guest evidence; selected global implementations.
- Historical material: permitted only when explicitly labeled, including NIST's 2020 PMS security reference design.
- Original human research: none. Published guest research is eligible evidence.
- Synthetic travelers: may illustrate a journey but are never evidence of guest preference or behavior.

## Source inclusion

Qualifying sources are primary research, independent research with disclosed samples, government or standards guidance, official product documentation, or official implementation records. Vendor sources can establish what a vendor states a product supports; they cannot independently establish guest benefit, causal value, or financial uplift.

Full retrieved documents stay in `data/cache/`, which is gitignored. Public records contain source metadata, content hashes, licensing status, short excerpts, locators, and derived atomic claims.

## Stages

1. The charter defines terms, inclusion rules, time window, stakeholders, and evidence requirements.
2. Discovery and perspective specialists search for independent, public, standards, and vendor evidence.
3. Extraction creates atomic claim records with dates, geography, metrics, excerpts, locators, limitations, and evidence class.
4. Entity resolution canonicalizes products, platforms, stakeholders, outcomes, risks, and value mechanisms.
5. Microsoft GraphRAG may propose entities, relationships, and communities across the corpus.
6. Deterministic Python resolves public IDs and rejects broken evidence chains.
7. Contradiction review searches for availability limits, stale context, privacy risks, accessibility gaps, network dependence, licensing, maintenance, and unsupported causation.
8. Citation audit verifies every public relationship from relationship → claim → source.
9. The frozen manifest generates counts and binds graph, explorer, poster, carousel, and copy to one release.

## Evidence states

- `fact` / solid edge: directly stated by the cited evidence.
- `supported-inference` / dashed edge: an interpretation supported by multiple facts, with limitations.
- `modeled-scenario` / dotted edge: a property-specific formula or hypothesis requiring local inputs and validation.

## Release gates

The release fails if any public relationship lacks a claim and source, any source exceeds the cutoff, a guest-behavior claim lacks independent evidence, IDs are duplicated, frozen counts do not match records, or GraphML and browser JSON diverge. The site and publication also require readable evidence IDs, a non-graph representation, consistent page dimensions, and explicit limitations.
