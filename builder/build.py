from datetime import datetime, date
import json
from .utils import SITE_DATA
from .scrape import discover_statements, discover_minutes, download_and_extract
from .preprocess import preprocess_text_files
from .aggregate import compute_timeseries

# 1) discover (실패해도 계속)
try:
    statements = discover_statements()
except Exception as e:
    print("[warn] discover_statements crashed:", e)
    statements = []

try:
    minutes = discover_minutes(years_back=6)
except Exception as e:
    print("[warn] discover_minutes crashed:", e)
    minutes = []

# 2) download (실패한 URL은 건너뜀)
text_paths: list[str] = []
for d, url in (statements + minutes):
    try:
        t = download_and_extract(url, date_hint=str(d))
        text_paths.append(t)
    except Exception as e:
        print("[warn] Download failed", url, e)

# 3) preprocess → rows
rows = preprocess_text_files(text_paths)

# 4) aggregate → site/data
compute_timeseries(rows, SITE_DATA)

# 5) 오프라인/빈 데이터일 때도 사이트가 비지 않게 스텁 JSON 생성
SITE_DATA.mkdir(parents=True, exist_ok=True)
index_monthly = SITE_DATA / "index_monthly.json"
latest_monthly = SITE_DATA / "latest_monthly.json"
if not index_monthly.exists():
    stub = [{
        "date": f"{date.today().isoformat()}T00:00:00.000Z",
        "score": 0.0,
        "index_0_100": 50
    }]
    index_monthly.write_text(json.dumps(stub), encoding="utf-8")
    latest_monthly.write_text(json.dumps(stub), encoding="utf-8")

print("[OK] Build completed at", datetime.utcnow().isoformat() + "Z")
