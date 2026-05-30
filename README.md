# StrategixAI

**AI-powered business strategy and decision intelligence platform for executive forecasting, SaaS simulation, and boardroom-ready analytics.**

StrategixAI is a premium analytics application that helps operators, founders, consultants, and finance teams model strategic business decisions before they commit capital. The project combines validated business schemas, a deterministic simulation engine, analytics-ready KPI transformations, and a polished Streamlit dashboard designed for executive decision-making.

> Current state: StrategixAI ships with a working deterministic SaaS simulation, analytics payload service, and Streamlit dashboard. AI advisory, persistence, and advanced scenario comparison are planned extensions supported by existing schema foundations.

---

## Project Overview

StrategixAI models how business assumptions translate into financial outcomes over time. It focuses on the questions leadership teams ask before making high-impact decisions:

- How quickly can this company grow under current acquisition economics?
- When does the business reach breakeven?
- How does cash runway change as marketing spend, churn, pricing, and costs evolve?
- Which operating metrics need attention before scaling?
- How can simulation outputs be converted into executive-grade insights?

The application is structured as a modular Python product rather than a single notebook or throwaway dashboard. Business contracts live in Pydantic schemas, simulation logic lives in the engine layer, analytics transformations sit behind the UI, and the Streamlit app only renders the experience.

---

## Business Problem

Strategic planning is often split across spreadsheets, static slides, disconnected dashboards, and generic AI summaries. This creates several problems:

- Assumptions are hard to validate and compare.
- Financial models are difficult to reuse across scenarios.
- KPI definitions drift between teams.
- Executive summaries often lack direct links to operating metrics.
- Strategy discussions become opinion-driven instead of evidence-driven.

StrategixAI addresses this by turning business assumptions into structured simulation outputs, analytics views, and future AI-generated recommendations.

---

## Key Features

- **Validated business assumptions** using strict Pydantic models for pricing, marketing, churn, costs, and scenarios.
- **Deterministic SaaS simulation engine** for month-by-month revenue, customer, cash, profitability, CAC, LTV, and runway modeling.
- **Executive KPI dashboard** with premium dark UI, high-level boardroom metrics, and Plotly trend charts.
- **Analytics orchestration layer** that converts simulation results into dashboard-ready payloads and DataFrames.
- **Scenario-ready architecture** with schemas for run requests, scenario status, Monte Carlo configuration, sensitivity variables, and comparisons.
- **AI advisory contracts** for executive summaries, risk analysis, and strategic recommendations.
- **Portfolio-grade separation of concerns** across models, engine, analytics, AI, visuals, database, config, and utilities.

---

## System Architecture

```txt
+--------------------------------------------------------------------+
|                            Streamlit UI                            |
|                                                                    |
|  app.py                                                            |
|  - Executive dashboard                                             |
|  - KPI cards                                                       |
|  - Plotly charts                                                   |
|  - Demo scenario controls                                          |
+--------------------------------^-----------------------------------+
                                 |
                                 | dashboard payload
                                 |
+--------------------------------+-----------------------------------+
|                         Analytics Layer                            |
|                                                                    |
|  analytics/dashboard_service.py                                    |
|  - Builds demo SaaS scenario                                       |
|  - Runs simulation                                                 |
|  - Extracts latest KPIs                                            |
|  - Builds chart-ready DataFrames                                   |
+--------------------------------^-----------------------------------+
                                 |
                                 | scenario run request/result
                                 |
+--------------------------------+-----------------------------------+
|                        Simulation Engine                           |
|                                                                    |
|  engine/simulation_engine.py                                       |
|  - Customer acquisition                                            |
|  - Churn and reactivation                                          |
|  - Revenue and gross profit                                        |
|  - Operating expenses                                              |
|  - Cash balance and runway                                         |
|  - CAC, LTV, payback, breakeven                                    |
+--------------------------------^-----------------------------------+
                                 |
                                 | validated contracts
                                 |
+--------------------------------+-----------------------------------+
|                          Domain Models                             |
|                                                                    |
|  models/business_schema.py                                         |
|  models/scenario_schema.py                                         |
|  models/metrics_schema.py                                          |
|  models/ai_schema.py                                               |
+--------------------------------------------------------------------+

Planned Extensions
+----------------------+   +----------------------+   +--------------+
| AI Advisory Layer    |   | Persistence Layer    |   | Config Layer |
| ai/                  |   | database/            |   | config/      |
| summaries, risks,    |   | scenarios, results,  |   | settings,    |
| recommendations      |   | user history         |   | environments |
+----------------------+   +----------------------+   +--------------+
```

---

## Tech Stack

| Category | Tools |
| --- | --- |
| Application | Python, Streamlit |
| Data Modeling | Pydantic |
| Analytics | pandas, NumPy |
| Visualization | Plotly |
| Simulation | Custom deterministic engine |
| Persistence-ready | DuckDB |
| AI-ready | OpenAI SDK, Google Generative AI SDK |
| Data Science-ready | scikit-learn, statsmodels, matplotlib, seaborn |
| Environment | python-dotenv, virtualenv |

---

## Folder Structure

