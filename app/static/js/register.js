// SCMS-F-001 registration page (register -> OTP -> login)
(function () {
  var form = document.getElementById("register-form");
  var otpForm = document.getElementById("otp-form");
  var msg = document.getElementById("message");
  var email = "";

  function post(url, body) {
    return fetch(url, {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body)
    }).then(function (r) { return r.json().then(function (d) { return { ok: r.ok, d: d }; }); });
  }

  function goLogin(text) {
    msg.textContent = text + " Redirecting to login...";
    setTimeout(function () { window.location.href = "/login"; }, 1200);
  }

  form.addEventListener("submit", function (e) {
    e.preventDefault();
    msg.textContent = "";
    if (form.password.value !== form.confirm.value) {
      msg.textContent = "Passwords do not match."; return;
    }
    email = form.email.value.trim().toLowerCase();
    post("/api/v1/auth/register", {
      name: form.name.value, email: email,
      mobile: form.mobile.value, password: form.password.value
    }).then(function (res) {
      if (!res.ok) { msg.textContent = SCMS.errorText(res.d, "Registration failed"); return; }
      if (res.d.verified) { goLogin("Registered."); return; }
      form.hidden = true;
      otpForm.hidden = false;
      msg.textContent = res.d.dev_otp
        ? "Dev mode: your OTP is " + res.d.dev_otp
        : "Enter the OTP sent to you.";
    }).catch(function () { msg.textContent = "Could not reach the server."; });
  });

  otpForm.addEventListener("submit", function (e) {
    e.preventDefault();
    post("/api/v1/auth/verify-otp", { email: email, otp: otpForm.otp.value.trim() })
      .then(function (res) {
        if (!res.ok) { msg.textContent = SCMS.errorText(res.d, "Verification failed"); return; }
        goLogin("Account verified.");
      });
  });

  document.getElementById("resend-btn").addEventListener("click", function () {
    post("/api/v1/auth/resend-otp", { email: email }).then(function (res) {
      msg.textContent = SCMS.errorText({ error: res.d.message }, "");
    });
  });
})();
