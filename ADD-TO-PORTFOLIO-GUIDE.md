# Add PeachTree to 0AI Portfolio - Implementation Guide

**Target:** https://0ai-cyberviser.github.io/0ai/  
**Repository:** Likely `0ai-Cyberviser/0ai-Cyberviser.github.io` or `0ai-Cyberviser/0ai`  
**Date:** April 27, 2026

---

## Step 1: Update Flagship Projects Count

**Find this line:**
```html
Flagship projects
4
```

**Change to:**
```html
Flagship projects
5
```

---

## Step 2: Add PeachTree Card

**Find this section in the HTML:**
```html
### Hancock

AI-powered cybersecurity workflows, operator interfaces, and authorized security
support built around the Hancock platform.
Open Hancock site
```

**Add PeachTree immediately after Hancock:**
```html
### Hancock

AI-powered cybersecurity workflows, operator interfaces, and authorized security
support built around the Hancock platform.
Open Hancock site

### PeachTree

Dataset control plane with provenance tracking, safety gates, and policy-first
automation for AI/ML training workflows. Part of the CyberViser AI stack for 
secure fuzzing and dataset generation.
Open PeachTree site
Company site

### MrClean

Policy-first automation for PR cleanup, repo monitoring, and guarded workflow
execution.
Open repository
```

---

## Exact HTML/Markdown Snippet to Insert

```html
### PeachTree

Dataset control plane with provenance tracking, safety gates, and policy-first
automation for AI/ML training workflows. Part of the <a href="https://cyberviserai.com/">CyberViser AI</a> stack for 
secure fuzzing and dataset generation.
<a href="https://0ai-cyberviser.github.io/PeachTree/">Open PeachTree site</a>
<a href="https://cyberviserai.com/">Company site</a>
```

**Or if using markdown:**
```markdown
### PeachTree

Dataset control plane with provenance tracking, safety gates, and policy-first
automation for AI/ML training workflows. Part of the [CyberViser AI](https://cyberviserai.com/) stack for 
secure fuzzing and dataset generation.

[Open PeachTree site](https://0ai-cyberviser.github.io/PeachTree/)
[Company site](https://cyberviserai.com/)
```

---

## Step 3: Locate the Source File

The portfolio page source is likely in one of these repositories:

**Option 1: Organization GitHub Pages repo**
```bash
# Clone the repo if you don't have it
git clone https://github.com/0ai-Cyberviser/0ai-Cyberviser.github.io.git
cd 0ai-Cyberviser.github.io

# Look for the portfolio page
ls -la index.html *.md
```

**Option 2: Dedicated 0ai repository**
```bash
# Or if it's in a dedicated repo
git clone https://github.com/0ai-Cyberviser/0ai.git
cd 0ai

# Look for source files
ls -la index.html README.md *.md
```

**Option 3: In a subdirectory**
```bash
# The /0ai/ URL suggests it might be a subdirectory
cd 0ai-Cyberviser.github.io/0ai/
ls -la
```

---

## Step 4: Make the Edits

**Find the file (likely `index.html` or `README.md`):**

### Edit #1: Update count
```html
<!-- BEFORE -->
<div>
  <div>Flagship projects</div>
  <div>4</div>
</div>

<!-- AFTER -->
<div>
  <div>Flagship projects</div>
  <div>5</div>
</div>
```

### Edit #2: Add PeachTree section

Insert this between Hancock and MrClean in the "Core projects" section:

```html
<section>
  <h3>PeachTree</h3>
  <p>Dataset control plane with provenance tracking, safety gates, and policy-first
  automation for AI/ML training workflows. Part of the <a href="https://cyberviserai.com/">CyberViser AI</a> 
  stack for secure fuzzing and dataset generation.</p>
  <a href="https://0ai-cyberviser.github.io/PeachTree/">Open PeachTree site</a>
  <a href="https://cyberviserai.com/">Company site</a>
</section>
```

---

## Step 5: Commit and Push

```bash
# Stage your changes
git add index.html  # or whatever file you edited

# Commit
git commit -m "feat: add PeachTree to portfolio

Add PeachTree dataset control plane to 0AI portfolio.

CHANGES:
- Add PeachTree card between Hancock and MrClean
- Update flagship projects count: 4 → 5
- Link to PeachTree docs and cyberviserai.com

PeachTree is the dataset engine with provenance tracking,
safety gates, and policy-first automation for AI/ML workflows.

Docs: https://0ai-cyberviser.github.io/PeachTree/
Company: https://cyberviserai.com/"

# Push to GitHub
git push origin main  # or master, depending on branch
```

---

## Step 6: Verify Deployment

GitHub Pages will rebuild automatically (2-5 minutes).

**Check:**
1. Visit https://0ai-cyberviser.github.io/0ai/
2. Verify "Flagship projects: 5" 
3. Confirm PeachTree appears between Hancock and MrClean
4. Test links:
   - PeachTree docs: https://0ai-cyberviser.github.io/PeachTree/
   - Company site: https://cyberviserai.com/

---

## Visual Reference

**Current structure:**
```
Core projects
├── Hancock ✅
├── MrClean ✅
├── CyberViser ViserHub ✅
└── 0AI Profile Layer ✅
```

**New structure:**
```
Core projects
├── Hancock ✅
├── PeachTree ⭐ NEW
├── MrClean ✅
├── CyberViser ViserHub ✅
└── 0AI Profile Layer ✅
```

---

## Troubleshooting

### Can't find the repository?

Check these locations:
1. https://github.com/0ai-Cyberviser/0ai-Cyberviser.github.io
2. https://github.com/0ai-Cyberviser/0ai
3. https://github.com/0ai-Cyberviser/.github
4. Check repository settings → Pages to see source

### Don't have push access?

If you're the owner but can't push:
1. Use the same Personal Access Token you used for PeachTree
2. Configure git credentials: `git config user.name "0ai-cyberviser"`
3. Use token in URL: `git remote set-url origin https://0ai-cyberviser:TOKEN@github.com/...`

### Changes not showing?

- Wait 5 minutes for GitHub Pages build
- Check Actions tab for build status
- Hard refresh browser (Ctrl+Shift+R)
- Clear browser cache

---

## Quick Command Sequence

```bash
# 1. Clone the portfolio repo (adjust URL as needed)
git clone https://github.com/0ai-Cyberviser/0ai-Cyberviser.github.io.git
cd 0ai-Cyberviser.github.io

# 2. Find and edit the file
# (Use your editor to add PeachTree section)

# 3. Commit and push
git add .
git commit -m "feat: add PeachTree to portfolio"
git push origin main
```

---

## Alternative: GitHub Web Editor

If you prefer to edit directly on GitHub:

1. Go to https://github.com/0ai-Cyberviser/[repo-name]
2. Navigate to the portfolio page source file
3. Click the pencil icon (Edit)
4. Add PeachTree section
5. Commit directly to main branch
6. Wait for Pages to rebuild

---

**Status:** Ready to implement  
**PeachTree Docs:** https://0ai-cyberviser.github.io/PeachTree/ ✅ LIVE  
**Company Site:** https://cyberviserai.com/ ✅ LIVE  
**Next:** Add to portfolio page and increase count to 5
