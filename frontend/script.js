const API_BASE = '/api';

// Demo datasets required by prompt specifications
const DEMO_BUGS = {
  1: {
    title: "API returns HTTP 500 after deployment",
    description: "Production API started returning HTTP 500 immediately after the latest deployment.",
    environment: "Production",
    recent_change: "Database configuration was modified during deployment.",
    error_logs: "Database connection failed.",
    resolution: {
      title: "API returns HTTP 500 after deployment",
      root_cause: "Incorrect database configuration after deployment.",
      fix_applied: "Restored the correct database configuration.",
      result: "API recovered immediately.",
      lesson: "After deployment-related HTTP 500 errors, check database configuration and connection settings first."
    }
  },
  2: {
    title: "API returns HTTP 500 again after deployment",
    description: "Production API is returning HTTP 500 again immediately after deployment.",
    environment: "Production",
    recent_change: "Deployment configuration changed.",
    error_logs: "Internal server error.",
    resolution: {
      title: "API returns HTTP 500 again after deployment",
      root_cause: "Deployment script reverted DB credentials.",
      fix_applied: "Updated deployment pipeline variables and restored DB config.",
      result: "API recovered.",
      lesson: "Lock DB config values in CI/CD pipeline."
    }
  }
};

document.addEventListener('DOMContentLoaded', () => {
  checkHealth();
  // Default to Demo Bug 1 on load
  loadDemoBug(1);
});

async function checkHealth() {
  try {
    const res = await fetch(`${API_BASE}/health`);
    const data = await res.json();
    
    // Update AI status badge
    const aiBadge = document.getElementById('ai-badge');
    const aiText = document.getElementById('ai-status-text');
    if (data.gemini_connected) {
      aiBadge.className = 'badge badge-gemini';
      aiText.textContent = 'AI: Gemini Connected';
    } else {
      aiBadge.className = 'badge badge-demo';
      aiText.textContent = 'AI: Demo Mode';
    }

    // Update Hindsight status badge
    const hsBadge = document.getElementById('hindsight-badge');
    const hsText = document.getElementById('hindsight-status-text');
    if (data.hindsight_connected) {
      hsBadge.className = 'badge badge-hindsight-on';
      hsText.textContent = 'Hindsight: Connected';
    } else {
      hsBadge.className = 'badge badge-hindsight-off';
      hsText.textContent = 'Hindsight: Not Connected';
      hsBadge.title = 'Add HINDSIGHT_API_KEY to .env to enable real Hindsight memory retention and recall';
    }
  } catch (err) {
    console.error('Health check failed:', err);
    document.getElementById('ai-status-text').textContent = 'AI: Offline';
    document.getElementById('hindsight-status-text').textContent = 'Hindsight: Offline';
  }
}

function loadDemoBug(index) {
  const bug = DEMO_BUGS[index];
  if (!bug) return;

  document.getElementById('bug-title').value = bug.title;
  document.getElementById('bug-desc').value = bug.description;
  document.getElementById('bug-env').value = bug.environment;
  document.getElementById('bug-change').value = bug.recent_change;
  document.getElementById('bug-logs').value = bug.error_logs;

  if (bug.resolution) {
    document.getElementById('res-title').value = bug.resolution.title;
    document.getElementById('res-cause').value = bug.resolution.root_cause;
    document.getElementById('res-fix').value = bug.resolution.fix_applied;
    document.getElementById('res-result').value = bug.resolution.result;
    document.getElementById('res-lesson').value = bug.resolution.lesson;
  }

  // Clear previous resolve alerts
  hideAlert('resolve-alert');
}

function clearForm() {
  document.getElementById('investigate-form').reset();
  document.getElementById('resolve-form').reset();
  document.getElementById('bug-env').value = 'Production';
  document.getElementById('res-result').value = 'API recovered immediately.';
  
  document.getElementById('investigation-content').classList.add('hidden');
  document.getElementById('investigation-empty').classList.remove('hidden');
  hideAlert('resolve-alert');
}

