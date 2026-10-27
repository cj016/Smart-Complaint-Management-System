// SCMS-F031 (view all), F032 (filter/sort), F030 (assign), F033 (update status + remarks).
// Expects the login page (SCMS-F-002) to store the JWT in localStorage under "scms_token".
// The page hides controls by role, but the server enforces the rules (SCMS-SR-002).
(function () {
  var TOKEN_KEY = "scms_token";
  var page = 1;
  var pages = 1;
  var selectedId = null;
  var isAdmin = false;

  function $(id) { return document.getElementById(id); }

  var warning = $("login-warning");
  var forbidden = $("forbidden-warning");
  var dashboard = $("dashboard");
  var tbody = document.querySelector("#complaints-table tbody");
  var message = $("message");
  var prevBtn = $("prev-btn");
  var nextBtn = $("next-btn");
  var pageInfo = $("page-info");
  var manage = $("manage");
  var mMessage = $("m-message");

  function token() { return localStorage.getItem(TOKEN_KEY); }

  function roleFromToken(t) {
    try {
      var part = t.split(".")[1].replace(/-/g, "+").replace(/_/g, "/");
      return JSON.parse(atob(part)).role || null;
    } catch (e) { return null; }
  }

  function slug(status) { return status.toLowerCase().replace(/\s+/g, "-"); }

  function setText(id, text) {
    // textContent (not innerHTML) keeps this XSS-safe (SCMS-SR-003)
    $(id).textContent = text || "-";
  }

  function errorText(data) {
    if (data && data.error) {
      if (typeof data.error === "string") { return data.error; }
      if (data.error.message) { return data.error.message; }
    }
    return "Something went wrong. Try again.";
  }

  function showLogin() {
    warning.hidden = false;
    forbidden.hidden = true;
    dashboard.hidden = true;
  }

  function showForbidden() {
    warning.hidden = true;
    forbidden.hidden = false;
    dashboard.hidden = true;
  }

  // Returns a promise of {status, data}. A 401 clears the token and shows the login notice.
  function api(method, url, body) {
    var opts = { method: method, headers: { Authorization: "Bearer " + token() } };
    if (body) {
      opts.headers["Content-Type"] = "application/json";
      opts.body = JSON.stringify(body);
    }
    return fetch(url, opts).then(function (resp) {
      if (resp.status === 401) {
        localStorage.removeItem(TOKEN_KEY);
        showLogin();
        throw new Error("unauthorised");
      }
      return resp.json().then(function (data) {
        return { status: resp.status, data: data };
      });
    });
  }

  function fillSelect(select, values, keepAll) {
    select.innerHTML = "";
    if (keepAll) {
      var all = document.createElement("option");
      all.value = "";
      all.textContent = "All";
      select.appendChild(all);
    }
    values.forEach(function (v) {
      var o = document.createElement("option");
      o.value = v;
      o.textContent = v;
      select.appendChild(o);
    });
  }

  function cell(text) {
    var td = document.createElement("td");
    td.textContent = text;
    return td;
  }

  function badge(status) {
    var span = document.createElement("span");
    span.className = "badge badge-" + slug(status);
    span.textContent = status;
    return span;
  }

  function render(items) {
    tbody.innerHTML = "";
    items.forEach(function (c) {
      var tr = document.createElement("tr");
      tr.appendChild(cell(c.complaintId));
      tr.appendChild(cell(c.category));
      tr.appendChild(cell(c.location));
      tr.appendChild(cell(c.priority));
      var statusTd = document.createElement("td");
      statusTd.appendChild(badge(c.status));
      tr.appendChild(statusTd);
      tr.appendChild(cell(c.assignedTo ? c.assignedTo.name : "-"));
      tr.appendChild(cell(new Date(c.createdAt).toLocaleDateString()));
      var actionTd = document.createElement("td");
      var btn = document.createElement("button");
      btn.type = "button";
      btn.className = "btn-secondary";
      btn.textContent = "Manage";
      btn.setAttribute("aria-label", "Manage " + c.complaintId);
      btn.addEventListener("click", function () { openManage(c.complaintId); });
      actionTd.appendChild(btn);
      tr.appendChild(actionTd);
      tbody.appendChild(tr);
    });
  }

  function query() {
    var params = ["page=" + page];
    [["f-q", "q"], ["f-status", "status"], ["f-category", "category"],
     ["f-priority", "priority"], ["f-sort", "sort"], ["f-order", "order"]
    ].forEach(function (pair) {
      var v = $(pair[0]).value.trim();
      if (v) { params.push(pair[1] + "=" + encodeURIComponent(v)); }
    });
    return params.join("&");
  }

  function load() {
    api("GET", "/api/v1/admin/complaints?" + query()).then(function (r) {
      if (r.status === 403) { showForbidden(); return; }
      if (r.status !== 200) { message.textContent = errorText(r.data); return; }
      render(r.data.items);
      pages = r.data.pages || 1;
      message.textContent = r.data.total === 0 ? "No complaints match these filters." : "";
      pageInfo.textContent = "Page " + r.data.page + " of " + pages;
      prevBtn.disabled = r.data.page <= 1;
      nextBtn.disabled = r.data.page >= pages;
    }).catch(function (e) {
      if (e.message !== "unauthorised") { message.textContent = "Could not load complaints."; }
    });
  }

  // ---- manage panel (assign + update status) ----

  function showDetail(c) {
    selectedId = c.complaintId;
    setText("m-id", c.complaintId);
    var b = $("m-status");
    b.className = "badge badge-" + slug(c.status);
    b.textContent = c.status;
    setText("m-category", c.category);
    setText("m-location", c.location);
    setText("m-description", c.description);
    setText("m-priority", c.priority);
    setText("m-department", c.department);
    setText("m-assignee", c.assignedTo ? c.assignedTo.name : "");
    setText("m-resolution", c.resolutionRemarks);

    var canMove = c.allowedStatuses && c.allowedStatuses.length > 0;
    fillSelect($("m-new-status"), c.allowedStatuses || [], false);
    $("status-box").hidden = !canMove;
    $("assign-box").hidden = !isAdmin || c.status === "Resolved" || c.status === "Closed";
    $("m-remarks").value = "";
    manage.hidden = false;
  }

  function openManage(id) {
    mMessage.textContent = "";
    api("GET", "/api/v1/admin/complaints/" + encodeURIComponent(id)).then(function (r) {
      if (r.status !== 200) { message.textContent = errorText(r.data); return; }
      showDetail(r.data);
      manage.scrollIntoView({ behavior: "smooth", block: "nearest" });
    }).catch(function () {});
  }

  function afterChange(r, okText) {
    if (r.status === 200) {
      showDetail(r.data);
      mMessage.textContent = okText;
      load();
    } else {
      mMessage.textContent = errorText(r.data);
    }
  }

  function assign() {
    var officerId = parseInt($("m-officer").value, 10);
    if (isNaN(officerId)) { mMessage.textContent = "Choose an officer first."; return; }
    var body = { officerId: officerId };
    var dept = $("m-department-input").value.trim();
    if (dept) { body.department = dept; }
    api("POST", "/api/v1/admin/complaints/" + encodeURIComponent(selectedId) + "/assign", body)
      .then(function (r) { afterChange(r, "Complaint assigned."); })
      .catch(function () {});
  }

  function updateStatus() {
    var body = { status: $("m-new-status").value, remarks: $("m-remarks").value };
    api("POST", "/api/v1/admin/complaints/" + encodeURIComponent(selectedId) + "/status", body)
      .then(function (r) { afterChange(r, "Status updated."); })
      .catch(function () {});
  }

  function loadOptions() {
    return api("GET", "/api/v1/admin/filter-options").then(function (r) {
      if (r.status === 200) {
        fillSelect($("f-status"), r.data.statuses, true);
        fillSelect($("f-priority"), r.data.priorities, true);
        fillSelect($("f-category"), r.data.categories, true);
      }
    });
  }

  function loadOfficers() {
    if (!isAdmin) { return Promise.resolve(); }
    return api("GET", "/api/v1/admin/officers").then(function (r) {
      var select = $("m-officer");
      select.innerHTML = "";
      if (r.status !== 200) { return; }
      r.data.items.forEach(function (o) {
        var opt = document.createElement("option");
        opt.value = o.id;
        opt.textContent = o.name + (o.department ? " (" + o.department + ")" : "");
        select.appendChild(opt);
      });
    });
  }

  function resetFilters() {
    ["f-q", "f-status", "f-category", "f-priority"].forEach(function (id) { $(id).value = ""; });
    $("f-sort").value = "created_at";
    $("f-order").value = "desc";
    page = 1;
    load();
  }

  $("apply-btn").addEventListener("click", function () { page = 1; load(); });
  $("reset-btn").addEventListener("click", resetFilters);
  $("f-q").addEventListener("keydown", function (e) {
    if (e.key === "Enter") { page = 1; load(); }
  });
  prevBtn.addEventListener("click", function () { if (page > 1) { page -= 1; load(); } });
  nextBtn.addEventListener("click", function () { if (page < pages) { page += 1; load(); } });
  $("assign-btn").addEventListener("click", assign);
  $("status-btn").addEventListener("click", updateStatus);
  $("close-btn").addEventListener("click", function () { manage.hidden = true; });

  if (!token()) {
    showLogin();
  } else {
    var role = roleFromToken(token());
    if (role === "Complainant") {
      showForbidden();
    } else {
      isAdmin = role === "Admin";
      dashboard.hidden = false;
      loadOptions().then(loadOfficers).then(load).catch(function () {});
    }
  }
})();
