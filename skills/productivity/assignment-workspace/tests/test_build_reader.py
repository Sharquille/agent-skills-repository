import importlib.util
import unittest
from pathlib import Path

spec = importlib.util.spec_from_file_location(
    "build_reader", Path(__file__).resolve().parents[1] / "scripts" / "build_reader.py")
assert spec is not None and spec.loader is not None
br = importlib.util.module_from_spec(spec)
spec.loader.exec_module(br)


def sample():
    return {
        "title": "Test Reader",
        "sources": [{
            "key": "A", "label": "Author · Title", "short": "Author", "cite_author": "Author",
            "source_line": "Author, Title. pp. 1–2.", "pdf": "../Materials/x.pdf",
            "blocks": [
                {"id": "a1", "label": "¶1", "page": 1, "pdf_page": 1, "text": "The quick brown fox."},
                {"id": "a2", "label": "¶2", "page": 2, "pdf_page": 2, "text": "Jumps over </script> the dog."},
            ],
        }],
        "questions": {"q1": {"source": "A", "title": "Q1", "tip": "Look.", "blocks": ["a1"], "phrases": ["brown fox"]}},
    }


class BuildReaderTests(unittest.TestCase):
    def test_valid_spec_builds(self):
        html = br.build(sample())
        self.assertIn("<title>Test Reader</title>", html)
        self.assertIn("brown fox", html)

    def test_script_close_tag_is_escaped(self):
        html = br.build(sample())
        self.assertNotIn("Jumps over </script>", html)

    def test_apa_cite_format_and_page_word(self):
        s = sample()
        s["sources"][0]["cite_format"] = "(Author, 2023, slide {page})"
        s["sources"][0]["page_word"] = "Slide"
        html = br.build(s)
        self.assertIn("(Author, 2023, slide {page})", html)
        self.assertIn('src.page_word||"Page"', html)

    def test_missing_phrase_fails(self):
        s = sample()
        s["questions"]["q1"]["phrases"] = ["red fox"]
        with self.assertRaises(ValueError):
            br.build(s)

    def test_phrase_outside_spotlight_blocks_fails(self):
        s = sample()
        s["questions"]["q1"]["phrases"] = ["the dog"]
        with self.assertRaises(ValueError):
            br.build(s)

    def test_unknown_block_fails(self):
        s = sample()
        s["questions"]["q1"]["blocks"] = ["zz"]
        self.assertTrue(br.validate(s))

    def test_duplicate_block_id_fails(self):
        s = sample()
        s["sources"][0]["blocks"][1]["id"] = "a1"
        self.assertTrue(br.validate(s))


if __name__ == "__main__":
    unittest.main()
