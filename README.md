<p align="center">
  <img src="architecture_diagram.png" alt="Splunk Zero Architecture" width="800">
</p>

<h1 align="center">Splunk Zero</h1>
<p align="center">
  <strong>Zero noise. Zero waste. Zero unused data.</strong><br>
  An autonomous AI agent that detects wasteful Splunk ingest, proves low usage<br>
  with Splunk's own data, and opens GitHub pull requests to reduce logging noise.
</p>

<p align="center">
  <a href="#the-problem">Problem</a> •
  <a href="#the-solution">Solution</a> •
  <a href="#quick-start">Quick Start</a> •
  <a href="#how-it-works">How It Works</a> •
  <a href="#architecture">Architecture</a> •
  <a href="#technology">Technology</a> •
  <a href="#hackathon-track">Track</a> •
  <a href="#license">License</a>
</p>

---

## The Problem

Every organization running Splunk at scale pays to ingest logs that nobody reads. Debug-level application logs, verbose service traces, and noisy internal metrics accumulate in indexes — consuming license capacity and storage — while teams only search a fraction of them. The cost adds up silently.

## The Solution

**Splunk Zero** is not a chatbot. It is an autonomous agent that:

1. **Queries** `_internal` to measure ingest volume by sourcetype
2. **Audits** `_audit` to find which sourcetypes teams actually search
3. **Detects** the gap — high-volume sources with zero or low search activity
4. **Traces** wasteful sourcetypes back to GitHub repository logging configs
5. **Analyzes** the code and proposes a safer log level (DEBUG → ERROR)
6. **Creates** a real GitHub pull request with the fix and cost savings evidence
7. **Reports** total monthly and annual savings with PR links

The entire investigation runs autonomously from a single button click. Judges and users watch every step through a live "UI of Thinking" dashboard.

---

## Quick Start

<details>
<summary><strong>Prerequisites</strong></summary>

- **Python 3.11+**
- **Splunk Enterprise** (local) with admin access
- **GitHub** personal access token with `repo` scope
- **Google Cloud** project with Vertex AI API enabled (uses Application Default Credentials)
- **Splunk MCP Server** app installed (optional — REST fallback available)

</details>

<details>
<summary><strong>Setup Instructions</strong></summary>

```bash
# Clone the repository
git clone https://github.com/yoriichi-07/splunk-zero.git
cd splunk-zero

# Create virtual environment
python -m venv venv
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your Splunk, GitHub, and GCP credentials

# Authenticate with Google Cloud (for Vertex AI)
gcloud auth application-default login
```

</details>

<details>
<summary><strong>Load Demo Data</strong></summary>

```bash
# Load synthetic application debug sourcetypes into Splunk HEC
python -m scripts.synthetic_data
```

This sends realistic debug-level logs for three synthetic services (`payment-service`, `user-auth`, `inventory-api`) into Splunk via HEC. Since nobody searches for them, the agent will detect them as wasteful.

</details>

<details>
<summary><strong>Run</strong></summary>

```bash
# Reset the demo repository (cleans branches & PRs)
python -m scripts.reset_demo

# Start the server
python -m src.server
```

Open **http://localhost:8888** and click **Start Investigation**.

</details>

---

## How It Works

Splunk Zero uses a **7-node LangGraph pipeline** that executes autonomously:

| Step | Node | What It Does |
|------|------|-------------|
| 1 | **Ingest Analysis** | Deploys Gemini agent with MCP tools to query `_internal` for ingest volume by sourcetype |
| 2 | **Search Audit** | Deploys Gemini agent with MCP tools to query `_audit` for completed searches by sourcetype |
| 3 | **Waste Detection** | Cross-references ingest vs. search usage to find waste (pure Python, no LLM) |
| 4 | **Source Tracing** | Maps wasteful sourcetypes to GitHub repos and config files (LLM reasoning) |
| 5 | **Code Analysis** | Reads logging configs, proposes log-level reductions via Gemini |
| 6 | **PR Creation** | Creates branch, commits change, opens PR with cost evidence |
| 7 | **Report** | Summarizes findings, savings, and PR links |

If no waste is detected at step 3, the pipeline skips to step 7 and reports a clean environment.

<details>
<summary><strong>Core SPL Queries</strong></summary>

**Ingest volume** — what you pay for:
```spl
index=_internal source=*metrics.log group=per_sourcetype_thruput
| stats sum(kb) as total_kb by series
| eval daily_gb = round(total_kb / 1024 / 1024 / 30, 2)
| sort - daily_gb | head 50
| eventstats sum(daily_gb) as grand_total
| eval pct_of_total = round(daily_gb / grand_total * 100, 1)
| table series, daily_gb, pct_of_total
| rename series as sourcetype
```

