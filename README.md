# StrategixAI

**A deterministic executive strategy intelligence platform for company workspaces, business simulations, scenario comparison, and boardroom-ready strategic insight.**

StrategixAI helps founders, operators, consultants, product leaders, analytics teams, and finance stakeholders evaluate strategic decisions before committing capital. The platform converts company assumptions into deterministic simulations, compares strategic scenarios, and generates explainable executive intelligence without relying on external AI APIs.

After Phase 6, StrategixAI lets users:

- Create and manage company workspaces.
- Run business simulations from validated assumptions.
- Compare strategic scenarios.
- Generate executive insights.
- Calculate a Business Health Score.
- View strategic signals.
- View a Risk Radar.
- Receive the top recommended actions.
- Identify why a scenario wins through Scenario Winner Analysis.

---

## Why This Project Exists

Strategic planning often lives across spreadsheets, static dashboards, disconnected slide decks, and subjective executive discussions. That makes it difficult to compare scenarios, validate assumptions, and explain tradeoffs clearly.

StrategixAI addresses that gap by turning operating assumptions into structured business outcomes:

- Forecast revenue, customers, cash, profitability, runway, and breakeven.
- Compare multiple deterministic strategy scenarios side by side.
- Identify the strongest operating baseline using measurable business signals.
- Generate executive-grade recommendations, risks, opportunities, and confidence scoring.
- Surface strategic intelligence such as business health, risk radar, signals, and top actions.
- Keep simulation, analytics, advisory, and intelligence logic modular and testable.

---

## Current Features

- **Deterministic Simulation Engine**  
  Models revenue, customer growth, cash balance, net income, breakeven timing, runway, and executive KPIs over configurable forecast horizons.

- **Scenario Comparison**  
  Compares Base Case, Growth Push, and Cost Optimization strategies across revenue, profitability, customers, cash balance, breakeven, and LTV/CAC.

- **Executive Dashboard**  
  Streamlit dashboard with executive KPI cards, scenario controls, comparison tables, Plotly charts, boardroom summaries, and responsive layout.

- **Executive Advisor**  
  Produces deterministic strategic recommendations, confidence scores, scenario alignment status, risk watchouts, opportunity areas, and operating baseline guidance.

- **Multi-Company Workspace Architecture**  
  Supports independent local company workspaces with isolated assumptions, dashboard payloads, scenario comparisons, and executive outputs.

- **Custom Company Creation**  
  Lets users create validated custom company workspaces from manual business assumptions.

- **JSON Company Import**  
  Supports importing compatible company workspace JSON files.

- **Workspace Lifecycle Management**  
  Supports local workspace creation, loading, updating, deletion, and selector-based switching.

- **Strategic Intelligence Engine**  
  Generates deterministic executive intelligence from simulation outputs and scenario comparison results.

- **Business Health Score**  
  Calculates a 0-100 explainable health score using growth, profitability, runway, churn, and CAC efficiency.

- **Risk Radar**  
  Scores Growth Risk, Profitability Risk, Runway Risk, and Retention Risk.

- **Strategic Signals**  
  Surfaces Growth Signals, Risk Signals, Efficiency Signals, and Cash Signals.

- **Top 3 Recommended Actions**  
  Prioritizes the highest-impact deterministic actions from the active simulation.

- **Scenario Winner Analysis**  
  Explains why the strongest scenario wins across revenue, profitability, customer growth, cash, breakeven, and CAC efficiency dimensions.

- **Dark/Light Theme**  
  Provides premium dark and light dashboard themes.

---

## Product Phases

| Phase | Status | Scope |
| --- | --- | --- |
| Phase 1 | Complete | Deterministic Simulation Engine |
| Phase 2 | Complete | Scenario Comparison |
| Phase 3 | Complete | Executive Dashboard and Executive Advisor |
| Phase 4 | Complete | Multi-Company Workspace Architecture |
| Phase 5 | Complete | Company Management and Workspace Lifecycle |
| Phase 6 | Complete | Strategic Intelligence Engine |

### Phase 1: Deterministic Simulation Engine

Completed capabilities:

- Revenue forecasting
- Customer growth forecasting
- Cash balance projection
- Net income analysis
- Runway calculation
- Breakeven detection
- KPI generation

### Phase 2: Scenario Comparison

Completed scenarios:

- Base Case
- Growth Push
- Cost Optimization

Completed comparison dimensions:

- Revenue comparison
- Profitability comparison
- Customer comparison
- Cash balance comparison
- Breakeven comparison
- LTV/CAC comparison

### Phase 3: Executive Dashboard and Advisor

Completed capabilities:

- Premium Streamlit executive dashboard
- Deterministic executive advisory layer
- Strategic recommendation engine
- Confidence scoring
- Scenario alignment detection
- Risk watchouts
- Opportunity areas
- Operating baseline recommendation

