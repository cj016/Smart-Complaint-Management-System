// SCMS-F-031 dashboard, F-032 filter/sort, F-030 assign, F-033 status update.
// Expects the login page (SCMS-F-002) to store the JWT in localStorage under "scms_token".
// The API enforces roles (SCMS-SR-002); this page only hides what a user cannot use.
(function () {
  var TOKEN_KEY = "scms_token";
  var API = "/api/v1/admin";
  var page = 1;
  var pages = 1;
  var selected = null; // the complaint row being managed

  function $(id) { return document.getElementById(id); }
  var warning = $("login-warning");
  var section = $("dashboard-section");
  var tbody = document.querySelector("#complaints-table tbody");
  var message = $("message");
  var panel = $("manage-panel");

  function slug(text) { return text.toLowerCase().replace(/\s+/g, "-"); }

  function cell(text) {
    var td = document.createElement("td");
    td.textContent = text; // textContent (not innerHTML) keeps this XSS-safe (SCMS-SR-003)
    return td;
  }

  function api(path, options) {
    var token = localStorage.getItem(TOKEN_KEY);
    options = options || {};
    options.headers = Object.assign({ Authorization: "Bearer " + token }, options.headers);
    return fetch(API + path, options).then(function (resp) {
      return resp.json().then(function (body) {
        return { status: resp.status, body: body };
      });
    });
  }

  function showLogin(text) {
    warning.querySelector("strong").textContent = text;
    warning.hidden = false;
    section.hidden = true;
  }

  function errorText(body) {
    if (body && body.error && body.error.details && body.error.details.fields) {
      var fields = body.error.details.fields;
      return Object.keys(fields).map(function (k) { return fields[k]; }).join(" ");
    }
    if (body && body.error && body.error.message) { return body.error.message; }
    return "Something went wrong. Try again.";
  }

  function render(items) {
    tbody.innerHTML = "";
    items.forEach(function (c) {
      var tr = document.createElement("tr");
      tr.appendChild(cell(c.complaintId));
      tr.appendChild(cell(c.category));
      tr.appendChild(cell(c.location));

      var priorityTd = cell(c.priority);
      if (c.priority === "Critical" || c.priority === "High") {
        priorityTd.className = "priority-" + slug(c.priority);
      }
      tr.appendChild(priorityTd);

      var statusTd = document.createElement("td");
      var badge = document.createElement("span");
      badge.className = "badge badge-" + slug(c.status);
      badge.textContent = c.status;
      statusTd.appendChild(badge);
      tr.appendChild(statusTd);

      tr.appendChild(cell(c.assignedTo ? c.assignedTo.name : "Unassigned"));
      tr.appendChild(cell(new Date(c.createdAt).toLocaleDateString()));

      var actionTd = document.createElement("td");
      var btn = document.createElement("button");
      btn.type = "button";
      btn.className = "btn-secondary";
      btn.textContent = "Manage";
      btn.setAttribute("aria-label", "Manage " + c.complaintId);
      btn.addEventListener("click", function () { openPanel(c); });
      actionTd.appendChild(btn);
      tr.appendChild(actionTd);
      tbody.appendChild(tr);
    });
  }

  function load() {
    if (!localStorage.getItem(TOKEN_KEY)) {
      showLogin("Please log in as an officer or admin to see this page.");
      return;
    }
    warning.hidden = true;
    section.hidden = false;

    var params = new URLSearchParams({
      page: page,
      sort: $("sort-field").value,
      order: $("sort-order").value
    });
    if ($("category-filter").value) { params.set("category", $("category-filter").value); }
    if ($("priority-filter").value) { params.set("priority", $("priority-filter").value); }
    if ($("status-filter").value) { params.set("status", $("status-filter").value); }

    api("/complaints?" + params.toString())
      .then(function (r) {
        if (r.status === 401) {
          localStorage.removeItem(TOKEN_KEY);
          showLogin("Your session has expired. Please log in again.");
          return;
        }
        if (r.status === 403) {
          showLogin("Your account does not have access to the admin dashboard.");
          return;
        }
        if (r.body.error) { message.textContent = errorText(r.body); return; }
        render(r.body.items);
        pages = r.body.pages || 1;
        message.textContent = r.body.total === 0 ? "No complaints match these filters." : "";
        $("page-info").textContent = "Page " + r.body.page + " of " + pages;
        $("prev-btn").disabled = r.body.page <= 1;
        $("next-btn").disabled = r.body.page >= pages;
      })
      .catch(function () { message.textContent = "Could not load complaints. Try again."; });
  }

  // ---- manage panel: assign (F-030) and status update (F-033) -------------------------

  function fillStatusOptions(c) {
    var select = $("status-select");
    select.innerHTML = "";
    c.nextStatuses.forEach(function (s) {
      var opt = document.createElement("option");
      opt.textContent = s;
      select.appendChild(opt);
    });
    var none = c.nextStatuses.length === 0;
    $("status-btn").disabled = none;
    $("status-message").textContent = none
      ? "No further status changes are possible from " + c.status +
        (c.status === "In Review" ? ". Assign an officer to continue." : ".")
      : "";
  }

  function openPanel(c) {
    selected = c;
    $("manage-title").textContent = "Manage " + c.complaintId;
    $("assign-message").textContent = "";
    $("remarks-input").value = "";
    $("department-input").value = c.department || "";
    fillStatusOptions(c);
    panel.hidden = false;
    panel.scrollIntoView({ behavior: "smooth", block: "nearest" });
  }

  function loadOfficers() {
    api("/officers").then(function (r) {
      var select = $("officer-select");
      if (r.status !== 200) { return; }
      r.body.items.forEach(function (o) {
        var opt = document.createElement("option");
        opt.value = o.id;
        opt.textContent = o.name + (o.department ? " (" + o.department + ")" : "");
        select.appendChild(opt);
      });
    });
  }

  $("assign-form").addEventListener("submit", function (e) {
    e.preventDefault();
    var out = $("assign-message");
    out.textContent = "";
    api("/complaints/" + encodeURIComponent(selected.complaintId) + "/assign", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        officerId: parseInt($("officer-select").value, 10),
        department: $("department-input").value
      })
    }).then(function (r) {
      if (r.status === 200) {
        selected = r.body;
        openPanel(r.body);
        $("assign-message").textContent = "Assigned to " + r.body.assignedTo.name + ".";
        load();
      } else if (r.status === 403) {
        out.textContent = "Only admins can assign complaints.";
      } else {
        out.textContent = errorText(r.body);
      }
    }).catch(function () { out.textContent = "Could not assign. Try again."; });
  });

  $("status-form").addEventListener("submit", function (e) {
    e.preventDefault();
    var out = $("status-message");
    out.textContent = "";
    api("/complaints/" + encodeURIComponent(selected.complaintId) + "/status", {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        status: $("status-select").value,
        remarks: $("remarks-input").value
      })
    }).then(function (r) {
      if (r.status === 200) {
        openPanel(r.body);
        $("status-message").textContent = "Status updated to " + r.body.status + ".";
        load();
      } else {
        out.textContent = errorText(r.body);
      }
    }).catch(function () { out.textContent = "Could not update. Try again."; });
  });

  $("close-panel").addEventListener("click", function () { panel.hidden = true; });

  ["category-filter", "priority-filter", "status-filter", "sort-field", "sort-order"]
    .forEach(function (id) {
      $(id).addEventListener("change", function () { page = 1; load(); });
    });
  $("prev-btn").addEventListener("click", function () { if (page > 1) { page -= 1; load(); } });
  $("next-btn").addEventListener("click", function () { if (page < pages) { page += 1; load(); } });

  if (localStorage.getItem(TOKEN_KEY)) { loadOfficers(); }
  load();
})();
