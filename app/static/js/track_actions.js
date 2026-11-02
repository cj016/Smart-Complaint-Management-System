// F024/F041. The server enforces ownership; displayed roles are cosmetic.
(function () {
  var result = document.getElementById('result');
  var section = document.getElementById('citizen-actions');
  var message = document.getElementById('action-message');
  var reopenForm = document.getElementById('reopen-form');
  var feedbackForm = document.getElementById('feedback-form');
  var currentId = '';
  var generation = 0;

  function sync() {
    var ticket = ++generation;
    var id = document.getElementById('result-id').textContent;
    var status = document.getElementById('result-status').textContent;
    section.hidden = result.hidden || SCMS.getRole() !== 'Complainant' ||
      ['Resolved', 'Closed'].indexOf(status) === -1;
    if (id !== currentId) {
      currentId = id;
      reopenForm.reset(); feedbackForm.reset(); message.textContent = '';
    }
    if (section.hidden) { return; }
    feedbackForm.hidden = true;
    SCMS.authFetch('/api/v1/tracking/by-id/' + encodeURIComponent(id) + '/feedback')
      .then(function (r) { if (!r.ok) { throw new Error('Could not load feedback.'); } return r.json(); })
      .then(function (data) {
        if (ticket !== generation) { return; }
        feedbackForm.hidden = !!data.feedback;
        message.textContent = data.feedback ? 'Feedback recorded: ' + data.feedback.rating + '/5.' : '';
      }).catch(function (e) { if (ticket === generation) { message.textContent = e.message; } });
  }

  function submit(form, action, body) {
    var id = currentId;
    var button = form.querySelector('button');
    button.disabled = true;
    message.textContent = 'Saving...';
    SCMS.authFetch('/api/v1/tracking/by-id/' + encodeURIComponent(id) + '/' + action, {
      method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body)
    }).then(function (r) {
      return r.json().then(function (data) {
        if (!r.ok) { throw new Error(SCMS.errorText(data)); }
        if (currentId !== id || result.hidden) { return; }
        if (action === 'reopen') {
          document.getElementById('search-btn').click();
          document.getElementById('message').textContent = 'Complaint reopened successfully.';
        } else {
          feedbackForm.hidden = true;
          message.textContent = 'Feedback saved. Thank you.';
        }
      });
    }).catch(function (e) { if (currentId === id) { message.textContent = e.message; } })
      .finally(function () { button.disabled = false; });
  }
  reopenForm.addEventListener('submit', function (e) {
    e.preventDefault();
    submit(reopenForm, 'reopen', { reason: document.getElementById('reopen-reason').value });
  });
  feedbackForm.addEventListener('submit', function (e) {
    e.preventDefault();
    submit(feedbackForm, 'feedback', {
      rating: Number(document.getElementById('feedback-rating').value),
      comment: document.getElementById('feedback-comment').value
    });
  });
  new MutationObserver(sync).observe(result, { attributes: true, attributeFilter: ['hidden'] });
})();