### Phase 4: Multi-Company Workspace Architecture

Completed capabilities:

- Company workspace schemas
- Local sample company profiles
- Workspace switching in the dashboard
- Company-specific dashboard payloads
- Company-specific scenario comparisons
- Company-specific executive advisor outputs
- Demo SaaS fallback workspace

Current sample workspaces:

- Northstar SaaS
- MarketBridge Marketplace
- RetailX D2C
- FinEdge FinTech
- LearnLoop EdTech

### Phase 5: Company Management and Workspace Lifecycle

Completed capabilities:

- Custom company creation from manual assumptions
- Validated company assumptions
- Local JSON persistence in `data/custom_companies/`
- Custom workspace loading through the existing selector
- Compatible company workspace JSON import
- Workspace update and deletion flows

### Phase 6: Strategic Intelligence Engine

Completed capabilities:

- Business Health Score
- Health classification
- Strategic Signals
- Executive verdict
- Top 3 Recommended Actions
- Risk Radar
- Scenario Winner Analysis
- Deterministic, explainable calculations

Authentication, deployment, AI/LLM integrations, portfolio/company comparison, benchmarking, and cloud infrastructure are not implemented in the current version.

---

## Architecture

Simple product flow:

```txt
Company Workspace
-> Simulation Engine
-> Scenario Comparison
-> Executive Advisor
-> Strategic Intelligence Engine
-> Dashboard Output
```

Repository structure:

```txt
StrategixAI
|
|-- app.py
|   |-- Streamlit dashboard
|   |-- Scenario controls
|   |-- KPI cards
|   |-- Plotly charts
|   |-- Scenario comparison section
|   |-- Executive Advisor rendering
|   `-- Strategic Intelligence rendering
|
|-- models/
|   |-- business_schema.py
|   |-- company_schema.py
|   |-- scenario_schema.py
|   |-- metrics_schema.py
|   |-- comparison_schema.py
|   |-- intelligence_schema.py
|   `-- ai_schema.py
|
|-- engine/
|   `-- simulation_engine.py
|
|-- analytics/
|   |-- company_ingestion_service.py
|   |-- dashboard_service.py
|   |-- comparison_service.py
|   |-- strategic_intelligence_service.py
|   `-- workspace_service.py
|
|-- ai/
|   `-- executive_advisor.py
|
|-- data/
|   |-- sample_companies/
|   `-- custom_companies/
|
|-- tests/
|   |-- test_simulation.py
|   |-- test_comparison.py
|   |-- test_executive_advisor.py
|   |-- test_workspace_service.py
|   |-- test_company_ingestion.py
|   `-- test_strategic_intelligence.py
|
`-- requirements.txt
```

### Data Flow

```txt
Company Workspace + Scenario + Forecast Horizon
        |
        v
Workspace Service / Dashboard Service
        |
        v
Deterministic Simulation Engine
        |
        v
Scenario Comparison + Analytics Payload
        |
        v
Executive Advisor + Strategic Intelligence Engine
        |
        v
Streamlit Dashboard Output
```

---

## Tech Stack

| Area | Technology |
| --- | --- |
| Language | Python |
| UI | Streamlit |
| Charts | Plotly |
| Data Processing | pandas, NumPy |
| Data Validation | Pydantic |
| Simulation | Custom deterministic engine |
| Advisory Layer | Deterministic rule-based executive advisor |
| Intelligence Layer | Deterministic strategic intelligence service |
| Testing | Python test scripts |

---

## How To Run Locally

Create and activate a virtual environment, then install dependencies:

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Run the Streamlit dashboard:

```powershell
streamlit run app.py
```

If using the existing virtual environment:

```powershell
.\venv\Scripts\Activate.ps1
streamlit run app.py
```

---

## Testing

Run the core test scripts:

```powershell
python tests/test_simulation.py
python tests/test_comparison.py
python tests/test_executive_advisor.py
python tests/test_workspace_service.py
python tests/test_company_ingestion.py
python tests/test_strategic_intelligence.py
```

The tests validate deterministic simulation output, scenario comparison behavior, Executive Advisor recommendation logic, local workspace loading, custom company ingestion, and Strategic Intelligence scoring/verdict generation.

---

## Roadmap

### V1 Remaining

- README and documentation polish
- Screenshots
- Deployment
- Report/export features if planned

### V2 Later

- Company comparison / portfolio intelligence
- Benchmarking
- AI copilot
- Authentication

---

## Portfolio Relevance

StrategixAI demonstrates applied capability across:

- Business decision intelligence
- Financial modeling
- SaaS metrics and unit economics
- Strategic scenario planning
- Product analytics
- Executive dashboard design
- Modular Python engineering
- AI-ready system architecture
- Explainable deterministic analytics

The project is designed to be reviewed by consulting, product management, analytics, and finance recruiters as a portfolio-grade example of turning business strategy questions into a structured software product.
