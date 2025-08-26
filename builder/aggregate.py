import pandas as pd


out_dir.mkdir(parents=True, exist_ok=True)


# Statements CSVs
save(st_daily.rename(columns={"date":"date"}), "Statements_date_data.csv")
save(st_month[["date","score"]], "Statements_month_data.csv")
save(st_quarter[["date","score"]], "Statements_quarter_data.csv")
save(st_month[["date","positive","neutral","negative"]], "Statements_month_ratio.csv")
save(st_quarter[["date","positive","neutral","negative"]], "Statements_quarter_ratio.csv")


# Minutes CSVs
save(mn_daily.rename(columns={"date":"date"}), "Minutes_date_data.csv")
save(mn_month[["date","score"]], "Minutes_month_data.csv")
save(mn_quarter[["date","score"]], "Minutes_quarter_data.csv")
save(mn_month[["date","positive","neutral","negative"]], "Minutes_month_ratio.csv")
save(mn_quarter[["date","positive","neutral","negative"]], "Minutes_quarter_ratio.csv")


# Headline JSONs used by the site
save(headline_m[["date","score","index_0_100"]], "index_monthly.json")
save(headline_q[["date","score","index_0_100"]], "index_quarterly.json")


# Latest snapshot
if not headline_m.empty:
latest = headline_m.sort_values("date").tail(1)
latest.to_json(out_dir / "latest_monthly.json", orient="records", force_ascii=False, date_format="iso")
