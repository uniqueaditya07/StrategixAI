# StrategixAI - AI Strategy Intelligence Platform

**Simulate business decisions. Compare strategic scenarios. Generate executive intelligence. Make better decisions.**

StrategixAI is an AI-powered strategy intelligence platform that helps founders, consultants, product managers, MBA students, business analysts, and decision-makers evaluate business strategies before committing resources.

The platform combines deterministic business simulation, scenario comparison, strategic intelligence, executive reporting, and secure user workspaces into a unified decision-support environment.

---

# Executive Summary

Organizations frequently make critical business decisions using spreadsheets, assumptions, presentations, and subjective discussions.

StrategixAI transforms that process into a structured and explainable decision-support workflow.

Users can:

* Simulate business outcomes
* Compare alternative strategies
* Analyze risk and business health
* Generate executive recommendations
* Export boardroom-ready reports
* Maintain secure company workspaces

The platform is inspired by consulting frameworks, corporate strategy teams, business intelligence systems, and executive planning workflows.

---

# Business Problem

Strategic decision-making is often fragmented across:

* Excel spreadsheets
* PowerPoint decks
* Financial models
* Team discussions
* Individual assumptions

This creates several challenges:

* Lack of reproducibility
* Inconsistent strategic evaluation
* Poor visibility into tradeoffs
* Slow decision cycles
* Limited risk awareness
* Difficulty comparing alternatives

Organizations need a structured way to evaluate scenarios before execution.

StrategixAI addresses this problem through deterministic business simulation and explainable strategic intelligence.

---

# Strategic Value

StrategixAI enables users to:

* Evaluate growth strategies before execution
* Understand financial tradeoffs
* Compare operating plans
* Detect risks early
* Prioritize executive actions
* Generate boardroom-ready reports
* Create repeatable decision-making workflows

The platform bridges the gap between business analytics and executive decision support.

---

# Project Overview

StrategixAI is designed as a decision-support platform rather than a chatbot.

Instead of generating generic advice, the platform:

1. Accepts structured business assumptions
2. Runs deterministic simulations
3. Compares strategic scenarios
4. Generates explainable executive intelligence
5. Produces professional reports

This ensures recommendations remain grounded in measurable business inputs and simulation outputs.

---

# Who Is It For?

StrategixAI is designed for:

* Startup Founders
* Product Managers
* Strategy Teams
* Consultants
* Business Analysts
* MBA Students
* Finance Teams
* Operations Teams
* Corporate Planning Teams

---

# Current Capabilities

StrategixAI currently supports:

### Simulation

* Revenue Forecasting
* Customer Growth Forecasting
* Profit Forecasting
* Cash Forecasting
* Runway Analysis
* Breakeven Estimation

### Strategic Intelligence

* Business Health Score
* Strategic Signals
* Risk Radar
* Recommended Actions
* Executive Recommendations
* Scenario Winner Analysis

### Scenario Analysis

* Base Case
* Growth Push
* Cost Optimization

### Reporting

* Executive PDF Reports
* JSON Exports
* KPI Summaries
* Strategic Findings
* Risk Reports

### Authentication & User System

* Google Sign-In
* Persistent Sessions
* User Onboarding
* Firestore User Profiles
* Protected Routes
* Secure Logout
* User Simulation History
* User Report Storage

---

# Authentication Architecture

```txt
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

# High-Level System Architecture

```txt
User Input
      ↓
Workspace Layer
      ↓
Dashboard Service
      ↓
Simulation Engine
      ↓
Scenario Comparison Engine
      ↓
Strategic Intelligence Engine
      ↓
Reporting Layer
      ↓
Executive Dashboard
```

---

# Key Features

## Deterministic Simulation Engine

StrategixAI uses deterministic calculations to generate reproducible business forecasts.

Forecasted KPIs include:

* Revenue
* ARR
* Customers
* Net Income
* Cash Balance
* Runway
* Churn
* CAC
* LTV/CAC
* Breakeven

---

## Scenario Comparison

Users can compare:

### Base Case

Current operating assumptions.

### Growth Push

Aggressive growth-focused strategy.

### Cost Optimization

Efficiency-focused strategy.

Comparison includes:

* Revenue
* Customers
* Profit
* Cash
* Unit Economics
* Runway

---

## Strategic Intelligence

### Business Health Score

Provides a 0–100 evaluation of overall business health.

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

### Executive Recommendations

Generates explainable recommendations based on simulation outputs.

---

## Workspace Management

Supports:

* Multiple companies
* Company switching
* Custom company creation
* Company editing
* Company deletion
* JSON imports

---

## Authentication & User System

### Firebase Authentication

* Google Sign-In
* Persistent Login
* Secure Session Management

### Firestore User Profiles

Stores:

* User Information
* Onboarding Preferences
* Simulations
* Reports

### Protected Routes

Authentication required for:

* Dashboard
* Simulator
* Scenario Comparison
* Saved Reports
* Company Management
* Future AI Copilot

---

# Firestore Data Model

```txt
users/
└── {uid}
    ├── profile
    ├── simulations/
    │   └── {simulationId}
    └── reports/
        └── {reportId}
