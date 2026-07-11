"use strict";
// Study-surface behaviors — authored for TypeScript 7 (native compiler),
// emitted as classic inline ES2019. Contract: no storage, no network, no
// eval, no inline handlers; every piece of state is in-memory and dies with
// the tab. This file is the source of truth; the compiled output is inlined
// into each artifact by the assembler.
const MARK_LABEL = {
    unmarked: "",
    got: "recalled",
    again: "revisit",
};
(() => {
    var _a, _b, _c, _d, _e;
    const doc = document;
    const rootEl = doc.documentElement;
    // ---- Theme toggle (in-memory only; default follows prefers-color-scheme).
    const themeBtn = doc.querySelector("[data-theme-toggle]");
    const systemDark = window.matchMedia("(prefers-color-scheme: dark)");
    const effectiveTheme = () => {
        const forced = rootEl.getAttribute("data-theme");
        if (forced === "dark" || forced === "light")
            return forced;
        return systemDark.matches ? "dark" : "light";
    };
    const paintThemeBtn = () => {
        if (!themeBtn)
            return;
        const next = effectiveTheme() === "dark" ? "light" : "dark";
        themeBtn.textContent = next === "dark" ? "◐ dark" : "◑ light";
        themeBtn.setAttribute("aria-label", `Switch to ${next} theme`);
    };
    const toggleTheme = () => {
        rootEl.setAttribute("data-theme", effectiveTheme() === "dark" ? "light" : "dark");
        paintThemeBtn();
    };
    themeBtn === null || themeBtn === void 0 ? void 0 : themeBtn.addEventListener("click", toggleTheme);
    systemDark.addEventListener("change", paintThemeBtn);
    paintThemeBtn();
    // ---- Scrollspy: highlight the index-rail link for the section in view.
    const railLinks = Array.from(doc.querySelectorAll(".rail a[href^='#']"));
    const byId = new Map(railLinks.map((a) => [a.hash.slice(1), a]));
    const spy = new IntersectionObserver((entries) => {
        for (const entry of entries) {
            const link = byId.get(entry.target.id);
            if (!link)
                continue;
            if (entry.isIntersecting) {
                for (const other of railLinks)
                    other.classList.remove("active");
                link.classList.add("active");
            }
        }
    }, { rootMargin: "-35% 0px -55% 0px" });
    for (const id of byId.keys()) {
        const section = doc.getElementById(id);
        if (section)
            spy.observe(section);
    }
    // ---- Retrieval deck: reveal/hide all, ephemeral self-marks, tally.
    const cues = Array.from(doc.querySelectorAll("[data-cue]")).flatMap((root) => {
        const details = root.querySelector("details");
        return details ? [{ root, details, mark: "unmarked" }] : [];
    });
    const tally = doc.querySelector("[data-tally]");
    const paintTally = () => {
        if (!tally)
            return;
        const got = cues.filter((c) => c.mark === "got").length;
        const again = cues.filter((c) => c.mark === "again").length;
        tally.textContent =
            `${cues.length} cues · ${got} recalled · ${again} to revisit` +
                " · resets on reload";
    };
    const paintCue = (cue) => {
        cue.root.setAttribute("data-mark", cue.mark);
        const state = cue.root.querySelector(".cue-state");
        if (state)
            state.textContent = MARK_LABEL[cue.mark];
    };
    const setMark = (cue, mark) => {
        cue.mark = cue.mark === mark ? "unmarked" : mark;
        paintCue(cue);
        paintTally();
    };
    for (const cue of cues) {
        (_a = cue.root
            .querySelector("[data-mark-got]")) === null || _a === void 0 ? void 0 : _a.addEventListener("click", () => setMark(cue, "got"));
        (_b = cue.root
            .querySelector("[data-mark-again]")) === null || _b === void 0 ? void 0 : _b.addEventListener("click", () => setMark(cue, "again"));
    }
    const setAll = (open) => {
        for (const cue of cues)
            cue.details.open = open;
    };
    (_c = doc
        .querySelector("[data-reveal-all]")) === null || _c === void 0 ? void 0 : _c.addEventListener("click", () => setAll(true));
    (_d = doc
        .querySelector("[data-hide-all]")) === null || _d === void 0 ? void 0 : _d.addEventListener("click", () => setAll(false));
    (_e = doc
        .querySelector("[data-reset-marks]")) === null || _e === void 0 ? void 0 : _e.addEventListener("click", () => {
        for (const cue of cues) {
            cue.mark = "unmarked";
            paintCue(cue);
        }
        paintTally();
    });
    // ---- Keyboard driving: j/k move between cues, o toggles, g/a mark, t theme.
    let cursor = -1;
    const focusCue = (index) => {
        var _a;
        if (cues.length === 0)
            return;
        cursor = (index + cues.length) % cues.length;
        const cue = cues[cursor];
        (_a = cue.details.querySelector("summary")) === null || _a === void 0 ? void 0 : _a.focus();
        cue.root.scrollIntoView({ block: "center", behavior: "smooth" });
    };
    doc.addEventListener("keydown", (event) => {
        if (event.metaKey || event.ctrlKey || event.altKey)
            return;
        const target = event.target;
        if (target && /^(BUTTON|A|SUMMARY)$/.test(target.tagName) === false) {
            // No form fields exist on this page; plain keys are safe everywhere.
        }
        switch (event.key) {
            case "j":
                focusCue(cursor + 1);
                break;
            case "k":
                focusCue(cursor - 1);
                break;
            case "o":
                if (cursor >= 0)
                    cues[cursor].details.open = !cues[cursor].details.open;
                break;
            case "g":
                if (cursor >= 0)
                    setMark(cues[cursor], "got");
                break;
            case "a":
                if (cursor >= 0)
                    setMark(cues[cursor], "again");
                break;
            case "t":
                toggleTheme();
                break;
            default:
                return;
        }
    });
    paintTally();
})();
