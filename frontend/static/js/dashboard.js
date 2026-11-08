const monthSelect = document.getElementById("month-select");
const riskDay = document.getElementById("risk-day");
const charts = {};

const SPENT_COLOR = "#2563eb";
const BUDGET_COLOR = "#9ca3af";

function drawChart(id, config) {
  if (charts[id]) charts[id].destroy();
  charts[id] = new Chart(document.getElementById(id), config);
}

function renderStats(data) {
  document.getElementById("stat-budget").textContent = money(data.budget);
  document.getElementById("stat-spent").textContent = money(data.spent);
  const remaining = document.getElementById("stat-remaining");
  remaining.textContent = money(data.remaining);
  remaining.classList.toggle("negative", data.remaining < 0);
  const usage = document.getElementById("stat-usage");
  usage.textContent = data.usage_pct === null ? "no budget" : `${data.usage_pct}%`;
  usage.classList.toggle("negative", data.usage_pct !== null && data.usage_pct > 100);
}

function renderCharts(data) {
  const categories = [...data.categories].sort((a, b) => b.spent - a.spent);
  drawChart("category-chart", {
    type: "bar",
    data: {
      labels: categories.map((c) => c.category),
      datasets: [
        { label: "Spent", data: categories.map((c) => c.spent), backgroundColor: SPENT_COLOR },
        { label: "Budget", data: categories.map((c) => c.budget), backgroundColor: BUDGET_COLOR },
      ],
    },
    options: {
      indexAxis: "y",
      maintainAspectRatio: false,
      scales: { x: { ticks: { callback: (v) => money(v) } }, y: { ticks: { autoSkip: false } } },
      plugins: { tooltip: { callbacks: { label: (ctx) => `${ctx.dataset.label}: ${money(ctx.raw)}` } } },
    },
  });

  drawChart("trend-chart", {
    type: "line",
    data: {
      labels: data.trend.map((t) => monthLabel(t.year, t.month)),
      datasets: [
        { label: "Spent", data: data.trend.map((t) => t.spent), borderColor: SPENT_COLOR, backgroundColor: SPENT_COLOR, tension: 0.2 },
        { label: "Budget", data: data.trend.map((t) => t.budget), borderColor: BUDGET_COLOR, backgroundColor: BUDGET_COLOR, borderDash: [6, 4], tension: 0.2 },
      ],
    },
    options: {
      maintainAspectRatio: false,
      scales: { y: { ticks: { callback: (v) => money(v) } } },
      plugins: { tooltip: { callbacks: { label: (ctx) => `${ctx.dataset.label}: ${money(ctx.raw)}` } } },
    },
  });
}

function renderAnomalies(anomalies) {
  const list = document.getElementById("anomaly-list");
  list.replaceChildren();
  if (!anomalies.length) {
    list.append(el("li", { class: "muted" }, "Nothing unusual this month."));
    return;
  }
  for (const a of anomalies) {
    list.append(
      el(
        "li",
        {},
        el("strong", {}, `${money(a.amount)} · ${a.category}`),
        el("span", { class: "muted small" }, ` ${a.date} ${a.description ? "· " + a.description : ""}`),
        el("div", { class: "small" }, a.reason),
      ),
    );
  }
}

function renderRisk(data) {
  document.getElementById("risk-note").textContent =
    `Chance each category ends ${monthLabel(data.year, data.month)} over budget, using spending up to day ${data.as_of_day}.`;
  const body = document.querySelector("#risk-table tbody");
  body.replaceChildren();
  if (!data.categories.length) {
    body.append(el("tr", {}, el("td", { colspan: 4, class: "muted" }, "Set budgets for this month to see risk.")));
    return;
  }
  for (const c of data.categories) {
    body.append(
      el(
        "tr",
        {},
        el("td", {}, c.category),
        el("td", { class: "num" }, money(c.spent_to_date)),
        el("td", { class: "num" }, money(c.budget)),
        el("td", {}, el("span", { class: `badge ${c.level}` }, `${Math.round(c.risk * 100)}% ${c.level}`)),
      ),
    );
  }
}

function renderRecommendations(rows) {
  const body = document.querySelector("#rec-table tbody");
  body.replaceChildren();
  if (!rows.length) {
    body.append(el("tr", {}, el("td", { colspan: 3, class: "muted" }, "Add expenses to get recommendations.")));
    return;
  }
  for (const r of rows) {
    body.append(
      el("tr", {}, el("td", {}, r.category), el("td", { class: "num" }, money(r.recommended)), el("td", { class: "small muted" }, r.reason)),
    );
  }
}

async function loadMonth() {
  const [year, month] = monthSelect.value.split("-").map(Number);
  const day = riskDay.value ? `?day=${riskDay.value}` : "";
  const [insights, risk] = await Promise.all([
    api(`/api/insights/${year}/${month}`),
    api(`/api/predict/overspend/${year}/${month}${day}`),
  ]);
  renderStats(insights);
  renderCharts(insights);
  renderAnomalies(insights.anomalies);
  renderRisk(risk);
}

async function init() {
  const months = await api("/api/months");
  if (!months.length) {
    document.getElementById("empty").hidden = false;
    document.getElementById("dashboard").hidden = true;
    return;
  }
  for (const m of months) {
    monthSelect.append(el("option", { value: `${m.year}-${m.month}` }, monthLabel(m.year, m.month)));
  }
  monthSelect.addEventListener("change", loadMonth);
  riskDay.addEventListener("change", loadMonth);
  renderRecommendations(await api("/api/recommendations"));
  await loadMonth();
}

init();
