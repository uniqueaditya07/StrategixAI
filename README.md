# StrategixAI - AI Strategy Intelligence Platform

Simulate business decisions, compare strategic scenarios, generate executive intelligence, and export boardroom-ready reports.

StrategixAI is a deterministic strategy intelligence dashboard for workspace-based company analysis. It helps users model business outcomes, compare scenarios, generate explainable executive insights from simulation outputs, and export professional JSON and PDF reports for internal review or board-level discussion.

## Project Overview

StrategixAI is built for decision support, not chat. It turns company assumptions into deterministic business simulations, then layers executive intelligence on top of those outputs so users can interpret what the numbers mean.

The platform supports:

- Workspace-based company assumptions, Supabase-backed user workspaces, and company profiles
- Deterministic simulation of revenue, customers, cash, profit, runway, churn, and CAC efficiency
- Scenario comparison across Base Case, Growth Push, and Cost Optimization
- Executive advisor guidance and strategic intelligence generated from existing outputs
- Professional JSON and PDF report exports for downstream use and executive review

## Current Capabilities

StrategixAI currently supports:

- Deterministic business simulation
- Scenario comparison
- Executive recommendations
- Business Health Score
- Strategic Signals
- Risk Radar
- Workspace-based company management
- Supabase Authentication
- User-specific workspace isolation
- Supabase-backed custom company persistence
- JSON imports
- Executive PDF reporting
- JSON report exports

Current Version: Phase 8.1 Complete (Google Sign-In and email/password auth via Supabase Auth)

## Phase 8 Supabase Setup

Phase 8 uses Google Sign-In and email/password authentication through Supabase Auth, plus Supabase Postgres for user-owned custom company workspaces. Demo and sample companies remain bundled with the app and visible to every authenticated user.

Local secrets are read from Streamlit secrets and must not be committed:

```toml
[supabase]
url = "https://YOUR_PROJECT.supabase.co"
anon_key = "YOUR_SUPABASE_ANON_KEY"

[auth_cookies]
password = "SET_A_LONG_RANDOM_COOKIE_ENCRYPTION_SECRET"

[auth]
redirect_url = "http://localhost:8501"
```

Use `.streamlit/secrets.example.toml` as the template for local setup. Supabase access and refresh tokens are persisted in encrypted browser cookies so refreshes keep the user signed in until Logout; tokens are not placed in URL query parameters or local JSON files. Set a strong `auth_cookies.password` value for cookie encryption. Run `supabase/schema.sql` in the Supabase SQL editor before using custom company persistence.

Google Sign-In setup:

1. Create a Google OAuth client in Google Cloud Console.
2. Add authorized redirect URI: `https://hlbmvljdarwjpuubanvu.supabase.co/auth/v1/callback`.
3. Enable Google in Supabase Authentication -> Sign In / Providers.
4. Add the Google Client ID and Client Secret in Supabase.
5. Add local redirect URL in Supabase: `http://localhost:8501`.
6. Add the deployed app redirect URL later when deployment is ready.

Email/password auth uses Supabase Authentication's built-in email provider. Keep it enabled in Supabase if users should be able to register and log in without Google.

## Why This Project Exists

Founders, product managers, consultants, business analysts, and finance teams often need fast scenario-based decision intelligence. In practice, that work is usually spread across spreadsheets, slide decks, and opinion-heavy reviews that are difficult to audit or reproduce.

StrategixAI addresses that gap by combining:

- Deterministic business calculations
- Executive-level interpretation of those calculations
- Workspace-based assumption management
- Explainable reporting and export workflows

It is designed to answer questions like:

- Which scenario performs best?
- What is the business health of the current plan?
- Which risks deserve attention first?
- What should the executive team do next?

## Who Is It For?

StrategixAI is designed for:

- Startup founders
- Product managers
- Strategy teams
- Consultants
- Business analysts
- MBA students
- Finance and operations teams

## Key Features

