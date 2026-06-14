# CSS Primitives Reference (2026)

These are the non-negotiable modern CSS techniques. Use them in every UI.

---

## oklch() — Perceptually Uniform Color

Forget HEX and HSL. `oklch(Lightness Chroma Hue)` distributes brightness evenly to the human eye and unlocks P3 wide-gamut colors on modern displays.

```css
/* Format: oklch(L C H) or oklch(L C H / alpha) */
/* L: 0 (black) → 1 (white)  */
/* C: 0 (gray)  → ~0.37 max (highly saturated) */
/* H: 0–360 hue angle */

--color-blue:   oklch(0.62 0.24 256);   /* Vivid blue */
--color-green:  oklch(0.72 0.15 145);   /* Emerald */
--color-red:    oklch(0.55 0.22 28);    /* Red-coral */
--color-amber:  oklch(0.78 0.17 75);    /* Amber */
--color-purple: oklch(0.60 0.20 295);   /* Rich purple */

/* Semi-transparent — append / alpha */
--surface: oklch(0.12 0.015 250 / 0.7);  /* 70% opaque */
```

**Quick cheat-sheet for Lightness values:**
- `0.08–0.13` → near-black background
- `0.40–0.55` → dark text, dark accent (high contrast on light bg)
- `0.60–0.72` → mid-range, standard accent/icon
- `0.82–0.95` → light text on dark bg
- `0.97–1.00` → near-white surfaces

---

## color-mix() — Dynamic Tints Without New Variables

```css
:root {
  --accent: oklch(0.62 0.24 256);

  /* 80% accent + 20% white = lighter tint (for hover) */
  --accent-hover: color-mix(in oklch, var(--accent) 80%, white);

  /* 85% accent + 15% black = darker shade (for active) */
  --accent-active: color-mix(in oklch, var(--accent) 85%, black);

  /* 10% accent + 90% transparent = subtle background */
  --accent-subtle: color-mix(in oklch, var(--accent) 10%, transparent);
}
```

---

## CSS Nesting (Native — No SASS Required)

```css
.card {
  background: var(--bg-surface);
  border: 1px solid var(--border);

  /* Nested children */
  .card-header {
    padding: var(--space-4);
    border-bottom: 1px solid var(--border-subtle);
  }

  /* Nested pseudo-class */
  &:hover {
    border-color: var(--border-strong);
  }

  /* Nested modifier */
  &.card--active {
    border-color: var(--accent-border);
  }

  /* Nested media query */
  @media (max-width: 640px) {
    padding: var(--space-3);
  }
}
```

---

## :has() — Parent Selector

Style a parent based on what's inside it. No JavaScript needed.

```css
/* Style a form field wrapper when its input is focused */
.field:has(input:focus) {
  border-color: var(--accent-border);
  box-shadow: 0 0 0 3px var(--accent-subtle);
}

/* Style a card when its checkbox is checked */
.item-card:has(input[type="checkbox"]:checked) {
  background: var(--accent-subtle);
  border-color: var(--accent-border);
}

/* Style a nav link's parent when it's active */
.nav-group:has(.nav-link.active) .group-label {
  color: var(--accent);
  font-weight: 600;
}

/* Alert variant based on icon inside */
.alert:has(.icon-warning) { border-left: 3px solid var(--warning); }
.alert:has(.icon-error)   { border-left: 3px solid var(--danger); }
```

---

## Container Queries — Component-Level Responsiveness

Don't use viewport media queries for components. Use container queries so components adapt wherever they're placed.

```css
/* Parent must declare container type */
.card-wrapper {
  container-type: inline-size;
  container-name: card;  /* Optional named container */
}

/* Card adapts based on its OWN width, not viewport */
.card {
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
}

@container (min-width: 420px) {
  .card {
    flex-direction: row;
    align-items: center;
  }
}

@container (min-width: 640px) {
  .card {
    gap: var(--space-5);
    padding: var(--space-6);
  }
}
```

---

## CSS Grid Subgrid — Perfect Alignment Across Cards

When cards in a row have varying content lengths, use subgrid to align headings, bodies, and footers.

```css
.card-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  grid-template-rows: auto;
  gap: var(--space-5);
}

.card {
  display: grid;
  grid-row: span 3;
  grid-template-rows: subgrid;  /* Inherit parent grid rows */

  .card-header { /* Row 1 — always same height across cards */ }
  .card-body   { /* Row 2 — flex-grow fills middle */ }
  .card-footer { /* Row 3 — always pinned to bottom */ }
}
```

