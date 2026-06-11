/* ============================================================
   SPLUNK ZERO — Premium App Logic
   Particle canvas · smooth animations · SSE pipeline
   ============================================================ */

const BASE_URL = window.location.origin;

let currentRunId = null;
let eventSource  = null;

// ── STEP MAP ─────────────────────────────────────────────────
const STEP_MAP = {
  triggered:           null,
  querying_ingest:     "ingest_analysis",
  ingest_complete:     "ingest_analysis",
  ingest_error:        "ingest_analysis",
  mcp_tools_ready:     "ingest_analysis",
  mcp_tool_called:     null,
  querying_audit:      "search_audit",
  audit_complete:      "search_audit",
  audit_error:         "search_audit",
  detecting_waste:     "waste_detection",
  waste_found:         "waste_detection",
  no_waste:            "waste_detection",
  tracing_source:      "source_tracing",
  source_traced:       "source_tracing",
  source_trace_failed: "source_tracing",
  tracing_complete:    "source_tracing",
  analyzing_code:      "code_analysis",
  reading_config:      "code_analysis",
  change_proposed:     "code_analysis",
  analysis_error:      "code_analysis",
  analysis_complete:   "code_analysis",
  creating_pr:         "pr_creation",
  creating_branch:     "pr_creation",
  pr_created:          "pr_creation",
  pr_error:            "pr_creation",
  prs_complete:        "pr_creation",
  complete:            "report",
  done:                "report",
  error:               null,
};

const STEP_ORDER = [
  "ingest_analysis",
  "search_audit",
  "waste_detection",
  "source_tracing",
  "code_analysis",
  "pr_creation",
  "report",
];

// ── PARTICLE CANVAS ───────────────────────────────────────────
(function initParticles() {
  const canvas = document.getElementById("particleCanvas");
  if (!canvas) return;
  const ctx = canvas.getContext("2d");

  let W = 0, H = 0;
  const particles = [];
  const PARTICLE_COUNT = 55;

  const COLORS = [
    "rgba(63,240,138,",
    "rgba(34,211,238,",
    "rgba(96,165,250,",
  ];

  function resize() {
    W = canvas.width  = window.innerWidth;
    H = canvas.height = window.innerHeight;
  }

  function createParticle() {
    return {
      x:     Math.random() * W,
      y:     Math.random() * H,
      r:     Math.random() * 1.4 + 0.4,
      vx:    (Math.random() - 0.5) * 0.3,
      vy:    (Math.random() - 0.5) * 0.3,
      color: COLORS[Math.floor(Math.random() * COLORS.length)],
      alpha: Math.random() * 0.5 + 0.1,
    };
  }

  window.addEventListener("resize", resize);
  resize();

  for (let i = 0; i < PARTICLE_COUNT; i++) {
    particles.push(createParticle());
  }

  function drawConnections() {
    for (let i = 0; i < particles.length; i++) {
      for (let j = i + 1; j < particles.length; j++) {
        const p1 = particles[i], p2 = particles[j];
        const dx = p1.x - p2.x, dy = p1.y - p2.y;
        const dist = Math.sqrt(dx * dx + dy * dy);
        if (dist < 140) {
          const alpha = (1 - dist / 140) * 0.08;
          ctx.beginPath();
          ctx.moveTo(p1.x, p1.y);
          ctx.lineTo(p2.x, p2.y);
          ctx.strokeStyle = `rgba(63,240,138,${alpha})`;
          ctx.lineWidth = 0.5;
          ctx.stroke();
        }
      }
    }
  }

  function loop() {
    ctx.clearRect(0, 0, W, H);
    drawConnections();
    particles.forEach(p => {
      p.x += p.vx;
      p.y += p.vy;
      if (p.x < 0 || p.x > W) p.vx *= -1;
      if (p.y < 0 || p.y > H) p.vy *= -1;
      ctx.beginPath();
      ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
      ctx.fillStyle = p.color + p.alpha + ")";
      ctx.fill();
    });
    requestAnimationFrame(loop);
  }

  loop();
})();

// ── HEALTH CHECK ──────────────────────────────────────────────
document.addEventListener("DOMContentLoaded", () => {
  checkHealth();
  setInterval(checkHealth, 30000);
});

