// SCMS-F041: submit resolution feedback for your own Resolved complaint.
(function () {
  "use strict";
  if (!SCMS.requireRole(["Complainant"])) { return; }

  var form = document.getElementById("feedback-form");
  var idInput = document.getElementById("feedback-id");
  var ratingInput = document.getElementById("feedback-rating");
  var commentInput = document.getElementById("feedback-comment");
  var message = document.getElementById("feedback-message");
  var submitBtn = document.getElementById("feedback-submit");
  var fromTrack = new URLSearchParams(window.location.search).get("complaintId");
  if (fromTrack) { idInput.value = fromTrack; }

  form.addEventListener("submit", function (event) {
    event.preventDefault();
    message.textContent = "";
    var id = idInput.value.trim().toUpperCase();
    var rating = Number(ratingInput.value);
    if (!/^SCMS-\d{4}-\d{5}$/.test(id)) {
      message.textContent = "Enter a valid Complaint ID.";
      return;
    }
    if (!Number.isInteger(rating) || rating < 1 || rating > 5) {
      message.textContent = "Select a rating from 1 to 5.";
      return;
    }
    submitBtn.disabled = true;
    SCMS.authFetch("/api/v1/complaints/" + encodeURIComponent(id) + "/feedback", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ rating: rating, comment: commentInput.value })
    }).then(function (response) {
      return response.json().then(function (body) {
        return { ok: response.ok, body: body };
      });
    }).then(function (result) {
      if (result.ok) {
        message.textContent = "Thank you. Your feedback was submitted.";
        form.reset();
        idInput.value = id;
      } else {
        message.textContent = SCMS.errorText(result.body, "Could not submit feedback.");
      }
    }).catch(function () {
      message.textContent = "Could not submit feedback. Try again.";
    }).finally(function () {
      submitBtn.disabled = false;
    });
  });
})();
