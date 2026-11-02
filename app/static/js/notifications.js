// SCMS-F023: Citizen notification inbox.

(function () {
  "use strict";

  var page = 1;
  var pages = 1;

  var warning = document.getElementById("notifications-login-warning");
  var section = document.getElementById("notifications-section");
  var list = document.getElementById("notifications-list");
  var message = document.getElementById("notifications-message");
  var unreadCount = document.getElementById("unread-count");
  var prev = document.getElementById("notifications-prev");
  var next = document.getElementById("notifications-next");
  var pageInfo = document.getElementById("notifications-page-info");

  function showLoginWarning() {
    list.replaceChildren();
    warning.hidden = false;
    section.hidden = true;
  }

  function apiRequest(url, options) {
    options = options || {};
    options.headers = Object.assign({}, options.headers, {
      Authorization: "Bearer " + SCMS.getToken()
    });

    return fetch(url, options).then(function (response) {
      if (response.status === 401) {
        SCMS.clear();
        showLoginWarning();
        return null;
      }

      return response.json().then(function (data) {
        if (!response.ok) {
          throw new Error(SCMS.errorText(data, "Request failed."));
        }
        return data;
      });
    });
  }

  function loadUnreadCount() {
    return apiRequest("/api/v1/notifications/unread-count")
      .then(function (data) {
        if (data) {
          unreadCount.textContent = data.unreadCount;
        }
      });
  }

  function render(items) {
    list.replaceChildren();

    items.forEach(function (item) {
      var card = document.createElement("article");
      card.className = "card notification-item";

      var text = document.createElement("p");
      text.textContent = item.message;
      card.appendChild(text);

      var info = document.createElement("small");
      info.textContent = item.isRead ? "Read" : "Unread";
      card.appendChild(info);

      if (!item.isRead && item.channel === "in_app") {
        var button = document.createElement("button");
        button.type = "button";
        button.textContent = "Mark as read";

        button.addEventListener("click", function () {
          button.disabled = true;

          apiRequest(
            "/api/v1/notifications/" + item.id + "/read",
            { method: "PATCH" }
          ).then(function (data) {
            if (data) {
              load();
            }
          }).catch(function (error) {
            message.textContent = error.message;
            button.disabled = false;
          });
        });

        card.appendChild(button);
      }

      list.appendChild(card);
    });
  }

  function load() {
    if (!SCMS.getToken() || SCMS.getRole() !== "Complainant") {
      showLoginWarning();
      return;
    }

    warning.hidden = true;
    section.hidden = false;
    message.textContent = "Loading notifications...";

    apiRequest("/api/v1/notifications/?page=" + page)
      .then(function (data) {
        if (!data) {
          return;
        }

        render(data.items);
        pages = data.pages || 1;

        pageInfo.textContent = "Page " + data.page + " of " + pages;
        prev.disabled = data.page <= 1;
        next.disabled = data.page >= pages;

        message.textContent = data.total === 0
          ? "No notifications yet."
          : "";

        loadUnreadCount().catch(function (error) {
          message.textContent = error.message;
        });
      })
      .catch(function (error) {
        message.textContent = error.message;
      });
  }

  prev.addEventListener("click", function () {
    if (page > 1) {
      page -= 1;
      load();
    }
  });

  next.addEventListener("click", function () {
    if (page < pages) {
      page += 1;
      load();
    }
  });

  load();
})();
