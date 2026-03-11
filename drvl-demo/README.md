# DRVL Governance Demo — Probabilistic Agent Edition

This folder contains a **minimal working demonstration** of the **Distributed Runtime Verification Layer (DRVL)** governing a **probabilistic AI agent**.

The demo simulates an autonomous agent performing database actions — where the agent **sometimes attempts risky or unsafe operations** — while DRVL enforces deterministic runtime governance policies in real time.

Actions are:

- **Executed** if they comply with policy  
- **Blocked** if they violate governance rules  

All decisions, alerts, and explanations are streamed live to a browser-based **governance dashboard**.

## Key Features

- **Probabilistic AI Agent**  
  Deliberately introduces realistic, non-deterministic behavior by occasionally attempting high-risk operations (e.g. DELETE, DROP) — exactly like real-world frontier AI systems might.

- **Deterministic Runtime Enforcement (DRVL)**  
  Applies policy rules consistently and verifiably — ensuring that even when the agent “misbehaves,” unsafe actions are blocked every time.

- **Real-Time Governance Dashboard**  
  Watch executed vs. blocked actions, live alerts, counters, policy explanations, and event stream in one clean interface.

- **Autonomous Mode**  
  Agent runs continuously at adjustable speed — simulating persistent, long-running autonomous operation under governance.

## Architecture

```
Probabilistic AI Agent
           ↓
     DRVL Policy Engine  ← deterministic enforcement
           ↓
      Database Execution
           ↓
        Event Bus
           ↓
   Governance Dashboard (browser)
```

Core idea: **Deterministic enforcement over probabilistic behavior** — the foundational principle of safe runtime AI governance.

## Demo UI Features

- Manual AI action trigger  
- Autonomous / continuous mode toggle  
- AI action speed control (interval slider)  
- Execution & block counters  
- Currently active governance policies view  
- Detailed policy decision & explanation panel  
- Real-time event stream  
- Live architecture diagram (updates with activity)

## Running the Demo

### 1. Install dependencies

```bash
pip install flask
```

### 2. Start the server

```bash
python app.py
```

### 3. Open the dashboard

http://localhost:10000

You should see the interface load immediately.

## Example Governance Rules (enforced in this demo)

| Operation | Result              |
|-----------|---------------------|
| READ      | Allowed             |
| UPDATE    | Allowed             |
| DELETE    | Requires escalation |
| DROP      | Forbidden           |

## Folder Contents

```
demo/
 ├── app.py               # Flask server + dashboard
 ├── agent.py             # Probabilistic AI agent logic
 ├── database.py          # Dummy database simulator
 ├── drvl.py              # Core deterministic policy engine
 ├── event_bus.py         # Simple event publishing
 ├── audit.py             # Decision & event logging
 ├── templates/
 │   └── index.html       # Dashboard frontend (HTML + JS)
 └── drvl_events.log      # Audit trail file (appended on run)
```

## Purpose

This edition explicitly highlights:

**“Deterministic enforcement controlling a probabilistic AI agent.”**

It provides a clean, reproducible prototype to demonstrate:

- Runtime policy enforcement on non-deterministic behavior  
- Reliable risk containment (even when the agent tries dangerous things)  
- Real-time auditability, explainability, and observability  

Not production code — a focused illustration of how DRVL can bring strong, verifiable governance to realistic, probabilistic autonomous systems.
