// SCMS-F-021: My Complaints page
// UI-03: Consistent expired-session handling.

(function () {
  "use strict";

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

  function cell(value) {
    var td = document.createElement("td");
    td.textContent = value == null ? "" : String(value);
    return td;
  }

  function clearComplaintData() {
    tbody.replaceChildren();
    message.textContent = "";
    pageInfo.textContent = "";
    page = 1;
    pages = 1;
    prevBtn.disabled = true;
    nextBtn.disabled = true;
  }

  function showLoginWarning() {
    clearComplaintData();
    warning.hidden = false;
    section.hidden = true;
  }

  function handleExpiredSession() {
    SCMS.clear();
    showLoginWarning();

    // Keep the shared navigation consistent without
    // modifying the authentication module.
    document.querySelectorAll("[data-auth]").forEach(function (el) {
      el.hidden = el.getAttribute("data-auth") === "in";
    });

    document.querySelectorAll("[data-roles]").forEach(function (el) {
      el.hidden = true;
    });

    var who = document.getElementById("nav-user");
    if (who) {
      who.textContent = "";
    }
  }

  function render(items) {
    tbody.replaceChildren();

    items.forEach(function (complaint) {
      var tr = document.createElement("tr");
      tr.appendChild(cell(complaint.complaintId));
      tr.appendChild(cell(complaint.category));
      tr.appendChild(cell(complaint.location));

      var statusTd = document.createElement("td");
      var badge = document.createElement("span");
      badge.className = "badge badge-" + slug(complaint.status);
      badge.textContent = complaint.status;
      statusTd.appendChild(badge);
      tr.appendChild(statusTd);

      var submitted = complaint.createdAt
        ? new Date(complaint.createdAt).toLocaleDateString()
        : "";

      tr.appendChild(cell(submitted));
      tbody.appendChild(tr);
    });
  }

  function load() {
    var token = SCMS.getToken();

    if (!token) {
      showLoginWarning();
      return;
    }

    warning.hidden = true;
    section.hidden = false;
    message.textContent = "Loading complaints...";

    var requestedPage = page;
    var url = "/api/v1/tracking/my-complaints?page=" + page;

    if (filter.value) {
      url += "&status=" + encodeURIComponent(filter.value);
    }

    fetch(url, {
      headers: { Authorization: "Bearer " + token }
    })
      .then(function (response) {
        if (response.status === 401) {
          handleExpiredSession();
          return null;
        }

        return response.json().then(function (data) {
          return { ok: response.ok, data: data };
        });
      })
      .then(function (result) {
        if (!result) {
          return;
        }

        // Ignore results from a session that has since changed.
        if (SCMS.getToken() !== token) {
          return;
        }

        if (!result.ok || result.data.error) {
          message.textContent = SCMS.errorText(
            result.data,
            "Could not load complaints."
          );
          return;
        }

        // Ignore an older pagination response.
        if (requestedPage !== page) {
          return;
        }

        var data = result.data;

        if (!Array.isArray(data.items)) {
          message.textContent = "Invalid response from server.";
          return;
        }

        render(data.items);

        pages = data.pages || 1;
        pageInfo.textContent = "Page " + data.page + " of " + pages;

        prevBtn.disabled = data.page <= 1;
        nextBtn.disabled = data.page >= pages;

        message.textContent = data.total === 0
          ? "No complaints found."
          : "";
      })
      .catch(function () {
        if (SCMS.getToken() === token) {
          message.textContent =
            "Could not load complaints. Try again.";
        }
      });
  }

  filter.addEventListener("change", function () {
    page = 1;
    load();
  });

  prevBtn.addEventListener("click", function () {
    if (page > 1) {
      page -= 1;
      load();
    }
  });

  nextBtn.addEventListener("click", function () {
    if (page < pages) {
      page += 1;
      load();
    }
  });

  load();
})();
