// Root is an entry point: no authenticated session -> shared login page.
// Routes and private data are still protected by server-side JWT/role checks.
(function () {
  "use strict";
  if (!SCMS.getToken()) {
    window.location.replace("/login");
    return;
  }
  var role = SCMS.getRole();
  if (role === "Complainant") {
    window.location.replace("/my-complaints");
  } else if (role === "Admin" || role === "Officer") {
    window.location.replace("/admin");
  } else {
    SCMS.clear();
    window.location.replace("/login");
  }
})();
