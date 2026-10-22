from __future__ import annotations

import html
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SKILL_DIR = Path(__file__).resolve().parents[1]
SCRIPT = SKILL_DIR / "scripts" / "build_anki_import.py"


class BuildAnkiImportTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.vault = self.root / "Vault"
        (self.vault / "_study" / "anki").mkdir(parents=True)
        (self.vault / "Notes").mkdir()
        (self.vault / "Notes" / "Chapter 1.md").write_text(
            "# Chapter 1\n\n## First\n\nFirst.\n\n## Second\n\nSecond.\n",
            encoding="utf-8",
        )

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def manifest(self) -> dict[str, object]:
        return {
            "schema": "anki-study-sync.manifest",
            "version": 1,
            "chapter_id": "chapter-1",
            "deck": "Course::Chapter 1",
            "notetype": "Basic",
            "objectives": ["First objective", "Second objective"],
            "cards": [
                {
                    "id": "course.ch1.second.typed",
                    "objective": "Second objective",
                    "type": "typed",
                    "prompt": "Second prompt",
                    "answer": "Second answer",
                    "source": "Notes/Chapter 1.md#Second",
                    "revision": 2,
                    "status": "active",
                    "tags": ["chapter-1", "course"],
                },
                {
                    "id": "course.ch1.first.basic",
                    "objective": "First objective",
                    "type": "basic",
                    "prompt": "First\nprompt",
                    "answer": "First & answer",
                    "source": "Notes/Chapter 1.md#First",
                    "revision": 1,
                    "status": "active",
                    "tags": ["course"],
                },
            ],
        }

    def run_script(
        self, manifest: dict[str, object]
    ) -> subprocess.CompletedProcess[str]:
        path = self.vault / "_study" / "anki" / "manifest.json"
        path.write_text(json.dumps(manifest), encoding="utf-8")
        return subprocess.run(
            [sys.executable, str(SCRIPT), str(path), "--vault", str(self.vault)],
            text=True,
            capture_output=True,
            check=False,
        )

    def test_renders_deterministic_sorted_tsv(self) -> None:
        first = self.run_script(self.manifest())
        second = self.run_script(self.manifest())
        self.assertEqual(first.returncode, 0, first.stderr)
        self.assertEqual(first.stdout, second.stdout)
        self.assertIn("#notetype:Basic", first.stdout)
        self.assertIn("#columns:Front\tBack\tGUID\tTags", first.stdout)
        self.assertIn("#guid column:3", first.stdout)
        self.assertIn("#tags column:4", first.stdout)
        self.assertIn("#tags:study-loop::chapter::chapter-1", first.stdout)
        rows = [line for line in first.stdout.splitlines() if not line.startswith("#")]
        first_fields = rows[0].split("\t")
        second_fields = rows[1].split("\t")
        self.assertEqual(len(first_fields), 4)
        self.assertEqual(first_fields[0], "First<br>prompt")
        self.assertIn("First &amp; answer", first_fields[1])
        self.assertIn("<b>Objective:</b> First objective", first_fields[1])
        self.assertIn("Notes/Chapter 1.md#First", first_fields[1])
        self.assertEqual(first_fields[2], "course.ch1.first.basic")
        self.assertIn("study-loop::status::active", first_fields[3])
        self.assertEqual(second_fields[0], "Second prompt")
        self.assertEqual(second_fields[2], "course.ch1.second.typed")
        self.assertIn("study-loop::typed", second_fields[3])
        self.assertNotEqual(first_fields[0], first_fields[2])

    def test_objective_with_quotes_matches_its_cards(self) -> None:
        data = self.manifest()
        quoted = '"And" vs "or" & more'
        data["objectives"] = [quoted if o == data["cards"][0]["objective"] else o for o in data["objectives"]]
        for card in data["cards"]:
            if card["objective"] == self.manifest()["cards"][0]["objective"]:
                card["objective"] = quoted
        result = self.run_script(data)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_rejects_duplicate_ids(self) -> None:
        manifest = self.manifest()
        manifest["cards"][1]["id"] = manifest["cards"][0]["id"]
        result = self.run_script(manifest)
        self.assertEqual(result.returncode, 1)
        self.assertIn("duplicate card IDs", result.stderr)

    def test_retired_card_is_exported_and_tagged(self) -> None:
        manifest = self.manifest()
        retired = manifest["cards"][1]
        retired["status"] = "retired"
        replacement = dict(retired)
        replacement["id"] = "course.ch1.first-current.basic"
        replacement["status"] = "active"
        manifest["cards"].append(replacement)
        result = self.run_script(manifest)
        self.assertEqual(result.returncode, 0, result.stderr)
        retired_row = next(
            row
            for row in result.stdout.splitlines()
            if "\tcourse.ch1.first.basic\t" in row
        )
        self.assertIn("study-loop::retired", retired_row)

    def test_rejects_unsafe_source(self) -> None:
        manifest = self.manifest()
        manifest["cards"][0]["source"] = "../Private.md#Secrets"
        result = self.run_script(manifest)
        self.assertEqual(result.returncode, 1)
        self.assertIn("stay inside the vault", result.stderr)

    def test_rejects_unknown_card_type(self) -> None:
        manifest = self.manifest()
        manifest["cards"][0]["type"] = "image-occlusion"
        result = self.run_script(manifest)
        self.assertEqual(result.returncode, 1)
        self.assertIn("basic, typed, mcq, or calc", result.stderr)

    def test_rejects_missing_source_heading(self) -> None:
        manifest = self.manifest()
        manifest["cards"][0]["source"] = "Notes/Chapter 1.md#Missing"
        result = self.run_script(manifest)
        self.assertEqual(result.returncode, 1)
        self.assertIn("heading does not exist", result.stderr)

    def test_rejects_heading_found_only_inside_code_fence(self) -> None:
        note = self.vault / "Notes" / "Chapter 1.md"
        note.write_text(
            "# Chapter 1\n\n```markdown\n## Hidden\n```\n\n## First\n\nFirst.\n",
            encoding="utf-8",
        )
        manifest = self.manifest()
        manifest["cards"][0]["source"] = "Notes/Chapter 1.md#Hidden"
        result = self.run_script(manifest)
        self.assertEqual(result.returncode, 1)
        self.assertIn("heading does not exist", result.stderr)

    def test_rejects_ambiguous_source_heading(self) -> None:
        note = self.vault / "Notes" / "Chapter 1.md"
        note.write_text(
            "# Chapter 1\n\n## First\n\nOne.\n\n## First\n\nTwo.\n\n## Second\n\nSecond.\n",
            encoding="utf-8",
        )
        result = self.run_script(self.manifest())
        self.assertEqual(result.returncode, 1)
        self.assertIn("heading is ambiguous", result.stderr)

    def test_rejects_tab_inside_visible_field(self) -> None:
        manifest = self.manifest()
        manifest["cards"][0]["prompt"] = "Broken\tprompt"
        result = self.run_script(manifest)
        self.assertEqual(result.returncode, 1)
        self.assertIn("must not contain tabs", result.stderr)

    def test_rejects_deictic_active_prompt(self) -> None:
        manifest = self.manifest()
        manifest["cards"][0]["prompt"] = "What topics does this chapter cover?"
        result = self.run_script(manifest)
        self.assertEqual(result.returncode, 1)
        self.assertIn("mixed-review quality", result.stderr)
        self.assertIn("section or course context", result.stderr)

    def test_allows_deictic_prompt_on_retired_card(self) -> None:
        manifest = self.manifest()
        retired = manifest["cards"][1]
        retired["status"] = "retired"
        retired["prompt"] = "What topics does this chapter cover?"
        replacement = dict(retired)
        replacement["id"] = "course.ch1.first-current.basic"
        replacement["prompt"] = "Name the first retrieval target."
        replacement["status"] = "active"
        manifest["cards"].append(replacement)
        result = self.run_script(manifest)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_rejects_duplicate_active_answers(self) -> None:
        manifest = self.manifest()
        manifest["cards"][1]["answer"] = manifest["cards"][0]["answer"]
        result = self.run_script(manifest)
        self.assertEqual(result.returncode, 1)
        self.assertIn("duplicate active answer", result.stderr)

    def test_rejects_duplicate_active_prompts(self) -> None:
        manifest = self.manifest()
        manifest["cards"][1]["prompt"] = manifest["cards"][0]["prompt"]
        result = self.run_script(manifest)
        self.assertEqual(result.returncode, 1)
        self.assertIn("duplicate active prompt", result.stderr)

    def test_rejects_numbered_lab_prompt(self) -> None:
        manifest = self.manifest()
        manifest["cards"][0]["prompt"] = "What does Lab 3.2 ask you to hash?"
        result = self.run_script(manifest)
        self.assertEqual(result.returncode, 1)
        self.assertIn("numbered lab or exercise", result.stderr)

    def test_rejects_undeclared_card_objective(self) -> None:
        manifest = self.manifest()
        manifest["cards"][0]["objective"] = "Unknown objective"
        result = self.run_script(manifest)
        self.assertEqual(result.returncode, 1)
        self.assertIn("card objectives are not declared", result.stderr)

    def test_retired_objective_drops_a_topic(self) -> None:
        manifest = self.manifest()
        manifest["cards"][0]["status"] = "retired"
        manifest["objectives"] = ["First objective"]
        manifest["retired_objectives"] = ["Second objective"]
        result = self.run_script(manifest)
        self.assertEqual(result.returncode, 0, result.stderr)
        row = next(r for r in result.stdout.splitlines() if "\tcourse.ch1.second.typed\t" in r)
        self.assertIn("study-loop::retired", row)

    def test_rejects_active_card_on_retired_objective(self) -> None:
        manifest = self.manifest()
        manifest["objectives"] = ["First objective"]
        manifest["retired_objectives"] = ["Second objective"]
        result = self.run_script(manifest)
        self.assertEqual(result.returncode, 1)
        self.assertIn("retired objectives with an active card", result.stderr)

    def test_rejects_objective_both_active_and_retired(self) -> None:
        manifest = self.manifest()
        manifest["retired_objectives"] = ["Second objective"]
        result = self.run_script(manifest)
        self.assertEqual(result.returncode, 1)
        self.assertIn("both active and retired", result.stderr)

    def test_rejects_objective_without_active_card(self) -> None:
        manifest = self.manifest()
        manifest["cards"][0]["status"] = "retired"
        result = self.run_script(manifest)
        self.assertEqual(result.returncode, 1)
        self.assertIn("objectives without an active card", result.stderr)

    def test_rejects_custom_note_type(self) -> None:
        manifest = self.manifest()
        manifest["notetype"] = "Study Loop"
        result = self.run_script(manifest)
        self.assertEqual(result.returncode, 1)
        self.assertIn("notetype must be Basic", result.stderr)

    def test_atomic_output_replaces_existing_file(self) -> None:
        manifest_path = self.vault / "_study" / "anki" / "manifest.json"
        manifest_path.write_text(json.dumps(self.manifest()), encoding="utf-8")
        output = self.vault / "_study" / "anki" / "chapter.tsv"
        output.write_text("old\n", encoding="utf-8")
        result = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                str(manifest_path),
                "--vault",
                str(self.vault),
                "--output",
                str(output),
            ],
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(output.read_text(encoding="utf-8").startswith("#separator:tab"))


