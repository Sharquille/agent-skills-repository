---
name: security-and-hardening
description: "Hardens code against vulnerabilities. Use when handling user input, authentication, data storage, or external integrations."
category: engineering
source: https://skillrepo.dev/skills/addyosmani/security-and-hardening
author: Addy Osmani
license: MIT
retrieved: 2026-06-14
---

# Security and Hardening

Security-first development practices for web applications. Treat every external input as hostile, every secret as sacred, and every authorization check as mandatory. Security is an architectural constraint on every line of code touching user data, authentication boundaries, or external APIs.

## When to Use

- Building endpoints or forms that accept and process user input.
- Implementing authentication (login/registration) or session-level authorization (RBAC/ABAC).
- Storing, encrypting, or transmitting sensitive user data (PII, tokens, payments).
- Integrating external APIs, handling file uploads, webhooks, or processing callbacks.
- Remediating security warnings, code smells, or executing dependency audits.

## When NOT to Use

- Managing network-layer configurations (BGP summary analysis, loopback routing states) → use [[network-bgp-diagnostics]] instead.
- Troubleshooting physical switch interfaces, duplex auto-negotiations, or cable diagnostics → use [[network-interface-health]] instead.
- General frontend aesthetic and layout changes that do not process untrusted datasets.

---

## The Three-Tier Boundary System

### 1. Always Do (No Exceptions)
- **Boundary Validation:** Validate all external input at the system boundaries (using schemas like Zod/Joi).
- **Parameterized Queries:** Parameterize all database queries. **Never** concatenate user input into SQL/NoSQL statements.
- **Output Encoding:** Encode output to prevent Cross-Site Scripting (XSS). Rely on framework auto-escaping; do not bypass it.
- **Secure Transport:** Mandate HTTPS for all external API and web communications.
- **Cryptographic Hashing:** Hash user passwords with robust, slow algorithms (bcrypt, scrypt, or argon2) before storage.
- **Security Headers:** Set secure headers (`CSP`, `HSTS`, `X-Frame-Options`, `X-Content-Type-Options`).
- **Session Protection:** Secure cookie boundaries using `httpOnly`, `secure`, and `sameSite` properties.
- **Dependency Auditing:** Perform regular audits (`npm audit` / `cargo audit`) as a blocking release gate.

### 2. Ask First (Requires Human/Operator Review)
- Deploying custom authentication schemas or changing core auth workflows.
- Storing new categories of sensitive user data or PII parameters.
- Incorporating new third-party services, APIs, or database integrations.
- Modifying Cross-Origin Resource Sharing (`CORS`) whitelist origins.
- Integrating file upload handlers or processing unstructured file directories.
- Relaxing rate-limiting thresholds or custom throttle windows.
- Granting elevated privileges, scopes, or system access rules.

### 3. Never Do (Hard Rules)
- **No Secrets in Code:** Never commit API credentials, tokens, SSH keys, or passwords to git version control.
- **No Sensitive Logs:** Never log credentials, cleartext tokens, or complete payment parameters.
- **Client-Side Assumptions:** Never treat client-side validation as a security boundary. Always validate on the server.
- **No Bypassing Headers:** Never disable security headers or CORS protection for developer convenience.
- **No Dynamic Execution:** Never utilize `eval()`, `new Function()`, or `innerHTML` with user-supplied strings.
- **No Client Sessions:** Never persist session tokens in client-accessible browser storage (e.g., `localStorage`).
- **No Internal Details:** Never expose detailed server stack traces or internal configuration errors to end users.

---

## OWASP Top 10 Prevention Patterns

### A. Injection Prevention
- ❌ **Bad (Vulnerable to SQL Injection):**
  ```javascript
  const query = `SELECT * FROM users WHERE id = '${userId}'`;
  ```
- ✓ **Good (Parameterized Input):**
  ```javascript
  const user = await db.query('SELECT * FROM users WHERE id = $1', [userId]);
  ```
- ✓ **Good (ORM Parameterization):**
  ```javascript
  const user = await prisma.user.findUnique({ where: { id: userId } });
  ```

### B. Secure Authentication
- **Secure Password Hashing (Node.js):**
  ```javascript
  import { hash, compare } from 'bcrypt';

  const SALT_ROUNDS = 12;
  const hashedPassword = await hash(plaintextPassword, SALT_ROUNDS);
  const isValid = await compare(plaintextPassword, hashedPassword);
  ```
- **Cookie Session Hardening:**
  ```javascript
  app.use(session({
    secret: process.env.SESSION_SECRET, // From env variables, never hardcoded
    resave: false,
    saveUninitialized: false,
    cookie: {
      httpOnly: true,     // Block JavaScript read access (prevent XSS token theft)
      secure: true,       // Force transmission over HTTPS only
      sameSite: 'lax',    // Mitigate Cross-Site Request Forgery (CSRF)
      maxAge: 24 * 60 * 60 * 1000,
    },
  }));
  ```

