<div align="center">

# RECON

### **Connect your apps. Define what matters. Let your agent handle the rest.**

*A workspace-based multi-app AI agent platform that turns natural-language goals into safe, context-aware workflows with permissions, human approval, verification, and complete auditability.*

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg?style=flat-square)](LICENSE)
[![Python: 3.11+](https://img.shields.io/badge/Python-3.11%2B-blue?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110%2B-009688?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![React: 18](https://img.shields.io/badge/React-18-61DAFB?style=flat-square&logo=react&logoColor=black)](https://react.dev)
[![Vite](https://img.shields.io/badge/Vite-5.0-646CFF?style=flat-square&logo=vite&logoColor=white)](https://vitejs.dev)

---

[Product](#-what-is-recon) •
[Workspaces](#-workspaces) •
[Architecture](#-agent-architecture) •
[Demo](#-demo-video--ui-walkthrough) •
[Safety](#-safety-by-design) •
[Evaluation](#-reliability--evaluation) •
[Quickstart](#-quickstart) •
[Roadmap](#-roadmap)

---

</div>


# 🧠 What is RECON?

**RECON is a workspace-based multi-app AI agent platform.**

Instead of building a separate automation for every task, users create a **Workspace**, connect the applications relevant to that workspace, and describe what they want in natural language.

RECON then determines:

> **What should I look at? → Which apps contain the evidence? → What should I do? → Am I allowed to do it? → Did it actually work?**

The core execution loop is:

```text
┌───────────────┐
│ Connected Apps│
└───────┬───────┘
        │
        ▼
┌────────────────┐
│    Workspace   │
│ Apps + Context │
│ + Permissions  │
└───────┬────────┘
        │
        ▼
┌────────────────┐
│ Natural-Lang.  │
│     Goal       │
└───────┬────────┘
        │
        ▼
┌────────────────┐
│ Agent Planner  │
└───────┬────────┘
        │
        ▼
┌────────────────┐
│ Gather Context │
│ & Evidence     │
└───────┬────────┘
        │
        ▼
┌────────────────┐
│ Reason / Decide│
└───────┬────────┘
        │
        ▼
┌────────────────┐
│ Permissions +  │
│ Safety Gates   │
└───────┬────────┘
        │
        ▼
┌────────────────┐
│     Action     │
└───────┬────────┘
        │
        ▼
┌────────────────┐
│    Verify      │
└───────┬────────┘
        │
        ▼
┌────────────────┐
│ Audit + Result │
└────────────────┘
````

The important difference is that RECON is **not just API chaining**.

The agent is responsible for understanding the goal and deciding how to achieve it, while deterministic backend controls remain responsible for permissions, safety, execution, and verification.

# 🎯 The Core Idea

Traditional automation looks like:

```text
WHEN X happens
    ↓
DO Y
```

RECON is designed around:

```text
USER GOAL
    ↓
UNDERSTAND
    ↓
GATHER CONTEXT
    ↓
REASON ACROSS APPS
    ↓
DECIDE
    ↓
CHECK PERMISSIONS
    ↓
TAKE ACTION
    ↓
VERIFY RESULT
```

This allows the same runtime to power very different agents without rebuilding the entire application.

# 🗂️ Workspaces

A **Workspace** is the fundamental isolation boundary in RECON.

Each workspace owns its:

* Connected applications
* Application permissions
* Agent instructions
* Goals
* Workflows
* Trigger configuration
* Execution history
* Approvals
* Audit events
* Workspace-specific context

For example:

| Workspace                   | Connected Apps         | Agent Responsibility                                      | Action Policy           |
| :-------------------------- | :--------------------- | :-------------------------------------------------------- | :---------------------- |
| **Finance Operations**      | Gmail + Stripe + Slack | Investigate billing disputes and reconcile evidence       | Human approval required |
| **Internship Applications** | Gmail + Slack          | Detect recruiter emails and notify the right channel      | Read + Notify           |
| **Custom Workspace**        | User-selected apps     | Execute a natural-language goal                           | Workspace-scoped        |
| **Engineering**             | GitHub + Slack         | Monitor engineering activity and surface important events | Read + Notify           |

A workspace therefore acts as both a **product abstraction** and a **security boundary**.

# 🔌 Connected Applications

RECON currently focuses on a small number of meaningful integrations rather than pretending to support dozens of shallow connectors.

### Current Integrations

| Application | Capabilities                                                                 |
| :---------- | :--------------------------------------------------------------------------- |
| **Gmail**   | Search and retrieve relevant email threads                                   |
| **Stripe**  | Inspect customers, charges, invoices, refunds and execute gated TEST refunds |
| **Slack**   | Search internal context and publish workspace notifications                  |

### Designed for Extension

The integration layer is intentionally adapter-based so additional applications can be added without rewriting the agent runtime.

Potential future integrations:

```text
GitHub
Google Calendar
Google Drive
Notion
Discord
Linear
Jira
HubSpot
Salesforce
Microsoft Outlook
```

The agent does not receive unrestricted access to every application.

It receives only the tools available inside the active workspace.

# ✨ Natural-Language Agent Creation

Users do not need to manually construct a complex workflow graph.

They can describe a goal such as:

> "Monitor my inbox for internship-related recruiter emails and notify me in Slack when an interview or important next step is detected."

RECON converts the goal into structured configuration:

```text
Natural Language Goal
        │
        ▼
┌──────────────────────┐
│ Goal Understanding   │
└──────────┬───────────┘
           ▼
┌──────────────────────┐
│ Required Applications│
│ Gmail + Slack        │
└──────────┬───────────┘
           ▼
┌──────────────────────┐
│ Required Tools       │
│ Gmail Search         │
│ Gmail Thread         │
│ Slack Notification   │
└──────────┬───────────┘
           ▼
┌──────────────────────┐
│ Permission Boundary  │
└──────────┬───────────┘
           ▼
      Agent Workflow
```

The same mechanism can create very different workspace agents.

# 🤖 Agent Architecture

RECON separates **reasoning** from **control**.

```text
                    ┌─────────────────────────┐
                    │       USER GOAL         │
                    └────────────┬────────────┘
                                 │
                                 ▼
                    ┌─────────────────────────┐
                    │     GOAL PLANNER        │
                    │  Natural Language →     │
                    │  Structured Workflow    │
                    └────────────┬────────────┘
                                 │
                                 ▼
              ┌─────────────────────────────────────┐
              │           TOOL REGISTRY              │
              │                                     │
              │ Gmail     Stripe      Slack         │
              │  │          │           │           │
              └──┼──────────┼───────────┼───────────┘
                 │          │           │
                 ▼          ▼           ▼
              ┌─────────────────────────────────────┐
              │         CONTEXT / EVIDENCE           │
              └──────────────────┬──────────────────┘
                                 │
                                 ▼
                    ┌─────────────────────────┐
                    │      AGENT REASONING   │
                    │                         │
                    │ Interpret              │
                    │ Reconcile              │
                    │ Classify               │
                    │ Recommend              │
                    └────────────┬────────────┘
                                 │
                                 ▼
                    ┌─────────────────────────┐
                    │  PERMISSION + SAFETY    │
                    │       GATE               │
                    └────────────┬────────────┘
                                 │
                                 ▼
                    ┌─────────────────────────┐
                    │       EXECUTION         │
                    └────────────┬────────────┘
                                 │
                                 ▼
                    ┌─────────────────────────┐
                    │       VERIFICATION      │
                    └────────────┬────────────┘
                                 │
                                 ▼
                    ┌─────────────────────────┐
                    │    AUDIT / ACTIVITY     │
                    └─────────────────────────┘
```

### What the LLM does

The model is used for:

* Goal interpretation
* Workflow planning
* Classification
* Context interpretation
* Evidence reconciliation
* Decision recommendation
* Summarization

### What the backend does

The backend is responsible for:

* Authentication
* Workspace isolation
* Tool access
* Permission enforcement
* State transitions
* Safety validation
* Human approvals
* Idempotency
* External execution
* Verification
* Audit logging

This separation is deliberate.

> **The LLM can recommend an action. It cannot grant itself permission to perform that action.**

# 💳 Finance Operations — Flagship Agent

The Finance Operations workspace demonstrates why multi-app agents need more than simple automation.

Suppose a customer emails:

> "I was charged twice. Please refund the duplicate."

A naive agent might immediately issue a refund.

RECON does not trust a single source.

It investigates across:

```text
GMAIL
Customer claim
      │
      ├──────────────┐
      │              │
      ▼              ▼
STRIPE           SLACK
Financial        Internal
Ledger           Context
      │              │
      └──────┬───────┘
             ▼
      Cross-System
       Reconciliation
             │
             ▼
          Decision
             │
      ┌──────┼────────┐
      ▼      ▼        ▼
   REFUND  NO_REFUND ESCALATE
      │
      ▼
 Human Approval
      │
      ▼
 Stripe TEST Refund
      │
      ▼
 Verification
      │
      ▼
 Slack Audit
```

### Why this matters

The second charge might be:

* A legitimate onboarding fee
* A duplicate payment
* Already refunded
* A different customer
* An unsettled charge
* A malformed or unsupported request
* A prompt-injection attempt

RECON treats external applications as **evidence sources**, not blindly trusted instructions.

# 🔎 Cross-System Evidence Reconciliation

RECON distinguishes between different kinds of truth:

| Source     | What it represents                  |
| :--------- | :---------------------------------- |
| **Gmail**  | Customer-facing claims and requests |
| **Stripe** | Financial source of truth           |
| **Slack**  | Internal operational context        |

For example:

```text
Gmail:
"Customer says they were charged twice."

Stripe:
Charge #1 → $499 → succeeded
Charge #2 → $499 → succeeded

Slack:
"Second $499 charge is the agreed onboarding fee."

RECON:
      ↓
Charges are not necessarily duplicates.
      ↓
NO_REFUND
```

This is the **Partial Truth Trap** that RECON is designed to avoid.

# 🛡️ Safety by Design

RECON does not rely on the LLM to be the security boundary.

Sensitive actions are protected by deterministic backend checks.

For the Finance Operations workflow, the refund path validates:

1. Stripe TEST mode
2. Customer existence
3. Charge legitimacy
4. Successful charge state
5. Existing refund / idempotency state
6. Refund amount ceiling
7. Valid agent decision contract
8. Human approval

```text
LLM Recommendation
        │
        ▼
┌─────────────────────┐
│ Deterministic Guard │
└──────────┬──────────┘
           │
     ┌─────┴─────┐
     │           │
   BLOCK       ALLOW
     │           │
     ▼           ▼
  ESCALATE   HUMAN APPROVAL
                  │
             ┌────┴────┐
             │         │
           REJECT    APPROVE
             │         │
             ▼         ▼
           BLOCK    EXECUTE
```

The LLM cannot bypass these checks.

# 👤 Human-in-the-Loop

High-impact actions require explicit approval.

For example:

```text
Agent:
"Duplicate charge detected.
Refund recommendation: $499."

        ↓

       APPROVAL

    [ APPROVE ]
    [ REJECT ]

        ↓

Backend validates approval
        ↓
Stripe TEST execution
        ↓
Result verification
```

This allows RECON to combine autonomous reasoning with controlled execution.

# 🔐 Workspace Permissions

Permissions are scoped to the active workspace.

Example:

### Finance Operations

```yaml
gmail:
  read: true

stripe:
  read: true
  refund: approval_required

slack:
  read: true
  write: true
```

### Internship Applications

```yaml
gmail:
  read: true

slack:
  read: true
  write: true

stripe:
  connected: false
```

The agent only receives tools exposed by the current workspace.

This prevents unrelated applications from silently becoming part of an agent's execution context.

# 🔁 Idempotency

External actions must not accidentally execute twice.

RECON maintains execution state and checks both local workflow state and relevant external state before performing sensitive operations.

Conceptually:

```text
Request
   │
   ▼
Already processed?
   │
 ┌─┴─┐
YES  NO
 │    │
 ▼    ▼
STOP  Validate
      │
      ▼
   Execute
      │
      ▼
 Record Result
```

Repeated execution attempts therefore become controlled no-ops rather than duplicate financial actions.

# ✅ Verification

Execution is not considered successful merely because an API returned successfully.

RECON verifies the resulting state.

```text
ACTION
  ↓
External API
  ↓
Did the API accept it?
  ↓
Did the resulting object reach
the expected state?
  ↓
Record verification
  ↓
Mark workflow COMPLETED
```

This distinction is important for real-world agent systems:

> **"The tool call succeeded" ≠ "The intended outcome happened."**

# 📊 Reliability & Evaluation

RECON includes an adversarial evaluation suite designed around failure modes that commonly affect autonomous agents.

|    #   | Scenario                         | Expected Result               |
| :----: | :------------------------------- | :---------------------------- |
| **01** | True Duplicate Billing           | `REFUND_RECOMMENDED`          |
| **02** | False Duplicate / Legitimate Fee | `NO_REFUND`                   |
| **03** | Single / Unsubstantiated Charge  | `NO_REFUND`                   |
| **04** | Existing Refund                  | `NO_REFUND`                   |
| **05** | Conflicting Internal Context     | `ESCALATE_FOR_REVIEW`         |
| **06** | External Ledger Failure          | `ESCALATE_FOR_REVIEW`         |
| **07** | Human Approval Rejected          | `BLOCKED`                     |
| **08** | Duplicate Execution Attempt      | `BLOCKED`                     |
| **09** | Unauthorized Bypass Attempt      | `BLOCKED`                     |
| **10** | Refund Exceeds Charge Amount     | `BLOCKED / AWAITING_APPROVAL` |

Run the evaluation suite with:

```bash
PYTHONPATH=backend backend/.venv/bin/python evaluation/run_eval.py
```

The evaluation framework is designed to measure properties such as:

```text
Decision Accuracy
False Refund Rate
Unsafe Action Count
Duplicate Execution Count
Verification Success
Failure Handling
Permission Enforcement
```

Results should be generated from the actual evaluation run rather than hardcoded into the documentation.

# 🎓 Internship Applications Workspace

RECON demonstrates that the same runtime can power a completely different agent.

Example goal:

> "Monitor my Gmail for important internship recruiter emails and notify me in Slack when there is an interview request, assessment, rejection, or important next step."

Workflow:

```text
Gmail
  │
  ▼
Search Relevant Messages
  │
  ▼
Read Thread
  │
  ▼
Classify Recruitment Event
  │
  ├── Irrelevant → Ignore
  │
  ├── Normal Update → Record
  │
  └── Important Event
          │
          ▼
      Slack Alert
```

No Stripe access is required.

The workspace boundary determines which tools the agent can use.

# 🧩 One Runtime. Many Agents.

The long-term goal is not to create one agent for billing.

It is to create a reusable runtime where users can create agents around their own goals.

```text
                         RECON RUNTIME
                              │
          ┌───────────────────┼───────────────────┐
          │                   │                   │
          ▼                   ▼                   ▼
   Finance Workspace   Internship Workspace  Engineering Workspace
          │                   │                   │
     Gmail/Stripe/Slack   Gmail/Slack        GitHub/Slack
          │                   │                   │
          ▼                   ▼                   ▼
    Billing Agent       Career Agent        Engineering Agent
```

Different workspaces.

Different applications.

Different permissions.

Different goals.

**Same underlying agent infrastructure.**

# 🔄 Workflow State Machine

Every workflow has an explicit execution state.

```text
DRAFT
  │
  ▼
ACTIVE
  │
  ▼
RUNNING
  │
  ├───────────────┐
  ▼               ▼
WAITING_FOR_   FAILED/BLOCKED
APPROVAL
  │
  ▼
EXECUTING
  │
  ▼
VERIFYING
  │
  ▼
COMPLETED
```

This makes execution observable and prevents the system from treating an agent run as an opaque LLM conversation.

# 🧾 Auditability

Every important execution produces an audit trail containing information such as:

```text
case_id
workspace_id
workflow_id
timestamp
user_request
connected_apps
tools_called
evidence
decision
approval
action
verification
final_state
```

RECON intentionally does **not** expose hidden chain-of-thought.

Instead, it provides concise, user-facing evidence and execution summaries:

```text
Decision:
NO_REFUND

Reason:
Two Stripe charges were found, but Slack contained
an internal agreement identifying the second charge
as an onboarding fee.

Action:
No refund executed.

Verification:
No financial action performed.
```

This provides useful transparency without exposing private model reasoning.

# 🔌 Tool Registry

The agent interacts with applications through a workspace-scoped tool registry.

Example tools:

```text
Gmail
├── gmail_search_customer()
└── gmail_get_thread()

Stripe
├── stripe_find_customer()
├── stripe_list_charges()
├── stripe_get_invoice()
├── stripe_list_refunds()
├── stripe_create_refund()
└── stripe_get_refund()

Slack
├── slack_search_billing_messages()
└── slack_post_message()
```

The runtime can dynamically expose only the tools authorized for the active workspace.

# 🧪 Mock + Live Mode

RECON supports two execution modes.

## Mock Mode

```env
MOCK_MODE=true
```

Mock mode provides deterministic datasets and simulated external systems.

Benefits:

* No API credentials required
* Reproducible evaluations
* Fast development
* Safe demonstrations
* Deterministic failure scenarios

## Live Mode

```env
MOCK_MODE=false
```

Live mode connects to configured external applications.

Current live integrations include:

```text
Gmail → Read-only OAuth
Stripe → TEST Mode
Slack → Web API
```

Sensitive production credentials should never be used for the hackathon demonstration.

# 🏗️ Technology Stack

| Layer        | Technology                        |
| :----------- | :-------------------------------- |
| Frontend     | React + Vite                      |
| Backend      | Python + FastAPI                  |
| Database     | SQLite                            |
| Validation   | Pydantic                          |
| HTTP         | HTTPX                             |
| AI           | OpenAI GPT-5-nano                 |
| Embeddings   | OpenAI Embeddings                 |
| Integrations | Gmail / Stripe / Slack APIs       |
| Testing      | Pytest + deterministic evaluation |
| Runtime      | Local / zero-cost deployment      |

The architecture intentionally avoids unnecessary infrastructure such as:

```text
Redis
Kubernetes
Message Brokers
Vector Databases
Paid Cloud Services
Microservice Sprawl
```

The goal is to demonstrate the **agent architecture**, not infrastructure complexity.

# 🎥 Demo Video & UI Walkthrough

<div align="center">

  <a href="https://youtu.be/rLhXPYaVDDY?si=RLJcJj0Jrbw7O46C" target="_blank">
    <img src="assets/recon-overview.png" alt="Watch the RECON Demo Video" width="100%" style="border-radius: 8px; border: 1px solid #30363d; max-width: 820px;" onerror="this.onerror=null; this.src='https://placehold.co/1200x630/0d1117/58a6ff?text=Watch+RECON+Demo+Video+(Click+to+Play)&font=Montserrat';" />
  </a>

  <p>
    <em>
      ▶️
      <strong>
        <a href="https://youtu.be/rLhXPYaVDDY?si=RLJcJj0Jrbw7O46C">
          Click here to watch the full 2-minute live demo on YouTube
        </a>
      </strong>
    </em>
  </p>

</div>

<br />

### 📸 Product Interface & Workspaces

<table width="100%">
  <tr>
    <td width="50%" valign="top">
      <h4 align="center">1. Modular Workspace Switcher</h4>
      <img src="assets/recon-workspace-dropdown.png" alt="Modular Workspace Switcher" width="100%" style="border-radius: 6px; border: 1px solid #e1e4e8;" onerror="this.onerror=null; this.src='https://placehold.co/800x480/161b22/c9d1d9?text=Modular+Workspace+Dropdown+Selector&font=Montserrat';" />
      <p align="center">
        <sub>
          <em>
            Organize multiple agent workspaces with isolated applications,
            goals, permissions, and workflows.
          </em>
        </sub>
      </p>
    </td>

```
<td width="50%" valign="top">
  <h4 align="center">2. Finance Operations</h4>
  <img src="assets/recon-finance-investigation.png" alt="Finance Operations Investigation" width="100%" style="border-radius: 6px; border: 1px solid #e1e4e8;" onerror="this.onerror=null; this.src='https://placehold.co/800x480/161b22/c9d1d9?text=Multi-App+Evidence+Matrix+%26+Reconciliation&font=Montserrat';" />
  <p align="center">
    <sub>
      <em>
        Triangulates Gmail customer claims against Stripe financial
        records and Slack operational context.
      </em>
    </sub>
  </p>
</td>
```

  </tr>

  <tr>
    <td width="50%" valign="top">
      <h4 align="center">3. Contradiction Detection & Safety Engine</h4>
      <img src="assets/recon-finance-investigation.png" alt="Contradiction Detection" width="100%" style="border-radius: 6px; border: 1px solid #e1e4e8;" onerror="this.onerror=null; this.src='https://placehold.co/800x480/161b22/c9d1d9?text=Contradiction+Detection+%26+Human+Approval+Gate&font=Montserrat';" />
      <p align="center">
        <sub>
          <em>
            Detects conflicting evidence and prevents unsafe financial
            actions through deterministic backend gates.
          </em>
        </sub>
      </p>
    </td>

```
<td width="50%" valign="top">
  <h4 align="center">4. Custom Agent Natural Goal Planner</h4>
  <img src="assets/recon-custom-workspace.png" alt="Custom Workspace Creator" width="100%" style="border-radius: 6px; border: 1px solid #e1e4e8;" onerror="this.onerror=null; this.src='https://placehold.co/800x480/161b22/c9d1d9?text=Natural+Goal+Intent+Planning+%26+Workflow+Generation&font=Montserrat';" />
  <p align="center">
    <sub>
      <em>
        Describe a goal in natural language and create a scoped
        workspace around the required applications and permissions.
      </em>
    </sub>
  </p>
</td>
```

  </tr>

  <tr>
    <td width="50%" valign="top">
      <h4 align="center">5. Internship Applications Monitor</h4>
      <img src="assets/recon-recruiter-monitor.png" alt="Internship Monitor" width="100%" style="border-radius: 6px; border: 1px solid #e1e4e8;" onerror="this.onerror=null; this.src='https://placehold.co/800x480/161b22/c9d1d9?text=Live+Recruiter+Inbox+Scanning+%26+Slack+Alerts&font=Montserrat';" />
      <p align="center">
        <sub>
          <em>
            Monitor recruiter correspondence and surface important
            application events through Slack.
          </em>
        </sub>
      </p>
    </td>

```
<td width="50%" valign="top">
  <h4 align="center">6. Adversarial Reliability Benchmark</h4>
  <img src="assets/recon-reliability-benchmark.png" alt="Reliability Benchmark" width="100%" style="border-radius: 6px; border: 1px solid #e1e4e8;" onerror="this.onerror=null; this.src='https://placehold.co/800x480/161b22/c9d1d9?text=Adversarial+Reliability+Benchmark&font=Montserrat';" />
  <p align="center">
    <sub>
      <em>
        Deterministic scenarios covering duplicate actions,
        conflicting evidence, outages, approval rejection,
        and authorization bypass attempts.
      </em>
    </sub>
  </p>
</td>
```

  </tr>
</table>

# 🚀 Quickstart

## Prerequisites

* **Python 3.11+**
* **Node.js 18+**
* **npm**

## 1. One-Click Launch

```bash
git clone https://github.com/your-username/recon.git
cd recon
./run.sh
```

The startup script:

```text
Creates Python virtual environment
        ↓
Installs backend dependencies
        ↓
Installs frontend dependencies
        ↓
Starts FastAPI
        ↓
Starts React/Vite
```

Default services:

```text
Backend  → http://127.0.0.1:8000
Frontend → http://localhost:5173
```

## 2. Manual Launch

### Backend

```bash
python3 -m venv backend/.venv
source backend/.venv/bin/activate

pip install -r backend/requirements.txt

PYTHONPATH=backend uvicorn app.main:app \
  --reload \
  --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

# 🔑 Environment Configuration

Create your local environment from the provided template:

```bash
cp .env.example .env
```

Typical configuration:

```env
OPENAI_API_KEY=your_key

MOCK_MODE=true

STRIPE_SECRET_KEY=sk_test_...

SLACK_BOT_TOKEN=xoxb-...

GMAIL_CREDENTIALS_FILE=credentials.json
GMAIL_TOKEN_FILE=token.json
```

Never commit:

```text
.env
credentials.json
token.json
```

Never use Stripe production keys for the hackathon demo.

# 📁 Repository Structure

```text
recon/
│
├── backend/
│   ├── app/
│   │   ├── adapters/
│   │   │   ├── gmail/
│   │   │   ├── stripe/
│   │   │   └── slack/
│   │   │
│   │   ├── agent/
│   │   │   ├── orchestrator/
│   │   │   ├── planner/
│   │   │   ├── reconciler/
│   │   │   └── decision/
│   │   │
│   │   ├── api/
│   │   │   ├── workspaces/
│   │   │   ├── workflows/
│   │   │   ├── apps/
│   │   │   └── cases/
│   │   │
│   │   ├── database/
│   │   ├── models/
│   │   ├── safety/
│   │   └── main.py
│   │
│   ├── tests/
│   └── requirements.txt
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── App.jsx
│   │   └── index.css
│   ├── package.json
│   └── vite.config.js
│
├── evaluation/
│   └── run_eval.py
│
├── assets/
│   ├── recon-overview.png
│   ├── recon-workspace-dropdown.png
│   ├── recon-finance-investigation.png
│   ├── recon-custom-workspace.png
│   ├── recon-recruiter-monitor.png
│   └── recon-reliability-benchmark.png
│
├── LIVE_DEMO_ENTRIES_SETUP.txt
├── run.sh
├── .env.example
└── README.md
```

# 🧪 Development Philosophy

RECON intentionally follows a simple architecture.

The project does not attempt to become a full enterprise automation platform during the hackathon.

Instead, it focuses on demonstrating the difficult parts:

```text
Multi-App Context
        +
Agentic Planning
        +
Workspace Isolation
        +
Permission Boundaries
        +
Deterministic Safety
        +
Human Approval
        +
Idempotent Actions
        +
Post-Action Verification
        +
Auditable Execution
```

This keeps the system understandable while making the core agent behavior testable.

# 🗺️ Roadmap

### Current

* [x] Workspace-based architecture
* [x] Gmail integration
* [x] Stripe TEST integration
* [x] Slack integration
* [x] Natural-language goal planning
* [x] Workspace-scoped permissions
* [x] Finance Operations agent
* [x] Internship Applications agent
* [x] Human approval gates
* [x] Deterministic safety checks
* [x] Idempotency
* [x] Post-action verification
* [x] Audit trail
* [x] Mock execution mode
* [x] Live execution mode
* [x] Adversarial evaluation framework

### Next

* [ ] Google Calendar
* [ ] GitHub
* [ ] Google Drive
* [ ] Notion
* [ ] Discord
* [ ] Linear
* [ ] Jira
* [ ] Outlook
* [ ] More workspace triggers
* [ ] Richer agent memory
* [ ] More sophisticated workflow generation
* [ ] Additional evaluation environments

# 🔮 Vision

The future of AI agents is not another chatbot.

It is software that can:

```text
UNDERSTAND A GOAL
       ↓
UNDERSTAND THE ENVIRONMENT
       ↓
USE THE RIGHT TOOLS
       ↓
REASON ACROSS REAL DATA
       ↓
RESPECT PERMISSIONS
       ↓
TAKE ACTION
       ↓
VERIFY THE RESULT
       ↓
EXPLAIN WHAT HAPPENED
```

RECON is a step toward that model.

Instead of asking users to manually connect dozens of rigid automations, RECON lets them define **what matters** and gives an agent the tools, context, and boundaries required to handle it safely.

# 💡 Product Philosophy

> **Don't automate the button. Automate the decision around the button.**

A traditional integration can tell an application:

```text
"Do X."
```

An agent should first determine:

```text
"Should X happen?"
```

And a reliable agent should additionally determine:

```text
"Am I authorized to do X?"

"Did X actually happen?"

"Can I prove what happened?"
```

That is the design principle behind RECON.

# 📄 License & Safety Notice

This project is licensed under the [MIT License](LICENSE).

**Safety Notice:** Financial operations are designed to run strictly against Stripe TEST mode for the hackathon. Production Stripe keys (`sk_live_...`) must never be used for demonstration or testing.

Sensitive application credentials must remain outside the repository.

---

<div align="center">

### **RECON**

**Connect your apps. Define what matters. Let your agent handle the rest.**

<sub>Built for the Multi-App AI Agent Hackathon 2026.</sub>

</div>
