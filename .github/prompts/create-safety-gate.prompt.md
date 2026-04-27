---
description: "Generate a new PeachTree safety gate implementation with tests and documentation"
argument-hint: "gate name and description"
agent: "agent"
tools: [read, edit, execute]
---

# Create New Safety Gate

Generate a complete safety gate implementation for PeachTree's dataset validation pipeline.

## Input Required

Gate specification:
- **Name**: What should the gate be called? (e.g., `PII detection`, `Code quality`, `License verification`)
- **Purpose**: What does this gate validate or filter?
- **Detection logic**: How to identify violations?

## Implementation Steps

1. **Create Gate Implementation**
   
   File: `src/peachtree/gates/{snake_case_name}.py`
   
   ```python
   from dataclasses import dataclass
   from peachtree.core.base_gate import SafetyGate
   from peachtree.models import DatasetRecord
   
   @dataclass(frozen=True)
   class {PascalCaseName}Gate(SafetyGate):
       """
       {Description of what this gate validates/filters}
       
       Safety rationale:
       - {Why this gate is important}
       - {What violations it prevents}
       """
       
       def validate(self, record: DatasetRecord) -> bool:
           """Check if record passes this gate."""
           # Implementation
           pass
       
       def filter(self, dataset: list[DatasetRecord]) -> list[DatasetRecord]:
           """Filter dataset, removing records that fail validation."""
           return [r for r in dataset if self.validate(r)]
       
       def report(self, dataset: list[DatasetRecord]) -> dict:
           """Generate report on gate violations."""
           total = len(dataset)
           passing = len([r for r in dataset if self.validate(r)])
           return {
               "gate": self.__class__.__name__,
               "total_records": total,
               "passing": passing,
               "failing": total - passing,
               "pass_rate": passing / total if total > 0 else 0
           }
   ```

2. **Create Comprehensive Tests**
   
   File: `tests/test_{snake_case_name}.py`
   
   Minimum test cases:
   - `test_validate_passing_record()` - Valid record passes
   - `test_validate_failing_record()` - Invalid record fails
   - `test_filter_mixed_dataset()` - Mix of valid/invalid
   - `test_edge_cases()` - Boundary conditions
   - `test_report_generation()` - Report accuracy

3. **Register Gate in Builder**
   
   Update: `src/peachtree/builder.py`
   - Import the new gate
   - Add to default safety gates list

4. **Document the Gate**
   
   Update: `docs/QUALITY_GATES.md`
   - Add gate description
   - Explain validation logic
   - Provide examples of pass/fail

5. **Verify Implementation**
   
   ```bash
   # Run tests
   pytest tests/test_{snake_case_name}.py -v
   
   # Verify linting
   ruff check src/peachtree/gates/{snake_case_name}.py tests/test_{snake_case_name}.py
   
   # Type check
   mypy src/peachtree/gates/{snake_case_name}.py --strict
   ```

## Safety Principles

Ensure the gate follows PeachTree safety-first design:
- **Conservative by default**: Prefer false positives over false negatives
- **Explainable**: Clear reason for each rejection
- **Testable**: Edge cases covered with tests
- **Documented**: Purpose and examples in docstrings

## Output

Provide:
1. Complete gate implementation code
2. Comprehensive test suite (5+ tests)
3. Documentation updates
4. Verification commands and results
