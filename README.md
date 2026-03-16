# AI SRE Control Tower inside Notion

AI-powered incident response system that turns Notion into an SRE command center.

## 1) Overview

### Problem
Teams often track incidents in docs/tables, but triage, diagnosis, and remediation are still manual and slow.

### Solution
This project makes Notion an AI-assisted SRE control plane:
- Ingest incidents from a Notion database
- Generate root cause, fix, timeline, and AI severity
- Trigger automation (GitHub Actions, optional Kubernetes)
- Write incident status/results back into Notion

### Why this project is useful
- Real engineering workflow (incident lifecycle, not just chat UI)
- Multi-system integration (Notion + AI + GitHub Actions + optional K8s)
- Works with or without live cluster (dry-run fallback)

## 2) What is implemented

- Incident ingestion from Notion Incidents DB
- AI analysis with fallback heuristics when API is unavailable/quota-limited
- Root cause + recommended fix + incident timeline generation
- AI-derived severity support and normalization in processing pipeline
- Notion field updates for status, analysis, fix, timeline, severity, trigger
- GitHub workflow dispatch for remediation path
- Notion resolve workflow update from GitHub Actions
- Synthetic incident generator for demo/test

## 3) Architecture

```text
Notion Incidents DB
      |
      v
Python Processor (main.py)
  - incident_detection
  - ai_analyzer
  - root_cause_analyser
  - incident_handler
      |
      +--> GitHub Actions (redeploy.yml)
      |       +--> Optional kubectl rollout
      |       +--> notion-incident-resolve.yml
      |
      +--> Notion write-back (analysis/fix/timeline/status/severity)
```

## 4) Repository structure

```text
AI-SRE-Control-Tower-Inside-Notion/
├── agent/
│   ├── ai_analyzer.py
│   ├── incident_handler.py
│   └── root_cause_analyser.py
├── integrations/
│   ├── notion_client.py
│   ├── github_actions.py
│   └── kubernetes.py
├── workflows/
│   ├── incident_detection.py
│   └── auto_fix.py
├── services/
│   └── error_service.py
├── .github/workflows/
│   ├── redeploy.yml
│   └── notion-incident-resolve.yml
├── .env.example
├── main.py
└── requirements.txt
```

## 5) Notion schema used

Use an Incidents database with these properties:
- Service Name (Title)
- Service Status (Select)
- Error Logs (Text/rich_text)
- Severity (Select)
- AI Analysis (Text/rich_text)
- Recommended Fix (Text/rich_text)
- Deployment Trigger (Checkbox)
- Incident Summary (Text/rich_text)
- Incident Timeline (Text/rich_text)

Share the database with your Notion integration.

## 6) Setup

### Local

1. Copy env template

```bash
# PowerShell
Copy-Item .env.example .env

# Bash
cp .env.example .env
```

2. Required secrets
- NOTION_API_KEY
- NOTION_DATABASE_ID

3. Recommended mapping for current schema
- NOTION_PROP_SERVICE_NAME=Service Name
- NOTION_PROP_STATUS=Service Status
- NOTION_PROP_STATUS_TYPE=select
- NOTION_PROP_ERROR_LOGS=Error Logs
- NOTION_PROP_SEVERITY=Severity
- NOTION_PROP_INCIDENT_TIMELINE=Incident Timeline
- NOTION_PROP_AI_ANALYSIS=AI Analysis
- NOTION_PROP_RECOMMENDED_FIX=Recommended Fix
- NOTION_PROP_DEPLOYMENT_TRIGGER=Deployment Trigger
- NOTION_PROP_DEPLOYMENT_TRIGGER_TYPE=checkbox
- NOTION_PROP_INCIDENT_SUMMARY=Incident Summary

4. Install and run

```bash
python -m pip install -r requirements.txt
python main.py
```

Polling mode:

```bash
python main.py --poll
```

Synthetic incident generation:

```bash
python services/error_service.py --once
python services/error_service.py --interval 60
```

### GitHub Actions

Repository secrets:
- NOTION_API_KEY
- NOTION_DATABASE_ID (recommended)
- KUBE_CONFIG_DATA (only if using live Kubernetes rollout)

Repository variables:
- NOTION_PROP_STATUS=Service Status
- NOTION_PROP_DEPLOYMENT_TRIGGER=Deployment Trigger
- NOTION_STATUS_RESOLVED=Resolved
- KUBE_NAMESPACE=default (if using K8s)

## 7) End-to-end walkthrough

1. Add incident row in Notion (example: orders-api, high, timeout log)
2. Run processor locally: python main.py
3. Show updated fields:
   - AI Analysis
   - Recommended Fix
   - Incident Timeline
   - Severity
   - Service Status
4. Run GitHub Actions redeploy workflow (manual or dispatched)
5. Show final Notion resolve state and trigger checkbox update

## 8) Design highlights

- Notion-first operations workflow
- Cross-platform orchestration and API integration
- Practical incident response lifecycle support
- Reliable fallback path when external dependencies are unavailable

## 9) Known limitations

- Single database processing loop
- No multi-tenant access model
- Severity still rule/AI hybrid (not historical learning model)

## 10) Roadmap

- Slack/Teams alerting
- Metrics correlation (Prometheus/Grafana)
- RCA confidence scoring with evidence links
- Multi-workspace and role-based workflows

## 11) Screenshots

Add your screenshots in a folder like `docs/screenshots/` and update the paths below.

### 1. Incident created in Notion
![Incident Created](docs/screenshots/Screenshot%20(1302).png)

### 2. AI analysis and recommendations updated
![AI Analysis Updated](docs/screenshots/Screenshot%20(1303).png)

### 3. Incident timeline and severity populated
![Timeline and Severity](docs/screenshots/Screenshot%20(1304).png)

### 4. GitHub Actions redeploy workflow run
![Redeploy Workflow](docs/screenshots/Screenshot%20(1308).png)

### 5. Notion resolve workflow update
![Notion Resolve Workflow](docs/screenshots/Screenshot%20(1309).png)
