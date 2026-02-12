# Project Structure Refactoring Plan

## Goal
Convert current structure to industry-standard Python package layout

## Current vs Target Structure

### Current (Non-standard)
```
omni-channel-ai-servicing/
├── src/                    # ❌ Non-standard for Python
│   ├── app/
│   ├── services/
│   └── ...
├── test_*.py               # ❌ Test files at root
├── run_*.sh                # ❌ Scripts at root
└── debug_credentials.py    # ❌ Debug files at root
```

### Target (Industry Standard)
```
omni-channel-ai-servicing/
├── omni_channel_ai_servicing/  # ✅ Package name matches import
│   ├── app/
│   ├── services/
│   └── ...
├── tests/                      # ✅ All tests here
├── scripts/                    # ✅ Organized scripts
├── config/                     # ✅ Centralized config
├── .github/workflows/          # ✅ CI/CD
├── Makefile                    # ✅ Common commands
└── .env.example                # ✅ Config template
```

---

## Phase 1: Package Rename (Breaking Change) ⚠️

### Step 1.1: Rename src/ → omni_channel_ai_servicing/
```bash
git checkout -b refactor/standardize-structure
mv src omni_channel_ai_servicing
```

### Step 1.2: Update all imports
**Before:** `from src.app.api import routes`
**After:** `from omni_channel_ai_servicing.app.api import routes`

**Files to update:**
- All Python files in the package
- All test files
- pyproject.toml
- setup.py (if exists)
- Shell scripts with Python paths

### Step 1.3: Update pyproject.toml
```toml
[project]
name = "omni-channel-ai-servicing"

[tool.setuptools.packages.find]
where = ["."]
include = ["omni_channel_ai_servicing*"]
exclude = ["tests*"]
```

---

## Phase 2: Organize Root-Level Files

### Step 2.1: Create scripts/ directory
```bash
mkdir -p scripts
mv run_*.sh scripts/
mv start_servers.sh scripts/
```

### Step 2.2: Move test files to tests/
```bash
mv test_email_simple.py tests/manual/
mv test_gmail_auth.py tests/manual/
mv debug_credentials.py tests/manual/
```

### Step 2.3: Create tools/ for utilities
```bash
mkdir -p tools
# Move any debug/utility scripts here
```

---

## Phase 3: Configuration Management

### Step 3.1: Create config/ directory
```bash
mkdir -p config
```

### Step 3.2: Create environment-specific configs
**config/default.yaml** - Base configuration
**config/development.yaml** - Local dev overrides
**config/production.yaml** - Prod settings
**config/test.yaml** - Test environment

### Step 3.3: Create .env.example
```bash
# Email Configuration
EMAIL_ADDRESS=your-email@example.com
EMAIL_PASSWORD=your-app-password
IMAP_SERVER=imap.gmail.com

# LLM Configuration
OPENAI_API_KEY=sk-...
GEMINI_API_KEY=...

# Service URLs
CORE_BANKING_URL=http://localhost:8001
CRM_URL=http://localhost:8002
```

### Step 3.4: Move existing config
```bash
# If you have config files scattered, consolidate them
mv src/app/config/*.yaml config/
```

---

## Phase 4: Add Standard Files

### Step 4.1: Create Makefile
```makefile
.PHONY: install test lint format run clean

install:
	uv pip install -e ".[dev]"

test:
	pytest tests/unit -v
	pytest tests/integration -v

test-cov:
	pytest tests/ --cov=omni_channel_ai_servicing --cov-report=html

lint:
	ruff check omni_channel_ai_servicing tests
	mypy omni_channel_ai_servicing

format:
	ruff format omni_channel_ai_servicing tests

run-api:
	python -m omni_channel_ai_servicing.app.main

run-email:
	python -m omni_channel_ai_servicing.services.email_idle_poller

docker-build:
	docker build -f infra/docker/Dockerfile -t omni-channel-ai .

docker-run:
	docker-compose -f infra/docker/docker-compose.yaml up

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -rf .pytest_cache .ruff_cache htmlcov
```

