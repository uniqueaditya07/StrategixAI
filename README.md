# StrategixAI - AI Strategy Intelligence Platform

> **Simulate business decisions. Compare strategic scenarios. Generate executive intelligence. Make better decisions.**

StrategixAI is an AI-powered Strategy Intelligence Platform designed to help founders, consultants, product managers, MBA students, business analysts, and decision-makers evaluate business strategies before committing resources.

The platform combines deterministic business simulation, scenario comparison, strategic intelligence, executive reporting, workspace management, and secure user authentication into a unified decision-support environment.

---

# Executive Summary

Organizations make critical strategic decisions every day:

* Expanding into new markets
* Hiring aggressively
* Optimizing costs
* Raising capital
* Launching products
* Adjusting pricing
* Managing cash flow

These decisions are often driven by spreadsheets, assumptions, presentations, and subjective discussions.

StrategixAI transforms this process into a structured, explainable, and repeatable decision-support workflow.

Users can:

* Simulate business outcomes
* Compare alternative strategies
* Evaluate financial impact
* Analyze risk exposure
* Generate executive recommendations
* Export boardroom-ready reports
* Maintain secure company workspaces
* Store and manage historical reports

StrategixAI bridges the gap between traditional business analytics and executive decision support.

---

# Business Problem

Strategic decision-making is frequently fragmented across:

* Excel spreadsheets
* Financial models
* PowerPoint presentations
* Team discussions
* Departmental assumptions
* Static dashboards

This creates several challenges:

### Lack of Reproducibility

Different stakeholders often arrive at different conclusions using different assumptions.

### Poor Strategic Visibility

Decision-makers struggle to understand tradeoffs between growth, profitability, efficiency, and cash preservation.

### Slow Decision Cycles

Teams spend significant time preparing analyses instead of evaluating outcomes.

### Risk Blind Spots

Potential risks often remain hidden until execution begins.

### Limited Scenario Evaluation

Organizations rarely compare multiple strategies side-by-side using consistent assumptions.

StrategixAI solves these challenges through deterministic simulation and explainable strategic intelligence.

---

# Strategic Value

StrategixAI enables organizations to:

* Evaluate growth strategies before execution
* Understand financial tradeoffs
* Compare operating plans
* Detect risks early
* Prioritize executive actions
* Improve planning quality
* Generate professional executive reports
* Create repeatable strategic workflows

The platform supports both operational planning and executive decision-making.

---

# Product Vision

StrategixAI is designed as a decision-support platform rather than a generic chatbot.

Instead of producing vague advice, the platform:

1. Accepts structured business assumptions
2. Executes deterministic simulations
3. Generates measurable outcomes
4. Compares strategic scenarios
5. Produces explainable recommendations
6. Generates executive intelligence
7. Creates boardroom-ready reports

Every recommendation is grounded in simulation outputs and measurable business metrics.

---

# Who Is It For?

StrategixAI is designed for:

### Founders & Startup Teams

* Evaluate growth plans
* Analyze runway
* Understand unit economics

### Product Managers

* Assess business impact
* Evaluate growth initiatives
* Analyze strategic tradeoffs

### Consultants

* Build scenario analyses
* Present strategic recommendations
* Support client decision-making

### Business Analysts

* Forecast business performance
* Evaluate operating plans
* Analyze risks

### MBA Students

* Learn business strategy
* Explore financial tradeoffs
* Practice executive decision-making

### Corporate Strategy Teams

* Conduct scenario planning
* Analyze business performance
* Generate executive reports

---

# Core Platform Capabilities

## 1. Deterministic Business Simulation

StrategixAI uses deterministic calculations to produce reproducible forecasts.

Supported metrics:

* Revenue
* ARR
* Customers
* Net Income
* Cash Balance
* Runway
* Churn
* CAC
* LTV
* LTV/CAC
* Breakeven Point

Outputs remain consistent for identical inputs.

---

## 2. Strategic Scenario Comparison

Users can compare multiple business strategies side-by-side.

### Base Case

Current operating assumptions.

### Growth Push

Aggressive growth-oriented strategy.

### Cost Optimization

Efficiency-focused strategy.

Comparison includes:

* Revenue
* Customers
* Profitability
* Cash Position
* Breakeven
* Unit Economics
* Business Health

---

