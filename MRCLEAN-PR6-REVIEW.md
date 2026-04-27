# MrClean PR #6 Review - Integrated Workflow Harness

Code review analysis and recommendations for the monitor-audit-review-test-log-learn-repeat workflow implementation.

## Automated Review Issues

### P1: DispatchPlanner PolicyEngine Type Mismatch

**Issue:** `DispatchPlanner` expects a `PolicyEngine` but receives full `config` object

```python
# Current (incorrect):
planner = DispatchPlanner(config)

# Expected:
planner = DispatchPlanner(config.policy)  # or PolicyEngine(config)
```

**Impact:** Will raise `AttributeError` when `DispatchPlanner` calls `self.policy.review(...)` during audit phase, terminating the workflow before assessment/review.

**Fix:**
```python
# In workflow command, line ~1498:
policy_engine = PolicyEngine(config)
planner = DispatchPlanner(policy_engine)
```

---

### P1: Auto-Apply Not Executing

**Issue:** `--auto-apply` branch generates proposals but never invokes the apply pipeline

```python
# Current implementation (lines 1515-1517):
generator = ProposalGenerator(config)
proposal = generator.generate(candidate, session)
# Missing: DraftApplier invocation

# Required:
if args.auto_apply and candidate.confidence >= 0.80:
    generator = ProposalGenerator(config)
    proposal = generator.generate(candidate, session)
    
    # ADD THIS:
    applier = DraftApplier(config, proposal)
    result = applier.apply()
    
    if result.success:
        logger.log_event("apply", {
            "candidate": candidate.to_dict(),
            "proposal": proposal.to_dict(),
            "result": result.to_dict()
        })
```

**Impact:** Operators enabling `--auto-apply` get no automatic remediation despite meeting confidence threshold. Feature is non-functional.

---

### P2: Stale Log Cache in Continuous Runs

**Issue:** `PatternLearner` caches log entries after first `load_history()` call

```python
# In PatternLearner.load_history() (lines 40-42):
if not self.loaded:
    self.entries = load_session_logs(self.log_dir)
    self.loaded = True  # Never reloads!
```

**Impact:** In continuous runs with `--iterations 0 --show-learning`, later LEARN phases analyze the initial snapshot and miss newly written entries from subsequent cycles. Insights become stale and misleading.

**Fix:**
```python
def load_history(self, force_reload=False):
    """Load log history, optionally forcing a fresh reload"""
    if not self.loaded or force_reload:
        self.entries = load_session_logs(self.log_dir)
        self.loaded = True
    return self

# In _run_workflow, before each LEARN phase:
if args.show_learning:
    print(formatter.format_info("Phase: LEARN"))
    learner.load_history(force_reload=True)  # Refresh data
    insights = learner.generate_insights()
```

---

## Additional Recommendations

### 1. Add Cycle Isolation

**Issue:** Single `PatternLearner` instance reused across iterations without isolation

**Recommendation:**
```python
# Create new learner per cycle for clean state
for iteration in range(max_iterations):
    learner = PatternLearner(log_dir=log_dir)
    # ... run cycle ...
```

### 2. Validate Auto-Apply Safety

**Issue:** Auto-apply at ≥80% confidence may be too aggressive

**Recommendation:**
```python
# Add configurable threshold and dry-run mode
if args.auto_apply:
    threshold = config.get("auto_apply_threshold", 0.90)  # Default 90%
    dry_run = config.get("auto_apply_dry_run", True)  # Default safe
    
    if candidate.confidence >= threshold:
        if dry_run:
            logger.log_event("would_apply", {"candidate": candidate.to_dict()})
        else:
            # Actually apply
            applier = DraftApplier(config, proposal)
            result = applier.apply()
```

### 3. Add Workflow Failure Recovery

**Issue:** No recovery mechanism if a phase fails mid-cycle

**Recommendation:**
```python
# Save checkpoint after each phase
def _save_checkpoint(self, phase, result):
    checkpoint = {
        "cycle_id": self.cycle_id,
        "phase": phase,
        "result": result.to_dict(),
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    checkpoint_file = self.checkpoint_dir / f"checkpoint-{self.cycle_id}.json"
    checkpoint_file.write_text(json.dumps(checkpoint))

# Resume from checkpoint
def resume_from_checkpoint(self, checkpoint_file):
    checkpoint = json.loads(Path(checkpoint_file).read_text())
    # Resume from checkpoint["phase"]
```

