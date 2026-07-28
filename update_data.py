"""
Perbarui data.json dashboard dari dataset/processed/cylinder_timeseries_clean.csv.

Jalankan ini kapan pun cylinder_timeseries_clean.csv sudah diperbarui (mis. ada
laporan mingguan baru masuk lalu dijalankan ulang clean_cylinder_timeseries.py),
lalu redeploy (lihat README.md).

    python update_data.py
    vercel --prod
"""
import json
import os

import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
SRC_CSV = os.path.join(HERE, "..", "dataset", "processed", "cylinder_timeseries_clean.csv")
OUT_JSON = os.path.join(HERE, "data.json")

df = pd.read_csv(SRC_CSV)
df["report_date"] = pd.to_datetime(df["report_date"])

CYL_METRICS = [
    "fuel_pump_index", "vit_index", "p_comp_kgcm2", "p_max_kgcm2",
    "exhaust_temp_c", "jcw_temp_c", "piston_cooling_outlet_temp_c",
]
CONTEXT_METRICS = ["total_running_hours", "rh_this_week", "load_pct", "fuel_sulphur_pct"]
CONTEXT_DEC = {"total_running_hours": 0, "rh_this_week": 1, "load_pct": 1, "fuel_sulphur_pct": 2}


def clean_val(v, dec):
    return None if pd.isna(v) else round(float(v), dec)


def cyl_series_payload(g):
    g = g.sort_values("report_date")
    out = {"dates": g["report_date"].dt.strftime("%Y-%m-%d").tolist()}
    for m in CYL_METRICS:
        dec = 1 if m in ("fuel_pump_index", "vit_index", "p_comp_kgcm2", "p_max_kgcm2") else 0
        out[m] = [clean_val(v, dec) for v in g[m]]
    out["qc_anomali_cols"] = [v if isinstance(v, str) and v else None for v in g["qc_anomali_cols"]]
    out["qc_sistematik_cols"] = [v if isinstance(v, str) and v else None for v in g["qc_sistematik_cols"]]
    out["qc_imputed_cols"] = [v if isinstance(v, str) and v else None for v in g["qc_imputed_cols"]]
    return out


vessels_payload = {}
for vessel, gv in df.groupby("vessel_code"):
    units = {}
    for unit, gu in gv.groupby("unit_no"):
        units[str(int(unit))] = cyl_series_payload(gu)

    rep = gv.drop_duplicates("report_date").sort_values("report_date")
    context = {"dates": rep["report_date"].dt.strftime("%Y-%m-%d").tolist()}
    for m in CONTEXT_METRICS:
        context[m] = [clean_val(v, CONTEXT_DEC[m]) for v in rep[m]]
    context["qc_trh_turun"] = [bool(v) for v in rep["qc_trh_turun"]]

    vessels_payload[vessel] = {
        "vessel_name": gv["vessel_name"].iloc[0],
        "units": units,
        "context": context,
        "n_reports": int(rep.shape[0]),
        "date_min": gv.report_date.min().strftime("%Y-%m-%d"),
        "date_max": gv.report_date.max().strftime("%Y-%m-%d"),
    }

payload = {
    "vessels": vessels_payload,
    "cyl_metrics": CYL_METRICS,
    "context_metrics": CONTEXT_METRICS,
    "meta": {
        "date_min": df.report_date.min().strftime("%Y-%m-%d"),
        "date_max": df.report_date.max().strftime("%Y-%m-%d"),
        "n_reports": int(df.drop_duplicates(["vessel_code", "report_date"]).shape[0]),
        "n_rows": int(len(df)),
        "n_anomaly": int(df.qc_anomali_cols.notna().sum()),
        "n_systematic": int(df.qc_sistematik_cols.notna().sum()),
        "n_imputed": int(df.qc_imputed_cols.notna().sum()),
        "n_trh_turun": int(df.qc_trh_turun.sum()),
    },
}

with open(OUT_JSON, "w", encoding="utf-8") as f:
    json.dump(payload, f, separators=(",", ":"))

print(f"data.json diperbarui: {os.path.getsize(OUT_JSON) / 1024:.1f} KB")
print(f"  {payload['meta']['n_reports']} laporan, {payload['meta']['date_min']} s/d {payload['meta']['date_max']}")
print("Langkah selanjutnya: jalankan  vercel --prod  di folder ini untuk publish perubahan.")