if __name__ == "__main__":
    unittest.main()


class McqTests(BuildAnkiImportTests):
    def mcq_manifest(self, **change: object) -> dict[str, object]:
        manifest = self.manifest()
        card = {
            "id": "course.ch1.first.router.mcq",
            "objective": "First objective",
            "type": "mcq",
            "prompt": "Traffic must be forwarded between your LAN and the Internet. Which device does that?",
            "answer": "A router forwards packets between networks.",
            "choices": ["A router", "A modem", "A switch", "A DNS server"],
            "source": "Notes/Chapter 1.md#First",
            "revision": 1,
            "status": "active",
            "tags": ["course"],
        }
        card.update(change)
        manifest["cards"].append(card)
        return manifest

    def test_mcq_goes_to_quiz_output_with_correct_letter(self) -> None:
        out = self.vault / "_study" / "anki" / "chapter-1.tsv"
        path = self.vault / "_study" / "anki" / "manifest.json"
        path.write_text(json.dumps(self.mcq_manifest()), encoding="utf-8")
        result = subprocess.run([sys.executable, str(SCRIPT), str(path), "--vault", str(self.vault), "--output", str(out)],
                                text=True, capture_output=True, check=False)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertNotIn("A modem", out.read_text(encoding="utf-8"))
        quiz = (self.vault / "_study" / "anki" / "chapter-1-quiz.tsv").read_text(encoding="utf-8")
        self.assertIn("#deck:Course::Chapter 1::Quiz", quiz)  # mixed deck: quiz in a subdeck
        self.assertIn("#notetype:Study MCQ", quiz)
        row = quiz.strip().splitlines()[-1].split("\t")
        options, letter = row[1:5], row[5]
        self.assertEqual(options["ABCD".index(letter)], "A router")
        self.assertEqual(sorted(options), sorted(["A router", "A modem", "A switch", "A DNS server"]))

    def test_mcq_needs_four_choices(self) -> None:
        result = self.run_script(self.mcq_manifest(choices=["A router", "A modem", "A switch"]))
        self.assertEqual(result.returncode, 1)
        self.assertIn("exactly 4 options", result.stderr)

    def test_mcq_rejects_all_of_the_above(self) -> None:
        result = self.run_script(self.mcq_manifest(choices=["A router", "A modem", "A switch", "All of the above"]))
        self.assertEqual(result.returncode, 1)
        self.assertIn("all/none/both", result.stderr)

    def test_mcq_rejects_question_that_names_the_answer(self) -> None:
        result = self.run_script(self.mcq_manifest(prompt="Which device, a router or a modem, forwards packets?"))
        self.assertEqual(result.returncode, 1)
        self.assertIn("gives away the correct option", result.stderr)

    def test_quiz_only_deck_is_the_chapter_deck(self) -> None:
        manifest = self.mcq_manifest()
        manifest["cards"] = [c for c in manifest["cards"] if c["type"] == "mcq"]
        manifest["objectives"] = ["First objective"]
        out = self.vault / "_study" / "anki" / "chapter-1.tsv"
        path = self.vault / "_study" / "anki" / "manifest.json"
        path.write_text(json.dumps(manifest), encoding="utf-8")
        result = subprocess.run([sys.executable, str(SCRIPT), str(path), "--vault", str(self.vault), "--output", str(out)],
                                text=True, capture_output=True, check=False)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse(out.exists())
        quiz = (self.vault / "_study" / "anki" / "chapter-1-quiz.tsv").read_text(encoding="utf-8")
        self.assertIn("#deck:Course::Chapter 1\n", quiz)



