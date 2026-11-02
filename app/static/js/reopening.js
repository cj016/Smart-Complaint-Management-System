(function () {
  var result = document.getElementById('result');
  var section = document.getElementById('citizen-actions');
  var form = document.getElementById('reopen-form');
  var message = document.getElementById('action-message');
  var currentId = '';
  function sync() {
    var id = document.getElementById('result-id').textContent;
    var status = document.getElementById('result-status').textContent;
    section.hidden = result.hidden || SCMS.getRole() !== 'Complainant' ||
      ['Resolved', 'Closed'].indexOf(status) === -1;
    if (id !== currentId) { currentId = id; form.reset(); message.textContent = ''; }
  }
  form.addEventListener('submit', function (event) {
    event.preventDefault();
    var id = currentId, button = form.querySelector('button');
    button.disabled = true; message.textContent = 'Saving...';
    SCMS.authFetch('/api/v1/tracking/by-id/' + encodeURIComponent(id) + '/reopen', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ reason: document.getElementById('reopen-reason').value })
    }).then(function (response) {
      return response.json().then(function (data) {
        if (!response.ok) { throw new Error(SCMS.errorText(data)); }
        if (currentId === id && !result.hidden) {
          document.getElementById('search-btn').click();
          document.getElementById('message').textContent = 'Complaint reopened successfully.';
        }
      });
    }).catch(function (error) { if (currentId === id) { message.textContent = error.message; } })
      .finally(function () { button.disabled = false; });
  });
  new MutationObserver(sync).observe(result, { attributes: true, attributeFilter: ['hidden'] });
})();
