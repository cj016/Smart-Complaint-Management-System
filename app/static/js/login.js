// SCMS-F-002: role-based login and safe return URLs.
(function () {
  "use strict";

  var HOME = { Complainant: "/my-complaints", Officer: "/admin", Admin: "/admin" };
  var form = document.getElementById("login-form");
  var msg = document.getElementById("message");
  var next = new URLSearchParams(window.location.search).get("next");

  // Never trust the return URL to send a user to a different role's page.
  function destination(role) {
    var home = HOME[role] || "/";
    if (!next || next.charAt(0) !== "/" || next.charAt(1) === "/" ||
        next.indexOf("\\") !== -1) { return home; }
    var path = next.split(/[?#]/)[0];
    if ((role === "Admin" || role === "Officer") && path === "/admin") {
      return next;
    }
    if (role === "Complainant" &&
        ["/my-complaints", "/lodge", "/track", "/notifications"].indexOf(path) !== -1) {
      return next;
    }
    return home;
  }

  // A previously expired token must not cause an automatic login-page redirect loop.
  // A fresh successful login replaces the entire stored session.
  form.addEventListener("submit", function (e) {
    e.preventDefault();
    msg.textContent = "";
    fetch("/api/v1/auth/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email: form.email.value, password: form.password.value })
    })
      .then(function (r) {
        return r.json().then(function (d) { return { ok: r.ok, d: d }; });
      })
      .then(function (res) {
        if (!res.ok) { msg.textContent = SCMS.errorText(res.d, "Login failed"); return; }
        if (!res.d.access_token || !HOME[res.d.role]) {
          msg.textContent = "Unexpected server login response.";
          return;
        }
        SCMS.save(res.d);
        window.location.href = destination(res.d.role);
      })
      .catch(function () { msg.textContent = "Could not reach the server."; });
  });
})();
