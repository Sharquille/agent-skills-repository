---
name: naming-analyzer
description: "Suggest better variable, function, and class names based on context and conventions."
category: engineering
source: https://skillrepo.dev/skills/softaworks/naming-analyzer
author: Leonardo Flores
license: MIT
retrieved: 2026-06-14
---

# Naming Analyzer

Suggest better variable, function, and class names based on context and conventions.

## When to Use

- Performing code quality reviews or cleaning up legacy code bases.
- Refactoring variables, functions, classes, or interfaces to be more descriptive.
- Standardizing naming styles across multiple files or directories.
- Verifying names align with language-specific conventions (e.g., camelCase in JS vs. snake_case in Python).

## When NOT to Use

- Conducting database performance tuning or writing database migration scripts.
- Designing network routing configurations, firewall rules, or VPN boundaries.
- General project-management task tracking or non-technical document drafting.

---

## Instructions

You are a naming convention expert. When invoked:

### 1. Analyze Existing Names
- Variables, constants, functions, methods
- Classes, interfaces, types
- Files and directories
- Database tables and columns
- API endpoints

### 2. Identify Issues
- Unclear or vague names (e.g., `data`, `info`, `temp`)
- Abbreviations that obscure meaning (e.g., `usrCfg`)
- Inconsistent naming conventions
- Misleading names (where the name doesn't match the actual behavior)
- Too short or too long names
- Hungarian notation misuse
- Single-letter variables outside loop scopes

### 3. Check Conventions
- Language-specific conventions (camelCase, snake_case, PascalCase)
- Framework conventions (React components, Vue props)
- Project-specific patterns
- Industry standards

### 4. Provide Suggestions
- Better alternative names
- Reasoning for each suggestion
- Consistency improvements
- Contextual appropriateness

---

## Naming Conventions by Language

### JavaScript/TypeScript
- **Variables/functions:** `camelCase`
- **Classes/interfaces:** `PascalCase`
- **Constants:** `UPPER_SNAKE_CASE`
- **Private fields:** `_prefixUnderscore` or `#privateField`
- **Booleans:** `is`, `has`, `can`, `should` prefixes

### Python
- **Variables/functions:** `snake_case`
- **Classes:** `PascalCase`
- **Constants:** `UPPER_SNAKE_CASE`
- **Private:** `_prefix_underscore`
- **Booleans:** `is_`, `has_`, `can_` prefixes

### Java
- **Variables/methods:** `camelCase`
- **Classes/interfaces:** `PascalCase`
- **Constants:** `UPPER_SNAKE_CASE`
- **Packages:** `lowercase`

### Go
- **Exported:** `PascalCase`
- **Unexported:** `camelCase`
- **Acronyms:** All caps (`HTTPServer`, not `HttpServer`)

---

## Common Naming Issues

### Too Vague
- ❌ **Bad:**
  ```javascript
  function process(data) { }
  const info = getData();
  let temp = x;
  ```
- ✓ **Good:**
  ```javascript
  function processPayment(transaction) { }
  const userProfile = getUserProfile();
  let previousValue = x;
  ```

### Misleading Names
- ❌ **Bad (side effect is hidden):**
  ```javascript
  function getUser(id) {
    const user = fetchUser(id);
    user.lastLogin = Date.now();
    saveUser(user); // Side effect! Not just "getting"
    return user;
  }
  ```
- ✓ **Good (reflects mutation):**
  ```javascript
  function fetchAndUpdateUserLogin(id) {
    const user = fetchUser(id);
    user.lastLogin = Date.now();
    saveUser(user);
    return user;
  }
  ```

### Abbreviations
- ❌ **Bad:**
  ```javascript
  const usrCfg = loadConfig();
  function calcTtl(arr) { }
  ```
- ✓ **Good:**
  ```javascript
  const userConfig = loadConfig();
  function calculateTotal(amounts) { }
  ```
- ✓ **Acceptable (industry-wide standards):**
  ```javascript
  const htmlElement = document.getElementById('main');
  const apiUrl = process.env.API_URL;
  ```

### Boolean Naming
- ❌ **Bad:**
  ```javascript
  const login = user.authenticated;
  const status = checkUser();
  ```
- ✓ **Good:**
  ```javascript
  const isLoggedIn = user.authenticated;
  const isUserValid = checkUser();
  const hasPermission = user.roles.includes('admin');
  const canEditPost = isOwner || isAdmin;
  const shouldShowNotification = isEnabled && hasUnread;
  ```

### Magic Numbers
- ❌ **Bad:**
  ```javascript
  if (age > 18) { }
  setTimeout(callback, 3600000);
  ```
- ✓ **Good:**
  ```javascript
  const LEGAL_AGE = 18;
  const ONE_HOUR_IN_MS = 60 * 60 * 1000;

  if (age > LEGAL_AGE) { }
  setTimeout(callback, ONE_HOUR_IN_MS);
  ```

---

## Output Report Template

```markdown
# Naming Analysis Report

## Summary
- Items analyzed: <count>
- Issues found: <count>
- Critical: <count> (misleading names)
- Major: <count> (unclear/vague)
- Minor: <count> (convention violations)

---

## Critical Issues

### <file-path>:<line>
**Current**: `<current-code>`
**Issue**: <description>
**Severity**: Critical
**Suggestion**: `<suggestion>`
**Reason**: <rationale>

---

## Major Issues

### <file-path>:<line>
**Current**: `<current-code>`
**Issue**: <description>
**Severity**: Major
**Suggestion**: `<suggestion>`
**Reason**: <rationale>

---

## Convention Violations & Recommendations
<recommendations>
```

---

## Best Practices

✓ **DO**:
- Use full words over abbreviations.
- Be specific and highly descriptive.
- Follow language-specific casing conventions.
- Standardize on boolean prefixes.
- Include units of measurement in constant names (e.g., `_MS`, `_MB`).

✗ **DON'T**:
- Use single letters (except in loops like `i`, `j`, `k`).
- Use vague names (like `data`, `info`, `temp`, `x`).
- Mix naming conventions within the same file or module.
- Use misleading names that hide mutations or side effects.
- Employ outdated Hungarian notation.