- Deterministic simulation engine that produces reproducible forecast output from structured company assumptions.
- SaaS and startup-style KPI forecasting for revenue, ARR, net income, customers, churn, CAC, LTV/CAC, runway, and breakeven.
- Scenario comparison across Base Case, Growth Push, and Cost Optimization.
- Executive advisor recommendations with confidence scoring and scenario-alignment reasoning.
- Business Health Score from 0 to 100.
- Strategic Signals grouped into Growth Signals, Risk Signals, Efficiency Signals, and Cash Signals.
- Risk Radar covering Growth Risk, Profitability Risk, Runway Risk, and Retention Risk.
- Top Recommended Actions focused on the highest-priority deterministic actions.
- Scenario Winner Analysis explaining why a scenario wins.
- Multi-company workspace selector for switching between local company profiles.
- Custom company creation.
- Custom company editing and deletion.
- JSON company import.
- Dark/light theme support.
- Professional sidebar and navigation.
- Executive PDF export.
- Structured JSON report export.

## Project Metrics

Completed Phases: 8

Core Services:
- Dashboard Service
- Comparison Service
- Workspace Service
- Company Ingestion Service
- Strategic Intelligence Service
- Report Service
- Authentication Service
- Supabase Workspace Service

Export Formats:
- JSON
- PDF

Supported Scenarios:
- Base Case
- Growth Push
- Cost Optimization

## Completed Phase Roadmap

### Phase 1 - Simulation Engine

- Built the deterministic simulation core.
- Forecasted revenue, customers, cash, profit, runway, and breakeven over a configurable horizon.
- Produced repeatable KPI outputs from structured company assumptions.
- Established the numeric foundation used by every later phase.

### Phase 2 - Scenario Comparison

- Added deterministic comparison across Base Case, Growth Push, and Cost Optimization.
- Compared scenarios on revenue, customers, profit, cash, breakeven, and unit economics.
- Supported side-by-side strategic decision making from the same simulation framework.
- Reused simulation outputs rather than recalculating alternate business logic.

### Phase 3 - Executive Advisor

- Added an executive advisory layer on top of the deterministic outputs.
- Generated strategic recommendations and confidence scoring.
- Identified scenario alignment and operating baseline guidance.
- Kept recommendations explainable and based on existing calculations.

### Phase 4 - Multi-Company Workspace Architecture

- Introduced workspace-based company isolation.
- Added support for multiple local company profiles.
- Wired workspace selection into dashboard payload generation.
- Allowed each company to maintain its own assumptions and outputs.

### Phase 5 - Workspace Management

- Added custom company creation from manual assumptions.
- Added custom company editing and deletion.
- Added JSON company import.
- Added workspace lifecycle management for local company data.

### Phase 6 - Strategic Intelligence

- Added Business Health Score.
- Added health classification.
- Added Strategic Signals.
- Added Risk Radar.
- Added Top 3 Recommended Actions.
- Added Scenario Winner Analysis.
- Kept the scoring and reasoning deterministic and explainable.

### Phase 7 - Executive Reporting & Export

- Added structured JSON export for downstream processing.
- Added professional PDF export for executive and boardroom review.
- Included report metadata, KPI snapshot, simulation summary, comparison summary, risk summary, findings, and recommendation outputs.
- Added branded PDF styling with cover page, headers, footers, and section hierarchy.
- Reused existing simulation, comparison, and intelligence outputs without duplicating business logic.

### Phase 8 - Authentication & Workspace Isolation

- Added Google Sign-In and email/password authentication via Supabase Authentication.
- Kept Supabase-issued sessions for RLS-backed workspace isolation.
- Added cookie-backed user session persistence across browser refresh.
- Added logout functionality that clears Supabase session state and auth cookies.
- Added Supabase-backed custom company persistence.
- Added user-owned workspace isolation.
- Added Row Level Security (RLS) policies for user-owned data.
- Preserved globally available demo and sample companies.
- Prepared authentication and persistence architecture for deployment.

## Next Major Milestone

Phase 9: Gemini AI Copilot

Planned Deliverables:
- AI executive strategy assistant
- Scenario interpretation
- KPI explanation
- Strategic recommendation generation
- Executive Q&A over simulation outputs

## Current V1 Roadmap / Remaining Work

### V1 Remaining

- Gemini AI Copilot
- Deployment and production hardening
- Final documentation and screenshots

### V2 Roadmap

- Portfolio intelligence
- Multi-company benchmarking
- Industry benchmarking
- Historical simulation tracking
- Portfolio comparison dashboard

Company comparison and portfolio intelligence are deferred to V2, not current V1 completion.

## Architecture

StrategixAI follows a modular Python architecture:

