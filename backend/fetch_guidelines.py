"""
fetch_guidelines.py
--------------------
Bulk-downloads clinical practice guidelines from WHO and NICE into
backend/guideline_docs/ for ingestion into the CDSS ChromaDB store.

Run this on YOUR machine (not in a restricted sandbox) since it needs
open internet access to who.int and nice.org.uk.

Install dependencies first:
    pip install requests beautifulsoup4

Usage:
    python fetch_guidelines.py --source who --limit 50
    python fetch_guidelines.py --source nice --limit 100
    python fetch_guidelines.py --source both

If NICE returns 0 results, re-run with --debug to save the raw HTML
response to nice_debug.html so we can see what's actually being returned:
    python fetch_guidelines.py --source nice --limit 5 --debug
"""

import argparse
import os
import re
import time

import requests
from bs4 import BeautifulSoup

# Realistic browser-like headers to reduce the chance of being served a
# stripped-down / bot-detection page instead of the real listing.
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.nice.org.uk/guidance",
}

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "guideline_docs")

WHO_LISTING_URL = "https://www.who.int/publications/i?publishingoffices=c09761c0-ab8e-4cfa-9744-99509c4d306b&page={page}"
NICE_LISTING_URL = "https://www.nice.org.uk/guidance/published?ps=50&pa={page}"

NICE_RELEVANT_PREFIXES = ("NG", "CG", "PH")

session = requests.Session()
session.headers.update(HEADERS)


def safe_filename(name: str, max_len: int = 120) -> str:
    name = re.sub(r"[^\w\-. ]", "_", name).strip()
    name = re.sub(r"\s+", "_", name)
    return name[:max_len] if len(name) > max_len else name


def download_pdf(url: str, dest_path: str) -> bool:
    if os.path.exists(dest_path) and os.path.getsize(dest_path) > 1024:
        print(f"  [SKIP-EXISTS] already have {os.path.basename(dest_path)}")
        return True
    try:
        resp = session.get(url, timeout=30)
        resp.raise_for_status()
        content_type = resp.headers.get("Content-Type", "")
        if "text/html" in content_type.lower():
            print(f"  [SKIP] {url} returned HTML, not a PDF (Content-Type: {content_type})")
            return False
        with open(dest_path, "wb") as f:
            f.write(resp.content)
        print(f"  [OK] saved {os.path.basename(dest_path)} ({len(resp.content)//1024} KB)")
        return True
    except requests.RequestException as e:
        print(f"  [FAIL] {url} -> {e}")
        return False


def fetch_who(limit: int, delay: float = 1.0, debug: bool = False):
    print("\n=== WHO Guidelines ===")
    out_dir = os.path.join(OUTPUT_DIR, "who")
    os.makedirs(out_dir, exist_ok=True)

    downloaded = 0
    page = 0
    while downloaded < limit:
        url = WHO_LISTING_URL.format(page=page)
        print(f"Fetching listing page {page}: {url}")
        try:
            resp = session.get(url, timeout=30)
            resp.raise_for_status()
        except requests.RequestException as e:
            print(f"  [FAIL] could not fetch listing page: {e}")
            break

        if debug and page == 0:
            with open("who_debug.html", "w", encoding="utf-8") as f:
                f.write(resp.text)
            print(f"  [DEBUG] saved raw response ({len(resp.text)} chars) to who_debug.html")

        soup = BeautifulSoup(resp.text, "html.parser")
        found_this_page = 0
        seen_titles = set()

        items = soup.find_all(string=re.compile(r"^Download$"))
        for dl_text in items:
            dl_link = dl_text.find_parent("a")
            if not dl_link or not dl_link.get("href"):
                continue
            pdf_url = dl_link["href"]
            if "bitstream" not in pdf_url:
                continue

            container = dl_link.find_parent()
            title = None
            for _ in range(6):
                if container is None:
                    break
                heading = container.find(["h3", "h2"])
                if heading and heading.get_text(strip=True):
                    title = heading.get_text(strip=True)
                    break
                container = container.find_parent()
            if not title:
                title = f"who_guideline_{downloaded+1}"
            if title in seen_titles:
                continue
            seen_titles.add(title)

            fname = safe_filename(title) + ".pdf"
            dest = os.path.join(out_dir, fname)
            print(f"[{downloaded+1}/{limit}] {title}")
            if download_pdf(pdf_url, dest):
                downloaded += 1
                found_this_page += 1
            time.sleep(delay)
            if downloaded >= limit:
                break

        if found_this_page == 0:
            print("No more results found, stopping.")
            break
        page += 1

    print(f"\nWHO: downloaded {downloaded} guideline PDFs to {out_dir}")


