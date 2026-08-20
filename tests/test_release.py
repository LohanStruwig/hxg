from __future__ import annotations

import hashlib
from pathlib import Path

import networkx as nx
import pymupdf

from hxg.graph import export_graphs
from hxg.io import GRAPH_DIR, PUBLIC_DIR, load_records, read_json
from hxg.models import Claim, Relationship, RunManifest, Source
from hxg.validation import validate_graph_parity, validate_public_release


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_release_integrity() -> None:
    counts = validate_public_release()
    assert counts["sources"] >= 50
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
        "algorithm": "semantic-rings",
        "seed": 42,
        "width": 1400,
        "height": 1040,
    }
    assert all(
        {
            "layout_x",
            "layout_y",
            "core_view",
            "label_priority",
            "layout_ring",
        }
        <= data.keys()
        for _, data in graph.nodes(data=True)
    )
    assert all("position" in node for node in browser_graph["elements"]["nodes"])
    core_nodes = [
        node for node in browser_graph["elements"]["nodes"] if node["data"]["core_view"]
    ]
    core_ids = {node["data"]["id"] for node in core_nodes}
    core_edges = [
        edge
        for edge in browser_graph["elements"]["edges"]
        if edge["data"]["source"] in core_ids and edge["data"]["target"] in core_ids
    ]
    assert len(core_nodes) == 13
    assert len(core_edges) == 12


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
    assert all(len(page.get_images(full=True)) == 1 for page in document)
