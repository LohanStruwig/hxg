from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest

from hxg.io import PUBLIC_DIR, load_records, read_json
from hxg.models import Claim, Relationship, Source, SourceRights, VendorLink
from hxg.research import retrieve_sources
from hxg.rights import PermissionGateway, RightsRefusal


def test_every_public_record_has_current_rights() -> None:
    sources = load_records(PUBLIC_DIR / "sources.json", Source)
    vendors = load_records(PUBLIC_DIR / "vendor-links.json", VendorLink)
    rights = load_records(PUBLIC_DIR / "source-rights.json", SourceRights)
    assert {record.record_id for record in rights} == {
        *(source.id for source in sources),
        *(vendor.id for vendor in vendors),
    }
    gateway = PermissionGateway.from_config(as_of=date(2026, 8, 20))
    for source in sources:
        gateway.authorize_source(source.model_dump(mode="json"))
    for vendor in vendors:
        gateway.authorize_vendor(vendor)


@pytest.mark.parametrize(
    ("record_id", "url"),
    [
        ("SRC-JDP-BLOCKED-TEST", "https://www.jdpower.com/example"),
        ("SRC-UNKNOWN-BLOCKED-TEST", "https://unknown-source.example/research"),
    ],
)
def test_unknown_or_denied_source_fails_before_http_client(
    monkeypatch: pytest.MonkeyPatch,
    record_id: str,
    url: str,
) -> None:
    created = False

    def forbidden_client(*args, **kwargs):
        nonlocal created
        created = True
        raise AssertionError("HTTP client must not be created")

    monkeypatch.setattr("hxg.research.httpx.Client", forbidden_client)
    candidate = {
        "id": record_id,
        "title": "Blocked",
        "publisher": "Blocked",
        "url": url,
        "publication_date": "2026-01-01",
    }
    with pytest.raises(RightsRefusal):
        retrieve_sources([candidate])
    assert created is False


def test_expired_rights_fail_closed() -> None:
    source = load_records(PUBLIC_DIR / "sources.json", Source)[0]
    gateway = PermissionGateway.from_config(as_of=date(2026, 11, 19))
    with pytest.raises(RightsRefusal, match="expired"):
        gateway.authorize_source(source.model_dump(mode="json"))


def test_vendor_links_never_enter_evidence_graph_or_cache() -> None:
    vendor_ids = {record.id for record in load_records(PUBLIC_DIR / "vendor-links.json", VendorLink)}
    claims = load_records(PUBLIC_DIR / "claims.json", Claim)
    relationships = load_records(PUBLIC_DIR / "relationships.json", Relationship)
    assert all(not (set(claim.evidence_ids) & vendor_ids) for claim in claims)
    serialized_relationships = str([record.model_dump(mode="json") for record in relationships])
    assert all(vendor_id not in serialized_relationships for vendor_id in vendor_ids)
    cache_names = {path.stem for path in Path("data/cache").glob("*") if path.is_file()}
    assert not (cache_names & vendor_ids)
    graph_text = Path("graphs/hospitality-experience-graph.graphml").read_text(encoding="utf-8")
    assert all(vendor_id not in graph_text for vendor_id in vendor_ids)


def test_public_claims_have_no_excerpts() -> None:
    assert all(not claim["excerpt"] for claim in read_json(PUBLIC_DIR / "claims.json"))
