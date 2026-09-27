import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import eli5  # noqa: E402

CSP = "default-src 'none'; style-src 'unsafe-inline'; script-src 'unsafe-inline'; img-src data:"


def page(body, csp=CSP, css="body{background:#fff}", head_extra=""):
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta http-equiv="Content-Security-Policy" content="{csp}">
<title>Nonverbal Codes</title>
<style>{css}</style>{head_extra}
</head>
<body>{body}</body>
</html>"""


GOOD_BODY = """
<section data-step="1"><h2>One</h2>
<svg role="img" aria-label="A face"><title>ignored</title><text>smile</text></svg></section>
<section data-step="2"><h2>Two</h2>
<svg role="img"><title>A hand</title></svg>
<svg aria-hidden="true"></svg></section>
<script>let x = 1;</script>
"""


class CheckTest(unittest.TestCase):
    def errors(self, text, **kw):
        return eli5.check(text, **kw)[0]

    def test_good_page_passes_and_counts_visible_words_only(self):
        errors, p = eli5.check(page(GOOD_BODY))
        self.assertEqual(errors, [])
        # "One", "smile", "Two"; script, style, and titles are not visible words.
        self.assertEqual(p.words, 3)
        self.assertEqual(len(p.svgs), 3)

    def test_missing_csp_and_external_sources_fail(self):
        errs = self.errors(page(GOOD_BODY, csp="default-src *"))
        self.assertTrue(any("default-src 'none'" in e for e in errs))
        self.assertTrue(any("wildcard" in e for e in errs))
        errs = self.errors(page(GOOD_BODY + '<img src="https://x.test/a.png">'))
        self.assertTrue(any("external resource" in e for e in errs))
        errs = self.errors(page(GOOD_BODY, css="@import url(//x.test/a.css);"))
        self.assertTrue(any("@import" in e for e in errs))
        self.assertTrue(any("url()" in e for e in errs))

    def test_anchor_links_and_data_uris_are_allowed(self):
        body = GOOD_BODY + '<a href="#step-2">next</a><img src="data:image/png;base64,AA==" alt="">'
        self.assertEqual(self.errors(page(body)), [])

    def test_svg_without_accessible_name_fails(self):
        body = GOOD_BODY.replace('aria-label="A face"', "")
        body = body.replace("<title>ignored</title>", "")
        errs = self.errors(page(body))
        self.assertTrue(any("accessible name" in e for e in errs))

    def test_nested_svg_title_does_not_name_outer_svg(self):
        body = GOOD_BODY.replace('aria-label="A face"><title>ignored</title>',
                                 '><g><svg><title>inner</title></svg></g>')
        errs = self.errors(page(body))
        self.assertTrue(any("accessible name" in e for e in errs))

    def test_steps_must_run_in_order(self):
        errs = self.errors(page(GOOD_BODY.replace('data-step="2"', 'data-step="3"')))
        self.assertTrue(any("1..N" in e for e in errs))
        errs = self.errors(page(GOOD_BODY.replace('data-step="2"', 'data-step="two"')))
        self.assertTrue(any("not a number" in e for e in errs))

    def test_word_budget(self):
        errs = self.errors(page(GOOD_BODY), max_words=2)
        self.assertTrue(any("exceeds the budget of 2" in e for e in errs))

    def test_animation_needs_reduced_motion(self):
        errs = self.errors(page(GOOD_BODY, css=".a{transition: opacity .2s}"))
        self.assertTrue(any("prefers-reduced-motion" in e for e in errs))
        css = ".a{transition: opacity .2s}@media (prefers-reduced-motion: reduce){.a{transition:none}}"
        self.assertEqual(self.errors(page(GOOD_BODY, css=css)), [])

    def test_document_basics(self):
        text = page(GOOD_BODY).replace("<!doctype html>", "").replace(' lang="en"', "")
        errs = self.errors(text)
        self.assertIn("missing <!doctype html> at the top", errs)
        self.assertIn("<html> needs a lang attribute", errs)


class ArtifactTest(unittest.TestCase):
    def test_keeps_title_styles_body_and_drops_wrapper_and_csp(self):
        out = eli5.to_artifact(page(GOOD_BODY))
        self.assertTrue(out.startswith("<title>Nonverbal Codes</title>"))
        self.assertIn("<style>body{background:#fff}</style>", out)
        self.assertIn('data-step="2"', out)
        self.assertIn("<script>let x = 1;</script>", out)
        for gone in ("<!doctype", "<html", "<head", "<body", "Content-Security-Policy"):
            self.assertNotIn(gone.lower(), out.lower())

    def test_missing_body_raises(self):
        with self.assertRaises(ValueError):
            eli5.to_artifact("<html><head><title>x</title></head></html>")


if __name__ == "__main__":
    unittest.main()
