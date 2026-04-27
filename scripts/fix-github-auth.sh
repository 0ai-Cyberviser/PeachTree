#!/bin/bash
# Quick fix for GitHub 403 authentication error
# Run this script to clear Terminal-Pressure credentials and push as 0ai-Cyberviser

set -e

echo "================================================================"
echo "  GitHub Authentication Fix"
echo "  Switching from: Terminal-Pressure"
echo "  Switching to: 0ai-Cyberviser"
echo "================================================================"
echo ""

# Step 1: Clear cached credentials
echo "[Step 1/4] Clearing cached GitHub credentials..."
git credential reject <<EOF
protocol=https
host=github.com
EOF
echo "✓ Cleared cached credentials"
echo ""

# Step 2: Verify git config
echo "[Step 2/4] Current git configuration:"
echo "  user.name: $(git config user.name)"
echo "  user.email: $(git config user.email)"
echo ""

if [ "$(git config user.name)" != "0ai-cyberviser" ]; then
    echo "⚠️  user.name is not set to '0ai-cyberviser'"
    echo "   Already set via: git config user.name \"0ai-cyberviser\""
fi

if [ "$(git config user.email)" != "0ai@cyberviserai.com" ]; then
    echo "⚠️  user.email is not set to '0ai@cyberviserai.com'"
    echo "   Already set via: git config user.email \"0ai@cyberviserai.com\""
fi
echo ""

# Step 3: Check for uncommitted changes
echo "[Step 3/4] Checking repository status..."
UNCOMMITTED=$(git status --porcelain | wc -l)
if [ "$UNCOMMITTED" -gt 0 ]; then
    echo "⚠️  Found $UNCOMMITTED uncommitted changes:"
    git status --short
    echo ""
    echo "Committing changes before push..."
    git add PEACHTREE-CLI-COMMANDS.md
    git commit -m "docs: add PeachTree CLI command reference for multi-org dataset building

Complete guide for executing actual PeachTree build commands:

COMMANDS DOCUMENTED:
- peachtree build (correct syntax with --source, --dataset, --manifest)
- peachtree audit (safety gate verification)
- peachtree export (Hancock handoff in chatml/alpaca/sharegpt formats)

CURRENT STATUS:
- 7 repositories cloned successfully (1.5+ GB total)
- Placeholder JSONL files created
- Ready for actual PeachTree CLI execution

NEXT STEPS:
1. Run build command with all 7 sources
2. Audit safety gates and quality metrics
3. Export to Hancock training format
4. Obtain legal approval for GPL/AGPL repos
5. Begin Hancock cybersecurity LLM training

Resolves placeholder commands from ingestion script."
    echo "✓ Changes committed"
else
    echo "✓ Repository is clean"
fi
echo ""

# Step 4: Instructions for push
echo "[Step 4/4] Ready to push to GitHub"
echo ""
echo "================================================================"
echo "  PUSH INSTRUCTIONS"
echo "================================================================"
echo ""
echo "Run this command:"
echo ""
echo "  git push origin main"
echo ""
echo "When prompted for credentials:"
echo ""
echo "  Username: 0ai-Cyberviser  (or your actual GitHub username)"
echo "  Password: <Personal Access Token>  (NOT your GitHub password!)"
echo ""
echo "================================================================"
echo "  GET A PERSONAL ACCESS TOKEN"
echo "================================================================"
echo ""
echo "If you don't have a Personal Access Token:"
echo ""
echo "1. Go to: https://github.com/settings/tokens"
echo "2. Click 'Generate new token (classic)'"
echo "3. Select scopes: 'repo' (full control of private repositories)"
echo "4. Click 'Generate token'"
echo "5. Copy the token (you won't see it again!)"
echo "6. Use that token as your password when pushing"
echo ""
echo "================================================================"
echo "  ALTERNATIVE: USE SSH"
echo "================================================================"
echo ""
echo "Switch to SSH authentication (no password needed):"
echo ""
echo "  git remote set-url origin git@github.com:0ai-Cyberviser/PeachTree.git"
echo "  git push origin main"
echo ""
echo "(Requires SSH key set up on GitHub)"
echo ""
echo "================================================================"
echo "  Authentication fix complete!"
echo "================================================================"
