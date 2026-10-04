"""
Tests for the credit card recommendation app.
Run: python tests/test_app.py
"""
import json
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import app as app_module

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")


def test_load_cards():
    """Test that cards.json loads correctly."""
    cards = app_module.load_cards()
    assert len(cards) > 0, "No cards loaded"
    print(f"  ✓ Loaded {len(cards)} cards")
    return cards


def test_card_fields():
    """Test that all cards have required fields."""
    cards = app_module.load_cards()
    required = ["id", "name", "issuer", "annual_fee", "annual_fee_text",
                "point_rate", "features", "tags", "rating"]
    for card in cards:
        for field in required:
            assert field in card, f"Card {card.get('name', '?')} missing field: {field}"
    print(f"  ✓ All {len(cards)} cards have required fields")


def test_scoring():
    """Test the card scoring algorithm."""
    cards = app_module.load_cards()

    # Simulate a shopping-heavy user
    answers = {
        "credit_level": "初心者",
        "shopping": 5,
        "travel": 1,
        "dining": 2,
        "cashback": 5,
        "mobile": 3,
        "annual_fee_priority": True,
        "brands": ["Visa"],
    }

    scored = []
    for card in cards:
        s = app_module.score_card(card, answers)
        scored.append((card["name"], s))

    scored.sort(key=lambda x: x[1], reverse=True)
    print(f"  ✓ Top card for shopping user: {scored[0][0]} (score: {scored[0][1]})")

    # Simulate a travel-heavy user
    answers2 = {
        "credit_level": "上級者",
        "shopping": 2,
        "travel": 5,
        "dining": 4,
        "cashback": 2,
        "mobile": 2,
        "annual_fee_priority": False,
        "brands": [],
    }

    scored2 = []
    for card in cards:
        s = app_module.score_card(card, answers2)
        scored2.append((card["name"], s))

    scored2.sort(key=lambda x: x[1], reverse=True)
    print(f"  ✓ Top card for travel user: {scored2[0][0]} (score: {scored2[0][1]})")

    # The travel user should get a different top card than the shopping user
    assert scored[0][0] != scored2[0][0] or len(cards) < 3, "Scoring should differentiate user types"
    print("  ✓ Different user types get different recommendations")


def test_unique_ids():
    """Test that all card IDs are unique."""
    cards = app_module.load_cards()
    ids = [c["id"] for c in cards]
    assert len(ids) == len(set(ids)), "Duplicate card IDs found"
    print(f"  ✓ All {len(ids)} card IDs are unique")


def test_go_redirect():
    """Test the /go tracked redirect falls back to the official URL."""
    client = app_module.app.test_client()
    resp = client.get("/go/rakuten-card?src=test")
    assert resp.status_code == 302, f"Expected 302, got {resp.status_code}"
    assert "rakuten-card.co.jp" in resp.headers.get("Location", ""), resp.headers.get("Location")
    print(f"  ✓ /go/rakuten-card -> {resp.headers.get('Location')}")

    resp404 = client.get("/go/nonexistent-card")
    assert resp404.status_code == 404, "Unknown card should 404"
    print("  ✓ /go/<unknown> returns 404")


def test_affiliate_config():
    """Test affiliate_links.json structure matches cards.json."""
    aff = app_module.load_affiliate_links()
    cards = app_module.load_cards()
    card_ids = {c["id"] for c in cards}
    configured = {k for k in aff if not k.startswith("_")}
    missing = card_ids - configured
    assert not missing, f"Cards missing from affiliate_links.json: {missing}"
    for cid in configured:
        entry = aff[cid]
        assert "tracking" in entry, f"{cid} missing tracking dict"
        assert entry.get("active", "") in ("",) + tuple(entry["tracking"].keys()), f"{cid} bad active value"
    print(f"  ✓ Affiliate config valid for {len(configured)} cards")


def test_click_logging():
    """Test clicks are logged (to a temp file so real data stays clean)."""
    import tempfile
    tmpdir = tempfile.mkdtemp()
    real_path = app_module.CLICK_LOG_FILE
    app_module.CLICK_LOG_FILE = os.path.join(tmpdir, "clicks.json")
    try:
        client = app_module.app.test_client()
        client.get("/go/jcb-card-w?src=test")
        with open(app_module.CLICK_LOG_FILE, "r", encoding="utf-8") as f:
            logs = json.load(f)
        assert len(logs) == 1, "Click not logged"
        assert logs[0]["card"] == "jcb-card-w", logs[0]
        assert logs[0]["asp"] == "official", logs[0]
        assert logs[0]["source"] == "test", logs[0]
        print("  ✓ Click logging works")
    finally:
        app_module.CLICK_LOG_FILE = real_path


def run_all():
    print("=" * 50)
    print("  クレジットカードおすすめ比較 - テスト")
    print("=" * 50 + "\n")

    tests = [
        ("Loading cards", test_load_cards),
        ("Card fields", test_card_fields),
        ("Scoring algorithm", test_scoring),
        ("Unique IDs", test_unique_ids),
        ("Go redirect", test_go_redirect),
        ("Affiliate config", test_affiliate_config),
        ("Click logging", test_click_logging),
    ]

    passed = 0
    failed = 0

    for name, test in tests:
        print(f"\n[テスト] {name}")
        try:
            test()
            passed += 1
        except AssertionError as e:
            print(f"  ✗ FAILED: {e}")
            failed += 1
        except Exception as e:
            print(f"  ✗ ERROR: {e}")
            failed += 1

    print(f"\n{'=' * 50}")
    print(f"  結果: {passed} 通過, {failed} 失敗")
    print(f"{'=' * 50}\n")

    return failed == 0


if __name__ == "__main__":
    success = run_all()
    sys.exit(0 if success else 1)
