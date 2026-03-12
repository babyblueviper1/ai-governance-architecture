# AI Governance Project

This repository contains both the conceptual governance architecture (Notes) and the deployable enforcement protocol specifications (Protocols) for capability-tiered AI governance systems.

**Version:** v0.7  
**Status:** Research Architecture & Protocol Drafting  
**Protocol:** CEGP v0.1  
**Lead:** Federico Blanco Sánchez-Llanos  
**Date:** March 2026

## Executive Overview

Advanced AI systems are evolving from assistive tools into persistent, economically active agents embedded within institutional and economic infrastructures.

As these systems gain autonomy, governance cannot rely solely on policy guidance or post-hoc monitoring. Governance must migrate into **execution infrastructure**.

The AI Governance Project explores a capability-tiered governance architecture in which AI systems operate within **deterministically enforced compute envelopes**. These envelopes define capability boundaries and require explicit governance escalation when agents attempt to exceed them.

The objective is not reactive regulation, but **structural synchronization between capability expansion and governance maturity** through enforcement mechanisms embedded directly into compute orchestration systems.

In this model, governance operates as a **control plane for probabilistic agents**, introducing deterministic boundaries, escalation pathways, and verifiable constraint enforcement.

As enforcement migrates into infrastructure, jurisdiction, sovereignty, and power distribution become design variables rather than external policy considerations.

## Repository Structure
```
├── notes/
│   ├── note-01-ai-agent-spectrum.md
│   ├── note-02-from-agent-spectrum-to-governance-architecture.md
│   ├── note-03-capability-tiered-governance-enforcement.md
│   ├── note-04-enforcement-primitives.md
│   └── note-05-enterprise-deployment-model.md
│
├── protocols/
│   └── cegp/
│       ├── cegp-v0.1.md
│       ├── cegp-spec.md
│       ├── cegp-envelope-schema.md
│       ├── cegp-escalation-flow.md
│       ├── cegp-enforcement-loop.md
│       ├── cegp-enterprise-deployment.md
│       ├── enforcement-invariants.md
│       ├── enforcement-patterns.md
│       └── threat-model.md
│
└── docs/
    ├── capability-tiered-governance-architecture-v0.1.png
    ├── cegp-use.cases.md
    ├── cegp-architecture.png
    └── cegp-escalation-flow.png
```
The repository separates strategic architecture research (Notes) from deployable enforcement protocol specifications (Protocols)

## Premise

The term “AI” currently collapses fundamentally different system types into a single regulatory category.

Stateless predictive tools, enterprise workflow agents, autonomous operational systems, economically active agents, sovereign-scale compute deployments, and decentralized rogue actors cannot coherently share the same governance regime.

Effective governance must map to capability — not branding.

As capability growth accelerates, governance must evolve proportionally.  
The question is not whether advanced AI systems will emerge — but whether enforcement infrastructure matures alongside them.

## Structure of the Research Series

### Core Protocol: CEGP

**CEGP — Compute Escalation Governance Protocol** introduces deterministic compute envelopes with cryptographic authorization and structured escalation pathways.  
It governs **compute-linked capability expansion**, not model cognition or content behavior.

CEGP does not attempt to regulate model cognition or interpret behavior.  
Instead, it enforces governance boundaries at **execution and orchestration layers**, where deterministic infrastructure controls remain possible even when model outputs are probabilistic.

This approach treats AI governance as a **fault-containment architecture for autonomous systems**, rather than a behavioral alignment problem.

Primary components:

- **Signed Compute Envelopes** — cryptographically defined capability and compute boundaries per agent.  
- **Deterministic Envelope Enforcement** — all actions pass through orchestration-level control to ensure governance rules are followed.  
- **Explicit Escalation Requests** — agents must request permission to exceed envelope limits; approvals are auditable and optionally anchored.  
- **Distributed Runtime Verification Layer (DRVL)** — envelope compliance is redundantly verified across independent runtime nodes, preventing unilateral bypass and supporting multi-node consensus.  
- **Risk-Tiered Governance Thresholds** — escalation requirements scale with agent autonomy and operational risk.  
- **Fault Containment Mechanisms** — constraints prevent cascading failures across agents, tools, and infrastructure, even in probabilistic or multi-agent environments.  
- **Tamper-Evident Audit Pathways** — all envelope and escalation events can be cryptographically verified for compliance and accountability.