**Search activity** — what teams actually use:
```spl
index=_audit action=search info=completed
| rex field=search "sourcetype\s*=\s*\"?(?<searched_sourcetype>[^\s\"|]+)"
| stats count as search_count by searched_sourcetype
| sort - search_count
```

</details>

<details>
<summary><strong>Agentic MCP Pattern</strong></summary>

Nodes 1 and 2 don't call Splunk REST directly — they deploy a **Gemini `react_agent`** equipped with Splunk MCP tools (`splunk_run_query`, `splunk_get_indexes`). The LLM autonomously decides which tool to call and with what SPL query. This is the true agentic MCP pattern: AI orchestrating Splunk data access.

The MCP client uses a custom HTTP POST transport wrapper that communicates with Splunk's JSON-RPC endpoint, resolving the SSE transport limitations on Windows.

</details>

---

## Architecture

```
┌─────────────────┐     POST /trigger      ┌──────────────────┐
│                 │ ──────────────────────► │                  │
│   Dashboard UI  │                        │  FastAPI Server   │
│  (HTML/CSS/JS)  │ ◄────────────────────  │  (Port 8888)     │
│                 │    SSE Event Stream     │                  │
└─────────────────┘                        └────────┬─────────┘
                                                    │
                                           ┌────────▼─────────┐
                                           │  LangGraph Agent  │
                                           │  (7-node pipeline)│
                                           └──┬─────┬─────┬───┘
                                              │     │     │
                               ┌──────────────┘     │     └──────────────┐
                               ▼                    ▼                    ▼
                    ┌──────────────────┐  ┌─────────────────┐  ┌─────────────────┐
                    │ Splunk Enterprise│  │  Google Gemini   │  │   GitHub API    │
                    │  _internal       │  │  (Vertex AI)     │  │  (PR creation)  │
                    │  _audit          │  │                  │  │                 │
                    └──────────────────┘  └─────────────────┘  └─────────────────┘
```

A visual architecture diagram is included at the root of this repository: [`architecture_diagram.png`](architecture_diagram.png)

<details>
<summary><strong>Data Flow</strong></summary>

1. The **Dashboard** sends `POST /trigger` to the FastAPI server
2. The server creates a run ID and starts the **LangGraph pipeline** in the background
3. Each pipeline node:
   - Deploys a **Gemini agent** with Splunk MCP tools for data access
   - Uses **Gemini** for source-to-repo mapping and config change reasoning
   - Calls **GitHub** to create branches, commit changes, and open PRs
   - Emits structured events to the **SSE EventManager**
4. The Dashboard subscribes to `GET /events/{run_id}` and renders every step live
5. The final report shows savings and clickable PR links

</details>