```txt
StrategixAI/
|-- ai/
|   `-- __init__.py
|-- analytics/
|   |-- __init__.py
|   `-- dashboard_service.py
|-- config/
|   `-- __init__.py
|-- database/
|   `-- __init__.py
|-- engine/
|   |-- __init__.py
|   `-- simulation_engine.py
|-- models/
|   |-- __init__.py
|   |-- ai_schema.py
|   |-- business_schema.py
|   |-- metrics_schema.py
|   `-- scenario_schema.py
|-- tests/
|   |-- __init__.py
|   `-- test_simulation.py
|-- utils/
|   `-- __init__.py
|-- visuals/
|   `-- __init__.py
|-- app.py
|-- DEVELOPMENT_RULES.md
|-- README.md
`-- requirements.txt
```

---

## Simulation Engine

The deterministic simulation engine converts a validated scenario into period-by-period business outcomes. It is designed to be reusable outside the UI and independent of Streamlit.

Core responsibilities:

- Accept a `ScenarioRunRequest` containing business assumptions and simulation configuration.
- Simulate each forecast period in sequence.
- Model paid, organic, and referral-driven customer acquisition.
- Apply logo churn and customer reactivation.
- Calculate active customers, revenue, gross profit, operating expenses, net income, burn rate, and cash balance.
- Calculate SaaS efficiency metrics including blended CAC, LTV, LTV/CAC ratio, payback period, net revenue retention, and runway.
- Return a validated `ScenarioRunResult` with full period outputs and summary metrics.

Example outputs include:

- Monthly recurring revenue
- Annual recurring revenue
- Active customers
- New customers
- Churned customers
- Cash balance
- Net income
- Breakeven period
- Cumulative revenue
- Ending cash balance

---

## Analytics Engine

The analytics layer prepares simulation results for executive reporting. It acts as the boundary between the engine and the user interface.

Current responsibilities:

- Build the demo SaaS base-case scenario.
- Run the deterministic simulation engine.
- Extract latest-period KPI values.
- Build revenue, customer, and cashflow DataFrames.
- Construct a consolidated dashboard payload consumed by `app.py`.
- Raise clear errors when simulation output is unavailable.

This design keeps analytics transformations separate from rendering, which makes the system easier to test, reuse, and extend into APIs, reports, or additional frontends.

---

## AI Advisory Layer

The AI advisory layer is currently represented by structured schemas in `models/ai_schema.py`. These contracts define the future shape of AI-generated strategy outputs.

Planned capabilities:

- Executive summaries grounded in simulation KPIs.
- Strategic recommendations across pricing, growth, retention, cost control, runway, fundraising, and operations.
- Risk analysis with severity, probability, impact, mitigation, and leading indicators.
- Recommendation confidence scoring.
- Boardroom-ready decision prompts for leadership teams.

The goal is not to build a generic chatbot. The AI layer should behave like a strategy advisor that explains tradeoffs, challenges weak assumptions, and ties recommendations back to measurable business outcomes.

---

## Screenshots

Add screenshots after running the Streamlit app locally.

### Executive Dashboard

```txt
Placeholder: screenshot of StrategixAI dashboard hero, KPI cards, and charts.
```

### Growth Model

```txt
Placeholder: screenshot of revenue and customer growth charts.
```

### Boardroom Snapshot

```txt
Placeholder: screenshot of cumulative revenue, net income, ending cash, and breakeven cards.
```

---

## Future Roadmap

- Move UI components and chart builders from `app.py` into reusable `visuals/` modules.
- Add interactive scenario inputs for pricing, churn, costs, marketing budgets, and forecast horizon.
- Add scenario comparison workflows for base case, upside, downside, aggressive growth, and conservative plans.
- Implement sensitivity analysis for churn, CAC, ARPU, growth rate, and fixed cost assumptions.
- Add Monte Carlo simulation support using the existing configuration schema.
- Build persistence for saved scenarios and historical simulation runs.
- Implement AI-generated executive summaries, strategic recommendations, and risk analysis.
- Add exportable reports for board decks, investor updates, and consulting-style strategy memos.
- Expand automated tests with assertion-based unit tests and analytics integration tests.
- Package the application for deployment.

---

## Resume Bullet Points

- Built a modular AI-powered strategy intelligence platform using Python, Streamlit, Pydantic, pandas, and Plotly to simulate SaaS growth, profitability, CAC, LTV, runway, and breakeven outcomes.
- Designed strict business, scenario, metrics, and AI advisory schemas with Pydantic to enforce clean contracts across simulation, analytics, and future recommendation workflows.
- Developed a deterministic financial simulation engine that models customer acquisition, churn, reactivation, recurring revenue, operating costs, cash balance, burn rate, and SaaS efficiency metrics over a 24-month horizon.
- Created an executive-grade Streamlit dashboard with dark premium UI, KPI cards, Plotly trend visualizations, and boardroom summary metrics for consulting, analytics, finance, and product strategy use cases.
- Separated application concerns across models, engine, analytics, UI, and planned AI/persistence layers to support maintainability, testing, and future product expansion.

---

## Author

**StrategixAI** was built as a portfolio-grade business strategy and analytics project demonstrating applied skills across:

- Product strategy
- Business analytics
- Financial modeling
- SaaS metrics
- Decision intelligence
- Python engineering
- Executive dashboard design
- AI-ready system architecture

For recruiters and reviewers, the project is intended to show the ability to turn ambiguous business strategy questions into a structured, reusable, and executive-facing software product.
