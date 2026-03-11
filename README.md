# AI Governance Project — Overview

![CEGP + DRVL Architecture](docs/cegp-architecture.png)

> AI Agent → DRVL → Database → Event Bus → Governance Dashboard

Architecture research exploring **deterministic governance** for autonomous AI systems through the **Compute Escalation Governance Protocol (CEGP)** and runtime verification.

## Overview

As AI systems become increasingly autonomous, traditional policy guidance is no longer sufficient. Governance must evolve into **deterministic control infrastructure** that enforces hard, verifiable boundaries at runtime.

The **Compute Escalation Governance Protocol (CEGP)** introduces a control-plane architecture where:

- AI agents operate strictly within **signed compute envelopes**  
- These envelopes cryptographically enforce capability, compute, memory, network, and action limits at the orchestration layer  
- Any attempt to exceed the envelope triggers an **explicit escalation request**  
- Escalation requests are validated (via policy engine or human-in-the-loop governance) before expanded capabilities are granted  

This creates a strong, auditable path for capability growth while preventing unauthorized or unsafe expansion.

## Live Demo — DRVL Governance with Escalation

🎮 **Try it live (no installation needed!)**  
https://drvl-demo.onrender.com/

*(First load may take 10–30 seconds due to Render free-tier spin-up. Subsequent visits are instant.)*

Watch a **probabilistic or real LLM-powered AI agent** perform database actions in real time under **deterministic DRVL governance**.

### New: Real LLM Mode (bring your own key)

- Toggle on → paste your **OpenAI** API key  
- **Demo currently supports OpenAI only** (GPT-4o / 4o-mini). Other providers coming soon.  
- Actions become truly non-deterministic (and occasionally risky — perfect to see DRVL govern real frontier-model behavior)  
- **Warning:** Using real LLM will consume your OpenAI tokens and may incur costs. Default simulation mode uses **no tokens**.  
- Key is sent once to the server, never stored or logged — only used for your session.

### Escalation & Auto-Decision Features
- `DELETE` operations trigger **escalation requests**  
- `DROP` operations are always **forbidden** (instantly blocked)  
- For escalations (DELETE), backend applies probabilistic decisions (demo realism):  
  - **~35% auto-approved** → executed immediately (green)  
  - **~35% auto-denied** → blocked immediately (red)  
  - **~30% pending** → appear in live queue with **Approve** and **Deny** buttons for manual control  

### Policy Integrity & Attestation
Every governance decision includes:
- **Policy hash** — SHA-256 of current rules (reproducible enforcement)  
- **Signature** — HMAC of event payload (cryptographic attestation)  

This demonstrates deterministic, auditable governance — key for real security and compliance systems.

### What You’ll See in the Dashboard
- Live stream of executed (green), blocked (red), pending (yellow), approved (bold green) actions  
- Real-time escalation queue with Approve/Deny controls  
- Execution / block / approved counters  
- Detailed policy decision explanations  
- Alerts for blocked or denied actions  
- Autonomous mode with adjustable speed slider  
- LLM mode status + error feedback  
- Policy hash + signature on every event

This demo clearly illustrates the core thesis:

> **Deterministic enforcement controlling a probabilistic — or real frontier — AI agent**,  
> combining automatic policy decisions, probabilistic auto-handling of edge cases,  
> cryptographic policy attestation, and human-in-the-loop oversight via escalation workflows.

### Quick Start (Local Run)

```bash
cd demo
pip install flask openai  # openai only needed for real LLM mode
python app.py
```

Then open in your browser:  
http://localhost:10000

## Key Components

- **Signed Compute Envelopes**  
  Cryptographic wrappers that define and enforce exact capability boundaries (compute, memory, network, allowed actions) for each AI agent instance.

- **Deterministic Orchestration Enforcement**  
  Infrastructure-level control plane that only provisions or scales resources when governed escalation is approved.

- **Escalation Requests**  
  Agents must formally request (and often justify) expanded privileges when they reach the limits of their current envelope.

- **Distributed Runtime Verification Layer (DRVL)**  
  Runtime interception and enforcement layer that monitors AI actions, applies policy rules, emits governance events, and provides explainability and observability.

## Repository Structure

```
.
├── demo/                    # DRVL runtime governance demo (Flask dashboard + LLM toggle)
├── docs/                    # Architecture diagrams, threat models, research notes
├── protocols/               # CEGP protocol definitions and message schemas
├── architecture-overview.md # Detailed architecture documentation
└── README.md                # This file
```

## Full Architecture & Research

For in-depth coverage including:

- Enforcement primitives and cryptographic mechanisms  
- Capability-tiered governance model  
- Deployment patterns (centralized vs. distributed control planes)  
- Threat modeling and attack surface analysis  
- Integration with existing orchestration systems  

See:  
[architecture-overview.md](https://github.com/babyblueviper1/ai-governance-architecture/blob/main/architecture-overview.md)

## License

Creative Commons Attribution–NonCommercial 4.0 International (CC BY-NC 4.0)
