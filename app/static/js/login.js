// SCMS-F-002 login page
(function () {
  // Change these to your real page URLs
  var HOME = { Complainant: "/my-complaints", Officer: "/my-complaints", Admin: "/my-complaints" };

  var form = document.getElementById("login-form");
  var msg = document.getElementById("message");

  var next = new URLSearchParams(window.location.search).get("next");
  if (SCMS.getToken()) { window.location.href = HOME[SCMS.getRole()] || "/"; }

  form.addEventListener("submit", function (e) {
    e.preventDefault();
    msg.textContent = "";
    fetch("/api/v1/auth/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        email: form.email.value, password: form.password.value
      })
    })
      .then(function (r) { return r.json().then(function (d) { return { ok: r.ok, d: d }; }); })
      .then(function (res) {
        if (!res.ok) { msg.textContent = SCMS.errorText(res.d, "Login failed"); return; }
        SCMS.save(res.d);
        // only allow same-site relative redirects
        var safe = next && next.charAt(0) === "/" && next.charAt(1) !== "/";
        window.location.href = safe ? next : (HOME[res.d.role] || "/");
      })
      .catch(function () { msg.textContent = "Could not reach the server."; });
  });
})();
