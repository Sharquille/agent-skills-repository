# Visual language

Copy these `classDef` blocks. Do not invent a second palette.

```text
classDef root fill:#1F3A5F,stroke:#1F3A5F,color:#FFFFFF,font-weight:bold,font-size:18px
classDef intro fill:#EEF3F8,stroke:#8FA8BE,color:#24313F
classDef hubV fill:#EFE9FA,stroke:#9B8AB8,color:#3E3357,font-weight:bold
classDef leafV fill:#F8F4FD,stroke:#B9A9D1,color:#4A3D63
classDef hubD fill:#E7F4EC,stroke:#6FA98A,color:#2F4F3C,font-weight:bold
classDef leafD fill:#F3FAF6,stroke:#93C2A8,color:#37543F
classDef hubI fill:#FBEFE3,stroke:#C98F5A,color:#5C4023,font-weight:bold
classDef leafI fill:#FEF8F1,stroke:#DBAC7E,color:#654626
```

- Navy root = course or chapter title
- Intro gray = definition / remember / gather
- Purple = variable hub and leaves
- Green = descriptive / population / parameter
- Peach (`hubI` / `leafI`) = inferential, **only after that chapter is earned**

Node labels: `<br/>` for line breaks. Keep text short enough to read on iPad.

**One job per map.** The filename and the root node say that job. A taxonomy
root can be the module or section title; leaves answer the job. Do not put
shop, storage, and "what is a computer" on the same chart.

**Labels are the course’s words.** Take them from the ledger: OCR, lecture
objectives, inspected figures. Stats 1.1 (`Individual`, `Qualitative`,
`Appearance`) and Module 2 (`IPOS`, `stored program`, `Fig 2-20`) are the pattern. A quiz-sort
root may be a question the source asks. Do not invent quiz-show phrasing
(`Can it load a new program?`) that the notes do not use.

**LR** = `flowchart LR` (concept / taxonomy). **TD** = `flowchart TD` (quiz sort).

**Parallel fork:** independent ideas after a named hub both leave the same
parent; do not draw a taxonomy as a causal chain. 1.1 worked example (keep this
pattern): `VAR --> VT` and `VAR --> DS`. Ordered steps are a chain with one
exit. Lookup facts can hang off a step with a dotted edge so they do not look
like the next step.

**Map layout checks.** The 4.1 HTTPS map printed as a thin strip with a
floating box and a lock that seemed to come from "James decrypts". Avoid all
three:

- **Ordered steps go top-down.** A chain of more than four steps is
  `flowchart TD` (concept maps stay LR). An LR chain prints as a strip across a
  portrait page and leaves it mostly blank.
- **One root.** Every node hangs off the map's one root. A box with no edge in
  is a second job; give it its own map or attach it to the hub it belongs to.
- **An edge claims a cause.** Draw an arrow only where the notes say one thing
  leads to the other. A result that needs two ideas (lock = encrypted data +
  valid certificate) gets an edge from each hub, never from the last step of
  one chain.

`validate_kit.py` warns on a long LR chain in a non-concept map and on a map
with more than one starting node. Render the map page and look at it before
release.

## Figures in Core

Maps name the ideas; a Core figure shows how one idea works, right after the
text it illustrates. Every new section gets figures for the ideas that are
spatial, ordered, set-like, a contrast, a procedure, or a scale (population
inside sample, levels of measurement, sampling methods, frame and
undercoverage, selection then assignment). Skip ideas that are only a
definition or an argument in prose; a literature section may need none.

