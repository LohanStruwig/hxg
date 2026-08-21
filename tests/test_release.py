from __future__ import annotations

import hashlib
from pathlib import Path

import networkx as nx
import pymupdf

from hxg.graph import GUIDED_PATHWAYS, export_graphs
from hxg.io import GRAPH_DIR, PUBLIC_DIR, load_records, read_json
from hxg.models import Claim, EvidenceStatus, Relationship, RunManifest, Source
from hxg.validation import validate_graph_parity, validate_public_release


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_release_integrity() -> None:
    counts = validate_public_release()
    assert counts["sources"] == 10
    assert counts["relationships"] > 0


def test_every_relationship_resolves_to_claim_and_source() -> None:
    sources = {record.id for record in load_records(PUBLIC_DIR / "sources.json", Source)}
    claims = {record.id: record for record in load_records(PUBLIC_DIR / "claims.json", Claim)}
    relationships = load_records(PUBLIC_DIR / "relationships.json", Relationship)
    for relationship in relationships:
        for claim_id in relationship.supporting_claim_ids:
            assert claim_id in claims
            assert set(claims[claim_id].evidence_ids) <= sources


def test_manifest_cutoff() -> None:
    manifest = RunManifest.model_validate(read_json(PUBLIC_DIR / "run-manifest.json"))
    for source in load_records(PUBLIC_DIR / "sources.json", Source):
        assert source.publication_date <= manifest.cutoff_date


def test_graphml_json_parity() -> None:
    validate_graph_parity()


def test_graph_exports_include_preset_layout() -> None:
    export_graphs()
    graph = nx.read_graphml(GRAPH_DIR / "hospitality-experience-graph.graphml")
    browser_graph = read_json(GRAPH_DIR / "hospitality-experience-graph.json")
    assert browser_graph["layout"] == {
        "name": "preset",
        "algorithm": "semantic-groups",
        "seed": 42,
        "width": 1500,
        "height": 1000,
    }
    assert all(
        {
            "layout_x",
            "layout_y",
            "display_label",
            "reader_summary",
            "story_lane",
            "story_layer",
            "label_priority",
        }
        <= data.keys()
        for _, data in graph.nodes(data=True)
    )
    assert all(
        {"display_verb", "relationship_role", "story_lane", "primary_path"}
        <= data.keys()
        for _, _, data in graph.edges(data=True)
    )
    assert all("position" in node for node in browser_graph["elements"]["nodes"])
    assert browser_graph["release"] == "hxg-v0.3.0"
    assert len(browser_graph["guided_pathways"]) == 6
    assert sum(edge["data"]["primary_path"] for edge in browser_graph["elements"]["edges"]) == 6


def test_guided_pathways_are_one_to_one_bounded_inferences() -> None:
    relationships = {
        record.id: record
        for record in load_records(PUBLIC_DIR / "relationships.json", Relationship)
    }
    assert len({pathway.capability_id for pathway in GUIDED_PATHWAYS}) == 6
    assert len({pathway.outcome_id for pathway in GUIDED_PATHWAYS}) == 6
    for pathway in GUIDED_PATHWAYS:
        relationship = relationships[pathway.relationship_id]
        assert relationship.source_entity_id == pathway.capability_id
        assert relationship.target_entity_id == pathway.outcome_id
        assert relationship.predicate == "can-support"
        assert relationship.evidence_status == EvidenceStatus.INFERRED
        assert relationship.limitations


def test_relationship_reclassifications() -> None:
    relationships = {
        record.id: record
        for record in load_records(PUBLIC_DIR / "relationships.json", Relationship)
    }
    expected = {
        "REL-IOT-CONTROL": 0.80,
        "REL-CONCIERGE-SUPPORTED": 0.80,
        "REL-OPERATOR-PROPERTY": 0.82,
    }
    for relationship_id, confidence in expected.items():
        relationship = relationships[relationship_id]
        assert relationship.evidence_status == EvidenceStatus.INFERRED
        assert relationship.confidence == confidence
        assert relationship.limitations


def test_graph_exports_are_deterministic() -> None:
    export_graphs()
    first = {
        path.name: digest(path)
        for path in (
            GRAPH_DIR / "hospitality-experience-graph.graphml",
            GRAPH_DIR / "hospitality-experience-graph.json",
            GRAPH_DIR / "hospitality-experience-map.svg",
        )
    }
    export_graphs()
    second = {path.name: digest(path) for path in GRAPH_DIR.iterdir() if path.name in first}
    assert first == second


def test_flattened_carousel_page_count_and_size() -> None:
    document = pymupdf.open(Path("reports/linkedin-carousel.pdf"))
    assert len(document) == 8
    assert {(page.rect.width, page.rect.height) for page in document} == {(1080.0, 1350.0)}
    assert [len(page.get_images(full=True)) for page in document] == [0, 0, 0, 0, 0, 0, 0, 1]
    assert all(page.get_text().strip() for page in document)
    assert all(page.first_annot is None for page in document)


def test_vector_poster_size_and_metadata() -> None:
    document = pymupdf.open(Path("reports/hxg-poster.pdf"))
    assert len(document) == 1
    assert (document[0].rect.width, document[0].rect.height) == (1800.0, 2700.0)
    assert len(document[0].get_images(full=True)) == 1
    assert "SIX GUIDED PATHWAYS" in document[0].get_text()
    assert document.metadata["author"] == "Hospitality Experience Graph (HXG)"
