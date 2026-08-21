from __future__ import annotations

from datetime import date
from typing import Any, Literal

import httpx

from hxg.io import (
    PUBLIC_DIR,
    ROOT,
    SEED_DIR,
    canonical_json,
    read_json,
    sha256_file,
    sha256_text,
    write_json,
)
from hxg.models import HumanReviewAction, RightsBasis, RunManifest, VendorLink
from hxg.rights import PermissionGateway, load_rights_records

CACHE_DIR = ROOT / "data" / "cache"


def _source_hash(record: dict[str, Any]) -> str:
    citation = {
        key: record[key]
        for key in ("id", "title", "publisher", "url", "publication_date")
    }
    return sha256_text(canonical_json(citation))


def retrieve_sources(source_records: list[dict[str, Any]], timeout: float = 20.0) -> list[dict[str, Any]]:
    gateway = PermissionGateway.from_config(as_of=date(2026, 8, 20))
    approvals = gateway.preflight_sources(source_records)
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    headers = {"User-Agent": "HXG-Research/0.1 (+https://github.com/LohanStruwig/hxg)"}
    with httpx.Client(headers=headers, follow_redirects=True, timeout=timeout) as client:
        for source in source_records:
            approval = approvals[source["id"]]
            if approval.rights_basis == RightsBasis.ORIGINAL:
                source["content_hash"] = _source_hash(source)
                source["hash_basis"] = "metadata-record"
                source["access_status"] = "accessible"
                continue
            cache_path = CACHE_DIR / f"{source['id']}.html"
            try:
                response = client.get(source["url"])
                response.raise_for_status()
                cache_path.write_bytes(response.content)
                source["content_hash"] = sha256_file(cache_path)
                source["hash_basis"] = "retrieved-content"
                source["access_status"] = "accessible"
            except (httpx.HTTPError, OSError):
                source["content_hash"] = _source_hash(source)
                source["hash_basis"] = "metadata-record"
                source["access_status"] = "limited"
    return source_records


def freeze_seed_release(
    *,
    cutoff: date,
    cost_limit_usd: float,
    retrieve: bool,
) -> RunManifest:
    sources = read_json(SEED_DIR / "sources.json")
    for source in sources:
        source.setdefault("content_hash", _source_hash(source))
        source.setdefault("hash_basis", "metadata-record")
        source.setdefault("access_status", "accessible")
    if retrieve:
        sources = retrieve_sources(sources)

    filenames = (
        "claims.json",
        "entities.json",
        "relationships.json",
        "contradictions.json",
        "vendor-links.json",
    )
    PUBLIC_DIR.mkdir(parents=True, exist_ok=True)
    write_json(PUBLIC_DIR / "sources.json", sources)
    for filename in filenames:
        write_json(PUBLIC_DIR / filename, read_json(SEED_DIR / filename))
    rights_records = load_rights_records()
    write_json(
        PUBLIC_DIR / "source-rights.json",
        [record.model_dump(mode="json") for record in rights_records],
    )
    gateway = PermissionGateway.from_config(as_of=date(2026, 8, 20))
    for vendor in [VendorLink.model_validate(item) for item in read_json(PUBLIC_DIR / "vendor-links.json")]:
        gateway.authorize_vendor(vendor)

    records = {
        filename.removesuffix(".json"): read_json(PUBLIC_DIR / filename)
        for filename in filenames
        if filename != "vendor-links.json"
    }
    geographies = {
        geography
        for source in sources
        for geography in source["geography"]
        if geography != "Global"
    }
    counts = {
        "sources": len(sources),
        "claims": len(records["claims"]),
        "entities": len(records["entities"]),
        "relationships": len(records["relationships"]),
        "contradictions": len(records["contradictions"]),
        "countries": len(geographies),
    }
    config_hash = sha256_file(ROOT / "config" / "research.toml")
    source_hashes = {source["id"]: source["content_hash"] for source in sources}
    manifest = RunManifest(
        id="RUN-HXG-2026-08-20-RIGHTS",
        release_version="0.3.0",
        mode="interactive-codex-seed",
        status="frozen",
        started_at="2026-08-20T09:00:00-05:00",
        frozen_at="2026-08-20T17:00:00-05:00",
        cutoff_date=cutoff,
        research_start_date="2024-01-01",
        model_versions={
            "configured-discovery": "gpt-5.6-terra",
            "configured-extraction": "gpt-5.6-terra",
            "configured-contradiction": "gpt-5.6-sol",
            "configured-final-audit": "gpt-5.6-sol",
            "executed-mode": "deterministic rights-policy rebuild; standalone API run not executed",
        },
        prompt_versions={
            "research-charter": "1.1.0",
            "evidence-extraction": "1.1.0",
            "contradiction-audit": "1.1.0",
            "publisher": "1.1.0",
        },
        configuration_hash=config_hash,
        estimated_cost_usd=0,
        cost_limit_usd=cost_limit_usd,
        source_hashes=source_hashes,
        human_review_actions=[
            HumanReviewAction(
                timestamp="2026-08-20T09:00:00-05:00",
                action="Fail-closed source-rights policy approved",
                rationale="Only reviewed open-license, public information, and original HXG records may enter evidence or model context.",
            ),
            HumanReviewAction(
                timestamp="2026-08-20T16:30:00-05:00",
                action="Rights-clean evidence and publication review",
                rationale="Removed restricted statistics, commercial-research claims, third-party excerpts, and vendor evidence edges.",
                record_ids=["CLM-HXG-PROPOSITION-01", "CLM-HXG-VALUE-ANCILLARY-01"],
            ),
        ],
        generated_counts=counts,
        notes=[
            "This is a deterministic rights-policy rebuild, not an unattended model-backed run.",
            "HXG v0.3.0 is rights-aware and rights-clean under the project source policy; it is not legal clearance.",
            "Vendor links are metadata-only and cannot enter claims, graph relationships, cache, or model context.",
        ],
    )
    write_json(PUBLIC_DIR / "run-manifest.json", manifest)
    return manifest


def run_agent_research(*, cutoff: date, cost_limit_usd: float) -> None:
    try:
        from hxg.agents import run_manager_pipeline
    except ImportError as error:
        raise RuntimeError(
            "Install research dependencies with: pip install -e '.[research]'"
        ) from error
    run_manager_pipeline(cutoff=cutoff, cost_limit_usd=cost_limit_usd)


def run_research(
    *,
    mode: Literal["seed", "agents"],
    cutoff: date,
    cost_limit_usd: float,
    retrieve: bool,
) -> None:
    if mode == "seed":
        freeze_seed_release(cutoff=cutoff, cost_limit_usd=cost_limit_usd, retrieve=retrieve)
        return
    run_agent_research(cutoff=cutoff, cost_limit_usd=cost_limit_usd)
