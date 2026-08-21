from __future__ import annotations

import html
from dataclasses import dataclass

import networkx as nx

from hxg.io import GRAPH_DIR, PUBLIC_DIR, load_records, write_json
from hxg.models import Claim, Entity, Relationship

RELEASE = "hxg-v0.3.0"
LAYOUT_SEED = 42
LAYOUT_WIDTH = 1500
LAYOUT_HEIGHT = 1000

OUTCOME_COLORS = {
    "human-experience": "#f6f1e8",
    "feel-at-home": "#4cb3ff",
    "feel-in-control": "#78d35d",
    "feel-recognized": "#f4bd32",
    "feel-included": "#a986ef",
    "feel-secure": "#49c5ca",
    "feel-supported": "#f29138",
    "stakeholder": "#8aa2b8",
    "value": "#57d6a7",
    "technology": "#7994ff",
    "risk": "#c7a86b",
    "context": "#c7a86b",
}


@dataclass(frozen=True)
class GuidedPathway:
    lane: str
    relationship_id: str
    capability_id: str
    capability_label: str
    outcome_id: str
    outcome_label: str
    summary: str


GUIDED_PATHWAYS = (
    GuidedPathway("home", "REL-CASTING-HOME", "ENT-CASTING", "Cast from your device", "ENT-FEEL-HOME", "Feel at home", "Familiar personal content can reduce friction in the room."),
    GuidedPathway("control", "REL-IOT-CONTROL", "ENT-IOT-CONTROLS", "Control room settings", "ENT-FEEL-CONTROL", "Feel in control", "Room controls can make comfort settings easier to adjust."),
    GuidedPathway("recognized", "REL-PMS-RECOGNIZED", "ENT-PMS-INTEGRATION", "Connect stay context", "ENT-FEEL-RECOGNIZED", "Feel recognized", "Connected stay context can make information and services more relevant."),
    GuidedPathway("included", "REL-LANGUAGE-INCLUDED", "ENT-LANGUAGE-ACCESS", "Present content accessibly", "ENT-FEEL-INCLUDED", "Feel included", "Language and access features can reduce barriers to using content."),
    GuidedPathway("secure", "REL-PRIVACY-SECURE", "ENT-PRIVACY-CONTROLS", "Protect sessions and data", "ENT-FEEL-SECURE", "Feel secure", "Session isolation and managed data lifecycles can reduce privacy risk."),
    GuidedPathway("supported", "REL-CONCIERGE-SUPPORTED", "ENT-DIGITAL-CONCIERGE", "Request services and help", "ENT-FEEL-SUPPORTED", "Feel supported", "Digital service channels can make requests and help easier to reach."),
)

GUIDED_BY_NODE = {node_id: pathway for pathway in GUIDED_PATHWAYS for node_id in (pathway.capability_id, pathway.outcome_id)}
GUIDED_BY_RELATIONSHIP = {pathway.relationship_id: pathway for pathway in GUIDED_PATHWAYS}
DISPLAY_LABELS = {pathway.capability_id: pathway.capability_label for pathway in GUIDED_PATHWAYS} | {pathway.outcome_id: pathway.outcome_label for pathway in GUIDED_PATHWAYS}
READER_SUMMARIES = {
    "ENT-HUMAN-EXPERIENCE": "The human outcome framework that organizes the research.",
    **{pathway.capability_id: pathway.summary for pathway in GUIDED_PATHWAYS},
    **{pathway.outcome_id: f"Guest outcome: {pathway.outcome_label.lower()}." for pathway in GUIDED_PATHWAYS},
}

# Stable coordinates are publication data, not a force-layout seed. They place
# complete-graph entities in separated semantic columns for deterministic exports.
SEMANTIC_POSITIONS = {
    "ENT-HUMAN-EXPERIENCE": (750, 65),
    "ENT-GUEST": (100, 170), "ENT-PROPERTY-OPERATOR": (100, 310), "ENT-BRAND": (100, 450),
    "ENT-OEM-PLATFORM": (100, 590), "ENT-INTEGRATOR": (100, 730), "ENT-TECH-PARTNERS": (100, 870),
    "ENT-CONNECTED-DISPLAY": (405, 115), "ENT-CASTING": (405, 215), "ENT-IOT-CONTROLS": (405, 315),
    "ENT-PMS-INTEGRATION": (405, 415), "ENT-LANGUAGE-ACCESS": (405, 515), "ENT-PRIVACY-CONTROLS": (405, 615),
    "ENT-DIGITAL-CONCIERGE": (405, 715), "ENT-CLOUD-MANAGEMENT": (405, 815),
    "ENT-FEEL-HOME": (750, 215), "ENT-FEEL-CONTROL": (750, 335), "ENT-FEEL-RECOGNIZED": (750, 455),
    "ENT-FEEL-INCLUDED": (750, 575), "ENT-FEEL-SECURE": (750, 695), "ENT-FEEL-SUPPORTED": (750, 815),
    "ENT-HUMAN-VALUE": (1090, 175), "ENT-PROPERTY-VALUE": (1090, 315), "ENT-ECOSYSTEM-VALUE": (1090, 455),
    "ENT-ENERGY-EFFICIENCY": (1090, 595), "ENT-ANCILLARY-REVENUE": (1090, 735), "ENT-OPERATIONAL-SUPPORT": (1090, 875),
    "ENT-NETWORK-DEPENDENCY": (1380, 255), "ENT-DATA-GOVERNANCE": (1380, 455),
    "ENT-AVAILABILITY-LIMITS": (1380, 655),
}


