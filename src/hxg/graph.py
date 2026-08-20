from __future__ import annotations

import html

import networkx as nx

from hxg.io import GRAPH_DIR, PUBLIC_DIR, load_records, write_json
from hxg.models import Claim, Entity, Relationship

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
    "context": "#c7a86b",
}

LAYOUT_SEED = 42
LAYOUT_WIDTH = 1400
LAYOUT_HEIGHT = 1040

CORE_NODE_IDS = {
    "ENT-HUMAN-EXPERIENCE",
    "ENT-FEEL-HOME",
    "ENT-FEEL-CONTROL",
    "ENT-FEEL-RECOGNIZED",
    "ENT-FEEL-INCLUDED",
    "ENT-FEEL-SECURE",
    "ENT-FEEL-SUPPORTED",
    "ENT-CASTING",
    "ENT-IOT-CONTROLS",
    "ENT-PMS-INTEGRATION",
    "ENT-LANGUAGE-ACCESS",
    "ENT-PRIVACY-CONTROLS",
    "ENT-DIGITAL-CONCIERGE",
}

PRIMARY_NODE_IDS = {
    "ENT-HUMAN-EXPERIENCE",
    "ENT-FEEL-HOME",
    "ENT-FEEL-CONTROL",
    "ENT-FEEL-RECOGNIZED",
    "ENT-FEEL-INCLUDED",
    "ENT-FEEL-SECURE",
    "ENT-FEEL-SUPPORTED",
}

# Semantic positions make the map reproducible and legible: the center and six
# outcomes form the first ring, their aligned capabilities form the second ring,
# and the complete explorer occupies separated outer sectors.
SEMANTIC_POSITIONS = {
    "ENT-HUMAN-EXPERIENCE": (700, 520),
    "ENT-FEEL-HOME": (475, 390),
    "ENT-FEEL-CONTROL": (700, 260),
    "ENT-FEEL-RECOGNIZED": (925, 390),
    "ENT-FEEL-INCLUDED": (925, 650),
    "ENT-FEEL-SECURE": (700, 780),
    "ENT-FEEL-SUPPORTED": (475, 650),
    "ENT-CASTING": (300, 290),
    "ENT-IOT-CONTROLS": (700, 60),
    "ENT-PMS-INTEGRATION": (1100, 290),
    "ENT-LANGUAGE-ACCESS": (1100, 750),
    "ENT-PRIVACY-CONTROLS": (700, 980),
    "ENT-DIGITAL-CONCIERGE": (300, 750),
    "ENT-CONNECTED-DISPLAY": (90, 115),
    "ENT-CLOUD-MANAGEMENT": (1310, 115),
    "ENT-SAMSUNG-REFERENCE": (1280, 510),
    "ENT-GUEST": (80, 430),
    "ENT-BRAND": (80, 570),
    "ENT-PROPERTY-OPERATOR": (80, 710),
    "ENT-OEM-PLATFORM": (175, 850),
    "ENT-INTEGRATOR": (175, 215),
    "ENT-TECH-PARTNERS": (175, 980),
    "ENT-HUMAN-VALUE": (1315, 280),
    "ENT-PROPERTY-VALUE": (1315, 640),
    "ENT-ECOSYSTEM-VALUE": (1315, 780),
    "ENT-ENERGY-EFFICIENCY": (1190, 860),
    "ENT-ANCILLARY-REVENUE": (1315, 930),
    "ENT-OPERATIONAL-SUPPORT": (1090, 965),
    "ENT-NETWORK-DEPENDENCY": (360, 985),
    "ENT-DATA-GOVERNANCE": (930, 985),
    "ENT-AVAILABILITY-LIMITS": (1190, 1010),
    "ENT-MACRO-CONTEXT": (1310, 490),
}


