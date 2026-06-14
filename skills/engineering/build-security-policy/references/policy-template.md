# Security Policy — &lt;Application Name&gt;

> Scope: one paragraph — what this app is, what sensitive data it handles, and what this policy covers.
> Status: DRAFT | APPROVED — &lt;date&gt; — &lt;owner&gt;
>
> **Open TODOs / assumptions**
> - TODO: &lt;unknown&gt; — assumption: &lt;what we assume until confirmed&gt;

## 1. Threat model
- **Assets:** &lt;data/systems worth protecting&gt;
- **Assumptions:** &lt;what must hold for this policy to be valid&gt;
- **In scope:** &lt;components/flows this policy governs&gt;
- **Out of scope (explicit):** &lt;what this policy does NOT cover&gt;
- **Primary threats:** &lt;e.g. credential theft, data exfiltration, privilege escalation, injection&gt;

## 2. Data classification (NIST CSF: Identify)
| Class | Examples | Handling rule |
|-------|----------|---------------|
| Restricted | PHI, financial/PCI, secrets | MUST encrypt at rest + in transit; access logged; MUST NOT appear in logs |
| Confidential | PII, user content | MUST encrypt in transit; least-privilege access |
| Internal | app config, non-sensitive metadata | SHOULD restrict to authenticated roles |
| Public | marketing, docs | MAY be served without auth |

## 3. Trust boundaries (NIST CSF: Protect)
| Boundary | Crossing data | Control |
|----------|--------------|---------|
| Client → API | user input, credentials | TLS 1.2+; input validation; authn required |
| API → datastore | restricted data | least-privilege creds; encryption at rest |
| App → third party | &lt;what leaves&gt; | MUST document purpose + minimize data sent |

## 4. Authentication & session (OWASP ASVS V2/V3)
- Users MUST authenticate via &lt;method&gt;.
- Passwords (if any) MUST be stored with a slow salted hash (argon2/bcrypt/scrypt).
- Sessions MUST expire after &lt;idle/absolute timeout&gt; and MUST be invalidated on logout.
- Session tokens MUST be `HttpOnly`, `Secure`, `SameSite`; MUST NOT be in URLs.
- MFA SHOULD be available for accounts with access to Restricted data.

## 5. Authorization
- Access control MUST be enforced server-side and default-deny.
- Roles/permissions MUST follow least privilege; no implicit admin.
- Every Restricted-data operation MUST check authorization at the boundary, not the UI.

## 6. Secrets & token handling
- Secrets MUST come from a secrets manager / environment, never source control.
- Keys/tokens MUST have a defined rotation policy and owner.
- On suspected exposure, the secret MUST be rotated and the exposure logged.

## 7. Logging & audit (OWASP ASVS V7 / NIST CSF: Detect)
- Security-relevant events (authn, authz failures, data access) MUST be logged with timestamp + actor.
- Logs MUST NOT contain secrets, full tokens, or Restricted data in cleartext.
- Logs MUST be retained for &lt;period&gt; and protected from tampering.

## 8. Retention & deletion
- Default retention per data class: &lt;period&gt;.
- User-initiated deletion MUST remove or irreversibly anonymize Restricted/Confidential data within &lt;SLA&gt;.
- Backups MUST honor deletion within &lt;backup cycle&gt;.

## 9. Incident response (NIST CSF: Respond / Recover)
1. **Detect** — &lt;how an incident is noticed/alerted&gt;
2. **Contain** — &lt;isolate affected systems/accounts&gt;
3. **Eradicate** — &lt;remove cause; rotate exposed secrets&gt;
4. **Recover** — &lt;restore service; verify integrity&gt;
5. **Review** — &lt;post-incident write-up; corrective actions&gt;
- Owner / on-call: &lt;who&gt;. Notification obligations: &lt;regulatory/contractual&gt;.

## 10. Security gates (go / no-go)
- [ ] No unmet **MUST** requirement remains open.
- [ ] Restricted data encrypted at rest and in transit.
- [ ] Authn/session controls implemented and tested.
- [ ] Authorization is default-deny and server-side.
- [ ] No secrets in source control or logs.
- [ ] Logging + retention configured.
- [ ] Incident-response owner assigned.

> **Go/No-go:** &lt;GO if all MUSTs met; otherwise NO-GO + list blocking gaps&gt;
