# DSC 209R - Project 3: U.S. Drug-Overdose Explorer

Interactive visualization of CDC VSRR Provisional Drug Overdose Death Counts
(12-month-ending totals by state, 2015-2026), built with D3.js.

**Team:** Derek Pham, Mustafa Hayeri

## What it does
- Choropleth of overdose deaths by state
- Drug-category selector (total / opioids / synthetic opioids (fentanyl) / heroin / cocaine / psychostimulants)
- Time slider across 137 monthly 12-month-ending periods
- Hover tooltips (details on demand); click a state for its trend over time (linked view)

## Run locally
Static site, no build step:

    python3 -m http.server 8000

then open http://localhost:8000/

## Tech
D3 v7, topojson-client, us-atlas (all via CDN). Data pre-aggregated into `data.json`.
Design rationale + development notes are in the write-up section of the page.