→ [CEGP Specification](./protocols/cegp/cegp-spec.md)

---

### Distributed Runtime Verification Layer (DRVL)

CEGP envelopes are validated **redundantly across independent runtime nodes**:

- Deterministic envelope replay to verify compliance  
- Network consensus prevents unilateral bypass of escalation logic  
- Resilient to partial node compromise  
- Interoperable with hardware attestation (SGX, Nitro Enclaves, etc.)  
- Ensures **provable escalation friction** in multi-cloud or hybrid sovereign environments

This architecture provides a **distributed verification layer for governance enforcement**, ensuring that envelope boundaries and escalation rules cannot be unilaterally bypassed by compromised runtimes, orchestration layers, or infrastructure operators.

---

## Interactive Demo — DRVL Runtime Governance in Action

A live, browser-based demonstration of **deterministic runtime governance** controlling a probabilistic (or real LLM-powered) AI agent.

🎮 **Try it now (no installation required)**  
https://drvl-demo.onrender.com/

*(Initial load may take 10–30 seconds on Render’s free tier; subsequent visits are fast.)*

### What the demo shows

- A lightweight AI agent attempts database operations: `READ`, `UPDATE`, `DELETE`, `DROP`
- The **Distributed Runtime Verification Layer (DRVL)** enforces deterministic policies at runtime:
  - Allowed actions execute immediately
  - Forbidden actions (`DROP`) are instantly blocked
  - Risky actions (`DELETE`) trigger **escalation requests**
- Escalation decisions (demo-only probabilistic logic):
  - ~35% auto-approved → executed (green)
  - ~35% auto-denied → blocked (red)
  - ~30% pending → queued for manual Approve/Deny via the dashboard
- Real-time dashboard features:
  - Toggle between simulated/random agent and real OpenAI LLM (bring your own key)
  - Live event stream with policy hash + cryptographic signature on every decision
  - Escalation queue with Approve/Deny buttons
  - Execution/block/approved counters
  - **Intentional integrity mismatches** (~15% of events) to visualize detection of tampered policy hashes or invalid signatures (red ✗ warning)

**Demo note on mismatches**  
~15% of events are deliberately tampered with (wrong policy hash or corrupted signature) to illustrate what integrity failure looks like in the UI.  
In a real deployment, policy hashes are designed to match for events under the current policy — the check detects changes, tampering, misconfigurations, or other anomalies.

### Real LLM Mode (optional)

- Toggle → enter your OpenAI API key (supports GPT-4o)
- Agent behavior becomes truly non-deterministic and occasionally risky
- **Warning:** consumes your OpenAI tokens (may incur costs). Simulated mode uses **zero tokens**.
- Key is sent once per session, never stored or logged.

### Why this demo matters

The DRVL demo is a **minimal, self-contained illustration** of core CEGP principles in action:

- Deterministic enforcement over probabilistic/agentic behavior
- Explicit escalation pathways with automated + human-in-the-loop control
- Cryptographic attestation (policy hash + event signature) for auditability
- Runtime constraint architecture that survives model non-determinism

It shows how governance can be **embedded in infrastructure** rather than layered on top as policy — exactly the structural shift this project explores.

→ Full demo source code & local setup instructions: [`demo/` folder README](./demo/README.md)

---

### [Note I — The AI Agent Spectrum](./notes/note-01-ai-agent-spectrum.md)
Introduces a capability-based classification of AI systems.

**Core thesis:** Governance must be capability-tiered.

Defines a spectrum based on:  
- Autonomy  
- Persistence  
- Goal formation  
- Economic participation  
- Infrastructure access  
- Identity continuity

### [Note II — From Agent Spectrum to Governance Architecture](./notes/note-02-from-agent-spectrum-to-governance-architecture.md)
Transitions from classification to structural governance implications.

