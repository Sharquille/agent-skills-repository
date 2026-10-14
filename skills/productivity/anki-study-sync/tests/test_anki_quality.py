from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from anki_quality import leak_warnings, leaked_term  # noqa: E402


class LeakTests(unittest.TestCase):
    def test_flags_answer_term_on_the_front(self) -> None:
        self.assertEqual(leaked_term("Which certificate field names the CA that issued it?", "Issuer."), "Issuer")
        self.assertEqual(leaked_term("Which function of language is used to regulate behavior?", "Regulatory."), "Regulatory")

    def test_choice_and_multi_part_fronts_are_skipped(self) -> None:
        self.assertIsNone(leaked_term("Tire pressure: discrete or continuous?", "Continuous."))
        self.assertIsNone(leaked_term("How does a static character differ from a dynamic one?", "Static: unchanged."))
        self.assertIsNone(leaked_term("Which property does hashing give, and which does encryption?", "Hashing gives integrity."))

    def test_formula_and_short_keys_are_skipped(self) -> None:
        self.assertIsNone(leaked_term("What is the formula for class width?", "Class width = range / classes."))
        self.assertIsNone(leaked_term("Which port does LDAP use?", "Port 389."))

    def test_clean_front_passes(self) -> None:
        self.assertIsNone(leaked_term("Which function of language directs other people's behavior?", "Regulatory."))

    def test_leak_ok_tag_and_retired_cards_are_silent(self) -> None:
        card = {"id": "c1", "status": "active", "prompt": "Which field names the CA that issued it?",
                "answer": "Issuer.", "tags": []}
        self.assertEqual(len(leak_warnings([card])), 1)
        self.assertEqual(leak_warnings([dict(card, tags=["leak-ok"])]), [])
        self.assertEqual(leak_warnings([dict(card, status="retired")]), [])


if __name__ == "__main__":
    unittest.main()
