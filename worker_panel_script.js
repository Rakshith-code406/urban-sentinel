
    function statusPill(status) {
      const key = (status || '').toLowerCase();
      if (key === 'resolved') return '<span class="pill resolved">Resolved</span>';
      if (key === 'in progress') return '<span class="pill progress">In Progress</span>';
      return '<span class="pill pending">' + (status || 'Pending') + '</span>';
    }
    let workerIssueStore = [];
    function closeWorkerComplaintModal(event) {
      if (event && event.target && event.target.id !== 'workerComplaintModal') return;
      const modal = document.getElementById('workerComplaintModal');
      if (modal) modal.classList.remove('show');
    }
    function viewWorkerComplaint(issueId) {
      const item = workerIssueStore.find(row => row.id === issueId);
      if (!item) return;
      const body = document.getElementById('workerComplaintBody');
      const imageBlock = (item.media_urls || []).length
        ? `<div class="thumbGrid">${item.media_urls.map(src => `<a href="${src}" target="_blank" rel="noopener noreferrer"><img src="${src}" alt="Complaint image" /></a>`).join('')}</div>`
        : '<p class="muted">No uploaded images for this complaint.</p>';
      body.innerHTML = `
        <div class="mono" style="margin-bottom:8px;">${item.complaint_number || '-'}</div>
        <p><strong>Issue:</strong> ${item.title || '-'}</p>
        <p><strong>Description:</strong> ${item.description || '-'}</p>
        <p><strong>Location:</strong> ${item.location || '-'}</p>
        <p><strong>Category:</strong> ${item.category || '-'}</p>
        <p><strong>Admin Status:</strong> ${item.status || '-'}</p>
        <p><strong>Worker Status:</strong> ${item.worker_status || 'Assigned'}</p>
        <p><strong>Deadline:</strong> ${item.assignment_duration_label || '-'}${item.assignment_deadline ? ' | ' + new Date(item.assignment_deadline).toLocaleString() : ''}</p>
        <h4 style="margin:12px 0 8px;">Uploaded Images</h4>
        ${imageBlock}
      `;
      document.getElementById('workerComplaintModal').classList.add('show');
    }
    async function updateWorkerComplaintStatus(issueId) {
      const picker = document.getElementById('worker_status_' + issueId);
      if (!picker) return;
      const nextStatus = picker.value;
      const res = await fetch('/worker/issues/' + issueId + '/status', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ status: nextStatus })
      });
      const payload = await res.json().catch(() => ({}));
      if (!res.ok) {
        alert(payload.detail || 'Unable to update worker status');
        return;
      }
      alert(payload.message || 'Worker status updated');
      loadWorkerPanel();
    }
    async function loadWorkerPanel() {
      const res = await fetch('/worker/panel-data');
      if (!res.ok) { window.location.href = '/worker'; return; }
      const data = await res.json();
      const rows = data.assigned_issues || [];
      workerIssueStore = rows;
      document.getElementById('workerMeta').textContent = data.worker.worker_id + ' | ' + data.worker.department + ' Department';
      document.getElementById('assignedCount').textContent = rows.length;
      document.getElementById('pendingCount').textContent = rows.filter(item => item.status !== 'Resolved' && item.status !== 'Rejected').length;
      document.getElementById('deadlineCount').textContent = rows.filter(item => item.assignment_deadline).length;
      document.getElementById('workerRows').innerHTML = rows.map(item => `
        <tr>
          <td>${item.complaint_number || '-'}</td>
          <td>${item.title || '-'}</td>
          <td>${item.location || '-'}</td>
          <td>
            ${statusPill(item.status)}
            <div style="margin-top:6px;">Worker: ${statusPill(item.worker_status || 'Assigned')}</div>
          </td>
          <td>${item.assignment_duration_label || '-'}${item.assignment_deadline ? ' | ' + new Date(item.assignment_deadline).toLocaleString() : ''}</td>
          <td>
            <div class="actionLeft">
              <button type="button" onclick="viewWorkerComplaint(${item.id})">View</button>
              <select id="worker_status_${item.id}">
                <option ${(item.worker_status || 'Assigned') === 'Assigned' ? 'selected' : ''}>Assigned</option>
                <option ${(item.worker_status || 'Assigned') === 'In Progress' ? 'selected' : ''}>In Progress</option>
                <option ${(item.worker_status || 'Assigned') === 'Resolved' ? 'selected' : ''}>Resolved</option>
              </select>
              <button type="button" onclick="updateWorkerComplaintStatus(${item.id})">Update</button>
            </div>
          </td>
        </tr>
      `).join('') || '<tr><td colspan="6">No complaints assigned to your department yet.</td></tr>';
    }
    loadWorkerPanel();
    setInterval(loadWorkerPanel, 20000);
  