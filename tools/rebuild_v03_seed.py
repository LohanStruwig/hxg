from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SEED = ROOT / "data" / "seed"


def write(name: str, payload: object) -> None:
    (SEED / name).write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def metadata_hash(record: dict) -> str:
    keys = ("id", "title", "publisher", "url", "publication_date")
    value = json.dumps({key: record[key] for key in keys}, sort_keys=True, separators=(",", ":"))
    return "sha256:" + hashlib.sha256(value.encode()).hexdigest()


def source(
    source_id: str,
    title: str,
    publisher: str,
    url: str,
    publication_date: str,
    geography: list[str],
    authority_tier: str,
    licensing_status: str,
    *,
    historical: bool = False,
    notes: str,
) -> dict:
    record = {
        "schema_version": "1.0.0",
        "id": source_id,
        "title": title,
        "publisher": publisher,
        "url": url,
        "publication_date": publication_date,
        "accessed_date": "2026-08-20",
        "geography": geography,
        "authority_tier": authority_tier,
        "licensing_status": licensing_status,
        "hash_basis": "metadata-record",
        "access_status": "accessible",
        "historical_context": historical,
        "notes": notes,
    }
    record["content_hash"] = metadata_hash(record)
    return record


sources = [
    source("SRC-W3C-WCAG22", "Web Content Accessibility Guidelines 2.2", "World Wide Web Consortium", "https://www.w3.org/TR/WCAG22/", "2023-10-05", ["Global"], "standard-or-government", "W3C Document License 2023", historical=True, notes="Open standards context; v0.3 public claims contain no excerpt."),
    source("SRC-W3C-ACCESSIBILITY-PRINCIPLES", "Accessibility Principles", "World Wide Web Consortium", "https://www.w3.org/WAI/fundamentals/accessibility-principles/", "2019-05-04", ["Global"], "standard-or-government", "W3C Document License 2023", historical=True, notes="Open accessibility context; v0.3 public claims contain no excerpt."),
    source("SRC-NIST-IOT-HANDBOOK-2024", "Product Development Cybersecurity Handbook for IoT Product Manufacturers", "National Institute of Standards and Technology", "https://csrc.nist.gov/pubs/cswp/33/product-development-cybersecurity-handbook/ipd", "2024-11-19", ["United States"], "standard-or-government", "NIST public information policy", notes="No item-specific copyright notice identified in the rights review."),
    source("SRC-NIST-PMS-2020", "Securing Property Management Systems", "National Institute of Standards and Technology", "https://csrc.nist.gov/pubs/sp/1800/27/final", "2020-10-01", ["United States"], "standard-or-government", "NIST public information policy", historical=True, notes="Historical security reference; v0.3 public claims contain no excerpt."),
    source("SRC-MS-GRAPHRAG-REPO", "Microsoft GraphRAG", "Microsoft", "https://github.com/microsoft/graphrag", "2024-07-01", ["Global"], "primary", "MIT License", notes="Repository method reference; code is not redistributed."),
    source("SRC-MS-GRAPHRAG-PAPER", "From Local to Global: A Graph RAG Approach to Query-Focused Summarization", "Microsoft Research", "https://arxiv.org/abs/2404.16130", "2024-04-24", ["Global"], "independent-research", "CC BY 4.0", notes="Method reference; public claim is paraphrased."),
    source("SRC-GITHUB-PAGES", "What Is GitHub Pages?", "GitHub", "https://docs.github.com/en/pages/getting-started-with-github-pages/what-is-github-pages", "2026-08-19", ["Global"], "primary", "GitHub Docs CC BY 4.0", notes="Static publication mechanism only."),
    source("SRC-HXG-FRAMEWORK", "HXG Six-Pathway Experience Framework", "Hospitality Experience Graph", "https://github.com/LohanStruwig/hxg/blob/main/docs/hxg-framework.md", "2026-08-19", ["Global"], "primary", "Original HXG content, CC BY 4.0", notes="Original analytical framework; not empirical guest-preference evidence."),
    source("SRC-HXG-METHODOLOGY", "HXG Rights-Aware Research Methodology", "Hospitality Experience Graph", "https://github.com/LohanStruwig/hxg/blob/main/methodology/research-methodology.md", "2026-08-19", ["Global"], "primary", "Original HXG content, CC BY 4.0", notes="Original methodology and governance record."),
    source("SRC-HXG-VALUE-MODEL", "HXG Property-Specific Value Model", "Hospitality Experience Graph", "https://github.com/LohanStruwig/hxg/blob/main/docs/value-model.md", "2026-08-19", ["Global"], "primary", "Original HXG content, CC BY 4.0", notes="Variable-based scenarios only; no universal rate, uplift, savings, or ROI."),
]


