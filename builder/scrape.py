import re
from datetime import datetime
import requests
from bs4 import BeautifulSoup
from pdfminer.high_level import extract_text
from .utils import RAW, TEXT, sha256_bytes

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; FOMC-Sentiment/1.0)"}
STATEMENTS_PAGE = "https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm"
MINUTES_YEAR_TPL = "https://www.federalreserve.gov/monetarypolicy/fomcminutes{year}.htm"
DATE_8_RE = re.compile(r"(20\d{2})(\d{2})(\d{2})")
STATEMENT_HREF_RE = re.compile(r"/pressreleases/monetary\d{8}[a-z]?\.htm", re.I)
PDF_RE = re.compile(r"\.pdf$", re.I)

def _get(url: str) -> requests.Response:
    r = requests.get(url, headers=HEADERS, timeout=30)
    r.raise_for_status()
    return r

def discover_statements():
    try:
        html = _get(STATEMENTS_PAGE).text
    except Exception as e:
        print("[warn] discover_statements: fetch failed:", e)
        return []
    soup = BeautifulSoup(html, "html.parser")
    out = []
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if STATEMENT_HREF_RE.search(href):
            abs_url = "https://www.federalreserve.gov" + href if href.startswith("/") else href
            m = DATE_8_RE.search(href)
            if not m:
                continue
            y, mth, d = m.groups()
            dt = datetime(int(y), int(mth), int(d)).date()
            out.append((dt, abs_url))
    out = sorted(set(out), key=lambda x: x[0])
    return out

def discover_minutes(years_back: int = 6):
    out = []
    today = datetime.utcnow().date()
    for y in range(today.year, today.year - years_back, -1):
        url = MINUTES_YEAR_TPL.format(year=y)
        try:
            html = _get(url).text
        except Exception as e:
            print("[warn] discover_minutes: fetch year page failed:", url, e)
            continue
        soup = BeautifulSoup(html, "html.parser")
        for a in soup.find_all("a", href=True):
            href = a["href"]
            text = (a.get_text() or "").lower()
            if "minutes" in text or PDF_RE.search(href):
                abs_url = "https://www.federalreserve.gov" + href if href.startswith("/") else href
                m = DATE_8_RE.search(href)
                if not m:
                    continue
                y2, m2, d2 = m.groups()
                dt = datetime(int(y2), int(m2), int(d2)).date()
                out.append((dt, abs_url))
    out = sorted(set(out), key=lambda x: x[0])
    return out

def download_and_extract(url: str, date_hint: str) -> str:
    r = _get(url)
    content = r.content
    sha = sha256_bytes(content)[:10]
    is_pdf = PDF_RE.search(url) is not None
    ext = ".pdf" if is_pdf else ".html"
    raw_path = RAW / f"{date_hint}_{sha}{ext}"
    raw_path.write_bytes(content)

    if is_pdf:
        text = extract_text(str(raw_path))
    else:
        soup = BeautifulSoup(content, "html.parser")
        for tag in soup(["script", "style", "noscript"]):
            tag.extract()
        text = soup.get_text(separator="\n")

    tpath = TEXT / f"{date_hint}_{sha}.txt"
    tpath.write_text(text, encoding="utf-8")
    return str(tpath)
