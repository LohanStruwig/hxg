from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from urllib.parse import urlparse

import yaml

from hxg.io import ROOT
from hxg.models import RightsBasis, SourceRights, VendorLink

LOGGER = logging.getLogger("hxg.rights")
RIGHTS_PATH = ROOT / "config" / "source-rights.yaml"
DENYLIST_PATH = ROOT / "config" / "blocked-domains.txt"
ALLOWED_INGEST_BASES = {
    RightsBasis.PUBLIC_DOMAIN,
    RightsBasis.CC0,
    RightsBasis.CC_BY,
    RightsBasis.OPEN_LICENSE,
    RightsBasis.EXPLICIT_PERMISSION,
    RightsBasis.ORIGINAL,
}


class RightsRefusal(RuntimeError):
    pass


def normalize_domain(url_or_domain: str) -> str:
    parsed = urlparse(url_or_domain if "://" in url_or_domain else f"https://{url_or_domain}")
    return (parsed.hostname or "").lower().rstrip(".")


def load_rights_records(path: Path = RIGHTS_PATH) -> list[SourceRights]:
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    return [SourceRights.model_validate(record) for record in payload["records"]]


def load_denylist(path: Path = DENYLIST_PATH) -> set[str]:
    return {
        line.strip().lower()
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    }


@dataclass(frozen=True)
class PermissionGateway:
    rights: dict[str, SourceRights]
    denylist: set[str]
    as_of: date
    max_age_days: int = 90

    @classmethod
    def from_config(cls, *, as_of: date | None = None) -> PermissionGateway:
        records = load_rights_records()
        return cls(
            rights={record.record_id: record for record in records},
            denylist=load_denylist(),
            as_of=as_of or date.today(),
        )

    def _refuse(self, record_id: str, reason: str) -> None:
        LOGGER.warning("HXG rights refusal for %s: %s", record_id, reason)
        raise RightsRefusal(f"{record_id}: {reason}")

    def _validate_review(self, record: SourceRights) -> None:
        age = (self.as_of - record.terms_reviewed_at).days
        if age < 0:
            self._refuse(record.record_id, "terms review is dated in the future")
        if age > self.max_age_days or self.as_of > record.review_expires_at:
            self._refuse(record.record_id, "rights review is expired")

    def _validate_domain(self, record_id: str, url: str, record: SourceRights) -> None:
        domain = normalize_domain(url)
        if any(domain == denied or domain.endswith(f".{denied}") for denied in self.denylist):
            self._refuse(record_id, f"domain {domain} is denylisted")
        if domain != record.domain:
            self._refuse(record_id, f"domain {domain} does not match reviewed domain {record.domain}")

    def authorize_source(self, source: dict) -> SourceRights:
        record_id = source["id"]
        record = self.rights.get(record_id)
        if record is None:
            self._refuse(record_id, "no reviewed rights record")
        self._validate_domain(record_id, source["url"], record)
        self._validate_review(record)
        if record.use_mode != "ingest" or record.rights_basis not in ALLOWED_INGEST_BASES:
            self._refuse(record_id, "record is not approved for ingestion")
        if not (
            record.automation_allowed
            and record.ai_processing_allowed
            and record.public_republication_allowed
        ):
            self._refuse(record_id, "required permissions are not all true")
        return record

    def authorize_vendor(self, vendor: VendorLink) -> SourceRights:
        record = self.rights.get(vendor.id)
        if record is None:
            self._refuse(vendor.id, "no reviewed link-only rights record")
        self._validate_domain(vendor.id, str(vendor.url), record)
        self._validate_review(record)
        if record.use_mode != "link-only" or record.rights_basis != RightsBasis.LINK_ONLY:
            self._refuse(vendor.id, "vendor link is not restricted to metadata-only use")
        return record

    def preflight_sources(self, sources: list[dict]) -> dict[str, SourceRights]:
        return {source["id"]: self.authorize_source(source) for source in sources}