**Core thesis:** Governance must move from declarative regulation to infrastructural architecture.

Explores:  
- Why uniform regulation fails  
- How governance attaches to leverage points  
- Compute, energy, identity, and infrastructure as control surfaces  
- Enforcement as a system layer

### [Note III — Capability-Tiered Governance & Enforcement Architecture](./notes/note-03-capability-tiered-governance-enforcement.md)
Formalizes governance maturity alignment and enforcement topology.

**Core thesis:** As AI systems gain persistence, planning capacity, and economic agency, governance must migrate from policy toward embedded runtime architecture.

Introduces:  
- A four-tier capability spectrum  
- Governance maturity alignment  
- Runtime constraint layers  
- Verification architecture  
- Enforcement node networks  

Enforcement becomes an architectural synchronization challenge.

### [Note IV — Enforcement Primitives & Runtime Constraint Architecture](./notes/note-04-enforcement-primitives.md)
Formalizes interoperable enforcement primitives and establishes Compute Gating as the sovereignty hinge.

**Core thesis:** Policy does not scale at machine speed. Infrastructure does.

Governance must embed into runtime systems through interoperable enforcement primitives, with compute gating anchoring sovereign control over scalable capability.

Defines:  
- A taxonomy of enforcement primitives  
- Compute gating regimes by capability tier  
- Distributed enforcement topologies  
- Geopolitical leverage and structural failure modes  

Sovereign leverage in advanced AI ecosystems increasingly correlates with control over scalable compute access.

### [Note V — Capability-Tiered Runtime Governance for Persistent AI Agents](./notes/note-05-enterprise-deployment-model.md)
**Transitions from structural doctrine to deployable architecture within enterprise AI environments.**

**Core thesis:**  
Capability-tiered runtime governance can be piloted within enterprise multi-agent orchestration systems without requiring regulatory reform.

**Demonstrates:**

- Tier-based runtime enforcement layering
- Identity-bound persistent agents
- Compute & execution gating within enterprise infrastructure
- Escalation and revocation mechanisms
- Progressive autonomy scaling models

This note serves as a **practical validation pathway** for embedded governance architecture.

## Protocol Modules

In addition to conceptual and architectural research, this project develops **modular enforcement protocol specifications** derived from the broader capability-tiered governance framework.

### [CEGP v0.1 — Compute Escalation Governance Protocol](./protocols/cegp/cegp-v0.1.md)  
**A Deterministic Governance Primitive for Autonomy-Linked Compute Expansion**

CEGP formalizes **cryptographically enforced compute envelopes** with structured escalation pathways embedded directly into AI execution infrastructure.

The protocol introduces:

- **Signed Compute Envelopes** defining agent capability and resource boundaries  
- **Deterministic boundary enforcement at the orchestration layer**  
- **Explicit escalation requests** for capability expansion beyond envelope limits  
- **Risk-tiered governance thresholds** proportional to operational autonomy  
- **Escalating governance friction tied to compute expansion**  
- **Optional public hash anchoring** for tamper-evident auditability

CEGP attaches governance friction to **compute expansion and infrastructure execution**, rather than attempting to interpret or regulate model cognition.

The protocol functions independently of blockchain infrastructure, though **optional external hash commitments** may strengthen audit guarantees in high-assurance environments.

CEGP is designed as a **modular enforcement primitive** within the broader capability-tiered governance architecture.

**Structural Logic**

As agents scale in autonomy, compute requirements increase.  
As compute requirements increase, governance friction increases.  
Escalation becomes progressively constrained, auditable, and expensive.

This mechanism transforms governance from a policy layer into a **deterministic control plane for autonomous compute systems**.

Governance therefore attaches to **deterministic infrastructure boundaries**, not to subjective interpretation of model behavior.

CEGP is designed to be:

- A **modular governance enforcement primitive**
- **Compatible with enterprise orchestration environments**
- **Composable with distributed runtime verification layers**
- **Potentially layerable onto public blockchain infrastructure**
- **Sovereignty-aware and non-centralized by default**

