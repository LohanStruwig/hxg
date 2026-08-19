# Evidence scoring

Confidence is a reviewable signal, not a probability of truth. Scores combine authority, independence, recency, specificity, corroboration, traceability, and disclosed limitations.

| Dimension | High signal | Confidence reduction |
|---|---|---|
| Authority | Original study, government standard, official product record | Secondary or unattributed summary |
| Independence | Independent guest or market study | Vendor describing its own outcomes |
| Recency | Inside the current evidence window | Historical context |
| Specificity | Named metric, period, geography, and sample | Broad or ambiguous language |
| Corroboration | Independent or cross-vendor support | Single-source assertion |
| Traceability | Stable URL, short excerpt, and locator | Inaccessible or missing locator |
| Limitations | Material constraints disclosed | Universal wording or hidden assumptions |

Suggested interpretation:

- `0.90–1.00`: strong direct evidence with clear provenance.
- `0.75–0.89`: supported but bounded; inspect limitations.
- `0.60–0.74`: useful inference or scenario requiring local validation.
- `<0.60`: not publication-ready without additional review.

Vendor-stated records may score highly for the narrow question “does the vendor state this capability?” They must not be reinterpreted as independent performance or outcome evidence.
