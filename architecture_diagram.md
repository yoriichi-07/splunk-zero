# Splunk Zero — Architecture Diagram

## System Overview

The following diagram shows how Splunk Zero's components interact:

```mermaid
flowchart TB
    subgraph UI["Dashboard UI<br/>(HTML/CSS/JS)"]
        BROWSER["Browser<br/>localhost:8888"]
    end

    subgraph SERVER["FastAPI Server"]
        TRIGGER["POST /trigger"]
        SSE["GET /events/{run_id}<br/>SSE Stream"]
        HEALTH["GET /health"]
        RESET["POST /reset-demo"]
        MTOOLS["GET /mcp-tools"]
    end

    subgraph PIPELINE["LangGraph Pipeline (7 Nodes)"]
        N1["Node 1: Ingest Analysis<br/>Gemini Agent + MCP Tools"]
        N2["Node 2: Search Audit<br/>Gemini Agent + MCP Tools"]
        N3["Node 3: Waste Detection<br/>Pure Python Logic"]
        N4["Node 4: Source Tracing<br/>Gemini LLM Reasoning"]
        N5["Node 5: Code Analysis<br/>Gemini + GitHub Read"]
        N6["Node 6: PR Creation<br/>GitHub API"]
        N7["Node 7: Report<br/>Summary Generation"]

        N1 --> N2 --> N3
        N3 -->|"waste found"| N4 --> N5 --> N6 --> N7
        N3 -->|"no waste"| N7
    end

    subgraph SPLUNK["Splunk Enterprise"]
        MCP_SERVER["MCP Server<br/>/services/mcp"]
        REST_API["REST API<br/>/services/search"]
        INTERNAL["_internal index<br/>Ingest Metrics"]
        AUDIT["_audit index<br/>Search Activity"]
    end

    subgraph GOOGLE["Google Cloud"]
        GEMINI["Gemini 2.5 Flash<br/>via Vertex AI"]
    end

    subgraph GITHUB["GitHub"]
        REPO["Demo Repository<br/>logging.conf"]
        PR["Pull Requests<br/>with Cost Evidence"]
    end

    subgraph EVENTS["SSE Event Manager"]
        QUEUE["Per-Run Event Queue"]
    end

    %% User interactions
    BROWSER -->|"Click Start Investigation"| TRIGGER
    BROWSER -->|"Subscribe to events"| SSE
    SSE -->|"Stream events"| BROWSER

    %% Server to Pipeline
    TRIGGER -->|"Creates run_id"| N1

    %% Pipeline to Splunk (via MCP)
    N1 -->|"MCP: splunk_run_query"| MCP_SERVER
    N2 -->|"MCP: splunk_run_query"| MCP_SERVER
    MCP_SERVER --> INTERNAL
    MCP_SERVER --> AUDIT

    %% Fallback path
    N1 -.->|"REST Fallback"| REST_API
    N2 -.->|"REST Fallback"| REST_API
    REST_API --> INTERNAL
    REST_API --> AUDIT

    %% Pipeline to Gemini
    N1 -->|"Agent invocation"| GEMINI
    N2 -->|"Agent invocation"| GEMINI
    N4 -->|"Sourcetype → repo mapping"| GEMINI
    N5 -->|"Config change proposal"| GEMINI

    %% Pipeline to GitHub
    N5 -->|"Read logging config"| REPO
    N6 -->|"Create branch + commit"| REPO
    N6 -->|"Open PR"| PR

    %% Events
    N1 -->|"emit()"| QUEUE
    N2 -->|"emit()"| QUEUE
    N3 -->|"emit()"| QUEUE
    N4 -->|"emit()"| QUEUE
    N5 -->|"emit()"| QUEUE
    N6 -->|"emit()"| QUEUE
    N7 -->|"emit()"| QUEUE
    QUEUE -->|"subscribe()"| SSE

    %% Health checks
    HEALTH -->|"Probe"| MCP_SERVER
    HEALTH -->|"Probe"| REST_API
    MTOOLS -->|"list_tools()"| MCP_SERVER

    %% Reset
    RESET -->|"Reset branches + PRs"| REPO

    classDef splunkNode fill:#1a472a,stroke:#3ff08a,color:#fff
    classDef geminiNode fill:#1a2747,stroke:#60a5fa,color:#fff
    classDef githubNode fill:#2d1b4e,stroke:#a78bfa,color:#fff
    classDef uiNode fill:#0d2b3e,stroke:#22d3ee,color:#fff
    classDef pipeNode fill:#1a1a2e,stroke:#fbbf24,color:#fff

    class INTERNAL,AUDIT,MCP_SERVER,REST_API splunkNode
    class GEMINI geminiNode
    class REPO,PR githubNode
    class BROWSER uiNode
    class N1,N2,N3,N4,N5,N6,N7 pipeNode
```

## Data Flow Summary

| Step | Component | Protocol | Purpose |
|------|-----------|----------|---------|
| 1 | Dashboard → Server | HTTP POST | Trigger pipeline run |
| 2 | Server → LangGraph | Python async | Start 7-node pipeline |
| 3 | Nodes 1-2 → Splunk | MCP (HTTP POST) / REST | Query `_internal` and `_audit` |
| 4 | Nodes 1-2, 4-5 → Gemini | Vertex AI gRPC | AI reasoning and tool orchestration |
| 5 | Nodes 5-6 → GitHub | REST API | Read configs, create PRs |
| 6 | All Nodes → EventManager | Python async Queue | Emit structured events |
| 7 | EventManager → Dashboard | SSE (HTTP streaming) | Real-time UI updates |

## MCP Integration Detail

Splunk Zero connects to the Splunk MCP Server using a **custom HTTP POST transport** that wraps the standard MCP JSON-RPC protocol. This approach:

- Sends JSON-RPC requests via `POST /services/mcp` with Bearer token auth
- Receives synchronous JSON-RPC responses (no SSE streaming needed)
- Falls back to direct Splunk REST API if MCP is unavailable
- Exposes MCP tools as LangChain `StructuredTool` instances for agent use
