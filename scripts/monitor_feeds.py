#!/usr/bin/env python3
"""
RSSフィード監視スクリプト - RSS Feed Monitor

Monitors financial news RSS feeds for credit card related news,
saves relevant articles to data/news.json for display on the website.

Usage:
    python scripts/monitor_feeds.py
"""

import json
import os
import datetime
import feedparser

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NEWS_FILE = os.path.join(BASE_DIR, "data", "news.json")

# Japanese financial news RSS feeds
FEEDS = [
    # General financial news
    "https://www.nikkei.com/rss/news/financial.xml",
    # Money-related
    "https://news.yahoo.co.jp/rss/categories/business.xml",
    # Card-portal news (example)
    "https://www.card-portal.jp/feed/news.xml",
]

# Keywords to filter for
KEYWORDS = [
    "クレジットカード", "カード", "年会費", "キャンペーン",
    "ポイント還元", "入会", "楽天カード", "セゾン",
    "JCB", "オリコ", "三井住友カード", "アメックス",
    "ダイナース", "プラチナ", "ゴールドカード",
]


def load_news():
    if os.path.exists(NEWS_FILE):
        with open(NEWS_FILE, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return []
    return []


def save_news(news):
    with open(NEWS_FILE, "w", encoding="utf-8") as f:
        json.dump(news, f, ensure_ascii=False, indent=2)


def check_feeds():
    """Fetch and filter RSS feeds for credit card news."""
    all_news = load_news()
    existing_links = {n.get("link") for n in all_news}
    new_items = []

    for feed_url in FEEDS:
        print(f"  Fetching: {feed_url}")
        try:
            feed = feedparser.parse(feed_url)
            for entry in feed.entries:
                title = entry.get("title", "")
                summary = entry.get("summary", "")
                link = entry.get("link", "")

                if link in existing_links:
                    continue

                # Check if any keyword matches
                text = f"{title} {summary}"
                matched = [kw for kw in KEYWORDS if kw in text]

                if matched:
                    new_items.append({
                        "title": title,
                        "link": link,
                        "summary": summary[:200],
                        "published": entry.get("published", ""),
                        "matched_keywords": matched,
                        "fetched_at": datetime.datetime.now().isoformat(),
                    })
                    print(f"    ✦ Match: {title}")
        except Exception as e:
            print(f"    ⚠ Error: {e}")

    if new_items:
        all_news.extend(new_items)
        # Keep last 200
        all_news = all_news[-200:]
        save_news(all_news)
        print(f"\n✓ {len(new_items)} new articles saved")
    else:
        print("\n✓ No new articles found")

    return new_items


def main():
    print("=" * 50)
    print("  RSSフィード監視スクリプト")
    print("=" * 50)
    print(f"\n監視対象: {len(FEEDS)}フィード")
    print(f"キーワード: {', '.join(KEYWORDS[:5])}...\n")
    check_feeds()
    print("\n完了。\n")


if __name__ == "__main__":
    main()
