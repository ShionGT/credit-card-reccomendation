#!/usr/bin/env python3
"""
データ更新スクリプト - Data Update Script

This script helps keep the credit card data up to date by:
1. Scraping card issuer websites for updated information (bonus campaigns, fees, etc.)
2. Merging scraped data with the existing cards.json
3. Logging changes for review

Usage:
    python scripts/update_data.py              # Full update
    python scripts/update_data.py --dry-run    # Show changes without writing
    python scripts/update_data.py --add        # Interactively add a new card
"""

import json
import os
import sys
import datetime
import requests
from bs4 import BeautifulSoup

# Paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CARDS_FILE = os.path.join(BASE_DIR, "data", "cards.json")
CHANGELOG_FILE = os.path.join(BASE_DIR, "data", "changelog.json")


def load_cards():
    with open(CARDS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_cards(cards):
    with open(CARDS_FILE, "w", encoding="utf-8") as f:
        json.dump(cards, f, ensure_ascii=False, indent=2)


def load_changelog():
    if os.path.exists(CHANGELOG_FILE):
        with open(CHANGELOG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def save_changelog(log):
    with open(CHANGELOG_FILE, "w", encoding="utf-8") as f:
        json.dump(log, f, ensure_ascii=False, indent=2)


def scrape_card_page(url):
    """Scrape a card issuer page for updated info."""
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
        }
        resp = requests.get(url, headers=headers, timeout=10)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

        # Extract title
        title = soup.find("title")
        title_text = title.text.strip() if title else ""

        # Try to extract campaign/bonus info (generic approach)
        bonus_text = ""
        for keyword in ["キャンペーン", "プレゼント", "ボーナス", "入会"]:
            elem = soup.find(string=lambda t: t and keyword in t)
            if elem:
                bonus_text = elem.strip()
                break

        return {
            "title": title_text,
            "bonus_hint": bonus_text,
            "scraped_at": datetime.datetime.now().isoformat(),
        }
    except Exception as e:
        return {"error": str(e), "url": url}


def update_cards(dry_run=False):
    """Update card data by scraping affiliate URLs."""
    cards = load_cards()
    changelog = load_changelog()
    changes = []

    for card in cards:
        url = card.get("affiliate_url", "")
        if not url or not url.startswith("http"):
            continue

        print(f"  Checking: {card['name']} ({url})")
        result = scrape_card_page(url)

        if "error" in result:
            print(f"    ⚠ Error: {result['error']}")
            changelog.append({
                "card_id": card["id"],
                "card_name": card["name"],
                "timestamp": datetime.datetime.now().isoformat(),
                "type": "scrape_error",
                "detail": result["error"],
            })
            continue

        # Check if bonus info changed
        old_bonus = card.get("bonus", "")
        new_hint = result.get("bonus_hint", "")

        if new_hint and new_hint != old_bonus:
            print(f"    ✦ Bonus may have changed: '{old_bonus}' -> '{new_hint}'")
            changes.append({
                "card_id": card["id"],
                "card_name": card["name"],
                "field": "bonus",
                "old": old_bonus,
                "new_hint": new_hint,
                "scraped_at": result["scraped_at"],
            })

            if not dry_run:
                card["bonus_hint"] = new_hint
                card["updated"] = datetime.date.today().isoformat()

        # Update last_checked timestamp
        if not dry_run:
            card["last_checked"] = datetime.datetime.now().isoformat()

    if changes:
        changelog.append({
            "timestamp": datetime.datetime.now().isoformat(),
            "type": "update_scan",
            "changes": changes,
        })
        if not dry_run:
            save_cards(cards)
            print(f"\n✓ Updated cards.json with {len(changes)} potential changes")
        else:
            print(f"\n[DRY RUN] Found {len(changes)} potential changes (not saved)")
    else:
        print("\n✓ No changes detected")

    if not dry_run:
        save_changelog(changelog)


def add_card_interactive():
    """Interactively add a new card to the database."""
    print("\n=== 新しいカードを追加 ===\n")
    card = {}
    card["id"] = input("ID (e.g. 'rakuten-pc'): ").strip().lower().replace(" ", "-")
    card["name"] = input("カード名: ").strip()
    card["issuer"] = input("発行会社: ").strip()
    card["annual_fee"] = int(input("年会費（数値、円）: ") or "0")
    card["annual_fee_text"] = input("年会費（テキスト）: ").strip()
    card["point_rate"] = input("還元率（例: 1.0%）: ").strip()
    card["point_system"] = input("ポイントシステム: ").strip()
    card["bonus"] = input("キャンペーン: ").strip()
    card["bonus_detail"] = input("キャンペーン詳細: ").strip()
    card["cashback_rate"] = input("キャッシュバック率: ").strip()
    card["cashback_max"] = float(input("最大還元率（数値）: ") or "1.0")

    brands_input = input("国際ブランド（カンマ区切り）: ").strip()
    card["international_brand"] = [b.strip() for b in brands_input.split(",")]

    for benefit in ["travel", "cashback", "shopping", "dining", "gas", "mobile"]:
        card[f"{benefit}_benefits"] = int(input(f"{benefit} benefits (0-5): ") or "1")

    card["credit_score_required"] = input("対象者: ").strip()

    features_input = input("特徴（カンマ区切り）: ").strip()
    card["features"] = [f.strip() for f in features_input.split(",")]

    tags_input = input("タグ（カンマ区切り）: ").strip()
    card["tags"] = [t.strip() for t in tags_input.split(",")]

    card["interest_rate"] = input("金利: ").strip()
    card["limit"] = "個別審査"
    card["image_url"] = input("画像URL（空Enter可）: ").strip()
    card["affiliate_url"] = input("アフィリエイトURL: ").strip()
    card["rating"] = float(input("評価（0-5）: ") or "3.0")
    card["updated"] = datetime.date.today().isoformat()

    cards = load_cards()
    cards.append(card)
    save_cards(cards)
    print(f"\n✓ 追加しました: {card['name']}")


def main():
    print("=" * 50)
    print("  クレジットカードデータ更新スクリプト")
    print("=" * 50)

    dry_run = "--dry-run" in sys.argv
    add_mode = "--add" in sys.argv

    if add_mode:
        add_card_interactive()
    else:
        print(f"\nモード: {'ドライラン' if dry_run else '更新'}")
        print(f"カード数: {len(load_cards())}\n")
        update_cards(dry_run=dry_run)

    print("\n完了しました。\n")


if __name__ == "__main__":
    main()
