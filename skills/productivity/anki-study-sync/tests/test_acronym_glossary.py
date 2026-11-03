from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from acronym_glossary import build_glossary, expand_answer, terms_line  # noqa: E402

GLOSSARY = {
    "NTLM": "New Technology LAN Manager",
    "LDAP": "Lightweight Directory Access Protocol",
    "LSASS": "Local Security Authority Subsystem Service",
    "UAC": "User Account Control",
    "UTM": "Unified Threat Management",
    "BEC": "Business Email Compromise",
}


class TermsLineTests(unittest.TestCase):
    def test_option_acronyms_get_a_terms_line(self):
        line = terms_line(
            "A Windows client signs in to an Active Directory domain. Which statement about the protocols is correct?",
            ["Kerberos is preferred; NTLM is kept for legacy use.", "LDAP is preferred; Kerberos is kept for legacy use.",
             "NTLM is preferred; LDAP is kept for legacy use.", "NTLM is preferred; Kerberos is kept for legacy use."],
            GLOSSARY)
        self.assertIn("New Technology LAN Manager", line)
        self.assertIn("Lightweight Directory Access Protocol", line)

    def test_acronym_question_never_gets_the_expansion(self):
        self.assertEqual(terms_line("What does UAC stand for?",
                                    ["User Account Control", "User Access Control", "A", "B"], GLOSSARY), "")

    def test_correct_option_hint_suppresses_option_terms(self):
        self.assertEqual(terms_line("Which appliance unifies firewall, filtering, and threat tools in one box?",
                                    ["A UTM", "A proxy", "A jump server", "An LDAP server"], GLOSSARY), "")

    def test_full_name_already_on_card_is_not_repeated(self):
        self.assertEqual(terms_line("Why does a business email compromise avoid malware?",
                                    ["BEC is targeted", "x", "y", "z"], GLOSSARY), "")


class ExplanationTests(unittest.TestCase):
    def test_explanation_only_acronym_is_spelled_out_once(self):
        out = expand_answer("LSASS passes credentials; LSASS prefers Kerberos.", "Which protocol?", GLOSSARY)
        self.assertEqual(out.count("Local Security Authority Subsystem Service"), 1)
        self.assertTrue(out.startswith("LSASS (Local Security Authority Subsystem Service) passes"))

    def test_acronym_already_on_front_is_not_repeated(self):
        out = expand_answer("NTLM remains for legacy systems.", "Which statement about NTLM is correct?", GLOSSARY)
        self.assertEqual(out, "NTLM remains for legacy systems.")


class GlossaryTests(unittest.TestCase):
    def test_sources_common_and_ambiguous(self):
        with tempfile.TemporaryDirectory() as tmp:
            kit = Path(tmp, "Chapter-Kits", "Chapter-01", "1.1")
            kit.mkdir(parents=True)
            Path(tmp, "Chapter-Kits", "acronyms.md").write_text(
                "| Acronym | Spelled out | Where |\n| --- | --- | --- |\n| LDAP | Lightweight Directory Access Protocol | 4.2 |\n")
            (kit / "X-Study-Notes.md").write_text(
                "**Abbreviations**\n\n| Short form | Stands for | Meaning |\n| --- | --- | --- |\n"
                "| USB | universal serial bus | ports |\n| MAC | media access control | address |\n\n"
                "> - **LSASS**: Local Security Authority Subsystem Service; checks credentials\n"
                "> - **MAC**: Mandatory Access Control; a model\n")
            g = build_glossary(Path(tmp))
        self.assertEqual(g["LDAP"], "Lightweight Directory Access Protocol")
        self.assertEqual(g["LSASS"], "Local Security Authority Subsystem Service")
        self.assertNotIn("USB", g)
        self.assertNotIn("MAC", g)


if __name__ == "__main__":
    unittest.main()


class CapTests(unittest.TestCase):
    def test_option_terms_dropped_together_when_over_cap(self):
        g = {"AAA": "Authentication, Authorization, and Accounting", "TACACS+": "Terminal Access Controller Access Control System",
             "RADIUS": "Remote Authentication Dial-in User Service", "EAP": "Extensible Authentication Protocol",
             "PAP": "Password Authentication Protocol"}
        line = terms_line("An audit finds an AAA protocol that encrypts the whole body. Which protocol?",
                          ["TACACS+", "RADIUS", "EAP", "PAP"], g)
        self.assertIn("AAA", line)
        for t in ("TACACS+", "RADIUS", "EAP", "PAP"):
            self.assertNotIn(t, line)


class InlineDefinitionTests(unittest.TestCase):
    def test_inline_full_name_with_matching_initials(self):
        from acronym_glossary import _inline
        self.assertEqual(_inline("Tukey called it exploratory data analysis (EDA) in 1977."),
                         [("EDA", "exploratory data analysis")])
        self.assertEqual(_inline("the National Institute of Standards and Technology (NIST) runs it"),
                         [("NIST", "National Institute of Standards and Technology")])

    def test_unrelated_parentheses_are_ignored(self):
        from acronym_glossary import _inline
        self.assertEqual(_inline("see the chart (Fig 2) and the rule (TEST MOVE)"), [])


class BasicCardTests(unittest.TestCase):
    G = {"CMC": "computer-mediated communication", "FTF": "face-to-face communication"}

    def test_basic_front_gets_terms_line_without_options(self):
        line = terms_line("What two approaches compare CMC with face-to-face (FTF) communication?", [], self.G)
        self.assertIn("computer-mediated communication", line)
        self.assertNotIn("FTF", line)  # its words are already on the card

    def test_basic_back_spells_out_explanation_only_acronym(self):
        out = expand_answer("The media deficit approach: CMC lacks nonverbal cues.", "What is filtered communication?", self.G)
        self.assertIn("CMC (computer-mediated communication)", out)


class AlreadySaidTests(unittest.TestCase):
    def test_option_list_of_parts_is_a_giveaway(self):
        g = {"AAA": "Authentication, Authorization, and Accounting"}
        self.assertEqual(terms_line("A user enters a password. Which AAA step is happening?",
                                    ["Authentication", "Authorization", "Accounting", "Identification"], g), "")

    def test_scattered_words_do_not_count_as_said(self):
        g = {"EFS": "Encrypted File System"}
        line = terms_line("An operating system mounts an encrypted disk. Which design explains it?",
                          ["A self-encrypting drive", "OS full-disk encryption", "Volume encryption software", "EFS file encryption"], g)
        self.assertIn("Encrypted File System", line)
