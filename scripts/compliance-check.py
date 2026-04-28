#!/usr/bin/env python3
"""
PeachTree Dataset Compliance Checker

Validates that datasets meet all required conditions before deployment:
1. Internal use only (no public deployment without expansion)
2. License compliance (MIT)
3. No automated exploitation without human oversight
4. Follow responsible disclosure policies
5. Expand to 100+ records before production
6. Implement ethical monitoring
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Tuple

class ComplianceChecker:
    def __init__(self, dataset_path: str, min_records: int = 100):
        self.dataset_path = Path(dataset_path)
        self.min_records = min_records
        self.violations: List[str] = []
        self.warnings: List[str] = []
        
    def check_all(self) -> Tuple[bool, List[str], List[str]]:
        """Run all compliance checks. Returns (passed, violations, warnings)."""
        self.check_dataset_size()
        self.check_license_compliance()
        self.check_safety_gates()
        self.check_provenance()
        self.check_ethical_markers()
        
        passed = len(self.violations) == 0
        return passed, self.violations, self.warnings
    
    def check_dataset_size(self):
        """Condition 1 & 5: Dataset size requirements."""
        if not self.dataset_path.exists():
            self.violations.append(f"Dataset not found: {self.dataset_path}")
            return
        
        record_count = 0
        with open(self.dataset_path, 'r') as f:
            for line in f:
                if line.strip():
                    record_count += 1
        
        if record_count < self.min_records:
            self.violations.append(
                f"PRODUCTION BLOCKED: Dataset has {record_count} records, "
                f"requires {self.min_records}+ for production deployment. "
                f"Current status: SEED TRAINING ONLY."
            )
        else:
            print(f"✅ Dataset size: {record_count} records (>= {self.min_records})")
    
    def check_license_compliance(self):
        """Condition 2: Verify all records have MIT license."""
        if not self.dataset_path.exists():
            return
        
        non_mit_licenses = set()
        missing_license = 0
        
        with open(self.dataset_path, 'r') as f:
            for i, line in enumerate(f, 1):
                if not line.strip():
                    continue
                try:
                    record = json.loads(line)
                    license_id = record.get('license_id', '')
                    if not license_id:
                        missing_license += 1
                    elif license_id != 'MIT':
                        non_mit_licenses.add(license_id)
                except json.JSONDecodeError:
                    self.violations.append(f"Invalid JSON at line {i}")
        
        if missing_license > 0:
            self.violations.append(
                f"LICENSE VIOLATION: {missing_license} records missing license_id"
            )
        
        if non_mit_licenses:
            self.violations.append(
                f"LICENSE VIOLATION: Non-MIT licenses found: {', '.join(non_mit_licenses)}"
            )
        
        if not non_mit_licenses and missing_license == 0:
            print("✅ License compliance: All records MIT licensed")
    
    def check_safety_gates(self):
        """Condition 3: Verify safety gates exist for handoff."""
        handoff_paths = [
            Path("data/handoff/hancock-unified-training.json"),
            Path("data/handoff/hancock-enterprise-training.json"),
            Path("handoff-bundle/trainer-handoff.json")
        ]
        
        found_handoff = False
        for handoff_path in handoff_paths:
            if handoff_path.exists():
                found_handoff = True
                with open(handoff_path, 'r') as f:
                    handoff = json.load(f)
                
                safety = handoff.get('safety', {})
                required_gates = {
                    'requires_human_approval_before_training': True,
                    'does_not_train_models': True,
                    'dry_run_only': True
                }
                
                missing_gates = []
                for gate, expected in required_gates.items():
                    if safety.get(gate) != expected:
                        missing_gates.append(gate)
                
                if missing_gates:
                    self.violations.append(
                        f"SAFETY VIOLATION: Missing required gates in {handoff_path.name}: "
                        f"{', '.join(missing_gates)}"
                    )
                else:
                    print(f"✅ Safety gates: All enabled in {handoff_path.name}")
                break
        
        if not found_handoff:
            self.warnings.append(
                "No handoff manifest found. Run: peachtree handoff --dataset <path>"
            )
    
    def check_provenance(self):
        """Condition 4: Verify responsible disclosure metadata."""
        if not self.dataset_path.exists():
            return
        
        missing_provenance = 0
        responsible_disclosure_count = 0
        
        with open(self.dataset_path, 'r') as f:
            for line in f:
                if not line.strip():
                    continue
                try:
                    record = json.loads(line)
                    
                    # Check provenance fields
                    required_fields = ['source_repo', 'source_path', 'source_digest']
                    if not all(record.get(f) for f in required_fields):
                        missing_provenance += 1
                    
                    # Check for responsible disclosure markers
                    output = record.get('output', '').lower()
                    if 'responsible disclosure' in output or 'disclosure' in record.get('metadata', {}).get('type', ''):
                        responsible_disclosure_count += 1
                        
                except json.JSONDecodeError:
                    pass
        
        if missing_provenance > 0:
            self.violations.append(
                f"PROVENANCE VIOLATION: {missing_provenance} records missing complete provenance"
            )
        else:
            print("✅ Provenance: 100% complete")
        
        if responsible_disclosure_count > 0:
            print(f"✅ Responsible disclosure: {responsible_disclosure_count} records include guidance")
    
    def check_ethical_markers(self):
        """Condition 6: Verify ethical monitoring markers exist."""
        ethical_markers_found = False
        
        # Check for model card
        model_card_paths = [
            Path("handoff-bundle/model-card.md"),
            Path("data/handoff/reports/model-card.md")
        ]
        
        for model_card_path in model_card_paths:
            if model_card_path.exists():
                content = model_card_path.read_text()
                if 'ethical' in content.lower() and 'monitoring' in content.lower():
                    ethical_markers_found = True
                    print(f"✅ Ethical monitoring: Documented in {model_card_path.name}")
                    break
        
        if not ethical_markers_found:
            self.warnings.append(
                "Ethical monitoring documentation not found in model card. "
                "Add ethical considerations and monitoring requirements."
            )

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Check dataset compliance')
    parser.add_argument('--dataset', required=True, help='Path to dataset JSONL file')
    parser.add_argument('--min-records', type=int, default=100, 
                       help='Minimum records for production (default: 100)')
    parser.add_argument('--strict', action='store_true',
                       help='Treat warnings as violations')
    
    args = parser.parse_args()
    
    checker = ComplianceChecker(args.dataset, args.min_records)
    passed, violations, warnings = checker.check_all()
    
    print("\n" + "="*70)
    print("PEACHTREE COMPLIANCE CHECK RESULTS")
    print("="*70)
    
    if violations:
        print("\n❌ VIOLATIONS:")
        for v in violations:
            print(f"  - {v}")
    
    if warnings:
        print("\n⚠️  WARNINGS:")
        for w in warnings:
            print(f"  - {w}")
    
    print("\n" + "="*70)
    
    if passed and (not args.strict or not warnings):
        print("✅ COMPLIANCE CHECK: PASSED")
        print("="*70)
        return 0
    else:
        print("❌ COMPLIANCE CHECK: FAILED")
        print("="*70)
        return 1

if __name__ == '__main__':
    sys.exit(main())
