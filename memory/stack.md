# Locked Stack

## Backend

| Component | Choice |
|---|---|
| Language | Python 3.13 local, code targets Python 3.11+ |
| Web framework | FastAPI |
| Server | Uvicorn |
| Agent orchestration | LangGraph |
| Splunk access | Splunk MCP client code with REST fallback |
| GitHub access | PyGithub |
| LLM | Google Vertex AI (Gemini via ADC) |
| Streaming | Server-Sent Events |

## Frontend

| Component | Choice |
|---|---|
| Markup | Vanilla HTML |
| Styling | Vanilla CSS |
| Logic | Vanilla JavaScript |
| Transport | EventSource over SSE |

No React or build step is used for Phase 3.

## Environment Variables

Use `.env.example` as the template. Real values live in `.env`.

Required:

- `SPLUNK_HOST`
- `SPLUNK_PORT`
- `SPLUNK_TOKEN`
- `SPLUNK_USERNAME`
- `SPLUNK_PASSWORD`
- `GITHUB_TOKEN`
- `GITHUB_REPO`
- `GCP_PROJECT`
- `GCP_LOCATION`

Useful demo settings:

- `APP_PORT=8888`
- `COST_PER_GB_PER_DAY=15`
- `WASTE_THRESHOLD_PCT=5`
- `MIN_SEARCH_COUNT=2`
- `ANALYSIS_PERIOD_DAYS=30`
- `SPLUNK_HEC_TOKEN`
- `SPLUNK_HEC_PORT=8088`
