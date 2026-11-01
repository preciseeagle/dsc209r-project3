#!/usr/bin/env python3
"""
DSC209R Project 3 - Exploratory Visualizations
CDC VSRR Provisional Drug Overdose Death Counts
"""
import csv
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from collections import defaultdict
from datetime import datetime

# Load data
print("Loading data...")
with open('raw_data.csv', 'r') as f:
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

# === PLOT 3: Latest-period state ranking (horizontal bar) ===
print("\nGenerating Plot 3: Latest-period state ranking...")
# Get latest period for each state (excluding US)
state_latest = {}
for state in data_by_state:
    if state == NATIONAL:
        continue
    if TOTAL_INDICATOR in data_by_state[state]:
        series = data_by_state[state][TOTAL_INDICATOR]
        if series:
            latest = series[-1]
            state_latest[state] = latest['value']

# Sort and get top states
sorted_states = sorted(state_latest.items(), key=lambda x: x[1], reverse=True)
top_states = sorted_states[:15]

states_list = [s[0] for s in top_states]
values_list = [s[1] for s in top_states]

fig, ax = plt.subplots(figsize=(10, 8))
y_pos = np.arange(len(states_list))
ax.barh(y_pos, values_list, color='#A23B72')
ax.set_yticks(y_pos)
ax.set_yticklabels([STATE_LABELS.get(s, s) for s in states_list])
ax.invert_yaxis()
ax.set_xlabel('Number of Deaths (12-month rolling, latest period)', fontsize=12)
ax.set_title('Top 15 States by Drug Overdose Deaths\n(Most Recent 12-month Period)',
             fontsize=14, fontweight='bold')
ax.grid(True, alpha=0.3, axis='x')
plt.tight_layout()
plt.savefig('p3_g3_state_ranking_latest.png', dpi=DPI)
plt.close()
print("✓ Saved: p3_g3_state_ranking_latest.png")

# === PLOT 4: Multi-state trajectories ===
print("\nGenerating Plot 4: Multi-state trajectories...")
# Use top 5 states from latest period
top5_states = [s[0] for s in sorted_states[:5]]

fig, ax = plt.subplots(figsize=(12, 7))
for state in top5_states:
    series = data_by_state[state][TOTAL_INDICATOR]
    dates = [d['date'] for d in series]
    values = [d['value'] for d in series]
    ax.plot(dates, values, linewidth=2, label=state, marker='', alpha=0.8)

ax.set_xlabel('Year', fontsize=12)
ax.set_ylabel('Number of Deaths (12-month rolling)', fontsize=12)
ax.set_title('Drug Overdose Death Trends: Top 5 States\n(12-month rolling periods)',
             fontsize=14, fontweight='bold')
ax.legend(loc='upper left', fontsize=11)
ax.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('p3_g4_multistate_trajectories.png', dpi=DPI)
plt.close()
print("✓ Saved: p3_g4_multistate_trajectories.png")

# === PLOT 5: Top-15 states bar for latest period ===
print("\nGenerating Plot 5: Top-15 states bar chart...")
# This is similar to plot 3 but vertical
fig, ax = plt.subplots(figsize=(12, 6))
x_pos = np.arange(len(states_list))
ax.bar(x_pos, values_list, color='#F18F01')
ax.set_xticks(x_pos)
ax.set_xticklabels([STATE_LABELS.get(s, s) for s in states_list], rotation=45, ha='right')
ax.set_ylabel('Number of Deaths (12-month rolling)', fontsize=12)
ax.set_title('Top 15 States by Drug Overdose Deaths\n(Most Recent 12-month Period)',
             fontsize=14, fontweight='bold')
ax.grid(True, alpha=0.3, axis='y')
plt.tight_layout()
plt.savefig('p3_g5_top15_states_bar.png', dpi=DPI)
plt.close()
print("✓ Saved: p3_g5_top15_states_bar.png")

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
