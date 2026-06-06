/* ============================================================
   Splunk Zero — Application Logic
   Handles SSE streaming, event rendering, and UI state
   ============================================================ */

const BASE_URL = window.location.origin;
let currentRunId = null;
let eventSource = null;

// ── Pipeline step mapping ─────────────────────────────────
const STEP_MAP = {
    'triggered':        null,
    'querying_ingest':  'ingest_analysis',
    'ingest_complete':  'ingest_analysis',
    'ingest_error':     'ingest_analysis',
    'querying_audit':   'search_audit',
    'audit_complete':   'search_audit',
    'audit_error':      'search_audit',
    'detecting_waste':  'waste_detection',
    'waste_found':      'waste_detection',
    'no_waste':         'waste_detection',
    'tracing_source':   'source_tracing',
    'source_traced':    'source_tracing',
    'source_trace_failed': 'source_tracing',
    'tracing_complete': 'source_tracing',
    'analyzing_code':   'code_analysis',
    'reading_config':   'code_analysis',
    'change_proposed':  'code_analysis',
    'analysis_error':   'code_analysis',
    'analysis_complete':'code_analysis',
    'creating_pr':      'pr_creation',
    'creating_branch':  'pr_creation',
    'pr_created':       'pr_creation',
    'pr_error':         'pr_creation',
    'prs_complete':     'pr_creation',
    'complete':         'report',
    'done':             'report',
    'error':            null,
};

// Steps in order — used to mark previous steps as complete
const STEP_ORDER = [
    'ingest_analysis',
    'search_audit',
    'waste_detection',
    'source_tracing',
    'code_analysis',
    'pr_creation',
    'report',
];

// ── Initialization ────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
    checkHealth();
    // Auto-refresh health every 30s
    setInterval(checkHealth, 30000);
});

// ── Health Check ──────────────────────────────────────────
async function checkHealth() {
    const indicator = document.getElementById('serverStatus');
    try {
        const res = await fetch(`${BASE_URL}/health`);
        const data = await res.json();

        if (data.status === 'healthy') {
            indicator.className = 'status-indicator healthy';
            const version = data.splunk?.version || '?';
            indicator.querySelector('span').textContent = `Splunk v${version} Connected`;
        } else {
            indicator.className = 'status-indicator error';
            indicator.querySelector('span').textContent = 'Config Issues';
        }
    } catch (e) {
        indicator.className = 'status-indicator error';
        indicator.querySelector('span').textContent = 'Server Offline';
    }
}

// ── Trigger Run ───────────────────────────────────────────
async function triggerRun() {
    const btn = document.getElementById('triggerBtn');
    if (btn.classList.contains('running')) return;

    // Close any existing SSE connection
    if (eventSource) {
        eventSource.close();
        eventSource = null;
    }

    // Update button state
    btn.classList.add('running');
    btn.querySelector('.btn-label').textContent = 'Running Investigation...';
    btn.querySelector('.btn-icon').innerHTML = `
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="12" cy="12" r="10"/>
            <path d="M12 6v6l4 2"/>
        </svg>
    `;

    // Reset UI
    resetUI();

    try {
        const res = await fetch(`${BASE_URL}/trigger`, { method: 'POST' });
        const data = await res.json();
        currentRunId = data.run_id;

        // Show run ID badge
        const badge = document.getElementById('runIdBadge');
        badge.style.display = 'block';
        document.getElementById('runIdText').textContent = `run:${currentRunId}`;

        // Show pipeline progress
        document.getElementById('pipelineProgress').style.display = 'block';

        // Connect to SSE stream
        connectSSE(currentRunId);

    } catch (e) {
        addEventCard({
            step: 'error',
            title: 'Failed to Start',
            detail: `Could not connect to server: ${e.message}`,
            status: 'error',
            timestamp: new Date().toISOString(),
        });
        resetButton();
    }
}

