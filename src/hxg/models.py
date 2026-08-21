from __future__ import annotations

from datetime import date, datetime
from enum import StrEnum
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, model_validator


class Record(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    schema_version: Literal["1.0.0"] = "1.0.0"


class AuthorityTier(StrEnum):
    PRIMARY = "primary"
    INDEPENDENT = "independent-research"
    STANDARD = "standard-or-government"
    VENDOR = "vendor-primary"
    HISTORICAL = "historical-context"


class ClaimClass(StrEnum):
    FACT = "fact"
    INFERENCE = "supported-inference"
    SCENARIO = "modeled-scenario"


class EvidenceStatus(StrEnum):
    DIRECT = "direct"
    INFERRED = "inferred"
    SCENARIO = "scenario"


class ReviewState(StrEnum):
    AUDITED = "audited"
    VENDOR = "vendor-stated"
    LIMITED = "limited"
    DRAFT = "draft"


class Source(Record):
    id: str = Field(pattern=r"^SRC-[A-Z0-9-]+$")
    title: str
    publisher: str
    url: HttpUrl
    publication_date: date
    accessed_date: date
    geography: list[str]
    authority_tier: AuthorityTier
    licensing_status: str
    content_hash: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    hash_basis: Literal["retrieved-content", "metadata-record"]
    access_status: Literal["accessible", "limited", "archived"]
    historical_context: bool = False
    notes: str | None = None


class RightsBasis(StrEnum):
    PUBLIC_DOMAIN = "public_domain"
    CC0 = "cc0"
    CC_BY = "cc_by"
    OPEN_LICENSE = "other_explicit_open_license"
    EXPLICIT_PERMISSION = "explicit_machine_access_and_reuse_permission"
    ORIGINAL = "original_hxg_content"
    LINK_ONLY = "metadata_link_only"


class SourceRights(Record):
    id: str = Field(pattern=r"^RGT-[A-Z0-9-]+$")
    record_id: str = Field(pattern=r"^(SRC|VND)-[A-Z0-9-]+$")
    use_mode: Literal["ingest", "link-only"]
    domain: str
    rights_basis: RightsBasis
    automation_allowed: bool
    ai_processing_allowed: bool
    public_republication_allowed: bool
    license_name: str
    license_url: HttpUrl
    terms_url: HttpUrl
    attribution_required: bool
    attribution_text: str
    excerpts_allowed: bool
    excerpt_limit_words: int = Field(ge=0)
    terms_reviewed_at: date
    review_expires_at: date
    reviewer: str
    notes: str | None = None

    @model_validator(mode="after")
    def validate_use_mode(self) -> SourceRights:
        if self.use_mode == "ingest":
            if self.rights_basis == RightsBasis.LINK_ONLY:
                raise ValueError("Ingest records cannot use link-only rights")
            if not (
                self.automation_allowed
                and self.ai_processing_allowed
                and self.public_republication_allowed
            ):
                raise ValueError("Ingest records require all processing permissions")
        else:
            if self.rights_basis != RightsBasis.LINK_ONLY:
                raise ValueError("Link-only records must use metadata_link_only")
            if self.automation_allowed or self.ai_processing_allowed:
                raise ValueError("Link-only records cannot authorize retrieval or AI processing")
        return self


class VendorLink(Record):
    id: str = Field(pattern=r"^VND-[A-Z0-9-]+$")
    publisher: str
    page_title: str
    product_name: str
    url: HttpUrl


class Claim(Record):
    id: str = Field(pattern=r"^CLM-[A-Z0-9-]+$")
    text: str
    classification: ClaimClass
    evidence_ids: list[str] = Field(min_length=1)
    metric: str | None = None
    value: float | None = None
    unit: str | None = None
    period: str | None = None
    geography: list[str]
    confidence: float = Field(ge=0, le=1)
    limitations: list[str]
    review_state: ReviewState
    excerpt: str = Field(max_length=320)
    locator: str
    outcome: str | None = None
    stakeholder: str | None = None
    value_type: str | None = None

    @model_validator(mode="after")
    def scenario_requires_limitations(self) -> Claim:
        if self.classification == ClaimClass.SCENARIO and not self.limitations:
            raise ValueError("Modeled scenarios must disclose limitations")
        return self


class Entity(Record):
    id: str = Field(pattern=r"^ENT-[A-Z0-9-]+$")
    canonical_name: str
    aliases: list[str] = []
    entity_type: str
    description: str
    outcome: str | None = None
    evidence_ids: list[str] = []


class Relationship(Record):
    id: str = Field(pattern=r"^REL-[A-Z0-9-]+$")
    source_entity_id: str
    predicate: str
    target_entity_id: str
    supporting_claim_ids: list[str] = Field(min_length=1)
    evidence_status: EvidenceStatus
    confidence: float = Field(ge=0, le=1)
    limitations: list[str] = []


class Contradiction(Record):
    id: str = Field(pattern=r"^CON-[A-Z0-9-]+$")
    title: str
    claim_ids: list[str]
    source_ids: list[str]
    assessment: str
    resolution: str
    severity: Literal["low", "medium", "high"]


class HumanReviewAction(Record):
    timestamp: datetime
    action: str
    rationale: str
    record_ids: list[str] = []


class RunManifest(Record):
    id: str
    release_version: str
    mode: Literal["interactive-codex-seed", "agents"]
    status: Literal["draft", "frozen"]
    started_at: datetime
    frozen_at: datetime | None
    cutoff_date: date
    research_start_date: date
    model_versions: dict[str, str]
    prompt_versions: dict[str, str]
    configuration_hash: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    estimated_cost_usd: float = Field(ge=0)
    cost_limit_usd: float = Field(gt=0)
    source_hashes: dict[str, str]
    human_review_actions: list[HumanReviewAction]
    generated_counts: dict[str, int]
    notes: list[str]
    output_hashes: dict[str, str] = {}


PUBLIC_MODELS: tuple[type[Record], ...] = (
    Source,
    SourceRights,
    VendorLink,
    Claim,
    Entity,
    Relationship,
    Contradiction,
    RunManifest,
)


def model_schema(model: type[Record]) -> dict[str, Any]:
    schema = model.model_json_schema()
    schema["$id"] = f"https://lohanstruwig.github.io/hxg/schemas/v1/{model.__name__.lower()}.schema.json"
    return schema