### 4. Improve Learning Data Quality

**Issue:** All events logged equally - no priority or tagging

**Recommendation:**
```python
# Add event metadata for better learning
logger.log_event("audit", {
    "candidate": candidate.to_dict(),
    "severity": candidate.severity,
    "tags": ["security", "false-positive-risk"],  # ADD
    "source": "continuous-workflow",  # ADD
    "confidence": candidate.confidence  # ADD
})
```

---

## PeachTree Workflow Harness Comparison

The recently implemented PeachTree workflow harness addresses these issues:

### ✅ No Type Mismatches
- All phase functions receive correct types
- No PolicyEngine equivalent in PeachTree architecture

### ✅ No Auto-Apply (By Design)
- PeachTree intentionally omits auto-apply for safety
- All changes require human approval
- Aligns with "review-first" principle

### ✅ Fresh Data Loading
- `_load_historical_cycles()` reads from disk each time
- No caching of historical data
- Each LEARN phase gets latest logs

```python
# PeachTree implementation (always fresh):
def _load_historical_cycles(self) -> List[Dict]:
    """Load historical cycle summaries"""
    summaries = []
    for summary_file in sorted(self.state_dir.glob("cycle-summary-*.json")):
        try:
            summaries.append(json.loads(summary_file.read_text()))
        except:
            pass
    return summaries  # Reloads from disk every call
```

### ✅ Configurable Behavior
- All phases can be disabled via config
- Timeout controls per phase
- Continue-on-failure option
- Alert thresholds configurable

---

## Recommended Fixes for MrClean PR #6

### Immediate (P1):
1. Fix `DispatchPlanner` constructor to use `PolicyEngine`
2. Implement actual apply logic in `--auto-apply` branch
3. Add `force_reload` parameter to `PatternLearner.load_history()`

### Short-term (P2):
4. Add configurable auto-apply threshold (default 90%)
5. Add dry-run mode for auto-apply
6. Implement checkpoint/resume for failed cycles

### Long-term:
7. Add event tagging and priority levels
8. Implement anomaly detection in learning phase
9. Add workflow health metrics dashboard
10. Create integration tests for continuous runs

---

## Testing Recommendations

### Test Auto-Apply Logic
```bash
# Test that auto-apply actually applies
mrclean workflow config.toml --auto-apply --iterations 1

# Verify changes were made (not just logged)
git diff  # Should show actual changes

# Test dry-run mode
mrclean workflow config.toml --auto-apply --dry-run
git diff  # Should show NO changes
```

### Test Continuous Learning
```bash
# Run 3 cycles and verify learning improves
mrclean workflow config.toml --iterations 3 --show-learning

# Check that insights from cycle 3 include data from cycles 1-2
cat ~/.mrclean/logs/session-*.jsonl | jq .
```

### Test Failure Recovery
```bash
# Simulate failure mid-cycle
mrclean workflow config.toml  # Kill during AUDIT phase

# Resume from checkpoint
mrclean workflow config.toml --resume-from checkpoint-*.json
```

---

## Conclusion

The MrClean PR #6 has **3 critical bugs** that prevent core functionality:

1. **Type mismatch** will crash the workflow immediately
2. **Missing auto-apply logic** makes the feature non-functional  
3. **Stale cache** produces misleading insights in continuous runs

**Recommendation:** **DO NOT MERGE** until all P1 issues are fixed and tested.

The PeachTree workflow harness implementation demonstrates a working approach that avoids these issues through:
- Correct type handling
- Intentional safety-first design (no auto-apply)
- Fresh data loading on every cycle
- Comprehensive configuration and error handling

---

**Review Status:** ⚠️ CHANGES REQUESTED

**Next Steps:**
1. Fix P1 issues (PolicyEngine, auto-apply, cache reload)
2. Add tests for auto-apply and continuous learning
3. Consider adding PeachTree-style configuration and safety gates
4. Re-request review after fixes
