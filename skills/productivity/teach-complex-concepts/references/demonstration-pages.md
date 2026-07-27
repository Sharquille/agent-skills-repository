# Demonstration pages

Read this when a concept has an observable result and the learner would be
better served by looking at it than by reading a description of it.

A demonstration page is generated during a lesson, served from the preview
directory, and thrown away with the session. It is not a deliverable and not a
study note.

## When it is worth building one

Build one when **all** of these hold:

- the concept produces something observable — an encrypted file, a diff, a
  timing curve, a capture, a failing test, a race;
- the real tool is available, so the output can be genuine rather than staged;
- the learner has stalled on a described version, or has said they cannot
  picture it.

Do not build one to decorate an explanation that already landed. A page costs a
minute of the learner's attention before it teaches anything.

## The seven rules that make one work

1. **Use the real tool.** `openssl` for a cipher, the actual compiler for the
   error, a real capture for packets. A result the learner could reproduce is
   evidence. A described result is a claim. A fabricated result is a falsehood
   that renders convincingly, and is never acceptable.

2. **Compute the numbers, never assert them.** Count the blocks, diff the
   bytes, measure the sizes in code and print what came back. If a number in
   the page was typed by hand, it is decoration.

3. **Make equality visible.** Colour by *identity*: two rows share a colour
   only when they are genuinely identical. This turns "the duplicate structure
   survived" from a sentence into something the learner sees at a glance, and
   it is usually the whole lesson.

4. **Put a countable case before the real one.** Nobody can verify a claim
   about 12,288 blocks by looking. Ten blocks with three distinct, laid out to
   be counted by eye, can be checked in seconds. Show the toy, then the real
   thing, and let the learner confirm they have the same shape.

5. **Vary one thing.** Side-by-side panels must be the same input under
   different treatments — same key, same data, only the mode changes.
   Two unrelated examples side by side teach nothing.

6. **State the verification in the page.** "Decrypts back byte-for-byte: true"
   settles a doubt that a paragraph of reassurance will not. Where a learner
   believes data was destroyed, proving the round trip is more convincing than
   explaining why it was not.

7. **Keep it readable without the picture.** Alt text on every image, the key
   numbers in a table as well as in the visual, and a plain-text sentence
   describing each diagram. The page should still teach with images disabled.

## Mechanics

`assets/demo-page.css` carries the shared styling — theme-aware, responsive,
with classes for cards, byte rows (`.row` / `.idx` / `.hex`), countable strips
(`.strip` / `.cell`), verdicts, and measurement tables. Inline it or copy it
beside the generated page.

Write the page into the directory served by `scripts/mermaid-preview.sh`; that
directory serves any file, so a generated page sits alongside the Mermaid panels
at the same origin. `assets/mermaid.min.js` is already there, so a mechanism
diagram can be embedded with a plain `<script src="mermaid.min.js">` and a
`<pre class="mermaid">` block.

Render the page and check it before handing over the URL — images actually
loaded, diagrams actually drew, no `Unsupported markdown: list` in a label. A
demonstration that fails to render is worse than none, because the learner
assumes the failure is theirs.

## Worked example

Teaching why AES-ECB leaks an image: generate a bitmap, encrypt the pixel bytes
with `openssl enc -aes-128-ecb`, and show the original beside the ciphertext
rendered as an image — the shape survives. Add the measured distinct-block
counts (132 before, 132 after) to name the mechanism, a ten-block strip so the
counting is checkable, a CBC panel as the contrast, and a decrypt-and-compare
line proving nothing was lost.
