import os, json
from datetime import datetime, date
from .utils import SITE_DATA

OFFLINE_ONLY = os.getenv("OFFLINE_ONLY") == "1"

# ---- 공통: 전처리/집계만 필요 ----
from .preprocess import preprocess_text_files
from .aggregate import compute_timeseries

def write_stub(outdir=SITE_DATA):
    """오프라인/빈 데이터일 때도 사이트가 비지 않게 스텁 생성"""
    outdir.mkdir(parents=True, exist_ok=True)
    stub = [{
        "date": f"{date.today().isoformat()}T00:00:00.000Z",
        "score": 0.0,
        "index_0_100": 50
    }]
    (outdir / "index_monthly.json").write_text(json.dumps(stub), encoding="utf-8")
    (outdir / "latest_monthly.json").write_text(json.dumps(stub), encoding="utf-8")
    # 선택: 링크용 CSV 스텁(비어있어도 문제 없음)
    for name in [
        "Statements_month_ratio.csv",
        "Minutes_month_ratio.csv",
        "Statements_month_data.csv",
        "Minutes_month_data.csv"
    ]:
        (outdir / name).write_text("date,score\n", encoding="utf-8")

def run_online():
    # 온라인 모드에서는 여기서만 scrape 모듈을 import (의존성 실패 회피)
    from .scrape import discover_statements, discover_minutes, download_and_extract

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

    # 5) 아무 파일도 안 나오면 스텁 생성
    if not (SITE_DATA / "index_monthly.json").exists():
        write_stub(SITE_DATA)

def run_offline():
    # 네트워크 완전 스킵 + 스텁 생성
    write_stub(SITE_DATA)

if __name__ == "__main__":
    if OFFLINE_ONLY:
        print("[info] OFFLINE_ONLY=1 → offline stub mode")
        run_offline()
    else:
        print("[info] OFFLINE_ONLY not set → online mode")
        run_online()
    print("[OK] Build completed at", datetime.utcnow().isoformat() + "Z")