async function checkHealth() {
  const serverPill = document.getElementById("serverStatus");
  const mcpPill    = document.getElementById("mcpStatus");

  try {
    const res  = await fetch(`${BASE_URL}/health`);
    const data = await res.json();

    if (data.status === "healthy" && data.splunk?.status === "healthy") {
      setPill(serverPill, "healthy", `Splunk ${data.splunk.version || ""}`.trim() || "Splunk");
    } else if (data.status === "healthy") {
      setPill(serverPill, "healthy", "Server Ready");
    } else {
      setPill(serverPill, "error", "Config Issue");
    }

    if (mcpPill && data.mcp) {
      const mcp = data.mcp;
      if (mcp.mcp_connected) {
        setPill(mcpPill, "healthy", `MCP · ${mcp.tool_count} tools`);
      } else {
        setPill(mcpPill, "warn", `MCP · REST (${mcp.tool_count})`);
      }
    }
  } catch {
    setPill(serverPill, "error", "Offline");
    if (mcpPill) setPill(mcpPill, "error", "MCP · unknown");
  }
}

function setPill(el, state, text) {
  el.className = `pill ${state}`;
  el.querySelector("span:last-child").textContent = text;
}

// ── TRIGGER RUN ───────────────────────────────────────────────
async function triggerRun() {
  const btn = document.getElementById("triggerBtn");
  if (btn.classList.contains("running")) return;

  if (eventSource) { eventSource.close(); eventSource = null; }

  btn.classList.add("running");
  setTriggerState("running");
  setStreamState("Connecting");
  resetUI();

  try {
    const res  = await fetch(`${BASE_URL}/trigger`, { method: "POST" });
    const data = await res.json();
    currentRunId = data.run_id;

    document.getElementById("runIdBadge").style.display       = "inline-flex";
    document.getElementById("runIdText").textContent           = `run:${currentRunId}`;
    document.getElementById("runIdPlaceholder").style.display  = "none";

    connectSSE(currentRunId);
  } catch (err) {
    addEventCard({
      step:      "error",
      title:     "Failed To Start",
      detail:    `Could not start the pipeline: ${err.message}`,
      status:    "error",
      timestamp: new Date().toISOString(),
    });
    setStreamState("Error");
    resetButton();
  }
}

function connectSSE(runId) {
  setStreamState("Streaming");
  eventSource = new EventSource(`${BASE_URL}/events/${runId}`);

  eventSource.onmessage = (event) => {
    try {
      let jsonStr = event.data;
      if (jsonStr.startsWith("data: ")) jsonStr = jsonStr.substring(6);
      handleEvent(JSON.parse(jsonStr));
    } catch {
      // ignore ping / malformed frames
    }
  };

  eventSource.onerror = () => {
    if (eventSource) { eventSource.close(); eventSource = null; }
  };
}

function handleEvent(event) {
  if (event.step === "done") {
    if (eventSource) { eventSource.close(); eventSource = null; }
    resetButton();
    markPipelineComplete();
    setStreamState("Complete");
    return;
  }
  updatePipelineStep(event.step, event.status);
  updateStats(event.step, event.data);
  addEventCard(event);
}

// ── PIPELINE STEP UPDATES ─────────────────────────────────────
function updatePipelineStep(step, status) {
  const mappedStep = STEP_MAP[step];
  if (!mappedStep) return;

  const stepIdx = STEP_ORDER.indexOf(mappedStep);
  if (stepIdx === -1) return;

  // Mark all prior as complete
  for (let i = 0; i < stepIdx; i++) {
    const el = document.querySelector(`.pipeline-step[data-step="${STEP_ORDER[i]}"]`);
    if (el && !el.classList.contains("error")) {
      el.className = "pipeline-step complete";
    }
  }

  const currentEl = document.querySelector(`.pipeline-step[data-step="${mappedStep}"]`);
  if (!currentEl) return;

  if (status === "error") {
    currentEl.className = "pipeline-step error";
    setStreamState("Error");
  } else if (status === "complete" && (step.endsWith("_complete") || step === "complete")) {
    currentEl.className = "pipeline-step complete";
  } else {
    currentEl.className = "pipeline-step active";
  }
}

