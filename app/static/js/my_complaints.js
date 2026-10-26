// SCMS-F-021 - "My Complaints" page.
// Expects the login page (SCMS-F-002) to store the JWT in localStorage under "scms_token".
(function () {
  var TOKEN_KEY = "scms_token";
  var page = 1;
  var pages = 1;

  var warning = document.getElementById("login-warning");
  var section = document.getElementById("complaints-section");
  var tbody = document.querySelector("#complaints-table tbody");
  var message = document.getElementById("message");
  var filter = document.getElementById("status-filter");
  var prevBtn = document.getElementById("prev-btn");
  var nextBtn = document.getElementById("next-btn");
  var pageInfo = document.getElementById("page-info");

  function slug(status) {
    return status.toLowerCase().replace(/\s+/g, "-");
  }

  function cell(text) {
    var td = document.createElement("td");
    td.textContent = text; // textContent (not innerHTML) keeps this XSS-safe (SCMS-SR-003)
    return td;
  }

  function render(items) {
    tbody.innerHTML = "";
    items.forEach(function (c) {
      var tr = document.createElement("tr");
      tr.appendChild(cell(c.complaintId));
      tr.appendChild(cell(c.category));
      tr.appendChild(cell(c.location));
      var statusTd = document.createElement("td");
      var badge = document.createElement("span");
      badge.className = "badge badge-" + slug(c.status);
      badge.textContent = c.status;
      statusTd.appendChild(badge);
      tr.appendChild(statusTd);
      tr.appendChild(cell(new Date(c.createdAt).toLocaleDateString()));
      tbody.appendChild(tr);
    });
  }

  function load() {
    var token = localStorage.getItem(TOKEN_KEY);
    if (!token) {
      warning.hidden = false;
      section.hidden = true;
      return;
    }
    warning.hidden = true;
    section.hidden = false;

    var url = "/api/v1/tracking/my-complaints?page=" + page;
    if (filter.value) { url += "&status=" + encodeURIComponent(filter.value); }

    fetch(url, { headers: { Authorization: "Bearer " + token } })
      .then(function (resp) {
        if (resp.status === 401) {
          localStorage.removeItem(TOKEN_KEY);
          warning.hidden = false;
          section.hidden = true;
          return null;
        }
        return resp.json();
      })
      .then(function (data) {
        if (!data) { return; }
        if (data.error) { message.textContent = data.error.message; return; }
        render(data.items);
        pages = data.pages || 1;
        message.textContent = data.total === 0 ? "No complaints found." : "";
        pageInfo.textContent = "Page " + data.page + " of " + pages;
        prevBtn.disabled = data.page <= 1;
        nextBtn.disabled = data.page >= pages;
      })
      .catch(function () { message.textContent = "Could not load complaints. Try again."; });
  }

  filter.addEventListener("change", function () { page = 1; load(); });
  prevBtn.addEventListener("click", function () { if (page > 1) { page -= 1; load(); } });
  nextBtn.addEventListener("click", function () { if (page < pages) { page += 1; load(); } });
  load();
})();