def claim(
    claim_id: str,
    text: str,
    classification: str,
    evidence_ids: list[str],
    confidence: float,
    limitations: list[str],
    locator: str,
    *,
    outcome: str | None = None,
    stakeholder: str | None = None,
    value_type: str | None = None,
    metric: str | None = None,
) -> dict:
    return {
        "schema_version": "1.0.0",
        "id": claim_id,
        "text": text,
        "classification": classification,
        "evidence_ids": evidence_ids,
        "metric": metric,
        "value": None,
        "unit": None,
        "period": None,
        "geography": ["Global"],
        "confidence": confidence,
        "limitations": limitations,
        "review_state": "audited" if classification == "fact" else "limited",
        "excerpt": "",
        "locator": locator,
        "outcome": outcome,
        "stakeholder": stakeholder,
        "value_type": value_type,
    }


pathways = [
    ("HOME", "Cast from your device", "Feel at home", "feel-at-home"),
    ("CONTROL", "Control room settings", "Feel in control", "feel-in-control"),
    ("RECOGNIZED", "Connect stay context", "Feel recognized", "feel-recognized"),
    ("INCLUDED", "Present content accessibly", "Feel included", "feel-included"),
    ("SECURE", "Protect sessions and data", "Feel secure", "feel-secure"),
    ("SUPPORTED", "Request services and help", "Feel supported", "feel-supported"),
]