def build_graph() -> nx.DiGraph:
    entities = load_records(PUBLIC_DIR / "entities.json", Entity)
    relationships = load_records(PUBLIC_DIR / "relationships.json", Relationship)
    claims = {record.id: record for record in load_records(PUBLIC_DIR / "claims.json", Claim)}

    graph = nx.DiGraph(id="hxg-v0.1.0", label="Hospitality Experience Graph")
    for entity in sorted(entities, key=lambda record: record.id):
        graph.add_node(
            entity.id,
            label=entity.canonical_name,
            entity_type=entity.entity_type,
            description=entity.description,
            outcome=entity.outcome or entity.entity_type,
            color=OUTCOME_COLORS.get(entity.outcome or entity.entity_type, "#8aa2b8"),
            evidence_ids="|".join(entity.evidence_ids),
            core_view=entity.id in CORE_NODE_IDS,
            label_priority="primary" if entity.id in PRIMARY_NODE_IDS else "secondary",
            layout_ring=(
                "center"
                if entity.id == "ENT-HUMAN-EXPERIENCE"
                else "outcome"
                if entity.id in PRIMARY_NODE_IDS
                else "capability"
                if entity.id in CORE_NODE_IDS
                else "outer"
            ),
        )
    for relationship in sorted(relationships, key=lambda record: record.id):
        evidence_ids = sorted(
            {
                evidence_id
                for claim_id in relationship.supporting_claim_ids
                for evidence_id in claims[claim_id].evidence_ids
            }
        )
        graph.add_edge(
            relationship.source_entity_id,
            relationship.target_entity_id,
            id=relationship.id,
            predicate=relationship.predicate,
            evidence_status=relationship.evidence_status.value,
            confidence=relationship.confidence,
            supporting_claim_ids="|".join(relationship.supporting_claim_ids),
            evidence_ids="|".join(evidence_ids),
            limitations="|".join(relationship.limitations),
        )
    return graph


def _apply_layout(graph: nx.DiGraph) -> None:
    """Attach the curated semantic layout to every public graph representation."""
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
        "release": "hxg-v0.1.0",
        "layout": {
            "name": "preset",
            "algorithm": "semantic-rings",
            "seed": LAYOUT_SEED,
            "width": LAYOUT_WIDTH,
            "height": LAYOUT_HEIGHT,
        },
        "elements": {
            "nodes": [
                {
                    "data": {"id": node_id, **attributes},
                    "position": {
                        "x": attributes["layout_x"],
                        "y": attributes["layout_y"],
                    },
                }
                for node_id, attributes in sorted(graph.nodes(data=True))
            ],
            "edges": [
                {"data": {"source": source, "target": target, **attributes}}
                for source, target, attributes in sorted(
                    graph.edges(data=True), key=lambda edge: edge[2]["id"]
                )
            ],
        },
    }


def _svg(graph: nx.DiGraph, width: int = 1600, height: int = 1000) -> str:
    pad_x, pad_y = width * 0.08, height * 0.08
    usable_width, usable_height = width - pad_x * 2, height - pad_y * 2
    points = {
        node_id: (
            pad_x + float(data["layout_x"]) / LAYOUT_WIDTH * usable_width,
            pad_y + float(data["layout_y"]) / LAYOUT_HEIGHT * usable_height,
        )
        for node_id, data in graph.nodes(data=True)
    }
    lines = []
    for source, target, data in graph.edges(data=True):
        x1, y1 = points[source]
        x2, y2 = points[target]
        dash = (
            ""
            if data["evidence_status"] == "direct"
            else ("10 8" if data["evidence_status"] == "inferred" else "2 8")
        )
        lines.append(
            f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" '
            f'stroke="#526879" stroke-width="2" stroke-dasharray="{dash}" marker-end="url(#arrow)" />'
        )
    nodes = []
    for node_id, data in graph.nodes(data=True):
        x, y = points[node_id]
        label = html.escape(data["label"])
        radius = 45 if node_id != "ENT-HUMAN-EXPERIENCE" else 68
        nodes.append(
            f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{radius}" fill="{data["color"]}" stroke="#071827" stroke-width="4" />'
            f'<text x="{x:.1f}" y="{y + radius + 22:.1f}" text-anchor="middle" fill="#f6f1e8" font-size="16" font-weight="650">{label}</text>'
        )
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc">
<title id="title">Hospitality Experience Graph</title>
<desc id="desc">Evidence-linked entities and relationships centered on human experience. Solid edges are direct evidence, dashed edges are supported inferences, and dotted edges are scenarios.</desc>
<rect width="100%" height="100%" fill="#071827" />
<defs><marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse"><path d="M 0 0 L 10 5 L 0 10 z" fill="#526879" /></marker></defs>
{"".join(lines)}
{"".join(nodes)}
</svg>"""


def export_graphs() -> None:
    graph = build_graph()
    _apply_layout(graph)
    GRAPH_DIR.mkdir(parents=True, exist_ok=True)
    nx.write_graphml(graph, GRAPH_DIR / "hospitality-experience-graph.graphml")
    write_json(GRAPH_DIR / "hospitality-experience-graph.json", _cytoscape_json(graph))
    (GRAPH_DIR / "hospitality-experience-map.svg").write_text(_svg(graph), encoding="utf-8")
