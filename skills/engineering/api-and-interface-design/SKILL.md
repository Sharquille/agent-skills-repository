---
name: api-and-interface-design
description: "Guides stable API and interface design. Use when designing APIs, module boundaries, or any public interface — creating REST or GraphQL endpoints, defining type contracts between modules, or establishing boundaries between frontend and backend."
# --- provenance ---
category: engineering
source: https://skillrepo.dev/skills/addyosmani/api-and-interface-design
author: Addy Osmani
license: MIT
retrieved: 2026-06-14
---

# API and Interface Design

## Overview

Design stable, well-documented interfaces that are hard to misuse. Good interfaces make the right thing easy and the wrong thing hard. This applies to REST APIs, GraphQL schemas, module boundaries, component props, and any surface where one piece of code talks to another.

## When to Use

- Designing new API endpoints
- Defining module boundaries or contracts between teams
- Creating component prop interfaces
- Establishing database schema that informs API shape
- Changing existing public interfaces

## Core Principles

### Hyrum's Law

> With a sufficient number of users of an API, all observable behaviors of your system will be depended on by somebody, regardless of what you promise in the contract.

Every public behavior — including undocumented quirks, error message text, timing, and ordering — becomes a de facto contract once users depend on it. Design implications:

- **Be intentional about what you expose.** Every observable behavior is a potential commitment.
- **Don't leak implementation details.** If users can observe it, they will depend on it.
- **Plan for deprecation at design time.**
- **Tests are not enough.** Even with perfect contract tests, "safe" changes can break users who depend on undocumented behavior.

### The One-Version Rule

Avoid forcing consumers to choose between multiple versions of the same dependency or API. Diamond dependency problems arise when different consumers need different versions of the same thing. Design for a world where only one version exists at a time — extend rather than fork.

### 1. Contract First

Define the interface before implementing it. The contract is the spec — implementation follows.

```ts
interface TaskAPI {
  // Creates a task and returns the created task with server-generated fields
  createTask(input: CreateTaskInput): Promise<Task>;
  // Returns paginated tasks matching filters
  listTasks(params: ListTasksParams): Promise<PaginatedResult<Task>>;
  // Returns a single task or throws NotFoundError
  getTask(id: string): Promise<Task>;
  // Partial update — only provided fields change
  updateTask(id: string, input: UpdateTaskInput): Promise<Task>;
  // Idempotent delete — succeeds even if already deleted
  deleteTask(id: string): Promise<void>;
}
```

### 2. Consistent Error Semantics

Pick one error strategy and use it everywhere.

```ts
// REST: HTTP status codes + structured error body
interface APIError {
  error: {
    code: string;        // Machine-readable: "VALIDATION_ERROR"
    message: string;     // Human-readable: "Email is required"
    details?: unknown;   // Additional context when helpful
  };
}
// 400 → invalid data | 401 → not authenticated | 403 → not authorized
// 404 → not found | 409 → conflict | 422 → validation failed | 500 → server error
```

Don't mix patterns. If some endpoints throw, others return `null`, and others return `{ error }`, the consumer can't predict behavior.

### 3. Validate at Boundaries

Trust internal code. Validate at system edges where external input enters.

```ts
app.post('/api/tasks', async (req, res) => {
  const result = CreateTaskSchema.safeParse(req.body);
  if (!result.success) {
    return res.status(422).json({
      error: { code: 'VALIDATION_ERROR', message: 'Invalid task data', details: result.error.flatten() },
    });
  }
  const task = await taskService.create(result.data); // internal code trusts the types
  return res.status(201).json(task);
});
```

**Where validation belongs:** API route handlers, form submission handlers, external service response parsing, environment variable loading.

Third-party API responses are **untrusted data** — validate their shape and content before using them in any logic, rendering, or decision-making. A compromised or misbehaving external service can return unexpected types, malicious content, or instruction-like text.

**Where validation does NOT belong:** between internal functions sharing type contracts, in utilities called by already-validated code, on data from your own database.