claims = [
    claim("CLM-HXG-PROPOSITION-01", "HXG proposes that an in-room display can be treated as an experience-orchestration layer connecting guest-facing capabilities, operational systems, and property-specific value questions.", "supported-inference", ["SRC-HXG-FRAMEWORK"], 0.82, ["This is an HXG analytical proposition, not a measured market or causal finding."], "HXG framework, working proposition"),
    *[
        claim(f"CLM-HXG-PATH-{code}-01", f"HXG maps the capability '{capability}' to the guest outcome '{outcome}' using the bounded relationship 'can support'.", "supported-inference", ["SRC-HXG-FRAMEWORK"], 0.80, ["This is an analytical pathway for evaluation, not an empirically proven guest preference or causal effect."], f"HXG framework, {outcome} pathway", outcome=slug)
        for code, capability, outcome, slug in pathways
    ],
    claim("CLM-W3C-ACCESS-01", "W3C accessibility guidance provides established principles for making digital content perceivable, operable, understandable, and robust.", "fact", ["SRC-W3C-WCAG22", "SRC-W3C-ACCESSIBILITY-PRINCIPLES"], 0.95, ["Conformance must be evaluated against the applicable interface and content; the guidance does not certify HXG or a hospitality product."], "WCAG 2.2 principles; paraphrase only", outcome="feel-included"),
    claim("CLM-NIST-IOT-LIFECYCLE-01", "NIST guidance treats cybersecurity as a lifecycle responsibility for IoT products and connected environments.", "fact", ["SRC-NIST-IOT-HANDBOOK-2024"], 0.94, ["General cybersecurity guidance does not certify any specific hospitality deployment."], "NIST IoT handbook overview; paraphrase only", outcome="feel-secure"),
    claim("CLM-NIST-PMS-RISK-01", "NIST documents security considerations for property management system environments and their connected components.", "fact", ["SRC-NIST-PMS-2020"], 0.94, ["Historical U.S. guidance; implementation and jurisdictional requirements vary."], "NIST SP 1800-27 overview; paraphrase only", outcome="feel-secure"),
    claim("CLM-GRAPHRAG-METHOD-01", "GraphRAG provides a graph-based approach for organizing entities, relationships, and community-level summaries from a source corpus.", "fact", ["SRC-MS-GRAPHRAG-REPO", "SRC-MS-GRAPHRAG-PAPER"], 0.93, ["Method capability does not establish the correctness of any HXG claim; deterministic validation and human review remain required."], "GraphRAG repository and paper overview; paraphrase only"),
    claim("CLM-GITHUB-PAGES-01", "GitHub Pages can publish a static site from repository content and an Actions-based build.", "fact", ["SRC-GITHUB-PAGES"], 0.95, ["This describes the publication mechanism, not evidence quality."], "GitHub Pages overview; paraphrase only"),
    claim("CLM-HXG-STAKEHOLDERS-01", "HXG groups stakeholders by who experiences the interaction, who operates the property, who enables the systems, and who must validate any claimed value.", "supported-inference", ["SRC-HXG-FRAMEWORK"], 0.84, ["Roles and commercial arrangements vary by property and deployment."], "HXG framework, stakeholder model", stakeholder="hospitality-ecosystem"),
    claim("CLM-HXG-VALUE-ANCILLARY-01", "Potential ancillary contribution can be modeled as eligible occupied room nights multiplied by measured engagement, incremental conversion, and contribution margin.", "modeled-scenario", ["SRC-HXG-VALUE-MODEL"], 0.60, ["Every input must be measured locally; no universal rate, uplift, or ROI is supplied."], "HXG value model, ancillary formula", value_type="ancillary-contribution", metric="eligible room nights x engagement x incremental conversion x contribution margin"),
    claim("CLM-HXG-VALUE-ENERGY-01", "Potential energy value can be modeled as a verified baseline multiplied by controllable share and a measured reduction attributable to the intervention.", "modeled-scenario", ["SRC-HXG-VALUE-MODEL"], 0.60, ["Requires a property baseline, a defensible counterfactual, and verified measurement; no savings rate is supplied."], "HXG value model, energy formula", value_type="energy-value", metric="verified baseline x controllable share x measured attributable reduction"),
    claim("CLM-HXG-VALUE-SUPPORT-01", "Potential operational-support value can be modeled as remotely resolved incidents multiplied by measured avoided dispatch cost.", "modeled-scenario", ["SRC-HXG-VALUE-MODEL"], 0.60, ["Remote resolution and avoided dispatches must be verified locally; no savings rate is supplied."], "HXG value model, support formula", value_type="operational-support", metric="verified remote resolutions x measured avoided dispatch cost"),
    claim("CLM-HXG-NETWORK-CONDITION-01", "HXG treats network readiness as a condition that can change whether connected guest capabilities function as intended.", "supported-inference", ["SRC-HXG-FRAMEWORK", "SRC-NIST-IOT-HANDBOOK-2024"], 0.82, ["Network requirements are deployment-specific."], "HXG framework, network condition"),
    claim("CLM-HXG-GOVERNANCE-CONDITION-01", "HXG treats data governance as a condition on systems that exchange stay, identity, preference, or operational context.", "supported-inference", ["SRC-HXG-FRAMEWORK", "SRC-NIST-PMS-2020"], 0.84, ["Applicable privacy, retention, and security obligations vary by jurisdiction and implementation."], "HXG framework, governance condition"),
    claim("CLM-HXG-AVAILABILITY-CONDITION-01", "HXG treats product, region, integration, language, and licensing availability as conditions that must be verified before a pathway is claimed in a real deployment.", "supported-inference", ["SRC-HXG-FRAMEWORK"], 0.86, ["Availability cannot be inferred from a generic architecture map."], "HXG framework, availability condition"),
]


def entity(entity_id: str, name: str, entity_type: str, description: str, *, outcome: str | None = None, evidence_ids: list[str] | None = None) -> dict:
    return {"schema_version": "1.0.0", "id": entity_id, "canonical_name": name, "aliases": [], "entity_type": entity_type, "description": description, "outcome": outcome, "evidence_ids": evidence_ids or []}


