# AI Governance Project — Overview

![CEGP + DRVL Architecture](docs/cegp-architecture.png)

> AI Agent → DRVL → Database → Event Bus → Governance Dashboar

Architecture research exploring **deterministic governance** for autonomous AI systems through the **Compute Escalation Governance Protocol (CEGP)** and runtime verification.

## Overview

As AI systems become increasingly autonomous, traditional policy guidance is no longer sufficient. Governance must evolve into **deterministic control infrastructure** that enforces hard boundaries at runtime.

The **Compute Escalation Governance Protocol (CEGP)** defines a control-plane architecture in which:

- AI agents operate strictly within **signed compute envelopes**  
- These envelopes cryptographically enforce capability, compute, memory, network, and action limits at the orchestration layer  
- Any attempt to exceed the envelope triggers an **explicit escalation request**  
- Escalation requests are validated (via policy engine or human-in-the-loop governance) before expanded capabilities are granted

This creates a verifiable, auditable path for capability growth while preventing unauthorized or unsafe expansion.

## Live Demo

🚀 A minimal, self-contained demonstration of **DRVL runtime governance** is included in the `demo/` folder.

Watch a simulated autonomous agent perform database operations under active runtime policies. You can observe in real time:

- Executed vs. blocked actions  
- Policy decision explanations  
- Governance and security alerts  
- Live event stream to the browser dashboard  

### Quick Start

```bash
cd demo
pip install flask
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
  A runtime interception and enforcement layer that monitors AI actions, applies policy rules, emits governance events, and provides explainability and observability.

## Repository Structure

```
.
├── demo/                    # DRVL runtime governance demo (Flask dashboard + simulation)
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

See the complete document:  
[architecture-overview.md](https://github.com/babyblueviper1/ai-governance-architecture/blob/main/architecture-overview.md)

## License

Creative Commons Attribution–NonCommercial 4.0 International (CC BY-NC 4.0)
