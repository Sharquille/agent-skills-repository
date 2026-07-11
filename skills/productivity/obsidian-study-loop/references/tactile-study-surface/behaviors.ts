// Study-surface behaviors — authored for TypeScript 7 (native compiler),
// emitted as classic inline ES2019. Contract: no storage, no network, no
// eval, no inline handlers; every piece of state is in-memory and dies with
// the tab. This file is the source of truth; the compiled output is inlined
// into each artifact by the assembler.

type CueMark = "unmarked" | "got" | "again";

interface CueState {
  readonly root: HTMLElement;
  readonly details: HTMLDetailsElement;
  mark: CueMark;
}

const MARK_LABEL = {
  unmarked: "",
  got: "recalled",
  again: "revisit",
} as const satisfies Record<CueMark, string>;

(() => {
  const doc = document;
  const rootEl = doc.documentElement;

  // ---- Theme toggle (in-memory only; default follows prefers-color-scheme).
  const themeBtn = doc.querySelector<HTMLButtonElement>("[data-theme-toggle]");
  const systemDark = window.matchMedia("(prefers-color-scheme: dark)");
  const effectiveTheme = (): "dark" | "light" => {
    const forced = rootEl.getAttribute("data-theme");
    if (forced === "dark" || forced === "light") return forced;
    return systemDark.matches ? "dark" : "light";
  };
  const paintThemeBtn = (): void => {
    if (!themeBtn) return;
    const next = effectiveTheme() === "dark" ? "light" : "dark";
    themeBtn.textContent = next === "dark" ? "◐ dark" : "◑ light";
    themeBtn.setAttribute("aria-label", `Switch to ${next} theme`);
  };
  const toggleTheme = (): void => {
    rootEl.setAttribute(
      "data-theme",
      effectiveTheme() === "dark" ? "light" : "dark",
    );
    paintThemeBtn();
  };
  themeBtn?.addEventListener("click", toggleTheme);
  systemDark.addEventListener("change", paintThemeBtn);
  paintThemeBtn();

  // ---- Scrollspy: highlight the index-rail link for the section in view.
  const railLinks = Array.from(
    doc.querySelectorAll<HTMLAnchorElement>(".rail a[href^='#']"),
  );
  const byId = new Map<string, HTMLAnchorElement>(
    railLinks.map((a) => [a.hash.slice(1), a]),
  );
  const spy = new IntersectionObserver(
    (entries) => {
      for (const entry of entries) {
        const link = byId.get(entry.target.id);
        if (!link) continue;
        if (entry.isIntersecting) {
          for (const other of railLinks) other.classList.remove("active");
          link.classList.add("active");
        }
      }
    },
    { rootMargin: "-35% 0px -55% 0px" },
  );
  for (const id of byId.keys()) {
    const section = doc.getElementById(id);
    if (section) spy.observe(section);
  }

  // ---- Retrieval deck: reveal/hide all, ephemeral self-marks, tally.
  const cues: CueState[] = Array.from(
    doc.querySelectorAll<HTMLElement>("[data-cue]"),
  ).flatMap((root) => {
    const details = root.querySelector<HTMLDetailsElement>("details");
    return details ? [{ root, details, mark: "unmarked" as CueMark }] : [];
  });

  const tally = doc.querySelector<HTMLElement>("[data-tally]");
  const paintTally = (): void => {
    if (!tally) return;
    const got = cues.filter((c) => c.mark === "got").length;
    const again = cues.filter((c) => c.mark === "again").length;
    tally.textContent =
      `${cues.length} cues · ${got} recalled · ${again} to revisit` +
      " · resets on reload";
  };

  const paintCue = (cue: CueState): void => {
    cue.root.setAttribute("data-mark", cue.mark);
    const state = cue.root.querySelector<HTMLElement>(".cue-state");
    if (state) state.textContent = MARK_LABEL[cue.mark];
  };

  const setMark = (cue: CueState, mark: CueMark): void => {
    cue.mark = cue.mark === mark ? "unmarked" : mark;
    paintCue(cue);
    paintTally();
  };

  for (const cue of cues) {
    cue.root
      .querySelector<HTMLButtonElement>("[data-mark-got]")
      ?.addEventListener("click", () => setMark(cue, "got"));
    cue.root
      .querySelector<HTMLButtonElement>("[data-mark-again]")
      ?.addEventListener("click", () => setMark(cue, "again"));
  }

  const setAll = (open: boolean): void => {
    for (const cue of cues) cue.details.open = open;
  };
  doc
    .querySelector<HTMLButtonElement>("[data-reveal-all]")
    ?.addEventListener("click", () => setAll(true));
  doc
    .querySelector<HTMLButtonElement>("[data-hide-all]")
    ?.addEventListener("click", () => setAll(false));
  doc
    .querySelector<HTMLButtonElement>("[data-reset-marks]")
    ?.addEventListener("click", () => {
      for (const cue of cues) {
        cue.mark = "unmarked";
        paintCue(cue);
      }
      paintTally();
    });

  // ---- Keyboard driving: j/k move between cues, o toggles, g/a mark, t theme.
  let cursor = -1;
  const focusCue = (index: number): void => {
    if (cues.length === 0) return;
    cursor = (index + cues.length) % cues.length;
    const cue = cues[cursor];
    cue.details.querySelector("summary")?.focus();
    cue.root.scrollIntoView({ block: "center", behavior: "smooth" });
  };

  doc.addEventListener("keydown", (event: KeyboardEvent) => {
    if (event.metaKey || event.ctrlKey || event.altKey) return;
    const target = event.target as HTMLElement | null;
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
        if (cursor >= 0) cues[cursor].details.open = !cues[cursor].details.open;
        break;
      case "g":
        if (cursor >= 0) setMark(cues[cursor], "got");
        break;
      case "a":
        if (cursor >= 0) setMark(cues[cursor], "again");
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
