# StrategixAI Development Rules

StrategixAI is a premium AI-powered business strategy and decision intelligence platform.

## Core Philosophy

- Executive-grade UI
- Minimal and premium design
- Modular architecture
- Typed Python code
- Production-grade structure
- Strong separation of concerns
- Business-first thinking
- Strategy-focused analytics
- Consulting-style reasoning

## Technical Rules

- Use Python type hints everywhere
- Use Pydantic schemas for validation
- Avoid monolithic files
- Keep business logic separate from UI
- Reusable Plotly chart functions
- Modular Streamlit components
- Configurable architecture
- Clean imports
- Avoid hardcoding values

## UI Philosophy

The UI should feel like:

- Stripe Dashboard
- Linear
- Notion AI
- McKinsey-style executive dashboard

Avoid:

- flashy colors
- clutter
- toy dashboards
- excessive animations

Preferred style:

- dark premium UI
- glassmorphism
- subtle shadows
- strong spacing
- executive KPI cards

## AI Philosophy

AI should:

- explain business tradeoffs
- generate executive summaries
- provide strategic recommendations
- challenge weak strategies
- explain risks clearly

Avoid:

- generic AI responses
- shallow chatbot behavior

## Engineering Principles

Every module should:

- have one responsibility
- be reusable
- be testable
- integrate cleanly with the system

## Folder Ownership

```txt
models/      → schemas and contracts
engine/      → simulation logic
analytics/   → KPI and business analysis
ai/          → GenAI workflows
visuals/     → charts and UI components
database/    → persistence layer
utils/       → shared utilities
```

## Coding Style

Prefer:

- clarity over cleverness
- readability over shortcuts
- business terminology over technical jargon