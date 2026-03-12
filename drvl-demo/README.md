# DRVL Governance Demo — Probabilistic Agent with Escalation

**Live Demo (no installation needed!)**  
🎮 https://drvl-demo.onrender.com/  
*(First load may take 10–30 seconds due to Render free-tier spin-up. Subsequent visits are instant.)*

This folder contains a **minimal, self-contained demonstration** of the **Distributed Runtime Verification Layer (DRVL)** governing an AI agent.

The agent attempts database operations (`READ`, `UPDATE`, `DELETE`, `DROP`) while DRVL enforces deterministic runtime policies — executing allowed actions, blocking forbidden ones, escalating risky ones, or auto-deciding based on simple rules.

## Real LLM Mode (bring your own key)

- Toggle the switch on → paste your **OpenAI** API key  
- **Demo currently supports OpenAI only** (GPT-4o / 4o-mini)  
- Actions become truly non-deterministic (and occasionally risky — perfect to see DRVL govern real frontier-model behavior)  
- **Warning:** Using real LLM will consume your OpenAI tokens and may incur costs. The default simulation mode uses **no tokens**.  
- Your key is sent once to the server, never stored or logged — only used for your current session.

## Policy Integrity & Attestation

Every governance decision includes:  
- **Policy hash** — SHA-256 fingerprint of the current rules (ensures reproducible enforcement)  
- **Signature** — HMAC-SHA256 of the event payload (provides cryptographic attestation)

This demonstrates deterministic, auditable governance — a core requirement for real security and compliance systems.

**Demo note (intentional mismatches):**  
For illustration purposes, **~15% of events are deliberately tampered** with (wrong policy hash or corrupted signature) to show what integrity detection looks like in the UI (red "✗ Tampered / Invalid" warning).  
In a real system, policy hashes are designed to match for events under the current policy — the check exists precisely to detect any changes, tampering, misconfigurations, or other issues.

## Key Features

- **Agent Mode Toggle**  
  Switch between:  
  - Simulated / random probabilistic agent (fast, free, predictable)  
  - Real OpenAI LLM (your API key) — unpredictable, realistic frontier-model behavior

- **Deterministic Runtime Enforcement**  
  Policies applied consistently:  
  - Allowed → execute  
  - Forbidden → block  
  - Escalatable → decide (auto or manual)

- **Escalation Handling (for DELETE)**  
  When escalation is required:  
  - **~35% auto-approved** → executed immediately (green)  
  - **~35% auto-denied** → blocked immediately (red)  
  - **~30% pending** → wait for manual Approve / Deny via dashboard buttons

- **Real-Time Governance Dashboard**  
  - Manual or autonomous action triggers  
  - Adjustable speed slider for autonomous mode  
  - Execution / block / approved counters  
  - Active policies view  
  - Latest decision panel with detailed explanation  
  - Live event stream with timestamps and color coding  
  - Escalation queue with pending requests + Approve/Deny buttons  
  - LLM mode status + error feedback  
  - Policy hash + signature displayed on every event

## Architecture

```
AI Agent (Simulated or Real LLM)
           ↓
     DRVL Policy Engine  ← deterministic rules + auto-decision
           ↓
      Database Execution
           ↓
        Event Bus
           ↓
   Governance Dashboard (browser)
```

## Running the Demo Locally

### 1. Install dependencies

```bash
pip install flask openai  # openai required only for real LLM mode
```

### 2. Start the server

```bash
python app.py
```

### 3. Open in browser

http://localhost:10000

## Example Governance Rules

| Operation | Result                  | Behavior in Demo                          |
|-----------|-------------------------|-------------------------------------------|
| READ      | Allowed                 | Executed (green)                          |
| UPDATE    | Allowed                 | Executed (green)                          |
| DELETE    | Requires escalation     | ~35% auto-approve, ~35% auto-deny, ~30% pending/manual |
| DROP      | Forbidden               | Always blocked (red)                      |

**Demo note:** Escalation decisions (DELETE) are probabilistic for realism — auto-approved (~35%), auto-denied (~35%), or pending (~30%) for human-in-the-loop control.

## Escalation Queue

- **Pending** requests show Approve (green) and Deny (red) buttons  
- **Auto-approved** requests execute immediately (no queue entry)  
- **Auto-denied** requests are blocked immediately (red event)  
- Manual Approve → executes action (green)  
- Manual Deny → blocks action (red)  

This illustrates **automated + human governance** working together over unpredictable (simulated or real LLM) AI behavior.

## Folder Contents

```
demo/
 ├── app.py               # Flask server + dashboard endpoints
 ├── agent.py             # AI agent (simulated + real LLM support)
 ├── database.py          # Dummy DB simulator
 ├── drvl.py              # Policy verification engine
 ├── event_bus.py         # Simple pub/sub for events
 ├── audit.py             # Logging decisions
 ├── templates/
 │   └── index.html       # Real-time dashboard (HTML + JS)
 └── drvl_events.log      # Audit trail (appended on run)
```

## Purpose

This prototype clearly shows:

**“Deterministic enforcement controlling a probabilistic — or real frontier — AI agent.”**

It demonstrates:
- Runtime policy enforcement on non-deterministic behavior  
- Automatic + manual risk containment  
- Real-time observability, explainability, and human oversight  
- Optional integration with real LLMs (bring your own key)

Not production-ready — a focused, runnable illustration of DRVL-style governance for autonomous systems.
