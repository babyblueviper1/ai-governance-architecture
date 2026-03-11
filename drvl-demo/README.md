# DRVL Governance Demo

This folder contains a **minimal working demonstration** of the **Distributed Runtime Verification Layer (DRVL)**.

The demo simulates an **autonomous AI agent performing database actions**, while DRVL enforces runtime governance policies in real time.

Actions are either:

- **Executed** if they comply with policy  
- **Blocked** if they violate governance rules  

All decisions are streamed live to a **governance dashboard**.

## What the Demo Shows

Five core governance capabilities:

1. Autonomous AI actions  
2. Runtime policy enforcement  
3. Real-time event monitoring  
4. Security alerting  
5. Policy decision explainability  

## Architecture

```
AI Agent
   ↓
DRVL Policy Engine
   ↓
Database Execution
   ↓
Event Bus ──→ Governance Dashboard (browser)
```

## Dashboard Features

- Manual AI action trigger  
- Autonomous mode  
- AI speed control  
- Execution / block counters  
- Active governance policies view  
- Policy decision explanation panel  
- Real-time event stream  
- Architecture diagram  

## Quick Start

### 1. Install dependencies

```bash
pip install flask
```

(Only Flask is needed — the rest is pure Python stdlib or minimal files)

### 2. Start the server

```bash
python app.py
```

### 3. Open in browser

```
http://localhost:10000
```

You should see the dashboard within seconds.

## Example Governance Rules (active in this demo)

| Operation | Decision            |
|-----------|---------------------|
| READ      | Allowed             |
| UPDATE    | Allowed             |
| DELETE    | Requires escalation |
| DROP      | Forbidden           |

## Folder Contents

```
demo/
 ├── app.py               # Flask server + dashboard
 ├── agent.py             # Simulated autonomous AI
 ├── database.py          # Dummy DB with action logging
 ├── drvl.py              # Core policy engine logic
 ├── event_bus.py         # Simple pub/sub for events
 ├── audit.py             # Decision logging
 ├── templates/
 │   └── index.html       # Dashboard frontend
 └── drvl_events.log      # Audit trail (appended during runs)
```

## Purpose

This is **not production code** — it is a clean, minimal prototype to show:

- How runtime verification can intercept and govern AI behavior  
- Real-time policy decisions and explainability  
- Live observability of autonomous systems  

**DRVL** = Distributed Runtime Verification Layer  
A governance layer for monitoring + enforcing policy over autonomous AI systems at runtime.
