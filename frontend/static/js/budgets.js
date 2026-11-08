const budgetForm = document.getElementById("budget-form");
const budgetMonth = document.getElementById("budget-month");
const budgetMessage = document.getElementById("budget-message");

function selectedMonth() {
  const [year, month] = budgetMonth.value.split("-").map(Number);
  return { year, month };
}

async function loadBudgets() {
  const { year, month } = selectedMonth();
  document.getElementById("budget-title").textContent = `Budgets for ${monthLabel(year, month)}`;
  const insights = await api(`/api/insights/${year}/${month}`);
  const body = document.querySelector("#budget-table tbody");
  body.replaceChildren();
  if (!insights.categories.length) {
    body.append(el("tr", {}, el("td", { colspan: 4, class: "muted" }, "No budgets or spending this month.")));
    return;
  }
  for (const c of insights.categories) {
    const over = c.usage_pct !== null && c.usage_pct > 100;
    body.append(
      el(
        "tr",
        {},
        el("td", {}, c.category),
        el("td", { class: "num" }, c.budget ? money(c.budget) : "-"),
        el("td", { class: "num" }, money(c.spent)),
        el("td", { class: `num ${over ? "negative" : ""}` }, c.usage_pct === null ? "-" : `${c.usage_pct}%`),
      ),
    );
  }
}

budgetForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const f = budgetForm.elements;
  try {
    await api("/api/budgets", {
      method: "POST",
      body: { category: f.category.value, amount: Number(f.amount.value), ...selectedMonth() },
    });
    showMessage(budgetMessage, `Saved ${f.category.value} budget.`);
    f.amount.value = "";
    await loadBudgets();
  } catch (err) {
    showMessage(budgetMessage, err.message, "error");
  }
});

document.getElementById("apply-recs").addEventListener("click", async () => {
  const recs = await api("/api/recommendations");
  if (!recs.length) {
    showMessage(budgetMessage, "No spending history yet, so there is nothing to recommend.", "warn");
    return;
  }
  const { year, month } = selectedMonth();
  if (!confirm(`Set ${recs.length} budgets for ${monthLabel(year, month)} from your recent spending?`)) return;
  for (const r of recs) {
    await api("/api/budgets", { method: "POST", body: { category: r.category, amount: r.recommended, year, month } });
  }
  showMessage(budgetMessage, `Applied ${recs.length} recommended budgets.`);
  await loadBudgets();
});

budgetMonth.value = new Date().toISOString().slice(0, 7);
budgetMonth.addEventListener("change", loadBudgets);
loadBudgets();
