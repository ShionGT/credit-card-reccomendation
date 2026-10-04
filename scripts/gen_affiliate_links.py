#!/usr/bin/env python3
"""Generate data/affiliate_links.json from data/cards.json.

Each card gets a tracking slot per ASP (A8.net, アクセストレード,
バリューコマース, afb, もしもアフィリエイト). When an ASP approves you for a
card program, paste the tracking URL into the matching slot and set that
card's "active" to the ASP key — every CTA on the site switches instantly.
Rerun this script after adding new cards to cards.json (existing entries
are preserved).
"""
import json
import os

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CARDS = os.path.join(BASE, "data", "cards.json")
OUT = os.path.join(BASE, "data", "affiliate_links.json")

ASPS = {
    "a8": "A8.net",
    "accesstrade": "アクセストレード",
    "valuecommerce": "バリューコマース",
    "afb": "afb",
    "moshimo": "もしもアフィリエイト",
}


def main():
    with open(CARDS, "r", encoding="utf-8") as f:
        cards = json.load(f)

    existing = {}
    if os.path.exists(OUT):
        with open(OUT, "r", encoding="utf-8") as f:
            existing = json.load(f)

    out: dict = {
        "_readme": (
            "ASP tracking links per card. Paste the tracking URL from each ASP "
            "into tracking.<asp>, then set active to that asp key (e.g. 'a8'). "
            "active='' falls back to the official site link in cards.json. "
            "Supported keys: " + ", ".join(ASPS)
        )
    }
    for card in cards:
        cid = card["id"]
        prev = existing.get(cid, {})
        prev_tracking = prev.get("tracking") if isinstance(prev, dict) else None
        tracking = prev_tracking or {k: "" for k in ASPS}
        for k in ASPS:
            tracking.setdefault(k, "")
        active = prev.get("active", "") if isinstance(prev, dict) else ""
        if active and active not in ASPS:
            active = ""
        out[cid] = {"tracking": tracking, "active": active}

    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print(f"Wrote {OUT} with {sum(1 for k in out if not k.startswith('_'))} cards")


if __name__ == "__main__":
    main()
