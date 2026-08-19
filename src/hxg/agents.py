from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import date

from agents import Agent, ModelSettings, RunConfig, Runner


@dataclass
class ResearchBudget:
    cost_limit_usd: float
    estimated_cost_usd: float = 0

    def check(self) -> None:
        if self.estimated_cost_usd >= self.cost_limit_usd:
            raise RuntimeError("Explicit HXG research cost limit reached")


DISCOVERY_MODEL = os.getenv("HXG_DISCOVERY_MODEL", "gpt-5.6-terra")
AUDIT_MODEL = os.getenv("HXG_AUDIT_MODEL", "gpt-5.6-sol")


def _specialist(name: str, instructions: str, *, audit: bool = False) -> Agent:
    return Agent(
        name=name,
        model=AUDIT_MODEL if audit else DISCOVERY_MODEL,
        instructions=instructions,
        model_settings=ModelSettings(temperature=0),
    )


source_discovery = _specialist(
    "Source discovery",
    "Find qualifying primary, independent, government, and standards sources. Return URLs and metadata only. Enforce the research date window and disclose vendor provenance.",
)
perspective_research = _specialist(
    "Stakeholder perspectives",
    "Research guest, operator, IT, revenue, integrator, sustainability, privacy, and accessibility perspectives independently. Never treat synthetic personas as evidence.",
)
evidence_extraction = _specialist(
    "Evidence extraction",
    "Extract atomic claims, short excerpts, locators, metrics, periods, geography, limitations, and fact/inference/scenario classes into the HXG v1 schema.",
)
entity_resolution = _specialist(
    "Entity resolution",
    "Resolve aliases to canonical products, platforms, stakeholders, outcomes, and value mechanisms. Preserve ambiguous matches for review.",
)
graph_construction = _specialist(
    "Graph construction",
    "Propose directed entity relationships. Every relationship must name supporting claim IDs and use direct, inferred, or scenario status.",
)
contradiction_review = _specialist(
    "Contradiction review",
    "Actively search for outdated claims, availability limitations, privacy concerns, accessibility gaps, network dependencies, vendor lock-in, licensing costs, and unsupported causal language.",
    audit=True,
)
citation_audit = _specialist(
    "Citation audit",
    "Reject every statistic, relationship, and publication statement that cannot resolve through a claim to an accessible source. Recheck dates and locators.",
    audit=True,
)
publisher = _specialist(
    "Publisher",
    "Create concise public copy from audited records only. Keep Samsung as a vendor-stated reference architecture and never type publication counts manually.",
    audit=True,
)


def run_manager_pipeline(*, cutoff: date, cost_limit_usd: float) -> None:
    if not os.getenv("OPENAI_API_KEY"):
        raise RuntimeError("OPENAI_API_KEY is required for model-backed research")

    budget = ResearchBudget(cost_limit_usd=cost_limit_usd)
    budget.check()
    manager = Agent(
        name="HXG research manager",
        model=AUDIT_MODEL,
        instructions=(
            "You own the complete HXG research run. Call bounded specialists as tools, retain final responsibility, "
            f"enforce the cutoff {cutoff.isoformat()}, stop before the explicit cost limit, and freeze only audited schema-valid outputs. "
            "Use Microsoft GraphRAG after extraction for entity/relationship/community proposals; deterministic Python remains authoritative for IDs, validation, counts, and exports."
        ),
        tools=[
            source_discovery.as_tool(tool_name="discover_sources", tool_description="Discover qualifying evidence sources"),
            perspective_research.as_tool(tool_name="research_perspectives", tool_description="Research stakeholder perspectives"),
            evidence_extraction.as_tool(tool_name="extract_evidence", tool_description="Extract normalized claim records"),
            entity_resolution.as_tool(tool_name="resolve_entities", tool_description="Resolve canonical entities"),
            graph_construction.as_tool(tool_name="construct_graph", tool_description="Construct evidence-linked graph proposals"),
            contradiction_review.as_tool(tool_name="review_contradictions", tool_description="Find limitations and contradictions"),
            citation_audit.as_tool(tool_name="audit_citations", tool_description="Audit every public citation chain"),
            publisher.as_tool(tool_name="prepare_publication", tool_description="Prepare audited publication content"),
        ],
    )
    result = Runner.run_sync(
        manager,
        "Execute the versioned HXG research charter in config/research.toml and write no public output until validation passes.",
        run_config=RunConfig(trace_include_sensitive_data=False, workflow_name="hxg-research"),
        max_turns=80,
    )
    print(result.final_output)
