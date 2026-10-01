# Enterprise AI Operating System

An advanced, multi-agent AI Operating System built with FastAPI, LangGraph, and pgvector.

## Architecture
- **Multi-Agent Supervisor**: Intelligently delegates tasks to Research, Math, and Writing sub-agents.
- **Enterprise Memory**: Dual-layer memory (conversational context + long-term semantic pgvector facts).
- **Self-Correction (Reflection)**: Evaluates generated responses for groundedness and routes backward to fix hallucinations.
- **Observability**: Node-level latency tracking and deterministic evaluation suites.

## Getting Started
1. Set `GEMINI_API_KEY` in your environment.
2. Run `docker-compose up --build`.
3. The API will be available at `http://localhost:8000`.

## Testing
Run the Pytest suite for security boundaries and deterministic routing:
```bash
pytest tests/
```

## Google Cloud Platform (GCP) Deployment
This OS is designed to run natively on Google Cloud.

1. **Cloud SQL (AlloyDB)**: Provision a PostgreSQL database with `pgvector` enabled for enterprise-grade semantic search.
2. **Secret Manager**: Store `GEMINI_API_KEY` and `ENTERPRISE_API_KEY` in GCP Secret Manager.
3. **Cloud Build**: We use `cloudbuild.yaml` to orchestrate our CI/CD pipeline automatically on `git push`.
4. **Cloud Run**: The FastAPI backend and LangGraph agents are containerized via Docker and deployed to Cloud Run, allowing for instant autoscaling and 0-to-N worker scaling for high-concurrency requests.

To deploy manually via GCP CLI:
```bash
gcloud builds submit --config cloudbuild.yaml .
```
