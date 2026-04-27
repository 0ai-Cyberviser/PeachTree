# Fix GitHub Authentication - 403 Error

**Problem:** `git push` fails with 403 error, denied to Terminal-Pressure

**Error:**
```
remote: Permission to 0ai-Cyberviser/PeachTree.git denied to Terminal-Pressure.
fatal: unable to access 'https://github.com/0ai-Cyberviser/PeachTree/': The requested URL returned error: 403
```

---

## Quick Fix (3 Steps)

### Step 1: Clear Old Credentials

```bash
# Clear cached GitHub credentials
git credential reject <<EOF
protocol=https
host=github.com
EOF
```

### Step 2: Configure Your Git Identity

```bash
# Set your actual GitHub username and email
git config user.name "YourGitHubUsername"
git config user.email "your-email@example.com"

# Or use global config
git config --global user.name "YourGitHubUsername"
git config --global user.email "your-email@example.com"
```

### Step 3: Push Again

```bash
git push origin main
```

When prompted:
- **Username:** Your actual GitHub username (NOT Terminal-Pressure)
- **Password:** Your GitHub Personal Access Token (NOT your GitHub password)

---

## Get a Personal Access Token

If you don't have a Personal Access Token:

1. **Go to:** https://github.com/settings/tokens
2. **Click:** "Generate new token (classic)"
3. **Name:** "PeachTree Push"
4. **Scopes:** Check `repo` (Full control of private repositories)
5. **Generate** and **copy** the token
6. **Use** this token as your password when pushing

**IMPORTANT:** Save the token somewhere - GitHub only shows it once!

---

## Alternative: Use SSH Instead

If you prefer SSH authentication:

```bash
# Change remote URL to SSH
git remote set-url origin git@github.com:0ai-Cyberviser/PeachTree.git

# Verify
git remote -v

# Push (uses SSH key)
git push origin main
```

**Requirements:**
- SSH key must be added to your GitHub account
- Test with: `ssh -T git@github.com`

---

## Alternative: Use GitHub CLI

```bash
# Authenticate with GitHub CLI
gh auth login

# Push
git push origin main
```

---

## Complete Script

Run this all at once:

```bash
cd /tmp/peachtree

# Clear old credentials
git credential reject <<EOF
protocol=https
host=github.com
EOF

# Configure your identity (REPLACE WITH YOUR INFO)
git config user.name "YourGitHubUsername"
git config user.email "your-email@example.com"

# Push (will prompt for credentials)
git push origin main
```

When prompted for password, paste your **Personal Access Token**.

---

## Verify Success

After successful push:

```bash
# Should show all commits on GitHub
git log origin/main --oneline -5

# Check GitHub Pages deployment
# Wait 2-5 minutes, then visit:
# https://0ai-cyberviser.github.io/PeachTree/
```

---

**Status:** Ready to push 30 commits  
**Next:** Follow Step 1-3 above to authenticate correctly
