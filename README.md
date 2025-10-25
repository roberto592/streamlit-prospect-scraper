# Prospect Scraper (Streamlit) — Pagination Edition

**New:** Fetch multiple pages per query + cap results per domain.

## What's new
- **Results per page (num)**: up to 100 per query page
- **Pages per query**: up to 5 (uses SerpAPI `start` offset)
- **Max results per domain**: keep more than 1 URL from the same site if desired
- Works with your existing: excludes, .com/.org filter, include-only keywords

## Run locally
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```