---

## Native Popover API

Popovers without JavaScript or positioning libraries.

```html
<!-- Trigger: popovertarget matches popover id -->
<button popovertarget="my-menu" id="menu-btn">Open Menu</button>

<!-- Popover: shows/hides natively, outside normal DOM flow -->
<div id="my-menu" popover>
  <p>Menu content here</p>
</div>
```

```css
/* Style the closed state */
.my-popover {
  opacity: 0;
  transform: translateY(-8px) scale(0.96);
  transition:
    opacity 0.2s var(--ease-out),
    transform 0.2s var(--ease-out),
    display 0.2s var(--ease-out) allow-discrete;
}

/* Style when open */
.my-popover:popover-open {
  opacity: 1;
  transform: none;

  /* Entry from hidden state — requires @starting-style */
  @starting-style {
    opacity: 0;
    transform: translateY(-8px) scale(0.96);
  }
}
```

---

## CSS Anchor Positioning — Tooltip/Dropdown Without Popper.js

```css
/* 1. Name the trigger element as an anchor */
.trigger-button {
  anchor-name: --my-trigger;
}

/* 2. Position the popover/tooltip relative to that anchor */
.tooltip {
  position: absolute;
  position-anchor: --my-trigger;

  /* Align bottom of tooltip to bottom of anchor, centered horizontally */
  top: anchor(bottom);
  left: anchor(center);
  transform: translateX(-50%);
  margin-top: 6px;
}

/* For dropdowns: align to bottom-left of trigger */
.dropdown-menu {
  position: absolute;
  position-anchor: --my-trigger;
  top: anchor(bottom);
  left: anchor(left);
  margin-top: 4px;
}

/* position-area shorthand (newer syntax) */
.popover {
  position: absolute;
  position-anchor: --my-trigger;
  position-area: bottom span-left;
  margin-top: 6px;
}
```

---

## @starting-style — Entry Animations

Animate elements FROM their hidden state when they first appear (popovers, dialogs, newly inserted DOM).

```css
.dialog {
  opacity: 1;
  transform: scale(1);
  transition: opacity 0.3s, transform 0.3s;

  /* The starting state before the element enters */
  @starting-style {
    opacity: 0;
    transform: scale(0.94) translateY(8px);
  }
}

/* Works with display: none → block transitions via allow-discrete */
.panel {
  display: none;
  transition: display 0.2s allow-discrete, opacity 0.2s;

  &.visible {
    display: block;
    opacity: 1;

    @starting-style {
      opacity: 0;
    }
  }
}
```

---

## Custom Easing Curves

Never use `ease`, `ease-in-out`, or `linear`. These feel robotic.

```css
:root {
  /* Swift enter, long smooth tail — feels premium */
  --ease-out-expo: cubic-bezier(0.16, 1, 0.3, 1);

  /* Slight overshoot — feels physical (use sparingly) */
  --ease-spring: cubic-bezier(0.34, 1.56, 0.64, 1);

  /* Fast exit — element leaving screen */
  --ease-in-expo: cubic-bezier(0.7, 0, 0.84, 0);

  /* Smooth deceleration */
  --ease-out-cubic: cubic-bezier(0.33, 1, 0.68, 1);
}
```

---

## Prefers Reduced Motion

Always wrap non-essential animations.

```css
/* Provide static fallback first */
.animated-element {
  /* Static version — works for everyone */
}

/* Then add motion for users who haven't opted out */
@media (prefers-reduced-motion: no-preference) {
  .animated-element {
    transition: transform 0.4s var(--ease-out-expo);
    animation: slide-in 0.5s var(--ease-out-expo) both;
  }
}
```

---

## Scroll-Driven Animations (No IntersectionObserver Needed)

```css
/* Fade in as element scrolls into view — pure CSS */
@keyframes fade-up {
  from { opacity: 0; transform: translateY(20px); }
  to   { opacity: 1; transform: translateY(0); }
}

.reveal {
  animation: fade-up linear both;
  animation-timeline: view();
  animation-range: entry 0% entry 30%;

  @media (prefers-reduced-motion: reduce) {
    animation: none;
  }
}
```
