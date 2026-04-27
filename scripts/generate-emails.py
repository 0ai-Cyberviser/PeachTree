#!/usr/bin/env python3
"""
Interactive Email Generator for April 26 Stakeholder Communications

This script helps you generate all 5 emails with filled-in contact information.
Run this before 14:00 UTC to prepare your emails.
"""

import os
import sys
from datetime import datetime

def print_header(text):
    print("\n" + "="*70)
    print(f"   {text}")
    print("="*70 + "\n")

def get_input(prompt, default=""):
    """Get user input with optional default"""
    if default:
        response = input(f"{prompt} [{default}]: ").strip()
        return response if response else default
    return input(f"{prompt}: ").strip()

def get_multiple_emails(prompt):
    """Get multiple email addresses"""
    print(f"\n{prompt}")
    print("Enter email addresses one per line. Press Enter twice when done.")
    emails = []
    while True:
        email = input("  Email: ").strip()
        if not email:
            break
        emails.append(email)
    return emails

def main():
    print_header("APRIL 26 STAKEHOLDER COMMUNICATIONS - EMAIL GENERATOR")
    
    print("This script will help you generate all 5 emails with your contact info.")
    print("You'll be able to copy/paste the generated emails into your email client.")
    print("\nLet's gather the contact information first...\n")
    
    # Gather all contact information
    print("\n📧 EMAIL 1: LEGAL TEAM")
    legal_emails = get_multiple_emails("Enter Legal Team email addresses:")
    legal_primary = get_input("Primary Legal Contact Name", "Senior Legal Counsel")
    
    print("\n📧 EMAIL 2: COMPLIANCE TEAM")
    compliance_emails = get_multiple_emails("Enter Compliance Team email addresses:")
    compliance_primary = get_input("Primary Compliance Officer Name", "Compliance Officer")
    
    print("\n📧 EMAIL 3: STAKEHOLDERS")
    stakeholder_emails = get_multiple_emails("Enter Stakeholder email addresses (VP Eng, Sponsors, Steering Committee):")
    vp_eng_name = get_input("VP Engineering Name", "VP Engineering")
    sponsor_name = get_input("Project Sponsor Name", "Project Sponsor")
    
    print("\n📧 EMAIL 4: EXECUTIVE")
    executive_emails = get_multiple_emails("Enter Executive email addresses (CTO, VP):")
    cto_name = get_input("CTO Name", "CTO")
    
    print("\n📧 EMAIL 5: TEAM MEMBERS")
    team_emails = get_multiple_emails("Enter Team distribution list emails (dev-team@, ops-team@, etc):")
    
    print("\n👤 YOUR INFORMATION")
    your_name = get_input("Your Name")
    your_title = get_input("Your Title", "ML Project Lead")
    your_email = get_input("Your Email")
    
    # Generate output directory
    output_dir = "generated-emails"
    os.makedirs(output_dir, exist_ok=True)
    
    print_header("GENERATING EMAILS")
    
    # Email 1: Legal Team
    email1_to = ", ".join(legal_emails)
    email1 = f"""TO: {email1_to}
SUBJECT: Legal Review Required - blockchain-node-instruct-ft-20260426 Ready for Approval
SEND AT: 14:30 UTC

---

Dear Legal Team,

We are requesting your legal review and approval for production deployment of our new ML model 
(blockchain-node-instruct-ft-20260426) scheduled for May 1, 2026.

TIMELINE:
- Staging deployment: Apr 27-28 (pending legal clearance)
- Go/No-Go decision: Apr 28, 12:00 UTC (REQUIRES your sign-off)
- Production deployment: May 1 (if legal approval obtained)

MATERIALS FOR YOUR REVIEW:
Please review the following documents in /tmp/peachtree/:
1. STAKEHOLDER-COMMUNICATION-PACKAGE.md (section: "FOR LEGAL TEAM")
2. PROJECT-COMPLETION-REPORT.md (data provenance section)
3. PRODUCTION-READINESS-REPORT.md (licensing compliance)

KEY QUESTIONS ANSWERED:
✓ Data provenance: Fully tracked with SHA256 digests
✓ IP clearance: 100% MIT-licensed sources
✓ Export control: No restrictions, open-source deployment
✓ Data retention: Procedures documented
✓ Liability review: Model training procedures included

APPROVAL REQUIRED:
Please complete the "Legal Approval Form" in STAKEHOLDER-COMMUNICATION-PACKAGE.md and return by 
April 28, 12:00 UTC to enable production deployment decision.

CONTACTS:
- {your_title}: {your_email}
- CTO (Escalation): {executive_emails[0] if executive_emails else 'cto@company.com'}

NEXT STEP:
Please acknowledge receipt of this email and indicate your review timeline.

Best regards,
{your_name}
{your_title}
{your_email}

---
ATTACHMENTS TO INCLUDE:
- STAKEHOLDER-COMMUNICATION-PACKAGE.md
- PROJECT-COMPLETION-REPORT.md
- PRODUCTION-READINESS-REPORT.md
"""
    
    with open(f"{output_dir}/email1-legal.txt", "w") as f:
        f.write(email1)
    print("✓ Generated: email1-legal.txt")
    
    # Email 2: Compliance Team
    email2_to = ", ".join(compliance_emails)
    email2 = f"""TO: {email2_to}
SUBJECT: Compliance Review Required - ML Model Production Deployment
SEND AT: 14:45 UTC

---

Dear Compliance Team,

We are requesting your compliance review and security sign-off for production deployment of our 
ML model (blockchain-node-instruct-ft-20260426) scheduled for May 1, 2026.

TIMELINE:
- Staging deployment: Apr 27-28 (pending compliance clearance)
- Go/No-Go decision: Apr 28, 12:00 UTC (REQUIRES your sign-off)
- Production deployment: May 1 (if compliance approval obtained)

MATERIALS FOR YOUR REVIEW:
Please review the following documents in /tmp/peachtree/:
1. STAKEHOLDER-COMMUNICATION-PACKAGE.md (section: "FOR COMPLIANCE TEAM")
2. PRODUCTION-READINESS-REPORT.md (safety gates & metrics)
3. INCIDENT-RESPONSE.md (24/7 procedures & escalation)

KEY VALIDATIONS COMPLETED:
✅ Secret filtering: PASSED (zero secrets found)
✅ Data protection: NO PII detected
✅ Quality metrics: 0.85/1.0 (exceeds 0.70 minimum)
✅ Deduplication: ZERO duplicates
✅ Policy compliance: All policies verified
✅ Operational safety: 24/7 monitoring & on-call ready

APPROVAL REQUIRED:
Please complete the "Compliance Approval Form" in STAKEHOLDER-COMMUNICATION-PACKAGE.md and return 
by April 28, 12:00 UTC to enable production deployment decision.

CONTACTS:
- {your_title}: {your_email}
- Compliance (Escalation): {compliance_emails[0] if compliance_emails else 'compliance@company.com'}

NEXT STEP:
Please acknowledge receipt and indicate your review timeline. Expected: ~1 business day.

Best regards,
{your_name}
{your_title}
{your_email}

---
ATTACHMENTS TO INCLUDE:
- STAKEHOLDER-COMMUNICATION-PACKAGE.md
- PRODUCTION-READINESS-REPORT.md
- INCIDENT-RESPONSE.md
"""
    
    with open(f"{output_dir}/email2-compliance.txt", "w") as f:
        f.write(email2)
    print("✓ Generated: email2-compliance.txt")
    
    # Email 3: Stakeholders
    email3_to = ", ".join(stakeholder_emails)
    email3 = f"""TO: {email3_to}
SUBJECT: ML Model Ready for Production - Stakeholder Approval Requested
SEND AT: 15:00 UTC

---

Dear Stakeholders,

We are pleased to announce that blockchain-node-instruct-ft-20260426 has successfully completed 
all technical requirements and is ready for production deployment. We require your approval to proceed.

EXECUTIVE SUMMARY:
✅ Model Accuracy: 92.04% (target: 85%, EXCEEDED by 7%)
✅ Safety Gates: 5/5 PASSED (secret filtering, licensing, quality, deduplication, provenance)
✅ Infrastructure: Staging + Production ready
✅ Timeline: On schedule (May 1 production deployment)
✅ Risk Profile: MANAGED with staged approach

DEPLOYMENT TIMELINE:
- Apr 27-28: Staging validation (48-hour test in isolated environment)
- Apr 28, 12:00 UTC: Go/No-Go decision point (REQUIRES legal/compliance approval)
- May 1, 10:00 UTC: Production deployment (if Go/No-Go = GO)
- May 3: Project completion expected

MATERIALS FOR YOUR REVIEW:
1. STAKEHOLDER-COMMUNICATION-PACKAGE.md (section: "FOR STAKEHOLDER APPROVAL")
2. PROJECT-COMPLETION-REPORT.md (full technical details)
3. PRODUCTION-READINESS-REPORT.md (operational readiness)

APPROVAL REQUIRED:
Please complete the "Stakeholder Approval Form" in STAKEHOLDER-COMMUNICATION-PACKAGE.md and return 
by April 28, 12:00 UTC.

CONTACTS:
- {your_title}: {your_email}
- {cto_name}: {executive_emails[0] if executive_emails else 'cto@company.com'}

NEXT STEP:
Please acknowledge receipt and confirm your decision timeline.

Best regards,
{your_name}
{your_title}
{your_email}

---
ATTACHMENTS TO INCLUDE:
- STAKEHOLDER-COMMUNICATION-PACKAGE.md
- PROJECT-COMPLETION-REPORT.md
- PRODUCTION-READINESS-REPORT.md
"""
    
    with open(f"{output_dir}/email3-stakeholders.txt", "w") as f:
        f.write(email3)
    print("✓ Generated: email3-stakeholders.txt")
    
    # Email 4: Executive
    email4_to = ", ".join(executive_emails)
    email4 = f"""TO: {email4_to}
SUBJECT: ML Model Ready for Production - Executive Decision Required
SEND AT: 15:15 UTC

⚠️  IMPORTANT: ADD CALENDAR INVITE WITH THIS EMAIL ⚠️

Calendar Invite Details:
  Title: blockchain-node-instruct-ft-20260426 Go/No-Go Decision
  Date: April 28, 2026
  Time: 12:00 UTC (30 minutes)
  Attendees: {email4_to}, Legal, Compliance, ML Lead, DevOps Lead
  Description: Final production deployment Go/No-Go decision

---

Dear {cto_name},

We are ready for your executive decision on production deployment of blockchain-node-instruct-ft-20260426.

EXECUTIVE SUMMARY:
✅ Model Performance: 92.04% accuracy (exceeds 85% target by 7%)
✅ Technical Readiness: All tests passing, infrastructure ready
✅ Safety Validation: 5/5 safety gates passed
✅ Team Readiness: All teams trained, procedures documented
✅ Deployment Plan: Staged approach with rollback procedures

DECISION REQUIRED:
We need your approval to proceed with production deployment on May 1, 2026.

GO/NO-GO MEETING:
I've scheduled a decision meeting for April 28, 12:00 UTC (calendar invite included).
We will present final validation results and request your approval.

MATERIALS FOR YOUR REVIEW:
1. STAKEHOLDER-COMMUNICATION-PACKAGE.md (section: "FOR EXECUTIVE GO/NO-GO")
2. PROJECT-COMPLETION-REPORT.md (complete project summary)
3. PRODUCTION-READINESS-REPORT.md (risk assessment + mitigation)

TIMELINE:
- Apr 27-28: Staging validation
- Apr 28, 12:00 UTC: Decision meeting (CALENDAR INVITE INCLUDED)
- May 1, 10:00 UTC: Production deployment (if approved)

CONTACTS:
- {your_title}: {your_email}

Please acknowledge receipt and confirm attendance at Apr 28, 12:00 UTC decision meeting.

Best regards,
{your_name}
{your_title}
{your_email}

---
ATTACHMENTS TO INCLUDE:
- STAKEHOLDER-COMMUNICATION-PACKAGE.md
- PROJECT-COMPLETION-REPORT.md
- PRODUCTION-READINESS-REPORT.md
- CALENDAR INVITE (Apr 28, 12:00 UTC, 30 min)
"""
    
    with open(f"{output_dir}/email4-executive.txt", "w") as f:
        f.write(email4)
    print("✓ Generated: email4-executive.txt")
    
    # Email 5: Team Members
    email5_to = ", ".join(team_emails)
    email5 = f"""TO: {email5_to}
SUBJECT: Staging Deployment This Weekend - Team Preparation Required
SEND AT: 15:30 UTC

---

Dear Team,

We are proceeding with staging deployment this weekend (April 27-28). All team members should 
prepare for deployment execution and be available for support.

DEPLOYMENT SCHEDULE:
- Apr 27, 6:00 AM UTC: Team standup (blockchain-node Phase 3)
- Apr 27, 8:00 AM UTC: Deployment execution begins
- Apr 27-28: 24-hour staging validation (both projects)
- Apr 28, 12:00 PM UTC: Final Go/No-Go decision meeting
- May 1, 10:00 AM UTC: Production deployment (if approved)

YOUR ACTION ITEMS:
1. Read deployment guides in /tmp/peachtree/:
   - PHASE-3-VALIDATION-STAGING.md
   - PHASE-4-PRODUCTION-DEPLOYMENT.md
   - INCIDENT-RESPONSE.md
2. Verify system access (Kubernetes, monitoring dashboards, logs)
3. Review validation procedures: scripts/validate_model.py
4. Be available Apr 27-28 for deployment support
5. Review PROJECT-COMPLETION-REPORT.md for full context

TEAM STANDUP:
- When: April 27, 6:00 AM UTC
- Where: [Your meeting room/Zoom link]
- Duration: 30 minutes
- Agenda: Deployment kickoff, role assignments, final checks

ON-CALL ROTATION:
- Apr 27-28: [On-call lead name] primary, [backup name] secondary
- Escalation: {your_email} → {executive_emails[0] if executive_emails else 'cto@company.com'}

CONTACTS:
- Deployment Lead: {your_email}
- On-Call: [oncall@company.com]
- Emergency: {executive_emails[0] if executive_emails else 'cto@company.com'}

Please acknowledge receipt and confirm your availability for Apr 27 standup.

Best regards,
{your_name}
{your_title}
{your_email}

---
ATTACHMENTS TO INCLUDE:
- PHASE-3-VALIDATION-STAGING.md
- PHASE-4-PRODUCTION-DEPLOYMENT.md
- INCIDENT-RESPONSE.md
- scripts/validate_model.py
- PROJECT-COMPLETION-REPORT.md
"""
    
    with open(f"{output_dir}/email5-team.txt", "w") as f:
        f.write(email5)
    print("✓ Generated: email5-team.txt")
    
    # Generate summary
    summary = f"""EMAIL GENERATION SUMMARY
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

All 5 emails have been generated in the '{output_dir}/' directory:

1. email1-legal.txt (Legal Team) - Send at 14:30 UTC
2. email2-compliance.txt (Compliance Team) - Send at 14:45 UTC
3. email3-stakeholders.txt (Stakeholders) - Send at 15:00 UTC
4. email4-executive.txt (Executive + Calendar) - Send at 15:15 UTC
5. email5-team.txt (Team Members) - Send at 15:30 UTC

NEXT STEPS:
1. Review each generated email file
2. Copy/paste into your email client at the specified times
3. Add the required attachments (listed at bottom of each email)
4. For Email 4: CREATE AND ATTACH CALENDAR INVITE (critical!)
5. Send exactly on time (±2 minutes acceptable)
6. Log each sent email in your tracking spreadsheet

IMPORTANT:
- Email 4 requires a calendar invite for Apr 28, 12:00 UTC
- All emails require attachments (listed in each file)
- Send at exact times: 14:30, 14:45, 15:00, 15:15, 15:30 UTC

Contact Information Used:
- Legal: {len(legal_emails)} emails
- Compliance: {len(compliance_emails)} emails
- Stakeholders: {len(stakeholder_emails)} emails
- Executive: {len(executive_emails)} emails
- Team: {len(team_emails)} emails

Your Name: {your_name}
Your Title: {your_title}
Your Email: {your_email}
"""
    
    with open(f"{output_dir}/README.txt", "w") as f:
        f.write(summary)
    
    print_header("✓ EMAIL GENERATION COMPLETE")
    print(summary)
    print(f"\nAll emails saved to: {output_dir}/")
    print("\nOpen each file, review, and copy/paste into your email client.")
    print("Good luck with the stakeholder communications! 🚀")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nEmail generation cancelled.")
        sys.exit(1)
