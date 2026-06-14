# Tactile Brutalism Design System

A pushback against sterile, overly smooth layouts. Honors raw geometry, grid lines, and print layout constraints — feels exceptionally crisp and precise. Human-engineered, not AI-generated.

**Best for:** Developer tools, security dashboards, CLI companion UIs, technical documentation, log viewers, network monitors, homelab interfaces, PCI/compliance tooling.

This is the default system for LexLabs tooling (ssh-hardener UI, mitmrouter status pages, EVE-NG lab dashboards, Wazuh companion views).

---

## Token System

```css
:root {
  /* Light mode base (Tactile works well light OR dark — choose per project) */
  --bg-page:        oklch(0.97 0.004 250);    /* Off-white, not pure white */
  --bg-surface:     oklch(1 0 0);
  --bg-sunken:      oklch(0.94 0.005 250);    /* Input backgrounds, code blocks */
  --bg-overlay:     oklch(0.96 0.004 250);    /* Hover states */

  /* Dark mode base (security/monitoring tools — swap in via prefers-color-scheme) */
  /* --bg-page:    oklch(0.10 0.008 250); */
  /* --bg-surface: oklch(0.13 0.01 250);  */
  /* --bg-sunken:  oklch(0.08 0.008 250); */

  /* Borders — the defining characteristic of Tactile */
  --border:         oklch(0.82 0.01 250);     /* Standard 1px border */
  --border-strong:  oklch(0.65 0.015 250);    /* Emphasis, active states */
  --border-subtle:  oklch(0.90 0.006 250);    /* Dividers */

  /* Text */
  --text-primary:   oklch(0.15 0.01 250);     /* Near-black */
  --text-secondary: oklch(0.40 0.015 250);
  --text-muted:     oklch(0.60 0.012 250);
  --text-disabled:  oklch(0.75 0.008 250);
  --text-on-accent: oklch(1 0 0);

  /* Accent — use sparingly, 1 primary accent max */
  --accent:         oklch(0.45 0.22 256);     /* Deep electric blue */
  --accent-hover:   color-mix(in oklch, var(--accent) 85%, black);
  --accent-subtle:  oklch(0.45 0.22 256 / 0.08);
  --accent-border:  oklch(0.45 0.22 256 / 0.35);

  /* Semantic */
  --success:        oklch(0.50 0.18 142);
  --success-subtle: oklch(0.50 0.18 142 / 0.08);
  --warning:        oklch(0.58 0.20 70);
  --warning-subtle: oklch(0.58 0.20 70 / 0.08);
  --danger:         oklch(0.50 0.22 28);
  --danger-subtle:  oklch(0.50 0.22 28 / 0.08);
  --info:           oklch(0.55 0.18 240);
  --info-subtle:    oklch(0.55 0.18 240 / 0.08);

  /* Mono — critical for security/terminal tools */
  --font-mono: 'JetBrains Mono', 'Fira Code', 'Cascadia Code', ui-monospace, monospace;
  --font-body: 'Inter Var', 'Geist Var', system-ui, sans-serif;

  /* Spacing */
  --space-1: 0.25rem;
  --space-2: 0.5rem;
  --space-3: 0.75rem;
  --space-4: 1rem;
  --space-5: 1.5rem;
  --space-6: 2rem;
  --space-8: 3rem;

  /* Radii — SMALL. This is the defining trait. */
  --radius-xs: 2px;
  --radius-sm: 4px;
  --radius-md: 6px;

  /* Shadows — asymmetric, physical */
  --shadow-sm: 2px 2px 0px var(--border);
  --shadow-md: 3px 3px 0px var(--border-strong);
  --shadow-lg: 4px 4px 0px var(--border-strong);

  /* Motion — faster, no spring */
  --ease-out: cubic-bezier(0.16, 1, 0.3, 1);
  --transition-fast:   all 0.12s var(--ease-out);
  --transition-base:   all 0.2s  var(--ease-out);
}
```

---

## Core Surface: Bordered Panel