CEGP is not a global control system.  
It is a **compute-linked escalation conditioning mechanism** designed to introduce deterministic governance boundaries into probabilistic AI agent ecosystems.

## Governance Architecture Overview

### Deterministic Governance Architecture

![Capability-Tiered Governance Architecture](./docs/cegp-architecture.png)
Diagram version: v0.2  
Architecture status: Conceptual structural model (non-normative)

This architecture establishes a **deterministic governance control plane** between autonomous AI agents and the infrastructure they operate on.

While the diagram focuses on the enforcement pathway, the architecture supports **capability-tiered governance**: AI systems classified by capability tier experience proportional governance friction, reflected in:

- Escalation requirements
- Envelope validation
- Audit checkpoints

Capability tiers serve as inputs into the **compute envelope** and **orchestration control layer**, shaping how escalation requests are evaluated and approved.

Governance is implemented as **deterministic enforcement logic** embedded directly into infrastructure layers — rather than relying on post-deployment policy. Key mechanisms include:

- Compute envelope enforcement
- Orchestration control layer validation
- Escalation and revocation pathways
- Identity verification and continuity controls
- Deployment authorization and economic interface conditioning
- Integration with the **Compute Escalation Governance Protocol (CEGP)**

Enforcement operates across four primary layers:

- Identity
- Compute allocation
- Deployment orchestration
- Economic interaction

It conditions access to scalable capabilities rather than attempting to retroactively constrain behavior.

**Compute gating** refers to infrastructural mechanisms that condition access to scalable training and inference resources based on:

- Capability tier classification
- Governance maturity alignment

**CEGP** represents one instantiation of compute-linked escalation conditioning.

### Why This Matters

If capability expansion is unconstrained, power and influence can concentrate uncontested.

By introducing:

- explicit checkpoints
- infrastructure commitments
- economic signaling
- distributed verification

governance scales proportionally with system capability.

The goal is **not** to restrict innovation — it is to ensure **alignment** between capability expansion and governance maturity, maintaining predictable and auditable infrastructure control.

### Threat & Risk Considerations

 - Centralization & concentration risk

 - Regulatory capture risk

 - Sovereign fragmentation

 - Over-constraint vs innovation suppression

 - Governance as geopolitical leverage

Autonomous multi-agent environments introduce cascading failure risk, where small model errors or hallucinations propagate through toolchains and agent networks. Runtime constraint layers and compute envelopes function as containment boundaries to limit uncontrolled capability propagation.

**Threat model:** [CEGP Threat Model](./protocols/cegp/threat-model.md)

### Use Cases: Where CEGP Adds Value

CEGP is designed to embed governance directly into execution infrastructure. Example scenarios include:

- **AI Agent Platforms**  
  Multi-agent orchestration environments where persistent agents require capability-tiered constraints.

- **Sovereign AI Infrastructure**  
  Government or regulated cloud deployments where deterministic control over compute escalation is necessary.

- **Regulated Financial AI Systems**  
  Automated trading, treasury operations, or multi-tenant financial computation with audit and escalation requirements.

- **Multi-Tenant Model Hosting**  
  AI marketplaces or enterprise SaaS where isolated compute environments must enforce capability boundaries.

- **Critical Infrastructure AI**  
  Industrial, energy, or healthcare AI where compute activation and escalation must be deterministic and auditable.
  
**Use cases:** [CEGP Use Cases](./cegp-use-cases.md)

### Important Clarification

This repository does not assume:
- Mandatory blockchain anchoring
- Mandatory Bitcoin integration
- Universal fee mechanisms
- A single sovereign compute regime

CEGP is explored as a structural candidate — not as ideological doctrine.

Enterprise pilots may precede sovereign-scale integration.

## Emerging Phase: Jurisdiction & Sovereignty

The next phase of this work develops the jurisdictional and sovereign implications of enforcement architecture.

As enforcement becomes infrastructural and partially autonomous, key questions emerge:

- Where does jurisdiction attach in distributed AI systems?  
- Who governs enforcement nodes?  
- How do sovereign compute regimes interact?  
- How is cross-border enforcement coordinated or contested?  
- What prevents enforcement concentration from becoming systemic power capture?

