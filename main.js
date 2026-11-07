import * as d3 from "https://cdn.jsdelivr.net/npm/d3@7.9.0/+esm";
import * as topojson from "https://cdn.jsdelivr.net/npm/topojson-client@3/+esm";

// Load the overdose data (static file) and the US states geometry (CDN).
const [data, us] = await Promise.all([
  d3.json("data.json"),
  d3.json("https://cdn.jsdelivr.net/npm/us-atlas@3/states-albers-10m.json"),
]);

// us-atlas states-albers-10m is pre-projected to a 975x610 viewport, so geoPath needs
// no projection and features carry properties.name (full state name).
const stateFeatures = topojson.feature(us, us.objects.states).features;
const stateBorders = topojson.mesh(us, us.objects.states, (a, b) => a !== b);
const geoPath = d3.geoPath();

const indicatorKeys = Object.keys(data.indicatorLabels);
let indicator = "total";
let metric = "counts"; // "counts" = raw deaths; "rate" = deaths per 100k residents
let periodIdx = data.periods.length - 1;
let selectedState = "California";
let color;

// ---- Controls ----
const indicatorSelect = d3.select("#indicator");
indicatorSelect
  .selectAll("option")
  .data(indicatorKeys)
  .join("option")
  .attr("value", (d) => d)
  .text((d) => data.indicatorLabels[d]);
indicatorSelect
  .property("value", indicator)
  .on("change", (event) => {
    indicator = event.target.value;
    recomputeColor();
    render();
  });

// Metric toggle: raw counts mostly track state population (big states always
// darkest), so per-100k rates are the fairer cross-state comparison. Both
// datasets share data.json's shape, so switching is just a dataset swap.
const metricSelect = d3.select("#metric");
metricSelect
  .property("value", metric)
  .on("change", (event) => {
    metric = event.target.value;
    recomputeColor();
    render();
  });

const periodSlider = d3
  .select("#period")
  .attr("max", data.periods.length - 1)
  .property("value", periodIdx)
  .on("input", (event) => {
    periodIdx = +event.target.value;
    render();
  });

// The active dataset follows the metric toggle; data.rate mirrors data.series.
function activeData() {
  return metric === "rate" ? data.rate : data.series;
}
// Per-metric number formatting and labels used by the tooltip, legend, and trend.
const METRIC = {
  counts: { value: d3.format(","), tick: d3.format("~s"), unit: "deaths", legend: "deaths" },
  rate: { value: d3.format(".1f"), tick: d3.format("~s"), unit: "per 100k", legend: "deaths per 100k" },
};

// Fixed color domain per indicator and metric (over all states & periods) so
// sliding through time reads as a real change in magnitude, not a rescaled palette.
function recomputeColor() {
  let max = 0;
  const series = activeData()[indicator];
  for (const st in series) {
    for (const v of series[st]) if (v != null && v > max) max = v;
  }
  color = d3.scaleSequential(d3.interpolateReds).domain([0, max || 1]);
}
recomputeColor();

function valueFor(name, idx = periodIdx) {
  const s = activeData()[indicator][name];
  return s ? s[idx] : null;
}

// ---- Map ----
const mapSvg = d3.select("#map");
const statePaths = mapSvg
  .append("g")
  .selectAll("path.state")
  .data(stateFeatures)
  .join("path")
  .attr("class", "state")
  .attr("d", geoPath)
  .on("mousemove", (event, f) => showTooltip(event, f.properties.name))
  .on("mouseleave", hideTooltip)
  .on("click", (event, f) => {
    selectedState = selectedState === f.properties.name ? null : f.properties.name;
    render();
  });
mapSvg.append("path").datum(stateBorders).attr("class", "borders").attr("d", geoPath);

// ---- Tooltip (details on demand) ----
const tooltip = d3.select("#tooltip");
function showTooltip(event, name) {
  const v = valueFor(name);
  tooltip
    .attr("hidden", null)
    .html(
      `<strong>${name}</strong><br>${v == null ? "no data" : METRIC[metric].value(v) + " " + METRIC[metric].unit}` +
        `<br><span class="tt-sub">${data.periodLabels[periodIdx]}</span>`,
    );
  // Flip to the cursor's other side when the tooltip would leave the viewport.
  const { offsetWidth: tw, offsetHeight: th } = tooltip.node();
  const left = event.clientX + 14 + tw > innerWidth ? event.clientX - 14 - tw : event.clientX + 14;
  const top = event.clientY + 14 + th > innerHeight ? event.clientY - 14 - th : event.clientY + 14;
  tooltip.style("left", `${Math.max(0, left)}px`).style("top", `${Math.max(0, top)}px`);
}
function hideTooltip() {
  tooltip.attr("hidden", true);
}

