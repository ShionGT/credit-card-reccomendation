#!/bin/bash
# データ更新 cron ジョブ - Daily data update cron job
# Add to crontab: 0 6 * * * /Users/shion/Documents/GitHub/creditcardrecc/ccr/scripts/cron_update.sh

set -e

PROJECT_DIR="/Users/shion/Documents/GitHub/creditcardrecc/ccr"
cd "$PROJECT_DIR"

# Activate venv if exists
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
fi

echo "=== $(date) - データ更新開始 ==="

# 1. Update card data (scrape issuer sites)
echo "1. カードデータ更新..."
python scripts/update_data.py 2>&1 || echo "WARN: update_data.py failed"

# 2. Monitor news feeds
echo "2. ニュースフィード監視..."
python scripts/monitor_feeds.py 2>&1 || echo "WARN: monitor_feeds.py failed"

# 3. Git commit if changes
cd "$PROJECT_DIR/.."
if [ -n "$(git status --porcelain)" ]; then
    echo "3. Git にコミット..."
    git add -A
    git commit -m "auto: データ更新 $(date +%Y-%m-%d)"
fi

echo "=== $(date) - 完了 ==="
