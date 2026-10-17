let selectedFile = null;
let currentResults = null;
const dropZone = document.getElementById('drop-zone');
const fileInput = document.getElementById('file-input');

dropZone.addEventListener('click', () => fileInput.click());
dropZone.addEventListener('dragover', (e) => {
  e.preventDefault();
  dropZone.classList.add('dragover');
});
dropZone.addEventListener('dragleave', () => dropZone.classList.remove('dragover'));
dropZone.addEventListener('drop', (e) => {
  e.preventDefault();
  dropZone.classList.remove('dragover');
  if (e.dataTransfer.files.length) handleFile(e.dataTransfer.files[0]);
});
fileInput.addEventListener('change', () => {
  if (fileInput.files.length) handleFile(fileInput.files[0]);
});

function handleFile(file) {
  if (!file.name.toLowerCase().endsWith('.pdf')) {
    alert('Please select a valid PDF file.');
    return;
  }
  if (file.size > 25 * 1024 * 1024) {
    alert('File size exceeds the 25 MB limit.');
    return;
  }
  selectedFile = file;
  document.getElementById('selected-name').textContent = file.name;
  document.getElementById('selected-size').textContent = (file.size / (1024 * 1024)).toFixed(2) + ' MB';
  document.getElementById('file-details').classList.remove('hidden');
  document.getElementById('start-btn').disabled = false;
}

function switchTab(tab) {
  document.getElementById('tab-scan').classList.toggle('active', tab === 'scan');
  document.getElementById('tab-tests').classList.toggle('active', tab === 'tests');
  document.getElementById('view-scan').classList.toggle('hidden', tab !== 'scan');
  document.getElementById('view-tests').classList.toggle('hidden', tab !== 'tests');
}

async function startScan() {
  if (!selectedFile) return;
  document.getElementById('start-btn').disabled = true;
  document.getElementById('progress-card').classList.remove('hidden');
  document.getElementById('results-card').classList.add('hidden');
  document.getElementById('progress-status').textContent = 'Uploading and validating PDF...';

  const formData = new FormData();
  formData.append('file', selectedFile);

  try {
    const res = await fetch('/api/scans/pdf', { method: 'POST', body: formData });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.message || 'Upload failed');
    }
    const data = await res.json();
    document.getElementById('progress-scan-id').textContent = data.scan_id;
    pollStatus(data.scan_id);
  } catch (err) {
    alert('Scan submission failed: ' + err.message);
    document.getElementById('progress-card').classList.add('hidden');
    document.getElementById('start-btn').disabled = false;
  }
}

async function pollStatus(scanId) {
  document.getElementById('progress-status').textContent = 'Analyzing accessibility criteria...';
  const interval = setInterval(async () => {
    try {
      const res = await fetch(`/api/scans/${scanId}/status`);
      const data = await res.json();
      document.getElementById('progress-status').textContent = 'Status: ' + data.status;

      if (data.status === 'COMPLETED') {
        clearInterval(interval);
        fetchResults(scanId);
      } else if (data.status === 'REJECTED') {
        clearInterval(interval);
        alert('Scan was rejected: ' + (data.error || 'Corrupted or unreadable PDF'));
        document.getElementById('progress-card').classList.add('hidden');
        document.getElementById('start-btn').disabled = false;
      }
    } catch (err) {
      clearInterval(interval);
      alert('Error polling scan status: ' + err.message);
      document.getElementById('start-btn').disabled = false;
    }
  }, 1000);
}

async function fetchResults(scanId) {
  try {
    const res = await fetch(`/api/scans/${scanId}/results`);
    currentResults = await res.json();
    renderResults(currentResults);
    document.getElementById('progress-card').classList.add('hidden');
    document.getElementById('results-card').classList.remove('hidden');
    document.getElementById('start-btn').disabled = false;
  } catch (err) {
    alert('Failed fetching results: ' + err.message);
  }
}

function escapeHTML(str) {
  if (str === null || str === undefined) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}

function renderResults(res) {
  document.getElementById('res-file').textContent = res.file_or_url;
  document.getElementById('metric-pages').textContent = res.pages;
  document.getElementById('metric-checks').textContent = res.summary.checks;
  document.getElementById('metric-passed').textContent = res.summary.passed;
  document.getElementById('metric-issues').textContent = res.summary.issues;
  document.getElementById('metric-review').textContent = res.summary.human_review;

  const tbody = document.getElementById('findings-tbody');
  tbody.innerHTML = '';
  res.findings.forEach(f => {
    const tr = document.createElement('tr');
    let badgeClass = 'badge-pass';
    if (f.status === 'Issue') badgeClass = 'badge-issue';
    else if (f.status === 'Needs Human Review') badgeClass = 'badge-review';

    const findingId = escapeHTML(f.finding_id);
    const location = escapeHTML(f.input_location);
    const wcag = escapeHTML(f.WCAG_criterion);
    const status = escapeHTML(f.status);
    const desc = escapeHTML(f.issue_description);
    const rem = f.remediation_guidance ? escapeHTML(f.remediation_guidance) : '';

    tr.innerHTML = `
      <td><strong>${findingId}</strong></td>
      <td>${location}</td>
      <td><span style="font-size: 0.8rem; color: var(--text-muted);">${wcag}</span></td>
      <td><span class="status-badge ${badgeClass}">${status}</span></td>
      <td>
        <div>${desc}</div>
        ${rem ? `<div style="font-size: 0.8rem; color: #475569; margin-top: 0.25rem;"><em>Remediation:</em> ${rem}</div>` : ''}
      </td>
    `;
    tbody.appendChild(tr);
  });
}

function downloadJSON() {
  if (!currentResults) return;
  const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(currentResults, null, 4));
  const a = document.createElement('a');
  a.href = dataStr;
  a.download = `${currentResults.file_or_url.replace(/\.pdf$/i, '')}_accessibility_report.json`;
  a.click();
}

async function runAutomatedTests() {
  const btn = document.getElementById('run-tests-btn');
  btn.disabled = true;
  btn.textContent = 'Running tests...';
  const tbody = document.getElementById('tests-tbody');
  tbody.innerHTML = '<tr><td colspan="5" style="text-align: center;"><span class="spinner"></span> Executing test fixtures...</td></tr>';

  try {
    const res = await fetch('/api/test-runner', { method: 'POST' });
    const summary = await res.json();

    document.getElementById('test-metric-total').textContent = summary.total;
    document.getElementById('test-metric-passed').textContent = summary.passed;
    document.getElementById('test-metric-failed').textContent = summary.failed;
    document.getElementById('tests-summary-box').classList.remove('hidden');

    tbody.innerHTML = '';
    summary.results.forEach((r, idx) => {
      const tr = document.createElement('tr');
      const badge = r.passed ? '<span class="status-badge badge-pass">PASS</span>' : '<span class="status-badge badge-issue">FAIL</span>';
      const name = escapeHTML(r.name);
      const reqRef = escapeHTML(r.requirement_ref || 'N/A');
      const details = escapeHTML(r.details);
      tr.innerHTML = `
        <td>${idx + 1}</td>
        <td>${badge}</td>
        <td><strong>${name}</strong></td>
        <td><span style="font-size: 0.8rem; color: var(--text-muted);">${reqRef}</span></td>
        <td>${details}</td>
      `;
      tbody.appendChild(tr);
    });
  } catch (err) {
    alert('Test runner error: ' + err.message);
  } finally {
    btn.disabled = false;
    btn.textContent = 'Run Acceptance Tests';
  }
}
