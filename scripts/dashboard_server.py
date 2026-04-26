#!/usr/bin/env python3
"""
Dashboard server for the India / Dhan production engine.

Stateless: every endpoint reads from disk (the engine's JSONL trade log,
the model registry, the saved model card). The dashboard never imports the
engine itself, so it is safe to run alongside live trading.

Endpoints
---------
GET  /                  -> dashboard.html
GET  /api/account       -> Dhan funds + RiskManager config
GET  /api/positions     -> currently-open positions reconstructed from the
                           trade log (open events without a matching close)
GET  /api/trades        -> last N closed + open trades from today's JSONL
GET  /api/stats         -> session totals (trades, win-rate, net INR/bps)
GET  /api/model_card    -> current champion + sibling model_card.json
"""
from __future__ import annotations

import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

if sys.platform == "win32":  # pragma: no cover
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

SCRIPTS = Path(__file__).resolve().parent
ROOT = SCRIPTS.parent
sys.path.insert(0, str(SCRIPTS))

from flask import Flask, jsonify, render_template
from flask_cors import CORS

from dhan_data_fetcher import DhanLiveDataFetcher  # noqa: E402
from utils.model_registry import ModelRegistry  # noqa: E402

app = Flask(
    __name__,
    template_folder=str(ROOT / "templates"),
    static_folder=str(ROOT / "static"),
)
CORS(app)


PRODUCTION_LOG_DIR = ROOT / "logs" / "production"


def _today_log() -> Path:
    return PRODUCTION_LOG_DIR / f"trades_{datetime.now().strftime('%Y%m%d')}.jsonl"


def _read_events(path: Optional[Path] = None) -> List[Dict[str, Any]]:
    """Read every JSONL event for today (or the given path)."""
    p = path or _today_log()
    if not p.exists():
        return []
    out: List[Dict[str, Any]] = []
    with open(p, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return out


def _open_and_closed(events: List[Dict[str, Any]]) -> tuple[Dict[str, dict], List[dict]]:
    """
    Walk events; pair each `open` with the next `close` of the same ticker.
    Returns (still_open_by_ticker, completed_round_trips).
    """
    opens: Dict[str, dict] = {}
    completed: List[dict] = []
    for ev in events:
        kind = ev.get("event")
        if kind == "open":
            opens[ev["ticker"]] = ev
        elif kind == "close":
            ticker = ev.get("ticker")
            entry = opens.pop(ticker, None)
            if entry is None:
                completed.append({"close": ev})
                continue
            entry_px = entry.get("price")
            exit_px = ev.get("exit_price")
            qty = entry.get("qty", 0)
            net_inr = None
            if entry_px is not None and exit_px is not None and qty:
                net_inr = (float(exit_px) - float(entry_px)) * float(qty)
            completed.append(
                {
                    "ticker": ticker,
                    "qty": qty,
                    "entry_price": entry_px,
                    "exit_price": exit_px,
                    "entry_time": entry.get("time"),
                    "exit_time": ev.get("time"),
                    "exit_reason": ev.get("reason"),
                    "net_inr": net_inr,
                    "stop": entry.get("stop"),
                    "target": entry.get("target"),
                }
            )
    return opens, completed


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@app.route("/")
def dashboard():
    return render_template("dashboard.html")


@app.route("/api/account")
def get_account():
    paper = not (os.getenv("DHAN_CLIENT_ID") and os.getenv("DHAN_ACCESS_TOKEN"))
    try:
        fetcher = DhanLiveDataFetcher(paper=paper)
        status = fetcher.account_status()
    except Exception as exc:
        return jsonify({"error": str(exc), "mode": "paper" if paper else "live"}), 200

    equity = float(status.get("equity", 0.0))

    # Today's realised P&L from the trade log.
    _, completed = _open_and_closed(_read_events())
    realised_inr = sum(c["net_inr"] for c in completed if c.get("net_inr") is not None)

    return jsonify(
        {
            "mode": "paper" if paper else "live",
            "broker": "dhan",
            "equity": equity,
            "cash": float(status.get("cash", equity)),
            "pnl": realised_inr,
            "pnl_pct": (realised_inr / equity * 100.0) if equity else 0.0,
            "status": status.get("status", "unknown"),
        }
    )


@app.route("/api/positions")
def get_positions():
    opens, _ = _open_and_closed(_read_events())
    positions = []
    for ticker, ev in opens.items():
        positions.append(
            {
                "symbol": ticker,
                "qty": ev.get("qty", 0),
                "avg_entry_price": ev.get("price"),
                "stop": ev.get("stop"),
                "target": ev.get("target"),
                "entry_time": ev.get("time"),
                "atr": ev.get("atr"),
            }
        )
    return jsonify({"positions": positions})


@app.route("/api/trades")
def get_trades():
    events = _read_events()
    _, completed = _open_and_closed(events)
    return jsonify({"trades": list(reversed(completed[-30:]))})


@app.route("/api/stats")
def get_stats():
    events = _read_events()
    opens, completed = _open_and_closed(events)
    n = len(completed)
    pnl_list = [c["net_inr"] for c in completed if c.get("net_inr") is not None]
    wins = sum(1 for x in pnl_list if x > 0)
    losses = sum(1 for x in pnl_list if x <= 0)
    symbols = sorted({c.get("ticker") for c in completed if c.get("ticker")})
    return jsonify(
        {
            "total_trades": n,
            "open_positions": len(opens),
            "wins": wins,
            "losses": losses,
            "win_rate": (wins / n * 100.0) if n else 0.0,
            "net_pnl_inr": sum(pnl_list) if pnl_list else 0.0,
            "symbols": symbols,
        }
    )


@app.route("/api/model_card")
def get_model_card():
    try:
        reg = ModelRegistry()
    except Exception as exc:
        return jsonify({"error": str(exc)}), 200

    champion = reg.registry.get("champion")
    if not champion:
        return jsonify({"champion": None, "card": None})

    card_path = Path(champion).with_name("model_card.json")
    card = None
    if card_path.exists():
        try:
            card = json.loads(card_path.read_text())
        except Exception:
            card = None

    history = reg.registry.get("history", [])
    return jsonify(
        {
            "champion": champion,
            "card": card,
            "history": history[-5:],
            "rejected": reg.registry.get("challengers", [])[-5:],
        }
    )


if __name__ == "__main__":
    print("=" * 70)
    print("  India / Dhan Trading Dashboard")
    print("=" * 70)
    print(f"  URL:  http://localhost:5000")
    print(f"  Logs: {PRODUCTION_LOG_DIR}")
    print("=" * 70)
    app.run(host="127.0.0.1", port=5000, debug=False, use_reloader=False)
