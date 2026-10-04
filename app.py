"""
クレジットカードおすすめ比較 - Flask Application
Japanese Credit Card Recommendation Website
"""
import json
import os
import datetime
from flask import Flask, render_template, jsonify, request, redirect, send_from_directory

app = Flask(__name__)

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
CARDS_FILE = os.path.join(DATA_DIR, "cards.json")
LOGS_FILE = os.path.join(DATA_DIR, "recommendation_logs.json")

app = Flask(__name__, template_folder=os.path.join(BASE_DIR, "app", "templates"), static_folder=os.path.join(BASE_DIR, "app", "static"))
import sys
sys.path.insert(0, os.path.join(BASE_DIR, "config"))
try:
    from adsense import ADSENSE_CLIENT_ID as _AD_CLIENT, ADSENSE_SLOTS as _AD_SLOTS, ADSENSE_ENABLED as _AD_ENABLED
except Exception:
    _AD_CLIENT = "ca-pub-0000000000000000"
    _AD_SLOTS = {}
    _AD_ENABLED = False

# Allow env vars to override config file (for Render / production)
ADSENSE_CLIENT_ID = os.environ.get("ADSENSE_CLIENT_ID", _AD_CLIENT)
ADSENSE_ENABLED = os.environ.get("ADSENSE_ENABLED", str(_AD_ENABLED)).lower() in ("true", "1", "yes")
ADSENSE_SLOTS = _AD_SLOTS


