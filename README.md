# Prospect Scraper (Streamlit)

A simple web app to find "Write for Us" / "Guest Post" pages for a given niche, extract emails & likely contact links, and export a CSV.

## Run locally
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```
Then open the local URL Streamlit shows (usually http://localhost:8501). Enter your **SERPAPI_API_KEY** in the sidebar.

## Deploy (Streamlit Community Cloud)
1. Push these three files to a **public GitHub repo**:
   - `app.py`
   - `requirements.txt`
   - `README.md`
2. On https://streamlit.io → **Deploy an app**, select your repo and branch, and set the main file to `app.py`.
3. Launch. Users will paste their own **SERPAPI_API_KEY** in the sidebar.

## Notes
- Be respectful of sites' TOS. This app uses modest delays.
- You can switch to Bing API with some code changes if preferred.