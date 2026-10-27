// SCMS-F-020 - track a complaint by its Complaint ID.
// Expects the login page (SCMS-F-002) to store the JWT in localStorage under "scms_token".
(function () {
  var TOKEN_KEY = "scms_token";
  var warning = document.getElementById("login-warning");
  var input = document.getElementById("complaint-id");
  var button = document.getElementById("search-btn");
  var message = document.getElementById("message");
  var result = document.getElementById("result");

  function setText(id, text) {
    // textContent (not innerHTML) keeps this XSS-safe (SCMS-SR-003)
    document.getElementById(id).textContent = text || "-";
  }

  function slug(status) {
    return status.toLowerCase().replace(/\s+/g, "-");
  }

  function renderTimeline(steps) {
    var list = document.getElementById("timeline");
    list.innerHTML = "";
    steps.forEach(function (step) {
      var li = document.createElement("li");
      var badge = document.createElement("span");
      badge.className = "badge badge-" + slug(step.status);
      badge.textContent = step.status;
      var when = document.createElement("time");
      when.dateTime = step.changedAt;
      when.textContent = new Date(step.changedAt).toLocaleString();
      li.appendChild(badge);
      li.appendChild(when);
      if (step.remarks) {
        var note = document.createElement("p");
        note.textContent = step.remarks; // textContent keeps this XSS-safe (SCMS-SR-003)
        li.appendChild(note);
      }
      list.appendChild(li);
    });
  }

  function loadTimeline(id, token) {
    // SCMS-F-022: status timeline
    fetch("/api/v1/tracking/by-id/" + encodeURIComponent(id) + "/timeline",
          { headers: { Authorization: "Bearer " + token } })
      .then(function (resp) { return resp.json(); })
      .then(function (data) { if (data.steps) { renderTimeline(data.steps); } })
      .catch(function () { /* the details above still show; timeline is optional */ });
  }

  function show(c) {
    setText("result-id", c.complaintId);
    var badge = document.getElementById("result-status");
    badge.className = "badge badge-" + slug(c.status);
    badge.textContent = c.status;
    setText("result-category", c.category);
    setText("result-location", c.location);
    setText("result-description", c.description);
    setText("result-priority", c.priority);
    setText("result-created", new Date(c.createdAt).toLocaleString());
    setText("result-updated", new Date(c.updatedAt).toLocaleString());
    result.hidden = false;
  }

  function search() {
    var token = localStorage.getItem(TOKEN_KEY);
    message.textContent = "";
    result.hidden = true;
    if (!token) { warning.hidden = false; return; }
    warning.hidden = true;

    var id = input.value.trim();
    if (!id) { message.textContent = "Please enter a Complaint ID."; return; }

    fetch("/api/v1/tracking/by-id/" + encodeURIComponent(id),
          { headers: { Authorization: "Bearer " + token } })
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
        if (data.error) { message.textContent = data.error.message; return; }
        show(data);
        loadTimeline(data.complaintId, token);
      })
      .catch(function () { message.textContent = "Could not search. Try again."; });
  }

  button.addEventListener("click", search);
  input.addEventListener("keydown", function (e) { if (e.key === "Enter") { search(); } });
  warning.hidden = !!localStorage.getItem(TOKEN_KEY);
})();