- `app.py` orchestrates the Streamlit UI and connects workspace, dashboard, intelligence, and export flows.
- `analytics/` contains the business services for dashboard payloads, scenario comparison, workspace management, company ingestion, strategic intelligence, and reporting.
- `models/` contains Pydantic schema definitions and typed contracts.
- `engine/` contains the deterministic simulation engine.
- `data/` contains bundled sample company profiles.
- User-owned custom company workspaces are persisted through Supabase Postgres.
- `tests/` provides regression coverage for the simulation, comparison, advisory, workspace, ingestion, intelligence, and reporting layers.

Simple flow:

```txt
User Input / Workspace
        ↓
Dashboard Service
        ↓
Deterministic Simulation Engine
        ↓
Scenario Comparison + Strategic Intelligence
        ↓
Executive Advisor + Export Service
        ↓
Streamlit UI + PDF / JSON Reports
```

## Project Structure

```txt
StrategixAI/
├── app.py
├── analytics/
├── engine/
├── models/
├── data/
├── supabase/
├── .streamlit/
├── tests/
├── requirements.txt
└── README.md
```

- `app.py` - Streamlit application entry point and UI orchestration.
- `analytics/` - dashboard, comparison, workspace, ingestion, strategic intelligence, and reporting services.
- `engine/` - deterministic simulation logic.
- `models/` - Pydantic schemas and data contracts.
- `data/` - sample company profiles and local custom company storage.
- `supabase/` - database schema and deployment assets.
- `.streamlit/` - local configuration and secrets templates.
- `tests/` - deterministic regression tests.
- `requirements.txt` - Python dependency list.
- `README.md` - project documentation.

## Reporting System

Phase 7 adds professional reporting on top of existing simulation and intelligence outputs.

### JSON Export

- Structured JSON for downstream use and programmatic consumption.
- Includes report metadata, company data, KPI snapshot, simulation summary, strategic intelligence, scenario comparison summary, key findings, top risks, and strategic recommendation.

### PDF Export

- Executive-grade PDF built for boardroom review.
- Includes a cover page, executive summary, KPI snapshot, simulation summary, business health score, strategic signals, risk radar, recommended actions, scenario winner analysis, scenario comparison summary, key findings, top risks, and final strategic recommendation.
- Includes branded footer treatment and copyright.
- Uses deterministic, locally generated formatting and does not depend on external AI APIs.

## Testing

Current report and core regression tests:

- `tests/test_simulation.py`
- `tests/test_comparison.py`
- `tests/test_executive_advisor.py`
- `tests/test_workspace_service.py`
- `tests/test_company_ingestion.py`
- `tests/test_report_service.py`
- `tests/test_auth_service.py`
- `tests/test_supabase_workspace_service.py`

Run them with:

```powershell
python tests/test_auth_service.py
python tests/test_supabase_workspace_service.py
python tests/test_simulation.py
python tests/test_comparison.py
python tests/test_executive_advisor.py
python tests/test_workspace_service.py
python tests/test_company_ingestion.py
python tests/test_report_service.py
```

## How To Run Locally

This project is currently developed on Windows PowerShell.

```powershell
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

## Export Usage

1. Run the dashboard with `streamlit run app.py`.
2. Review the simulation outputs and strategic intelligence sections.
3. Scroll to the Export Center.
4. Download the JSON report or the PDF report.

## Tech Stack

### Backend
- Python
- Pandas
- Pydantic

### Frontend
- Streamlit
- Custom CSS UI System

### Analytics
- Deterministic Simulation Engine
- Strategic Intelligence Engine
- Scenario Comparison Engine

### Reporting
- JSON Export
- PDF Export Service

### Authentication & Persistence

- Supabase Auth
- Encrypted Streamlit browser cookies for auth token persistence
- Supabase Postgres
- Row Level Security (RLS)

### Development
- Git
- GitHub
- Pytest-style regression tests

## Screenshots

Screenshots will be added after final V1 UI polish.

## Future Enhancements

- Gemini AI Copilot
- Cloud persistence
- Deployed public demo
- Portfolio/company comparison in V2
- Industry benchmarking in V2
- Historical simulation runs
- Better report templates

## Project Status

Current Status: Phase 8.1 complete - Google Sign-In and email/password auth via Supabase Auth implemented.

Next Phase: Gemini AI Copilot.

## Author

Built by Aditya Vijay Athawale


Keywords:
business-intelligence, strategy, analytics, simulation, streamlit,
product-management, consulting, saas, startup, dashboard, forecasting