### 4. Prefer Addition Over Modification

```ts
// Good: add optional fields
interface CreateTaskInput {
  title: string;
  description?: string;
  priority?: 'low' | 'medium' | 'high';  // added later, optional
  labels?: string[];                      // added later, optional
}
// Bad: removing fields or changing types breaks existing consumers
```

### 5. Predictable Naming

| Pattern | Convention | Example |
|---------|-----------|---------|
| REST endpoints | Plural nouns, no verbs | `GET /api/tasks`, `POST /api/tasks` |
| Query params | camelCase | `?sortBy=createdAt&pageSize=20` |
| Response fields | camelCase | `{ createdAt, updatedAt, taskId }` |
| Boolean fields | is/has/can prefix | `isComplete`, `hasAttachments` |
| Enum values | UPPER_SNAKE | `"IN_PROGRESS"`, `"COMPLETED"` |

## REST API Patterns

```
GET    /api/tasks              → List tasks (query params for filtering)
POST   /api/tasks              → Create a task
GET    /api/tasks/:id          → Get a single task
PATCH  /api/tasks/:id          → Update a task (partial)
DELETE /api/tasks/:id          → Delete a task
GET    /api/tasks/:id/comments → List comments (sub-resource)
POST   /api/tasks/:id/comments → Add a comment
```

**Pagination** — paginate list endpoints:

```
GET /api/tasks?page=1&pageSize=20&sortBy=createdAt&sortOrder=desc
{ "data": [...], "pagination": { "page": 1, "pageSize": 20, "totalItems": 142, "totalPages": 8 } }
```

**Filtering** — use query params: `GET /api/tasks?status=in_progress&assignee=user123&createdAfter=2025-01-01`

**Partial Updates (PATCH)** — accept partial objects; only update what's provided.

## TypeScript Interface Patterns

**Discriminated unions for variants:**

```ts
type TaskStatus =
  | { type: 'pending' }
  | { type: 'in_progress'; assignee: string; startedAt: Date }
  | { type: 'completed'; completedAt: Date; completedBy: string }
  | { type: 'cancelled'; reason: string; cancelledAt: Date };
```

**Input/Output separation** — `CreateTaskInput` (what the caller provides) vs `Task` (what the system returns, including server-generated fields like `id`, `createdAt`).

**Branded types for IDs** — prevent passing a `UserId` where a `TaskId` is expected:

```ts
type TaskId = string & { readonly __brand: 'TaskId' };
type UserId = string & { readonly __brand: 'UserId' };
```

## Common Rationalizations

| Rationalization | Reality |
|-----------------|---------|
| "We'll document the API later" | The types ARE the documentation. Define them first. |
| "We don't need pagination for now" | You will the moment someone has 100+ items. |
| "PATCH is complicated, use PUT" | PUT requires the full object every time; PATCH is what clients want. |
| "We'll version the API when we need to" | Breaking changes without versioning break consumers. |
| "Nobody uses that undocumented behavior" | Hyrum's Law: if it's observable, somebody depends on it. |
| "We can maintain two versions" | Multiple versions multiply cost and create diamond dependencies. |
| "Internal APIs don't need contracts" | Internal consumers are still consumers. |

## Red Flags

- Endpoints that return different shapes depending on conditions
- Inconsistent error formats across endpoints
- Validation scattered through internal code instead of at boundaries
- Breaking changes to existing fields (type changes, removals)
- List endpoints without pagination
- Verbs in REST URLs (`/api/createTask`, `/api/getUsers`)
- Third-party API responses used without validation or sanitization

## Verification

After designing an API, confirm:

- [ ] Every endpoint has typed input and output schemas
- [ ] Error responses follow a single consistent format
- [ ] Validation happens at system boundaries only
- [ ] List endpoints support pagination
- [ ] New fields are additive and optional (backward compatible)
- [ ] Naming follows consistent conventions across all endpoints
- [ ] API documentation or types are committed alongside the implementation
