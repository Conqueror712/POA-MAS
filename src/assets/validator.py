from __future__ import annotations

from typing import Any


def validate_assets(assets: list[dict[str, Any]], min_confidence: float = 0.5) -> list[dict[str, Any]]:
    return [asset for asset in assets if float(asset.get("confidence", 0.0)) >= min_confidence]

