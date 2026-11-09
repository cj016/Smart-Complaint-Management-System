// Shared auth helpers (SCMS-F-002, SCMS-SR-002). Load this in base.html on every page.
// Uses the same localStorage key as my_complaints.js ("scms_token").
var SCMS = (function () {
  var TOKEN_KEY = "scms_token", ROLE_KEY = "scms_role", NAME_KEY = "scms_name";

  function getToken() { return localStorage.getItem(TOKEN_KEY); }
  function getRole() { return localStorage.getItem(ROLE_KEY); }

  function save(data) {
    localStorage.setItem(TOKEN_KEY, data.access_token);
    localStorage.setItem(ROLE_KEY, data.role);
    localStorage.setItem(NAME_KEY, data.name || "");
  }

  function clear() {
    [TOKEN_KEY, ROLE_KEY, NAME_KEY].forEach(function (k) { localStorage.removeItem(k); });
  }

  // Works with {"error": "text"} and {"error": {"message": "text"}}
  function errorText(data, fallback) {
    var e = data && data.error;
    if (typeof e === "string") { return e; }
    if (e && e.message) { return e.message; }
    return fallback || "Something went wrong";
  }

  // fetch with the Bearer token; on 401 clears the session and goes to /login
  function authFetch(url, opts) {
    opts = opts || {};
    opts.headers = Object.assign({}, opts.headers, { Authorization: "Bearer " + getToken() });
    return fetch(url, opts).then(function (resp) {
      if (resp.status === 401) {
        clear();
        window.location.href = "/login?next=" + encodeURIComponent(window.location.pathname);
      }
      return resp;
    });
  }

  function logout() {
    // JWTs are stateless on this server; removing the local token logs out this browser.
    // Do not wait for the network before clearing it.
    clear();
    window.location.href = "/login";
  }

  // Role-based navigation. Cosmetic only; the server enforces access (roles_required).
  // <a data-roles="Officer,Admin">, <a data-auth="in">, <a data-auth="out">
  function applyNav() {
    var role = getRole(), loggedIn = !!getToken();
    document.querySelectorAll("[data-roles]").forEach(function (el) {
      var allowed = el.getAttribute("data-roles").split(",");
      el.hidden = !(loggedIn && allowed.indexOf(role) !== -1);
    });
    document.querySelectorAll("[data-auth]").forEach(function (el) {
      var want = el.getAttribute("data-auth") === "in";
      el.hidden = (want !== loggedIn);
    });
    var who = document.getElementById("nav-user");
    if (who) { who.textContent = loggedIn ? (localStorage.getItem(NAME_KEY) || "") : ""; }
    var out = document.getElementById("logout-btn");
    if (out) { out.addEventListener("click", function (e) { e.preventDefault(); logout(); }); }
  }
  document.addEventListener("DOMContentLoaded", applyNav);
    function requireRole(roles) {
    if (!getToken()) {
      window.location.href = "/login?next=" + encodeURIComponent(window.location.pathname);
      return false;
    }
    if (roles.indexOf(getRole()) === -1) {
      window.location.href = "/";
      return false;
    }
    return true;
  }
  return { getToken: getToken, getRole: getRole, save: save, clear: clear,
           authFetch: authFetch, logout: logout, errorText: errorText, requireRole: requireRole };
})();
