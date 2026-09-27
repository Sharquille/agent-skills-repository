#!/usr/bin/env python3
"""Check an ELI5 explainer page, or convert it to an Artifact fragment.

  eli5.py check FILE [--max-words N]
  eli5.py artifact FILE > fragment.html

Standard library only.
"""
import argparse
import re
import sys
from html.parser import HTMLParser

DEFAULT_MAX_WORDS = 900
# Text inside these never reaches the reader as visible words.
HIDDEN_TEXT = {"script", "style", "title", "desc", "head", "noscript"}
EXTERNAL = re.compile(r"^\s*(https?:)?//", re.I)


class Page(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack = []
        self.words = 0
        self.title = ""
        self.lang = None
        self.meta_charset = False
        self.meta_viewport = False
        self.csp = None
        self.steps = []
        self.external = []
        self.svgs = []  # (line, has_name) for each outermost <svg>
        self.css = []

    def handle_starttag(self, tag, attrs):
        a = {k: (v or "") for k, v in attrs}
        line = self.getpos()[0]
        if tag == "html":
            self.lang = a.get("lang", "").strip() or None
        elif tag == "meta":
            if "charset" in a:
                self.meta_charset = True
            if a.get("name", "").lower() == "viewport":
                self.meta_viewport = True
            if a.get("http-equiv", "").lower() == "content-security-policy":
                self.csp = a.get("content", "")
        for key in ("src", "href", "action", "poster", "data"):
            if key in a and EXTERNAL.match(a[key]):
                self.external.append(f"line {line}: <{tag} {key}={a[key]!r}>")
        if "data-step" in a:
            self.steps.append((line, a["data-step"]))
        if tag == "svg" and "svg" not in self.stack:
            named = bool(a.get("aria-label", "").strip() or a.get("aria-labelledby", "").strip())
            decorative = a.get("aria-hidden", "").lower() == "true"
            self.svgs.append([line, a.get("role") == "img", named, decorative])
        elif tag == "title" and self.stack and self.stack[-1] == "svg" and self.stack.count("svg") == 1:
            self.svgs[-1][2] = True
        if tag not in {"meta", "link", "br", "img", "input", "hr", "source", "col", "wbr", "area", "base"}:
            self.stack.append(tag)

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if self.stack and self.stack[-1] == tag:
            self.stack.pop()

    def handle_endtag(self, tag):
        if tag in self.stack:
            while self.stack:
                if self.stack.pop() == tag:
                    break

    def handle_data(self, data):
        if not self.stack:
            return
        top = self.stack[-1]
        if top == "title" and "svg" not in self.stack:
            self.title += data
        if top == "style":
            self.css.append(data)
        if not HIDDEN_TEXT.intersection(self.stack):
            self.words += len(re.findall(r"[A-Za-z0-9][\w'’-]*", data))


def check(text, max_words=DEFAULT_MAX_WORDS):
    """Return (errors, page) for an ELI5 page's source text."""
    errors = []
    if not re.match(r"\s*<!doctype html>", text, re.I):
        errors.append("missing <!doctype html> at the top")
    page = Page()
    page.feed(text)
    page.close()

    if not page.lang:
        errors.append("<html> needs a lang attribute")
    if not page.meta_charset:
        errors.append("missing <meta charset>")
    if not page.meta_viewport:
        errors.append("missing viewport <meta>")
    if not page.title.strip():
        errors.append("missing or empty <title>")

    if page.csp is None:
        errors.append("missing Content-Security-Policy <meta>")
    else:
        if not re.match(r"\s*default-src\s+'none'", page.csp):
            errors.append("CSP must start with default-src 'none'")
        if re.search(r"(https?:|//|\*)", page.csp):
            errors.append("CSP allows an external or wildcard source")

    errors.extend(f"external resource {e}" for e in page.external)
    css = "\n".join(page.css)
    if re.search(r"@import", css):
        errors.append("CSS uses @import")
    if re.search(r"url\(\s*['\"]?\s*(https?:)?//", css, re.I):
        errors.append("CSS url() points outside the file")
    if re.search(r"\b(animation|transition)\s*:", css) and "prefers-reduced-motion" not in css:
        errors.append("CSS animates but never checks prefers-reduced-motion")

    for line, role_img, named, decorative in page.svgs:
        if decorative:
            continue
        if not (role_img and named):
            errors.append(f"line {line}: <svg> needs role=\"img\" and an accessible name, or aria-hidden=\"true\"")

    numbers = []
    for line, value in page.steps:
        if not value.isdigit():
            errors.append(f"line {line}: data-step={value!r} is not a number")
        else:
            numbers.append(int(value))
    if len(page.steps) < 2:
        errors.append("need at least two data-step elements")
    elif numbers != list(range(1, len(numbers) + 1)):
        errors.append(f"data-step values must run 1..N in order, found {numbers}")

    if page.words > max_words:
        errors.append(f"{page.words} visible words exceeds the budget of {max_words}")
    return errors, page


def to_artifact(text):
    """Drop the document wrapper and CSP meta; keep title, styles, body, scripts."""
    flags = re.I | re.S
    head = re.search(r"<head[^>]*>(.*?)</head>", text, flags)
    body = re.search(r"<body[^>]*>(.*)</body>", text, flags)
    title = re.search(r"<title>.*?</title>", head.group(1), flags) if head else None
    if head is None or title is None or body is None:
        raise ValueError("page needs a <head> <title> and a <body> to convert")
    # Styles in <head> move up front; styles and scripts in <body> travel with it.
    styles = re.findall(r"<style[^>]*>.*?</style>", head.group(1), flags)
    return "\n".join([title.group(0), *styles, body.group(1).strip()]) + "\n"


def main(argv=None):
    parser = argparse.ArgumentParser(description="Check an ELI5 explainer page, or convert it to an Artifact fragment.")
    sub = parser.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("check", help="validate a portable ELI5 page")
    c.add_argument("file")
    c.add_argument("--max-words", type=int, default=DEFAULT_MAX_WORDS)
    a = sub.add_parser("artifact", help="print an Artifact fragment of the page")
    a.add_argument("file")
    args = parser.parse_args(argv)

    with open(args.file, encoding="utf-8") as fh:
        text = fh.read()
    if args.cmd == "artifact":
        try:
            sys.stdout.write(to_artifact(text))
        except ValueError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 1
        return 0

    errors, page = check(text, args.max_words)
    for e in errors:
        print(f"FAIL {e}")
    if errors:
        return 1
    print(f"OK {len(page.steps)} steps, {len(page.svgs)} inline SVGs, "
          f"{page.words}/{args.max_words} visible words")
    return 0


if __name__ == "__main__":
    sys.exit(main())
