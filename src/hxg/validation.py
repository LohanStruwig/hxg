from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

import networkx as nx

from hxg.graph import GUIDED_PATHWAYS
from hxg.io import GRAPH_DIR, PUBLIC_DIR, load_records, read_json
from hxg.models import (
    Claim,
    ClaimClass,
    Contradiction,
    Entity,
    EvidenceStatus,
    Relationship,
    RunManifest,
    Source,
)


class ValidationError(RuntimeError):
    pass


ALLOWED_TRANSITIONS = {
    ("human-experience", "outcome"),
    ("outcome", "value"),
    ("risk", "technology"),
    ("stakeholder", "value"),
    ("technology", "outcome"),
    ("technology", "technology"),
    ("technology", "value"),
    ("value", "context"),
    ("value", "value"),
}
UNSUPPORTED_CAUSAL_PREDICATES = {
    "causes",
    "creates",
    "delivers",
    "drives",
    "guarantees",
    "improves",
    "proves",
}


def _validate_relationship_semantics(
    relationships: list[Relationship],
    entities: list[Entity],
    claims: list[Claim],
) -> None:
    entity_by_id = {record.id: record for record in entities}
    claim_by_id = {record.id: record for record in claims}
    seen_edges: set[tuple[str, str, str]] = set()

    for relationship in relationships:
        source = entity_by_id[relationship.source_entity_id]
        target = entity_by_id[relationship.target_entity_id]
        transition = (source.entity_type, target.entity_type)
        if transition not in ALLOWED_TRANSITIONS:
            raise ValidationError(
                f"{relationship.id} has invalid type transition {transition[0]} -> {transition[1]}"
            )
        edge_key = (
            relationship.source_entity_id,
            relationship.predicate,
            relationship.target_entity_id,
        )
        if edge_key in seen_edges:
            raise ValidationError(f"Duplicate relationship edge: {edge_key}")
        seen_edges.add(edge_key)

        if relationship.predicate in UNSUPPORTED_CAUSAL_PREDICATES:
            raise ValidationError(
                f"{relationship.id} uses unsupported causal wording: {relationship.predicate}"
            )
        if transition == ("technology", "outcome"):
            if relationship.evidence_status == EvidenceStatus.DIRECT:
                raise ValidationError(
                    f"{relationship.id} cannot classify technology-to-outcome evidence as direct"
                )
            if relationship.predicate != "can-support":
                raise ValidationError(
                    f"{relationship.id} must use the non-causal predicate can-support"
                )
        if relationship.evidence_status == EvidenceStatus.SCENARIO:
            supporting = [claim_by_id[claim_id] for claim_id in relationship.supporting_claim_ids]
            if not any(claim.classification == ClaimClass.SCENARIO for claim in supporting):
                raise ValidationError(
                    f"{relationship.id} scenario relationship lacks a modeled-scenario claim"
                )
            if not relationship.limitations:
                raise ValidationError(f"{relationship.id} scenario lacks limitations")

    relationship_by_id = {relationship.id: relationship for relationship in relationships}
    guided_sources: set[str] = set()
    guided_targets: set[str] = set()
    for pathway in GUIDED_PATHWAYS:
        relationship = relationship_by_id.get(pathway.relationship_id)
        if relationship is None:
            raise ValidationError(f"Missing guided pathway {pathway.relationship_id}")
        expected = (pathway.capability_id, "can-support", pathway.outcome_id)
        actual = (
            relationship.source_entity_id,
            relationship.predicate,
            relationship.target_entity_id,
        )
        if actual != expected:
            raise ValidationError(
                f"{pathway.relationship_id} guided mapping mismatch: {actual} != {expected}"
            )
        if relationship.evidence_status != EvidenceStatus.INFERRED:
            raise ValidationError(f"{pathway.relationship_id} must be classified as inferred")
        if not relationship.limitations:
            raise ValidationError(f"{pathway.relationship_id} must disclose limitations")
        if pathway.capability_id in guided_sources or pathway.outcome_id in guided_targets:
            raise ValidationError("Guided pathways must remain one-to-one")
        guided_sources.add(pathway.capability_id)
        guided_targets.add(pathway.outcome_id)


def _unique(records: list, label: str) -> None:
    counts = Counter(record.id for record in records)
    duplicate_ids = sorted(record_id for record_id, count in counts.items() if count > 1)
    if duplicate_ids:
        raise ValidationError(f"Duplicate {label} IDs: {', '.join(duplicate_ids)}")


