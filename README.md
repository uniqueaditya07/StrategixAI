# StrategixAI

**An AI-powered business decision intelligence platform for simulating strategic scenarios, comparing business outcomes, and generating executive-grade recommendations.**

StrategixAI helps founders, operators, consultants, product leaders, analytics teams, and finance stakeholders evaluate strategic decisions before committing capital. The platform combines deterministic business simulation, scenario comparison, executive KPI analysis, and a rule-based advisory layer designed for boardroom-style decision support.

The current product includes completed Phase 1, Phase 2, and Phase 3 capabilities: a deterministic simulation engine, a scenario comparison engine, and an executive advisor that translates simulation outcomes into strategic recommendations.

---

## Why This Project Exists

Strategic planning often lives across spreadsheets, static dashboards, disconnected slide decks, and subjective executive discussions. That makes it difficult to compare scenarios, validate assumptions, and explain tradeoffs clearly.

StrategixAI addresses that gap by turning operating assumptions into structured business outcomes:

- Forecast revenue, customers, cash, profitability, and breakeven.
- Compare multiple deterministic strategy scenarios side by side.
- Identify the strongest operating baseline using measurable business signals.
- Generate executive-grade recommendations, risks, opportunities, and confidence scoring.
- Keep simulation, analytics, and advisory logic modular and testable.

---

## Core Capabilities

- **Deterministic Simulation Engine**  
  Models revenue, customer growth, cash balance, net income, breakeven timing, and executive KPIs over configurable forecast horizons.

- **Scenario Comparison Engine**  
  Compares Base Case, Growth Push, and Cost Optimization strategies across revenue, profitability, customers, cash balance, breakeven, and LTV/CAC.

- **Executive Advisor**  
  Produces deterministic strategic recommendations, confidence scores, scenario alignment status, risk watchouts, opportunity areas, and operating baseline guidance.

- **Premium Executive Dashboard**  
  Streamlit dashboard with dark B2B SaaS styling, KPI cards, scenario controls, comparison tables, Plotly charts, and boardroom-oriented summary sections.

- **Modular Architecture**  
  Business schemas, simulation logic, analytics services, comparison outputs, and advisory logic are separated into focused Python modules.

---

## Completed Phases

### Phase 1: Deterministic Simulation Engine

Completed capabilities:

- Revenue forecasting
- Customer growth forecasting
- Cash balance projection
- Net income analysis
- Breakeven detection
- KPI generation

### Phase 2: Scenario Comparison Engine

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

### Phase 3: Executive Advisor

Completed advisory capabilities:

- Deterministic executive advisory layer
- Strategic recommendation engine
- Confidence scoring
- Scenario alignment detection
- Risk watchouts
- Opportunity areas
- Operating baseline recommendation
- Boardroom-style decision support

---

## Current Architecture

```txt
StrategixAI
|
|-- app.py
|   |-- Streamlit dashboard
|   |-- Scenario controls
|   |-- KPI cards
|   |-- Plotly charts
|   |-- Scenario comparison section
|   `-- Executive Advisor rendering
|
|-- models/
|   |-- business_schema.py
|   |-- scenario_schema.py
|   |-- metrics_schema.py
|   |-- comparison_schema.py
|   `-- ai_schema.py
|
|-- engine/
|   `-- simulation_engine.py
|
|-- analytics/
|   |-- dashboard_service.py
|   `-- comparison_service.py
|
|-- ai/
|   `-- executive_advisor.py
|
|-- tests/
|   |-- test_simulation.py
|   |-- test_comparison.py
|   `-- test_executive_advisor.py
|
`-- requirements.txt
```

### Data Flow

```txt
Business Model + Scenario + Forecast Horizon
        |
        v
Dashboard Service
        |
        v
Deterministic Simulation Engine
        |
        v
Analytics Payload + Scenario Comparison
        |
        v
Executive Advisor
        |
        v
Streamlit Dashboard
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
```

The tests validate deterministic simulation output, scenario comparison behavior, and Executive Advisor recommendation logic.

---

## Roadmap

### Completed

- Phase 1: Simulation Engine
- Phase 2: Scenario Comparison Engine
- Phase 3: Executive Advisor

### Upcoming

- Phase 4: Multi-Company Workspace Engine
- Phase 5: Gemini-Powered Strategy Consultant
- Phase 6: What-If Decision Lab
- Phase 7: Boardroom Reports
- Phase 8: SaaS Deployment

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

The project is designed to be reviewed by consulting, product management, analytics, and finance recruiters as a portfolio-grade example of turning business strategy questions into a structured software product.
