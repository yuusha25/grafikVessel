"""
Perbarui ring_data.json dari ml/dataset/ring_measurements_long.csv (pengukuran
fisik vertical clearance ring piston, 4 ring per cylinder).

Beda dari update_data.py (data operasional mingguan): file ini levelnya
pengukuran fisik langsung -- lebih jarang, per kunjungan/inspeksi.

    python update_ring_data.py
    vercel --prod
"""
import json
import os

import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
SRC_CSV = os.path.join(HERE, "..", "..", "ml", "dataset", "ring_measurements_long.csv")
OUT_JSON = os.path.join(HERE, "ring_data.json")

THRESHOLD_MM = 0.70  # batas vertical clearance -- di atas ini, ring piston seharusnya diganti

df = pd.read_csv(SRC_CSV)
df["report_date"] = pd.to_datetime(df["report_date"])


def cv(v, dec=3):
    return None if pd.isna(v) else round(float(v), dec)


vessels_payload = {}
for vessel, gv in df.groupby("vessel_code"):
    cylinders = {}
    for cyl, gc in gv.groupby("cylinder_no"):
        reports = gc.drop_duplicates("report_date").sort_values("report_date")
        dates, avg_old, avg_new, replaced, ring_hours = [], [], [], [], []
        rings = {str(r): [] for r in range(1, 5)}
        for d in reports.report_date:
            rows = gc[gc.report_date == d].sort_values("ring_no")
            dates.append(d.strftime("%Y-%m-%d"))
            old_vals = rows["vertical_clearance_old"].tolist()
            new_vals = rows["vertical_clearance_new"].tolist()
            avg_old.append(cv(sum(old_vals) / len(old_vals)) if old_vals else None)
            new_present = [v for v in new_vals if pd.notna(v)]
            avg_new.append(cv(sum(new_present) / len(new_present)) if new_present else None)
            replaced.append(bool(rows["is_replacement_event"].any()))
            rh = rows["ring_hours"].dropna()
            ring_hours.append(cv(rh.iloc[0], 0) if len(rh) else None)
            for r in range(1, 5):
                rr = rows[rows.ring_no == r]
                rings[str(r)].append(cv(rr["vertical_clearance_old"].iloc[0]) if len(rr) else None)
        cylinders[str(int(cyl))] = {
            "dates": dates, "avg_old": avg_old, "avg_new": avg_new,
            "is_replacement": replaced, "ring_hours": ring_hours, "rings": rings,
        }
    vessels_payload[vessel] = {
        "vessel_name": gv["vessel_name"].iloc[0],
        "cylinders": cylinders,
        "n_reports": int(gv.report_date.nunique()),
        "date_min": gv.report_date.min().strftime("%Y-%m-%d"),
        "date_max": gv.report_date.max().strftime("%Y-%m-%d"),
    }

payload = {
    "vessels": vessels_payload,
    "meta": {
        "threshold_mm": THRESHOLD_MM,
        "date_min": df.report_date.min().strftime("%Y-%m-%d"),
        "date_max": df.report_date.max().strftime("%Y-%m-%d"),
        "n_rows": int(len(df)),
        "n_replacement_events": int(df.is_replacement_event.sum()),
    },
}

with open(OUT_JSON, "w", encoding="utf-8") as f:
    json.dump(payload, f, separators=(",", ":"))

print(f"ring_data.json diperbarui: {os.path.getsize(OUT_JSON) / 1024:.1f} KB")
print(f"  kapal dengan data ring: {list(vessels_payload.keys())}")
for v, d in vessels_payload.items():
    print(f"  {v}: {len(d['cylinders'])} cylinder, {d['n_reports']} laporan, {d['date_min']}..{d['date_max']}")
