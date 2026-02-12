# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed
- Refactored project structure to industry-standard Python package layout
- Renamed `src/` to `omni_channel_ai_servicing/` for proper packaging
- Organized scripts into `scripts/` directory
- Moved manual test files to `tests/manual/`
- Added `Makefile` for common development tasks
- Added `.env.example` for configuration template
- Added LICENSE (MIT)

## [0.1.0] - 2026-02-11

### Added
- **Metrics Collection System**
  - MetricsCollector with counters, histograms, and gauges
  - Thread-safe metrics with Lock for concurrent access
  - Prometheus format export (`/metrics` endpoint)
  - JSON format export (`/metrics/summary` endpoint)
  - MetricsTimer context manager for operation timing
  - Integration with email poller and API routes
  - 12 comprehensive unit tests

- **Guardrails Validation System**
  - GuardrailService with input/output validation
  - PII detection (SSN, credit card, phone numbers)
  - SQL injection prevention
  - Hallucination detection (fake policy/account numbers)
  - Profanity and off-topic content warnings
  - Confidence threshold routing (default 0.7)
  - PII sanitization for secure logging
  - Prompt-based guardrails (SYSTEM_PROMPT_GUARDRAILS)
  - Integration with email processor, intent classifier, entity extractor
  - 27 comprehensive unit tests

- **Email Integration**
  - IMAP IDLE polling for real-time email processing
  - Email filtering by sender whitelist
  - Integration with LangGraph workflows
  - Automated response generation and sending

- **LangGraph Workflows**
  - Master router for intent-based routing
  - Address update workflow
  - Dispute/fraud workflow
  - Fallback workflow for unhandled intents
  - Policy-based decision making

- **LLM Integration**
  - Intent classification
  - Entity extraction
  - Response generation
  - RAG (Retrieval-Augmented Generation) foundation
  - Support for OpenAI, Gemini, Anthropic models

- **Infrastructure**
  - Docker and Docker Compose configuration
  - Kubernetes deployment manifests
  - Terraform infrastructure as code
  - Mock services for testing

- **Testing**
  - Unit tests for metrics, guardrails, and core logic
  - Integration tests for end-to-end workflows
  - Test data and sample emails

- **Documentation**
  - Architecture documentation
  - API contracts
  - Guardrails design document
  - Deployment guide
  - Sequence diagrams

### Fixed
- Deadlock in metrics collection (lock re-entry issue)
- Percentile calculation off-by-one error
- Email processing thread safety

### Technical Debt
- Consider migrating from regex to ML-based PII detection
- Add more comprehensive error handling
- Implement rate limiting for API endpoints
- Add distributed tracing (OpenTelemetry)

## [0.0.1] - 2026-01-15

### Added
- Initial project setup
- Basic FastAPI application structure
- Email client integration
- LangGraph graph definition
- Policy engine foundation
