# AI Agent Guidelines for OTAI Financial Forecasting System

## Project Overview
OTAI Financial Forecasting System is a B2B business simulation tool that models growth, revenue, and financial dynamics through monthly decision-making.

## Architecture Principles

### Data Models
- Use **Pydantic models** for data validation and serialization
- Keep models **immutable** where possible
- Place all data structures in `models.py`

### Module Organization
```
otai_forecast/
├── models.py          # Data models and validation
├── simulator.py       # Main simulation engine
├── compute.py         # Monthly calculation functions
├── config.py          # Default configurations
├── decision_optimizer.py  # Optimization algorithms
├── plots.py           # Visualization functions
└── export.py          # Excel export utilities
```

### Core Design Patterns
- **Simulation Loop**: Monthly state updates through `calculate_new_monthly_data()` → `calculate_new_state()`
- **Decision Variables**: All decisions are monthly and can vary over time
- **Diminishing Returns**: Use logarithmic curves for realistic scaling (CPC, SEO, scraping)
- **State Management**: Maintain immutable state snapshots for each month

## Code Guidelines

### Naming Conventions
- Use descriptive names: `ads_budget` not `ads_spend`
- Private helpers start with underscore: `_effective_cpc()`
- Constants in UPPER_CASE: `DEFAULT_MONTHS`

### Function Design
- Keep functions pure and side-effect free
- Return structured data, not modified inputs
- Use type hints consistently
- Document complex business logic

### Error Handling
- Use Pydantic validation for model constraints
- Raise descriptive exceptions for invalid states
- Log warnings for edge cases (e.g., running out of cash)

### Performance Considerations
- Vectorize calculations where possible (pandas/numpy)
- Cache expensive computations
- Use generators for large data streams
- Optimize hot paths in simulation loop

## Testing Strategy

### Focus Areas
- **Business logic validation**: Complex multi-step calculations
- **Edge cases**: Zero values, maximum limits, negative cash
- **Integration flows**: End-to-end simulation scenarios
- **Optimization**: Verify improvement and constraint satisfaction

### Avoid Testing
- Trivial getters/setters
- Type annotations (Pydantic handles this)
- Basic arithmetic operations
- Dataclass immutability

### Test Structure
```python
def test_complex_business_logic():
    # Arrange: Set up edge case scenario
    # Act: Execute function
    # Assert: Verify business rules
```

## Development Workflow

### Adding New Features
1. Define data models in `models.py`
2. Implement calculations in `compute.py`
3. Add tests for business logic
4. Update simulation flow if needed
5. Add visualizations/export if relevant

### Modifying Existing Logic
- Check for dependent tests
- Update models first
- Maintain backward compatibility where possible
- Document breaking changes

## Best Practices

### Code Quality
- Follow PEP 8 style guidelines
- Use meaningful variable names
- Keep functions focused and small
- Add docstrings for public APIs

### Data Handling
- Use `.model_dump()` for Pydantic serialization
- Prefer `.model_copy(update={...})` over `dataclasses.replace()`
- Validate inputs at model boundaries

### Documentation & Knowledge Management
- **MCP Context7**: Use for getting up-to-date documentation for libraries and frameworks
- **Web Search**: Use for researching best practices, new AI tools, and AI model capabilities
- **Keep AGENTS.md short**: Update when changes occur, but maintain brevity - focus on guidelines, not implementation details
- **Tests must stay current**: All code changes require corresponding test updates to maintain coverage

### Working with Temporary Files
- **Use `.tmp/` folder**: Store small test files, quick experiments, and temporary outputs in the `.tmp/` directory
- **Clean up regularly**: Remove outdated test files from `.tmp/` to keep the workspace organized

### Simulation Specifics
- Monthly granularity for all time-based variables
- Forward simulation only (no prediction)
- Market cap based on TTM Revenue × Multiple
- Cash flow constraints are hard limits

## Running the System

```bash
# Full pipeline
uv run otai_forecast.run

# Tests
uv run pytest tests/
```

Remember: This is a simulation tool for exploring business scenarios, not a prediction system. Focus on modeling realistic business dynamics and constraints.
