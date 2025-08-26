import re
def _get(url: str) -> requests.Response:
r = requests.get(url, headers=HEADERS, timeout=30)
r.raise_for_status()
return r




def discover_statements():
html = _get(STATEMENTS_PAGE).text
soup = BeautifulSoup(html, "lxml")
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
except Exception:
continue
soup = BeautifulSoup(html, "lxml")
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
"""Download file → extract text (PDF/HTML) → save .txt and return its path."""
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
soup = BeautifulSoup(content, "lxml")
for tag in soup(["script", "style", "noscript"]):
tag.extract()
text = soup.get_text(separator="\n")


tpath = TEXT / f"{date_hint}_{sha}.txt"
tpath.write_text(text, encoding="utf-8")
return str(tpath)
