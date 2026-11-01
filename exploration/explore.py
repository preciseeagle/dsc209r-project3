#!/usr/bin/env python3
"""
DSC209R Project 3 - Exploratory Visualizations
CDC VSRR Provisional Drug Overdose Death Counts
"""
import csv
import os
import sys
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from collections import defaultdict
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'data'))
from build_data import POP  # 2020 Census populations, same table as the site
os.chdir(HERE)

# Load data
print("Loading data...")
with open(os.path.join(HERE, '..', 'data', 'raw_data.csv'), 'r') as f:
    reader = csv.DictReader(f)
    rows = list(reader)

print(f"Loaded {len(rows)} rows")

# Clean and parse data
def clean_value(val):
    """Convert data value to float, handling commas and empty strings"""
    if not val or val.strip() == '':
        return np.nan
    return float(val.replace(',', ''))

def month_to_num(month_str):
    """Convert month name to number"""
    months = {
        'January': 1, 'February': 2, 'March': 3, 'April': 4,
        'May': 5, 'June': 6, 'July': 7, 'August': 8,
        'September': 9, 'October': 10, 'November': 11, 'December': 12
    }
    return months.get(month_str, 0)

# Parse all rows
data_by_state = defaultdict(lambda: defaultdict(list))
for row in rows:
    state = row['state']
    indicator = row['indicator']
    year = int(row['year'])
    month = month_to_num(row['month'])
    data_value = clean_value(row['data_value'])
    predicted_value = clean_value(row['predicted_value'])

    if not np.isnan(data_value):
        data_by_state[state][indicator].append({
            'year': year,
            'month': month,
            'value': data_value,
            'predicted': predicted_value,
            'date': datetime(year, month, 1)
        })

# Sort time series
for state in data_by_state:
    for indicator in data_by_state[state]:
        data_by_state[state][indicator].sort(key=lambda x: (x['year'], x['month']))

print(f"Parsed data for {len(data_by_state)} states/territories")

# Constants
NATIONAL = 'US'
TOTAL_INDICATOR = 'Number of Drug Overdose Deaths'
DPI = 150
STATE_LABELS = {'YC': 'NYC'}  # CDC reports NYC separately from NY state

# === PLOT 1: National overdose deaths over time ===
print("\nGenerating Plot 1: National overdose deaths over time...")
us_total = data_by_state[NATIONAL][TOTAL_INDICATOR]
dates = [d['date'] for d in us_total]
values = [d['value'] for d in us_total]

fig, ax = plt.subplots(figsize=(10, 6))
ax.plot(dates, values, linewidth=2, color='#2E86AB')
ax.set_xlabel('Year', fontsize=12)
ax.set_ylabel('Number of Deaths (12-month rolling)', fontsize=12)
ax.set_title('US Drug Overdose Deaths Over Time\n(National Aggregate, 12-month rolling periods)',
             fontsize=14, fontweight='bold')
ax.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('p3_g1_national_overdose_trend.png', dpi=DPI)
plt.close()
print("✓ Saved: p3_g1_national_overdose_trend.png")

# === PLOT 2: Drug-category composition over time (national) ===
print("\nGenerating Plot 2: Drug-category composition over time...")
drug_indicators = [
    'Opioids (T40.0-T40.4,T40.6)',
    'Synthetic opioids, excl. methadone (T40.4)',
    'Heroin (T40.1)',
    'Cocaine (T40.5)',
    'Psychostimulants with abuse potential (T43.6)'
]
labels = ['Opioids', 'Synthetic opioids (Fentanyl)', 'Heroin', 'Cocaine', 'Psychostimulants']

fig, ax = plt.subplots(figsize=(12, 7))
for indicator, label in zip(drug_indicators, labels):
    if indicator in data_by_state[NATIONAL]:
        series = data_by_state[NATIONAL][indicator]
        dates = [d['date'] for d in series]
        values = [d['value'] for d in series]
        ax.plot(dates, values, linewidth=2, label=label, marker='', alpha=0.8)