<details>
<summary><strong>Key Endpoints</strong></summary>

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/` | Dashboard UI |
| `GET` | `/health` | System health check (Splunk + MCP connectivity) |
| `GET` | `/mcp-tools` | Live MCP tool discovery — shows available Splunk MCP tools |
| `POST` | `/trigger` | Start an agent pipeline run |
| `GET` | `/events/{run_id}` | SSE stream of pipeline events |
| `POST` | `/reset-demo` | Reset demo repository to clean state |

</details>

---

## Technology

| Layer | Technology |
|-------|-----------:|
| **Agent Orchestration** | [LangGraph](https://github.com/langchain-ai/langgraph) — state machine with 7 nodes |
| **Web Server** | [FastAPI](https://fastapi.tiangolo.com/) + [Uvicorn](https://www.uvicorn.org/) |
| **Splunk Access** | Splunk MCP Server (HTTP POST transport) with REST API fallback |
| **AI Reasoning** | [Google Gemini](https://ai.google.dev/) via Vertex AI (ADC) |
| **GitHub Integration** | [PyGithub](https://pygithub.readthedocs.io/) |
| **Real-time Streaming** | Server-Sent Events (SSE) |
| **Frontend** | Vanilla HTML / CSS / JavaScript (no build step) |

<details>
<summary><strong>Why This Stack</strong></summary>

- **LangGraph** gives us a typed state machine with conditional routing — the pipeline can skip remediation if no waste is found
- **FastAPI + SSE** enables real-time "UI of Thinking" without WebSocket complexity
- **Vanilla frontend** means zero build tooling and instant deployment
- **MCP + REST fallback** for Splunk ensures reliability across environments
- **Vertex AI (ADC)** provides secure authentication without managing raw API keys

</details>

---

## Project Structure

<details>
<summary><strong>View Structure</strong></summary>

```
splunk-zero/
├── src/
│   ├── server.py              # FastAPI application
│   ├── config.py              # Environment configuration
│   ├── agent/
│   │   ├── graph.py           # LangGraph workflow definition
│   │   ├── state.py           # Agent state schema
│   │   └── nodes/
│   │       ├── ingest_analysis.py   # Node 1: Query _internal (agentic MCP)
│   │       ├── search_audit.py      # Node 2: Query _audit (agentic MCP)
│   │       ├── waste_detection.py   # Node 3: Cross-reference usage vs cost
│   │       ├── source_tracing.py    # Node 4: Map sourcetype → GitHub repo
│   │       ├── code_analysis.py     # Node 5: Propose log-level changes
│   │       ├── pr_creation.py       # Node 6: Create GitHub PRs
│   │       └── report.py           # Node 7: Final report with savings
│   ├── mcp/
│   │   └── splunk_client.py   # Splunk MCP/REST client + LangChain tools
│   ├── github/
│   │   └── client.py          # GitHub API wrapper (PyGithub)
│   └── ui/
│       ├── events.py          # SSE event manager (per-run queues)
│       └── static/
│           ├── index.html     # Dashboard markup
│           ├── style.css      # Premium design system
│           └── app.js         # SSE handling & live rendering
├── scripts/
│   ├── reset_demo.py          # Reset demo repo for clean runs
│   └── synthetic_data.py      # Load demo sourcetypes into Splunk HEC
├── tests/
│   ├── test_pipeline.py       # End-to-end pipeline test
│   ├── test_mcp_connection.py # Splunk MCP/REST connectivity test
│   ├── test_github_connection.py
│   ├── test_llm_connection.py
│   └── test_waste_detection.py # 27 unit tests for core logic
├── .env.example               # Environment variable template
├── requirements.txt           # Python dependencies
├── architecture_diagram.png   # Visual architecture diagram
├── LICENSE                    # MIT License
└── README.md                  # This file
```

</details>

---

## Configuration

<details>
<summary><strong>Environment Variables</strong></summary>

Copy `.env.example` to `.env` and fill in your credentials:

| Variable | Description | Required |
|----------|-------------|----------|
| `SPLUNK_HOST` | Splunk management host | Yes |
| `SPLUNK_PORT` | Splunk management port (default: `8089`) | Yes |
| `SPLUNK_TOKEN` | Splunk MCP encrypted token | Yes |
| `SPLUNK_USERNAME` | Splunk admin username | Yes |
| `SPLUNK_PASSWORD` | Splunk admin password | Yes |
| `GITHUB_TOKEN` | GitHub personal access token (`repo` scope) | Yes |
| `GITHUB_REPO` | Target demo repo (e.g., `user/splunk-zero-demo-app`) | Yes |
| `GCP_PROJECT` | Google Cloud project ID (for Vertex AI) | Yes |
| `GCP_LOCATION` | GCP region (default: `us-central1`) | Yes |
| `LLM_MODEL` | Gemini model name (default: `gemini-2.5-flash`) | No |
| `APP_PORT` | Application port (default: `8888`) | No |
| `COST_PER_GB_PER_DAY` | Splunk license cost per GB/day (default: `15`) | No |
| `WASTE_THRESHOLD_PCT` | Minimum ingest % to flag as waste (default: `5`) | No |
| `MIN_SEARCH_COUNT` | Search count below which a source is "unused" (default: `2`) | No |
| `ANALYSIS_PERIOD_DAYS` | Lookback window in days (default: `30`) | No |
| `SPLUNK_HEC_TOKEN` | HEC token for loading demo data | For demo |
| `SPLUNK_HEC_PORT` | HEC port (default: `8088`) | For demo |

</details>

---

## Demo Setup

<details>
<summary><strong>Running the Demo</strong></summary>

The project includes a demo repository (`yoriichi-07/splunk-zero-demo-app`) with a `logging.conf` file. The agent will detect its synthetic debug sourcetypes as waste and create real PRs against it.

```bash
# 1. Load synthetic data into Splunk
python -m scripts.synthetic_data

# 2. Reset demo repo (clean branches, close old PRs, reset logging.conf)
python -m scripts.reset_demo

# 3. Start the server
python -m src.server

# 4. Open http://localhost:8888 and click Start Investigation
```

The demo uses deterministic production-scale baselines for synthetic sourcetypes, so the savings numbers reflect realistic enterprise Splunk costs.

</details>

---

## Testing

<details>
<summary><strong>Test Commands</strong></summary>

```bash
# Unit tests (no external services needed) — 27 tests
python -m pytest tests/test_waste_detection.py -v

# Connection tests (requires Splunk running)
python -m tests.test_mcp_connection
python -m tests.test_github_connection
python -m tests.test_llm_connection

# End-to-end pipeline test (requires server running)
python -m tests.test_pipeline
```

</details>

---

## Splunk Hackathon 
**Name:** Shreesaanth R

**Theme:** Platform & Developer Experience  


---

## License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.

---

<p align="center">
  <em>Splunk Zero: Turning operational data into action.</em><br>
  <em>Zero noise. Zero waste. Zero unused data.</em>
</p>
