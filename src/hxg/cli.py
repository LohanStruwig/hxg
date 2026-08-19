from __future__ import annotations

from datetime import date
from typing import Annotated, Literal

import typer
from rich.console import Console

from hxg.graph import export_graphs
from hxg.research import run_research
from hxg.schema_export import export_schemas
from hxg.validation import validate_graph_parity, validate_public_release

app = typer.Typer(no_args_is_help=True, help="Hospitality Experience Graph research toolkit")
console = Console()


@app.command()
def research(
    mode: Annotated[Literal["seed", "agents"], typer.Option()] = "seed",
    cutoff: Annotated[str, typer.Option(help="Evidence cutoff in YYYY-MM-DD format")] = "2026-08-19",
    cost_limit_usd: Annotated[float, typer.Option(min=0.01)] = 10.0,
    retrieve: Annotated[bool, typer.Option(help="Cache and hash source documents locally")] = False,
) -> None:
    """Run the governed seed freeze or the local model-backed manager pipeline."""
    run_research(
        mode=mode,
        cutoff=date.fromisoformat(cutoff),
        cost_limit_usd=cost_limit_usd,
        retrieve=retrieve,
    )
    export_schemas()
    console.print("[green]Research outputs prepared.[/green]")


@app.command()
def validate() -> None:
    """Validate schemas, evidence chains, cutoff, counts, and graph parity."""
    counts = validate_public_release()
    validate_graph_parity()
    console.print(f"[green]Release valid:[/green] {counts}")


@app.command("build-graph")
def build_graph_command() -> None:
    """Export canonical GraphML, browser JSON, and accessible SVG."""
    export_graphs()
    validate_graph_parity()
    console.print("[green]Graph exports built and parity-checked.[/green]")


@app.command("build-publication")
def build_publication_command(
    verified_url: Annotated[str | None, typer.Option(help="Live URL; required before QR generation")] = None,
) -> None:
    """Build the poster, carousel, and publication package from frozen evidence."""
    from hxg.publication import build_publication

    build_publication(verified_url=verified_url)
    console.print("[green]Publication package built.[/green]")