def validate_public_release(public_dir: Path = PUBLIC_DIR) -> dict[str, int]:
    sources = load_records(public_dir / "sources.json", Source)
    claims = load_records(public_dir / "claims.json", Claim)
    entities = load_records(public_dir / "entities.json", Entity)
    relationships = load_records(public_dir / "relationships.json", Relationship)
    contradictions = load_records(public_dir / "contradictions.json", Contradiction)
    manifest = RunManifest.model_validate(read_json(public_dir / "run-manifest.json"))

    for records, label in (
        (sources, "source"),
        (claims, "claim"),
        (entities, "entity"),
        (relationships, "relationship"),
        (contradictions, "contradiction"),
    ):
        _unique(records, label)

    source_ids = {record.id for record in sources}
    claim_ids = {record.id for record in claims}
    entity_ids = {record.id for record in entities}

    for source in sources:
        if source.publication_date > manifest.cutoff_date:
            raise ValidationError(f"{source.id} is newer than cutoff {manifest.cutoff_date}")
        if source.publication_date < manifest.research_start_date and not source.historical_context:
            raise ValidationError(f"{source.id} predates research window without historical label")

    for claim in claims:
        missing = set(claim.evidence_ids) - source_ids
        if missing:
            raise ValidationError(f"{claim.id} has missing sources: {sorted(missing)}")
        if claim.stakeholder == "guest-behavior":
            independent = [
                source
                for source in sources
                if source.id in claim.evidence_ids
                and source.authority_tier.value == "independent-research"
            ]
            if not independent:
                raise ValidationError(f"Guest behavior claim {claim.id} lacks independent evidence")

    for relationship in relationships:
        missing_entities = {
            relationship.source_entity_id,
            relationship.target_entity_id,
        } - entity_ids
        if missing_entities:
            raise ValidationError(
                f"{relationship.id} has missing entities: {sorted(missing_entities)}"
            )
        missing_claims = set(relationship.supporting_claim_ids) - claim_ids
        if missing_claims:
            raise ValidationError(f"{relationship.id} has missing claims: {sorted(missing_claims)}")
        relationship_source_ids = {
            source_id
            for claim in claims
            if claim.id in relationship.supporting_claim_ids
            for source_id in claim.evidence_ids
        }
        if not relationship_source_ids:
            raise ValidationError(f"{relationship.id} does not resolve to a source")

    _validate_relationship_semantics(relationships, entities, claims)

    for contradiction in contradictions:
        if set(contradiction.claim_ids) - claim_ids:
            raise ValidationError(f"{contradiction.id} references missing claims")
        if set(contradiction.source_ids) - source_ids:
            raise ValidationError(f"{contradiction.id} references missing sources")

    counts = {
        "sources": len(sources),
        "claims": len(claims),
        "entities": len(entities),
        "relationships": len(relationships),
        "contradictions": len(contradictions),
        "countries": len(
            {geo for source in sources for geo in source.geography if geo != "Global"}
        ),
    }
    if counts["sources"] < 50:
        raise ValidationError("Release requires at least 50 source records")
    if manifest.generated_counts != counts:
        raise ValidationError(
            f"Manifest counts do not match records: {manifest.generated_counts} != {counts}"
        )
    return counts


def validate_graph_parity(graphml_path: Path | None = None, json_path: Path | None = None) -> None:
    graphml_path = graphml_path or GRAPH_DIR / "hospitality-experience-graph.graphml"
    json_path = json_path or GRAPH_DIR / "hospitality-experience-graph.json"
    graph = nx.read_graphml(graphml_path)
    browser_graph = json.loads(json_path.read_text(encoding="utf-8"))
    json_nodes = {node["data"]["id"] for node in browser_graph["elements"]["nodes"]}
    json_edges = {edge["data"]["id"] for edge in browser_graph["elements"]["edges"]}
    if set(graph.nodes) != json_nodes:
        raise ValidationError("GraphML/JSON node parity failed")
    if set(graph.edges) != {
        (edge["data"]["source"], edge["data"]["target"])
        for edge in browser_graph["elements"]["edges"]
    }:
        raise ValidationError("GraphML/JSON edge parity failed")
    if {data["id"] for _, _, data in graph.edges(data=True)} != json_edges:
        raise ValidationError("GraphML/JSON relationship ID parity failed")
    for node in browser_graph["elements"]["nodes"]:
        node_id = node["data"]["id"]
        for field in (
            "display_label",
            "reader_summary",
            "story_lane",
            "story_layer",
            "label_priority",
        ):
            if graph.nodes[node_id].get(field) != node["data"].get(field):
                raise ValidationError(f"GraphML/JSON {field} parity failed for {node_id}")
        position = node.get("position", {})
        if "x" not in position or "y" not in position:
            raise ValidationError(f"Browser graph node {node_id} has no preset position")
        if "layout_x" not in graph.nodes[node_id] or "layout_y" not in graph.nodes[node_id]:
            raise ValidationError(f"GraphML node {node_id} has no layout coordinates")
        if abs(float(graph.nodes[node_id]["layout_x"]) - float(position["x"])) > 0.0001:
            raise ValidationError(f"GraphML/JSON X coordinate parity failed for {node_id}")
        if abs(float(graph.nodes[node_id]["layout_y"]) - float(position["y"])) > 0.0001:
            raise ValidationError(f"GraphML/JSON Y coordinate parity failed for {node_id}")
    graphml_edges = {data["id"]: data for _, _, data in graph.edges(data=True)}
    for edge in browser_graph["elements"]["edges"]:
        edge_id = edge["data"]["id"]
        for field in (
            "display_verb",
            "relationship_role",
            "story_lane",
            "primary_path",
        ):
            if graphml_edges[edge_id].get(field) != edge["data"].get(field):
                raise ValidationError(f"GraphML/JSON {field} parity failed for {edge_id}")
    guided = browser_graph.get("guided_pathways", [])
    if len(guided) != 6:
        raise ValidationError("Browser graph must expose exactly six guided pathways")
    if {item["relationship_id"] for item in guided} != {
        pathway.relationship_id for pathway in GUIDED_PATHWAYS
    }:
        raise ValidationError("Browser graph guided-pathway parity failed")