### Step 4.2: Create LICENSE
```bash
# Choose appropriate license (MIT, Apache 2.0, etc.)
cat > LICENSE << 'EOF'
MIT License

Copyright (c) 2026 [Your Name]

Permission is hereby granted, free of charge...
EOF
```

### Step 4.3: Create CHANGELOG.md
```markdown
# Changelog

## [0.1.0] - 2026-02-11

### Added
- Metrics collection system with Prometheus export
- Guardrails validation (PII, injection, hallucinations)
- Email IDLE polling service
- LangGraph workflow orchestration
- Policy-based routing
- Mock service integrations

### Tests
- 12 metrics unit tests
- 27 guardrails unit tests
- Integration test suite
```

### Step 4.4: Update README.md
Add sections:
- **Installation** (using new structure)
- **Development Setup** (make install)
- **Running Tests** (make test)
- **Project Structure** (document new layout)

---

## Phase 5: CI/CD Setup

### Step 5.1: Create .github/workflows/ci.yml
```yaml
name: CI

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.11", "3.12"]
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: ${{ matrix.python-version }}
      
      - name: Install dependencies
        run: |
          pip install uv
          uv pip install -e ".[dev]"
      
      - name: Run tests
        run: pytest tests/ -v --cov=omni_channel_ai_servicing
      
      - name: Lint
        run: ruff check omni_channel_ai_servicing tests
```

### Step 5.2: Create .github/workflows/cd.yml
```yaml
name: CD

on:
  push:
    tags:
      - 'v*'

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Build Docker image
        run: docker build -f infra/docker/Dockerfile -t omni-channel-ai:${{ github.ref_name }} .
      
      - name: Push to registry
        # Add your deployment steps
```

---

## Phase 6: Package Configuration

### Step 6.1: Update pyproject.toml (Complete)
```toml
[build-system]
requires = ["setuptools>=68.0"]
build-backend = "setuptools.build_meta"

[project]
name = "omni-channel-ai-servicing"
version = "0.1.0"
description = "AI-powered omnichannel customer service platform"
readme = "README.md"
requires-python = ">=3.11"
license = {text = "MIT"}
authors = [
    {name = "Your Name", email = "your.email@example.com"}
]
classifiers = [
    "Development Status :: 3 - Alpha",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: MIT License",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
]
dependencies = [
    "fastapi>=0.109.0",
    "uvicorn>=0.27.0",
    "langgraph>=0.0.25",
    "langchain>=0.1.0",
    "pydantic>=2.5.0",
    # ... rest of dependencies
]

[project.optional-dependencies]
dev = [
    "pytest>=9.0.0",
    "pytest-cov>=4.1.0",
    "ruff>=0.1.0",
    "mypy>=1.8.0",
]

[project.scripts]
omni-api = "omni_channel_ai_servicing.app.main:main"
omni-email = "omni_channel_ai_servicing.services.email_idle_poller:main"

[tool.setuptools.packages.find]
where = ["."]
include = ["omni_channel_ai_servicing*"]
exclude = ["tests*", "scripts*", "docs*"]

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
addopts = "-v --strict-markers"

[tool.ruff]
line-length = 100
target-version = "py311"
select = ["E", "F", "I", "N", "W", "B", "C90"]
ignore = []

[tool.mypy]
python_version = "3.11"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
```

---

## Execution Plan

### Week 1: Core Refactoring
**Day 1-2: Phase 1 (Package Rename)**
- Create feature branch
- Rename src/ → omni_channel_ai_servicing/
- Update ALL imports (use find/replace)
- Update pyproject.toml
- Run tests to verify nothing broke

**Day 3: Phase 2 (Organize Files)**
- Create scripts/, tools/ directories
- Move files to appropriate locations
- Update script paths

**Day 4: Phase 3 (Configuration)**
- Create config/ directory
- Add environment-specific configs
- Create .env.example
- Update config loading code

**Day 5: Testing & Validation**
- Run full test suite
- Verify all scripts work
- Test imports across modules

### Week 2: Polish & CI/CD
**Day 1: Phase 4 (Standard Files)**
- Create Makefile
- Add LICENSE, CHANGELOG.md
- Update README.md