// ── SSE Connection ────────────────────────────────────────
function connectSSE(runId) {
    eventSource = new EventSource(`${BASE_URL}/events/${runId}`);

    eventSource.onmessage = (event) => {
        try {
            // Handle the double "data: " prefix from sse-starlette
            let jsonStr = event.data;
            if (jsonStr.startsWith('data: ')) {
                jsonStr = jsonStr.substring(6);
            }

            const data = JSON.parse(jsonStr);
            handleEvent(data);
        } catch (e) {
            // Ignore parse errors (ping events, etc.)
        }
    };

    eventSource.onerror = () => {
        // SSE connection closed (normal after stream ends)
        if (eventSource) {
            eventSource.close();
            eventSource = null;
        }
    };
}

// ── Event Handler ─────────────────────────────────────────
function handleEvent(event) {
    const { step, title, detail, status, data, timestamp } = event;

    // Update pipeline progress
    updatePipelineStep(step, status);

    // Update stats based on event data
    updateStats(step, data);

    // Add event card to stream
    addEventCard(event);

    // Handle stream completion
    if (step === 'done') {
        if (eventSource) {
            eventSource.close();
            eventSource = null;
        }
        resetButton();
        markPipelineComplete();
    }
}

// ── Pipeline Step Updates ─────────────────────────────────
function updatePipelineStep(step, status) {
    const mappedStep = STEP_MAP[step];
    if (!mappedStep) return;

    const stepIdx = STEP_ORDER.indexOf(mappedStep);
    if (stepIdx === -1) return;

    // Mark all previous steps as complete
    for (let i = 0; i < stepIdx; i++) {
        const el = document.querySelector(`.step[data-step="${STEP_ORDER[i]}"]`);
        if (el && !el.classList.contains('error')) {
            el.className = 'step complete';
        }
    }

    // Mark current step
    const currentEl = document.querySelector(`.step[data-step="${mappedStep}"]`);
    if (currentEl) {
        if (status === 'error') {
            currentEl.className = 'step error';
        } else if (status === 'complete' && (step.endsWith('_complete') || step === 'complete' || step === 'done')) {
            currentEl.className = 'step complete';
        } else {
            currentEl.className = 'step active';
        }
    }
}

function markPipelineComplete() {
    STEP_ORDER.forEach(stepName => {
        const el = document.querySelector(`.step[data-step="${stepName}"]`);
        if (el && !el.classList.contains('error')) {
            el.className = 'step complete';
        }
    });
}

// ── Stats Updates ─────────────────────────────────────────
function updateStats(step, data) {
    if (!data) return;

    if (data.sourcetype_count !== undefined) {
        updateStatCard('statSources', data.sourcetype_count);
    }

    if (data.wasteful_count !== undefined) {
        updateStatCard('statWaste', data.wasteful_count, 'highlight-red');
    }

    if (data.total_monthly_savings !== undefined) {
        const formatted = '$' + data.total_monthly_savings.toLocaleString('en-US', { 
            minimumFractionDigits: 0, 
            maximumFractionDigits: 0 
        });
        updateStatCard('statSavings', formatted, 'highlight');
    }

    if (data.prs_created !== undefined) {
        updateStatCard('statPRs', data.prs_created, 'highlight');
    }
}

function updateStatCard(id, value, highlightClass) {
    const card = document.getElementById(id);
    if (!card) return;

    const valueEl = card.querySelector('.stat-value');

    // Check if this is a dollar value for countup animation
    if (typeof value === 'string' && value.startsWith('$')) {
        const target = parseFloat(value.replace(/[$,]/g, ''));
        animateCountUp(valueEl, 0, target, 1200, v => '$' + v.toLocaleString('en-US', { minimumFractionDigits: 0, maximumFractionDigits: 0 }));
    } else {
        valueEl.textContent = value;
    }

    if (highlightClass) {
        card.classList.add(highlightClass);
    }

    // Animate the update
    card.style.transform = 'scale(1.05)';
    valueEl.classList.add('counting');
    setTimeout(() => {
        card.style.transform = 'scale(1)';
    }, 200);
    setTimeout(() => {
        valueEl.classList.remove('counting');
    }, 800);
}

