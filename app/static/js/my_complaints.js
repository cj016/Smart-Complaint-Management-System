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
  var reopenPanel = document.getElementById("reopen-panel");
  var reopenForm = document.getElementById("reopen-form");
  var reopenReason = document.getElementById("reopen-reason");
  var reopenMessage = document.getElementById("reopen-message");
  var reopenId = null;

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
    reopenPanel.hidden = true;
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

  function openReopenPanel(complaintId) {
    reopenId = complaintId;
    document.getElementById("reopen-id").textContent = complaintId;
    reopenMessage.textContent = "";
    reopenReason.value = "";
    reopenForm.hidden = false;
    reopenPanel.hidden = false;
    reopenReason.focus();
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

      var actions = document.createElement("td");
      var view = document.createElement("a");
      view.href = "/track?complaintId=" + encodeURIComponent(complaint.complaintId);
      view.className = "btn btn-secondary action-link";
      view.textContent = "Track";
      actions.appendChild(view);
      if (complaint.status === "Resolved") {
        var rate = document.createElement("a");
        rate.href = "/feedback?complaintId=" + encodeURIComponent(complaint.complaintId);
        rate.className = "btn btn-secondary action-link";
        rate.textContent = "Rate";
        actions.appendChild(rate);
      }
      if (complaint.status === "Resolved" || complaint.status === "Closed") {
        var reopenBtn = document.createElement("button");
        reopenBtn.type = "button";
        reopenBtn.textContent = "Reopen";
        reopenBtn.setAttribute("aria-label", "Reopen " + complaint.complaintId);
        reopenBtn.addEventListener("click", function () {
          openReopenPanel(complaint.complaintId);
        });
        actions.appendChild(reopenBtn);
      }
      tr.appendChild(actions);
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

  document.getElementById("reopen-cancel").addEventListener("click", function () {
    reopenPanel.hidden = true;
    reopenId = null;
  });

  reopenForm.addEventListener("submit", function (event) {
    event.preventDefault();
    var token = SCMS.getToken();
    if (!token) {
      handleExpiredSession();
      return;
    }
    var reason = reopenReason.value.trim();
    if (!reason) {
      reopenMessage.textContent = "Please enter a reason for reopening.";
      return;
    }
    var complaintId = reopenId;
    var submit = document.getElementById("reopen-submit");
    submit.disabled = true;
    reopenMessage.textContent = "Reopening complaint...";

    fetch("/api/v1/complaints/" + encodeURIComponent(complaintId) + "/reopen", {
      method: "POST",
      headers: {
        Authorization: "Bearer " + token,
        "Content-Type": "application/json"
      },
      body: JSON.stringify({ reason: reason })
    }).then(function (response) {
      if (response.status === 401) {
        handleExpiredSession();
        return null;
      }
      return response.json().then(function (data) {
        return { ok: response.ok, data: data };
      });
    }).then(function (result) {
      if (!result || token !== SCMS.getToken()) { return; }
      if (!result.ok) {
        reopenMessage.textContent = SCMS.errorText(result.data, "Could not reopen complaint.");
        return;
      }
      reopenForm.hidden = true;
      reopenMessage.textContent = "Complaint reopened. Check its updated status and timeline.";
      load();
    }).catch(function () {
      if (token === SCMS.getToken()) {
        reopenMessage.textContent = "Could not reopen complaint. Try again.";
      }
    }).finally(function () {
      submit.disabled = false;
    });
  });

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
