# GitHub SSH Authentication Setup

## Current Status ✅

**Your changes are already pushed and accessible:**
- ✅ Branch `claude/update-ci-dependency-versions` pushed to `origin` (Terminal-Pressure/PeachTree)
- ✅ Commit `7ace80f` includes all bug bounty enhancements (474 new lines)
- ✅ Pull Request #19 is active: https://github.com/0ai-Cyberviser/PeachTree/pull/19
- ✅ Changes visible in the PR (GitHub syncs fork automatically)

**What's pending:**
- ⏳ SSH key needs to be added to GitHub account (for future pushes to upstream)

---

## SSH Key Setup (Complete This When You Return)

### Your SSH Public Key
```
ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAINoOgfGs2un4siZG6yUcqhmQt0ybs0+g1dmVAe01TfTz your_email@example.com
```

### Steps to Add SSH Key to GitHub

1. **Go to GitHub SSH Settings:**
   ```
   https://github.com/settings/ssh/new
   ```

2. **Sign in** with your 0ai-Cyberviser account

3. **Fill in the form:**
   - **Title:** `PeachTree Development (Kali Linux)` (or any descriptive name)
   - **Key type:** `Authentication Key`
   - **Key:** Paste the public key above

4. **Click "Add SSH key"**

5. **Verify the connection:**
   ```bash
   ssh -T git@github.com
   ```
   
   Expected output:
   ```
   Hi 0ai-Cyberviser! You've successfully authenticated, but GitHub does not provide shell access.
   ```

6. **Push to upstream** (if needed):
   ```bash
   git push upstream claude/update-ci-dependency-versions
   ```

---

## Alternative: Personal Access Token (PAT)

If you prefer token-based authentication over SSH:

### Create Token
1. Go to: https://github.com/settings/tokens/new
2. Note: `PeachTree CLI Access`
3. Expiration: 90 days (or your preference)
4. Scopes: Select `repo` (full control of private repositories)
5. Click "Generate token"
6. **Copy the token immediately** (you won't see it again)

### Configure Git
```bash
# Update upstream remote to use token
git remote set-url upstream https://<YOUR_TOKEN>@github.com/0ai-Cyberviser/PeachTree.git

# Or use credential helper (more secure)
git config --global credential.helper store
git push upstream claude/update-ci-dependency-versions
# Enter token when prompted for password
```

---

## Current Git Configuration

```bash
$ git remote -v
origin    https://github.com/Terminal-Pressure/PeachTree.git (fetch)
origin    https://github.com/Terminal-Pressure/PeachTree.git (push)
upstream  git@github.com:0ai-Cyberviser/PeachTree.git (fetch)
upstream  git@github.com:0ai-Cyberviser/PeachTree.git (push)
```

**Notes:**
- `origin` uses HTTPS (works, already authenticated)
- `upstream` uses SSH (needs key added to GitHub)
- To switch `upstream` back to HTTPS with token:
  ```bash
  git remote set-url upstream https://<TOKEN>@github.com/0ai-Cyberviser/PeachTree.git
  ```

---

## Why SSH Is Recommended

✅ **Advantages:**
- No password/token expiration
- More secure (private key never transmitted)
- Easier for frequent pushes
- Works across all repos automatically

❌ **Personal Access Token drawbacks:**
- Expires (must regenerate)
- Must be stored securely
- Visible in git config/command history if not careful

---

## Troubleshooting

### "Permission denied (publickey)"
- SSH key not added to GitHub account
- Wrong key uploaded (must be the **public** key: `~/.ssh/id_ed25519.pub`)
- SSH agent not running: `eval "$(ssh-agent -s)" && ssh-add ~/.ssh/id_ed25519`

### "Invalid username or token"
- Password authentication not supported (use SSH or PAT)
- Token expired or has wrong scopes
- Token format incorrect in URL

### "You don't have permission to push"
- Pushing to wrong remote (`upstream` vs `origin`)
- Account doesn't have write access to repository
- Repository settings restrict branch pushes

---

## Quick Reference

```bash
# Copy SSH key to clipboard
cat ~/.ssh/id_ed25519.pub | xclip -selection clipboard

# Test SSH connection
ssh -T git@github.com

# Check remote configuration
git remote -v

# Push to fork (always works)
git push origin <branch-name>

# Push to upstream (needs auth)
git push upstream <branch-name>

# View commit log
git log --oneline -5

# Check branch status
git status
```

---

**Generated:** April 27, 2026  
**Context:** Bug bounty enhancements for crypto-exchange-bug-bounty.instructions.md  
**Commit:** 7ace80f (226 insertions)
