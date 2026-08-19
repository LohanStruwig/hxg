from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, TypeVar

from pydantic import BaseModel

from hxg.models import Record

ROOT = Path(__file__).resolve().parents[2]
SEED_DIR = ROOT / "data" / "seed"
PUBLIC_DIR = ROOT / "data" / "public"
SCHEMA_DIR = ROOT / "data" / "schemas" / "v1"
GRAPH_DIR = ROOT / "graphs"
REPORT_DIR = ROOT / "reports"

T = TypeVar("T", bound=Record)


def canonical_json(value: Any) -> str:
    if isinstance(value, BaseModel):
        value = value.model_dump(mode="json")
    return json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def sha256_text(value: str) -> str:
    return "sha256:" + hashlib.sha256(value.encode("utf-8")).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return "sha256:" + digest.hexdigest()


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def load_records(path: Path, model: type[T]) -> list[T]:
    return [model.model_validate(item) for item in read_json(path)]


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(canonical_json(value), encoding="utf-8", newline="\n")


def copy_seed_to_public(filename: str) -> Path:
    source = SEED_DIR / filename
    target = PUBLIC_DIR / filename
    write_json(target, read_json(source))
    return target
