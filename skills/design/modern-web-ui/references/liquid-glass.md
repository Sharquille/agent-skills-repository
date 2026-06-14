# Liquid Glass Design System

A highly refined evolution of glassmorphism. Surfaces act like physical materials — bending light, with subtle translucency that adapts as content moves beneath them.

**Best for:** SaaS dashboards, consumer apps, creative portfolios, monitoring UIs, premium settings panels.

---

## Token System

```css
:root {
  /* Backgrounds */
  --bg-base:          oklch(0.08 0.01 250);         /* Near-black space */
  --bg-elevated:      oklch(0.11 0.012 250);

  /* Glass surfaces — use with backdrop-filter */
  --glass-surface:    oklch(0.12 0.015 250 / 0.7);  /* 70% transparent */
  --glass-surface-sm: oklch(0.15 0.015 250 / 0.6);  /* Lighter variant */
  --glass-border:     oklch(1 0 0 / 0.08);           /* Near-invisible white */
  --glass-highlight:  oklch(1 0 0 / 0.12);           /* Inset top edge */
  --glass-glow:       oklch(0.65 0.19 260 / 0.08);   /* Accent radial bleed */

  /* Text */
  --text-primary:     oklch(0.95 0.005 250);
  --text-secondary:   oklch(0.82 0.008 250);
  --text-muted:       oklch(0.65 0.012 250);
  --text-disabled:    oklch(0.45 0.008 250);

  /* Accent palette */
  --accent:           oklch(0.65 0.19 260);          /* Electric blue */
  --accent-hover:     color-mix(in oklch, var(--accent) 80%, white);
  --accent-subtle:    oklch(0.65 0.19 260 / 0.12);

  --success:          oklch(0.72 0.15 145);           /* Emerald */
  --success-subtle:   oklch(0.72 0.15 145 / 0.1);
  --warning:          oklch(0.78 0.17 75);            /* Amber */
  --warning-subtle:   oklch(0.78 0.17 75 / 0.1);
  --danger:           oklch(0.62 0.18 28);            /* Red coral */
  --danger-subtle:    oklch(0.62 0.18 28 / 0.1);

  /* Spacing — 4px/8px grid */
  --space-1: 0.25rem;   /* 4px */
  --space-2: 0.5rem;    /* 8px */
  --space-3: 0.75rem;   /* 12px */
  --space-4: 1rem;      /* 16px */
  --space-5: 1.5rem;    /* 24px */
  --space-6: 2rem;      /* 32px */
  --space-8: 3rem;      /* 48px */

  /* Radii */
  --radius-xs: 4px;
  --radius-sm: 8px;
  --radius-md: 14px;
  --radius-lg: 20px;
  --radius-pill: 9999px;

  /* Motion */
  --ease-out-expo:   cubic-bezier(0.16, 1, 0.3, 1);
  --ease-spring:     cubic-bezier(0.34, 1.56, 0.64, 1);
  --ease-in-expo:    cubic-bezier(0.7, 0, 0.84, 0);
  --transition-fast:   all 0.15s var(--ease-out-expo);
  --transition-fluid:  all 0.4s  var(--ease-out-expo);
  --transition-spring: all 0.5s  var(--ease-spring);
}
```

---

## Core Glass Surface

```css
.glass-card {
  background: var(--glass-surface);
  backdrop-filter: blur(24px) saturate(120%);
  -webkit-backdrop-filter: blur(24px) saturate(120%);
  border: 1px solid var(--glass-border);
  border-radius: var(--radius-md);
  box-shadow:
    0 8px 32px oklch(0 0 0 / 0.3),
    inset 0 1px 0 var(--glass-highlight);    /* Top-edge catch light */
  transition: var(--transition-fluid);

  &:hover {
    border-color: oklch(1 0 0 / 0.18);
    box-shadow:
      0 16px 48px oklch(0 0 0 / 0.4),
      inset 0 1px 0 oklch(1 0 0 / 0.25);
    transform: translateY(-2px);
  }
}
```

## Mouse-Tracked Radial Glow (CSS + JS)

```css
/* In CSS: radial gradient reads --mouse-x and --mouse-y CSS vars */
.card-glow {
  position: absolute;
  inset: 0;
  pointer-events: none;
  border-radius: inherit;
  background: radial-gradient(
    300px circle at var(--mouse-x, 50%) var(--mouse-y, 50%),
    var(--glass-glow),
    transparent 70%
  );
  z-index: 1;
}
```

```ts
// In TS/JS: track pointer and inject into CSS vars
card.addEventListener('mousemove', (e: MouseEvent) => {
  const rect = card.getBoundingClientRect();
  const x = ((e.clientX - rect.left) / rect.width)  * 100;
  const y = ((e.clientY - rect.top)  / rect.height) * 100;
  card.style.setProperty('--mouse-x', `${x}%`);
  card.style.setProperty('--mouse-y', `${y}%`);
});
```