class CalcTests(BuildAnkiImportTests):
    def calc_manifest(self, **change: object) -> dict[str, object]:
        manifest = self.manifest()
        card = {
            "id": "course.ch1.first.exact.calc",
            "objective": "First objective",
            "type": "calc",
            "kind": "binom-exact",
            "params": {"n": [5, 9], "p": [0.6, 0.7]},
            "prompt": "Seeds germinate with probability {p}. You plant {n}. What is the probability that exactly {r} germinate?",
            "answer": "Exactly r successes: P(r) = C(n,r) p^r q^(n-r).",
            "source": "Notes/Chapter 1.md#First",
            "revision": 1,
            "status": "active",
            "tags": ["course"],
        }
        card.update(change)
        manifest["cards"].append(card)
        return manifest

    def build(self, manifest: dict[str, object]) -> subprocess.CompletedProcess[str]:
        path = self.vault / "_study" / "anki" / "manifest.json"
        path.write_text(json.dumps(manifest), encoding="utf-8")
        out = self.vault / "_study" / "anki" / "chapter-1.tsv"
        return subprocess.run([sys.executable, str(SCRIPT), str(path), "--vault", str(self.vault), "--output", str(out)],
                              text=True, capture_output=True, check=False)

    def test_calc_goes_to_calc_output(self) -> None:
        result = self.build(self.calc_manifest())
        self.assertEqual(result.returncode, 0, result.stderr)
        calc = (self.vault / "_study" / "anki" / "chapter-1-calc.tsv").read_text(encoding="utf-8")
        self.assertIn("#deck:Course::Chapter 1::Quiz", calc)
        self.assertIn("#notetype:Study Calc", calc)
        row = calc.strip().splitlines()[-1].split("\t")
        self.assertEqual(row[1], "binom-exact")
        self.assertEqual(json.loads(html.unescape(row[2])), {"n": [5, 9], "p": [0.6, 0.7]})
        self.assertEqual(row[5], "course.ch1.first.exact.calc")
        self.assertNotIn("germinate", (self.vault / "_study" / "anki" / "chapter-1.tsv").read_text(encoding="utf-8"))

    def test_rejects_unknown_kind_and_missing_placeholder(self) -> None:
        self.assertIn("kind must be one of", self.build(self.calc_manifest(kind="normal-z")).stderr)
        missing_r = self.calc_manifest(prompt="Seeds germinate with probability {p}. You plant {n}. Find P(4).")
        self.assertIn("must show {r}", self.build(missing_r).stderr)
        typo = self.calc_manifest(prompt="Probability {p}, {n} seeds, exactly {r}, {k} more.")
        self.assertIn("unknown placeholders: k", self.build(typo).stderr)

    def test_rejects_r_range_outside_n(self) -> None:
        bad = self.calc_manifest(params={"n": [3, 9], "p": [0.5], "r": [4, -1]})
        self.assertIn("out-of-range r for n = 3", self.build(bad).stderr)

    def test_order_needs_labels(self) -> None:
        card = {"kind": "binom-order", "params": {"n": [3, 4], "p": [0.25]},
                "prompt": "You guess with {inv} choices each. Probability of {seq}?"}
        self.assertIn("labels must name", self.build(self.calc_manifest(**card)).stderr)


