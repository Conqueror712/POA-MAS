from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from src.assets.extractor import extract_assets, load_events
from src.assets.store import AssetStore
from src.assets.validator import validate_assets
from src.utils.config import load_json


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description="Extract role and organization assets from a run.")
    parser.add_argument("--config", default="configs/experiments.json")
    parser.add_argument("--run-dir", default="trajectories/latest")
    parser.add_argument("--min-confidence", type=float, default=0.5)
    args = parser.parse_args()

    config = load_json(args.config)
    events = load_events(args.run_dir)
    role_assets, org_assets = extract_assets(events)
    role_assets = validate_assets(role_assets, min_confidence=args.min_confidence)
    org_assets = validate_assets(org_assets, min_confidence=args.min_confidence)

    store = AssetStore(config["asset_root"])
    role_path = store.save_role_assets(role_assets)
    org_path = store.save_organization_assets(org_assets)

    payload = {
        "source_run_dir": str(Path(args.run_dir)),
        "role_asset_path": str(role_path),
        "organization_asset_path": str(org_path),
        "num_role_assets": len(role_assets),
        "num_organization_assets": len(org_assets),
    }
    print(json.dumps(payload, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()

