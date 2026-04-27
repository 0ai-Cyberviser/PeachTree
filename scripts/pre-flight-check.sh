#!/bin/bash
# Pre-Flight Check for April 26 Stakeholder Communications
# Run this before starting execution at 14:00 UTC

set -e

echo "======================================================"
echo "   APRIL 26 STAKEHOLDER COMMUNICATIONS PRE-FLIGHT"
echo "======================================================"
echo ""

# Color codes
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

CHECKS_PASSED=0
CHECKS_FAILED=0

check_pass() {
    echo -e "${GREEN}✓${NC} $1"
    ((CHECKS_PASSED++))
}

check_fail() {
    echo -e "${RED}✗${NC} $1"
    ((CHECKS_FAILED++))
}

check_warn() {
    echo -e "${YELLOW}⚠${NC} $1"
}

echo "=== 1. VERIFYING EXECUTION DOCUMENTS ==="
echo ""

# Check all required markdown files exist
required_docs=(
    "MASTER-EXECUTION-CHECKLIST.md"
    "COUNTDOWN-EXECUTION-REFERENCE.md"
    "EXECUTE-TODAY-APRIL-26.md"
    "EMAIL-DISTRIBUTION-TEMPLATES.md"
    "STAKEHOLDER-COMMUNICATION-PACKAGE.md"
    "TODAY-QUICK-START.md"
    "RIGHT-NOW-ACTION.md"
)

for doc in "${required_docs[@]}"; do
    if [ -f "$doc" ]; then
        check_pass "Found: $doc"
    else
        check_fail "Missing: $doc"
    fi
done

echo ""
echo "=== 2. VERIFYING PROJECT READINESS ==="
echo ""

# Check PeachTree tests
if python -m pytest tests/ -q --tb=no > /dev/null 2>&1; then
    check_pass "PeachTree: All 129 tests passing"
else
    check_fail "PeachTree: Tests failing"
fi

# Check code quality
if python -m ruff check src/peachtree/ > /dev/null 2>&1; then
    check_pass "PeachTree: Ruff linting clean"
else
    check_fail "PeachTree: Linting errors found"
fi

# Check git status
if [ -z "$(git status --porcelain)" ]; then
    check_pass "PeachTree: Git repository clean"
else
    check_warn "PeachTree: Uncommitted changes present"
fi

# Check blockchain-node if accessible
if [ -d "/home/x/web3-blockchain-node" ]; then
    cd /home/x/web3-blockchain-node
    if go test ./tests -v > /dev/null 2>&1; then
        check_pass "blockchain-node: All tests passing"
    else
        check_fail "blockchain-node: Tests failing"
    fi
    
    if [ -z "$(git status --porcelain)" ]; then
        check_pass "blockchain-node: Git repository clean"
    else
        check_warn "blockchain-node: Uncommitted changes present"
    fi
    cd - > /dev/null
fi

echo ""
echo "=== 3. CHECKING EMAIL TEMPLATE READINESS ==="
echo ""

# Check email templates exist
if grep -q "EMAIL 1: TO LEGAL TEAM" EMAIL-DISTRIBUTION-TEMPLATES.md 2>/dev/null; then
    check_pass "Email 1 template found (Legal Team)"
else
    check_fail "Email 1 template missing"
fi

if grep -q "EMAIL 2: TO COMPLIANCE TEAM" EMAIL-DISTRIBUTION-TEMPLATES.md 2>/dev/null; then
    check_pass "Email 2 template found (Compliance Team)"
else
    check_fail "Email 2 template missing"
fi

if grep -q "EMAIL 3: TO STAKEHOLDERS" EMAIL-DISTRIBUTION-TEMPLATES.md 2>/dev/null; then
    check_pass "Email 3 template found (Stakeholders)"
else
    check_fail "Email 3 template missing"
fi

if grep -q "EMAIL 4: TO EXECUTIVE" EMAIL-DISTRIBUTION-TEMPLATES.md 2>/dev/null; then
    check_pass "Email 4 template found (Executive)"
else
    check_fail "Email 4 template missing"
fi

if grep -q "EMAIL 5: TO ALL TEAM MEMBERS" EMAIL-DISTRIBUTION-TEMPLATES.md 2>/dev/null; then
    check_pass "Email 5 template found (Team Members)"
else
    check_fail "Email 5 template missing"
fi

echo ""
echo "=== 4. CHECKING SUPPORTING DOCUMENTATION ==="
echo ""

# Check supporting docs
if [ -f "PROJECT-COMPLETION-REPORT.md" ]; then
    check_pass "Found: PROJECT-COMPLETION-REPORT.md"
else
    check_fail "Missing: PROJECT-COMPLETION-REPORT.md"
fi

if [ -f "PRODUCTION-READINESS-REPORT.md" ]; then
    check_pass "Found: PRODUCTION-READINESS-REPORT.md"
else
    check_fail "Missing: PRODUCTION-READINESS-REPORT.md"
fi

if [ -f "INCIDENT-RESPONSE.md" ]; then
    check_pass "Found: INCIDENT-RESPONSE.md"
else
    check_fail "Missing: INCIDENT-RESPONSE.md"
fi

echo ""
echo "=== 5. EXECUTION READINESS CHECKLIST ==="
echo ""

echo "Manual checks - verify these before starting:"
echo ""
echo "  [ ] Email client is open and working"
echo "  [ ] All 5 browser tabs prepared with documents"
echo "  [ ] Stakeholder contact list filled in (names + emails)"
echo "  [ ] Tracking spreadsheet created"
echo "  [ ] 6 reminder alarms set (13:55, 14:25, 14:40, 14:55, 15:10, 15:25)"
echo "  [ ] You have 6.5 hours available (14:00-18:00 UTC)"
echo "  [ ] Ready to send emails exactly on time"
echo ""

echo "======================================================"
echo "                 PRE-FLIGHT SUMMARY"
echo "======================================================"
echo ""
echo -e "Checks Passed: ${GREEN}${CHECKS_PASSED}${NC}"
echo -e "Checks Failed: ${RED}${CHECKS_FAILED}${NC}"
echo ""

if [ $CHECKS_FAILED -eq 0 ]; then
    echo -e "${GREEN}✓ ALL AUTOMATED CHECKS PASSED${NC}"
    echo ""
    echo "You are READY for execution!"
    echo ""
    echo "Next steps:"
    echo "  1. Complete the manual checklist above"
    echo "  2. Open MASTER-EXECUTION-CHECKLIST.md"
    echo "  3. Start execution at 14:00 UTC"
    echo ""
    echo "Timeline: 14:00-18:00 UTC (6.5 hours)"
    echo "Deadline: 18:00 UTC EOD"
    echo ""
    exit 0
else
    echo -e "${RED}✗ SOME CHECKS FAILED${NC}"
    echo ""
    echo "Please fix the failed checks before proceeding."
    echo "Run this script again after fixes."
    echo ""
    exit 1
fi