ax.set_xlabel('Year', fontsize=12)
ax.set_ylabel('Number of Deaths (12-month rolling)', fontsize=12)
ax.set_title('US Drug Overdose Deaths by Drug Category\n(National Aggregate, 12-month rolling periods)',
             fontsize=14, fontweight='bold')
ax.legend(loc='upper left', fontsize=10)
ax.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('p3_g2_drug_category_trends.png', dpi=DPI)
plt.close()
print("✓ Saved: p3_g2_drug_category_trends.png")

# Per-capita helpers: fold NYC into NY so every state matches the population table
names = {row['state']: row['state_name'] for row in rows}

def state_totals():
    """{state name: {date: deaths}} for the total indicator, NYC merged into NY."""
    out = defaultdict(dict)
    for code, inds in data_by_state.items():
        if code == NATIONAL:
            continue
        name = 'New York' if code == 'YC' else names[code]
        for d in inds.get(TOTAL_INDICATOR, []):
            out[name][d['date']] = out[name].get(d['date'], 0) + d['value']
    return out

totals = state_totals()
ABBR = {v: k for k, v in names.items() if k not in ('YC', NATIONAL)}

def rate(name, deaths):
    return deaths / POP[name] * 100000

latest_date = max(max(v) for v in totals.values())
latest = {s: v[latest_date] for s, v in totals.items() if latest_date in v}

# === PLOT 3: Top 15 states by death rate (per 100k) ===
print("\nGenerating Plot 3: Top 15 states by death rate...")
ranked = sorted(latest.items(), key=lambda x: rate(*x), reverse=True)[:15]
fig, ax = plt.subplots(figsize=(10, 8))
y_pos = np.arange(len(ranked))
ax.barh(y_pos, [rate(s, v) for s, v in ranked], color='#A23B72')
ax.set_yticks(y_pos)
ax.set_yticklabels([ABBR[s] for s, _ in ranked])
ax.set_ylabel('State', fontsize=12)
ax.invert_yaxis()
ax.set_xlabel('Deaths per 100,000 residents (12 months ending '
              f"{latest_date:%b %Y})", fontsize=12)
ax.set_title('Top 15 States by Overdose Death Rate\n(per 100k, 2020 Census population)',
             fontsize=14, fontweight='bold')
ax.grid(True, alpha=0.3, axis='x')
plt.tight_layout()
plt.savefig('p3_g3_state_rate_ranking.png', dpi=DPI)
plt.close()
print("✓ Saved: p3_g3_state_rate_ranking.png")

# === PLOT 4: Heatmap of death rate by state and year ===
print("\nGenerating Plot 4: State x year death-rate heatmap...")
years = sorted({d.year for v in totals.values() for d in v if d.month == 12})
order = sorted(totals, key=lambda s: rate(s, latest.get(s, 0)), reverse=True)
grid = np.full((len(order), len(years)), np.nan)
for i, s in enumerate(order):
    for j, y in enumerate(years):
        v = totals[s].get(datetime(y, 12, 1))
        if v is not None:
            grid[i, j] = rate(s, v)

fig, ax = plt.subplots(figsize=(9, 14))
cmap = plt.get_cmap('Reds').copy()
cmap.set_bad('#e0e0e0')
im = ax.imshow(np.ma.masked_invalid(grid), aspect='auto', cmap=cmap)
ax.set_xticks(range(len(years)))
ax.set_xticklabels(years, rotation=45)
ax.set_yticks(range(len(order)))
ax.set_yticklabels([ABBR[s] for s in order], fontsize=8)
ax.set_xlabel('Year (12 months ending in December)', fontsize=12)
ax.set_ylabel('State', fontsize=12)
ax.set_title('Overdose Death Rate by State and Year\n(calendar-year deaths per 100k; '
             'sorted by latest rate; gray = no data)', fontsize=13, fontweight='bold')