entities = [
    entity("ENT-HUMAN-EXPERIENCE", "Human experience", "human-experience", "The HXG organizing framework for six guest outcomes.", evidence_ids=["SRC-HXG-FRAMEWORK"]),
    entity("ENT-FEEL-HOME", "Feel at home", "outcome", "Familiarity and reduced friction in the room.", outcome="feel-at-home", evidence_ids=["SRC-HXG-FRAMEWORK"]),
    entity("ENT-FEEL-CONTROL", "Feel in control", "outcome", "Clear, usable control over relevant room settings.", outcome="feel-in-control", evidence_ids=["SRC-HXG-FRAMEWORK"]),
    entity("ENT-FEEL-RECOGNIZED", "Feel recognized", "outcome", "Stay context can make information and service more relevant.", outcome="feel-recognized", evidence_ids=["SRC-HXG-FRAMEWORK"]),
    entity("ENT-FEEL-INCLUDED", "Feel included", "outcome", "Content and interaction designed to reduce access barriers.", outcome="feel-included", evidence_ids=["SRC-HXG-FRAMEWORK", "SRC-W3C-WCAG22"]),
    entity("ENT-FEEL-SECURE", "Feel secure", "outcome", "Trust supported by visible, effective privacy and security controls.", outcome="feel-secure", evidence_ids=["SRC-HXG-FRAMEWORK", "SRC-NIST-IOT-HANDBOOK-2024"]),
    entity("ENT-FEEL-SUPPORTED", "Feel supported", "outcome", "Timely access to service and help.", outcome="feel-supported", evidence_ids=["SRC-HXG-FRAMEWORK"]),
    entity("ENT-CONNECTED-DISPLAY", "Connected in-room display", "technology", "A guest-facing interface within a wider property system.", evidence_ids=["SRC-HXG-FRAMEWORK"]),
    entity("ENT-CASTING", "Personal-device casting", "technology", "A capability for presenting guest-selected content from a personal device.", evidence_ids=["SRC-HXG-FRAMEWORK"]),
    entity("ENT-IOT-CONTROLS", "Room controls", "technology", "Interfaces and integrations for eligible room settings.", evidence_ids=["SRC-HXG-FRAMEWORK", "SRC-NIST-IOT-HANDBOOK-2024"]),
    entity("ENT-PMS-INTEGRATION", "Stay-context integration", "technology", "A controlled exchange of relevant stay context between property systems.", evidence_ids=["SRC-HXG-FRAMEWORK", "SRC-NIST-PMS-2020"]),
    entity("ENT-LANGUAGE-ACCESS", "Accessible content presentation", "technology", "Language, captioning, navigation, and presentation choices that reduce barriers.", evidence_ids=["SRC-HXG-FRAMEWORK", "SRC-W3C-WCAG22"]),
    entity("ENT-PRIVACY-CONTROLS", "Session and data protection", "technology", "Controls for session isolation, data handling, and secure lifecycle management.", evidence_ids=["SRC-HXG-FRAMEWORK", "SRC-NIST-IOT-HANDBOOK-2024", "SRC-NIST-PMS-2020"]),
    entity("ENT-DIGITAL-CONCIERGE", "Service-request channel", "technology", "A guest-facing channel for requests, information, and help.", evidence_ids=["SRC-HXG-FRAMEWORK"]),
    entity("ENT-CLOUD-MANAGEMENT", "Remote device management", "technology", "A management capability for monitoring and supporting connected endpoints.", evidence_ids=["SRC-HXG-FRAMEWORK", "SRC-NIST-IOT-HANDBOOK-2024"]),
    entity("ENT-GUEST", "Guest", "stakeholder", "The person experiencing the stay.", evidence_ids=["SRC-HXG-FRAMEWORK"]),
    entity("ENT-PROPERTY-OPERATOR", "Property owner or operator", "stakeholder", "The organization accountable for service, operations, and local performance.", evidence_ids=["SRC-HXG-FRAMEWORK"]),
    entity("ENT-BRAND", "Brand or management company", "stakeholder", "The organization shaping experience standards and portfolio consistency.", evidence_ids=["SRC-HXG-FRAMEWORK"]),
    entity("ENT-OEM-PLATFORM", "OEM or platform owner", "stakeholder", "A provider of hardware, software, or platform capabilities.", evidence_ids=["SRC-HXG-FRAMEWORK"]),
    entity("ENT-INTEGRATOR", "Dealer or integrator", "stakeholder", "A party that designs, installs, integrates, and supports a deployment.", evidence_ids=["SRC-HXG-FRAMEWORK"]),
    entity("ENT-TECH-PARTNERS", "Technology partners", "stakeholder", "Providers of connected systems, content, and services.", evidence_ids=["SRC-HXG-FRAMEWORK"]),
    entity("ENT-HUMAN-VALUE", "Human value", "value", "Time, effort, familiarity, access, control, and trust considered without automatic monetization.", evidence_ids=["SRC-HXG-VALUE-MODEL"]),
    entity("ENT-PROPERTY-VALUE", "Property-specific value", "value", "A locally measured operational or financial result.", evidence_ids=["SRC-HXG-VALUE-MODEL"]),
    entity("ENT-ECOSYSTEM-VALUE", "Ecosystem participation", "value", "Potential hardware, software, integration, and service roles without revenue estimates.", evidence_ids=["SRC-HXG-VALUE-MODEL"]),
    entity("ENT-ENERGY-EFFICIENCY", "Measured energy value", "value", "A property-specific scenario based on verified baseline and attributable reduction.", evidence_ids=["SRC-HXG-VALUE-MODEL"]),
    entity("ENT-ANCILLARY-REVENUE", "Measured ancillary contribution", "value", "A property-specific scenario based on measured incremental behavior and contribution margin.", evidence_ids=["SRC-HXG-VALUE-MODEL"]),
    entity("ENT-OPERATIONAL-SUPPORT", "Measured operational support", "value", "A property-specific scenario based on verified remote resolutions and avoided dispatches.", evidence_ids=["SRC-HXG-VALUE-MODEL"]),
    entity("ENT-NETWORK-DEPENDENCY", "Network readiness", "risk", "Connectivity, segmentation, capacity, and support conditions.", evidence_ids=["SRC-HXG-FRAMEWORK", "SRC-NIST-IOT-HANDBOOK-2024"]),
    entity("ENT-DATA-GOVERNANCE", "Data governance", "risk", "Purpose, access, security, retention, and jurisdictional controls.", evidence_ids=["SRC-HXG-FRAMEWORK", "SRC-NIST-PMS-2020"]),
    entity("ENT-AVAILABILITY-LIMITS", "Availability and licensing limits", "risk", "Product, region, language, integration, and licensing conditions.", evidence_ids=["SRC-HXG-FRAMEWORK"]),
]


