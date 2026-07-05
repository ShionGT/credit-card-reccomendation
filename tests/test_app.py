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


def run_all():
    print("=" * 50)
    print("  クレジットカードおすすめ比較 - テスト")
    print("=" * 50 + "\n")

    tests = [
        ("Loading cards", test_load_cards),
        ("Card fields", test_card_fields),
        ("Scoring algorithm", test_scoring),
        ("Unique IDs", test_unique_ids),
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