def fetch_nice(limit: int, delay: float = 1.0, debug: bool = False):
    print("\n=== NICE Guidelines ===")
    out_dir = os.path.join(OUTPUT_DIR, "nice")
    os.makedirs(out_dir, exist_ok=True)

    downloaded = 0
    page = 1
    while downloaded < limit:
        url = NICE_LISTING_URL.format(page=page)
        print(f"Fetching listing page {page}: {url}")
        try:
            resp = session.get(url, timeout=30)
            resp.raise_for_status()
            print(f"  [INFO] status={resp.status_code} length={len(resp.text)} chars")
        except requests.RequestException as e:
            print(f"  [FAIL] could not fetch listing page: {e}")
            break

        if debug and page == 1:
            with open("nice_debug.html", "w", encoding="utf-8") as f:
                f.write(resp.text)
            print("  [DEBUG] saved raw response to nice_debug.html -- open it and search for 'guidance/ng' to check if data is present")

        soup = BeautifulSoup(resp.text, "html.parser")
        rows = soup.select("table a[href*='/guidance/']")
        if not rows:
            rows = soup.find_all("a", href=re.compile(r"/guidance/[a-zA-Z]+\d+$"))

        candidates = []
        for a in rows:
            href = a.get("href", "")
            m = re.search(r"/guidance/([a-zA-Z]+)(\d+)$", href)
            if not m:
                continue
            prefix = m.group(1).upper()
            if prefix not in NICE_RELEVANT_PREFIXES:
                continue
            title = a.get_text(strip=True)
            ref = prefix + m.group(2)
            full_url = href if href.startswith("http") else "https://www.nice.org.uk" + href
            candidates.append((ref, title, full_url))

        seen = set()
        unique_candidates = []
        for c in candidates:
            if c[0] not in seen:
                seen.add(c[0])
                unique_candidates.append(c)
        candidates = unique_candidates

        print(f"  [INFO] found {len(rows)} raw links, {len(candidates)} matching NG/CG/PH guidelines on this page")

        if not candidates:
            print("No more relevant guidelines found, stopping.")
            break

        for ref, title, guidance_url in candidates:
            if downloaded >= limit:
                break
            print(f"[{downloaded+1}/{limit}] {ref}: {title}")
            try:
                page_resp = session.get(guidance_url, timeout=30)
                page_resp.raise_for_status()
            except requests.RequestException as e:
                print(f"  [FAIL] could not fetch guideline page: {e}")
                continue

            page_soup = BeautifulSoup(page_resp.text, "html.parser")
            pdf_link = page_soup.find("a", string=re.compile(r"Download guidance", re.I))
            if not pdf_link or not pdf_link.get("href"):
                pdf_link = page_soup.find("a", href=re.compile(r"-pdf-\d+"))
            if not pdf_link:
                print("  [SKIP] no PDF link found on this guideline's page")
                time.sleep(delay)
                continue

            pdf_url = pdf_link["href"]
            if pdf_url.startswith("/"):
                pdf_url = "https://www.nice.org.uk" + pdf_url

            fname = safe_filename(f"{ref}_{title}") + ".pdf"
            dest = os.path.join(out_dir, fname)
            if download_pdf(pdf_url, dest):
                downloaded += 1
            time.sleep(delay)

        page += 1

    print(f"\nNICE: downloaded {downloaded} guideline PDFs to {out_dir}")


def main():
    parser = argparse.ArgumentParser(description="Bulk-download WHO/NICE clinical guidelines")
    parser.add_argument("--source", choices=["who", "nice", "both"], default="both")
    parser.add_argument("--limit", type=int, default=50, help="Max documents per source")
    parser.add_argument("--delay", type=float, default=1.0, help="Seconds between requests (be polite)")
    parser.add_argument("--debug", action="store_true", help="Save raw HTML of first listing page for inspection")
    args = parser.parse_args()

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    if args.source in ("who", "both"):
        fetch_who(args.limit, args.delay, args.debug)
    if args.source in ("nice", "both"):
        fetch_nice(args.limit, args.delay, args.debug)

    print(f"\nDone. All PDFs are under: {OUTPUT_DIR}")
    print("Next step: point ingest.py's DOCS_DIR at this folder (or merge subfolders) and re-run ingestion.")


if __name__ == "__main__":
    main()