```

User-owned data is protected through Firebase Authentication and Firestore Security Rules.

---

# Skills Demonstrated

This project demonstrates skills across multiple domains.

## Product Management

* KPI Design
* User Workflow Design
* Product Thinking
* Decision-Support Systems

## Strategy & Consulting

* Scenario Analysis
* Strategic Planning
* Risk Assessment
* Business Intelligence
* Executive Reporting

## Data & Analytics

* Forecasting
* Simulation Modeling
* KPI Analysis
* Deterministic Analytics

## Software Engineering

* Python
* Streamlit
* Flask
* Firebase Authentication
* Firestore
* Software Architecture
* Secure Authentication Systems

---

# Project Metrics

### Completed Phases

8

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

### Supported Scenarios

* Base Case
* Growth Push
* Cost Optimization

---

# Completed Phase Roadmap

## Phase 1 – Simulation Engine

* Deterministic simulation core
* Revenue forecasting
* Customer forecasting
* Profit forecasting
* Cash forecasting
* Runway forecasting

## Phase 2 – Scenario Comparison

* Multi-scenario evaluation
* KPI comparison framework
* Scenario winner identification

## Phase 3 – Executive Advisor

* Strategic recommendations
* Confidence scoring
* Explainable reasoning

## Phase 4 – Multi-Company Workspace Architecture

* Workspace isolation
* Company-specific assumptions
* Workspace selection

## Phase 5 – Workspace Management

* Create companies
* Edit companies
* Delete companies
* Import companies

## Phase 6 – Strategic Intelligence

* Business Health Score
* Strategic Signals
* Risk Radar
* Recommended Actions

## Phase 7 – Executive Reporting & Export

* PDF Reporting
* JSON Reporting
* Boardroom-ready exports

## Phase 8 – Firebase Authentication & User System

* Firebase Authentication
* Google Sign-In
* Firestore Profiles
* User Onboarding
* Protected Routes
* Secure Logout
* User Simulation History
* User Report Storage

---

# Product Vision

The long-term vision of StrategixAI is to evolve from a deterministic strategy simulator into a complete AI-powered strategy copilot.

Future versions will support:

* Conversational Strategy Assistance
* AI-Powered Scenario Analysis
* Portfolio Intelligence
* Benchmarking Systems
* Multi-Company Intelligence
* Executive Decision Copilots

---

# Next Major Milestone

## Phase 9 – Gemini AI Copilot

Planned Deliverables:

* Executive AI Assistant
* KPI Explanations
* Scenario Interpretation
* Strategic Q&A
* Business Insights
* Executive Recommendations

---

# Current V1 Roadmap

### Remaining Work

* Gemini AI Copilot
* Deployment
* Production Hardening
* Documentation Polish
* Screenshots

---

# V2 Roadmap

### Planned Enhancements

* Portfolio Intelligence
* Industry Benchmarking
* Historical Simulation Tracking
* Multi-Company Analytics
* Portfolio Dashboard

---

# Project Structure

```txt
StrategixAI/
├── app.py
├── analytics/
├── backend/
├── engine/
├── data/
├── tests/
├── firestore.rules
├── requirements.txt
└── README.md
```

### Directory Overview

* app.py → Main Streamlit Application
* analytics/ → Business Logic Services
* backend/ → Firebase Authentication Layer
* engine/ → Simulation Engine
* data/ → Company Data
* tests/ → Regression Tests
* firestore.rules → Security Rules

---

# Firebase Setup

Enable:

* Firebase Authentication
* Google Sign-In
* Firestore Database
* Web App Configuration
* Admin SDK

Copy:

```txt
.streamlit/secrets.example.toml
```

to:

```txt
.streamlit/secrets.toml
```

and populate Firebase credentials.

Deploy Firestore Rules:

```powershell
firebase deploy --only firestore:rules
```

Authorized Domains should include:

```txt
localhost
127.0.0.1
your-production-domain.com
```

---

# Reporting System

## JSON Export

Includes:

* Metadata
* KPI Snapshot
* Simulation Summary
* Strategic Intelligence
* Risk Summary
* Recommendations

## PDF Export

Includes:

* Cover Page
* Executive Summary
* KPI Dashboard
* Business Health Score
* Strategic Signals
* Risk Radar
* Recommendations
* Scenario Comparison

---

# Testing

Core test coverage includes:

* Simulation Engine
* Comparison Engine
* Strategic Intelligence
* Workspace Management
* Company Ingestion
* Reporting Services

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

# How To Run Locally

```powershell
python -m venv venv

venv\Scripts\activate

pip install -r requirements.txt

streamlit run app.py
```

---

# Tech Stack

## Backend

* Python
* Flask
* Firebase Admin SDK
* Pandas
* Pydantic

## Frontend

* Streamlit
* Custom CSS

## Database

* Firestore

## Authentication

* Firebase Authentication
* Google OAuth

## Analytics

* Deterministic Simulation Engine
* Strategic Intelligence Engine
* Scenario Comparison Engine

## Reporting

* PDF Export
* JSON Export

## Development

* Git
* GitHub

---

# Release History

## v0.8.0

* Firebase Authentication
* Google Sign-In
* User Onboarding
* Firestore Integration
* Protected Routes
* User Profile System
* Simulation History
* Saved Reports

## v0.7.0

* Executive Reporting
* PDF Export
* JSON Export

## v0.6.0

* Strategic Intelligence
* Business Health Score
* Risk Radar

---

# Screenshots

To Be Added:

* Landing Page
* Authentication Page
* User Onboarding
* Dashboard
* Scenario Comparison
* Strategic Intelligence
* Reporting
* Gemini AI Copilot

---

# Future Enhancements

* Gemini AI Copilot
* Public Deployment
* Portfolio Intelligence
* Industry Benchmarking
* Historical Analytics
* AI Strategy Assistant

---

# Project Status

**Current Status:** Phase 8 Complete ✅

**Next Phase:** Gemini AI Copilot

---

# Author

**Aditya Vijay Athawale**

Walchand College of Engineering, Sangli

---

### Keywords

business-intelligence, strategy, analytics, simulation, streamlit, consulting, product-management, startup, saas, forecasting, dashboard, firebase, firestore, authentication
