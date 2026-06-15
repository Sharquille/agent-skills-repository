---
name: design-tokens
description: Build a systematic, three-layer design token architecture (primitive → semantic → component) with CSS variables, spacing/typography scales, component specs, and Tailwind integration. Use for design tokens, CSS variable systems, component state definitions, design-to-code handoff, or making a UI's styling consistent and themeable. Complements ui-styling (shadcn/Tailwind components) and modern-web-ui (from-scratch CSS).
# --- provenance ---
category: design
source: https://github.com/nextlevelbuilder/ui-ux-pro-max-skill (.claude/skills/design-system)
author: claudekit (adapted — namespace dropped; slide-generation system, CSV data, and helper scripts removed to keep the design-token scope)
license: MIT
retrieved: 2026-06-14
---

# Design Tokens

Token architecture, component specifications, and systematic design for consistent, themeable UIs. The core idea: never hardcode a raw value in a component — flow it through three layers so a single change propagates everywhere.

## When to use

- Creating or restructuring design tokens
- Defining component states (default/hover/active/disabled)
- Building a CSS variable system
- Establishing spacing / typography scales
- Design-to-code handoff
- Tailwind theme configuration

## Three-layer token structure

```
Primitive (raw values)        e.g. --color-blue-600: #2563EB
        ↓
Semantic (purpose aliases)    e.g. --color-primary: var(--color-blue-600)
        ↓
Component (component-specific) e.g. --button-bg: var(--color-primary)
```

Components reference **component** tokens, which reference **semantic** tokens, which reference **primitives**. Rebrand by changing primitives; re-theme by changing semantics — components never change.

## Component spec pattern

Define every interactive component as a state table so the implementation is unambiguous:

| Property | Default | Hover | Active | Disabled |
|----------|---------|-------|--------|----------|
| Background | primary | primary-dark | primary-darker | muted |
| Text | white | white | white | muted-fg |
| Border | none | none | none | muted-border |
| Shadow | sm | md | none | none |

## References

Load the reference for the layer or task you're working on:

| Topic | File |
|-------|------|
| Token architecture (the three-layer model) | `references/token-architecture.md` |
| Primitive tokens (raw value scales) | `references/primitive-tokens.md` |
| Semantic tokens (purpose aliases) | `references/semantic-tokens.md` |
| Component tokens | `references/component-tokens.md` |
| Component specs | `references/component-specs.md` |
| States & variants | `references/states-and-variants.md` |
| Tailwind integration | `references/tailwind-integration.md` |

## Integration

- **With `ui-styling`:** component tokens map directly into the Tailwind/shadcn theme config — see `references/tailwind-integration.md`.
- **With `modern-web-ui`:** use these layered tokens in place of a flat `:root` list when a project needs systematic theming or multi-brand support.

## Best practices

1. **No hardcoded values in components** — always reference a token.
2. **One source of truth** — primitives define raw values once.
3. **Semantic names describe purpose, not appearance** — `--color-primary`, not `--color-blue`.
4. **Validate** — grep the codebase for hardcoded hex/px that should be tokens.
5. **Document states** — every component ships its default/hover/active/disabled spec.
