(function () {
  if (!SCMS.requireRole(['Complainant', 'Admin'])) { return; }
  var citizen = SCMS.getRole() === 'Complainant';
  document.getElementById('citizen-feedback').hidden = !citizen;
  document.getElementById('admin-feedback').hidden = citizen;
  var form = document.getElementById('feedback-form');
  var message = document.getElementById('citizen-message');
  var selected = '', generation = 0, page = 1;
  function checked(response) {
    return response.json().then(function (data) {
      if (!response.ok) { throw new Error(SCMS.errorText(data)); } return data;
    });
  }
  function find() {
    var ticket = ++generation;
    var id = document.getElementById('feedback-id').value.trim().toUpperCase();
    selected = ''; form.hidden = true; form.reset(); message.textContent = 'Loading...';
    var base = '/api/v1/tracking/by-id/' + encodeURIComponent(id);
    SCMS.authFetch(base).then(checked).then(function (complaint) {
      if (ticket !== generation) { return null; }
      if (['Resolved', 'Closed'].indexOf(complaint.status) === -1) {
        throw new Error('Feedback requires a resolved or closed complaint.');
      }
      return SCMS.authFetch(base + '/feedback').then(checked);
    }).then(function (data) {
      if (!data || ticket !== generation) { return; }
      if (data.feedback) {
        message.textContent = 'Saved rating: ' + data.feedback.rating + '/5. ' +
          (data.feedback.comment || ''); return;
      }
      selected = id; form.hidden = false; message.textContent = 'Complaint found: ' + id;
    }).catch(function (error) { if (ticket === generation) { message.textContent = error.message; } });
  }
  document.getElementById('feedback-load').addEventListener('click', find);
  document.getElementById('feedback-id').addEventListener('input', function () {
    generation += 1; selected = ''; form.hidden = true; message.textContent = '';
  });
  form.addEventListener('submit', function (event) {
    event.preventDefault(); if (!selected) { return; }
    var id = selected, ticket = generation, button = form.querySelector('button');
    button.disabled = true;
    SCMS.authFetch('/api/v1/tracking/by-id/' + encodeURIComponent(id) + '/feedback', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ rating: Number(document.getElementById('feedback-rating').value),
        comment: document.getElementById('feedback-comment').value })
    }).then(checked).then(function () {
      if (ticket === generation) { form.hidden = true; message.textContent = 'Feedback saved.'; }
    }).catch(function (error) { if (ticket === generation) { message.textContent = error.message; } })
      .finally(function () { button.disabled = false; });
  });
  function adminLoad() {
    var ticket = ++generation, params = new URLSearchParams();
    var note = document.getElementById('feedback-message');
    var prev = document.getElementById('feedback-prev'), next = document.getElementById('feedback-next');
    prev.disabled = true; next.disabled = true;
    document.getElementById('feedback-rows').textContent = ''; note.textContent = 'Loading...';
    params.set('page', page);
    params.set('start_date', document.getElementById('feedback-start').value);
    params.set('end_date', document.getElementById('feedback-end').value);
    SCMS.authFetch('/api/v1/feedback/admin?' + params).then(checked).then(function (data) {
      if (ticket !== generation) { return; }
      data.items.forEach(function (item) {
        var tr = document.createElement('tr');
        ['complaintId', 'rating', 'comment', 'createdAt'].forEach(function (key) {
          var td = document.createElement('td'); td.textContent = item[key] == null ? '-' : item[key];
          tr.appendChild(td);
        });
        document.getElementById('feedback-rows').appendChild(tr);
      });
      note.textContent = data.total + ' ratings; page ' + data.page + ' of ' + (data.pages || 1);
      prev.disabled = data.page <= 1; next.disabled = data.page >= data.pages;
    }).catch(function (error) { if (ticket === generation) { note.textContent = error.message; } });
  }
  document.getElementById('feedback-refresh').addEventListener('click', function () {
    page = 1; adminLoad();
  });
  document.getElementById('feedback-prev').addEventListener('click', function () {
    if (page > 1) { page -= 1; adminLoad(); }
  });
  document.getElementById('feedback-next').addEventListener('click', function () { page += 1; adminLoad(); });
  if (!citizen) { adminLoad(); }
})();