def load_cards():
    """Load card data from JSON file."""
    with open(CARDS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def load_logs():
    """Load recommendation logs (for analytics)."""
    if os.path.exists(LOGS_FILE):
        with open(LOGS_FILE, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return []
    return []


def save_logs(logs):
    with open(LOGS_FILE, "w", encoding="utf-8") as f:
        json.dump(logs, f, ensure_ascii=False, indent=2)


# --- Affiliate (ASP) link management ---------------------------------------
AFFILIATE_FILE = os.path.join(DATA_DIR, "affiliate_links.json")
CLICK_LOG_FILE = os.path.join(DATA_DIR, "click_logs.json")


def load_affiliate_links():
    """Load ASP tracking link config (card_id -> {tracking: {asp: url}, active: asp})."""
    if os.path.exists(AFFILIATE_FILE):
        try:
            with open(AFFILIATE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            return {}
    return {}


def get_apply_url(card_id):
    """Return (tracking_url, asp_name) for the active ASP, or (None, None) to fall back to the official link."""
    cfg = load_affiliate_links().get(card_id) or {}
    active = cfg.get("active", "")
    if active:
        url = (cfg.get("tracking") or {}).get(active, "")
        if url:
            return url, active
    return None, None


def affiliate_active(card_id):
    """True when a real ASP tracking link is live for this card."""
    return get_apply_url(card_id)[1] is not None


def log_click(card_id, asp, source):
    """Append a click record; logging failures must never break the redirect."""
    try:
        logs = []
        if os.path.exists(CLICK_LOG_FILE):
            with open(CLICK_LOG_FILE, "r", encoding="utf-8") as f:
                logs = json.load(f)
        logs.append({
            "timestamp": datetime.datetime.now().isoformat(),
            "card": card_id,
            "asp": asp,
            "source": source,
        })
        logs = logs[-5000:]
        with open(CLICK_LOG_FILE, "w", encoding="utf-8") as f:
            json.dump(logs, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


def score_card(card, answers):
    """
    Score a card based on user answers.
    Each answer is a dict with category weights.
    """
    score = 0.0

    # Primary category scoring
    category_map = {
        "shopping": "shopping_benefits",
        "travel": "travel_benefits",
        "dining": "dining_benefits",
        "cashback": "cashback_benefits",
        "gas": "gas_benefits",
        "mobile": "mobile_benefits",
    }

    for cat_key, card_key in category_map.items():
        user_pref = answers.get(cat_key, 0)
        card_val = card.get(card_key, 0)
        score += user_pref * card_val

    # Annual fee preference (lower fee = higher score for budget-conscious)
    if answers.get("annual_fee_priority"):
        if card.get("annual_fee", 0) == 0:
            score += 5
        else:
            score -= card.get("annual_fee", 0) / 5000.0

    # Credit level matching
    level = answers.get("credit_level", "初心者")
    if level in card.get("credit_score_required", ""):
        score += 10

    # Brand preference
    preferred_brands = answers.get("brands", [])
    if preferred_brands:
        card_brands = card.get("international_brand", [])
        for b in preferred_brands:
            if b in card_brands:
                score += 3

    # Rating bonus
    score += card.get("rating", 0) * 0.5

    return round(score, 2)


@app.route("/")
def index():
    """Home page with recommendation quiz."""
    cards = load_cards()
    return render_template(
        "index.html",
        cards=cards,
        adsense_client_id=ADSENSE_CLIENT_ID,
        adsense_slots=ADSENSE_SLOTS,
        adsense_enabled=ADSENSE_ENABLED,
    )


@app.route("/recommend", methods=["POST"])
def recommend():
    """API endpoint to get card recommendations."""
    answers = request.json or {}
    cards = load_cards()

    scored = []
    for card in cards:
        s = score_card(card, answers)
        scored.append({"card": card, "score": s})

    scored.sort(key=lambda x: x["score"], reverse=True)
    top = scored[:5]

    # Log recommendation
    logs = load_logs()
    log_entry = {
        "timestamp": datetime.datetime.now().isoformat(),
        "answers": answers,
        "results": [{"id": r["card"]["id"], "score": r["score"]} for r in top],
    }
    logs.append(log_entry)
    if len(logs) > 1000:
        logs = logs[-1000:]
    save_logs(logs)

    return jsonify({"recommendations": top})


@app.route("/cards")
def cards_list():
    """Full card listing page."""
    cards = load_cards()
    return render_template(
        "cards.html",
        cards=cards,
        adsense_client_id=ADSENSE_CLIENT_ID,
        adsense_slots=ADSENSE_SLOTS,
        adsense_enabled=ADSENSE_ENABLED,
    )


@app.route("/card/<card_id>")
def card_detail(card_id):
    """Individual card detail page."""
    cards = load_cards()
    card = next((c for c in cards if c["id"] == card_id), None)
    if not card:
        return render_template("404.html"), 404
    return render_template(
        "card_detail.html",
        card=card,
        aff_active=affiliate_active(card_id),
        adsense_client_id=ADSENSE_CLIENT_ID,
        adsense_slots=ADSENSE_SLOTS,
        adsense_enabled=ADSENSE_ENABLED,
    )


@app.route("/about")
def about():
    """About / disclaimer page."""
    return render_template(
        "about.html",
        adsense_client_id=ADSENSE_CLIENT_ID,
        adsense_slots=ADSENSE_SLOTS,
        adsense_enabled=ADSENSE_ENABLED,
    )


@app.route("/api/cards")
def api_cards():
    """API endpoint returning all card data as JSON."""
    cards = load_cards()
    return jsonify(cards)


@app.route("/api/cards/<card_id>")
def api_card(card_id):
    """API endpoint returning a single card as JSON."""
    cards = load_cards()
    card = next((c for c in cards if c["id"] == card_id), None)
    if not card:
        return jsonify({"error": "not found"}), 404
    return jsonify(card)


@app.route("/health")
def health():
    """Health check endpoint."""
    cards = load_cards()
    return jsonify({"status": "ok", "cards_count": len(cards), "date": datetime.datetime.now().isoformat()})


@app.route("/go/<card_id>")
def go_apply(card_id):
    """Tracked application redirect: ASP tracking URL if configured, else the official page."""
    cards = load_cards()
    card = next((c for c in cards if c["id"] == card_id), None)
    if not card:
        return render_template("404.html"), 404
    source = request.args.get("src", "unknown")
    url, asp = get_apply_url(card_id)
    if not url:
        url = card.get("affiliate_url") or "/"
        asp = "official"
    log_click(card_id, asp, source)
    return redirect(url, code=302)


@app.route("/api/clicks")
def api_clicks():
    """Aggregate click counts (no personal data) for quick CTR checks."""
    logs = []
    if os.path.exists(CLICK_LOG_FILE):
        try:
            with open(CLICK_LOG_FILE, "r", encoding="utf-8") as f:
                logs = json.load(f)
        except (json.JSONDecodeError, OSError):
            logs = []
    agg = {}
    for entry in logs:
        key = (entry.get("card"), entry.get("asp"), entry.get("source"))
        agg[key] = agg.get(key, 0) + 1
    return jsonify({
        "total": len(logs),
        "breakdown": [
            {"card": c, "asp": a, "source": s, "count": n}
            for (c, a, s), n in sorted(agg.items(), key=lambda kv: -kv[1])
        ],
    })


@app.route("/privacy")
def privacy():
    """Privacy policy page."""
    return render_template(
        "privacy.html",
        adsense_client_id=ADSENSE_CLIENT_ID,
        adsense_slots=ADSENSE_SLOTS,
        adsense_enabled=ADSENSE_ENABLED,
    )


@app.route("/robots.txt")
def robots():
    return "User-agent: *\nAllow: /\nDisallow: /go/\n", 200, {"Content-Type": "text/plain; charset=utf-8"}


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=os.environ.get("FLASK_DEBUG", "0") == "1")