### C. Cross-Site Scripting (XSS) Mitigation
- ❌ **Bad:**
  ```javascript
  element.innerHTML = userInput;
  ```
- ✓ **Good (Framework Escaping):**
  ```jsx
  return <div>{userInput}</div>; // React automatically escapes strings
  ```
- ✓ **Good (Explicit Sanitization):**
  ```javascript
  import DOMPurify from 'dompurify';
  const cleanHtml = DOMPurify.sanitize(userInput);
  ```

### D. Scoped Access Control
```javascript
app.patch('/api/tasks/:id', authenticate, async (req, res) => {
  const task = await taskService.findById(req.params.id);

  // Programmatic access checking: Verify ownership
  if (task.ownerId !== req.user.id) {
    return res.status(403).json({
      error: { code: 'FORBIDDEN', message: 'Not authorized to modify this resource' }
    });
  }

  const updated = await taskService.update(req.params.id, req.body);
  return res.json(updated);
});
```

### E. Security Headers & CORS Limits
```javascript
import helmet from 'helmet';
app.use(helmet());

// Tight Content Security Policy (CSP)
app.use(helmet.contentSecurityPolicy({
  directives: {
    defaultSrc: ["'self'"],
    scriptSrc: ["'self'"],
    styleSrc: ["'self'", "'unsafe-inline'"],
    imgSrc: ["'self'", 'data:', 'https:'],
    connectSrc: ["'self'"],
  },
}));

// Strictly bound CORS Origins
app.use(cors({
  origin: process.env.ALLOWED_ORIGINS?.split(',') || 'http://localhost:3000',
  credentials: true,
}));
```

---

## Input Validation Patterns (Zod Schema)

Validate untrusted inputs immediately at system boundaries:

```typescript
import { z } from 'zod';

const CreateTaskSchema = z.object({
  title: z.string().min(1).max(200).trim(),
  description: z.string().max(2000).optional(),
  priority: z.enum(['low', 'medium', 'high']).default('medium'),
  dueDate: z.string().datetime().optional(),
});

app.post('/api/tasks', async (req, res) => {
  const result = CreateTaskSchema.safeParse(req.body);
  if (!result.success) {
    return res.status(422).json({
      error: {
        code: 'VALIDATION_ERROR',
        message: 'Invalid input',
        details: result.error.flatten(),
      },
    });
  }
  // Safe parsed output is statically typed and cleaned
  const task = await taskService.create(result.data);
  return res.status(201).json(task);
});
```

---

## File Upload Boundaries

Validate file metadata before executing filesystem transfers:

```typescript
const ALLOWED_MIMETYPES = ['image/jpeg', 'image/png', 'image/webp'];
const MAX_FILE_SIZE_BYTES = 5 * 1024 * 1024; // 5MB

function validateUpload(file: UploadedFile) {
  if (!ALLOWED_MIMETYPES.includes(file.mimetype)) {
    throw new ValidationError('File extension or media type not allowed');
  }
  if (file.size > MAX_FILE_SIZE_BYTES) {
    throw new ValidationError('File size exceeds safety limit of 5MB');
  }
  // Check magic byte signatures if uploading to public endpoints
}
```

---

## Dependency Triage Protocol (`npm audit`)

```text
npm audit reports a vulnerability
├── Severity: critical or high
│   ├── Is the vulnerable code reachable in your app?
│   │   ├── YES --> Fix immediately (update, patch, or replace the dependency)
│   │   └── NO (dev-only dep, unused code path) --> Fix soon, but not a blocker
│   └── Is a fix available?
│       ├── YES --> Update to the patched version
│       └── NO --> Check for workarounds, consider replacing the dependency, or add to allowlist with a review date
├── Severity: moderate
│   ├── Reachable in production? --> Fix in the next release cycle
│   └── Dev-only? --> Fix when convenient, track in backlog
└── Severity: low
    └── Track and fix during regular dependency updates
```

---

## Rate Limiting & Throttling
```javascript
import rateLimit from 'express-rate-limit';

// Standard API limit
app.use('/api/', rateLimit({
  windowMs: 15 * 60 * 1000, // 15 mins
  max: 100,
  standardHeaders: true,
  legacyHeaders: false,
}));

// Strict limit for authentication ports
app.use('/api/auth/', rateLimit({
  windowMs: 15 * 60 * 1000,
  max: 10, // Max 10 attempts
}));
```

---

## Secrets Boundary Audit
Verify that `.gitignore` prevents secrets leakage:
```text
.env
.env.local
.env.*.local
*.pem
*.key
```

Execute a pre-commit verification:
```bash
git diff --cached | grep -i "password\|secret\|api_key\|token"
```

---

## See Also

- Companion Checklist: [[references/security-checklist]] (for detailed pre-commit audits)
- Skill: [[security-best-practices]] (for baseline language auditing rules)
- Skill: [[security-threat-model]] (for mapping system boundaries)
- Skill: [[build-security-policy]] (for drafting project security baselines)
