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

GoodNotes claim query:

```text
source=chatgpt
type=mermaid|markdown
code=<base64 of file>
pattern=dotted
color=white
themeColor=classic
themeShade=light
title=<short>
claim_id=<uuid>   # mermaid only
```

Node labels: `<br/>` for line breaks. Keep text short enough to read on iPad.

**One job per map.** The filename and the root node say that job. Do not put
shop, storage, and "what is a computer" on the same chart.

**Labels are the course’s words.** Take them from the ledger: OCR, lecture
objectives, inspected figures. Stats 1.1 (`Individual`, `Qualitative`) and
Module 2 (`IPOS`, `stored program`, `Fig 2-20`) are the pattern. A quiz-sort
root may be a question the source asks. Do not invent quiz-show phrasing
(`Can it load a new program?`) that the notes do not use.

Independent ideas fork in parallel. Ordered steps are a chain with one exit.
Lookup facts can hang off a step with a dotted edge so they do not look like
the next step.

**LR** = `flowchart LR` (concept / taxonomy). **TD** = `flowchart TD` (quiz sort).

**Parallel fork:** if two ideas are independent, both edges leave the same
parent. Do not draw a taxonomy as a causal chain.

1.1 worked example (keep this pattern): `VAR --> VT` and `VAR --> DS`.
