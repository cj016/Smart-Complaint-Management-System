// SCMS-F024: Staff can read their own in-app reopen notifications.
(function () {
  "use strict";
  var message = document.getElementById("staff-notifications-message");
  var section = document.getElementById("staff-notifications-section");
  var list = document.getElementById("staff-notifications-list");
  var unread = document.getElementById("staff-unread-count");

  function fetchStaff(url, options) {
    return SCMS.authFetch(url, options).then(function (response) {
      return response.json().then(function (data) {
        if (!response.ok) {
          throw new Error(SCMS.errorText(data, "Request failed."));
        }
        return data;
      });
    });
  }

  function load() {
    if (!SCMS.getToken() || ["Admin", "Officer"].indexOf(SCMS.getRole()) === -1) {
      message.textContent = "Please log in as an Admin or Officer.";
      section.hidden = true;
      return;
    }
    message.textContent = "Loading notifications...";
    fetchStaff("/api/v1/notifications/staff").then(function (data) {
      list.replaceChildren();
      unread.textContent = data.unreadCount;
      section.hidden = false;
      message.textContent = data.items.length ? "" : "No staff notifications yet.";
      data.items.forEach(function (entry) {
        var item = document.createElement("li");
        var text = document.createElement("span");
        text.textContent = entry.message;
        item.appendChild(text);
        if (!entry.isRead) {
          var button = document.createElement("button");
          button.type = "button";
          button.textContent = "Mark as read";
          button.addEventListener("click", function () {
            button.disabled = true;
            fetchStaff("/api/v1/notifications/staff/" + entry.id + "/read",
                       { method: "PATCH" }).then(load).catch(function (error) {
              message.textContent = error.message;
              button.disabled = false;
            });
          });
          item.appendChild(document.createTextNode(" "));
          item.appendChild(button);
        }
        list.appendChild(item);
      });
    }).catch(function (error) {
      message.textContent = error.message;
    });
  }

  load();
})();
