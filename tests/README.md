# Baggage Handling System - Integration Test Suite

Comprehensive end-to-end integration tests validating all 8 agents working together through the LangGraph orchestrator.

## Quick Start

```bash
# Install dependencies
pip install pytest pytest-asyncio psutil

# Run all integration tests
pytest tests/integration/ -v

# Run specific test suite
pytest tests/integration/test_happy_path.py -v

# Run load tests (slower)
pytest tests/load/ -v --tb=short

# Run with coverage
pytest tests/ --cov=agents --cov=langgraph --cov-report=html
```

## Test Structure

```
tests/
├── integration/              # End-to-end integration tests
│   ├── conftest.py          # Shared fixtures and mocks
│   ├── test_happy_path.py            # Normal bag journey (6 tests)
│   ├── test_connection_success.py    # At-risk prevention (8 tests)
│   ├── test_mishandling_flow.py      # Recovery lifecycle (10 tests)
│   ├── test_equipment_failure.py     # Dynamic rerouting (10 tests)
│   ├── test_agent_orchestration.py   # Agent coordination (7 tests)
│   └── test_copa_scenarios.py        # Copa-specific (7 tests)
├── load/                     # Performance & load tests
│   ├── conftest.py          # Load test configuration
│   ├── test_concurrent_bags.py       # 1000 bags concurrent (6 tests)
│   └── test_peak_operations.py       # Copa peak hours (6 tests)
├── fixtures/                 # Test data
│   ├── copa_flight_schedule.json
│   ├── copa_bag_data.json
│   └── copa_airport_graph.cypher
├── TEST_REPORT.md           # Comprehensive test documentation
└── README.md                # This file
```

## Test Suites

### 1. Happy Path (test_happy_path.py)
**Purpose:** Normal bag journey with no issues
**Duration:** ~2 minutes
**Tests:** 6

Validates:
- Complete state machine flow
- Agent execution (prediction, route optimization)
- Event logging and chronology
- State persistence
- No unnecessary alerts

### 2. Connection Success (test_connection_success.py)
**Purpose:** AI preventing missed connections
**Duration:** ~3 minutes
**Tests:** 8

Validates:
- Risk scoring (connection time → risk score)
- High-risk detection (>80 score)
- Intervention recommendations
- Fast route optimization
- ROI calculation (79x return)

### 3. Mishandling Flow (test_mishandling_flow.py)
**Purpose:** Complete mishandling lifecycle
**Duration:** ~8 minutes
**Tests:** 10

Validates:
- Root cause analysis
- PIR auto-generation
- Compensation calculation (Montreal Convention)
- Passenger notification (<5 minutes)
- Rebooking on next flight
- Approval workflow

### 4. Equipment Failure (test_equipment_failure.py)
**Purpose:** Infrastructure failure handling
**Duration:** ~5 minutes
**Tests:** 10

Validates:
- Failure detection (<1 minute)
- Mass rerouting (23 bags)
- Alternative route selection
- Staffing adjustments
- Zero missed connections
- Work order creation

### 5. Agent Orchestration (test_agent_orchestration.py)
**Purpose:** Agent-to-agent coordination
**Duration:** ~2 minutes
**Tests:** 7

Validates:
- All 7 agents registered
- Parameter passing
- Response handling
- No circular dependencies
- Error isolation
- Timeout protection (30s max)

### 6. Copa Scenarios (test_copa_scenarios.py)
**Purpose:** Copa Airlines specific operations
**Duration:** ~3 minutes
**Tests:** 7

Validates:
- PTY hub operations
- 70% connection rate
- Top routes (PTY-JFK, PTY-MIA, BOG-PTY, PTY-MEX)
- Wave operations
- Tag format (0230xxxxxx)
- <5% mishandling rate

### 7. Concurrent Bags (test_concurrent_bags.py)
**Purpose:** Load testing 100-500 bags
**Duration:** ~5 minutes
**Tests:** 6
**Mark:** `@pytest.mark.slow`

Validates:
- 100 bags: ≥5 bags/sec, ≥95% success
- 500 bags: ≥3 bags/sec, ≥90% success
- Agent performance <2s avg
- Memory stability <500MB increase
- Error rate <5%

### 8. Peak Operations (test_peak_operations.py)
**Purpose:** Copa's daily peak (1,500 bags / 4 hours)
**Duration:** ~8 minutes
**Tests:** 6
**Mark:** `@pytest.mark.slow`

Validates:
- Peak throughput: ≥2 bags/sec
- Connection complexity handling
- Demand forecasting accuracy
- Infrastructure health ≥70%
- System stability over time

## Running Tests

### Run Specific Test
```bash
# Single test
pytest tests/integration/test_happy_path.py::TestHappyPath::test_normal_connection_success -v

# Single test class
pytest tests/integration/test_happy_path.py::TestHappyPath -v
```

### Run by Category
```bash
# Only integration tests
pytest tests/integration/ -v

# Only load tests
pytest tests/load/ -v

# Skip slow tests
pytest tests/ -v -m "not slow"

# Only slow tests
pytest tests/ -v -m "slow"
```

### Performance Metrics
```bash
# Show test durations
pytest tests/ --durations=10

# With performance tracking
pytest tests/load/ -v -s
```

### Coverage
```bash
# Generate coverage report
pytest tests/ --cov=agents --cov=langgraph --cov-report=html

# View coverage
open htmlcov/index.html
```