```tsx
// In TSX: same pattern via useRef
const ref = useRef<HTMLDivElement>(null);
const handleMove = (e: React.MouseEvent) => {
  const rect = ref.current!.getBoundingClientRect();
  ref.current!.style.setProperty('--mouse-x', `${((e.clientX - rect.left) / rect.width) * 100}%`);
  ref.current!.style.setProperty('--mouse-y', `${((e.clientY - rect.top) / rect.height) * 100}%`);
};
return <div ref={ref} onMouseMove={handleMove} style={{ position: 'relative' }}>...</div>;
```

---

## Status Indicator (Pulsing Dot)

```css
.status-indicator {
  display: inline-flex;
  align-items: center;
  gap: var(--space-2);
  background: var(--success-subtle);
  border: 1px solid oklch(0.72 0.15 145 / 0.25);
  padding: 0.2rem 0.6rem;
  border-radius: var(--radius-pill);

  .dot {
    width: 6px;
    height: 6px;
    background: var(--success);
    border-radius: 50%;
    box-shadow: 0 0 8px var(--success);

    @media (prefers-reduced-motion: no-preference) {
      animation: pulse-dot 2s infinite ease-in-out;
    }
  }

  .label {
    font-size: 0.75rem;
    font-weight: 500;
    color: var(--success);
  }
}

@keyframes pulse-dot {
  0%, 100% { transform: scale(1); opacity: 1; }
  50%       { transform: scale(1.3); opacity: 0.6; box-shadow: 0 0 14px var(--success); }
}
```

## Glass Button

```css
.btn-primary {
  display: inline-flex;
  align-items: center;
  gap: var(--space-2);
  background: var(--accent);
  color: oklch(1 0 0);
  border: none;
  padding: 0.6rem 1.1rem;
  border-radius: var(--radius-sm);
  font-size: 0.875rem;
  font-weight: 600;
  cursor: pointer;
  box-shadow: 0 4px 16px oklch(0.65 0.19 260 / 0.25);
  transition: var(--transition-fluid);

  &:hover {
    background: var(--accent-hover);
    box-shadow: 0 6px 20px oklch(0.65 0.19 260 / 0.4);
    transform: translateY(-1px);
  }

  &:active { transform: translateY(1px); box-shadow: none; }
  &:focus-visible { outline: 2px solid var(--accent); outline-offset: 3px; }
}

.btn-ghost {
  background: oklch(1 0 0 / 0.04);
  border: 1px solid var(--glass-border);
  color: var(--text-secondary);
  /* same padding/radius/transition as above */

  &:hover {
    background: oklch(1 0 0 / 0.08);
    color: var(--text-primary);
    border-color: oklch(1 0 0 / 0.15);
  }
}
```

## Glass Popover (Native Popover API + Anchor Positioning)

```css
.glass-popover {
  /* Anchor binding */
  position: absolute;
  position-anchor: --trigger-anchor;
  top: anchor(bottom);
  position-area: bottom span-left;
  margin-top: var(--space-2);

  /* Surface */
  margin: 0;
  padding: var(--space-2);
  background: oklch(0.13 0.015 250 / 0.92);
  backdrop-filter: blur(20px);
  border: 1px solid var(--glass-border);
  border-radius: var(--radius-sm);
  box-shadow: 0 12px 28px oklch(0 0 0 / 0.45);
  width: 200px;

  /* Entry animation */
  opacity: 0;
  transform: translateY(-6px) scale(0.97);
  transition:
    opacity  0.2s var(--ease-out-expo),
    transform 0.2s var(--ease-out-expo),
    display  0.2s var(--ease-out-expo) allow-discrete;

  &:popover-open {
    opacity: 1;
    transform: translateY(0) scale(1);

    @starting-style {
      opacity: 0;
      transform: translateY(-6px) scale(0.97);
    }
  }
}

/* Trigger button must declare anchor */
.trigger-btn { anchor-name: --trigger-anchor; }
```

---

## Liquid Glass Dashboard Layout Pattern

```css
.dashboard {
  display: grid;
  grid-template-columns: 240px 1fr;
  grid-template-rows: 56px 1fr;
  min-height: 100vh;
  background: var(--bg-base);
  gap: 0;
}

.sidebar {
  grid-row: 1 / -1;
  background: oklch(0.10 0.012 250 / 0.85);
  backdrop-filter: blur(32px);
  border-right: 1px solid var(--glass-border);
}

.topbar {
  background: oklch(0.09 0.01 250 / 0.8);
  backdrop-filter: blur(24px);
  border-bottom: 1px solid var(--glass-border);
}

.main-content {
  padding: var(--space-6);
  overflow-y: auto;

  .card-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
    gap: var(--space-5);
    container-type: inline-size;
  }
}
```
