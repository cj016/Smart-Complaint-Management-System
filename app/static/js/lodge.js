// SCMS-F-010 / F-012 - citizen complaint form.
// Expects the login page (SCMS-F-002) to store the JWT in localStorage under "scms_token".
(function () {
  var TOKEN_KEY = "scms_token";
  var FIELDS = ["category", "location", "description"];
  var MAX_PHOTOS = 3;
  var MAX_PHOTO_BYTES = 5 * 1024 * 1024;  // same limits as the server
  var form = document.getElementById("lodge-form");
  var warning = document.getElementById("login-warning");
  var success = document.getElementById("success");
  var formError = document.getElementById("form-error");
  var submitBtn = document.getElementById("submit-btn");

  function showErrors(errors) {
    FIELDS.forEach(function (f) {
      // textContent (not innerHTML) keeps this XSS-safe (SCMS-SR-003)
      document.getElementById("error-" + f).textContent = errors[f] || "";
    });
  }

  function checkInBrowser() {
    // Quick check for a better experience; the server checks again (SCMS-F-012).
    var errors = {};
    FIELDS.forEach(function (f) {
      if (!form.elements[f].value.trim()) {
        errors[f] = f.charAt(0).toUpperCase() + f.slice(1) + " is required.";
      }
    });
    var files = Array.prototype.slice.call(form.elements.photos.files);
    var photoError = "";
    if (files.length > MAX_PHOTOS) {
      photoError = "You can attach at most " + MAX_PHOTOS + " photos.";
    } else if (files.some(function (f) { return f.size > MAX_PHOTO_BYTES; })) {
      photoError = "Each photo must be 5 MB or smaller.";
    }
    showErrors(errors);
    document.getElementById("error-photos").textContent = photoError;
    return Object.keys(errors).length === 0 && !photoError;
  }

  form.addEventListener("submit", function (e) {
    e.preventDefault();
    success.hidden = true;
    formError.hidden = true;

    var token = localStorage.getItem(TOKEN_KEY);
    if (!token) { warning.hidden = false; return; }
    warning.hidden = true;

    if (!checkInBrowser()) { return; }

    submitBtn.disabled = true;
    // FormData is sent as multipart/form-data (SAD 4.3) so photos can be added later.
    fetch("/api/v1/complaints", {
      method: "POST",
      headers: { Authorization: "Bearer " + token },
      body: new FormData(form)
    })
      .then(function (resp) {
        if (resp.status === 401) {
          localStorage.removeItem(TOKEN_KEY);
          warning.hidden = false;
          return null;
        }
        return resp.json();
      })
      .then(function (data) {
        if (!data) { return; }
        if (data.error) {
          showErrors((data.error.details && data.error.details.fields) || {});
          formError.textContent = data.error.message;
          formError.hidden = false;
          return;
        }
        document.getElementById("new-id").textContent = data.complaintId;
        success.hidden = false;
        form.reset();
        showErrors({});
        document.getElementById("error-photos").textContent = "";
      })
      .catch(function () {
        formError.textContent = "Could not submit. Please try again.";
        formError.hidden = false;
      })
      .then(function () { submitBtn.disabled = false; });
  });

  warning.hidden = !!localStorage.getItem(TOKEN_KEY);
})();
