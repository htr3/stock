#!/usr/bin/env python3
"""Champion / Challenger model registry with backtest-driven promotion gate."""
from __future__ import annotations

import hashlib
import json
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any, Mapping

import joblib

ROOT = Path(__file__).resolve().parents[2]


# Promotion gate -- a challenger must beat ALL of these to become champion.
PROMOTION_GATE = {
    "sharpe": 1.0,
    "max_drawdown": 0.10,   # 10% maximum drawdown allowed
    "win_rate": 0.50,
    "net_pnl_bps": 0.0,
    "trades": 30,
}


class ModelRegistry:
    def __init__(self):
        self.registry_path = ROOT / "models" / "metadata" / "model_registry.json"
        self.registry_path.parent.mkdir(parents=True, exist_ok=True)

        if self.registry_path.exists():
            with open(self.registry_path) as f:
                self.registry = json.load(f)
        else:
            self.registry = {"champion": None, "challengers": []}

    # ------------------------------------------------------------------
    # Read access
    # ------------------------------------------------------------------

    def champion(self):
        if self.registry.get("champion"):
            return joblib.load(self.registry["champion"])
        return None

    # ------------------------------------------------------------------
    # Promotion gate
    # ------------------------------------------------------------------

    def evaluate_promotion(
        self,
        challenger_path: str,
        metrics: Mapping[str, Any],
    ) -> tuple[bool, dict]:
        """
        Apply the Sharpe / maxDD / win-rate / net-PnL / trade-count gate.

        Returns
        -------
        (passed, details)
            ``details`` lists which gates failed, suitable for logging.
        """
        failed: dict[str, Any] = {}

        sharpe = float(metrics.get("sharpe", 0.0))
        if sharpe < PROMOTION_GATE["sharpe"]:
            failed["sharpe"] = (sharpe, PROMOTION_GATE["sharpe"])

        max_dd = float(metrics.get("max_drawdown", 1.0))
        if max_dd > PROMOTION_GATE["max_drawdown"]:
            failed["max_drawdown"] = (max_dd, PROMOTION_GATE["max_drawdown"])

        win_rate = float(metrics.get("win_rate", 0.0))
        if win_rate < PROMOTION_GATE["win_rate"]:
            failed["win_rate"] = (win_rate, PROMOTION_GATE["win_rate"])

        net_bps = float(metrics.get("net_pnl_bps", 0.0))
        if net_bps <= PROMOTION_GATE["net_pnl_bps"]:
            failed["net_pnl_bps"] = (net_bps, PROMOTION_GATE["net_pnl_bps"])

        trades = int(metrics.get("trades", 0))
        if trades < PROMOTION_GATE["trades"]:
            failed["trades"] = (trades, PROMOTION_GATE["trades"])

        return (not failed), {"gate": dict(PROMOTION_GATE), "failed": failed}

    # ------------------------------------------------------------------
    # Promote / archive
    # ------------------------------------------------------------------

    def promote_challenger(
        self,
        challenger_path: str,
        metrics: Mapping[str, Any] | None = None,
        extra: Mapping[str, Any] | None = None,
    ) -> Path:
        """Move challenger to champion and write a sibling ``model_card.json``."""
        self.registry["champion"] = challenger_path
        self.registry.setdefault("history", []).append(
            {
                "path": challenger_path,
                "promoted_at": datetime.utcnow().isoformat() + "Z",
                "metrics": dict(metrics) if metrics else {},
            }
        )
        self._save_registry()

        card_path = Path(challenger_path).with_name("model_card.json")
        card = {
            "model_path": str(challenger_path),
            "trained_at": datetime.utcnow().isoformat() + "Z",
            "metrics": dict(metrics) if metrics else {},
            "code_sha": _git_sha(),
            "feature_set_hash": _hash_extra(extra),
            "extra": dict(extra) if extra else {},
        }
        card_path.write_text(json.dumps(card, indent=2))
        return card_path

    def archive_challenger(
        self,
        model_path: str,
        metrics: Mapping[str, Any] | None = None,
        reason: str = "rejected",
    ) -> None:
        self.registry["challengers"].append(
            {
                "path": model_path,
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "status": reason,
                "metrics": dict(metrics) if metrics else {},
            }
        )
        self._save_registry()

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _save_registry(self):
        with open(self.registry_path, "w") as f:
            json.dump(self.registry, f, indent=2)


def _git_sha() -> str:
    try:
        out = subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=ROOT,
            stderr=subprocess.DEVNULL,
        )
        return out.decode().strip()
    except Exception:
        return "unknown"


def _hash_extra(extra: Mapping[str, Any] | None) -> str:
    if not extra:
        return ""
    blob = json.dumps(extra, sort_keys=True, default=str).encode()
    return hashlib.sha256(blob).hexdigest()[:16]
