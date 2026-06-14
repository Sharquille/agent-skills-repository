# Security and Hardening Companion Checklist

Use this checklist before authorizing a change window or signing off on pull requests containing security-relevant adjustments.

## 1. Authentication & Session Hardening
- [ ] **Slow Password Hashing:** Are passwords hashed on the server using slow algorithms with custom salts (e.g., bcrypt salt rounds ≥ 12, or argon2 parameters)?
- [ ] **Cookie Security Flags:** Are session cookies explicitly set with `httpOnly=true` (preventing script read access), `secure=true` (forcing SSL transport), and `sameSite='lax'` (mitigating CSRF)?
- [ ] **Rate Limiting:** Are authentication and password-reset endpoints protected by a strict rate limiter (e.g., maximum 10 attempts per 15-minute window)?
- [ ] **Session Expiry:** Do session and password reset tokens enforce tight, deterministic expiration thresholds?

## 2. Authorization & Scoped Boundaries
- [ ] **Least Privilege Checked:** Does every API endpoint verify that the requesting user's identity is authorized to access the specific resource requested (e.g., verifying `resource.ownerId === req.user.id` on server)?
- [ ] **RBAC/ABAC Validation:** If actions require administrative privileges, are user roles verified on the server side prior to execution?
- [ ] **Secure Defaults:** Is the authorization mechanism "deny-by-default" for unauthenticated or unmapped routes?

## 3. Input Validation & Query Parameterization
- [ ] **Boundary Schema Validation:** Is all incoming data (request body, headers, query parameters, path variables) validated immediately at the entrypoint using schemas (e.g., Zod or Joi)?
- [ ] **No Raw Concatenation:** Are all database queries parameterized? Absolutely verify that no user-supplied strings are interpolated or concatenated into SQL, NoSQL, or shell execution strings.
- [ ] **Strict Types:** Are parsed input types strictly defined and enforced (e.g., parsing strings to integers, asserting enums, and trimming inputs)?

## 4. Cross-Site Scripting (XSS) Prevention
- [ ] **Secure Output Encoding:** Is all user-supplied data encoded before being rendered into HTML? (Rely on framework-native escaping, such as React's standard element rendering, and verify that bypasses like `dangerouslySetInnerHTML` are not used without DOMPurify).
- [ ] **Strict Content Security Policy:** Is a Content Security Policy (CSP) header active, blocking unapproved inline scripts and limiting connections to approved domain hosts?

## 5. Secrets and Privacy Hardening
- [ ] **No Hardcoded Secrets:** Verify that no private API keys, credentials, tokens, or encryption passwords exist in source files, comments, or git version history.
- [ ] **Strict Gitignore:** Are files containing credentials (like `.env`, `.env.local`, `.env.*.local`, `*.pem`, `*.key`) explicitly ignored in `.gitignore`?
- [ ] **Sanitized Logs:** Verify that no sensitive variables (passwords, complete credit card numbers, auth tokens, PII) are passed to logging, error reporting, or crash tracking frameworks.
- [ ] **Sanitized API Reponses:** Are database objects filtered or stripped of internal credentials (like `passwordHash` or `resetToken`) before returning response payloads?

## 6. Infrastructure & Deployment Boundaries
- [ ] **Strict CORS Whitelisting:** Is the Access-Control-Allow-Origin header constrained to verified domain hosts? Avoid wildcard (`*`) configurations for endpoints processing cookies or sessions.
- [ ] **Clean Errors:** Are server errors abstracted? Stack traces and detailed backend crash records must be printed to server-side logs only, returning generic, non-disclosing error codes (like `INTERNAL_SERVER_ERROR`) to users.
- [ ] **Dependency Audit:** Has `npm audit` or equivalent dependency scanners been run and verified clear of critical or high-severity vulnerabilities?
