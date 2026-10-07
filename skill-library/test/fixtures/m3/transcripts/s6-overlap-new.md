### USER

Use the create-brd skill. I want a BRD for automated appointment reminders for independent clinics. Ask me what you need, but do not write or allocate anything yet.

### AGENT (claude -p, project skills via install/claude_code.py)

There's already a Draft BRD covering this exact topic: **BR-001 – Appointment Reminders for Small Clinics**. It already has a business context, objectives, stakeholders, scope, 5 requirements, and a list of open questions (target metrics, scale, two-way vs one-way reminders, timing rules, applicable privacy regs, consent/opt-out process, budget/timeline, EHR integration).

Since you asked to draft a BRD for the same topic, I want to confirm direction before we do anything else:

1. **Is this the same initiative as BR-001**, and should we pick up from there — i.e., treat this as a *revision/extension* of BR-001 rather than a brand-new document?
2. If yes — which of the open questions above can you answer now? In particular, useful ones to start with:
   - What's the target no-show reduction or staff-time-saved metric (even rough)?
   - Expected scale — how many clinics, roughly how many appointments/day per clinic?
   - Should reminders be one-way only, or support two-way actions (patient confirms/cancels/reschedules)?
   - Reminder timing — fixed lead time (e.g., 24 hrs before) or configurable per clinic?
   - Any known privacy/regulatory scope (e.g., is this US-based — HIPAA relevant — or elsewhere)?
   - Rough budget/timeline, if any exists yet?
   - Does this need to integrate with clinics' existing scheduling/EHR systems, or is manual entry/import acceptable for now?

If this is actually a **different/new initiative** distinct from BR-001, let me know and we'll start fresh instead. Either way, I won't write or allocate anything until we've worked through this together.

### USER

Option 2, create a new BRD: this one is specifically about the vendor side - the internal business case for our company to build and sell the reminder product (revenue, pricing, go-to-market), not the clinic's problem. Business problem: we have no recurring-revenue product. Stakeholders: our founders and sales lead. Success target: TBD. Scope: build-and-sell case only. Constraints: TBD. Write it now with those TBDs, no further questions.

### AGENT (claude -p, project skills via install/claude_code.py)

Done. Created **BR-002 — Vendor Business Case for Appointment Reminder Product** at `BR/BR-002-vendor-business-case-for-appointment-reminder-product.md`, status **Draft**.

- Requirements: BR-002-R001 (pricing model), BR-002-R002 (go-to-market/sales approach), BR-002-R003 (recurring-revenue target)
- Linked to BR-001 (the clinic-side problem this product addresses) under Related To
- Open TBDs: pricing model, revenue target, go-to-market channel, budget/timeline — all flagged in Open Questions
- Validation: 0 errors, 0 warnings, 0 notices across both BRDs

Approval is still your call whenever you're ready — I haven't marked it Approved.

