
    function statusPill(status) {
      const key = (status || '').toLowerCase();
      if (key === 'resolved') return '<span class="pill resolved">Resolved</span>';
      if (key === 'in progress') return '<span class="pill progress">In Progress</span>';
      if (key === 'rejected') return '<span class="pill rejected">Rejected</span>';
      return '<span class="pill pending">' + (status || 'Pending') + '</span>';
    }
    async function updateIssueStatus(issueId, nextStatus) {
      const formData = new FormData();
      formData.append('status', nextStatus);
      const res = await fetch('/admin/issues/' + issueId, { method: 'PUT', body: formData });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        alert(err.detail || 'Status not been updated');
        return;
      }
      const payload = await res.json();
      if (payload.mail_sent === false) {
        alert('Status updated, but email failed: ' + (payload.mail_status || 'unknown'));
      } else if (payload.mail_sent === true) {
        alert('Status updated and user notification email sent.');
      }
      loadPanel();
    }
    let emergencyAlertStore = [];
    let complaintStore = [];
    let workerStore = [];
    let workerResetStore = [];
    let workerResolutionStore = [];
    let departmentStore = [];
    let currentAssignmentIssueId = null;
    function esc(value) {
      return String(value ?? '')
        .replaceAll('&', '&amp;')
        .replaceAll('<', '&lt;')
        .replaceAll('>', '&gt;')
        .replaceAll('"', '&quot;')
        .replaceAll("'", '&#39;');
    }
    function prettyDate(value) {
      if (!value) return '-';
      try { return new Date(value).toLocaleString(); } catch (_) { return value; }
    }
    function renderDepartmentOptions(targetId) {
      const target = document.getElementById(targetId);
      if (!target) return;
      target.innerHTML = (departmentStore || []).map(item => `<option value="${esc(item)}">${esc(item)}</option>`).join('');
    }
    function getWorkersForDepartment(department) {
      const selected = String(department || '').trim().toLowerCase();
      return (workerStore || []).filter(worker =>
        worker.is_active !== false && String(worker.department || '').trim().toLowerCase() === selected
      );
    }
    function renderAssignmentWorkerOptions() {
      const departmentField = document.getElementById('assignDepartment');
      const workerField = document.getElementById('assignWorker');
      const helper = document.getElementById('assignWorkerHelper');
      const assignButton = document.getElementById('assignSubmitButton');
      if (!departmentField || !workerField) return;
      const departmentWorkers = getWorkersForDepartment(departmentField.value);
      workerField.innerHTML = departmentWorkers.length
        ? departmentWorkers.map(worker => `<option value="${esc(worker.worker_id)}">${esc(worker.worker_id)} - ${esc(worker.department)} Department</option>`).join('')
        : '<option value="">No registered worker available</option>';
      workerField.disabled = departmentWorkers.length === 0;
      if (assignButton) assignButton.disabled = departmentWorkers.length === 0;
      if (helper) {
        helper.textContent = departmentWorkers.length
          ? `${departmentWorkers.length} registered worker${departmentWorkers.length === 1 ? '' : 's'} available. New workers appear here after creation.`
          : 'Create a worker for this department before assigning this complaint.';
      }
    }
    function openWorkerModal() {
      renderDepartmentOptions('workerDepartment');
      const modal = document.getElementById('workerModal');
      if (modal) modal.classList.add('show');
    }
    function closeWorkerModal(event) {
      if (event && event.target && event.target.id !== 'workerModal') return;
      const modal = document.getElementById('workerModal');
      if (modal) modal.classList.remove('show');
    }
    function viewWorkerPassword(workerDbId) {
      const worker = workerStore.find(item => item.id === workerDbId);
      if (!worker) return;
      alert(`Worker ID: ${worker.worker_id}\nPassword: ${worker.password_plaintext || 'Not available'}`);
    }
    async function createWorker(event) {
      event.preventDefault();
      const message = document.getElementById('workerCreateMessage');
      const payload = {
        department: document.getElementById('workerDepartment').value,
        password: document.getElementById('workerPassword').value
      };
      message.textContent = '';
      const res = await fetch('/admin/workers', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) {
        message.textContent = data.detail || 'Unable to create worker';
        return;
      }
      message.textContent = (data.message || 'Worker created successfully') + ' | Worker ID: ' + (data.worker?.worker_id || '-');
      document.getElementById('workerPassword').value = '';
      alert('Worker created.\nWorker ID: ' + (data.worker?.worker_id || '-') + '\nPassword: ' + payload.password);
      loadPanel();
    }
    async function adminResetWorkerPassword(workerDbId) {
      const nextPassword = prompt('Enter the new password for this worker:');
      if (!nextPassword) return;
      const res = await fetch('/admin/workers/' + workerDbId + '/reset-password', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ new_password: nextPassword })
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) {
        alert(data.detail || 'Unable to update worker password');
        return;
      }
      alert(data.message || 'Worker password updated');
      loadPanel();
    }
    async function deleteWorkerResetRequest(requestId) {
      if (!requestId) return;
      const confirmed = confirm('Delete this password reset request?');
      if (!confirmed) return;
      const res = await fetch('/admin/worker-reset-requests/' + requestId, { method: 'DELETE' });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) {
        alert(data.detail || 'Unable to delete password reset request');
        return;
      }
      loadPanel();
    }
    function openAssignModal(issueId) {
      const issue = complaintStore.find(item => item.id === issueId);
      currentAssignmentIssueId = issueId;
      renderDepartmentOptions('assignDepartment');
      const departmentField = document.getElementById('assignDepartment');
      if (departmentField && issue?.assigned_department) departmentField.value = issue.assigned_department;
      renderAssignmentWorkerOptions();
      document.getElementById('assignComplaintLabel').textContent = issue
        ? `${issue.complaint_number || '-'} | ${issue.title || '-'}`
        : 'Assign selected complaint';
      document.getElementById('assignDurationValue').value = 1;
      document.getElementById('assignDurationUnit').value = 'days';
      document.getElementById('assignModal').classList.add('show');
    }
    function closeAssignModal(event) {
      if (event && event.target && event.target.id !== 'assignModal') return;
      const modal = document.getElementById('assignModal');
      if (modal) modal.classList.remove('show');
      currentAssignmentIssueId = null;
    }
    async function submitAssignment() {
      if (!currentAssignmentIssueId) return;
      const payload = {
        department: document.getElementById('assignDepartment').value,
        worker_id: document.getElementById('assignWorker')?.value || '',
        duration_value: Number(document.getElementById('assignDurationValue').value || 1),
        duration_unit: document.getElementById('assignDurationUnit').value
      };
      if (!payload.worker_id) {
        alert('Select a registered worker before assigning this complaint.');
        return;
      }
      const res = await fetch('/admin/issues/' + currentAssignmentIssueId + '/assign', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) {
        alert(data.detail || 'Complaint assignment failed');
        return;
      }
      closeAssignModal();
      loadPanel();
    }
    function viewEmergency(index) {
      const item = emergencyAlertStore[index];
      if (!item) return;
      const message =
        `Sender: ${item.sender_name || '-'}
` +
        `Email: ${item.sender_email || '-'}
` +
        `Phone: ${item.sender_phone || '-'}
` +
        `Location: ${item.location || '-'}
` +
        `Sensor: ${item.sensor_label || '-'}
` +
        `Severity: ${item.severity || '-'}
` +
        `Priority: ${item.priority || '-'}
` +
        `Value: ${item.value || '-'}
` +
        `Note: ${item.note || '-'}
` +
        `Time: ${item.created_at || '-'}`;
      alert(message);
    }
    async function updateEmergencyStatus(index) {
      const item = emergencyAlertStore[index];
      if (!item) return;
      const picker = document.getElementById('em_status_' + index);
      if (!picker) return;
      const nextStatus = picker.value;
      const formData = new FormData();
      formData.append('status', nextStatus);
      const res = await fetch('/admin/emergency-alerts/' + item.id + '/status', { method: 'PUT', body: formData });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        alert(err.detail || 'Emergency status update failed');
        return;
      }
      const payload = await res.json();
      if (payload.mail_sent === true) {
        alert('Emergency status updated and user email sent.');
      } else if (payload.mail_sent === false) {
        alert('Emergency status updated, but email failed: ' + (payload.mail_status || 'unknown'));
      }
      loadPanel();
    }
    async function deleteEmergency(index) {
      const item = emergencyAlertStore[index];
      if (!item) return;
      const confirmed = confirm('Delete this emergency alert? This action cannot be undone.');
      if (!confirmed) return;
      const res = await fetch('/admin/emergency-alerts/' + item.id, { method: 'DELETE' });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        alert(err.detail || 'Emergency delete failed');
        return;
      }
      loadPanel();
    }
    function closeComplaintModal(event) {
      if (event && event.target && event.target.id !== 'complaintModal') return;
      const modal = document.getElementById('complaintModal');
      if (modal) modal.classList.remove('show');
    }
    function viewComplaint(index) {
      const item = complaintStore[index];
      if (!item) return;
      const modal = document.getElementById('complaintModal');
      const body = document.getElementById('complaintModalBody');
      if (!modal || !body) return;

      const imageBlock = (item.media_urls || []).length
        ? `<div class="thumbGrid">${item.media_urls.map(src => `<a href="${esc(src)}" target="_blank" rel="noopener noreferrer"><img src="${esc(src)}" alt="Complaint photo" /></a>`).join('')}</div>`
        : '<p class="muted">No uploaded images for this complaint.</p>';

      body.innerHTML = `
        <div class="mono" style="margin-bottom:8px;">${esc(item.complaint_number || '-')}</div>
        <p><strong>User:</strong> ${esc(item.user_name || '-')}</p>
        <p><strong>Issue:</strong> ${esc(item.title || '-')}</p>
        <p><strong>Location:</strong> ${esc(item.location || '-')}</p>
        <p><strong>Status:</strong> ${esc(item.status || '-')}</p>
        <p><strong>Category:</strong> ${esc(item.category || '-')}</p>
        <p><strong>Assigned Department:</strong> ${esc(item.assigned_department || 'Not assigned')}</p>
        <p><strong>Deadline:</strong> ${esc(item.assignment_duration_label || '-')}${item.assignment_deadline ? ' | ' + esc(prettyDate(item.assignment_deadline)) : ''}</p>
        <p><strong>Reported At:</strong> ${esc(prettyDate(item.created_at))}</p>
        <p><strong>Description:</strong> ${esc(item.description || '-')}</p>
        <h4 style="margin:12px 0 8px;">Uploaded Images</h4>
        ${imageBlock}
      `;
      modal.classList.add('show');
    }
    async function deleteComplaint(issueId) {
      if (!issueId) return;
      const confirmed = confirm('Delete this complaint? This action cannot be undone.');
      if (!confirmed) return;
      const res = await fetch('/admin/issues/' + issueId, { method: 'DELETE' });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        alert(err.detail || 'Delete failed');
        return;
      }
      closeComplaintModal();
      loadPanel();
    }
    async function loadPanel() {
      const res = await fetch('/admin/panel-data');
      if (!res.ok) { window.location.href = '/admin'; return; }
      const data = await res.json();
      emergencyAlertStore = data.recent_alerts || [];
      complaintStore = data.reported_complaints || [];
      workerStore = data.workers || [];
      workerResetStore = data.worker_reset_requests || [];
      workerResolutionStore = data.worker_resolution_requests || [];
      departmentStore = data.departments || [];
      renderDepartmentOptions('workerDepartment');
      const assignDepartment = document.getElementById('assignDepartment');
      if (assignDepartment && !assignDepartment.dataset.bound) {
        assignDepartment.addEventListener('change', renderAssignmentWorkerOptions);
        assignDepartment.dataset.bound = 'true';
      }
      renderAssignmentWorkerOptions();
      document.getElementById('total').textContent = data.stats.total_issues;
      document.getElementById('pending').textContent = data.stats.pending;
      document.getElementById('progress').textContent = data.stats.in_progress;
      document.getElementById('resolved').textContent = data.stats.resolved;
      document.getElementById('emTotal').textContent = data.stats.emergency_total ?? 0;
      document.getElementById('emResolved').textContent = data.stats.emergency_resolved ?? 0;
      document.getElementById('issueRows').innerHTML = data.recent_issues.map(item =>
        `<tr>
          <td>${item.complaint_number || '-'}</td>
          <td>${item.title || '-'}</td>
          <td>${item.location || '-'}</td>
          <td class="statusCell">
            <div class="statusMain">
              <div class="statusMeta">
                ${statusPill(item.status)}
                ${item.assigned_department ? `<span class="pill progress">${esc(item.assigned_department)}</span>` : ''}
              </div>
            </div>
            <div class="statusActions">
              ${item.worker_status_message ? `<div class="workerInline"><strong>${esc(item.worker_status_message)}</strong> ${statusPill(item.worker_status || '')}</div>` : '<div class="workerInline"><strong>Worker:</strong> <span style="color:#64748b;font-weight:600;">No update</span></div>'}
              <div class="statusActionRow">
                <select id="status_${item.id}">
                  <option ${item.status === 'Pending' ? 'selected' : ''}>Pending</option>
                  <option ${item.status === 'In Progress' ? 'selected' : ''}>In Progress</option>
                  <option ${item.status === 'Resolved' ? 'selected' : ''}>Resolved</option>
                  <option ${item.status === 'Rejected' ? 'selected' : ''}>Rejected</option>
                </select>
                <button onclick="updateIssueStatus(${item.id}, document.getElementById('status_${item.id}').value)">Update</button>
                <button class="iconBtn" title="Delete complaint" onclick="deleteComplaint(${item.id})">&#128465;</button>
              </div>
            </div>
          </td>
        </tr>`
      ).join('') || '<tr><td colspan="4">No complaints found</td></tr>';
      document.getElementById('alertRows').innerHTML = (data.recent_alerts || []).map((item, idx) =>
        `<tr>
          <td>${item.sender_name || '-'}</td>
          <td>${item.location || '-'}</td>
          <td><span class="pill danger">${item.severity || '-'}</span></td>
          <td>
            <select id="em_status_${idx}">
              <option ${item.status === 'Open' ? 'selected' : ''}>Open</option>
              <option ${item.status === 'In Progress' ? 'selected' : ''}>In Progress</option>
              <option ${item.status === 'Resolved' ? 'selected' : ''}>Resolved</option>
              <option ${item.status === 'Rejected' ? 'selected' : ''}>Rejected</option>
            </select>
            <button onclick="updateEmergencyStatus(${idx})">Update</button>
          </td>
          <td class="actionCell">
            <div class="actionWrap">
              <span class="actionLeft"><button onclick="viewEmergency(${idx})">Emergency</button></span>
              <button class="iconBtn" title="Delete emergency" onclick="deleteEmergency(${idx})">&#128465;</button>
            </div>
          </td>
        </tr>`
      ).join('') || '<tr><td colspan="5">No emergency alerts</td></tr>';
      document.getElementById('complaintRows').innerHTML = complaintStore.map((item, idx) =>
        `<tr>
          <td class="singleLine" title="${esc(item.user_name || '-')}">${esc(item.user_name || '-')}</td>
          <td class="singleLine" title="${esc(item.title || '-')}">${esc(item.title || '-')}</td>
          <td class="compactLocationWrap"><div class="compactLocation" title="${esc(item.location || '-')}">${esc(item.location || '-')}</div></td>
          <td class="actionCell complaintAction">
            <div class="actionWrap">
              <span class="actionLeft"><button onclick="viewComplaint(${idx})">View Complaint</button><button onclick="openAssignModal(${item.id})">Assign</button></span>
              <button class="iconBtn" title="Delete complaint" onclick="deleteComplaint(${item.id})">&#128465;</button>
            </div>
          </td>
        </tr>`
      ).join('') || '<tr><td colspan="4">No complaints reported</td></tr>';
      document.getElementById('userCards').innerHTML = data.users.map(user => `
        <article class="userCard">
          <div><strong>${user.full_name || 'Unknown User'}</strong> <span class="mono">#${user.id}</span></div>
          <div class="muted">${user.email || 'No email'} | ${user.phone || 'No phone'}</div>
          <div class="muted">Complaints: ${user.complaints.length} | Emergencies: ${user.emergency_alerts.length}</div>
          <details>
            <summary>View complaints</summary>
            ${(user.complaints || []).length ? user.complaints.map(c =>
              `<div class="mono">${c.complaint_number} | ${c.status} | ${c.location || '-'} | ${c.title || '-'}</div>`
            ).join('') : '<div class="muted">No complaints submitted</div>'}
          </details>
          <details>
            <summary>View emergencies</summary>
            ${(user.emergency_alerts || []).length ? user.emergency_alerts.map(a =>
              `<div class="mono">${a.created_at || ''} | ${a.sensor_label || '-'} | ${a.severity || '-'} | ${a.note || '-'}</div>`
            ).join('') : '<div class="muted">No emergency alerts</div>'}
          </details>
        </article>
      `).join('') || '<p class="muted">No users registered yet.</p>';
      document.getElementById('workerList').innerHTML = workerStore.map(worker => `
        <article class="userCard">
          <div style="display:flex;justify-content:space-between;align-items:center;gap:10px;flex-wrap:wrap;">
            <strong>${esc(worker.worker_id)}</strong>
            <span class="actionLeft">
              <button onclick="viewWorkerPassword(${worker.id})">View Password</button>
            </span>
          </div>
          <div class="muted">${esc(worker.department)} Department</div>
          <div class="muted">Created: ${esc(prettyDate(worker.created_at))} | Last login: ${esc(prettyDate(worker.last_login_at))}</div>
          <div class="muted">Department login page: <a href="/worker/login/${esc(worker.department_slug)}" target="_blank" rel="noopener noreferrer">/worker/login/${esc(worker.department_slug)}</a></div>
        </article>
      `).join('') || '<p class="muted">No workers created yet.</p>';
      document.getElementById('workerResetRequests').innerHTML = workerResetStore.map(item => `
        <article class="userCard">
          <div><strong>${esc(item.worker_id)}</strong> <span class="muted">${esc(item.department)}</span></div>
          <div class="muted">Requested: ${esc(prettyDate(item.requested_at))} | Status: ${esc(item.status)}</div>
          <div class="actionLeft">
            <button onclick="adminResetWorkerPassword(${item.worker_db_id})">Set New Password</button>
            <button class="iconBtn" title="Delete password reset request" onclick="deleteWorkerResetRequest(${item.id})">&#128465;</button>
          </div>
        </article>
      `).join('') || '<p class="muted">No worker password reset requests.</p>';
      document.getElementById('workerResolutionRequests').innerHTML = workerResolutionStore.map(item => `
        <article class="userCard">
          <div><strong>${esc(item.complaint_number)}</strong> <span class="muted">${esc(item.department || '-')}</span></div>
          <div class="muted">${esc(item.title || '-')}</div>
          <div class="muted">Worker marked resolved on: ${esc(prettyDate(item.requested_at))}</div>
          <div class="muted">Update the official complaint status from the complaints table after verification.</div>
        </article>
      `).join('') || '<p class="muted">No worker resolution notifications yet.</p>';
    }
    loadPanel();
    setInterval(loadPanel, 15000);
  
