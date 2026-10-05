import ast
import contextlib
import importlib.util
import io
import hashlib
import json
import sys
import tempfile
import unittest
import unittest.mock
import zipfile
from pathlib import Path
from unittest.mock import patch

SCRIPTS = Path(__file__).resolve().parents[1] / 'scripts'


def load(name):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / (name + '.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


validate = load('validate_kit')
pptx = load('extract_pptx')
sync = load('sync_skill')
scaffold = load('new_section')
notebook = load('build_section_pdf')


class KitTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.kit = Path(self.temp.name)
        self.section = self.kit / 'Chapter-01' / '1.1'
        self.section.mkdir(parents=True)
        (self.kit / 'overall-flow.mmd').write_text('flowchart LR\n S --> CH1_1\n')

    def test_extract_core_rejects_empty(self):
        with self.assertRaisesRegex(ValueError, 'no Core'):
            notebook.extract_core('# 1.1 Retrieval\nOnly questions\n')

    def test_kit_contract_requires_week_on_state(self):
        self.fill_live_contract()
        (self.section / 'state.json').write_text(json.dumps({'status': 'ready'}))
        errors = '\n'.join(validate.check_kit(self.kit))
        self.assertIn('positive integer week', errors)

    def test_relative_source_links(self):
        sources = self.kit / 'SOURCES.md'
        (self.kit / 'A B.pptx').write_text('fixture')
        sources.write_text('[slide](A%20B.pptx) [missing](../missing.ppt) [web](https://example.com)')
        self.assertEqual(validate.missing_links(sources), ['../missing.ppt'])

    def test_kit_contract_catches_missing_hub_and_pending(self):
        (self.kit / 'ocr-S001.pending.txt').write_text('')
        errors = '\n'.join(validate.check_kit(self.kit))
        self.assertIn('Missing hub.json', errors)
        self.assertIn('Leftover pending OCR', errors)
        self.assertIn('missing ledger.md', errors)

    def test_kit_contract_rejects_statistics_prefix_on_it_course(self):
        course = Path(self.temp.name)
        kit = course / 'IT-100' / 'Chapter-Kits'
        kit.mkdir(parents=True)
        (kit / 'hub.json').write_text(json.dumps({
            'title': 'Wrong', 'prefix': 'Statistics'}))
        errors = '\n'.join(validate.check_kit(kit))
        self.assertIn('belongs to MA-235', errors)

    def test_practice_bank_requires_source_outcomes_and_explanatory_answers(self):
        practice = self.section / 'Practice.md'
        plan = self.section / 'practice-plan.md'
        practice.write_text(
            '> [!question]- Q01. First decision?\n'
            '> **Answer:** One. **Why:** Source reason. **Review:** Core 1.\n'
            '> [!question]- Q02. Second decision?\n'
            '> **Answer:** Two. **Why:** Source reason. **Review:** Core 2.\n'
            '> [!question]- Q03. Varied second decision?\n'
            '> **Answer:** Two. **Why:** New context. **Review:** Core 2.\n')
        plan.write_text(
            'Q_min = A + H = 2 + 1 = 3\n'
            '| Outcome | Core/source anchor | Learner decision | Extra reason | Primary | Varied extra |\n'
            '| --- | --- | --- | --- | --- | --- |\n'
            '| 1 | Core 1 | Decide one | — | Q01 | — |\n'
            '| 2 | Core 2 | Decide two | Contrast | Q02 | Q03 |\n')
        self.assertEqual(validate.check_practice(practice, plan), [])
        practice.write_text(practice.read_text().replace('Q03. Varied', 'Q04. Varied')
                            .replace('**Why:** New context. ', ''))
        errors = '\n'.join(validate.check_practice(practice, plan))
        self.assertIn('question IDs must be consecutive', errors)
        self.assertIn('Q04 needs **Why:**', errors)
        self.assertIn('map each question ID exactly once', errors)

    def test_practice_items_ask_about_ideas_not_source_locations(self):
        practice = self.section / 'Practice.md'
        plan = self.section / 'practice-plan.md'
        plan.write_text(
            'Q_min = A + H = 2 + 0 = 2\n'
            '| Outcome | Core/source anchor | Learner decision | Extra reason | Primary | Varied extra |\n'
            '| --- | --- | --- | --- | --- | --- |\n'
            '| 1 | Core 1 | Decide one | — | Q01 | — |\n'
            '| 2 | Core 2 | Decide two | — | Q02 | — |\n')
        practice.write_text(
            '> [!question]- Q01. Which cues does PP4 list?\n'
            '> **Answer:** Face. **Why:** Slide 2 lists them. **Review:** Core 1, Figure 2-19.\n'
            '> [!question]- Q02. A clerk rings you up in a lecture hall. Which distance?\n'
            '> **Answer:** Social. **Why:** Impersonal business, not a printed letter. **Review:** Core 2.\n')
        errors = validate.check_practice(practice, plan)
        self.assertEqual(len(errors), 1)
        self.assertIn('Q01 cites the source ("PP4")', errors[0])

    def fill_live_contract(self):
        (self.kit / 'hub.json').write_text(json.dumps({
            'title': 'T', 'prefix': 'T',
            'goodnotes_root': 'Monroe University', 'goodnotes_term': '2026 Fall',
            'goodnotes_course': 'T-100 Test'}))
        (self.kit / 'README.md').write_text('Map then Retrieval then Practice.md')
        (self.kit / 'SOURCES.md').write_text('# sources\n')
        (self.kit / 'overall-flow.prev.mmd').write_text((self.kit / 'overall-flow.mmd').read_text())
        (self.kit / 'Chapter-01' / 'README.md').write_text('# Chapter 01\n')
        (self.section / 'ledger.md').write_text('# ledger\n')
        (self.section / 'state.json').write_text(json.dumps({
            'status': 'ready', 'week': 1, 'coverage': 'partial', 'title': 'Data Basics'}))
        (self.section / 'Practice.md').write_text(
            '> [!question]- Q01. Test idea?\n'
            '> **Answer:** Yes. **Why:** Source. **Review:** Core 1.\n')
        (self.section / 'practice-plan.md').write_text(
            'Q_min = A + H = 1 + 0 = 1\n'
            '| Outcome | Core/source anchor | Learner decision | Extra reason | Primary | Varied extra |\n'
            '| --- | --- | --- | --- | --- | --- |\n'
            '| 1 | Core 1 | Test idea | — | Q01 | — |\n')
        (self.section / 'N-Study-Notes.md').write_text('# Core\nRead me\n')
        (self.section / '1.1-concept-map.mmd').write_text('flowchart LR\nA --> B\n')
        (self.section / '1.1-decision-flow.mmd').write_text('flowchart TD\nA --> B\n')

    def test_filled_contract_passes(self):
        self.fill_live_contract()
        self.assertEqual(validate.check_kit(self.kit), [])

    def test_hub_json_without_goodnotes_route_fails_contract(self):
        self.fill_live_contract()
        data = json.loads((self.kit / 'hub.json').read_text())
        del data['goodnotes_course']
        (self.kit / 'hub.json').write_text(json.dumps(data))
        self.assertIn('goodnotes_course', '\n'.join(validate.check_kit(self.kit)))

    def test_section_folder_name_never_repeats_number(self):
        self.assertEqual(notebook.section_folder_name('1.1', '1.1'), '1.1')
        self.assertEqual(notebook.section_folder_name('1.1', ''), '1.1')
        self.assertEqual(notebook.section_folder_name('3.2', '3.2 Variation'), '3.2 Variation')
        self.assertEqual(notebook.section_folder_name('3.2', 'Variation'), '3.2 Variation')

    def test_state_requires_status_coverage_and_title(self):
        self.fill_live_contract()
        (self.section / 'state.json').write_text(json.dumps({
            'status': 'done', 'week': 1, 'coverage': 'most'}))
        errors = '\n'.join(validate.check_kit(self.kit))
        self.assertIn('status must be one of', errors)
        self.assertIn('coverage must be one of', errors)
        self.assertIn('human title', errors)

    def test_complete_needs_every_check_passed_and_partial_is_not_a_status(self):
        self.fill_live_contract()
        state = {'status': 'complete', 'week': 1, 'coverage': 'partial', 'title': 'T',
                 'verification': {'local': 'passed', 'render': 'passed', 'import': 'pending'}}
        (self.section / 'state.json').write_text(json.dumps(state))
        self.assertIn('complete needs verification', '\n'.join(validate.check_kit(self.kit)))
        state['verification']['import'] = 'passed'
        (self.section / 'state.json').write_text(json.dumps(state))
        self.assertEqual(validate.check_kit(self.kit), [])
        state['status'] = 'partial'
        (self.section / 'state.json').write_text(json.dumps(state))
        self.assertIn('status must be one of', '\n'.join(validate.check_kit(self.kit)))

    def test_free_text_verification_warns_but_passes(self):
        self.fill_live_contract()
        (self.section / 'state.json').write_text(json.dumps({
            'status': 'ready', 'week': 1, 'coverage': 'partial', 'title': 'T',
            'verification': {'local': 'validate_kit passed', 'render': 'passed', 'import': 'pending'}}))
        self.assertEqual(validate.check_kit(self.kit), [])
        warnings = '\n'.join(validate.kit_warnings(self.kit))
        self.assertIn('verification local should be pending, passed, or failed', warnings)
        self.assertNotIn('render', warnings)

    def test_scripts_define_each_function_once(self):
        # A second definition silently replaces the first, so an edit to the first does nothing.
        for script in SCRIPTS.glob('*.py'):
            names = [node.name for node in ast.parse(script.read_text()).body
                     if isinstance(node, (ast.FunctionDef, ast.ClassDef))]
            duplicates = sorted({name for name in names if names.count(name) > 1})
            self.assertEqual(duplicates, [], script.name)

    def test_mermaid_is_pinned_and_integrity_checked(self):
        self.assertRegex(notebook.MERMAID_JS, r'/mermaid@\d+\.\d+\.\d+/')
        self.assertRegex(notebook.MERMAID_SRI, r'^sha384-[A-Za-z0-9+/]{64}$')
        page, _ = notebook.overview_html(self.kit, 'C')
        self.assertIn(f'integrity="{notebook.MERMAID_SRI}" crossorigin="anonymous"', page)

    def test_map_directions_enforced(self):
        self.fill_live_contract()
        (self.section / '1.1-concept-map.mmd').write_text('flowchart TD\nA --> B\n')
        (self.section / '1.1-error-flow.mmd').write_text('flowchart LR\nA --> B\n')
        errors = '\n'.join(validate.check_kit(self.kit))
        self.assertIn('1.1-concept-map.mmd must be flowchart LR', errors)
        self.assertIn('1.1-error-flow.mmd must be flowchart TD', errors)

    def test_section_check_ignores_other_sections(self):
        self.fill_live_contract()
        (self.kit / 'Chapter-02' / '2.1').mkdir(parents=True)
        self.assertEqual(validate.check_section(self.section), [])
        self.assertIn('missing ledger.md', validate.check_section(self.kit / 'Chapter-02' / '2.1'))

    def test_outcome_id_format_is_explained(self):
        self.fill_live_contract()
        plan = self.section / 'practice-plan.md'
        plan.write_text(plan.read_text().replace('| 1 | Core 1', '| O1 | Core 1'))
        errors = '\n'.join(validate.check_practice(self.section / 'Practice.md', plan))
        self.assertIn('numeric ID', errors)

    def test_ledger_without_source_rows_warns_but_passes(self):
        self.fill_live_contract()
        self.assertEqual(validate.check_kit(self.kit), [])
        self.assertIn('no source table rows', '\n'.join(validate.kit_warnings(self.kit)))
        (self.section / 'ledger.md').write_text('| S001 | a | b | c | d |\n')
        self.assertFalse([w for w in validate.kit_warnings(self.kit) if 'source table' in w])

    def test_scaffold_creates_collecting_section_and_refuses_existing(self):
        folder = scaffold.scaffold(self.kit, '3.2', 3, 'Measures of Variation')
        self.assertEqual(folder, self.kit / 'Chapter-03' / '3.2')
        state = json.loads((folder / 'state.json').read_text())
        self.assertEqual((state['status'], state['week'], state['title']),
                         ('collecting', 3, 'Measures of Variation'))
        self.assertEqual(validate.check_state(folder / 'state.json'), [])
        self.assertIn('| ID | Original location |', (folder / 'ledger.md').read_text())
        self.assertFalse((folder / 'Practice.md').exists())
        with self.assertRaisesRegex(ValueError, 'already exists'):
            scaffold.scaffold(self.kit, '3.2', 3, 'Again')
        with self.assertRaisesRegex(ValueError, 'week'):
            scaffold.scaffold(self.kit, '3.3', 0, 'X')

    OVERALL = (
        'flowchart LR\n'
        '  classDef ch fill:#EEE\n'
        '  S(["STATS"])\n'
        '  CH1_1(["1.1 Basics"])\n'
        '  IND("Individual")\n'
        '  CH2_1(["2.1 Tables"])\n'
        '  S --> CH1_1\n'
        '  CH1_1 --> IND\n'
        '  S --> CH2_1\n'
        '  CH2_1 --> FT["Frequency table"]:::ch\n'
        '  S --> NOTE("Course note")\n'
        '  class CH1_1,CH2_1 ch\n'
        '  linkStyle 1,3 stroke:#999\n')

    def test_overall_split_is_per_chapter_and_lossless(self):
        parts = dict(notebook.split_overall(self.OVERALL))
        self.assertEqual(sorted(parts), [1, 2])
        self.assertIn('CH1_1 --> IND', parts[1])
        self.assertIn('S --> NOTE', parts[1])
        self.assertNotIn('CH2_1', parts[1])
        self.assertIn('CH2_1 --> FT["Frequency table"]:::ch', parts[2])
        self.assertNotIn('IND', parts[2])
        self.assertIn('class CH2_1 ch', parts[2])
        # Edge 1 (CH1_1 --> IND) is the second edge in part 1; edge 3 is second in part 2.
        self.assertIn('linkStyle 1 stroke:#999', parts[1])
        self.assertIn('linkStyle 1 stroke:#999', parts[2])

    def test_overall_split_refuses_unknown_syntax_and_single_chapter(self):
        with self.assertRaisesRegex(ValueError, 'cannot be split'):
            notebook.split_overall(self.OVERALL + '  subgraph X\n')
        with self.assertRaisesRegex(ValueError, 'fewer than two chapters'):
            notebook.split_overall('flowchart LR\n  S(["S"])\n  S --> CH1_1\n')

    def test_sync_updates_known_old_copy_and_preserves_unrelated(self):
        source, dest = self.kit / 'source', self.kit / 'dest'
        source.mkdir(); dest.mkdir()
        (source / 'SKILL.md').write_text('new')
        (dest / 'SKILL.md').write_text('old')
        (dest / 'personal.txt').write_text('keep')
        (source / 'MANIFEST.json').write_text(json.dumps({'files': {'SKILL.md': sync.digest(source / 'SKILL.md')}}))
        (dest / 'MANIFEST.json').write_text(json.dumps({'files': {'SKILL.md': sync.digest(dest / 'SKILL.md')}}))
        sync.synchronize(source, dest, write=True)
        self.assertEqual((dest / 'SKILL.md').read_text(), 'new')
        self.assertEqual((dest / 'personal.txt').read_text(), 'keep')
        self.assertEqual(sync.synchronize(source, dest), [])

    def test_sync_refuses_unreviewed_drift_before_writing(self):
        source, dest = self.kit / 'source', self.kit / 'dest'
        source.mkdir(); dest.mkdir()
        (source / 'SKILL.md').write_text('new')
        (dest / 'SKILL.md').write_text('local edit')
        (source / 'MANIFEST.json').write_text(json.dumps({'files': {'SKILL.md': sync.digest(source / 'SKILL.md')}}))
        with self.assertRaisesRegex(ValueError, 'Unreviewed deployed edit'):
            sync.synchronize(source, dest, write=True)
        self.assertEqual((dest / 'SKILL.md').read_text(), 'local edit')

    def test_sync_refuses_destination_file_symlink(self):
        source, dest = self.kit / 'source', self.kit / 'dest'
        source.mkdir(); dest.mkdir()
        (source / 'SKILL.md').write_text('new')
        (self.kit / 'outside.md').write_text('private edit')
        (dest / 'SKILL.md').symlink_to(self.kit / 'outside.md')
        (source / 'MANIFEST.json').write_text(json.dumps({'files': {'SKILL.md': sync.digest(source / 'SKILL.md')}}))
        with self.assertRaisesRegex(ValueError, 'Symlink'):
            sync.synchronize(source, dest, write=True)
        self.assertEqual((self.kit / 'outside.md').read_text(), 'private edit')

    def deck(self, empty=False):
        path = self.kit / 'example.pptx'
        with zipfile.ZipFile(path, 'w') as z:
            z.writestr('ppt/presentation.xml', f'<p:presentation xmlns:p="{pptx.NS["p"]}" xmlns:r="{pptx.NS["r"]}"><p:sldIdLst><p:sldId r:id="r2"/><p:sldId r:id="r1"/></p:sldIdLst></p:presentation>')
            z.writestr('ppt/_rels/presentation.xml.rels', '<Relationships><Relationship Id="r1" Target="slides/slide1.xml"/><Relationship Id="r2" Target="slides/slide2.xml"/></Relationships>')
            for i in [1, 2]:
                text = '' if empty and i == 1 else f'Text {i}'
                z.writestr(f'ppt/slides/slide{i}.xml', f'<p:sld xmlns:p="{pptx.NS["p"]}" xmlns:a="{pptx.NS["a"]}"><a:p><a:r><a:t>{text}</a:t></a:r></a:p></p:sld>')
        return path

    def test_pptx_uses_presentation_order(self):
        text = pptx.extract(self.deck())
        self.assertLess(text.index('Text 2'), text.index('Text 1'))
        self.assertIn('slides: 2', text)

    def test_pptx_image_only_slide_fails(self):
        with self.assertRaisesRegex(ValueError, 'Slide 2: no extractable text'):
            pptx.extract(self.deck(empty=True))

    def concept_code(self, hubs=5, leaves=4):
        lines = ['flowchart LR', '  S(["COURSE"])']
        for h in range(hubs):
            lines.append(f'  H{h}("Hub {h}")')
            lines.append(f'  S --> H{h}')
            for leaf in range(leaves):
                lines.append(f'  L{h}_{leaf}("Leaf {h}.{leaf}")')
                lines.append(f'  H{h} --> L{h}_{leaf}')
        return '\n'.join(lines + ['  classDef root fill:#1F3A5F'])

    def test_large_concept_map_gets_one_lossless_page_per_hub(self):
        pages = notebook.split_concept(self.concept_code())
        self.assertEqual([label for label, _ in pages], [f'Hub {h}' for h in range(5)])
        for h, (_, code) in enumerate(pages):
            self.assertTrue(code.startswith('flowchart LR'))
            self.assertIn(f'S --> H{h}', code)
            self.assertIn('classDef root', code)
            for leaf in range(4):
                self.assertIn(f'H{h} --> L{h}_{leaf}', code)
            self.assertNotIn(f'H{(h + 1) % 5} -->', code)

    def test_concept_split_leaves_small_or_labelled_maps_whole(self):
        self.assertEqual(notebook.split_concept(self.concept_code(hubs=3)), [])
        labelled = self.concept_code().replace('S --> H0', 'S -->|yes| H0')
        self.assertEqual(notebook.split_concept(labelled), [])

    def test_notebook_keeps_core_only_and_redraws_before_check(self):
        (self.section / 'state.json').write_text(json.dumps({'week': 1, 'title': 'Data Basics'}))
        (self.section / 'X-Study-Notes.md').write_text(
            '# 1.1 Core\n## A. Basics\n### 1. Idea\nCore text.\n\n**TEST MOVE:** Decide.\n'
            '# 1.1 Quiz why\nOfficial key text\n')
        (self.section / 'x-1.1-concept-map.mmd').write_text('flowchart LR\n  S --> A\n')
        (self.section / 'x-1.1-decision-flow.mmd').write_text('flowchart TD\n  Q --> A\n')
        (self.section / 'x-1.1-https-flow.mmd').write_text('flowchart LR\n  K --> L\n')
        page, diagrams = notebook.section_html('1.1', self.section, 'MA-235 Statistics', 1, 'Data Basics')
        self.assertEqual(diagrams, page.count('<pre class="mermaid">'))
        self.assertEqual(diagrams, 3)
        self.assertIn('Core text.', page)
        self.assertIn('class="test"', page)
        self.assertNotIn('Official key text', page)
        self.assertIn('Map · HTTPS', page)
        self.assertLess(page.index('Quiz Sort: redraw from memory'), page.index('Quiz Sort: check'))
        self.assertIn('1.1 Data Basics', page)

    def test_render_check_reports_undrawn_diagrams(self):
        good = '<title>READY</title>' + '<pre data-processed="true">' * 2
        self.assertEqual(notebook.rendered_ok(good, 2), [])
        problems = notebook.rendered_ok('<title>x</title><pre data-processed="true">', 2)
        self.assertIn('1 of 2 Mermaid diagrams rendered', problems)
        self.assertIn('page did not finish rendering', problems)

    def test_notebook_goes_to_matching_week_work_folder(self):
        course = self.kit / 'course'
        for name in ('Week-04_2026-09-28_to_2026-10-04', 'Weeks-14-15_Finals_2026-12-07_to_2026-12-17'):
            (course / name).mkdir(parents=True)
        self.assertEqual(notebook.week_work(course, 4).parent.name, 'Week-04_2026-09-28_to_2026-10-04')
        self.assertEqual(notebook.week_work(course, 15).parent.name, 'Weeks-14-15_Finals_2026-12-07_to_2026-12-17')
        with self.assertRaises(FileNotFoundError):
            notebook.week_work(course, 5)
        self.assertEqual(notebook.pdf_name(Path('IT-100'), '4.1', 'The Web'), 'IT-100_4.1_The-Web_GoodNotes.pdf')

    def test_notebook_refuses_collecting_section_before_rendering(self):
        (self.kit / 'hub.json').write_text(json.dumps({'goodnotes_course': 'T-100 Test'}))
        (self.section / 'state.json').write_text(json.dumps({'status': 'collecting', 'week': 1, 'title': 'T'}))
        with patch.object(notebook.validate_kit, 'check_kit', return_value=[]), \
                patch.object(notebook, 'render') as render:
            with self.assertRaisesRegex(ValueError, 'collecting'):
                notebook.build(self.kit, None, False)
        render.assert_not_called()

    def test_notebook_refuses_kit_that_fails_contract(self):
        with patch.object(notebook, 'render') as render:
            with self.assertRaisesRegex(ValueError, 'kit contract failed'):
                notebook.build(self.kit, None, False)
        render.assert_not_called()
    def test_course_overview_notebook_has_one_page_per_chapter(self):
        (self.kit / 'overall-flow.mmd').write_text(
            'flowchart LR\nS["COURSE"]\nS --> CH1_1\nCH1_1["1.1 A"]\nCH1_1 --> X["x"]\n'
            'S --> CH2_1\nCH2_1["2.1 B"]\nCH2_1 --> Y["y"]\n')
        page, diagrams = notebook.overview_html(self.kit, 'MA-235 Statistics')
        self.assertEqual(diagrams, 3)
        self.assertEqual(page.count('<pre class="mermaid">'), 3)
        self.assertIn('Overall map · Chapter 2', page)
        (self.kit / 'overall-flow.mmd').write_text('flowchart LR\nS --> CH1_1\n')
        self.assertEqual(notebook.overview_html(self.kit, 'MA-235 Statistics')[1], 1)

    def test_core_drops_quiz_why_and_retrieval(self):
        core = notebook.extract_core('# 1.1 Core\nKeep this.\n\n# 1.1 Quiz why\nOfficial stem\n\n# 1.1 Retrieval\nPrompt\n')
        self.assertEqual(core, '# 1.1 Core\nKeep this.\n')

    def test_alert_label_joins_first_paragraph_without_literal_quote_marker(self):
        notes = self.section / '1.1-Study-Notes.md'
        notes.write_text('# 1.1 Core\n\n> [!NOTE]\n> The slides define it.\n>\n> Second paragraph.\n\n'
                         '> [!tip]\n>\n> After a blank line.\n')
        body = notebook.core_html(notes)
        self.assertNotIn('&gt;', body)
        self.assertIn('<p><strong>NOTE:</strong> The slides define it.</p>\n<p>Second paragraph.</p>', body)
        self.assertIn('<p><strong>TIP:</strong> After a blank line.</p>', body)

    def test_map_title_drops_course_tag_and_restores_acronyms(self):
        for name in ('it-3.1-address-flow.mmd', 'stats-3.1-address-flow.mmd', '3.1-address-flow.mmd'):
            self.assertEqual(notebook.map_title('3.1', Path(name)), 'Address')
        self.assertEqual(notebook.map_title('4.1', Path('it-4.1-https-flow.mmd')), 'HTTPS')
        self.assertEqual(notebook.map_title('4.1', Path('it-4.1-error-flow.mmd')), 'Error Sort')
        self.assertEqual(notebook.map_title('4.1', Path('it-4.1-decision-flow.mmd')), 'Quiz Sort')

    def test_notebook_needs_exactly_one_canonical_notes_file(self):
        (self.section / 'A-Study-Notes.md').write_text('# Core\nA\n')
        (self.section / 'B-Study-Notes.md').write_text('# Core\nB\n')
        with self.assertRaisesRegex(ValueError, 'exactly one'):
            notebook.section_html('1.1', self.section, 'C', 1, 'T')

    def test_render_retries_once_then_refuses_without_printing(self):
        good = '<title>READY</title><pre data-processed="true">'
        out = self.kit / 'n.pdf'
        calls = []

        def fake_chrome(*args):
            calls.append(args[0])
            if args[0] == '--dump-dom':
                return unittest.mock.Mock(stdout='' if calls.count('--dump-dom') == 1 else good)
            Path(args[0].split('=', 1)[1]).write_text('pdf')
            return unittest.mock.Mock(stdout='')
        with patch.object(notebook, 'CHROME', Path(sys.executable)), patch.object(notebook, 'chrome', fake_chrome):
            notebook.render('<html></html>', 1, out)
        self.assertEqual(out.read_text(), 'pdf')
        self.assertEqual(calls.count('--dump-dom'), 2)
        out.write_text('previous')
        with patch.object(notebook, 'CHROME', Path(sys.executable)), \
                patch.object(notebook, 'chrome', lambda *a: unittest.mock.Mock(stdout='')):
            with self.assertRaisesRegex(RuntimeError, '0 of 1 Mermaid diagrams'):
                notebook.render('<html></html>', 1, out)
        self.assertEqual(out.read_text(), 'previous')

if __name__ == '__main__':
    unittest.main()