## 3. Strategic Intelligence Engine

The Strategic Intelligence Engine transforms simulation outputs into executive insights.

### Business Health Score

0–100 overall health evaluation.

### Strategic Signals

Categorized into:

* Growth Signals
* Risk Signals
* Efficiency Signals
* Cash Signals

### Risk Radar

Evaluates:

* Growth Risk
* Profitability Risk
* Runway Risk
* Retention Risk

### Recommended Actions

Generates explainable recommendations based on simulation results.

### Scenario Winner Analysis

Identifies the strongest strategic option based on performance indicators.

---

## 4. Executive Reporting System

StrategixAI generates boardroom-ready executive reports.

### PDF Reports

Include:

* Executive Summary
* KPI Dashboard
* Business Health Analysis
* Strategic Signals
* Risk Radar
* Recommendations
* Scenario Comparison
* Strategic Conclusions

### JSON Reports

Include:

* Metadata
* KPI Snapshot
* Strategic Intelligence
* Recommendations
* Risk Analysis
* Report Data

---

## 5. Saved Reports Management

StrategixAI includes a persistent executive report library.

Capabilities:

* Saved Reports Dashboard
* Report History
* Report Preview
* PDF Downloads
* JSON Downloads
* Report Deletion
* Duplicate Prevention
* Firestore Persistence

Reports remain available across sessions.

---

## 6. Workspace Management

Supports:

* Multi-company workspaces
* Workspace switching
* Custom company creation
* Company editing
* Company deletion
* JSON imports

Each workspace maintains its own assumptions and simulations.

---

## 7. Authentication & User System

### Firebase Authentication

* Google Sign-In
* Secure Login
* Persistent Sessions

### User Profiles

Stores:

* User Information
* Onboarding Preferences
* Simulation History
* Saved Reports

### Protected Routes

Authentication required for:

* Dashboard
* Scenario Comparison
* Saved Reports
* Workspace Management
* Future AI Copilot

---

# High-Level Architecture

```text
User
   ↓
Authentication Layer
   ↓
Workspace Layer
   ↓
Simulation Engine
   ↓
Scenario Comparison Engine
   ↓
Strategic Intelligence Engine
   ↓
Reporting Engine
   ↓
Executive Dashboard
```

---

# Authentication Architecture

```text
User
   ↓
Google Sign-In
   ↓
Firebase Authentication
   ↓
Firebase ID Token
   ↓
Flask Auth Helper
   ↓
Firebase Admin Verification
   ↓
Firestore User Profile
   ↓
Protected StrategixAI Workspace
```

---

# Firestore Data Model

```text
users/
└── {uid}
    ├── profile
    ├── simulations/
    │   └── {simulationId}
    └── reports/
        └── {reportId}
```

---

# Saved Reports Architecture

```text
Executive Report
        ↓
Save Report
        ↓
Firestore
        ↓
users/{uid}/reports/{reportId}
        ↓
Saved Reports Dashboard
        ↓
Preview / PDF / JSON / Delete
```

User-owned data is protected through Firebase Authentication and Firestore Security Rules.

---

# Technology Stack

## Backend

* Python
* Flask
* Firebase Admin SDK
* Pydantic
* Pandas

## Frontend

* Streamlit
* Custom CSS

## Database

* Firestore

## Authentication

* Firebase Authentication
* Google OAuth

## Analytics

* Simulation Engine
* Strategic Intelligence Engine
* Scenario Comparison Engine

## Reporting

* PDF Export
* JSON Export

## Development

* Git
* GitHub

---

# Skills Demonstrated

## Product Management

* KPI Design
* Product Thinking
* User Workflow Design
* Decision Support Systems

## Strategy & Consulting

* Scenario Analysis
* Strategic Planning
* Business Intelligence
* Executive Reporting
* Risk Assessment

## Data & Analytics

* Forecasting
* KPI Analysis
* Business Metrics
* Simulation Modeling

## Software Engineering

* Python Development
* Streamlit Applications
* Flask APIs
* Firebase Authentication
* Firestore Integration
* Software Architecture
* Secure Authentication Systems

---

# Project Metrics

### Completed Phases

**8 / 11**

### Core Services

* Dashboard Service
* Comparison Service
* Workspace Service
* Company Ingestion Service
* Strategic Intelligence Service
* Report Service
* Authentication Service

