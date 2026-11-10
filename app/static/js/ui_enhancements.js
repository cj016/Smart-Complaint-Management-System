// SCMS Sprint 3: scoped UI enhancements.
document.addEventListener("DOMContentLoaded", function () {
  document.body.classList.add("scms-uniform-ui");

  [
    "login-form",
    "register-form",
    "otp-form",
    "lodge-form",
    "feedback-form"
  ].forEach(function (id) {
    var form = document.getElementById(id);
    if (form) {
      form.classList.add("uniform-form");
    }
  });
});
