const MONTH_NAMES = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];

function errorText(data, status) {
  if (!data || !data.detail) return `Request failed (${status})`;
  if (Array.isArray(data.detail)) {
    return data.detail.map((d) => `${d.loc[d.loc.length - 1]}: ${d.msg.replace("Value error, ", "")}`).join("; ");
  }
  return data.detail;
}

async function api(path, { method = "GET", body, redirectOn401 = true } = {}) {
  const res = await fetch(path, {
    method,
    credentials: "same-origin",
    headers: body ? { "Content-Type": "application/json" } : {},
    body: body ? JSON.stringify(body) : undefined,
  });
  if (res.status === 401 && redirectOn401) {
    window.location.href = "/login";
    throw new Error("Not signed in");
  }
  if (res.status === 204) return null;
  const data = await res.json().catch(() => null);
  if (!res.ok) throw new Error(errorText(data, res.status));
  return data;
}

function money(value) {
  return "₹" + Number(value).toLocaleString("en-IN", { maximumFractionDigits: 0 });
}

function monthLabel(year, month) {
  return `${MONTH_NAMES[month - 1]} ${year}`;
}

function el(tag, attrs = {}, ...children) {
  const node = document.createElement(tag);
  for (const [key, value] of Object.entries(attrs)) {
    if (key === "class") node.className = value;
    else if (key.startsWith("on")) node.addEventListener(key.slice(2), value);
    else node.setAttribute(key, value);
  }
  for (const child of children) {
    node.append(child instanceof Node ? child : document.createTextNode(child ?? ""));
  }
  return node;
}

function showMessage(node, text, kind = "ok") {
  node.textContent = text;
  node.className = `message ${kind}`;
  node.hidden = !text;
}

const logoutButton = document.getElementById("logout");
if (logoutButton) {
  logoutButton.addEventListener("click", async () => {
    await api("/api/auth/logout", { method: "POST" });
    window.location.href = "/login";
  });
}