def _story_layer(entity: Entity) -> str:
    return {
        "human-experience": "framework", "outcome": "guest-outcome", "technology": "connected-system",
        "stakeholder": "stakeholder", "value": "value-pathway", "risk": "condition-context", "context": "condition-context",
    }[entity.entity_type]


def _edge_role(relationship: Relationship, entities: dict[str, Entity]) -> str:
    if relationship.id in GUIDED_BY_RELATIONSHIP:
        return "guest-pathway"
    source = entities[relationship.source_entity_id]
    target = entities[relationship.target_entity_id]
    if source.entity_type == "risk":
        return "condition"
    if relationship.evidence_status.value == "scenario":
        return "modeled-scenario"
    if "value" in {source.entity_type, target.entity_type}:
        return "value-pathway"
    if source.entity_type == target.entity_type == "technology":
        return "system-connection"
    return "research-relationship"


def build_graph() -> nx.DiGraph:
    entity_records = load_records(PUBLIC_DIR / "entities.json", Entity)
    relationship_records = load_records(PUBLIC_DIR / "relationships.json", Relationship)
    claims = {record.id: record for record in load_records(PUBLIC_DIR / "claims.json", Claim)}
    entities = {record.id: record for record in entity_records}
    graph = nx.DiGraph(id=RELEASE, label="Hospitality Experience Graph")
    for entity in sorted(entity_records, key=lambda record: record.id):
        guided = GUIDED_BY_NODE.get(entity.id)
        graph.add_node(
            entity.id,
            label=entity.canonical_name,
            display_label=DISPLAY_LABELS.get(entity.id, entity.canonical_name),
            reader_summary=READER_SUMMARIES.get(entity.id, entity.description),
            entity_type=entity.entity_type,
            description=entity.description,
            outcome=entity.outcome or entity.entity_type,
            color=OUTCOME_COLORS.get(entity.outcome or entity.entity_type, "#8aa2b8"),
            evidence_ids="|".join(entity.evidence_ids),
            story_lane=guided.lane if guided else "shared",
            story_layer=_story_layer(entity),
            label_priority="primary" if entity.id == "ENT-HUMAN-EXPERIENCE" or entity.entity_type == "outcome" else "secondary" if guided else "tertiary",
        )
    for relationship in sorted(relationship_records, key=lambda record: record.id):
        evidence_ids = sorted({evidence_id for claim_id in relationship.supporting_claim_ids for evidence_id in claims[claim_id].evidence_ids})
        guided = GUIDED_BY_RELATIONSHIP.get(relationship.id)
        graph.add_edge(
            relationship.source_entity_id,
            relationship.target_entity_id,
            id=relationship.id,
            predicate=relationship.predicate,
            display_verb="can support" if guided else relationship.predicate.replace("-", " "),
            relationship_role=_edge_role(relationship, entities),
            story_lane=guided.lane if guided else "shared",
            primary_path=bool(guided),
            evidence_status=relationship.evidence_status.value,
            confidence=relationship.confidence,
            supporting_claim_ids="|".join(relationship.supporting_claim_ids),
            evidence_ids="|".join(evidence_ids),
            limitations="|".join(relationship.limitations),
        )
    return graph


def _apply_layout(graph: nx.DiGraph) -> None:
    if set(graph.nodes) != set(SEMANTIC_POSITIONS):
        missing = sorted(set(graph.nodes) - set(SEMANTIC_POSITIONS))
        extra = sorted(set(SEMANTIC_POSITIONS) - set(graph.nodes))
        raise ValueError(f"Semantic layout mismatch; missing={missing}, extra={extra}")
    for node_id in sorted(graph.nodes):
        x, y = SEMANTIC_POSITIONS[node_id]
        graph.nodes[node_id]["layout_x"] = float(x)
        graph.nodes[node_id]["layout_y"] = float(y)


