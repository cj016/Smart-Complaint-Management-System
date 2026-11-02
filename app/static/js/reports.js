(function () {
  if (!SCMS.requireRole(['Admin'])) { return; }
  var message = document.getElementById('report-message');
  var version = 0, feedbackVersion = 0, feedbackPage = 1;
  function query() {
    var params = new URLSearchParams();
    params.set('start_date', document.getElementById('report-start').value);
    params.set('end_date', document.getElementById('report-end').value);
    return params;
  }
  function renderRows(target, items, fields) {
    target.textContent = '';
    items.forEach(function (item) {
      var tr = document.createElement('tr');
      fields.forEach(function (key) {
        var td = document.createElement('td');
        td.textContent = item[key] == null ? '-' : item[key]; tr.appendChild(td);
      });
      target.appendChild(tr);
    });
  }
  function checked(r) {
    if (!r.ok) {
      return r.json().then(function (data) { throw new Error(SCMS.errorText(data)); });
    }
    return r.json();
  }
  function loadFeedback() {
    var ticket = ++feedbackVersion, params = query();
    var note = document.getElementById('feedback-message');
    var prev = document.getElementById('feedback-prev');
    var next = document.getElementById('feedback-next');
    prev.disabled = true; next.disabled = true;
    document.getElementById('feedback-rows').textContent = '';
    note.textContent = 'Loading feedback...';
    params.set('page', feedbackPage);
    SCMS.authFetch('/api/v1/reports/feedback?' + params).then(checked).then(function (data) {
      if (ticket !== feedbackVersion) { return; }
      renderRows(document.getElementById('feedback-rows'), data.items,
        ['complaintId', 'rating', 'comment', 'createdAt']);
      note.textContent = data.total + ' ratings; page ' + data.page + ' of ' + (data.pages || 1);
      prev.disabled = data.page <= 1; next.disabled = data.page >= data.pages;
    }).catch(function (e) { if (ticket === feedbackVersion) { note.textContent = e.message; } });
  }
  function load(csv) {
    var ticket = ++version, params = query();
    var group = document.getElementById('report-group').value;
    params.set('group_by', group); params.set('format', csv ? 'csv' : 'json');
    message.textContent = 'Loading...';
    if (!csv) {
      document.getElementById('report-rows').textContent = '';
      feedbackPage = 1; loadFeedback();
    }
    SCMS.authFetch('/api/v1/reports?' + params)
      .then(function (r) { return csv && r.ok ? r.blob() : checked(r); })
      .then(function (data) {
        if (ticket !== version) { return; }
        if (csv) {
          var url = URL.createObjectURL(data);
          var a = document.createElement('a'); a.href = url;
          a.download = 'scms-' + group + '-report.csv';
          document.body.appendChild(a); a.click(); a.remove();
          setTimeout(function () { URL.revokeObjectURL(url); }, 1000);
          message.textContent = 'CSV downloaded.'; return;
        }
        renderRows(document.getElementById('report-rows'), data.items,
          ['group', 'total', 'resolved', 'closed', 'reopened', 'completed', 'open',
            'resolutionRate', 'averageTurnaroundHours', 'turnaroundSamples']);
        message.textContent = data.totalComplaints + ' complaints. ' +
          (data.items.length ? '' : 'No data yet.');
      }).catch(function (e) { if (ticket === version) { message.textContent = e.message; } });
  }
  document.getElementById('load-report').addEventListener('click', function () { load(false); });
  document.getElementById('export-report').addEventListener('click', function () { load(true); });
  document.getElementById('feedback-prev').addEventListener('click', function () {
    if (feedbackPage > 1) { feedbackPage -= 1; loadFeedback(); }
  });
  document.getElementById('feedback-next').addEventListener('click', function () {
    feedbackPage += 1; loadFeedback();
  });
  load(false);
})();