1. **One idea per figure; the text adds only what the figure cannot.** The
   figure carries the structure, so the prose around it gives the reason or
   decision and does not describe the picture again
   ([notes-contract.md](notes-contract.md#say-it-once)). The TEST MOVE stays.
2. **Labels on the picture, in the course's words** from Core and the ledger.
   Numbers come only from the notes or ledger; `validate_kit.py` rejects a
   multi-digit, decimal, or percent value it cannot find there. Placeholders
   that only show a pattern (`Climber 1`, `here k = 4`) read as examples.
3. **Same meaning, same colour, in every figure of a course.** Palette
   colours only; the validator rejects others.

   | Course | Green | Navy | Purple | Peach |
   | --- | --- | --- | --- | --- |
   | MA-235 | population, parameter, descriptive | sample, statistic | individuals, variables | inferential, traps, errors, undercoverage |
   | IT-100 | server, destination, receiver | your device, client, sender | data, packets, components | failure, loss, attacker |
   | EN-221, LA-122 | the other side, receiver, outcome | speaker, character, sender | message, channel, story parts | conflict, gap, noise |
   | Security+ | protected asset, business function, goal | defender, organization, process, role | control category and type | attack, incident, security added late |

   A new course picks its mapping on its first figure and adds a row here.
   Draw on a 470-wide `viewBox` with labels at 10 or larger; a wider canvas
   shrinks to the column, and `validate_kit.py --kit` warns when a label
   prints under 8.
4. **Replace a table only when the figure holds every cell** (the levels
   staircase, the sampling-method panels). Otherwise keep the table and draw
   the relation the table cannot show.
5. **No decoration and no caption that repeats nearby text.** A picture that
   does not carry the idea costs attention.
6. **Check the figure against its definition sentence.** A shape can teach the
   opposite of the words (undercoverage is only the population outside the
   frame, never inside it). Render the page and inspect it for overlap and
   clipping before release.
7. **One margin prompt per level-2 group**, drawn or written before looking
   back. Skip a group that only bounds an assignment or retells the reading;
   a prompt asks for the concept, never a worksheet or graded answer:

   ```markdown
   > [!TIP]
   > **SKETCH:** The population circle with a sample inside. Tag P and S.
   ```

   Use `**RECALL:**` for a list to write from memory. The notebook prints it in
   the writing margin; Obsidian shows a tip callout.

### Analogy picture (only when the source shows layers)

When one idea runs on another, draw a real, everyday object whose parts depend
on each other the same way, and label each part with the course term. A vehicle
on a road fits network topics; another familiar object (a building, a
container, a machine) fits other topics. Draw one **only where it is
needed**: the dependency is earned, the section is hard to picture without it,
and no plainer figure already shows it. Most sections need none.

Patterns: `it-4.1-fig-web-vehicle.svg` (a delivery truck on a road between the
Web server and your browser) and `it-5.1-fig-email-vehicle.svg` (an SMTP van
to a post-office email server, then a POP3/IMAP pickup to your client, on the
same road and wheels; the source itself calls the email server a central post
office).

| Course term | Part drawn | Why that part |
| --- | --- | --- |
| Internet | road | everything travels on it |
| TCP/IP | wheels | the delivery and addressing rules that move the load |
| HTTP | truck | delivers the page elements |
| Web page | cargo | what is delivered |
| HTTPS | padlock on the cargo | the data stream is encrypted |
| Certificate | a license framed on the Web server | helps the browser verify the site; it belongs to the site, not the delivery |

**Pick an object that passes the intuitiveness test.** The truck works
because a beginner can guess most mappings before reading a label. Check every
candidate object against these three questions before drawing:

1. Has everyone used it? (a car, a taxi, a bus, a post office, an apartment
   building, a self-storage unit; not a library card catalog or a stand mixer)
2. Does its physical arrangement already show the relation: stacking (road
   under wheels under cargo), passing through (a lobby, then a door), or who
   does the work (you drive, a driver drives, you ride)?
3. Could the learner guess most part mappings from the picture alone?

A grid of boxes, an index card, or a kitchen tool that needs its label to make
sense fails. Propose two or three objects to the learner, with the part mapping
for each, and let them pick before anything is drawn; the object is their
call.

Accepted objects so far: the Web as a delivery truck (4.1), email as the post
(5.1), file storage as a self-storage facility (6.5: your list = folders, the
front-desk ledger = file system, floors and units = tracks and sectors, a block
of units = a cluster, cleaners = the shredder), IaaS/PaaS/SaaS as a rental car,
a taxi, and a bus (Sec+ 10.4), and share vs NTFS permissions as a lobby doorman
and an apartment door (Sec+ 8.2). Rejected as unintuitive: a library shelf
grid, a bakery with a mixer for "platform", a turnstile with a clipboard.

Build it in the Teaching-with-Analogies order (Glynn): the target idea is
already in the text, the picture is the familiar object, the labels map each
part, and one line states where the picture stops. Draw real details (doors,
windows, steering wheels, stick figures with round heads) so the object reads
without labels.

- **Replace, don't add.** When the section already has a plain figure of the
  same path, the analogy picture replaces it; carry over any earned fact the
  old figure held (as a callout or the "where it stops" line).
- **No label on the part that repeats its callout** (no "HTTP" painted on the
  cab when a callout already says HTTP = the truck).
- **Attach each role to its owner and show who asks.** A credential sits on the side that owns it (the site's certificate on the server), and a picture of a delivery shows the request that started it (the browser's request in the far lane of the road).
- **Label the part, beside the part.** Each callout reads
  `**Course term** = part: what it does`, with a short leader line to the part
  it names. Leader lines never cross each other or a label. The course term is
  bold; the analogy word is plain.
- **Bottom-up order stays visible.** The base sits at the bottom of the drawing
  (road, then wheels, then body, then load), so the picture still reads as the
  dependency stack.
- **Map only earned roles.** Each drawn part needs a ledger item in this
  section or a Builds on to an earlier one. Add a role such as the license
  plate only when the section teaches it (certificates in 4.1). Leave a part
  undrawn when nothing earns it, and don't add detail the source doesn't
  teach.
- **One "Where the picture stops" line** follows the figure. It names the
  first way the analogy misleads, and that fact must be earned too (4.1: one
  truck carries the whole page, but TCP/IP splits it into packets on different
  routes, Section 3.1).
- **Put it on the heading where the last mapped part is taught** (4.1 Core 39,
  certificates). It is the only drawing of that dependency; don't add a second
  plain stack of the same layers.
- **Reuse across the course.** A later section that shares the lower layers
  keeps the same road and wheels and draws its own vehicle (email can be a
  different vehicle on the same road once its section is earned).
- Skip it for a list, a taxonomy, or a sequence; those keep their own shapes.

Draw it with the `svg_figure.py` analogy parts: `road()`, `truck()` (returns
anchor points for the cargo, cab, wheels, and rear plate), `padlock()`,
`envelope()`, `callout()`, and `leader()`, on a 470-wide canvas with the road
top at y 214, palette colours only, labels 10 or larger. Render it and check that no label overlaps a line or another label.

Build figures with `scripts/svg_figure.py` (palette, labels, boxes, circles,
arrows, accessible `<svg>`), save each as `<prefix>-<section>-fig-<idea>.svg`
beside the notes, and embed it on its own line with alt text that states the
idea: `![Levels of measurement as a staircase](stats-1.1-fig-levels.svg)`.
Figures must have `role="img"` and an `aria-label`, and no scripts, links, or
embedded images.