**Day 2: Phase 5 (CI/CD)**
- Create GitHub Actions workflows
- Test CI pipeline

**Day 3: Phase 6 (Package Config)**
- Finalize pyproject.toml
- Test package installation
- Verify entry points

**Day 4-5: Documentation & Testing**
- Update all documentation
- Final integration tests
- Merge to main

---

## Migration Commands (Step-by-Step)

### Step 1: Create branch
```bash
git checkout main
git pull origin main
git checkout -b refactor/standardize-structure
```

### Step 2: Rename package
```bash
mv src omni_channel_ai_servicing
```

### Step 3: Update imports (automated)
```bash
# Find all Python files and replace imports
find . -name "*.py" -type f -exec sed -i 's/from src\./from omni_channel_ai_servicing./g' {} +
find . -name "*.py" -type f -exec sed -i 's/import src\./import omni_channel_ai_servicing./g' {} +
```

### Step 4: Organize directories
```bash
mkdir -p scripts config tools tests/manual .github/workflows

# Move scripts
mv run_*.sh start_servers.sh scripts/

# Move test files
mv test_email_simple.py test_gmail_auth.py debug_credentials.py tests/manual/

# Move mock services if standalone
mv run_mock_services.sh scripts/
```

### Step 5: Test everything
```bash
# Run tests
python -m pytest tests/unit -v
python -m pytest tests/integration -v

# Try imports
python -c "from omni_channel_ai_servicing.app.main import app"
python -c "from omni_channel_ai_servicing.monitoring.metrics import get_metrics"
```

### Step 6: Update scripts
```bash
# Update Python paths in shell scripts
sed -i 's/python -m src\./python -m omni_channel_ai_servicing./g' scripts/*.sh
```

### Step 7: Commit and test
```bash
git add .
git commit -m "refactor: standardize project structure to industry conventions

- Rename src/ → omni_channel_ai_servicing/ for proper packaging
- Organize scripts/ and config/ directories
- Add Makefile for common commands
- Add .env.example for configuration template
- Update all imports to use new package name
- Add LICENSE and CHANGELOG.md
- Configure GitHub Actions for CI/CD"

git push origin refactor/standardize-structure
```

---

## Risks & Mitigation

### Risk 1: Breaking Changes
**Impact:** All imports break
**Mitigation:** 
- Test on feature branch first
- Run full test suite after changes
- Use automated find/replace for consistency

### Risk 2: Shell Scripts Break
**Impact:** Deployment scripts fail
**Mitigation:**
- Update all Python module paths
- Test each script individually
- Document new paths in README

### Risk 3: CI/CD Breaks
**Impact:** Pipeline failures
**Mitigation:**
- Update CI configs first
- Test locally with act (GitHub Actions simulator)
- Gradual rollout

### Risk 4: Import Confusion
**Impact:** Developers use old imports
**Mitigation:**
- Update documentation immediately
- Add deprecation warnings (if supporting old imports temporarily)
- Clear communication in PR

---

## Post-Refactoring Checklist

- [ ] All tests passing (unit + integration)
- [ ] All scripts executable and working
- [ ] Documentation updated (README, docs/)
- [ ] CI/CD pipeline green
- [ ] Package installable via `pip install -e .`
- [ ] Entry points working (`omni-api`, `omni-email`)
- [ ] No remaining `from src.` imports
- [ ] .env.example covers all config
- [ ] Makefile commands work
- [ ] Docker build succeeds

---

## Interview Talking Points

**"Why did you refactor the structure?"**
- "Aligned with Python packaging standards (PEP 518, PEP 621)"
- "Improved developer experience with Makefile and clear structure"
- "Enabled proper CI/CD with GitHub Actions"
- "Made package installable and distributable"

**"What challenges did you face?"**
- "Breaking change required updating 50+ import statements"
- "Shell scripts needed path updates"
- "Tested thoroughly to avoid runtime breaks"
- "Used automated tools (sed) for consistency"

**"How did you ensure nothing broke?"**
- "Feature branch + comprehensive test suite"
- "Automated import replacement with verification"
- "Manual testing of all entry points"
- "CI pipeline validation before merge"
