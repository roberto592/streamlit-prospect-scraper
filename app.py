
# app.py — Prospect Scraper (Streamlit) with Filters + Include-only Keywords
import re, time
from io import StringIO
from urllib.parse import urljoin, urlparse
import requests
from bs4 import BeautifulSoup
import streamlit as st

USER_AGENT = "ProspectScraper/0.4 (+contact: your-email@example.com)"
EMAIL_REGEX = re.compile(r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}", re.I)
CONTACT_KEYWORDS = ["contact", "contact us", "about", "editor", "pitch", "media", "press", "submit", "guidelines"]

DEFAULT_EXCLUDES = "facebook.com,pinterest.com,linkedin.com,instagram.com,twitter.com,t.co,youtube.com,medium.com,reddit.com,quora.com"
DEFAULT_INCLUDES = "guest post,write for us,submit an article,contribute,editorial guidelines"

def extract_emails(text):
    return sorted(set(m.group(0) for m in EMAIL_REGEX.finditer(text)))

def extract_domain(url):
    try:
        netloc = urlparse(url).netloc.lower()
        parts = netloc.split(".")
        return ".".join(parts[-2:]) if len(parts) >= 2 else netloc
    except:
        return ""

def domain_allowed(domain: str, allowed_tlds_only: bool) -> bool:
    if not domain:
        return False
    if allowed_tlds_only:
        return domain.endswith(".com") or domain.endswith(".org")
    return True

def serpapi_search(query, api_key, num=20):
    endpoint = "https://serpapi.com/search.json"
    r = requests.get(
        endpoint,
        params={"q": query, "engine": "google", "api_key": api_key, "num": min(num, 100)},
        headers={"User-Agent": USER_AGENT},
        timeout=20,
    )
    r.raise_for_status()
    data = r.json()
    out = []
    for item in data.get("organic_results", []):
        out.append({
            "title": item.get("title", ""),
            "url": item.get("link", ""),
            "snippet": item.get("snippet", ""),
        })
    return out

def fetch_html(url):
    try:
        r = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=20)
        if r.status_code >= 400:
            return ""
        return r.text
    except:
        return ""

def extract_links(soup, base_url):
    links = []
    for a in soup.find_all("a", href=True):
        full = urljoin(base_url, a["href"])
        txt = (a.get_text() or "").strip().lower()
        links.append((txt, full))
    return links

def find_candidate_contact_links(links):
    seen, out = set(), []
    for txt, url in links:
        if any(kw in txt for kw in CONTACT_KEYWORDS):
            if url not in seen:
                out.append(url); seen.add(url)
    return out[:10]

def search_queries(niche):
    b = niche.strip()
    return [
        f'"write for us" {b}',
        f'"guest post" {b}',
        f'"contribute" {b}',
        f'"submit an article" {b}',
        f'"editorial guidelines" {b}',
    ]

def parse_csv_list(s: str):
    return [t.strip().lower() for t in s.split(",") if t.strip()]

def matches_include_keywords(rec, include_terms):
    if not include_terms:
        return True
    hay = " ".join([rec.get("title",""), rec.get("url",""), rec.get("snippet","")]).lower()
    return any(term in hay for term in include_terms)

st.set_page_config(page_title="Prospect Scraper", page_icon="🔎", layout="centered")
st.title("🔎 Prospect Scraper (Guest Post / Write For Us)")

with st.sidebar:
    st.markdown("**Engine**: SerpAPI (Google)")
    serp_key = st.text_input("SERPAPI_API_KEY", type="password", help="Your SerpAPI key (not stored).")
    niche = st.text_input("Niche / Topic", value="digital marketing")
    limit = st.slider("Results per query", 10, 100, 25, 5)
    delay = st.slider("Delay between requests (sec)", 0.0, 5.0, 1.5, 0.5)
    st.markdown("---")
    st.subheader("Filters")
    excludes_str = st.text_input("Exclude domains (comma-separated)", DEFAULT_EXCLUDES)
    only_com_org = st.checkbox("Only include .com or .org", value=True)
    include_str = st.text_input("Include-only keywords (comma-separated)", DEFAULT_INCLUDES,
                                help="Results must contain at least one of these terms in title, URL, or snippet.")
    run = st.button("Run search")

if run:
    if not serp_key:
        st.error("Please enter your SERPAPI_API_KEY in the sidebar.")
    elif not niche.strip():
        st.error("Please enter a niche.")
    else:
        exclude_set = set(parse_csv_list(excludes_str))
        include_terms = parse_csv_list(include_str)

        progress = st.progress(0)
        status = st.empty()
        all_results = []
        queries = search_queries(niche)
        for i, q in enumerate(queries, 1):
            status.write(f"Searching: {q}")
            try:
                all_results += serpapi_search(q, serp_key, num=limit)
            except Exception as e:
                st.warning(f"Search failed for '{q}': {e}")
            progress.progress(int(i / len(queries) * 33))
            time.sleep(delay)

        # 1) Dedupe URLs
        seen_urls, deduped = set(), []
        for r in all_results:
            url = r["url"]
            if url and url not in seen_urls:
                seen_urls.add(url); deduped.append(r)

        # 2) Apply include-only & exclude & TLD BEFORE domain-level dedupe
        filtered = []
        for r in deduped:
            d = extract_domain(r["url"])
            if not d:
                continue
            if exclude_set and any(ex in d for ex in exclude_set):
                continue
            if not domain_allowed(d, only_com_org):
                continue
            if not matches_include_keywords(r, include_terms):
                continue
            filtered.append(r)

        # 3) One result per domain
        seen_domains, per_domain = set(), []
        for r in filtered:
            d = extract_domain(r["url"])
            if d and d not in seen_domains:
                seen_domains.add(d); per_domain.append(r)

        rows = []
        for i, item in enumerate(per_domain, 1):
            url = item["url"]; title = item.get("title", ""); snippet = item.get("snippet", "")
            status.write(f"Visiting ({i}/{len(per_domain)}): {url}")
            html = fetch_html(url)
            emails = extract_emails(html) if html else []
            contacts = []
            if html:
                soup = BeautifulSoup(html, "html.parser")
                contacts = find_candidate_contact_links(extract_links(soup, url))
            rows.append({
                "domain": extract_domain(url),
                "url": url,
                "title": title,
                "snippet": snippet,
                "emails": ";".join(emails[:5]),
                "contact_links": ";".join(contacts),
            })
            progress.progress(33 + int(i / len(per_domain) * 67))
            time.sleep(delay)

        st.success(f"Done! Collected {len(rows)} prospects after filtering.")
        st.dataframe(rows, use_container_width=True)

        # CSV download
        import csv
        output = StringIO()
        writer = csv.DictWriter(output, fieldnames=["domain","url","title","snippet","emails","contact_links"])
        writer.writeheader()
        for r in rows: writer.writerow(r)
        st.download_button("Download CSV", output.getvalue().encode("utf-8"), file_name="prospects.csv", mime="text/csv")
        status.empty(); progress.empty()
