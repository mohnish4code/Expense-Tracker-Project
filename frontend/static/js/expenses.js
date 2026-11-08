const expenseForm = document.getElementById("expense-form");
const formMessage = document.getElementById("form-message");
const submitBtn = document.getElementById("submit-btn");
const cancelEdit = document.getElementById("cancel-edit");
const filterMonth = document.getElementById("filter-month");
const filterCategory = document.getElementById("filter-category");

function today() {
  return new Date().toISOString().slice(0, 10);
}

function resetForm() {
  expenseForm.reset();
  expenseForm.elements.id.value = "";
  expenseForm.elements.date.value = today();
  document.getElementById("form-title").textContent = "Add expense";
  submitBtn.textContent = "Add expense";
  cancelEdit.hidden = true;
}

function startEdit(expense) {
  for (const field of ["id", "date", "category", "amount", "payment_method", "description"]) {
    expenseForm.elements[field].value = expense[field];
  }
  expenseForm.elements.is_recurring.checked = expense.is_recurring;
  document.getElementById("form-title").textContent = "Edit expense";
  submitBtn.textContent = "Save changes";
  cancelEdit.hidden = false;
  expenseForm.scrollIntoView({ behavior: "smooth" });
}

async function loadExpenses() {
  const params = new URLSearchParams();
  if (filterMonth.value) {
    const [year, month] = filterMonth.value.split("-");
    params.set("year", year);
    params.set("month", Number(month));
  }
  if (filterCategory.value) params.set("category", filterCategory.value);
  const expenses = await api(`/api/expenses?${params}`);

  const total = expenses.reduce((sum, e) => sum + e.amount, 0);
  document.getElementById("expense-summary").textContent = `${expenses.length} expenses, ${money(total)} total`;

  const body = document.querySelector("#expense-table tbody");
  body.replaceChildren();
  for (const e of expenses) {
    body.append(
      el(
        "tr",
        {},
        el("td", {}, e.date),
        el("td", {}, e.category, e.is_recurring ? el("span", { class: "tag" }, "recurring") : ""),
        el("td", {}, e.description),
        el("td", {}, e.payment_method),
        el("td", { class: "num" }, money(e.amount)),
        el(
          "td",
          { class: "row-actions" },
          el("button", { class: "link", onclick: () => startEdit(e) }, "Edit"),
          el("button", { class: "link danger", onclick: () => removeExpense(e) }, "Delete"),
        ),
      ),
    );
  }
}

async function removeExpense(expense) {
  if (!confirm(`Delete ${money(expense.amount)} ${expense.category} on ${expense.date}?`)) return;
  await api(`/api/expenses/${expense.id}`, { method: "DELETE" });
  showMessage(formMessage, "Expense deleted.");
  await loadExpenses();
}

expenseForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const f = expenseForm.elements;
  const body = {
    date: f.date.value,
    category: f.category.value,
    amount: Number(f.amount.value),
    payment_method: f.payment_method.value,
    is_recurring: f.is_recurring.checked,
    description: f.description.value,
  };
  try {
    const editing = Boolean(f.id.value);
    await api(editing ? `/api/expenses/${f.id.value}` : "/api/expenses", { method: editing ? "PUT" : "POST", body });
    const check = await api("/api/predict/anomaly", {
      method: "POST",
      body: { category: body.category, amount: body.amount, payment_method: body.payment_method, is_recurring: body.is_recurring },
    });
    if (check.anomaly) showMessage(formMessage, `Saved, but this looks unusual: ${check.reason}.`, "warn");
    else showMessage(formMessage, editing ? "Expense updated." : "Expense added.");
    resetForm();
    await loadExpenses();
  } catch (err) {
    showMessage(formMessage, err.message, "error");
  }
});

cancelEdit.addEventListener("click", resetForm);
filterMonth.addEventListener("change", loadExpenses);
filterCategory.addEventListener("change", loadExpenses);

resetForm();
loadExpenses();
