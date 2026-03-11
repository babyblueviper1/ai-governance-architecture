# DRVL Governance Demo — Probabilistic Agent with Escalation

This folder contains a **working demonstration** of the **Distributed Runtime Verification Layer (DRVL)** governing a **probabilistic AI agent**.  

The demo now includes **escalation requests** for restricted actions (`DELETE` / `DROP`) with:

- Every **3rd request automatically approved** for demo purposes.  
- Manual **Approve button** to simulate human review of other requests.  

### Key Features

- **Probabilistic AI Agent**  
  Occasionally attempts risky operations, showing DRVL enforcement in action.

- **Deterministic Runtime Enforcement (DRVL)**  
  All policy rules are applied deterministically; unsafe actions are blocked or escalated.

- **Escalation Requests**  
  Restricted actions generate requests. Approved requests are executed; blocked requests remain pending until approved.

- **Real-Time Dashboard**  
  - Executed vs blocked actions  
  - Escalation queue with manual approval  
  - Alerts for high-risk actions  
  - Counters for executed, blocked, and escalated actions  

- **Autonomous Mode**  
  The agent runs continuously, generating actions according to the slider speed.

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

**Note:** For demo purposes, **every 3rd escalation request is automatically approved** to simulate a mix of automated and manual governance decisions.

## Escalation Queue Panel

The dashboard now features a **live Escalation Queue** section, providing real-time visibility and control over capability expansion requests:

- **Pending requests** appear in the queue with an **Approve** button  
- **Auto-approved requests** (every 3rd one) are executed immediately and marked as such  
- **Human operators** (in demo mode: you) can manually approve any pending request by clicking Approve  
- Clear visual feedback shows the status of each request:  
  - **PENDING** — awaiting decision  
  - **APPROVED** — escalation granted (auto or manual)  
  - **EXECUTED** — expanded capabilities now active for the agent  

This panel demonstrates how DRVL integrates escalation workflows — combining deterministic automation with human-in-the-loop oversight — to safely govern probabilistic AI behavior.


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
