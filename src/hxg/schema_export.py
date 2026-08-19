from __future__ import annotations

from hxg.io import SCHEMA_DIR, write_json
from hxg.models import PUBLIC_MODELS, model_schema


def export_schemas() -> None:
    for model in PUBLIC_MODELS:
        write_json(SCHEMA_DIR / f"{model.__name__.lower()}.schema.json", model_schema(model))