async function handleInvestigate(event) {
  event.preventDefault();
  
  const payload = {
    title: document.getElementById('bug-title').value.trim(),
    description: document.getElementById('bug-desc').value.trim(),
    environment: document.getElementById('bug-env').value.trim(),
    recent_change: document.getElementById('bug-change').value.trim(),
    error_logs: document.getElementById('bug-logs').value.trim()
  };

  if (!payload.title) {
    alert('Please enter a bug title.');
    return;
  }

  // Show UI Loading states
  document.getElementById('investigation-empty').classList.add('hidden');
  document.getElementById('investigation-content').classList.add('hidden');
  document.getElementById('investigation-loading').classList.remove('hidden');

  try {
    const res = await fetch(`${API_BASE}/investigate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });

    if (!res.ok) {
      const errData = await res.json();
      throw new Error(errData.detail || 'Investigation failed');
    }

    const data = await res.json();
    renderInvestigationResult(data);

  } catch (err) {
    console.error(err);
    document.getElementById('investigation-loading').classList.add('hidden');
    document.getElementById('investigation-empty').classList.remove('hidden');
    alert(`Error: ${err.message}`);
  }
}

function renderInvestigationResult(data) {
  document.getElementById('investigation-loading').classList.add('hidden');
  document.getElementById('investigation-content').classList.remove('hidden');

  // Fill Investigation Result Card
  document.getElementById('rec-first-check').textContent = data.recommended_first_check || 'N/A';
  document.getElementById('rec-why').textContent = data.why_recommendation_made || '';
  document.getElementById('rec-probable-cause').textContent = data.probable_cause || 'N/A';
  document.getElementById('rec-confidence').textContent = data.confidence_explanation || 'N/A';

  // Render Steps
  const stepsList = document.getElementById('rec-steps');
  stepsList.innerHTML = '';
  if (data.investigation_steps && data.investigation_steps.length > 0) {
    data.investigation_steps.forEach(step => {
      const li = document.createElement('li');
      li.textContent = step;
      stepsList.appendChild(li);
    });
  }

  // Memory Influenced Tag
  const tag = document.getElementById('memory-influenced-tag');
  if (data.memory_influenced) {
    tag.className = 'tag tag-memory';
    tag.textContent = '🧠 Memory-Guided Recommendation';
  } else {
    tag.className = 'tag tag-neutral';
    tag.textContent = 'Standard Heuristic Analysis';
  }

  // Render Memory Used Panel
  renderMemoryPanel(data.memories_recalled, data.hindsight_status);
}

function renderMemoryPanel(memories, hindsightStatus) {
  const container = document.getElementById('memory-list');
  container.innerHTML = '';

  if (hindsightStatus === "Not Connected" && (!memories || memories.length === 0)) {
    container.innerHTML = `
      <div class="empty-state">
        <div class="empty-icon">🔌</div>
        <p><strong>Hindsight Memory Not Connected</strong></p>
        <p style="font-size: 11px; margin-top: 4px;">Add <code>HINDSIGHT_API_KEY</code> to <code>.env</code> to connect real persistent vector memory.</p>
      </div>
    `;
    return;
  }

  if (!memories || memories.length === 0) {
    container.innerHTML = `
      <div class="empty-state">
        <div class="empty-icon">💭</div>
        <p>No relevant previous experience found in Hindsight memory bank.</p>
      </div>
    `;
    return;
  }

  memories.forEach(mem => {
    const card = document.createElement('div');
    card.className = 'memory-card';
    card.innerHTML = `
      <div class="memory-header">
        <div class="memory-title">Incident: ${escapeHtml(mem.incident)}</div>
        <span class="memory-tag">🧠 Previous Experience</span>
      </div>
      <div class="memory-field"><strong>Root Cause:</strong> ${escapeHtml(mem.root_cause)}</div>
      <div class="memory-field"><strong>Fix Applied:</strong> ${escapeHtml(mem.fix)}</div>
      ${mem.context ? `<div class="memory-field"><strong>Lesson / Context:</strong> ${escapeHtml(mem.context)}</div>` : ''}
    `;
    container.appendChild(card);
  });
}

async function handleResolve(event) {
  event.preventDefault();

  const payload = {
    bug_title: document.getElementById('res-title').value.trim(),
    root_cause: document.getElementById('res-cause').value.trim(),
    fix_applied: document.getElementById('res-fix').value.trim(),
    result: document.getElementById('res-result').value.trim(),
    additional_lesson: document.getElementById('res-lesson').value.trim()
  };

  if (!payload.bug_title || !payload.root_cause || !payload.fix_applied) {
    alert('Please fill out Bug Title, Root Cause, and Fix Applied.');
    return;
  }

  try {
    const res = await fetch(`${API_BASE}/resolve`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });

    const data = await res.json();
    if (res.ok && data.success) {
      showAlert('resolve-alert', 'alert-success', data.message || '✓ Bug experience saved to Hindsight memory!');
    } else {
      showAlert('resolve-alert', 'alert-error', data.message || 'Failed to save resolution to memory.');
    }
  } catch (err) {
    console.error(err);
    showAlert('resolve-alert', 'alert-error', `Error saving resolution: ${err.message}`);
  }
}

function showAlert(elementId, alertClass, text) {
  const el = document.getElementById(elementId);
  el.className = `alert ${alertClass}`;
  el.textContent = text;
  el.classList.remove('hidden');
}

function hideAlert(elementId) {
  const el = document.getElementById(elementId);
  el.classList.add('hidden');
}

function escapeHtml(str) {
  if (!str) return '';
  return str.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;").replace(/'/g, "&#039;");
}
