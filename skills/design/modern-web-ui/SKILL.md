---
name: modern-web-ui
description: >
  Build high-end, human-authored static web UIs using TSX, CSS, and HTML with 2026 design standards.
  Use this skill whenever the user asks to build a UI component, dashboard, landing page, tool interface,
  web app screen, or any frontend artifact — especially when they want it to look polished, professional,
  or non-generic. Trigger on phrases like: build me a UI, create a component, design a dashboard,
  make a landing page, I need a web interface, build a tool UI, make this look better, it looks like AI slop,
  redesign this, modern UI, clean design, or any request involving TSX/React components, CSS styling,
  or static HTML pages. Also trigger when the user asks for any security tool UI, homelab dashboard,
  developer utility, or technical interface — these benefit heavily from the Tactile Brutalism system defined here.
# --- provenance ---
category: design
source: self-authored (this repository)
author: Sharquille Andrew
license: MIT
retrieved: 2026-06-14
---

# Modern Web UI Skill

You are building a **premium, human-authored** web interface. The goal is something that looks intentional and professional — not the recognizable "AI Default Aesthetic" of purple/indigo gradients, rounded-2xl on everything, and generic card grids.

Before writing any code, read the design system reference most appropriate for the project:
- **Liquid Glass** → `/references/liquid-glass.md` — consumer apps, SaaS dashboards, creative tools
- **Tactile Brutalism** → `/references/tactile-brutalism.md` — developer tools, security tools, CLIs, docs, utilities

If unsure which to use: security/homelab/technical → Tactile Brutalism. Consumer/portfolio/SaaS → Liquid Glass.

---

## Step 0: Choose Aesthetic Direction

Answer these before writing code:

1. **What is this UI for?** (name the actual product/tool)
2. **Who uses it?** (technical operator, end user, business user)
3. **Which system?** Liquid Glass or Tactile Brutalism
4. **What is the one signature element** that makes this memorable?

State your choices. Then build.

---

## Step 1: Set Up the Token System

All UIs start with CSS custom properties. Copy the appropriate base from the reference files. Adjust palette to match the project — never use the exact same tokens for every project.

**Non-negotiables:**
- Colors in `oklch()` — never HEX or HSL directly in components
- Spacing on the 4px/8px grid using `--space-N` variables
- At least one custom easing curve (`cubic-bezier`) for transitions
- No `border-radius > 14px` on cards (Liquid Glass) or `> 6px` (Tactile Brutalism) unless it's a pill/badge

---

## Step 2: File Structure

**For HTML/CSS artifacts** (single file):

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <!-- Meta, title, Google Fonts or system font stack -->
  <style>
    /* :root tokens first, then component styles */
  </style>
</head>
<body>
  <!-- Semantic HTML -->
  <script>
    // Minimal interaction only — pointer tracking, keyboard bindings
  </script>
</body>
</html>
```

**For TSX/React artifacts:**

```tsx
// Single file component — CSS-in-JS via template literals or inline style objects
// Use oklch() values in JS strings: `oklch(0.62 0.24 256.4)`
// State via useState only — no external dependencies unless specified
```

**For multi-file projects (Claude Code / bash):**

```
src/
├── styles/tokens.css       ← all :root custom props
├── styles/components.css   ← per-component rules
├── components/             ← TSX components
└── index.html              ← entry point
```

---

## Step 3: CSS Techniques to Always Apply

Read `/references/css-primitives.md` for full examples. Summary of what to always use:

| Technique | When |
|-----------|------|
| `oklch()` colors | Every color value |
| `color-mix()` | Hover/active state tints |
| CSS Nesting | Inside every component block |
| `:has()` | Checkbox states, active panels, form validation |
| `container-type: inline-size` | Any reusable card/widget |
| `@starting-style` | Entry animations on popovers/modals |
| `backdrop-filter: blur()` | Liquid Glass surfaces only |
| `anchor-name` / `position-anchor` | Tooltips, dropdowns, context menus |
| Custom `cubic-bezier` | All transitions |

---

## Step 4: TSX-Specific Patterns

When building React/TSX components:

```tsx
// ✅ DO: Use CSS custom properties via style prop
const cardStyle: React.CSSProperties = {
  background: 'oklch(0.12 0.015 250 / 0.7)',
  backdropFilter: 'blur(24px) saturate(120%)',
  border: '1px solid oklch(1 0 0 / 0.08)',
  borderRadius: '14px',
  transition: 'all 0.4s cubic-bezier(0.16, 1, 0.3, 1)',
};

