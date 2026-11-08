const authForm = document.getElementById("auth-form");
const authError = document.getElementById("auth-error");

authForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const form = new FormData(authForm);
  const mode = authForm.dataset.mode;
  try {
    await api(`/api/auth/${mode}`, {
      method: "POST",
      body: { username: form.get("username"), password: form.get("password") },
      redirectOn401: false,
    });
    window.location.href = "/";
  } catch (err) {
    authError.textContent = err.message;
    authError.hidden = false;
  }
});