def relationship(rel_id: str, source_id: str, predicate: str, target_id: str, claims_used: list[str], status: str, confidence: float, limitation: str) -> dict:
    return {"schema_version": "1.0.0", "id": rel_id, "source_entity_id": source_id, "predicate": predicate, "target_entity_id": target_id, "supporting_claim_ids": claims_used, "evidence_status": status, "confidence": confidence, "limitations": [limitation]}


outcome_specs = [
    ("HOME", "ENT-FEEL-HOME"), ("CONTROL", "ENT-FEEL-CONTROL"), ("RECOGNIZED", "ENT-FEEL-RECOGNIZED"),
    ("INCLUDED", "ENT-FEEL-INCLUDED"), ("SECURE", "ENT-FEEL-SECURE"), ("SUPPORTED", "ENT-FEEL-SUPPORTED"),
]
capability_specs = [
    ("REL-CASTING-HOME", "ENT-CASTING", "HOME", "ENT-FEEL-HOME"),
    ("REL-IOT-CONTROL", "ENT-IOT-CONTROLS", "CONTROL", "ENT-FEEL-CONTROL"),
    ("REL-PMS-RECOGNIZED", "ENT-PMS-INTEGRATION", "RECOGNIZED", "ENT-FEEL-RECOGNIZED"),
    ("REL-LANGUAGE-INCLUDED", "ENT-LANGUAGE-ACCESS", "INCLUDED", "ENT-FEEL-INCLUDED"),
    ("REL-PRIVACY-SECURE", "ENT-PRIVACY-CONTROLS", "SECURE", "ENT-FEEL-SECURE"),
    ("REL-CONCIERGE-SUPPORTED", "ENT-DIGITAL-CONCIERGE", "SUPPORTED", "ENT-FEEL-SUPPORTED"),
]

