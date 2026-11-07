// SCMS-F042: Admin-only resolution reports. API enforces access independently.
(function () {
  "use strict";
  if (!SCMS.requireRole(["Admin"])) { return; }

  var form = document.getElementById("report-filters");
  var area = document.getElementById("report-content");
  var message = document.getElementById("report-message");
  var start = document.getElementById("start-date");
  var end = document.getElementById("end-date");
  area.hidden = false;

  function query() {
    var params = new URLSearchParams();
    if (start.value) { params.set("start_date", start.value); }
    if (end.value) { params.set("end_date", end.value); }
    return params.toString() ? "?" + params.toString() : "";
  }

  function displayCounts(id, items) {
    var tbody = document.querySelector("#" + id + " tbody");
    tbody.replaceChildren();
    if (!items.length) {
      var empty = document.createElement("tr");
      var cell = document.createElement("td");
      cell.colSpan = 2;
      cell.textContent = "No matching complaints";
      empty.appendChild(cell);
      tbody.appendChild(empty);
      return;
    }
    items.forEach(function (item) {
      var tr = document.createElement("tr");
      var name = document.createElement("td");
      var count = document.createElement("td");
      name.textContent = item.name;
      count.textContent = String(item.count);
      tr.appendChild(name);
      tr.appendChild(count);
      tbody.appendChild(tr);
    });
  }

  function load() {
    if (start.value && end.value && start.value > end.value) {
      message.textContent = "Start date must be on or before end date.";
      return;
    }
    message.textContent = "Loading report...";
    SCMS.authFetch("/api/v1/reports/summary" + query()).then(function (response) {
      return response.json().then(function (data) {
        if (!response.ok) {
          message.textContent = SCMS.errorText(data, "Unable to load report.");
          return;
        }
        document.getElementById("total-complaints").textContent =
          String(data.totalComplaints);
        document.getElementById("average-turnaround").textContent =
          data.averageTurnaroundHours === null ? "N/A" :
          data.averageTurnaroundHours.toFixed(2) + " hours";
        document.getElementById("sample-note").textContent =
          "Turnaround based on " + data.turnaroundSampleCount +
          " currently Resolved/Closed complaints with valid timestamps.";
        displayCounts("category-table", data.byCategory);
        displayCounts("department-table", data.byDepartment);
        displayCounts("status-table", data.byStatus);
        message.textContent = "Showing " + data.totalComplaints + " complaints.";
      });
    }).catch(function () { message.textContent = "Unable to load report."; });
  }

  form.addEventListener("submit", function (event) {
    event.preventDefault();
    load();
  });
  document.getElementById("clear-filters").addEventListener("click", function () {
    start.value = "";
    end.value = "";
    load();
  });
  document.getElementById("export-csv").addEventListener("click", function () {
    if (start.value && end.value && start.value > end.value) {
      message.textContent = "Start date must be on or before end date.";
      return;
    }
    SCMS.authFetch("/api/v1/reports/summary.csv" + query()).then(function (response) {
      if (!response.ok) {
        message.textContent = "Could not export report.";
        return null;
      }
      return response.blob();
    }).then(function (blob) {
      if (!blob) { return; }
      var url = URL.createObjectURL(blob);
      var link = document.createElement("a");
      link.href = url;
      link.download = "scms-reports.csv";
      document.body.appendChild(link);
      link.click();
      link.remove();
      URL.revokeObjectURL(url);
    }).catch(function () { message.textContent = "Could not export report."; });
  });
  load();
})();