function markPipelineComplete() {
  STEP_ORDER.forEach(stepName => {
    const el = document.querySelector(`.pipeline-step[data-step="${stepName}"]`);
    if (el && !el.classList.contains("error")) {
      el.className = "pipeline-step complete";
    }
  });
}

// ── STATS UPDATE ──────────────────────────────────────────────
function updateStats(step, data) {
  if (!data) return;

  if (data.sourcetype_count !== undefined) {
    updateStatCard("statSources", "valSources", data.sourcetype_count, null);
  }
  if (data.wasteful_count !== undefined) {
    updateStatCard("statWaste", "valWaste", data.wasteful_count, "highlight-warn");
  }
  if (data.total_monthly_savings !== undefined) {
    updateStatCard("statSavings", "valSavings", formatCurrency(data.total_monthly_savings, 0), "highlight");
  }
  if (data.prs_created !== undefined) {
    updateStatCard("statPRs", "valPRs", data.prs_created, "highlight");
  }
}

function updateStatCard(cardId, valueId, value, highlightClass) {
  const card = document.getElementById(cardId);
  const valueEl = document.getElementById(valueId) || (card && card.querySelector(".metric-value"));
  if (!card || !valueEl) return;

  if (highlightClass) {
    card.classList.remove("highlight", "highlight-warn");
    card.classList.add(highlightClass);
  }

  if (typeof value === "string" && value.startsWith("$")) {
    const target = Number(value.replace(/[$,]/g, ""));
    animateCountUp(valueEl, 0, target, 1100, v => formatCurrency(v, 0));
  } else {
    valueEl.textContent = value;
  }

  card.classList.add("pop");
  valueEl.classList.add("counting");
  setTimeout(() => {
    card.classList.remove("pop");
    valueEl.classList.remove("counting");
  }, 800);
}

function animateCountUp(element, start, end, duration, formatter) {
  const t0 = performance.now();
  const diff = end - start;

  function tick(now) {
    const elapsed  = now - t0;
    const progress = Math.min(elapsed / duration, 1);
    const eased    = 1 - Math.pow(1 - progress, 3);
    element.textContent = formatter(start + diff * eased);
    if (progress < 1) requestAnimationFrame(tick);
  }

  requestAnimationFrame(tick);
}

// ── EVENT CARDS ───────────────────────────────────────────────
function addEventCard(event) {
  const emptyState = document.getElementById("emptyState");
  if (emptyState) emptyState.remove();

  const stream = document.getElementById("eventStream");
  const card   = document.createElement("article");

  if (event.step === "complete" && event.data?.total_monthly_savings !== undefined) {
    card.className = "event-card final-report";
    card.innerHTML  = renderFinalReport(event);
  } else {
    card.className = `event-card status-${event.status || "info"}`;
    card.innerHTML  = renderEventCard(event);
  }

  stream.appendChild(card);
  requestAnimationFrame(() => { stream.scrollTop = stream.scrollHeight; });
}

