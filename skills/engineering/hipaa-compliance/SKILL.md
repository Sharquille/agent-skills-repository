---
name: hipaa-compliance
description: "Use this as the HIPAA-specific entrypoint when a task is clearly about US healthcare compliance and protecting Protected Health Information (PHI)."
category: engineering
source: https://skillrepo.dev/skills/affaan-m/hipaa-compliance
author: Affaan Mustafa
license: MIT
retrieved: 2026-06-14
---

# HIPAA Compliance

Use this as the HIPAA-specific entrypoint when a task is clearly about US healthcare compliance. This skill establishes concrete security guardrails and decision gates for handling Protected Health Information (PHI).

## When to Use

- The request explicitly mentions HIPAA, PHI, covered entities, business associates, or Business Associate Agreements (BAAs).
- Building or reviewing US healthcare software that stores, processes, exports, or transmits PHI.
- Assessing whether logging, analytics, LLM prompts, storage, or support workflows create HIPAA exposure.
- Designing patient-facing or clinician-facing systems where minimum necessary access and auditability matter.

## When NOT to Use

- General application development tasks that do not involve sensitive patient data or PHI.
- Traditional security review tasks (e.g., general auth, secrets handling, server hardening) → use [[security-best-practices]] or [[security-threat-model]] instead.
- General database performance tuning or infrastructure scripting, unless directly modifying sensitive data storage encryption or access controls.

## How It Works

Treat HIPAA as an overlay on top of broader data classification and policy rules:

1. **Classify the Data**: Is this data Protected Health Information (PHI) under HIPAA? (Any health information linked to one of the 18 HIPAA identifiers like name, email, phone, MRN, etc.).
2. **Apply Decision Gates**:
   - Is this actor/system a Covered Entity (CE) or Business Associate (BA)?
   - Does a third-party vendor or model provider require a signed Business Associate Agreement (BAA) before touching the data?
   - Is access strictly limited to the **minimum necessary** scope for the task?
   - Are read/write/export events fully auditable?
3. **Verify Security Policies**: Ensure proper administrative, physical, and technical safeguards are outlined → use [[build-security-policy]] to establish a solid HIPAA-compliant policy framework.

## HIPAA-Specific Guardrails

- **Zero PHI in Logs/Reports**: Never place PHI in log files, analytics events, crash reports, LLM prompts, or client-visible error strings.
- **Secure Transport & Client Bounds**: Never expose PHI in URLs, local browser storage (`localStorage`/`sessionStorage`), screenshots, or unredacted example payloads.
- **Mandatory Audit Trails**: Require authenticated access, robust scoped authorization (RBAC/ABAC), and automated audit trails for all PHI reads, writes, and modifications.
- **Default-Deny for Third Parties**: Treat third-party SaaS, observability tools, support channels, and LLM providers as blocked-by-default until BAA status and data boundaries are fully verified and signed.
- **Minimum Necessary Access**: Ensure the authenticated user or process only has access to the smallest possible PHI slice necessary to complete the current transaction.
- **Prefer Opaque Identifiers**: Use non-reversible opaque internal UUIDs instead of direct names, Medical Record Numbers (MRNs), phone numbers, or physical addresses whenever possible.

## Examples

### Example 1: Product request framed as HIPAA

**User request:**
> Add AI-generated visit summaries to our clinician dashboard. We serve US clinics and need to stay HIPAA compliant.

**Response pattern:**
1. Activate `hipaa-compliance`.
2. Review the data flow: Where is the clinical transcript stored? Is it sent to a third-party LLM?
3. Verify whether the summarization LLM provider is covered by an active, signed BAA before any PHI is sent.
4. Escalate to the team's compliance reviewer if summaries or transcripts are used to influence clinical decisions or diagnostics.

### Example 2: Vendor/tooling decision

**User request:**
> Can we send support transcripts and patient messages into our analytics stack?

**Response pattern:**
1. Assume support messages contain unstructured PHI (patient-reported symptoms, names, medication history).
2. Block the integration unless the analytics vendor has signed a BAA and maintains HIPAA-compliant data separation boundaries.
3. Recommend a redaction layer or a completely non-PHI metadata event model.

## See Also

- Skill: [[security-best-practices]] (for coding and deployment hardening)
- Skill: [[build-security-policy]] (for drafting HIPAA-compliant administrative policies)
- Skill: [[security-threat-model]] (for mapping out trust boundaries and data leaks)
