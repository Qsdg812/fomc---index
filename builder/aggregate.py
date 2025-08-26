from __future__ import annotations
import pandas as pd
from pathlib import Path

def _to_index(x: float) -> int:
    # [-1,1] → [0,100]
    x = float(x)
    if x < -1: x = -1
    if x > 1:  x = 1
    return int(round((x + 1.0) * 50.0))

def _save(df: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.suffix == ".json":
        df.to_json(path, orient="records", force_ascii=False, date_format="iso")
    else:
        df.to_csv(path, index=False)

def compute_timeseries(rows: list[dict], out_dir: Path) -> None:
    df = pd.DataFrame(rows)
    if df.empty:
        return

    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.dropna(subset=["date", "sentence"]).copy()

    # 라벨 예측 (여기에 실제 모델 연결 가능)
    from .sentiment import predict_labels
    df["label"] = predict_labels(df["sentence"].astype(str).tolist())

    # one-hot 비율
    df["positive"] = (df["label"] == 1).astype(int)
    df["neutral"]  = (df["label"] == 0).astype(int)
    df["negative"] = (df["label"] == -1).astype(int)

    # 일별 집계
    daily = (df.groupby([pd.Grouper(key="date", freq="D"), "doc_type"], as_index=False).agg(score=("label", "mean"), positive=("positive", "mean"),neutral=("neutral", "mean"), negative=("negative", "mean")).sort_values("date"))

    def resample(doc_type: str):
        part = daily[daily["doc_type"] == doc_type].set_index("date").sort_index()
        m = part.resample("MS").mean().reset_index()
        q = part.resample("QS").mean().reset_index()
        return part.reset_index(), m, q

    st_daily, st_month, st_quarter = resample("statement")
    mn_daily, mn_month, mn_quarter = resample("minutes")

    # 헤드라인(Statement/Minutes 평균)
    headline_m = (pd.concat([st_month.assign(src="statement"), mn_month.assign(src="minutes")], ignore_index=True).groupby("date", as_index=False)["score"].mean())
    headline_m["index_0_100"] = headline_m["score"].apply(_to_index)

    headline_q = (pd.concat([st_quarter.assign(src="statement"), mn_quarter.assign(src="minutes")], ignore_index=True).groupby("date", as_index=False)["score"].mean())
    headline_q["index_0_100"] = headline_q["score"].apply(_to_index)

    out_dir.mkdir(parents=True, exist_ok=True)

    # Statements 출력
    _save(st_daily.rename(columns={"date": "date"}), out_dir / "Statements_date_data.csv")
    _save(st_month[["date","score"]], out_dir / "Statements_month_data.csv")
    _save(st_quarter[["date","score"]], out_dir / "Statements_quarter_data.csv")
    _save(st_month[["date","positive","neutral","negative"]], out_dir / "Statements_month_ratio.csv")
    _save(st_quarter[["date","positive","neutral","negative"]], out_dir / "Statements_quarter_ratio.csv")

    # Minutes 출력
    _save(mn_daily.rename(columns={"date": "date"}), out_dir / "Minutes_date_data.csv")
    _save(mn_month[["date","score"]], out_dir / "Minutes_month_data.csv")
    _save(mn_quarter[["date","score"]], out_dir / "Minutes_quarter_data.csv")
    _save(mn_month[["date","positive","neutral","negative"]], out_dir / "Minutes_month_ratio.csv")
    _save(mn_quarter[["date","positive","neutral","negative"]], out_dir / "Minutes_quarter_ratio.csv")

    # 인덱스(0~100) 출력
    _save(headline_m[["date","score","index_0_100"]], out_dir / "index_monthly.json")
    _save(headline_q[["date","score","index_0_100"]], out_dir / "index_quarterly.json")

    # 최신 월간 1행
    if not headline_m.empty:
        latest = headline_m.sort_values("date").tail(1)
        latest.to_json(out_dir / "latest_monthly.json", orient="records", force_ascii=False, date_format="iso")
