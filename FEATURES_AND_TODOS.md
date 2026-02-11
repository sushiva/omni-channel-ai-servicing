# Omni-Channel AI Servicing — Features & Enhancement TODOs

## Existing Features (Implemented)

### LangGraph Workflow Engine
- StateGraph with Pydantic BaseModel as state schema
- Linear node chaining (add_node / add_edge)
- Conditional edges for policy check and intent-based routing
- Entry point configuration
- Graph compilation and async invocation (ainvoke)
- Address update workflow: classify_intent -> extract_entities -> apply_policy -> route_decision -> update_address/create_case -> generate_response

### Graph Nodes
- **classify_intent** — LLM-based intent classification (update_address, request_statement, report_fraud, unknown)
- **extract_entities** — LLM-based entity extraction returning structured JSON
- **route_decision** — routes to the correct action node based on intent
- **apply_policy** — placeholder policy check, short-circuits on violations
- **update_address** — calls core banking mock service to update customer address
- **create_case** — calls CRM mock service to create a support case
- **generate_response** — generates final user-facing response
- **send_notification** — sends email notification via mock service

### LLM Integration
- Async OpenAI client (gpt-4o-mini, temperature=0)
- Prompt templates for intent classification and entity extraction
- Environment variable loading via python-dotenv

### Integration Clients
- BaseServiceClient with async HTTP (httpx) — _post and _get helpers
- CoreBankingClient — update_address, get_customer
- CRMClient — create_case, add_note
- NotificationClient — send_email
- WorkflowClient — start_workflow, get_workflow

### Mock Services (FastAPI)
- Core Banking API — address update + customer lookup (SQLite-backed)
- CRM API — case creation + note addition
- Notification API — email sending (console output)
- Workflow API — workflow start + status lookup
- SQLite database with seeded test data (customer cust123)

### Configuration
- Centralized settings (MOCK_SERVICES_BASE_URL)
- .env support for API keys

---

## Enhancement TODOs

### Phase 1 — Observability

#### 1. Structured Logging
- **File:** `src/app/config/logging_config.py`
- **Scope:** Configure Python logging with JSON-formatted structured output
- **Integrate into:** All graph nodes, LLM client, integration clients
- **Why:** Visibility into every step of the pipeline

#### 2. Audit Logger
- **File:** `src/monitoring/audit_logger.py`
- **Scope:** Log every graph node transition, LLM call (prompt + response), and integration call (request + response)
- **Why:** Banking compliance — every action must be auditable

#### 3. Tracing
- **File:** `src/monitoring/tracing.py`
- **Scope:** Correlation ID per request that flows through all nodes and integration calls
- **Why:** End-to-end request tracing for debugging and incident response

#### 4. Monitoring Hooks
- **File:** `src/monitoring/metrics.py`
- **Scope:** Track LLM latency, node execution time, integration call duration, error counts
- **Why:** Operational awareness and performance visibility

### Phase 2 — Core Intelligence

#### 5. RAG + Policy Engine
- **Files:** `src/policy_engine/evaluator.py`, `src/policy_engine/validator.py`, `src/policy_engine/rules/*.yaml`, `src/llm/rag/vectorstore.py`, `src/llm/rag/retriever.py`, `src/llm/rag/loaders/policy_loader.py`
- **Scope:**
  - Load policy documents (YAML rules for address_update, dispute, channel_permissions)
  - Vector store for policy document embeddings
  - RAG retriever to ground LLM decisions in policy
  - Policy evaluator to validate actions against rules before execution
- **Why:** Core differentiator — AI decisions grounded in actual business policy

#### 6. LLM Fallback Chain
- **File:** `src/llm/client.py`
- **Scope:** Ollama (local) -> OpenAI -> Gemini -> Anthropic with automatic failover
- **Why:** Resilience — no single LLM provider dependency

### Phase 3 — LangGraph Advanced Features

#### 7. Checkpointer + Persistence
- **File:** `src/graph/workflows/address_update_graph.py`
- **Scope:** Add MemorySaver or SqliteSaver to graph.compile(checkpointer=...)
- **Why:** Persist state between runs; enables conversation continuity and crash recovery

#### 8. Human-in-the-Loop Interrupt
- **File:** `src/graph/workflows/address_update_graph.py`, `src/graph/nodes/update_address.py`
- **Scope:** interrupt_before on update_address node — pause for user confirmation before executing the address change
- **Why:** Real banking requirement — destructive operations need user confirmation

### Phase 4 — API & Workflows

#### 9. API Layer
- **Files:** `src/app/api/routes.py`, `src/app/api/schemas.py`
- **Scope:** POST /chat endpoint accepting user message + customer_id, returning graph result. Pydantic request/response schemas.
- **Why:** Exposes the graph as a usable REST API

#### 10. Dispute Workflow
- **File:** `src/graph/workflows/dispute_graph.py`
- **Scope:** Second LangGraph workflow for dispute handling (classify -> extract -> verify transaction -> apply dispute policy -> create case -> notify)
- **Why:** Shows the system is extensible beyond a single use case

### Phase 5 — Security & Quality

#### 11. PII Masking
- **File:** `src/app/security/pii_masking.py`
- **Scope:** Mask SSN, account numbers, email addresses in logs and LLM prompts
- **Why:** Banking compliance — PII must never leak into logs or third-party LLM calls

#### 12. Tests
- **Files:** `tests/unit/`, `tests/integration/`
- **Scope:** Unit tests for intent classification, policy evaluation, graph transitions. Integration test for end-to-end address update flow.
- **Why:** Validates the system works and shows engineering rigor

### Phase 6 — Deployment

#### 13. Gradio UI + Hugging Face Spaces
- **Files:** `app.py` (root), `Dockerfile`, HF Space metadata
- **Scope:** Chat-based Gradio interface, Docker packaging, HF Spaces deployment
- **Why:** Live demo that anyone can try

---

## Architecture Overview

```
User Message
    |
    v
[FastAPI /chat] --> [LangGraph StateGraph]
                         |
                    classify_intent (LLM)
                         |
                    extract_entities (LLM)
                         |
                    apply_policy (RAG + Rules)
                         |
                    route_decision
                    /          \
          update_address    create_case
          (Core Banking)     (CRM)
                    \          /
                    generate_response
                         |
                    send_notification
                         |
                         v
                   Final Response
```

## Tech Stack
- **Orchestration:** LangGraph
- **API:** FastAPI + Pydantic
- **LLM:** OpenAI (gpt-4o-mini) via async client
- **HTTP Client:** httpx (async)
- **Database:** SQLite (aiosqlite) for mock services
- **Environment:** python-dotenv
