# クレジットカードおすすめ比較
Japanese credit card recommendation website with AdSense and auto-updating data.

## Setup
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python app.py
```

Visit [https://japanese-ccr.onrender.com](https://japanese-ccr.onrender.com)

## Features
- Interactive recommendation quiz
- Credit card database (JSON, auto-updatable)
- Google AdSense integration
- Data update scripts (scrape + manual edit)
- Mobile-responsive Japanese UI

## Affiliate (ASP) monetization
Application links run through `/go/<card_id>` (tracked, `robots.txt`-excluded) and
read `data/affiliate_links.json`. To switch a card to a real ASP tracking link:
1. Register with an ASP (A8.net, アクセストレード, etc.) and apply to the card program.
2. Paste the tracking URL into `tracking.<asp>` for that card in `data/affiliate_links.json`.
3. Set that card's `active` to the ASP key (e.g. `"a8"`). Commit + push — done.

`active: ""` falls back to the official site URL in `cards.json`.
Click analytics: `GET /api/clicks` (aggregated, no personal data).
Regenerate slots after adding cards: `python scripts/gen_affiliate_links.py`
