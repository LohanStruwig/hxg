# HXG source policy

HXG v0.3.0 uses a fail-closed source-rights policy. “Rights-aware” and “rights-clean under the project source policy” describe this process; they are not legal clearance.

## Eligible evidence

A source may enter retrieval, cache, model context, claims, or graph relationships only when a current `SourceRights` record approves all three of these permissions:

- automated acquisition;
- AI processing;
- public republication of derived records.

The accepted rights bases are public domain, CC0, CC BY, another explicit open licence, explicit machine-access and reuse permission, or original HXG content.

## Fail-closed rules

- The rights review must be no more than 90 days old and not past its explicit expiry date.
- The reviewed domain must match the source URL.
- A denylisted or unknown domain is refused before an HTTP client is created.
- Missing, false, unknown, denied, or expired permissions are refusals.
- A conflicting page-specific notice overrides a general permission and blocks the source.
- Public v0.3.0 claims contain no third-party excerpts.

## Vendor links

`VendorLink` records contain only publisher, page title, product name, and outbound URL. They are metadata-only and cannot be retrieved, cached, quoted, hashed from page content, sent to a model, used in claims, or used in graph relationships.

## Files

- Reviewed permissions: `config/source-rights.yaml`
- Explicit blocks: `config/blocked-domains.txt`
- Public rights records: `data/public/source-rights.json`
- Public vendor links: `data/public/vendor-links.json`
- Historical removals: `REMOVAL_REPORT.md`

The project owner remains responsible for reviewing permissions and deciding whether to publish.