function renderEventCard(event) {
  const { step, title, detail, status, data, timestamp } = event;
  let extraHTML = "";

  // MCP tool events
  if (step === "mcp_tools_ready" || step === "mcp_tool_called") {
    const transport    = data?.transport || "unknown";
    const isMcpDirect  = transport === "mcp_sse";
    const transportBadge = isMcpDirect
      ? `<span class="mcp-badge mcp-live">MCP SSE</span>`
      : `<span class="mcp-badge mcp-rest">REST Fallback</span>`;

    let toolsList = "";
    if (Array.isArray(data?.tools) && data.tools.length > 0) {
      toolsList = `<div class="mcp-tools-list">${data.tools.map(t => `<code>${esc(t)}</code>`).join("")}</div>`;
    }
    const toolInfo = data?.tool
      ? `<div class="mcp-tool-call">⚡ Tool: <code>${esc(data.tool)}</code> on <code>${esc(data.index || "")}</code></div>`
      : "";

    return `
      <div class="event-card-header">
        <span class="event-title">${esc(title || "")}</span>
        ${transportBadge}
      </div>
      ${detail ? `<div class="event-detail">${esc(detail)}</div>` : ""}
      ${toolsList}
      ${toolInfo}
      <div class="event-timestamp">${formatTime(timestamp)}</div>
    `;
  }

  if (data?.pr_url) {
    extraHTML += renderPrLink(data.pr_url, `PR #${data.pr_number || ""}`.trim(), data.title || "View Pull Request");
  }

  if (step === "waste_found" && data?.total_monthly_savings !== undefined) {
    extraHTML += `
      <div class="event-savings">
        ${formatCurrency(data.total_monthly_savings, 0)}
        <small>/ month estimated</small>
      </div>
    `;
    if (Array.isArray(data.wasteful_sources) && data.wasteful_sources.length > 0) {
      extraHTML += renderWasteTable(data.wasteful_sources);
    }
  }

  return `
    <div class="event-card-header">
      <span class="event-title">${esc(title || "Untitled Event")}</span>
      <span class="event-badge ${esc(status || "info")}">${esc(status || "info")}</span>
    </div>
    ${detail ? `<div class="event-detail">${esc(detail)}</div>` : ""}
    ${extraHTML}
    <div class="event-timestamp">${formatTime(timestamp)}</div>
  `;
}

function renderWasteTable(sources) {
  const rows = sources.slice(0, 5).map(source => {
    const scaled = source.demo_scaled ? `<span class="scale-badge">modeled</span>` : "";
    return `
      <tr>
        <td>${esc(source.sourcetype || "")}${scaled}</td>
        <td>${formatNumber(source.daily_gb, 2)}</td>
        <td>${formatNumber(source.search_count_30d || 0, 0)}</td>
        <td>${formatCurrency(source.est_monthly_cost || 0, 0)}</td>
      </tr>
    `;
  }).join("");

  return `
    <div class="waste-table-wrap">
      <table class="waste-table">
        <thead>
          <tr>
            <th>Sourcetype</th>
            <th>GB / day</th>
            <th>Searches (30d)</th>
            <th>Savings / mo</th>
          </tr>
        </thead>
        <tbody>${rows}</tbody>
      </table>
    </div>
  `;
}

function renderFinalReport(event) {
  const data    = event.data || {};
  const savings = data.total_monthly_savings || 0;
  const annual  = data.total_annual_savings  || savings * 12;
  const prUrls  = data.pr_urls || (data.pull_requests || []).map(pr => pr.url).filter(Boolean);

  return `
    <div class="event-card-header">
      <span class="event-title">Investigation Complete</span>
      <span class="event-badge complete">done</span>
    </div>
    <div class="event-detail">${esc(data.summary || event.detail || "")}</div>
    <div class="report-grid">
      ${reportItem("Sources",  data.sources_analyzed      ?? "--")}
      ${reportItem("Waste",    data.wasteful_sources_count ?? 0)}
      ${reportItem("PRs",      data.prs_created            ?? 0)}
      ${reportItem("Monthly",  formatCurrency(savings, 0),   true)}
      ${reportItem("Annual",   formatCurrency(annual, 0),    true)}
    </div>
    ${prUrls.length > 0 ? `<div>${prUrls.map((url, i) => renderPrLink(url, `PR #${i + 1}`, "Open")).join("")}</div>` : ""}
    <div class="event-timestamp">${formatTime(data.timestamp || event.timestamp)}</div>
  `;
}

function reportItem(label, value, positive = false) {
  return `
    <div class="report-item">
      <span class="report-item-label">${esc(label)}</span>
      <span class="report-item-value" ${positive ? 'style="color:var(--emerald);"' : ""}>${esc(String(value))}</span>
    </div>
  `;
}

function renderPrLink(url, label, title) {
  return `
    <a href="${escAttr(url)}" target="_blank" rel="noopener" class="event-pr-link" title="${escAttr(title)}">
      <svg viewBox="0 0 24 24" aria-hidden="true">
        <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/>
        <path d="M15 3h6v6"/>
        <path d="M10 14 21 3"/>
      </svg>
      ${esc(label)}
    </a>
  `;
}

