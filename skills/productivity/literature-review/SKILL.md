---
name: literature-review
description: "Use this skill when the task is to find, screen, synthesize, and cite a body of academic or technical literature."
category: productivity
source: https://skillrepo.dev/skills/affaan-m/literature-review
author: Affaan Mustafa
license: MIT
retrieved: 2026-06-14
---

# Literature Review

Use this skill when the task is to systematically find, screen, synthesize, and cite a body of academic or technical literature.

## When to Use

- Building a systematic, scoping, or narrative literature review.
- Synthesizing the state of the art for a research question.
- Finding evidence gaps, methodological contradictions, or future-work directions.
- Preparing citation-backed background sections for papers, patents, or technical reports.
- Comparing evidence across peer-reviewed papers, preprints, patents, and official technical reports.

## When NOT to Use

- Performing codebase modifications, bug fixes, or writing code refactors.
- Developing backend API routing, database migrations, or server configuration scripts.
- General software testing or code-level architecture design.

## Review Types

- **Narrative review:** Broad synthesis; useful for initial orientation on a topic.
- **Scoping review:** Maps key concepts, research methods, and evidence gaps.
- **Systematic review:** Employs a predefined protocol, reproducible search, and explicit screening/exclusion criteria.
- **Meta-analysis:** A systematic review combined with quantitative statistical effect aggregation.

*Ask the user which level of rigor is needed. If unspecified, default to a scoping review for exploratory work and a systematic review for publication or clinical claims.*

---

## Workflow

### 1. Define the Question

Convert the prompt into a searchable, structured research question.

- **For Clinical / Biomedical Work (PICO):**
  - **P**opulation (patient or problem)
  - **I**ntervention or exposure
  - **C**omparator (baseline or control)
  - **O**utcome (measured effect)
- **For Technical / Engineering Work:**
  - **System or Domain**
  - **Method or Intervention**
  - **Comparison Baseline**
  - **Evaluation Metric**

### 2. Plan the Search

Create a search protocol before collecting sources:
- Databases to search (e.g., PubMed, arXiv, Semantic Scholar, Crossref, IEEE Xplore).
- Date ranges and languages.
- Publication types (e.g., journal articles, preprints, conference proceedings, patents).
- Explicit inclusion and exclusion criteria.
- Exact search strings/queries.

### 3. Search and Log Evidence

Keep a search log that makes the review fully reproducible:

| Database | Date searched | Query | Filters | Results | Export |
|---|---|---|---|---|---|
| PubMed | 2026-05-11 | `("CRISPR"[tiab] OR "Cas9"[tiab]) AND "sickle cell"[tiab]` | 2020:2026, English | 86 | PMID list |
| arXiv | 2026-05-11 | `CRISPR sickle cell gene editing` | q-bio, 2020:2026 | 9 | BibTeX |

*Save raw IDs, URLs, DOIs, abstracts, and notes separately from the final prose.*

### 4. Deduplicate

Deduplicate incoming papers in this order:
1. DOI
2. PMID or arXiv ID
3. Exact Title
4. Normalized title plus first author and year

*Record how many duplicates were removed.*

### 5. Screen Sources

Screen in stages:
1. Title screening
2. Abstract screening
3. Full-text screening

*For systematic work, record explicit exclusion reasons (e.g., wrong population, wrong outcome, wrong intervention, not primary research, duplicate, outside date range, full-text unavailable).*

### 6. Extract Data

Use a structured extraction table:

| Study | Design | Population/Data | Method | Comparator | Outcome | Key finding | Limitations |
|---|---|---|---|---|---|---|---|
| Author Year | RCT/cohort/review/etc. | sample or corpus | method | baseline | measured outcome | result | caveat |

*For technical papers, include dataset, benchmark, metric, baseline, and reproducibility notes.*

### 7. Synthesize

Group evidence by themes rather than summarizing papers one by one.

#### Useful Synthesis Lenses:
- **Evidence Strength:** Strongest evidence vs. early speculative findings.
- **Contradictions:** Conflicting evidence or results.
- **Weaknesses:** Methodological or sample limitations.
- **Practical Implications:** Real-world applications and limitations.
- **Unanswered Questions:** Key knowledge gaps.

#### Categorize Claims by Confidence:
- **High confidence:** Replicated, high-quality evidence across multiple independent sources.
- **Medium confidence:** Plausible claims, but limited by sample size, method, or recency.
- **Low confidence:** Early, speculative, single-source, or weakly measured findings.

### 8. Verify Citations

Before finalizing:
- Verify DOI, PMID, arXiv ID, or official URL.
- Check author names and publication year.
- Ensure you do not cite a paper for a claim it does not make.
- Mark preprints clearly as preprints.
- Distinguish reviews from primary evidence.

---

## Output Template

```markdown
# Literature Review: <Topic>

Generated: <date>
Review type: <narrative | scoping | systematic | meta-analysis>
Search window: <dates>
Databases: <list>

## Research Question

## Search Strategy

## Inclusion and Exclusion Criteria

## Evidence Summary

## Thematic Synthesis

## Gaps and Limitations

## References

## Search Log
```

---

## Pitfalls to Avoid

- **Abstract-Only Bias:** Do not treat search snippets or abstracts as full evidence.
- **Unlabeled Formats:** Do not mix preprints, reviews, and primary studies without labeling them.
- **Confirmation Bias:** Do not omit negative, contradictory, or conflicting findings.
- **Protocol Drift:** Do not claim systematic-review rigor without a pre-defined, reproducible protocol.
- **Single Database Bias:** Do not use a single database for broad claims unless the scope is explicitly limited.
