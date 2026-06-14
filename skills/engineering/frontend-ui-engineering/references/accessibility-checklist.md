# Accessibility (WCAG 2.1 AA) Checklist

Use this companion checklist when validating components or pages built with the `frontend-ui-engineering` skill.

## 1. Keyboard Navigation & Interaction

- [ ] **Focus Order:** Navigation order must be logical and sequential (usually top-to-bottom, left-to-right).
- [ ] **Focus Indicator:** Interactive elements must have a visible, clear `:focus-visible` styling. Never disable the default outline without providing a highly visible custom design.
- [ ] **Interactive Elements:** Buttons (`<button>`), links (`<a>`), inputs (`<input>`), select dropdowns (`<select>`), and checkboxes must be focusable using the `Tab` key.
- [ ] **No Keyboard Traps:** Focus must never be trapped within an element or widget (like an open modal dialog) unless it can be dismissed using a standard key (e.g., `Esc`).
- [ ] **Activation:** Buttons must be activatable with both `Enter` and `Space`. Links must be activatable with `Enter`.

## 2. Forms & Inputs

- [ ] **Associated Labels:** Every form input must have a programmatically associated `<label>` using matching `id` and `htmlFor` (or wrapped in `<label>`).
- [ ] **Required Fields:** Required fields must have an `aria-required="true"` or `required` attribute.
- [ ] **Error Descriptions:** Form validation error messages must be programmatically associated with their corresponding fields using `aria-describedby`.
- [ ] **Inert Fields:** Disabled fields should use the standard `disabled` attribute to ensure they are skipped in the focus order.

## 3. ARIA & Semantics

- [ ] **Semantic Markup:** Prefer semantic tags (e.g., `<main>`, `<header>`, `<nav>`, `<footer>`, `<section>`) over generic `<div>` grids to allow screen readers to parse page layout.
- [ ] **Heading Hierarchy:** Headings must go sequentially from `h1` through `h6`. Do not skip heading levels (e.g., do not jump from `h1` to `h3`).
- [ ] **Image Alt Text:** Every image (`<img>`) must have an `alt` description. Decorative images must use an empty alt attribute (`alt=""`).
- [ ] **ARIA Roles & State:** For custom controls (e.g., accordion, tab panel), correct ARIA roles and state indicators (`aria-expanded="true/false"`, `aria-selected="true/false"`) must be dynamically set and updated in component state.
- [ ] **Dynamic Content Updates:** Use polite live regions (`aria-live="polite"` or `role="status"`) for toast notifications, live counts, or status banners that change dynamically on the page.

## 4. Visual Layout & Color Contrast

- [ ] **Minimum Contrast:** Normal text (under 18pt) must have a contrast ratio of at least **4.5:1** against its background. Large text (over 18pt or bold over 14pt) must have at least **3:1**.
- [ ] **No Color-Only Cues:** Color must never be the *sole* visual indicator of state, action, or success/error. Always supplement with icons, bold text, or text labels (e.g., an error input must have an error icon and descriptive text, not just a red border).
- [ ] **Responsive Reflow:** The page must support zooming up to 200% without losing text content or layout usability, and must reflow cleanly without horizontal scrollbars.
- [ ] **Touch Target Size:** Interactive touch targets must be at least **44x44 CSS pixels** to allow easy tapping on mobile screens.

## 5. Automated Verification Checklist

- [ ] **DevTools Audit:** Run the browser's Lighthouse/Accessibility audit or axe-core extension before committing.
- [ ] **Keyboard-Only Test:** Unplug your mouse, tab through the page, activate modals, expand dropdowns, and close dialogs to verify complete accessibility.
- [ ] **Console Audit:** Confirm that no duplicate ID warnings or missing ARIA attribute errors are printed in the developer console.
