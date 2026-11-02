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


class OfficialAcronymTests(unittest.TestCase):
    def test_official_acronym_card_allowed_but_double_definition_flagged(self):
        from anki_quality import official_acronyms, overlap_warnings
        official = official_acronyms("| Acronym | Spelled out |\n| --- | --- |\n| ARP | Address Resolution Protocol |\n")
        self.assertEqual(official, frozenset({"ARP"}))
        c = lambda i, p, a: {"id": i, "prompt": p, "answer": a, "status": "active", "tags": []}
        decks = {"ch05.json": [c("a", "What does ARP stand for?", "Address Resolution Protocol."),
                               c("b", "How does ARP poisoning work?", "It spoofs MAC-to-IP replies.")]}
        self.assertEqual(overlap_warnings(decks, official), [])
        self.assertTrue(overlap_warnings(decks))
        decks["ch06.json"] = [c("d", "What does ARP stand for?", "Address resolution protocol, for mapping IPs.")]
        self.assertTrue(any("both define 'arp'" in w for w in overlap_warnings(decks, official)))


class ExplanationNoiseTests(unittest.TestCase):
    def _card(self, answer, **extra):
        return dict({"id": "c1", "status": "active", "prompt": "Which property failed?",
                     "answer": answer, "tags": []}, **extra)

    def test_wins_formula_is_an_error(self):
        from anki_quality import quality_errors
        errors = quality_errors([self._card("Integrity wins because data must stay as intended.")])
        self.assertTrue(any("wins because" in e for e in errors))

    def test_precedence_wins_is_allowed(self):
        from anki_quality import quality_errors
        self.assertEqual(quality_errors([self._card(
            "The last applied GPO wins, and the OU is closer than the domain, so 5 minutes applies.")]), [])

    def test_distractor_commentary_tail_is_an_error(self):
        from anki_quality import quality_errors
        errors = quality_errors([self._card(
            "User Account Control is the expansion, while the near misses swap Account for Access.")])
        self.assertTrue(any("other options" in e for e in errors))

    def test_contrast_with_one_named_option_passes(self):
        from anki_quality import quality_errors
        self.assertEqual(quality_errors([self._card(
            "A logic bomb waits for an event, while a time bomb waits for a date.")]), [])


class ReworderRepeatTests(unittest.TestCase):
    def test_same_answer_and_options_flagged_across_decks(self):
        from anki_quality import overlap_warnings
        opts = ["Confidentiality", "Integrity", "Availability", "Non-repudiation"]
        w = overlap_warnings({
            "ch01.json": [{"id": "a", "status": "active", "prompt": "An employee reads a salary file without permission. Which goal was harmed?",
                           "answer": "Confidentiality: only authorized people read data.", "choices": opts, "tags": []}],
            "ch04.json": [{"id": "b", "status": "active", "prompt": "Someone unauthorized opens a protected record. Which property failed?",
                           "answer": "Confidentiality: unauthorized reading breaks it.", "choices": opts, "tags": []}],
        })
        self.assertTrue(any("same correct option" in x for x in w))

    def test_same_options_different_answer_is_not_a_repeat(self):
        from anki_quality import overlap_warnings
        a = ["Site-to-site", "Client-to-site", "Host-to-host", "Clientless gateway"]
        b = ["Client-to-site", "Site-to-site", "Host-to-host", "Clientless gateway"]
        w = overlap_warnings({"ch04.json": [
            {"id": "a", "status": "active", "prompt": "Two branch routers build a tunnel. Which topology?", "answer": "Site-to-site.", "choices": a, "tags": []},
            {"id": "b", "status": "active", "prompt": "A hotel laptop runs a VPN app. Which topology?", "answer": "Client-to-site.", "choices": b, "tags": []}]})
        self.assertFalse(any("same correct option" in x for x in w))