// ✅ DO: Mouse tracking with useRef for glow effects
const cardRef = useRef<HTMLDivElement>(null);
const handleMouseMove = (e: React.MouseEvent) => {
  const rect = cardRef.current!.getBoundingClientRect();
  const x = ((e.clientX - rect.left) / rect.width) * 100;
  const y = ((e.clientY - rect.top) / rect.height) * 100;
  cardRef.current!.style.setProperty('--mouse-x', `${x}%`);
  cardRef.current!.style.setProperty('--mouse-y', `${y}%`);
};

// ❌ NEVER: Tailwind mega-classes that bake in non-semantic sizes
// ❌ NEVER: rounded-2xl, shadow-2xl, gradient-to-r from-purple-500 (AI slop)
// ❌ NEVER: inline style objects with raw hex values
```

**State rules:**
- Use `useState` for UI state (open/closed, active tab, selected item)
- Use `useRef` for DOM measurements and CSS variable injection
- Use `useEffect` only for keyboard binding setup and cleanup

---

## Step 5: Typography

Load a variable font. Use these in order of preference:
1. `'Geist Var'` (developer/technical feel)
2. `'Inter Var'` (neutral, professional)
3. System font stack: `system-ui, -apple-system, sans-serif` (no network request)

```css
:root {
  --font-display: 'Geist Var', system-ui, sans-serif;
  --font-body: 'Inter Var', system-ui, sans-serif;
  --font-mono: 'JetBrains Mono', 'Fira Code', monospace;
}

h1 { font-weight: 700; letter-spacing: -0.025em; }
h2 { font-weight: 650; letter-spacing: -0.015em; }
p  { font-weight: 400; line-height: 1.6; }
```

For Google Fonts in HTML artifacts:

```html
<link href="https://fonts.googleapis.com/css2?family=Geist:wght@100..900&display=swap" rel="stylesheet">
```

---

## Step 6: Motion & Accessibility

```css
/* Always wrap non-essential animation */
@media (prefers-reduced-motion: no-preference) {
  .card {
    transition: var(--transition-fluid);
  }

  @keyframes heartbeat {
    50% { transform: scale(1.15); opacity: 0.7; }
  }
}

/* Keyboard focus — never remove, always style */
:focus-visible {
  outline: 2px solid var(--color-accent);
  outline-offset: 2px;
  border-radius: var(--radius-sm);
}
```

---

## Step 7: Self-Critique Checklist

Before delivering, verify:

- [ ] Zero purple/indigo gradients unless the brief specifically called for them
- [ ] No `border-radius > 14px` on primary surfaces
- [ ] Every color is `oklch()` with valid L C H values
- [ ] At least one `container-type` for responsive behavior
- [ ] Transitions use `cubic-bezier`, not `ease-in-out`
- [ ] Status indicators / badges use semantic colors (success=green, warning=amber, error=red)
- [ ] Typography has clear hierarchy (3+ distinct sizes/weights)
- [ ] Interactive elements have `:hover`, `:active`, and `:focus-visible` states
- [ ] No lorem ipsum — use realistic, domain-appropriate content
- [ ] The UI has **one signature element** that isn't generic

---

## Reference Files

- `/references/liquid-glass.md` — Full Liquid Glass token system + component patterns
- `/references/tactile-brutalism.md` — Full Tactile Brutalism token system + component patterns
- `/references/css-primitives.md` — oklch, :has(), container queries, anchor positioning, @starting-style examples
- `/references/anti-patterns.md` — What NOT to do (with examples)
