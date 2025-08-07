document.addEventListener("DOMContentLoaded", () => {
  const form = document.getElementById("loginForm");

  form.addEventListener("submit", function (e) {
    const username = form.username.value.trim();
    const password = form.password.value.trim();

    if (!username || !password) {
      alert("Both fields are required.");
      e.preventDefault();
    }
  });
});