// ---- Legend (color gradient) ----
const legend = d3.select("#legend");
function renderLegend() {
  const max = color.domain()[1];
  const w = 260,
    h = 12,
    n = 40;
  legend.html("");
  const svg = legend.append("svg").attr("width", w).attr("height", h + 34);
  const grad = svg.append("defs").append("linearGradient").attr("id", "legend-grad");
  d3.range(n + 1).forEach((i) =>
    grad
      .append("stop")
      .attr("offset", `${(100 * i) / n}%`)
      .attr("stop-color", color((i / n) * max)),
  );
  svg
    .append("rect")
    .attr("width", w)
    .attr("height", h)
    .attr("fill", "url(#legend-grad)")
    .attr("stroke", "#999");
  const scale = d3.scaleLinear().domain([0, max]).range([0, w]);
  svg
    .append("g")
    .attr("transform", `translate(0,${h})`)
    .call(d3.axisBottom(scale).ticks(5).tickFormat(METRIC[metric].tick))
    .call((g) => g.select(".domain").remove());
  svg
    .append("text")
    .attr("y", h + 30)
    .attr("class", "legend-title")
    .text(`${data.indicatorLabels[indicator]} - ${METRIC[metric].legend} (12-mo ending)`);
}

// ---- Trend (linked view: selected state over time) ----
const trendSvg = d3.select("#trend");
const trendTitle = d3.select("#trend-title");
function renderTrend() {
  trendSvg.html("");
  if (!selectedState) {
    trendTitle.text("Click a state to see its trend over time");
    return;
  }
  trendTitle.text(`${selectedState} - ${data.indicatorLabels[indicator]}${metric === "rate" ? " (per 100k)" : ""}`);
  trendTitle.append("span").attr("class", "trend-hint").text("Click the state again to clear.");
  const series = activeData()[indicator][selectedState] || [];
  const pts = series.map((v, i) => ({ i, v })).filter((d) => d.v != null);
  if (!pts.length) return;

  // National per-100k reference, rate mode only (national counts would flatten a single state).
  const natPts =
    metric === "rate"
      ? data.nationalRate[indicator].map((v, i) => ({ i, v })).filter((d) => d.v != null)
      : [];

  const W = 520,
    H = 300,
    m = { top: 16, right: 30, bottom: 28, left: 54 };
  const x = d3.scaleLinear().domain([0, data.periods.length - 1]).range([m.left, W - m.right]);
  const y = d3
    .scaleLinear()
    .domain([0, d3.max(natPts.concat(pts), (d) => d.v) || 1])
    .nice()
    .range([H - m.bottom, m.top]);

  // One tick per year (December period).
  const yearTicks = [];
  data.periods.forEach((p, i) => {
    if (p.slice(5) === "12") yearTicks.push({ i, yr: p.slice(0, 4) });
  });
  trendSvg
    .append("g")
    .attr("transform", `translate(0,${H - m.bottom})`)
    .call(
      d3
        .axisBottom(x)
        .tickValues(yearTicks.map((t) => t.i))
        .tickFormat((d, k) => yearTicks[k].yr),
    );
  trendSvg
    .append("g")
    .attr("transform", `translate(${m.left},0)`)
    .call(d3.axisLeft(y).ticks(5).tickFormat(METRIC[metric].tick));

  trendSvg
    .append("text")
    .attr("class", "axis-label")
    .attr("transform", `translate(12,${(m.top + H - m.bottom) / 2}) rotate(-90)`)
    .attr("text-anchor", "middle")
    .text(metric === "rate" ? "deaths per 100k" : "deaths");

  const line = d3.line().x((d) => x(d.i)).y((d) => y(d.v));
  if (natPts.length) {
    const end = natPts[natPts.length - 1];
    trendSvg.append("path").datum(natPts).attr("class", "national-line").attr("d", line);
    trendSvg
      .append("text")
      .attr("class", "axis-label")
      .attr("x", x(end.i) + 3)
      .attr("y", y(end.v))
      .attr("dy", "0.32em")
      .text("U.S.");
  }
  trendSvg.append("path").datum(pts).attr("class", "trend-line").attr("d", line);

  // No marker when the slider period has no value for this state.
  const cur = pts.find((d) => d.i === periodIdx);
  if (cur)
    trendSvg
      .append("circle")
      .attr("class", "trend-marker")
      .attr("cx", x(cur.i))
      .attr("cy", y(cur.v))
      .attr("r", 4);
}

// ---- Render everything from current state ----
function render() {
  statePaths
    .attr("fill", (f) => {
      const v = valueFor(f.properties.name);
      return v == null ? "#eee" : color(v);
    })
    .classed("selected", (f) => f.properties.name === selectedState);
  d3.select("#period-label").text(data.periodLabels[periodIdx]);
  renderLegend();
  renderTrend();
}

render();
