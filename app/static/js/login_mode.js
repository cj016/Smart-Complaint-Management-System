// One genuine login endpoint for Citizens, Officers and Admins.
// The selected tab changes presentation only: the server decides the real role.
(function () {
  "use strict";
  var citizen = document.getElementById("login-citizen");
  var staff = document.getElementById("login-staff");
  var email = document.getElementById("email");
  var hint = document.getElementById("role-hint");
  var registerCta = document.getElementById("register-cta");
  var demoAdmin = "admin@scms.test"; // Fixed username only; password is never in JS.
  if (!citizen || !staff || !email) { return; }
  function setMode(mode) {
    var isStaff = mode === "staff";
    citizen.classList.toggle("active", !isStaff);
    staff.classList.toggle("active", isStaff);
    citizen.setAttribute("aria-pressed", String(!isStaff));
    staff.setAttribute("aria-pressed", String(isStaff));
    hint.textContent = isStaff
      ? ""
      : "Use your registered Citizen account.";
    registerCta.hidden = isStaff;
    if (isStaff && !email.value.trim()) { email.value = demoAdmin; }
    if (!isStaff && email.value.trim().toLowerCase() === demoAdmin) {
      email.value = "";
    }
    email.focus();
  }
  citizen.addEventListener("click", function () { setMode("citizen"); });
  staff.addEventListener("click", function () { setMode("staff"); });
  setMode("citizen");
})();
