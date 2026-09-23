# Earned overall map

`Chapter-Kits/overall-flow.mmd` is the live course map. It grows when a
section's source evidence is recorded. It does not show the rest of the textbook.

## Rules

1. Root node id `S`, label `STATISTICS` (or the course short name).
2. One hub **per processed section**, sibling off the root. Id `CH{chapter}_{section}`
   (`CH1_1`, `CH1_2`, `CH2_1`). Label `1.1 Data basics`, `1.2 …`.
3. Under a hub, only nodes justified by that section's `ledger.md`.
   Screenshots earn nodes when they are the section source (read in place; do
   not copy PNGs into Chapter-Kits). They do not earn nodes for a later
   section the user has not sent.
4. When 1.2 arrives: prepare a candidate, then **add** `CH1_2` beside
   `CH1_1`. Do not delete 1.1. Do not add a Chapter-1 parent that 1.1 never had.
5. If `overall-flow.mmd` is missing, create root + this section only. Never
   seed from the syllabus preview.
6. Preserve prior nodes, labels, and edges, not just hub IDs. Use one node or
   edge per line. Before replacing the live file, run:

   ```sh
   python3 "$SKILL_DIR/scripts/validate_kit.py" --previous "$KIT/overall-flow.mmd" --candidate "$KIT/overall-flow.candidate.mmd"
   ```

   Only after this passes, copy live to `overall-flow.prev.mmd`, then promote
   the candidate. The check is conservative and is not a Mermaid syntax parser.
   Separately inspect syntax and rendering. For an intentional correction,
   document the exact changed statements and source evidence in the ledger,
   review the validator's diff, and obtain explicit correction approval before
   bypassing preservation. Never reset the baseline just to silence a failure.
7. Publisher flowcharts that preview later chapters stay in
   `preserved-claims.json` as **Syllabus preview**. They are not the Overall
   Map button.
8. Keep one `overall-flow.mmd` even when it outgrows a single GoodNotes URL.
   The hub builder splits the import by chapter (`CH{chapter}_{section}` hubs);
   do not hand-split the live file. The split handles plain `A --> B` edges,
   inline node labels, `class`, and `linkStyle`. Any other statement (for
   example `subgraph`) stops the build instead of guessing.
9. Discrete vs continuous, mean/median, inference, regression: omit until a
   supplied source actually teaches them.

## Test

A stranger looking only at overall-flow.mmd should not be able to study the
next unearned section from it.

1.1 earned/not-earned list: `Chapter-Kits/Chapter-01/1.1/ledger.md`.
