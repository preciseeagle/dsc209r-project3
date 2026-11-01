#!/usr/bin/env python3
"""Build data.json for the Project 3 overdose explorer from the CDC VSRR dataset.

Pulls "VSRR Provisional Drug Overdose Death Counts" (CDC Socrata id xkb8-kh2a),
aggregates to state x 12-month-ending-period x drug-indicator, merges NYC into
New York (so state values join the us-atlas geometry), adds per-100k death
rates using 2020 Census population, and writes ../data.json.

Usage:
    python3 data/build_data.py
If data/raw_data.csv is missing it is fetched from the CDC API first (it is
gitignored because it is ~17 MB).
"""
import csv
import json
import os
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
RAW = os.path.join(HERE, "raw_data.csv")
OUT = os.path.join(ROOT, "data.json")
CDC_URL = "https://data.cdc.gov/resource/xkb8-kh2a.csv?$limit=200000"

# CDC indicator string -> our short key
IND = {
    "Number of Drug Overdose Deaths": "total",
    "Opioids (T40.0-T40.4,T40.6)": "opioids",
    "Synthetic opioids, excl. methadone (T40.4)": "synthetic",
    "Heroin (T40.1)": "heroin",
    "Cocaine (T40.5)": "cocaine",
    "Psychostimulants with abuse potential (T43.6)": "psychostim",
}
LABELS = {
    "total": "All drug overdose deaths",
    "opioids": "Opioids",
    "synthetic": "Synthetic opioids (fentanyl)",
    "heroin": "Heroin",
    "cocaine": "Cocaine",
    "psychostim": "Psychostimulants",
}
MON = {m: i for i, m in enumerate(
    ["January", "February", "March", "April", "May", "June", "July",
     "August", "September", "October", "November", "December"], start=1)}
NATIONAL = "United States"
MERGE = {"New York City": "New York"}  # CDC reports NYC separately; fold into NY

# April 1, 2020 resident population (Census Bureau, 2020 Census-based estimates
# base, NST-EST2023-ALLDATA). Used as a fixed denominator for every period.
POP = {
    "Alabama": 5024294,
    "Alaska": 733374,
    "Arizona": 7157902,
    "Arkansas": 3011490,
    "California": 39538212,
    "Colorado": 5773707,
    "Connecticut": 3605912,
    "Delaware": 989946,
    "District of Columbia": 689548,
    "Florida": 21538216,
    "Georgia": 10713771,
    "Hawaii": 1455274,
    "Idaho": 1839117,
    "Illinois": 12813469,
    "Indiana": 6785442,
    "Iowa": 3190427,
    "Kansas": 2937835,
    "Kentucky": 4506297,
    "Louisiana": 4657785,
    "Maine": 1363177,
    "Maryland": 6177253,
    "Massachusetts": 7032933,
    "Michigan": 10077674,
    "Minnesota": 5706804,
    "Mississippi": 2961306,
    "Missouri": 6154889,
    "Montana": 1084244,
    "Nebraska": 1961965,
    "Nevada": 3104617,
    "New Hampshire": 1377524,
    "New Jersey": 9289039,
    "New Mexico": 2117525,
    "New York": 20202320,
    "North Carolina": 10439459,
    "North Dakota": 779079,
    "Ohio": 11799331,
    "Oklahoma": 3959411,
    "Oregon": 4237279,
    "Pennsylvania": 13002788,
    "Puerto Rico": 3285874,
    "Rhode Island": 1097371,
    "South Carolina": 5118422,
    "South Dakota": 886668,
    "Tennessee": 6910786,
    "Texas": 29145459,
    "Utah": 3271614,
    "Vermont": 643077,
    "Virginia": 8631373,
    "Washington": 7705267,
    "West Virginia": 1793713,
    "Wisconsin": 5893713,
    "Wyoming": 576850,
    "United States": 331464948,
}


def num(v):
    v = (v or "").replace(",", "").strip()
    try:
        return float(v) if v else None
    except ValueError:
        return None


def main():
    if not os.path.exists(RAW):
        print("raw_data.csv not found; fetching from the CDC API...")
        urllib.request.urlretrieve(CDC_URL, RAW)

    rows = list(csv.DictReader(open(RAW)))
    periods = set()
    acc = {k: {} for k in LABELS}
    for r in rows:
        ik = IND.get(r["indicator"])
        if not ik:
            continue
        try:
            y, m = int(r["year"]), MON.get(r["month"], 0)
        except (ValueError, KeyError):
            continue
        if not m:
            continue
        val = num(r.get("data_value"))
        if val is None:
            continue
        st = MERGE.get(r["state_name"].strip(), r["state_name"].strip())
        periods.add((y, m))
        d = acc[ik].setdefault(st, {})
        d[(y, m)] = (d.get((y, m)) or 0) + val

    periods = sorted(periods)
    states = sorted({s for ik in acc for s in acc[ik]} - {NATIONAL})
    mn = ["", "Jan", "Feb", "Mar", "Apr", "May", "Jun",
          "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

    def arr(ik, st):
        d = acc[ik].get(st, {})
        return [round(d[p]) if p in d else None for p in periods]

    def arr_rate(ik, st):
        # deaths per 100k residents; None when the count or population is missing
        pop = POP.get(st)
        return [round(v / pop * 100000, 2) if v is not None and pop else None
                for v in arr(ik, st)]

    out = {
        "periods": [f"{y}-{m:02d}" for y, m in periods],
        "periodLabels": [f"12-mo ending {mn[m]} {y}" for y, m in periods],
        "indicatorLabels": LABELS,
        "states": states,
        "series": {ik: {st: arr(ik, st) for st in states} for ik in LABELS},
        "national": {ik: arr(ik, NATIONAL) for ik in LABELS},
        "rate": {ik: {st: arr_rate(ik, st) for st in states} for ik in LABELS},
        "nationalRate": {ik: arr_rate(ik, NATIONAL) for ik in LABELS},
    }
    json.dump(out, open(OUT, "w"))
    print(f"wrote {OUT}: {len(periods)} periods, {len(states)} states, "
          f"{len(LABELS)} indicators")


if __name__ == "__main__":
    main()