```css
.panel {
  background: var(--bg-surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  padding: var(--space-5);

  /* Optional: asymmetric shadow for physical feel */
  box-shadow: var(--shadow-sm);
}

.panel--active {
  border-color: var(--accent-border);
  box-shadow: 2px 2px 0px var(--accent-border);
}

/* :has() to auto-style panels with active children */
.panel:has(input:focus) {
  border-color: var(--accent-border);
}
```

## Tactile Button System

```css
.btn {
  display: inline-flex;
  align-items: center;
  gap: var(--space-2);
  padding: 0.45rem 0.9rem;
  border-radius: var(--radius-sm);
  font-size: 0.875rem;
  font-weight: 500;
  font-family: var(--font-body);
  cursor: pointer;
  transition: var(--transition-fast);
  white-space: nowrap;

  &:focus-visible {
    outline: 2px solid var(--accent);
    outline-offset: 2px;
  }
}

.btn-primary {
  background: var(--accent);
  color: var(--text-on-accent);
  border: 1px solid var(--accent);
  box-shadow: var(--shadow-sm);

  &:hover {
    background: var(--accent-hover);
    box-shadow: var(--shadow-md);
    transform: translate(-1px, -1px);   /* Lifts away from shadow */
  }

  &:active {
    transform: translate(2px, 2px);     /* Presses into shadow */
    box-shadow: none;
  }
}

.btn-secondary {
  background: var(--bg-surface);
  color: var(--text-primary);
  border: 1px solid var(--border-strong);
  box-shadow: var(--shadow-sm);

  &:hover {
    background: var(--bg-overlay);
    box-shadow: var(--shadow-md);
    transform: translate(-1px, -1px);
  }

  &:active { transform: translate(2px, 2px); box-shadow: none; }
}

.btn-danger {
  background: var(--danger-subtle);
  color: var(--danger);
  border: 1px solid oklch(0.50 0.22 28 / 0.3);
}
```

## Data Table (Security/Log Viewer Pattern)

```css
.data-table {
  width: 100%;
  border-collapse: collapse;
  font-family: var(--font-body);
  font-size: 0.875rem;

  thead {
    background: var(--bg-sunken);
    border-bottom: 2px solid var(--border-strong);

    th {
      padding: var(--space-2) var(--space-4);
      text-align: left;
      font-weight: 600;
      font-size: 0.75rem;
      letter-spacing: 0.06em;
      text-transform: uppercase;
      color: var(--text-muted);
    }
  }

  tbody {
    tr {
      border-bottom: 1px solid var(--border-subtle);
      transition: var(--transition-fast);

      &:hover { background: var(--bg-overlay); }
      &:last-child { border-bottom: none; }
    }

    td {
      padding: var(--space-3) var(--space-4);
      color: var(--text-primary);
      vertical-align: middle;
    }
  }
}

/* Monospace columns for IPs, ports, hashes, CVEs */
.cell-mono {
  font-family: var(--font-mono);
  font-size: 0.8rem;
  color: var(--text-secondary);
}
```

## Status Badge System

```css
.badge {
  display: inline-flex;
  align-items: center;
  gap: var(--space-1);
  padding: 0.15rem 0.5rem;
  border-radius: var(--radius-sm);
  font-size: 0.7rem;
  font-weight: 600;
  letter-spacing: 0.04em;
  text-transform: uppercase;
  border: 1px solid;
}

.badge-success { background: var(--success-subtle); color: var(--success); border-color: oklch(0.50 0.18 142 / 0.3); }
.badge-warning { background: var(--warning-subtle); color: var(--warning); border-color: oklch(0.58 0.20 70 / 0.3); }
.badge-danger  { background: var(--danger-subtle);  color: var(--danger);  border-color: oklch(0.50 0.22 28 / 0.3); }
.badge-info    { background: var(--info-subtle);    color: var(--info);    border-color: oklch(0.55 0.18 240 / 0.3); }
.badge-neutral { background: var(--bg-sunken);      color: var(--text-muted); border-color: var(--border); }
```

## Keyboard Shortcut Hint

```css
.kbd {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 20px;
  height: 20px;
  padding: 0 4px;
  background: var(--bg-sunken);
  border: 1px solid var(--border);
  border-bottom-width: 2px;             /* Physical key feel */
  border-radius: var(--radius-xs);
  font-family: var(--font-mono);
  font-size: 0.65rem;
  font-weight: 600;
  color: var(--text-secondary);
  line-height: 1;
}
```

