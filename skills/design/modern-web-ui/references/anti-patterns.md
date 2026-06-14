# Anti-Patterns: What NOT to Do

These are the patterns that make a UI look AI-generated, generic, or low-effort. Avoid all of them.

---

## ❌ The AI Default Aesthetic (The "Slop" Checklist)

These combinations immediately signal an AI-generated default:

```css
/* ❌ NEVER: Purple/indigo gradient background */
background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);

/* ❌ NEVER: Giant border radius on everything */
border-radius: 24px;  /* rounded-2xl */
border-radius: 16px;  /* rounded-xl on cards */

/* ❌ NEVER: Massive drop shadow */
box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25);  /* shadow-2xl */

/* ❌ NEVER: Raw HEX in component styles */
color: #6366f1;  /* indigo-500 */
background: #f9fafb;  /* gray-50 */

/* ❌ NEVER: Uniform card grid with zero hierarchy */
/* Every card same size, same padding, same color = visual noise */

/* ❌ NEVER: "Glassmorphism lite" — just blur + opacity with no refinement */
background: rgba(255, 255, 255, 0.1);
backdrop-filter: blur(10px);
/* Without: thin borders, proper color depth, highlight catches, or mouse tracking */
```

**The four-way test:** If your UI uses (1) purple/indigo palette, (2) `border-radius > 16px`, (3) `rgba()` colors, AND (4) a uniform card grid — it is AI slop. Change at least 3 of these 4.

---

## ❌ Tailwind Anti-Patterns (in Claude artifacts especially)

```tsx
// ❌ NEVER: Stacking generic Tailwind utilities that bake in AI defaults
<div className="rounded-2xl shadow-2xl bg-gradient-to-r from-purple-500 to-indigo-600 p-8">

// ❌ NEVER: Text-gray-500 / text-gray-400 for everything muted
// Use oklch() custom properties instead — gives you semantic control

// ❌ NEVER: "ring" utilities as a substitute for real focus styles
// Implement :focus-visible with actual design intent

// ✅ OK: Tailwind for LAYOUT utilities only
<div className="flex items-center gap-3 w-full">

// ✅ BETTER: CSS custom properties for all visual decisions
<div style={{ background: 'var(--glass-surface)', borderRadius: 'var(--radius-md)' }}>
```

---

## ❌ Animation Anti-Patterns

```css
/* ❌ NEVER: Linear transitions on interactive elements */
transition: all 0.3s linear;

/* ❌ NEVER: Excessive animation on every element */
/* Only animate what the user directly interacted with, or one ambient element */

/* ❌ NEVER: Scale animations that affect layout (cause reflow) */
/* Use transform: scale() — not width/height */

/* ❌ NEVER: Animations without prefers-reduced-motion */
@keyframes bounce { ... }  /* No media query wrapper = accessibility fail */

/* ❌ NEVER: Hover transforms without a transition */
.card:hover { transform: translateY(-4px); }  /* Snaps instantly — looks broken */
/* Must pair: */
.card { transition: transform 0.3s var(--ease-out-expo); }
```

---

## ❌ Typography Anti-Patterns

```css
/* ❌ NEVER: System default font with no customization */
/* Always declare a font stack with a variable font */

/* ❌ NEVER: All font weights at 400 or 700 only */
/* Use 450, 500, 550, 600, 650, 700 across heading levels */

/* ❌ NEVER: No letter-spacing on headings */
/* Display text looks better with slight negative tracking */
h1 { /* Missing: letter-spacing: -0.025em */ }

/* ❌ NEVER: line-height: 1 on body text */
/* Body should be 1.5–1.65 for readability */

/* ❌ NEVER: Font size below 12px for any readable label */
/* 11px max for purely decorative metadata, 12px minimum for functional text */
```

---

## ❌ Color Anti-Patterns

```css
/* ❌ NEVER: oklch values with L > 0.95 and C > 0.01 simultaneously */
/* That's too saturated for backgrounds — causes eye strain */

/* ❌ NEVER: Two high-chroma accent colors competing */
/* One primary accent. Secondary is desaturated. */

/* ❌ NEVER: "Light mode" as pure white #fff / "dark mode" as pure black #000 */
/* Pure white: oklch(0.97 0.004 250) — barely off-white */
/* Pure black: oklch(0.08 0.01 250) — not #000000 */

/* ❌ NEVER: Semantic colors chosen arbitrarily */
/* Success = GREEN. Warning = AMBER. Error = RED. Info = BLUE. */
/* Don't use blue for success or green for info. */

/* ❌ NEVER: Insufficient contrast for muted text */
/* --text-muted must pass 4.5:1 against its background */
```

---

## ❌ Layout Anti-Patterns

```css
/* ❌ NEVER: Viewport-based media queries on card components */
/* Cards that break at 768px but work inside a 400px sidebar? Use container queries. */

/* ❌ NEVER: Fixed pixel widths on cards in a grid */
.card { width: 300px; }  /* Will overflow on mobile, gap on desktop */
/* Use: width: min(300px, 100%) or auto-fill minmax() */

/* ❌ NEVER: Z-index values above 9999 */
/* Design your stacking context. 10/20/30 is enough. */

/* ❌ NEVER: Position: absolute without a positioned parent */
/* Creates bugs when the component moves to a different context */

/* ❌ NEVER: Overflow: hidden on scrollable containers without explicit height */
/* Results in content clipping invisibly */
```

---

## ❌ Interaction Anti-Patterns

```css
/* ❌ NEVER: Removing :focus outline without a replacement */
:focus { outline: none; }  /* Accessibility failure */
/* Always provide :focus-visible styles */

/* ❌ NEVER: Click handlers on non-interactive elements without ARIA */
<div onClick={handle}>  /* Should be <button> or role="button" with keyboard support */

/* ❌ NEVER: Tooltips that appear on click on desktop */
/* Tooltips are hover. Context menus / popovers are click. */

/* ❌ NEVER: Touch targets smaller than 44x44px on mobile */
/* Minimum: padding 0.5rem on icons inside buttons */
```

---

## ❌ TSX / React Anti-Patterns

```tsx
// ❌ NEVER: Inline style objects with magic numbers
style={{ padding: '13px', marginTop: '7px', borderRadius: '11px' }}
// Use: CSS custom properties via var() or the --space-N scale

// ❌ NEVER: useEffect for simple derived state
// Compute it directly in the render body

// ❌ NEVER: Multiple useState when a single object suffices
const [tab, setTab] = useState(0);
const [open, setOpen] = useState(false);
const [active, setActive] = useState(null);
// Consider: const [ui, setUi] = useState({ tab: 0, open: false, active: null })

// ❌ NEVER: setTimeout in components without cleanup
useEffect(() => {
  setTimeout(() => setState(...), 300);  // Memory leak if component unmounts
}, []);
// Use: const t = setTimeout(...); return () => clearTimeout(t);

// ❌ NEVER: Anonymous inline arrow functions for expensive handlers
<div onMouseMove={e => expensiveCalc(e)}>  // New fn every render
// Use: useCallback or define handler outside JSX
```

---

## The Final Check

Before delivering any UI, ask yourself:

> "If I saw this in a screenshot without context, would I immediately know it was built by Claude using default settings?"

If yes → change the palette, tighten the radius, add a signature element, and make it specific to the actual product.
