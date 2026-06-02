# Tech Stack — Locked

## Backend

| Component | Choice | Version |
|---|---|---|
| Language | Python | 3.11+ |
| Orchestration | LangGraph | latest |
| Web Framework | FastAPI | latest |
| ASGI Server | Uvicorn | latest |
| Splunk Integration | Splunk MCP Server (official) | 1.1 |
| MCP Client | `langchain-mcp-adapters` | latest |
| GitHub Integration | PyGithub | latest |
| LLM Client | LangChain Google GenAI (Gemini Flash) | latest |

## Frontend (UI of Thinking)

| Component | Choice |
|---|---|
| Markup | Vanilla HTML |
| Styling | Vanilla CSS (dark theme, glassmorphism) |
| Logic | Vanilla JavaScript |
| Data Transport | Server-Sent Events (SSE) |

## Infrastructure

| Component | Choice |
|---|---|
| Splunk Instance | Local Docker (Splunk Enterprise, free dev license) |
| Dev Environment | Python venv |
| Demo Hosting | Local + ngrok (for webhook demo if needed) |

## Environment Variables (.env)

```env
# Splunk MCP
SPLUNK_HOST=localhost
SPLUNK_PORT=8089
SPLUNK_TOKEN=your_admin_token_here
SPLUNK_MCP_URL=http://localhost:8088/mcp

# GitHub
GITHUB_TOKEN=ghp_your_personal_access_token
GITHUB_REPO=your-org/your-repo
GITHUB_BRANCH_PREFIX=splunk-zero

# LLM
GOOGLE_API_KEY=your_gemini_api_key
LLM_MODEL=gemini-2.0-flash

# App
APP_PORT=8000
COST_PER_GB_PER_DAY=15
WASTE_THRESHOLD_PCT=5
MIN_SEARCH_COUNT=2
ANALYSIS_PERIOD_DAYS=30
```

## Python Dependencies (requirements.txt)

```
langgraph
langchain
langchain-google-genai
fastapi
uvicorn[standard]
sse-starlette
PyGithub
python-dotenv
httpx
pydantic
```