## Code / Terminal Block

```css
.code-block {
  background: var(--bg-sunken);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  padding: var(--space-4);
  font-family: var(--font-mono);
  font-size: 0.8rem;
  line-height: 1.65;
  color: var(--text-primary);
  overflow-x: auto;

  /* Optional: left accent stripe for emphasis */
  &.highlighted {
    border-left: 3px solid var(--accent);
    padding-left: calc(var(--space-4) - 2px);
  }
}

/* Inline code */
code {
  font-family: var(--font-mono);
  font-size: 0.85em;
  background: var(--bg-sunken);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-xs);
  padding: 0.1em 0.35em;
  color: var(--accent);
}
```

## Security Tool Layout Pattern

```css
/* Classic security tool layout: sidebar nav + main panel + detail drawer */
.security-layout {
  display: grid;
  grid-template-columns: 220px 1fr;
  min-height: 100vh;
  background: var(--bg-page);
}

.sidebar-nav {
  background: var(--bg-surface);
  border-right: 1px solid var(--border);
  padding: var(--space-4) 0;

  .nav-section-label {
    padding: var(--space-2) var(--space-4);
    font-size: 0.65rem;
    font-weight: 700;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: var(--text-disabled);
    margin-top: var(--space-3);
  }

  .nav-item {
    display: flex;
    align-items: center;
    gap: var(--space-3);
    padding: var(--space-2) var(--space-4);
    color: var(--text-secondary);
    font-size: 0.875rem;
    font-weight: 450;
    cursor: pointer;
    border-left: 2px solid transparent;
    transition: var(--transition-fast);

    &:hover {
      background: var(--bg-overlay);
      color: var(--text-primary);
    }

    &.active {
      background: var(--accent-subtle);
      color: var(--accent);
      border-left-color: var(--accent);
      font-weight: 600;
    }
  }
}

.main-panel {
  display: flex;
  flex-direction: column;
  overflow: hidden;

  .panel-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: var(--space-4) var(--space-5);
    border-bottom: 1px solid var(--border);
    background: var(--bg-surface);
  }

  .panel-body {
    flex: 1;
    padding: var(--space-5);
    overflow-y: auto;
  }
}
```

## Stat Card (Metrics / KPIs)

```css
.stat-card {
  background: var(--bg-surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  padding: var(--space-4) var(--space-5);
  box-shadow: var(--shadow-sm);
  container-type: inline-size;

  .stat-label {
    font-size: 0.75rem;
    font-weight: 600;
    letter-spacing: 0.06em;
    text-transform: uppercase;
    color: var(--text-muted);
    margin-bottom: var(--space-2);
  }

  .stat-value {
    font-size: 2rem;
    font-weight: 700;
    letter-spacing: -0.02em;
    color: var(--text-primary);
    line-height: 1;
  }

  .stat-delta {
    font-size: 0.8rem;
    font-weight: 500;
    margin-top: var(--space-2);

    &.up   { color: var(--success); }
    &.down { color: var(--danger); }
  }
}
```

---

## Dark Mode Switch (Security Tools)

```css
@media (prefers-color-scheme: dark) {
  :root {
    --bg-page:        oklch(0.10 0.008 250);
    --bg-surface:     oklch(0.13 0.01 250);
    --bg-sunken:      oklch(0.08 0.008 250);
    --bg-overlay:     oklch(0.16 0.01 250);

    --border:         oklch(0.25 0.01 250);
    --border-strong:  oklch(0.35 0.015 250);
    --border-subtle:  oklch(0.18 0.008 250);

    --text-primary:   oklch(0.93 0.006 250);
    --text-secondary: oklch(0.75 0.01 250);
    --text-muted:     oklch(0.55 0.012 250);
    --text-disabled:  oklch(0.40 0.008 250);

    --shadow-sm: 2px 2px 0px oklch(0 0 0 / 0.5);
    --shadow-md: 3px 3px 0px oklch(0 0 0 / 0.6);
  }
}
```
