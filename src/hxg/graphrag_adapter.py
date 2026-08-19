from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from hxg.io import ROOT


class GraphRAGAdapter:
    """Local-only Microsoft GraphRAG staging adapter.

    GraphRAG may propose entities, relationships, and communities. HXG's versioned
    records and deterministic validator remain the publication authority.
    """

    def __init__(self, workspace: Path | None = None) -> None:
        self.workspace = workspace or ROOT / "data" / "private" / "graphrag"

    def available(self) -> bool:
        return shutil.which("graphrag") is not None

    def index(self) -> None:
        if not self.available():
            raise RuntimeError("Microsoft GraphRAG CLI is not installed")
        self.workspace.mkdir(parents=True, exist_ok=True)
        subprocess.run(
            ["graphrag", "index", "--root", str(self.workspace)],
            check=True,
            cwd=ROOT,
        )