As enforcement becomes infrastructural, sovereignty design becomes inseparable from AI governance architecture.

Enterprise deployment environments provide an initial proving ground for runtime governance architectures. Structured pilot environments allow enforcement primitives to mature operationally before sovereign-scale integration.

## Risks & Structural Tensions

Any enforcement architecture introduces structural tradeoffs. This project explicitly examines:

- Centralization and concentration risk  
- Regulatory capture risk  
- Sovereign fragmentation  
- Innovation suppression through over-constraint  
- Governance infrastructure becoming geopolitical leverage  

These risks are not peripheral — they are integral to the design problem.

## Project Approach

This initiative proceeds sequentially:

1. Map the terrain  
2. Clarify capability categories  
3. Identify structural leverage points  
4. Develop enforcement architecture models  
5. Pilot deployable runtime control architectures   
6. Analyze jurisdictional and sovereign implications
7. Articulate strategic doctrine considerations 

Analytical foundations precede policy positioning.

## Non-Goals

This repository does not:

- Propose a global centralized AI authority  
- Advocate premature capability caps  
- Promote broad surveillance expansion  
- Restrict open research by default  
- Assume a single geopolitical governance model  

The work focuses on structural alignment and sovereignty-aware architecture — not prescriptive overreach.

## Working Assumptions

These assumptions are examined, not asserted:

- AI systems will increase in autonomy and persistence  
- Economically active agents will proliferate  
- Compute concentration will shape geopolitical leverage  
- Governance will increasingly attach to infrastructure  
- Enforcement cannot remain purely declarative  
- Sovereignty will increasingly map to control over scalable compute and enforcement nodes  

## Initiative Position

This repository represents early-stage development of a capability-tiered governance and enforcement doctrine for advanced AI systems.

It aims to complement — not replace — existing frameworks such as:

- ISO/IEC JTC 1/SC 42  
- NIST AI Risk Management Framework  

The contribution is structural:  
- Capability-tiered alignment  
- Enforcement architecture modeling  
- Sovereignty-aware governance design  

## Objective

The objective is to:

- Formalize classification frameworks  
- Define enforcement architecture requirements  
- Model interoperable enforcement primitives  
- Clarify jurisdictional attachment points  
- Develop sovereignty-aware governance doctrine  
- Contribute to emerging standards discourse  

This remains an architectural and strategic exploration phase.

Future iterations may include:  
- Draft technical specifications  
- Reference enforcement topologies  
- Sovereign compute governance models  
- Collaborative standards alignment  

## Audience

- Governance advisors  
- Policy designers  
- Infrastructure architects  
- National security analysts  
- Institutional leaders  
- AI systems designers  
- Sovereign technology strategists  

## Collaboration & Engagement

The AI Governance Project welcomes substantive engagement from researchers, institutional leaders, and practitioners working at the intersection of AI systems design, enforcement architecture, and sovereignty.

We particularly welcome:

- Research on enforcement primitives or runtime constraint systems  
- Feedback on capability-tiered classification  
- Proposals for verifiable identity or cross-agent verification models  
- Perspectives on sovereign compute regimes  
- Jurisdictional coordination models  
- Power-distribution analysis in enforcement networks  

Focused structural critique is encouraged.

### How to Engage

If your work intersects with capability-tiered governance, enforcement architectures, identity continuity, jurisdictional attachment, interoperable enforcement nodes, or sovereign compute regimes:

→ Open an issue describing the overlap or proposed contribution.

For deeper discussion, formal critique, collaborative refinement, or potential standards alignment:

→ Contact the project lead directly.

Please reference specific notes or architectural elements to ensure focused dialogue.

## Contact

**Federico Blanco Sánchez-Llanos**  
Email: fsllanos@gmail.com  
LinkedIn: [linkedin.com/in/fedblanco](https://www.linkedin.com/in/fedblanco)

## License

Creative Commons Attribution–NonCommercial 4.0 International (CC BY-NC 4.0).

Commercial use, institutional embedding, or derivative advisory applications require explicit permission.