def _cytoscape_json(graph: nx.DiGraph) -> dict:
    return {
        "schema_version": "1.0.0",
        "release": RELEASE,
        "layout": {"name": "preset", "algorithm": "semantic-groups", "seed": LAYOUT_SEED, "width": LAYOUT_WIDTH, "height": LAYOUT_HEIGHT},
        "guided_pathways": [
            {"story_lane": pathway.lane, "relationship_id": pathway.relationship_id, "capability_id": pathway.capability_id, "outcome_id": pathway.outcome_id}
            for pathway in GUIDED_PATHWAYS
        ],
        "elements": {
            "nodes": [
                {"data": {"id": node_id, **attributes}, "position": {"x": attributes["layout_x"], "y": attributes["layout_y"]}}
                for node_id, attributes in sorted(graph.nodes(data=True))
            ],
            "edges": [
                {"data": {"source": source, "target": target, **attributes}}
                for source, target, attributes in sorted(graph.edges(data=True), key=lambda edge: edge[2]["id"])
            ],
        },
    }


def _svg(graph: nx.DiGraph, width: int = 1600, height: int = 1180) -> str:
    node_data = dict(graph.nodes(data=True))
    edge_data = {data["id"]: data for _, _, data in graph.edges(data=True)}
    rows: list[str] = []
    for index, pathway in enumerate(GUIDED_PATHWAYS):
        y = 215 + index * 145
        capability = node_data[pathway.capability_id]
        outcome = node_data[pathway.outcome_id]
        edge = edge_data[pathway.relationship_id]
        color = outcome["color"]
        rows.append(
            f'<g data-relationship="{pathway.relationship_id}">'
            f'<rect x="90" y="{y - 48}" width="540" height="96" rx="8" fill="#0b2134" stroke="#315069" />'
            f'<circle cx="145" cy="{y}" r="22" fill="{color}" />'
            f'<text x="188" y="{y + 8}" fill="#f6f1e8" font-size="25" font-weight="700">{html.escape(capability["display_label"])}</text>'
            f'<line x1="670" y1="{y}" x2="910" y2="{y}" stroke="#9eb0bc" stroke-width="3" stroke-dasharray="12 9" marker-end="url(#arrow)" />'
            f'<text x="790" y="{y - 16}" text-anchor="middle" fill="#b8cad6" font-size="18">{html.escape(edge["display_verb"])}</text>'
            f'<rect x="950" y="{y - 48}" width="560" height="96" rx="8" fill="#0b2134" stroke="{color}" />'
            f'<circle cx="1005" cy="{y}" r="22" fill="{color}" />'
            f'<text x="1048" y="{y + 8}" fill="#f6f1e8" font-size="25" font-weight="700">{html.escape(outcome["display_label"])}</text>'
            "</g>"
        )
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc">
<title id="title">HXG guided guest pathways</title>
<desc id="desc">Six evidence-linked capability-to-outcome pathways. Each capability can support, but does not prove, a guest outcome.</desc>
<rect width="100%" height="100%" fill="#061522" />
<defs><marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto"><path d="M 0 0 L 10 5 L 0 10 z" fill="#9eb0bc" /></marker></defs>
<text x="90" y="76" fill="#f6f1e8" font-size="42" font-weight="750">Six guided guest pathways</text>
<text x="90" y="118" fill="#9eb0bc" font-size="21">Capabilities can support guest outcomes; they do not prove perception or value.</text>
<text x="90" y="158" fill="#4cc4d9" font-size="16" font-weight="700">CAPABILITY</text>
<text x="950" y="158" fill="#4cc4d9" font-size="16" font-weight="700">GUEST OUTCOME</text>
{''.join(rows)}
<text x="90" y="1120" fill="#6f8492" font-size="16">HXG v0.3.0 · Evidence cutoff 19 August 2026 · Full {len(graph.nodes)}-node graph available in GraphML and JSON.</text>
</svg>'''


def export_graphs() -> None:
    graph = build_graph()
    _apply_layout(graph)
    GRAPH_DIR.mkdir(parents=True, exist_ok=True)
    nx.write_graphml(graph, GRAPH_DIR / "hospitality-experience-graph.graphml")
    write_json(GRAPH_DIR / "hospitality-experience-graph.json", _cytoscape_json(graph))
    (GRAPH_DIR / "hospitality-experience-map.svg").write_text(_svg(graph), encoding="utf-8")