// ── UI HELPERS ────────────────────────────────────────────────
function resetUI() {
  const stream = document.getElementById("eventStream");
  stream.innerHTML = "";

  // Reset metric cards
  ["valSources","valWaste","valSavings","valPRs"].forEach(id => {
    const el = document.getElementById(id);
    if (el) { el.textContent = "--"; el.classList.remove("counting"); }
  });

  ["statSources","statWaste","statSavings","statPRs"].forEach(id => {
    const el = document.getElementById(id);
    if (el) { el.classList.remove("highlight","highlight-warn","pop"); }
  });

  document.querySelectorAll(".pipeline-step").forEach(el => {
    el.className = "pipeline-step";
  });
}

function resetButton() {
  const btn = document.getElementById("triggerBtn");
  btn.classList.remove("running");
  setTriggerState("idle");
}

function setTriggerState(state) {
  const label   = document.getElementById("triggerLabel");
  const iconWrap = document.getElementById("triggerIconWrap");

  if (state === "running") {
    label.textContent = "Investigation Running";
    iconWrap.innerHTML = `
      <svg viewBox="0 0 24 24" aria-hidden="true">
        <path d="M12 2a10 10 0 1 0 10 10"/>
        <path d="M12 6v6l4 2"/>
      </svg>`;
  } else {
    label.textContent = "Start Investigation";
    iconWrap.innerHTML = `
      <svg viewBox="0 0 24 24" aria-hidden="true">
        <path d="M8 5v14l11-7Z" fill="currentColor" stroke="none"/>
      </svg>`;
  }
}

function setStreamState(label) {
  // Update both pipeline badge and stream badge
  ["streamState","streamStateBadge"].forEach(id => {
    const el = document.getElementById(id);
    if (!el) return;
    el.textContent = label;
    el.className   = el.className.replace(/\b(streaming|complete|error)\b/g, "").trim();
    if (label === "Streaming") {
      el.classList.add("streaming");
      el.textContent = "● Streaming";
    }
    if (label === "Complete") el.classList.add("complete");
    if (label === "Error")    el.classList.add("error");
  });
}

// ── RESET DEMO ────────────────────────────────────────────────
async function resetDemo() {
  const btn = document.getElementById("resetBtn");
  btn.classList.add("resetting");
  btn.innerHTML = "<span>Resetting…</span>";

  try {
    const res  = await fetch(`${BASE_URL}/reset-demo`, { method: "POST" });
    const data = await res.json();

    if (data.status === "success") {
      btn.innerHTML = "<span>Reset Complete</span>";
      btn.style.borderColor = "rgba(63,240,138,0.40)";
      btn.style.color       = "var(--emerald)";
    } else {
      btn.innerHTML = "<span>Reset Failed</span>";
      btn.style.borderColor = "rgba(248,113,113,0.40)";
      btn.style.color       = "var(--red)";
    }
  } catch {
    btn.innerHTML = "<span>Reset Error</span>";
    btn.style.color = "var(--red)";
  }

  setTimeout(() => {
    btn.classList.remove("resetting");
    btn.style.borderColor = "";
    btn.style.color       = "";
    btn.innerHTML = `
      <svg viewBox="0 0 24 24" aria-hidden="true">
        <path d="M3 12a9 9 0 1 0 3-6.7"/>
        <path d="M3 4v6h6"/>
      </svg>
      <span>Reset Demo</span>
    `;
  }, 2200);
}

// ── FORMATTERS ────────────────────────────────────────────────
function formatCurrency(value, digits = 0) {
  return Number(value || 0).toLocaleString("en-US", {
    style: "currency",
    currency: "USD",
    minimumFractionDigits: digits,
    maximumFractionDigits: digits,
  });
}

function formatNumber(value, digits = 0) {
  return Number(value || 0).toLocaleString("en-US", {
    minimumFractionDigits: digits,
    maximumFractionDigits: digits,
  });
}

function formatTime(value) {
  if (!value) return "";
  const d = new Date(value);
  return isNaN(d.getTime()) ? "" : d.toLocaleTimeString();
}

function esc(text) {
  const d = document.createElement("div");
  d.textContent = String(text ?? "");
  return d.innerHTML;
}

function escAttr(text) {
  return esc(text).replace(/"/g, "&quot;");
}
