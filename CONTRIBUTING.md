# Contributing to RECON

Thank you for your interest in contributing to **RECON** (Multi-App AI Agent Workspace Platform).

## Development Setup

### 1. Clone the repository
```bash
git clone https://github.com/your-username/recon.git
cd recon
```

### 2. Environment Configuration
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```
By default, `MOCK_MODE=true` is enabled. You can run all evaluation benchmarks and test scenarios locally without external API keys.

### 3. Launch with Run Script
```bash
./run.sh
```

## Running Tests & Benchmarks

### Backend Test Suite
```bash
PYTHONPATH=backend backend/.venv/bin/pytest backend/tests/test_workspaces_workflows.py
```

### Adversarial Evaluation Suite
```bash
PYTHONPATH=backend backend/.venv/bin/python evaluation/run_eval.py
```

### Frontend Build
```bash
cd frontend
npm run build
```

## Core Architectural Invariants

When contributing to RECON, preserve these non-negotiable architectural guarantees:
1. **The LLM Never Directly Executes Financial Actions**: The AI model is strictly restricted to returning structured recommendations. Financial execution is exclusively performed by deterministic Python backend logic.
2. **Deterministic Safety Validation**: All refund transactions must pass the 8-point deterministic safety engine and have verified human approval.
3. **Idempotency**: All operations must enforce duplicate prevention against local SQLite ledgers and upstream APIs.
4. **Clean Design Language**: No emojis in the user interface. Maintain the minimalist, high-contrast Stripe/Linear aesthetic with Inter and JetBrains Mono typography.
