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


class OverlapTests(unittest.TestCase):
    def card(self, cid, prompt, answer, tags=None):
        return {"id": cid, "prompt": prompt, "answer": answer, "status": "active", "tags": tags or []}

    def test_same_term_across_decks(self):
        from anki_quality import overlap_warnings
        w = overlap_warnings({
            "ch04.json": [self.card("a", "What is fair use?", "Limited use without permission.")],
            "ch05.json": [self.card("b", "What is the fair use?", "Use of copyrighted work for review.")],
        })
        self.assertEqual(len(w), 1)
        self.assertIn("both define 'fair use'", w[0])

    def test_acronym_card_redundant_with_concept_card(self):
        from anki_quality import overlap_warnings
        w = overlap_warnings({"ch03.json": [
            self.card("a", "What does DNS stand for?", "Domain Name System."),
            self.card("b", "How does DNS find a server?", "It resolves a name to an IP address."),
        ]})
        self.assertTrue(any("DNS expansion card" in x for x in w))

    def test_contrast_pair_tagged_ok_is_silent(self):
        from anki_quality import overlap_warnings
        w = overlap_warnings({"ch04.json": [
            self.card("a", "What does the GET HTTP method do?", "Requests data from a source.", ["overlap-ok"]),
            self.card("b", "What does the GET HTTP method do in a form?", "Requests data from a source.", ["overlap-ok"]),
        ]})
        self.assertEqual(w, [])

    def test_distinct_cards_pass(self):
        from anki_quality import overlap_warnings
        w = overlap_warnings({"ch03.json": [
            self.card("a", "What is latency?", "Delay: how long data takes to travel."),
            self.card("b", "What is jitter?", "Variation in packet delay."),
        ]})
        self.assertEqual(w, [])


class SourceTagTests(unittest.TestCase):
    def test_source_tagged_front_is_an_error(self):
        from anki_quality import quality_errors
        cards = [{"id": "a", "prompt": "What five file-naming conventions does IT-100 Module 6 list?", "answer": "x", "status": "active"},
                 {"id": "b", "prompt": "In the lecture's model, what does ROM contain?", "answer": "y", "status": "active"},
                 {"id": "c", "prompt": "What does ROM contain?", "answer": "z", "status": "active"}]
        errors = quality_errors(cards)
        self.assertTrue(any(e.startswith("a:") for e in errors))
        self.assertTrue(any(e.startswith("b:") for e in errors))
        self.assertFalse(any(e.startswith("c:") for e in errors))