function animateCountUp(element, start, end, duration, formatter) {
    const startTime = performance.now();
    const diff = end - start;

    function update(currentTime) {
        const elapsed = currentTime - startTime;
        const progress = Math.min(elapsed / duration, 1);
        // Ease out cubic
        const eased = 1 - Math.pow(1 - progress, 3);
        const current = start + diff * eased;
        element.textContent = formatter(current);

        if (progress < 1) {
            requestAnimationFrame(update);
        }
    }

    requestAnimationFrame(update);
}

// ── Event Card Rendering ──────────────────────────────────
function addEventCard(event) {
    const { step, title, detail, status, data, timestamp } = event;

    // Remove empty state
    const emptyState = document.getElementById('emptyState');
    if (emptyState) emptyState.remove();

    const stream = document.getElementById('eventStream');
    const card = document.createElement('div');

    // Check if this is the final report
    if (step === 'complete' && data?.total_monthly_savings) {
        card.className = `event-card final-report`;
        card.innerHTML = renderFinalReport(event);
    } else {
        card.className = `event-card status-${status}`;
        card.innerHTML = renderEventCard(event);
    }

    stream.appendChild(card);

    // Auto-scroll to bottom
    requestAnimationFrame(() => {
        stream.scrollTop = stream.scrollHeight;
    });
}

function renderEventCard(event) {
    const { step, title, detail, status, data, timestamp } = event;
    const time = timestamp ? new Date(timestamp).toLocaleTimeString() : '';

    let extraHTML = '';

    // PR link
    if (data?.pr_url) {
        extraHTML += `
            <a href="${data.pr_url}" target="_blank" rel="noopener" class="event-pr-link">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M18 13v6a2 2 0 01-2 2H5a2 2 0 01-2-2V8a2 2 0 012-2h6"/>
                    <polyline points="15 3 21 3 21 9"/>
                    <line x1="10" y1="14" x2="21" y2="3"/>
                </svg>
                PR #${data.pr_number}: ${data.title || 'View PR'}
            </a>
        `;
    }

    // Savings highlight + waste table
    if (data?.total_monthly_savings && step === 'waste_found') {
        const annual = data.total_monthly_savings * 12;
        extraHTML += `
            <div style="margin-top: 8px;">
                <span class="event-savings">$${data.total_monthly_savings.toLocaleString()}/month</span>
                <span style="font-size: 0.7rem; color: var(--text-muted); margin-left: 8px;">
                    ($${annual.toLocaleString()}/year)
                </span>
            </div>
        `;

        // Add waste table showing top sources
        if (data.wasteful_sources && data.wasteful_sources.length > 0) {
            const topSources = data.wasteful_sources.slice(0, 5);
            extraHTML += `
                <table class="waste-table">
                    <tr><th>Sourcetype</th><th>GB/day</th><th>Searches</th><th>Savings</th></tr>
                    ${topSources.map(s => `
                        <tr>
                            <td>${escapeHtml(s.sourcetype)}</td>
                            <td>${s.daily_gb.toFixed(2)}</td>
                            <td>${s.search_count_30d}</td>
                            <td>$${s.est_monthly_cost.toLocaleString()}/mo</td>
                        </tr>
                    `).join('')}
                    ${data.wasteful_sources.length > 5 ? `<tr><td colspan="4" style="color: var(--text-muted); font-style: italic;">...and ${data.wasteful_sources.length - 5} more</td></tr>` : ''}
                </table>
            `;
        }
    }

    return `
        <div class="event-card-header">
            <span class="event-title">${escapeHtml(title)}</span>
            <span class="event-badge ${status}">${status}</span>
        </div>
        ${detail ? `<div class="event-detail">${escapeHtml(detail)}</div>` : ''}
        ${extraHTML}
        <div class="event-timestamp">${time}</div>
    `;
}