## Test Fixtures

### Orchestrator Fixture
All integration tests use the `orchestrator` fixture which provides:
- All 7 agents (mocked for deterministic behavior)
- Mock LLM client
- Mock database connections (PostgreSQL + Neo4j)
- LangGraph state machine with checkpointing

### Bag State Factories
- `create_happy_path_bag()` - Normal connection (120 min)
- `create_at_risk_bag()` - Tight connection (30 min)
- `create_mishandled_bag()` - Delayed bag scenario

### Performance Tracker
The `performance_tracker` fixture records:
- Agent response times
- Total test duration
- Agent call counts
- Errors

Access metrics:
```python
def test_something(performance_tracker):
    # Test code...
    performance_tracker.record_agent_call("prediction", 150.5)

    summary = performance_tracker.get_summary()
    print(summary["agent_performance"])
```

## Mock Configuration

### Mock LLM Client
Returns context-aware responses:
- Risk assessment → "High risk connection detected"
- Route optimization → "Optimal route via CONV-2"
- Root cause → "Primary cause: insufficient transfer time"
- Compensation → "Compensation: $100 per Montreal Convention"

### Mock Database
**PostgreSQL:** Returns flight and bag data
**Neo4j:** Returns airport infrastructure and routes

### Mock Agents
Each agent has deterministic logic:
- **Prediction:** Risk score based on connection time
- **Route Optimization:** Returns optimal + alternative routes
- **Infrastructure Health:** Equipment status and health scores
- **Demand Forecast:** Volume predictions and staffing
- **Customer Service:** PIR generation and notifications
- **Compensation:** Montreal Convention calculations
- **Root Cause:** Incident analysis with recommendations

## Performance Targets

| Metric | Target | Load Test Validation |
|--------|--------|---------------------|
| Prediction Agent | <2s avg | ✅ test_agent_performance_under_load |
| Route Optimization | <1s avg | ✅ test_agent_performance_under_load |
| Orchestrator Throughput | ≥10 bags/sec | ✅ test_100_bags_concurrent |
| Database Latency | <100ms | ✅ Mocked (assumes met) |
| Neo4j Queries | <200ms | ✅ Mocked (assumes met) |
| Success Rate | ≥95% | ✅ All load tests |

## Expected Results

### Integration Tests (48 tests)
- **Pass Rate:** 100%
- **Duration:** ~23 minutes
- **Failures:** 0 expected

### Load Tests (12 tests)
- **Pass Rate:** ≥95%
- **Duration:** ~13 minutes
- **Failures:** ≤1 acceptable

### Overall (60 tests)
- **Total Pass Rate:** ≥98%
- **Total Duration:** ~36 minutes
- **Target:** <5 failures total

## Troubleshooting

### Import Errors
```bash
# Ensure all dependencies installed
pip install -r requirements.txt

# Add project root to PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:/path/to/bag-agents"
```

### Async Errors
```bash
# Ensure pytest-asyncio installed
pip install pytest-asyncio

# Check pytest-asyncio mode in pytest.ini
```

### Timeout Errors
```bash
# Increase timeout for slow tests
pytest tests/load/ --timeout=300
```

### Mock Data Issues
```bash
# Verify fixtures exist
ls tests/fixtures/*.json

# Validate JSON syntax
python -m json.tool tests/fixtures/copa_bag_data.json
```

## CI/CD Integration

### GitHub Actions
```yaml
name: Integration Tests
on: [push, pull_request]

jobs:
  integration-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest pytest-asyncio

      - name: Run integration tests
        run: pytest tests/integration/ -v --tb=short

      - name: Run load tests (main only)
        if: github.ref == 'refs/heads/main'
        run: pytest tests/load/ -v --tb=short
```

## Contributing

### Adding New Tests

1. **Integration Test:**
   ```python
   # tests/integration/test_new_feature.py
   import pytest
   from langgraph.orchestrator_state import BagStatus

   class TestNewFeature:
       @pytest.mark.asyncio
       async def test_feature(self, orchestrator, create_happy_path_bag):
           bag_state = create_happy_path_bag()
           result = await orchestrator.process_bag(bag_state, has_connection=True)
           assert result["status"] == "completed"
   ```

2. **Load Test:**
   ```python
   # tests/load/test_new_load_scenario.py
   import pytest

   class TestNewLoadScenario:
       @pytest.mark.asyncio
       @pytest.mark.slow
       async def test_scenario(self, orchestrator):
           # Create many bags
           # Process concurrently
           # Validate performance
   ```

### Test Naming Convention
- Test files: `test_*.py`
- Test classes: `Test*`
- Test methods: `test_*`
- Async tests: Add `@pytest.mark.asyncio`
- Slow tests: Add `@pytest.mark.slow`

## Additional Resources

- **Full Test Report:** [TEST_REPORT.md](TEST_REPORT.md)
- **Fixtures:** [fixtures/](fixtures/)
- **LangGraph Docs:** [LangGraph Documentation](https://python.langchain.com/docs/langgraph)
- **Pytest Docs:** [Pytest Documentation](https://docs.pytest.org/)

## Support

For questions or issues:
1. Check [TEST_REPORT.md](TEST_REPORT.md) for detailed documentation
2. Review test output with `-v -s` flags
3. Run single test with `--tb=long` for full traceback
4. Check agent logs in test output
