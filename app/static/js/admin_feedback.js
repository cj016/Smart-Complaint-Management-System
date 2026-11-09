// SCMS-F041: Admin-only resolution feedback listing.
(function () {
  "use strict";
  if (!SCMS.requireRole(["Admin"])) { return; }

  var page = 1;
  var pages = 1;
  var tbody = document.querySelector("#feedback-table tbody");
  var message = document.getElementById("feedback-list-message");
  var prev = document.getElementById("feedback-prev");
  var next = document.getElementById("feedback-next");
  var pageInfo = document.getElementById("feedback-page-info");

  function cell(value) {
    var td = document.createElement("td");
    td.textContent = value == null ? "" : String(value);
    return td;
  }

  function load() {
    message.textContent = "Loading feedback...";
    SCMS.authFetch("/api/v1/admin/feedback?page=" + page + "&per_page=20")
      .then(function (response) {
        return response.json().then(function (body) {
          return { ok: response.ok, body: body };
        });
      }).then(function (result) {
        if (!result.ok) {
          message.textContent = SCMS.errorText(result.body, "Could not load feedback.");
          return;
        }
        tbody.replaceChildren();
        result.body.items.forEach(function (item) {
          var tr = document.createElement("tr");
          tr.appendChild(cell(item.complaintId));
          tr.appendChild(cell(item.category));
          tr.appendChild(cell(item.status));
          tr.appendChild(cell(item.rating + " / 5"));
          tr.appendChild(cell(item.comment));
          tr.appendChild(cell(item.createdAt
            ? new Date(item.createdAt).toLocaleString() : ""));
          tbody.appendChild(tr);
        });
        pages = result.body.pages || 1;
        pageInfo.textContent = "Page " + result.body.page + " of " + pages;
        prev.disabled = page <= 1;
        next.disabled = page >= pages;
        message.textContent = result.body.total === 0 ? "No feedback submitted yet." : "";
      }).catch(function () {
        message.textContent = "Could not load feedback. Try again.";
      });
  }
  prev.addEventListener("click", function () {
    if (page > 1) { page -= 1; load(); }
  });
  next.addEventListener("click", function () {
    if (page < pages) { page += 1; load(); }
  });
  load();
})();