### Export Formats

* PDF
* JSON

### Authentication Features

* Google OAuth
* Persistent Sessions
* User Profiles
* Protected Routes
* Saved Reports

### Reporting Features

* Executive Reports
* Report History
* Report Preview
* PDF Downloads
* JSON Downloads

### Supported Scenarios

* Base Case
* Growth Push
* Cost Optimization

---

# Development Roadmap

## Phase 1 – Simulation Engine ✅

* Deterministic simulation core
* Revenue forecasting
* Customer forecasting
* Profit forecasting
* Cash forecasting
* Runway forecasting

## Phase 2 – Scenario Comparison ✅

* Multi-scenario evaluation
* KPI comparison framework
* Scenario winner identification

## Phase 3 – Executive Advisor ✅

* Strategic recommendations
* Confidence scoring
* Explainable reasoning

## Phase 4 – Multi-Company Architecture ✅

* Workspace isolation
* Company-specific assumptions
* Workspace selection

## Phase 5 – Workspace Management ✅

* Create companies
* Edit companies
* Delete companies
* Import companies

## Phase 6 – Strategic Intelligence ✅

* Business Health Score
* Strategic Signals
* Risk Radar
* Recommended Actions

## Phase 7 – Executive Reporting ✅

* PDF Reporting
* JSON Reporting
* Executive Reports

## Phase 8 – Authentication & User System ✅

* Google Sign-In
* Firebase Authentication
* Firestore Profiles
* Protected Routes
* Secure Logout
* Simulation History
* Saved Reports Dashboard
* Executive Report Library
* PDF Downloads
* JSON Downloads
* Report Deletion
* Duplicate Protection

## Phase 9 – Gemini AI Copilot 🚧

Planned:

* Executive AI Assistant
* KPI Explanations
* Scenario Interpretation
* Strategic Q&A
* Business Insights
* AI Recommendations

## Phase 10 – Deployment ⏳

Planned:

* Production Deployment
* Environment Management
* Security Hardening
* Monitoring

## Phase 11 – GitHub Professionalization Sprint ⏳

Planned:

* Final Documentation
* Screenshots
* Demo Assets
* Architecture Diagrams
* Portfolio Packaging

---

# How To Run Locally

```powershell
python -m venv venv

venv\Scripts\activate

pip install -r requirements.txt

venv\Scripts\python -m flask --app backend.app run --host 127.0.0.1 --port 5000

venv\Scripts\python -m streamlit run app.py
```

---

# Firebase Setup

Enable:

* Firebase Authentication
* Google Sign-In
* Firestore Database
* Web App Configuration
* Admin SDK

Copy:

```text
.streamlit/secrets.example.toml
```

to:

```text
.streamlit/secrets.toml
```

Deploy Firestore Rules:

```powershell
firebase deploy --only firestore:rules
```

Authorized Domains:

```text
localhost
127.0.0.1
your-production-domain.com
```

---

# Testing

Run:

```powershell
python tests/test_simulation.py
python tests/test_comparison.py
python tests/test_executive_advisor.py
python tests/test_workspace_service.py
python tests/test_company_ingestion.py
python tests/test_report_service.py
```

---

# Screenshots

*To be added after deployment*

* Authentication Page
* User Onboarding
* Dashboard
* Scenario Comparison
* Strategic Intelligence
* Executive Reporting
* Saved Reports Dashboard
* Report Preview
* PDF Downloads
* Workspace Management
* Gemini AI Copilot

---

# Current Status

## Phase 8 Complete ✅

Major Deliverables:

* Deterministic Simulation Engine
* Strategic Intelligence System
* Executive Reporting
* Workspace Management
* Firebase Authentication
* Google OAuth
* Firestore User Profiles
* Protected Workspaces
* Saved Reports Dashboard
* Executive Report Library
* PDF/JSON Report Management

## Next Phase

**Phase 9 – Gemini AI Copilot**

---

# Author

**Aditya Vijay Athawale**

Walchand College of Engineering, Sangli
Information Technology Department (2023-2027)

---

### Keywords

business-intelligence, strategy, analytics, simulation, consulting, product-management, startup, saas, forecasting, dashboard, streamlit, firebase, firestore, authentication, decision-support, strategic-intelligence
