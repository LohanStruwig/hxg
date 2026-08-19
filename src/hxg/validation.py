from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

import networkx as nx

from hxg.io import GRAPH_DIR, PUBLIC_DIR, load_records, read_json
from hxg.models import Claim, Contradiction, Entity, Relationship, RunManifest, Source


class ValidationError(RuntimeError):
    pass


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
                source for source in sources
                if source.id in claim.evidence_ids and source.authority_tier.value == "independent-research"
            ]
            if not independent:
                raise ValidationError(f"Guest behavior claim {claim.id} lacks independent evidence")

    for relationship in relationships:
        missing_entities = {
            relationship.source_entity_id,
            relationship.target_entity_id,
        } - entity_ids
        if missing_entities:
            raise ValidationError(f"{relationship.id} has missing entities: {sorted(missing_entities)}")
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
        "countries": len({geo for source in sources for geo in source.geography if geo != "Global"}),
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
