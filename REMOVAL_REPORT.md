# HXG v0.3.0 removal report

HXG v0.3.0 removes public v0.2.0 material that did not meet the new fail-closed source policy.

## Removed source families

- J.D. Power sources and `CLM-JDP-*` claims;
- AHLA sources and `CLM-AHLA-*` claims;
- WTTC sources and `CLM-WTTC-*` claims;
- ENERGY STAR quantitative context and `CLM-ENERGY-COST-01` / `CLM-ENERGY-HVAC-01`;
- commercial product and implementation sources that lack an approved ingestion rights record;
- Samsung evidence sources, claims, `ENT-SAMSUNG-REFERENCE`, and `REL-SAM-*` edges.

The earlier 74%, 62%, 44,787-person, $805B, 6%, 40%, and $11.6T figures are not present in the v0.3.0 site, data, graph, poster, carousel, or post copy.

`ENT-MACRO-CONTEXT` and `REL-AHLA-CONTEXT` were removed. Orphaned records were removed during deterministic validation.

## Replacement approach

- The six pathway relationship IDs remain, now supported only by original HXG analytical claims with explicit non-empirical limitations.
- Property value uses three original variable-based scenarios with no universal input or result.
- Samsung appears only through four metadata-only outbound links and an independence disclosure.

## Residual historical exposure

Git history was not rewritten. Earlier HXG-generated claims and artifacts therefore remain visible in old commits. No copied third-party PDFs or source images were found in the reachable-history audit, but old generated summaries remain residual exposure. Copies downloaded before takedown cannot be retracted by this repository.

The GitHub-created squash commit for the emergency takedown also retains the owner's private author email in commit metadata. The v0.3 branch and local repository use the GitHub noreply address. The owner should enable GitHub email privacy before any future server-side merge; removing the existing metadata would require a separately approved history rewrite and cache-purge request.
