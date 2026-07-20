from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from src.utils.config import ensure_dir


class AssetStore:
    def __init__(self, asset_root: str | Path):
        self.asset_root = ensure_dir(asset_root)
        self.role_dir = ensure_dir(self.asset_root / "role_assets")
        self.org_dir = ensure_dir(self.asset_root / "organization_assets")
        self.game_dir = ensure_dir(self.asset_root / "game_assets")

    def save_role_assets(self, assets: list[dict[str, Any]], filename: str = "latest_role_assets.json") -> Path:
        path = self.role_dir / filename
        with path.open("w", encoding="utf-8") as f:
            json.dump(assets, f, indent=2, ensure_ascii=False)
        return path

    def save_organization_assets(self, assets: list[dict[str, Any]], filename: str = "latest_organization_assets.json") -> Path:
        path = self.org_dir / filename
        with path.open("w", encoding="utf-8") as f:
            json.dump(assets, f, indent=2, ensure_ascii=False)
        return path

    def save_game_assets(self, assets: list[dict[str, Any]], filename: str = "latest_strategy_assets.json") -> Path:
        path = self.game_dir / filename
        with path.open("w", encoding="utf-8") as f:
            json.dump(assets, f, indent=2, ensure_ascii=False)
        return path

    def load_game_assets(self, filename: str = "latest_strategy_assets.json") -> dict[str, Any]:
        path = self.game_dir / filename
        if not path.exists():
            return {}
        return {"strategy_assets": json.loads(path.read_text(encoding="utf-8"))}

    def load_latest(self, mode: str = "full") -> dict[str, Any]:
        loaded: dict[str, Any] = {}
        if mode in {"full", "role"}:
            role_path = self.role_dir / "latest_role_assets.json"
            if role_path.exists():
                loaded["role_assets"] = json.loads(role_path.read_text(encoding="utf-8"))
        if mode in {"full", "organization"}:
            org_path = self.org_dir / "latest_organization_assets.json"
            if org_path.exists():
                loaded["organization_assets"] = json.loads(org_path.read_text(encoding="utf-8"))
        if mode == "game":
            loaded.update(self.load_game_assets())
        return loaded