relationships = [
    *[relationship(f"REL-HXG-{code}", "ENT-HUMAN-EXPERIENCE", "includes", outcome_id, ["CLM-HXG-PROPOSITION-01"], "inferred", 0.82, "Framework organization, not a measured construct.") for code, outcome_id in outcome_specs],
    *[relationship(rel_id, capability_id, "can-support", outcome_id, [f"CLM-HXG-PATH-{code}-01"], "inferred", 0.80, "Analytical pathway; it does not prove guest preference, perception, or causation.") for rel_id, capability_id, code, outcome_id in capability_specs],
    *[relationship(f"REL-{code}-HUMAN", outcome_id, "contributes-to", "ENT-HUMAN-VALUE", [f"CLM-HXG-PATH-{code}-01"], "inferred", 0.72, "Human value is an evaluation category, not a monetized result.") for code, outcome_id in outcome_specs],
    relationship("REL-DISPLAY-CASTING", "ENT-CONNECTED-DISPLAY", "can-enable", "ENT-CASTING", ["CLM-HXG-PATH-HOME-01"], "inferred", 0.76, "Actual support depends on the selected display, network, and integration."),
    relationship("REL-IOT-ENERGY", "ENT-IOT-CONTROLS", "may-create", "ENT-ENERGY-EFFICIENCY", ["CLM-HXG-VALUE-ENERGY-01"], "scenario", 0.60, "Requires local baseline, attribution, and measurement."),
    relationship("REL-ENERGY-PROPERTY", "ENT-ENERGY-EFFICIENCY", "contributes-to", "ENT-PROPERTY-VALUE", ["CLM-HXG-VALUE-ENERGY-01"], "scenario", 0.60, "No universal savings rate or ROI is claimed."),
    relationship("REL-CONCIERGE-ANCILLARY", "ENT-DIGITAL-CONCIERGE", "may-create", "ENT-ANCILLARY-REVENUE", ["CLM-HXG-VALUE-ANCILLARY-01"], "scenario", 0.60, "Incrementality and contribution margin require property data."),
    relationship("REL-ANCILLARY-PROPERTY", "ENT-ANCILLARY-REVENUE", "contributes-to", "ENT-PROPERTY-VALUE", ["CLM-HXG-VALUE-ANCILLARY-01"], "scenario", 0.60, "No universal conversion rate, uplift, or ROI is claimed."),
    relationship("REL-CLOUD-SUPPORT", "ENT-CLOUD-MANAGEMENT", "may-create", "ENT-OPERATIONAL-SUPPORT", ["CLM-HXG-VALUE-SUPPORT-01"], "scenario", 0.60, "Remote resolution must be verified locally."),
    relationship("REL-SUPPORT-PROPERTY", "ENT-OPERATIONAL-SUPPORT", "contributes-to", "ENT-PROPERTY-VALUE", ["CLM-HXG-VALUE-SUPPORT-01"], "scenario", 0.60, "No universal avoided-cost rate or ROI is claimed."),
    relationship("REL-GUEST-HUMAN", "ENT-GUEST", "evaluates", "ENT-HUMAN-VALUE", ["CLM-HXG-STAKEHOLDERS-01"], "inferred", 0.78, "Guest outcomes require direct validation in the intended population."),
    relationship("REL-OPERATOR-PROPERTY", "ENT-PROPERTY-OPERATOR", "evaluates", "ENT-PROPERTY-VALUE", ["CLM-HXG-STAKEHOLDERS-01"], "inferred", 0.82, "Property value must be measured with local inputs."),
    relationship("REL-BRAND-PROPERTY", "ENT-BRAND", "governs", "ENT-PROPERTY-VALUE", ["CLM-HXG-STAKEHOLDERS-01"], "inferred", 0.76, "Brand and management responsibilities vary."),
    relationship("REL-OEM-ECOSYSTEM", "ENT-OEM-PLATFORM", "participates-in", "ENT-ECOSYSTEM-VALUE", ["CLM-HXG-STAKEHOLDERS-01"], "inferred", 0.76, "No vendor revenue is estimated."),
    relationship("REL-INTEGRATOR-ECOSYSTEM", "ENT-INTEGRATOR", "participates-in", "ENT-ECOSYSTEM-VALUE", ["CLM-HXG-STAKEHOLDERS-01"], "inferred", 0.74, "Commercial terms are deployment-specific."),
    relationship("REL-PARTNERS-ECOSYSTEM", "ENT-TECH-PARTNERS", "participates-in", "ENT-ECOSYSTEM-VALUE", ["CLM-HXG-STAKEHOLDERS-01"], "inferred", 0.74, "No partner revenue is estimated."),
    relationship("REL-NETWORK-CASTING", "ENT-NETWORK-DEPENDENCY", "conditions", "ENT-CASTING", ["CLM-HXG-NETWORK-CONDITION-01"], "inferred", 0.82, "Network readiness must be verified for the deployment."),
    relationship("REL-GOVERNANCE-PMS", "ENT-DATA-GOVERNANCE", "conditions", "ENT-PMS-INTEGRATION", ["CLM-HXG-GOVERNANCE-CONDITION-01"], "inferred", 0.84, "Jurisdiction and implementation determine required controls."),
    relationship("REL-AVAILABILITY-DISPLAY", "ENT-AVAILABILITY-LIMITS", "conditions", "ENT-CONNECTED-DISPLAY", ["CLM-HXG-AVAILABILITY-CONDITION-01"], "inferred", 0.86, "Specific product and licensing availability must be checked."),
]