fig.colorbar(im, ax=ax, shrink=0.5, label='Deaths per 100k')
plt.tight_layout()
plt.savefig('p3_g4_state_rate_heatmap.png', dpi=DPI)
plt.close()
print("✓ Saved: p3_g4_state_rate_heatmap.png")

# === PLOT 5: Population vs deaths (do raw counts just track population?) ===
print("\nGenerating Plot 5: Population vs deaths scatter...")
fig, ax = plt.subplots(figsize=(10, 8))
pops = np.array([POP[s] for s in latest])
deaths = np.array([latest[s] for s in latest])
ax.scatter(pops, deaths, color='#F18F01', edgecolor='white', s=60, zorder=3)
xs = np.array([pops.min() * 0.8, pops.max() * 1.2])
ax.set_xlim(pops.min() * 0.7, pops.max() * 2.6)
for r, style in [(10, ':'), (20, '--'), (40, '-.')]:
    ax.plot(xs, xs * r / 100000, color='gray', linestyle=style, linewidth=1)
    ax.text(xs[1], xs[1] * r / 100000, f' {r} per 100k', va='center', fontsize=9, color='gray')
LABEL_OFFSETS = {'California': (6, 4), 'Texas': (6, 4), 'Florida': (6, 4),
                 'New York': (6, -10), 'West Virginia': (6, 4), 'New Mexico': (6, 4),
                 'District of Columbia': (-22, 4), 'Nebraska': (6, 4), 'Puerto Rico': (6, -10)}
for s, off in LABEL_OFFSETS.items():
    if s in latest:
        ax.annotate(ABBR[s], (POP[s], latest[s]), textcoords='offset points',
                    xytext=off, fontsize=9)
ax.set_xscale('log')
ax.set_yscale('log')
ax.set_xlabel('State population (2020 Census, log scale)', fontsize=12)
ax.set_ylabel(f"Overdose deaths, 12 months ending {latest_date:%b %Y} (log scale)", fontsize=12)
ax.set_title('Raw Death Counts Mostly Track Population\n(dashed lines = equal death rates)',
             fontsize=14, fontweight='bold')
ax.grid(True, alpha=0.3, which='both')
plt.tight_layout()
plt.savefig('p3_g5_population_vs_deaths.png', dpi=DPI)
plt.close()
print("✓ Saved: p3_g5_population_vs_deaths.png")

# === PLOT 6: Reported vs predicted (national) ===
print("\nGenerating Plot 6: Reported vs predicted...")
us_total = data_by_state[NATIONAL][TOTAL_INDICATOR]
dates = [d['date'] for d in us_total]
reported = [d['value'] for d in us_total]
predicted = [d['predicted'] if not np.isnan(d['predicted']) else None for d in us_total]

fig, ax = plt.subplots(figsize=(12, 7))
ax.plot(dates, reported, linewidth=2, label='Reported', color='#2E86AB', marker='')
# Only plot predicted where it exists
pred_dates = [dates[i] for i in range(len(predicted)) if predicted[i] is not None]
pred_values = [predicted[i] for i in range(len(predicted)) if predicted[i] is not None]
ax.plot(pred_dates, pred_values, linewidth=2, label='Predicted',
        color='#C73E1D', linestyle='--', marker='', alpha=0.7)

ax.set_xlabel('Year', fontsize=12)
ax.set_ylabel('Number of Deaths (12-month rolling)', fontsize=12)
ax.set_title('US Drug Overdose Deaths: Reported vs Predicted\n(Shows reporting lag effect)',
             fontsize=14, fontweight='bold')
ax.legend(loc='upper left', fontsize=11)
ax.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('p3_g6_reported_vs_predicted.png', dpi=DPI)
plt.close()
print("✓ Saved: p3_g6_reported_vs_predicted.png")

print("\n" + "="*70)
print("All 6 visualizations generated successfully!")
print("="*70)