class CalcScriptTests(unittest.TestCase):
    """The card's own solver (assets/study-calc/calc.js), run under node when it is installed."""

    def run_node(self, code: str) -> str:
        node = shutil.which("node")
        if node is None:
            self.skipTest("node is not installed")
        js = Path(__file__).resolve().parents[1] / "assets" / "study-calc" / "calc.js"
        result = subprocess.run([node, "-e", f"const m = require({json.dumps(str(js))});\n{code}"],
                                text=True, capture_output=True, check=True)
        return result.stdout.strip()

    def test_kinds_match_the_builder(self) -> None:
        sys.path.insert(0, str(SCRIPT.parent))
        from build_anki_import import CALC_KINDS
        kinds = json.loads(self.run_node("console.log(JSON.stringify(Object.keys(m.KINDS)))"))
        self.assertEqual(sorted(kinds), sorted(CALC_KINDS))
        how = json.loads(self.run_node("console.log(JSON.stringify(Object.keys(m.HOW)))"))
        self.assertEqual(sorted(how), sorted(CALC_KINDS))  # every kind explains its formula

    def test_matches_worked_examples(self) -> None:
        out = json.loads(self.run_node("""
const v = (n, p, r, x) => Object.assign({n, p, q: m.qOf(p), r, labels: ["right", "wrong"]}, x || {});
console.log(JSON.stringify([
  m.KINDS["binom-exact"].solve(v(10, 0.59, 6)).answer,
  m.KINDS["binom-atmost"].solve(v(6, 0.5, 4)).answer,
  m.KINDS["binom-atleast"].solve(v(6, 0.7, 2)).answer,
  m.KINDS["binom-sd"].solve(v(6, 0.7)).answer,
  m.KINDS["binom-mean"].solve(v(6, 0.7)).answer,
  m.KINDS["binom-order"].solve(v(3, 0.25, null, {k: 2, seq: "right, right, wrong"})).answer,
  m.KINDS["binom-count"].solve(v(10, 0.5, 6)).answer,
  m.KINDS["binom-atleast1"].solve(v(4, 0.1)).answer]));"""))
        expected = [0.2503, 0.8906, 0.9891, 1.1225, 4.2, 0.046875, 210, 0.3439]
        for got, want in zip(out, expected):
            self.assertAlmostEqual(got, want, places=4)