contradictions = [
    {"schema_version": "1.0.0", "id": "CON-ANALYTICAL-NOT-EMPIRICAL", "title": "Analytical pathway is not guest-preference evidence", "claim_ids": [f"CLM-HXG-PATH-{code}-01" for code, *_ in pathways], "source_ids": ["SRC-HXG-FRAMEWORK"], "assessment": "The six pathways are structured propositions for testing, not empirical findings about what guests prefer.", "resolution": "Use can support language and require direct validation before operational claims.", "severity": "high"},
    {"schema_version": "1.0.0", "id": "CON-FORMULA-NOT-ROI", "title": "Formula is not ROI", "claim_ids": ["CLM-HXG-VALUE-ANCILLARY-01", "CLM-HXG-VALUE-ENERGY-01", "CLM-HXG-VALUE-SUPPORT-01"], "source_ids": ["SRC-HXG-VALUE-MODEL"], "assessment": "A variable-based formula makes assumptions visible but does not supply a result.", "resolution": "Publish no universal rates; require local baselines, attribution, and verification.", "severity": "high"},
    {"schema_version": "1.0.0", "id": "CON-ACCESS-REQUIRES-TEST", "title": "Accessible intent is not conformance", "claim_ids": ["CLM-HXG-PATH-INCLUDED-01", "CLM-W3C-ACCESS-01"], "source_ids": ["SRC-HXG-FRAMEWORK", "SRC-W3C-WCAG22"], "assessment": "An accessibility pathway does not demonstrate that an interface conforms to a standard or works for every user.", "resolution": "Test the actual interface, content, and assistive-technology path.", "severity": "high"},
    {"schema_version": "1.0.0", "id": "CON-SECURITY-NOT-GUARANTEE", "title": "Security controls do not guarantee a secure feeling", "claim_ids": ["CLM-HXG-PATH-SECURE-01", "CLM-NIST-IOT-LIFECYCLE-01", "CLM-NIST-PMS-RISK-01"], "source_ids": ["SRC-HXG-FRAMEWORK", "SRC-NIST-IOT-HANDBOOK-2024", "SRC-NIST-PMS-2020"], "assessment": "Controls can reduce risk, but perception and system security require separate validation.", "resolution": "Keep the pathway inferred and disclose implementation limits.", "severity": "high"},
]

vendor_links = [
    {"schema_version": "1.0.0", "id": "VND-SAM-HOSPITALITY", "publisher": "Samsung Electronics", "page_title": "Hospitality and Hotel Technology & Solutions", "product_name": "Samsung Hospitality Solutions", "url": "https://www.samsung.com/us/business/solutions/industries/hospitality/"},
    {"schema_version": "1.0.0", "id": "VND-SAM-FRAME-HOSPITALITY", "publisher": "Samsung Electronics", "page_title": "Samsung Launches The Frame Hospitality Model at HITEC 2026", "product_name": "The Frame Hospitality", "url": "https://news.samsung.com/us/samsung-launches-frame-hospitality-model-hitec-2026"},
    {"schema_version": "1.0.0", "id": "VND-SAM-SMARTTHINGS-PRO", "publisher": "Samsung Electronics", "page_title": "SmartThings Pro", "product_name": "SmartThings Pro", "url": "https://www.samsung.com/us/business/industries/smartthings-pro/"},
    {"schema_version": "1.0.0", "id": "VND-SAM-LYNK-CLOUD", "publisher": "Samsung Electronics", "page_title": "Samsung LYNK Cloud", "product_name": "LYNK Cloud", "url": "https://www.samsung.com/us/business/solutions/industries/hospitality/lynk-cloud/"},
]

write("sources.json", sources)
write("claims.json", claims)
write("entities.json", entities)
write("relationships.json", relationships)
write("contradictions.json", contradictions)
write("vendor-links.json", vendor_links)
