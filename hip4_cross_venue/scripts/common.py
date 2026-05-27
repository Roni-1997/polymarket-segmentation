from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any


BASE_DIR = Path(__file__).resolve().parents[1]
REPO_DIR = BASE_DIR.parent
DATA_DIR = BASE_DIR / "data"
RESULTS_DIR = REPO_DIR / "results"

HL_INFO_URL = "https://api.hyperliquid.xyz/info"


def read_json(path: Path) -> Any:
    with path.open() as f:
        return json.load(f)


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as f:
        json.dump(data, f, indent=2)
        f.write("\n")


def hl_info(payload: dict[str, Any], timeout: int = 20) -> Any:
    r = subprocess.run(
        [
            "curl",
            "-sS",
            "-X",
            "POST",
            HL_INFO_URL,
            "-H",
            "Content-Type: application/json",
            "-d",
            json.dumps(payload),
        ],
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
    )
    if r.returncode != 0 or not r.stdout.strip():
        return None
    try:
        return json.loads(r.stdout)
    except json.JSONDecodeError:
        return None


def is_hip4_coin(coin: str | None) -> bool:
    return bool(coin and coin.startswith("#") and coin[1:].isdigit() and int(coin[1:]) >= 1000)


def polymarket_volume_musd(row: dict[str, str]) -> float:
    """Return wallet-side/touched Polymarket volume in millions of dollars.

    Older result exports used vol_musd; audited exports use touched_vol_musd.
    """
    raw = row.get("touched_vol_musd") or row.get("vol_musd") or "0"
    return float(raw)