function renderFinalReport(event) {
    const { data } = event;
    const savings = data.total_monthly_savings || 0;
    const annual = data.total_annual_savings || savings * 12;

    return `
        <div class="event-card-header">
            <span class="event-title">Investigation Complete</span>
            <span class="event-badge complete">DONE</span>
        </div>
        <div class="event-detail">${escapeHtml(data.summary || event.detail || '')}</div>
        <div class="report-grid">
            <div class="report-item">
                <span class="report-item-label">Sources Analyzed</span>
                <span class="report-item-value">${data.sources_analyzed || '--'}</span>
            </div>
            <div class="report-item">
                <span class="report-item-label">Waste Found</span>
                <span class="report-item-value">${data.wasteful_sources_count || '--'}</span>
            </div>
            <div class="report-item">
                <span class="report-item-label">PRs Created</span>
                <span class="report-item-value">${data.prs_created || 0}</span>
            </div>
            <div class="report-item">
                <span class="report-item-label">Monthly Savings</span>
                <span class="report-item-value" style="color: var(--accent-green);">$${savings.toLocaleString()}</span>
            </div>
        </div>
        ${data.pr_urls && data.pr_urls.length > 0 ? `
            <div style="margin-top: 12px;">
                ${data.pr_urls.map((url, i) => `
                    <a href="${url}" target="_blank" rel="noopener" class="event-pr-link" style="margin-right: 8px; margin-bottom: 4px;">
                        PR #${i + 1}
                    </a>
                `).join('')}
            </div>
        ` : ''}
        <div class="event-timestamp">${new Date(data.timestamp).toLocaleTimeString()}</div>
    `;
}

// ── Utilities ─────────────────────────────────────────────
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function resetUI() {
    // Clear event stream
    const stream = document.getElementById('eventStream');
    stream.innerHTML = '';

    // Reset stats
    document.querySelectorAll('.stat-value').forEach(el => el.textContent = '--');
    document.querySelectorAll('.stat-card').forEach(el => {
        el.classList.remove('highlight', 'highlight-red');
    });

    // Reset pipeline steps
    document.querySelectorAll('.step').forEach(el => {
        el.className = 'step';
    });
}

function resetButton() {
    const btn = document.getElementById('triggerBtn');
    btn.classList.remove('running');
    btn.querySelector('.btn-label').textContent = 'Start Investigation';
    btn.querySelector('.btn-icon').innerHTML = `
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polygon points="5 3 19 12 5 21 5 3"/>
        </svg>
    `;
}

// ── Demo Reset ────────────────────────────────────────────
async function resetDemo() {
    const btn = document.getElementById('resetBtn');
    btn.classList.add('resetting');
    btn.textContent = 'Resetting...';

    try {
        const res = await fetch(`${BASE_URL}/reset-demo`, { method: 'POST' });
        const data = await res.json();

        if (data.status === 'success') {
            btn.textContent = 'Reset Complete!';
            btn.style.borderColor = 'rgba(0, 255, 136, 0.3)';
            btn.style.color = 'var(--accent-green)';
        } else {
            btn.textContent = 'Reset Failed';
            btn.style.borderColor = 'rgba(255, 68, 102, 0.3)';
            btn.style.color = 'var(--accent-red)';
        }
    } catch (e) {
        btn.textContent = 'Error';
        btn.style.color = 'var(--accent-red)';
    }

    setTimeout(() => {
        btn.classList.remove('resetting');
        btn.innerHTML = `
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M1 4v6h6"/><path d="M3.51 15a9 9 0 102.13-9.36L1 10"/>
            </svg>
            Reset Demo
        `;
        btn.style.borderColor = '';
        btn.style.color = '';
    }, 2000);
}
