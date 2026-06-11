const BASE_URL = window.location.origin;

let currentRunId = null;
let eventSource = null;

const STEP_MAP = {
    triggered: null,
    querying_ingest: "ingest_analysis",
    ingest_complete: "ingest_analysis",
    ingest_error: "ingest_analysis",
    mcp_tools_ready: "ingest_analysis",
    mcp_tool_called: null,
    querying_audit: "search_audit",
    audit_complete: "search_audit",
    audit_error: "search_audit",
    detecting_waste: "waste_detection",
    waste_found: "waste_detection",
    no_waste: "waste_detection",
    tracing_source: "source_tracing",
    source_traced: "source_tracing",
    source_trace_failed: "source_tracing",
    tracing_complete: "source_tracing",
    analyzing_code: "code_analysis",
    reading_config: "code_analysis",
    change_proposed: "code_analysis",
    analysis_error: "code_analysis",
    analysis_complete: "code_analysis",
    creating_pr: "pr_creation",
    creating_branch: "pr_creation",
    pr_created: "pr_creation",
    pr_error: "pr_creation",
    prs_complete: "pr_creation",
    complete: "report",
    done: "report",
    error: null,
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

document.addEventListener("DOMContentLoaded", () => {
    checkHealth();
    setInterval(checkHealth, 30000);
});

async function checkHealth() {
    const indicator = document.getElementById("serverStatus");
    const mcpIndicator = document.getElementById("mcpStatus");

    try {
        const res = await fetch(`${BASE_URL}/health`);
        const data = await res.json();

        if (data.status === "healthy" && data.splunk?.status === "healthy") {
            indicator.className = "health-pill healthy";
            indicator.querySelector("span:last-child").textContent = `Splunk ${data.splunk.version || ""}`.trim();
        } else if (data.status === "healthy") {
            indicator.className = "health-pill healthy";
            indicator.querySelector("span:last-child").textContent = "Server Ready";
        } else {
            indicator.className = "health-pill error";
            indicator.querySelector("span:last-child").textContent = "Config Issue";
        }

        // Update MCP status pill
        if (mcpIndicator && data.mcp) {
            const mcp = data.mcp;
            if (mcp.mcp_connected) {
                mcpIndicator.className = "health-pill healthy";
                mcpIndicator.querySelector("span:last-child").textContent = `MCP: ${mcp.tool_count} tools`;
            } else {
                mcpIndicator.className = "health-pill warn";
                mcpIndicator.querySelector("span:last-child").textContent = `MCP: REST fallback (${mcp.tool_count} tools)`;
            }
        }
    } catch (error) {
        indicator.className = "health-pill error";
        indicator.querySelector("span:last-child").textContent = "Offline";
        if (mcpIndicator) {
            mcpIndicator.className = "health-pill error";
            mcpIndicator.querySelector("span:last-child").textContent = "MCP: unknown";
        }
    }
}

async function triggerRun() {
    const btn = document.getElementById("triggerBtn");
    if (btn.classList.contains("running")) return;

    if (eventSource) {
        eventSource.close();
        eventSource = null;
    }

    btn.classList.add("running");
    btn.querySelector(".trigger-label").textContent = "Investigation Running";
    btn.querySelector(".trigger-icon").innerHTML = `
        <svg viewBox="0 0 24 24" aria-hidden="true">
            <path d="M12 2a10 10 0 1 0 10 10"/>
            <path d="M12 6v6l4 2"/>
        </svg>
    `;

    setStreamState("Connecting");
    resetUI();

    try {
        const res = await fetch(`${BASE_URL}/trigger`, { method: "POST" });
        const data = await res.json();
        currentRunId = data.run_id;

        document.getElementById("runIdBadge").style.display = "inline-flex";
        document.getElementById("runIdText").textContent = `run:${currentRunId}`;
        document.getElementById("runIdPlaceholder").style.display = "none";
        document.getElementById("pipelineProgress").style.display = "flex";

        connectSSE(currentRunId);
    } catch (error) {
        addEventCard({
            step: "error",
            title: "Failed To Start",
            detail: `Could not start the pipeline: ${error.message}`,
            status: "error",
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
            if (jsonStr.startsWith("data: ")) {
                jsonStr = jsonStr.substring(6);
            }
            handleEvent(JSON.parse(jsonStr));
        } catch (error) {
            // Ignore ping frames or malformed transport noise.
        }
    };

    eventSource.onerror = () => {
        if (eventSource) {
            eventSource.close();
            eventSource = null;
        }
    };
}

function handleEvent(event) {
    if (event.step === "done") {
        if (eventSource) {
            eventSource.close();
            eventSource = null;
        }
        resetButton();
        markPipelineComplete();
        setStreamState("Complete");
        return;
    }

    updatePipelineStep(event.step, event.status);
    updateStats(event.step, event.data);
    addEventCard(event);
}

function updatePipelineStep(step, status) {
    const mappedStep = STEP_MAP[step];
    if (!mappedStep) return;

    const stepIdx = STEP_ORDER.indexOf(mappedStep);
    if (stepIdx === -1) return;

    for (let i = 0; i < stepIdx; i += 1) {
        const el = document.querySelector(`.step[data-step="${STEP_ORDER[i]}"]`);
        if (el && !el.classList.contains("error")) {
            el.className = "step complete";
        }
    }

    const currentEl = document.querySelector(`.step[data-step="${mappedStep}"]`);
    if (!currentEl) return;

    if (status === "error") {
        currentEl.className = "step error";
        setStreamState("Error");
    } else if (status === "complete" && (step.endsWith("_complete") || step === "complete")) {
        currentEl.className = "step complete";
    } else {
        currentEl.className = "step active";
    }
}

function markPipelineComplete() {
    STEP_ORDER.forEach((stepName) => {
        const el = document.querySelector(`.step[data-step="${stepName}"]`);
        if (el && !el.classList.contains("error")) {
            el.className = "step complete";
        }
    });
}

function updateStats(step, data) {
    if (!data) return;

    if (data.sourcetype_count !== undefined) {
        updateStatCard("statSources", data.sourcetype_count);
    }

    if (data.wasteful_count !== undefined) {
        updateStatCard("statWaste", data.wasteful_count, "highlight-red");
    }

    if (data.total_monthly_savings !== undefined) {
        updateStatCard("statSavings", formatCurrency(data.total_monthly_savings, 0), "highlight");
    }

    if (data.prs_created !== undefined) {
        updateStatCard("statPRs", data.prs_created, "highlight");
    }
}

function updateStatCard(id, value, highlightClass) {
    const card = document.getElementById(id);
    if (!card) return;

    const valueEl = card.querySelector(".metric-value");
    if (!valueEl) return;

    if (typeof value === "string" && value.startsWith("$")) {
        const target = Number(value.replace(/[$,]/g, ""));
        animateCountUp(valueEl, 0, target, 1000, (v) => formatCurrency(v, 0));
    } else {
        valueEl.textContent = value;
    }

    if (highlightClass) {
        card.classList.add(highlightClass);
    }

    card.style.transform = "translateY(-2px)";
    valueEl.classList.add("counting");
    setTimeout(() => {
        card.style.transform = "";
        valueEl.classList.remove("counting");
    }, 720);
}

function animateCountUp(element, start, end, duration, formatter) {
    const startTime = performance.now();
    const diff = end - start;

    function update(currentTime) {
        const elapsed = currentTime - startTime;
        const progress = Math.min(elapsed / duration, 1);
        const eased = 1 - Math.pow(1 - progress, 3);
        element.textContent = formatter(start + diff * eased);

        if (progress < 1) {
            requestAnimationFrame(update);
        }
    }

    requestAnimationFrame(update);
}

function addEventCard(event) {
    const emptyState = document.getElementById("emptyState");
    if (emptyState) emptyState.remove();

    const stream = document.getElementById("eventStream");
    const card = document.createElement("article");

    if (event.step === "complete" && event.data?.total_monthly_savings !== undefined) {
        card.className = "event-card final-report";
        card.innerHTML = renderFinalReport(event);
    } else {
        card.className = `event-card status-${event.status || "info"}`;
        card.innerHTML = renderEventCard(event);
    }

    stream.appendChild(card);
    requestAnimationFrame(() => {
        stream.scrollTop = stream.scrollHeight;
    });
}

function renderEventCard(event) {
    const { step, title, detail, status, data, timestamp } = event;
    let extraHTML = "";

    // Special rendering for MCP tool events
    if (step === "mcp_tools_ready" || step === "mcp_tool_called") {
        const transport = data?.transport || "unknown";
        const isMcpDirect = transport === "mcp_sse";
        const transportBadge = isMcpDirect
            ? `<span class="mcp-badge mcp-live">MCP SSE</span>`
            : `<span class="mcp-badge mcp-rest">REST fallback</span>`;

        let toolsList = "";
        if (Array.isArray(data?.tools) && data.tools.length > 0) {
            toolsList = `<div class="mcp-tools-list">${data.tools.map(t => `<code>${escapeHtml(t)}</code>`).join(" ")}</div>`;
        }
        const toolInfo = data?.tool ? `<div class="mcp-tool-call">⚡ Tool: <code>${escapeHtml(data.tool)}</code> on <code>${escapeHtml(data.index || "")}</code></div>` : "";

        return `
            <div class="event-card-header">
                <span class="event-title">${escapeHtml(title || "")}</span>
                ${transportBadge}
            </div>
            ${detail ? `<div class="event-detail">${escapeHtml(detail)}</div>` : ""}
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
                <small>/ month</small>
            </div>
        `;

        if (Array.isArray(data.wasteful_sources) && data.wasteful_sources.length > 0) {
            extraHTML += renderWasteTable(data.wasteful_sources);
        }
    }

    return `
        <div class="event-card-header">
            <span class="event-title">${escapeHtml(title || "Untitled Event")}</span>
            <span class="event-badge ${escapeHtml(status || "info")}">${escapeHtml(status || "info")}</span>
        </div>
        ${detail ? `<div class="event-detail">${escapeHtml(detail)}</div>` : ""}
        ${extraHTML}
        <div class="event-timestamp">${formatTime(timestamp)}</div>
    `;
}

function renderWasteTable(sources) {
    const rows = sources.slice(0, 5).map((source) => {
        const scaled = source.demo_scaled ? `<span class="scale-badge">modeled</span>` : "";
        return `
            <tr>
                <td>${escapeHtml(source.sourcetype || "")}${scaled}</td>
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
                        <th>GB/day</th>
                        <th>Searches</th>
                        <th>Savings/mo</th>
                    </tr>
                </thead>
                <tbody>${rows}</tbody>
            </table>
        </div>
    `;
}

function renderFinalReport(event) {
    const data = event.data || {};
    const savings = data.total_monthly_savings || 0;
    const annual = data.total_annual_savings || savings * 12;
    const prUrls = data.pr_urls || (data.pull_requests || []).map((pr) => pr.url).filter(Boolean);

    return `
        <div class="event-card-header">
            <span class="event-title">Investigation Complete</span>
            <span class="event-badge complete">done</span>
        </div>
        <div class="event-detail">${escapeHtml(data.summary || event.detail || "")}</div>
        <div class="report-grid">
            ${renderReportItem("Sources", data.sources_analyzed ?? "--")}
            ${renderReportItem("Waste", data.wasteful_sources_count ?? 0)}
            ${renderReportItem("PRs", data.prs_created ?? 0)}
            ${renderReportItem("Monthly", formatCurrency(savings, 0), true)}
            ${renderReportItem("Annual", formatCurrency(annual, 0), true)}
        </div>
        ${prUrls.length > 0 ? `
            <div>
                ${prUrls.map((url, index) => renderPrLink(url, `PR #${index + 1}`, "Open")).join("")}
            </div>
        ` : ""}
        <div class="event-timestamp">${formatTime(data.timestamp || event.timestamp)}</div>
    `;
}

function renderReportItem(label, value, positive = false) {
    return `
        <div class="report-item">
            <span class="report-item-label">${escapeHtml(label)}</span>
            <span class="report-item-value" ${positive ? 'style="color: var(--green);"' : ""}>${escapeHtml(String(value))}</span>
        </div>
    `;
}

function renderPrLink(url, label, title) {
    return `
        <a href="${escapeAttribute(url)}" target="_blank" rel="noopener" class="event-pr-link" title="${escapeAttribute(title)}">
            <svg viewBox="0 0 24 24" aria-hidden="true">
                <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/>
                <path d="M15 3h6v6"/>
                <path d="M10 14 21 3"/>
            </svg>
            ${escapeHtml(label)}
        </a>
    `;
}

function resetUI() {
    const stream = document.getElementById("eventStream");
    stream.innerHTML = "";

    document.querySelectorAll(".metric-value").forEach((el) => {
        el.textContent = "--";
        el.classList.remove("counting");
    });

    document.querySelectorAll(".metric-card").forEach((el) => {
        el.classList.remove("highlight", "highlight-red");
        el.style.transform = "";
    });

    document.querySelectorAll(".step").forEach((el) => {
        el.className = "step";
    });
}

function resetButton() {
    const btn = document.getElementById("triggerBtn");
    btn.classList.remove("running");
    btn.querySelector(".trigger-label").textContent = "Start Investigation";
    btn.querySelector(".trigger-icon").innerHTML = `
        <svg viewBox="0 0 24 24" aria-hidden="true">
            <path d="M8 5v14l11-7Z"/>
        </svg>
    `;
}

async function resetDemo() {
    const btn = document.getElementById("resetBtn");
    btn.classList.add("resetting");
    btn.innerHTML = "<span>Resetting</span>";

    try {
        const res = await fetch(`${BASE_URL}/reset-demo`, { method: "POST" });
        const data = await res.json();

        if (data.status === "success") {
            btn.innerHTML = "<span>Reset Complete</span>";
            btn.style.borderColor = "rgba(63, 240, 138, 0.42)";
            btn.style.color = "var(--green)";
        } else {
            btn.innerHTML = "<span>Reset Failed</span>";
            btn.style.borderColor = "rgba(255, 107, 122, 0.42)";
            btn.style.color = "var(--red)";
        }
    } catch (error) {
        btn.innerHTML = "<span>Reset Error</span>";
        btn.style.color = "var(--red)";
    }

    setTimeout(() => {
        btn.classList.remove("resetting");
        btn.innerHTML = `
            <svg viewBox="0 0 24 24" aria-hidden="true">
                <path d="M3 12a9 9 0 1 0 3-6.7"/>
                <path d="M3 4v6h6"/>
            </svg>
            <span>Reset Demo</span>
        `;
        btn.style.borderColor = "";
        btn.style.color = "";
    }, 1800);
}

function setStreamState(label) {
    const el = document.getElementById("streamState");
    if (el) el.textContent = label;
}

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
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) return "";
    return date.toLocaleTimeString();
}

function escapeHtml(text) {
    const div = document.createElement("div");
    div.textContent = String(text ?? "");
    return div.innerHTML;
}

function escapeAttribute(text) {
    return escapeHtml(text).replace(/"/g, "&quot;");
}
