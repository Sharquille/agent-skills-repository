import contextlib
import importlib.util
import io
import hashlib
import json
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

SCRIPTS = Path(__file__).resolve().parents[1] / 'scripts'


def load(name):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / (name + '.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


hub = load('build_goodnotes_hub')
validate = load('validate_kit')
pptx = load('extract_pptx')
sync = load('sync_skill')
scaffold = load('new_section')


class KitTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.kit = Path(self.temp.name)
        self.section = self.kit / 'Chapter-01' / '1.1'
        self.section.mkdir(parents=True)
        (self.kit / 'overall-flow.mmd').write_text('flowchart LR\n S --> CH1_1\n')

    def test_short_canonical_is_discovered_and_stale_splits_ignored(self):
        (self.section / 'Example-Study-Notes.md').write_text('# Core\nFresh notes\n')
        (self.section / 'Example-Notes-Core.md').write_text('Stale notes')
        (self.section / 'notes-migration.json').write_text(json.dumps({
            'canonical': 'Example-Study-Notes.md',
            'legacy_sha256': {'Example-Notes-Core.md': hashlib.sha256(b'Stale notes').hexdigest()}}))
        self.assertEqual(hub.note_imports('1.1', self.section, 7600),
                         [('1.1 Notes', '# Core\nFresh notes\n')])

    def test_unreviewed_legacy_edit_refused(self):
        (self.section / 'N-Study-Notes.md').write_text('Canonical')
        (self.section / 'N-Notes-Core.md').write_text('Unique student edit')
        with self.assertRaisesRegex(ValueError, 'legacy notes differ'):
            hub.note_imports('1.1', self.section, 7600)

    def test_exact_url_limit_and_unicode_lossless_split(self):
        text = ''.join(f'## {i}. Idea\n' + 'é漢字 ' * 40 + '\n' for i in range(6))
        exact = len(hub.markdown_url(text, '1.1 Notes'))
        self.assertEqual(len(hub.split_notes(text, '1.1 Notes', exact)), 1)
        chunks = hub.split_notes(text, '1.1 Notes', exact - 1)
        self.assertGreater(len(chunks), 1)
        self.assertEqual(''.join(code for _, code in chunks), text)
        self.assertTrue(all(len(hub.markdown_url(code, name)) <= exact - 1
                            for name, code in chunks))

    def test_table_and_question_answer_order_preserved(self):
        text = '# Core\n' + 'Text. ' * 100 + '\n## Questions\n| Q | Cue |\n| --- | --- |\n| One | Two |\n## Answers\n' + 'Answer. ' * 100
        chunks = hub.split_notes(text, 'Notes', 1700)
        self.assertEqual(''.join(code for _, code in chunks), text)
        self.assertTrue(any('| Q | Cue |\n| --- | --- |\n| One | Two |' in code for _, code in chunks))
        self.assertLess(text.index('## Questions'), text.index('## Answers'))

    def test_h3_ideas_stay_with_parent_section_h2(self):
        intro = '# Core\nIntro.\n'
        section_a = (
            '## Section A: Device basics\n'
            '### 2. IPOS\n' + 'Input. ' * 30 + '\n'
            '### 3. Stored program\n' + 'Load. ' * 30 + '\n'
        )
        section_b = (
            '## Section B: Device options\n'
            '### 9. Enterprise\n' + 'Server. ' * 30 + '\n'
        )
        text = intro + section_a + section_b
        limit = max(len(hub.markdown_url(block, '1.1 Notes 3/3'))
                    for block in (intro, section_a, section_b))
        chunks = hub.split_notes(text, '1.1 Notes', limit)
        self.assertEqual(''.join(code for _, code in chunks), text)
        self.assertGreater(len(chunks), 1)
        section_a_chunk = next(code for _, code in chunks if '### 2. IPOS' in code)
        self.assertIn('## Section A: Device basics', section_a_chunk)
        self.assertIn('### 3. Stored program', section_a_chunk)
        self.assertNotIn('## Section B: Device options', section_a_chunk)

    def test_oversized_block_rejected_instead_of_truncation(self):
        with self.assertRaisesRegex(ValueError, 'heading block exceeds'):
            hub.split_notes('## Official stem\n' + 'x' * 5000, 'Notes', 1000)

    def test_fenced_headings_do_not_create_boundaries(self):
        with self.assertRaisesRegex(ValueError, 'heading block exceeds'):
            hub.split_notes('## Code\n```\n## fake\n' + 'x' * 4000 + '\n```\n', 'Notes', 1000)

    def test_duplicate_canonical_refused(self):
        for name in ['A', 'B']:
            (self.section / f'{name}-Study-Notes.md').write_text('notes')
        with self.assertRaisesRegex(ValueError, 'one canonical'):
            hub.note_imports('1.1', self.section, 7600)

    def test_legacy_core_only_for_goodnotes(self):
        for suffix in ['Retrieval', 'Quiz', 'Core']:
            (self.section / f'N-Notes-{suffix}.md').write_text(suffix)
        self.assertEqual([code for _, code in hub.note_imports('1.1', self.section, 7600)],
                         ['Core\n'])

    def test_canonical_drops_quiz_why_and_retrieval_and_ignores_practice(self):
        (self.section / 'N-Study-Notes.md').write_text(
            '# 1.1 Core\nKeep this.\n\n# 1.1 Quiz why\nOfficial stem\n\n# 1.1 Retrieval\nPrompt\n')
        (self.section / 'Practice.md').write_text('> [!question]- Hidden\n> Answer\n')
        imported = hub.note_imports('1.1', self.section, 7600)
        self.assertEqual(imported, [('1.1 Notes', '# 1.1 Core\nKeep this.\n')])
        self.assertNotIn('Official', imported[0][1])
        self.assertNotIn('Prompt', imported[0][1])

    def test_extract_core_rejects_empty(self):
        with self.assertRaisesRegex(ValueError, 'no Core'):
            hub.extract_core('# 1.1 Retrieval\nOnly questions\n')

    def test_hub_json_writes_a_separate_english_panel(self):
        (self.kit / 'hub.json').write_text(json.dumps({
            'title': 'EN-221 English Kit',
            'editable_stem': 'English-Editable-GoodNotes',
            'preview_stem': 'English-Preview-GoodNotes',
            'prefix': 'English',
        }))
        (self.section / 'N-Study-Notes.md').write_text('# Core\nRead me\n')
        with patch.object(hub, 'check', side_effect=AssertionError('network forbidden')):
            with patch.object(sys, 'argv', ['hub', '--kit', str(self.kit), '--offline']):
                with contextlib.redirect_stdout(io.StringIO()):
                    hub.main()
        preview = (self.kit / 'English-Preview-GoodNotes.html').read_text()
        self.assertIn('EN-221 English Kit', preview)
        self.assertFalse((self.kit / 'Statistics-Preview-GoodNotes.html').exists())

    def test_hub_json_rejects_path_stem(self):
        (self.kit / 'hub.json').write_text(json.dumps({
            'title': 'X', 'editable_stem': '../escape', 'preview_stem': 'P', 'prefix': 'X'}))
        with self.assertRaisesRegex(ValueError, 'bare filename stem'):
            hub.load_hub_meta(self.kit)

    def test_hub_splits_retrieval_maps_from_legend_maps(self):
        (self.section / 'stats-1.1-concept-map.mmd').write_text('flowchart LR\nA --> B\n')
        (self.section / 'stats-1.1-decision-flow.mmd').write_text('flowchart TD\nA --> B\n')
        (self.section / 'stats-1.1-levels-flow.mmd').write_text('flowchart TD\nA --> B\n')
        (self.section / 'N-Study-Notes.md').write_text('# Core\nRead me\n\n# 1.1 Quiz why\nSkip\n')
        with patch.object(hub, 'check'):
            with patch.object(sys, 'argv', ['hub', '--kit', str(self.kit), '--offline']):
                with contextlib.redirect_stdout(io.StringIO()):
                    hub.main()
        preview = (self.kit / 'Statistics-Preview-GoodNotes.html').read_text()
        self.assertIn('Chapter 1.1 Retrieval maps', preview)
        self.assertIn('1.1 Quiz Sort', preview)
        self.assertIn('1.1 Concept Map', preview)
        self.assertIn('1.1 Levels', preview)
        self.assertIn('<summary>Unscheduled</summary>', preview)
        self.assertNotIn('# 1.1 Quiz why', preview)
        self.assertNotIn('\nSkip\n', preview)

    def test_hub_groups_buttons_under_week_sections(self):
        html = hub.render_hub(
            'T',
            [('Overall Map', '', 'https://example.com/o')],
            [
                (1, [('Chapter 1.1 maps', [('1.1 Concept Map', '', 'https://example.com/a')])]),
                (2, [('Chapter 2.1 maps', [('2.1 Concept Map', '', 'https://example.com/b')])]),
            ],
        )
        self.assertIn('href="#week-1"', html)
        self.assertIn('href="#week-2"', html)
        self.assertIn('<details class="week" id="week-1">', html)
        self.assertIn('<details class="week" open id="week-2">', html)
        self.assertIn('<summary>Week 1</summary>', html)
        self.assertIn('<summary>Week 2</summary>', html)
        self.assertLess(html.index('id="week-1"'), html.index('id="week-2"'))
        self.assertLess(html.index('1.1 Concept Map'), html.index('2.1 Concept Map'))
        self.assertNotIn('Unscheduled', html)

    def test_hub_prints_exact_goodnotes_destinations(self):
        html = hub.render_hub(
            'T',
            [('Overall Map', '', 'https://example.com/o')],
            [(3, [('Chapter 3.2 notes', [('3.2 Notes', '', 'https://example.com/n')])])],
            destinations={
                'Course-wide': 'Monroe University → 2026 Fall → MA-235 Statistics → 00 Course Overview',
                'Chapter 3.2 notes': 'Monroe University → 2026 Fall → MA-235 Statistics → Week 03 → 3.2 Measures of Variation → Notes',
            },
        )
        self.assertIn('Place in:', html)
        self.assertIn('Week 03 → 3.2 Measures of Variation → Notes', html)
        self.assertIn('00 Course Overview', html)

    def test_section_title_uses_state_and_has_safe_fallback(self):
        self.assertEqual(hub.section_title(self.section, '1.1'), '1.1')
        (self.section / 'state.json').write_text(json.dumps({
            'week': 1,
            'title': 'Data Basics & Levels',
        }))
        self.assertEqual(hub.section_title(self.section, '1.1'), 'Data Basics & Levels')

    def test_hub_meta_accepts_goodnotes_folder_names(self):
        (self.kit / 'hub.json').write_text(json.dumps({
            'goodnotes_root': 'Monroe University',
            'goodnotes_term': '2026 Fall',
            'goodnotes_course': 'EN-221 English',
        }))
        meta = hub.load_hub_meta(self.kit)
        self.assertEqual(meta['goodnotes_course'], 'EN-221 English')

    def test_kit_contract_requires_week_on_state(self):
        self.fill_live_contract()
        (self.section / 'state.json').write_text(json.dumps({'status': 'ready'}))
        errors = '\n'.join(validate.check_kit(self.kit))
        self.assertIn('positive integer week', errors)

    def test_collecting_refuses_live_build_and_preserves_output(self):
        (self.section / 'state.json').write_text(json.dumps({'status': 'collecting'}))
        published = self.kit / 'Statistics-Editable-GoodNotes.html'
        published.write_text('published')
        with patch.object(sys, 'argv', ['hub', '--kit', str(self.kit)]):
            with self.assertRaisesRegex(ValueError, 'collecting'):
                hub.main()
        self.assertEqual(published.read_text(), 'published')

    def test_offline_preview_never_calls_network_or_replaces_live(self):
        (self.section / 'state.json').write_text(json.dumps({'status': 'partial'}))
        (self.section / 'N-Study-Notes.md').write_text('# Notes\nRead me')
        published = self.kit / 'Statistics-Editable-GoodNotes.html'
        published.write_text('published')
        with patch.object(hub, 'check', side_effect=AssertionError('network forbidden')):
            with patch.object(sys, 'argv', ['hub', '--kit', str(self.kit), '--offline']):
                with contextlib.redirect_stdout(io.StringIO()):
                    hub.main()
        self.assertEqual(published.read_text(), 'published')
        preview = (self.kit / 'Statistics-Preview-GoodNotes.html').read_text()
        self.assertIn('Unverified preview', preview)
        self.assertIn('1.1 Notes', preview)
        self.assertFalse((self.section / 'imports').exists())

    def test_network_failure_preserves_published_output(self):
        self.fill_live_contract()
        published = self.kit / 'T-Editable-GoodNotes.html'
        published.write_text('published')
        with patch.object(hub, 'check', side_effect=OSError('offline')):
            with patch.object(sys, 'argv', ['hub', '--kit', str(self.kit)]):
                with contextlib.redirect_stdout(io.StringIO()):
                    with self.assertRaises(OSError):
                        hub.main()
        self.assertEqual(published.read_text(), 'published')

    def test_map_hub_remaining_does_not_hide_removed_branch(self):
        previous, candidate = self.kit / 'old.mmd', self.kit / 'new.mmd'
        previous.write_text('flowchart LR\nS --> CH1_1\nCH1_1 --> VAR\nVAR("Variable")\n')
        candidate.write_text('flowchart LR\nS --> CH1_1\nVAR("Variable")\n')
        self.assertEqual(validate.check_map(previous, candidate), ['CH1_1 --> VAR'])
        candidate.write_text(previous.read_text() + 'S --> CH1_2\n')
        self.assertEqual(validate.check_map(previous, candidate), [])

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
            'title': 'Wrong', 'editable_stem': 'Statistics-Editable-GoodNotes',
            'preview_stem': 'P', 'prefix': 'Statistics'}))
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

    def fill_live_contract(self):
        (self.kit / 'hub.json').write_text(json.dumps({
            'title': 'T', 'editable_stem': 'T-Editable-GoodNotes',
            'preview_stem': 'T-Preview-GoodNotes', 'prefix': 'T',
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

    def test_missing_goodnotes_course_falls_back_to_own_prefix(self):
        (self.kit / 'hub.json').write_text(json.dumps({'prefix': 'IT'}))
        self.assertEqual(hub.load_hub_meta(self.kit)['goodnotes_course'], 'IT')

    def test_map_label_drops_any_course_tag(self):
        for name in ('it-3.1-address-flow.mmd', 'stats-3.1-address-flow.mmd', '3.1-address-flow.mmd'):
            self.assertEqual(hub.map_label('3.1', Path(name)), '3.1 Address')
        self.assertEqual(hub.map_label('3.1', Path('it-3.1-secure-lan-flow.mmd')), '3.1 Secure Lan')

    def test_section_folder_name_never_repeats_number(self):
        self.assertEqual(hub.section_folder_name('1.1', '1.1'), '1.1')
        self.assertEqual(hub.section_folder_name('1.1', ''), '1.1')
        self.assertEqual(hub.section_folder_name('3.2', '3.2 Variation'), '3.2 Variation')
        self.assertEqual(hub.section_folder_name('3.2', 'Variation'), '3.2 Variation')

    def test_state_requires_status_coverage_and_title(self):
        self.fill_live_contract()
        (self.section / 'state.json').write_text(json.dumps({
            'status': 'done', 'week': 1, 'coverage': 'most'}))
        errors = '\n'.join(validate.check_kit(self.kit))
        self.assertIn('status must be one of', errors)
        self.assertIn('coverage must be one of', errors)
        self.assertIn('human title', errors)

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

    def test_import_changes_ignore_random_claim_id(self):
        old = {'Map': hub.mermaid_url('flowchart LR\nA', 'Map'),
               'Notes': hub.markdown_url('one', 'Notes'),
               'Gone': hub.markdown_url('x', 'Gone')}
        new = {'Map': hub.mermaid_url('flowchart LR\nA', 'Map'),
               'Notes': hub.markdown_url('two', 'Notes'),
               'Added': hub.markdown_url('y', 'Added')}
        self.assertNotEqual(old['Map'], new['Map'])
        link_txt = ''.join(f'{name}:\n{url}\n\n' for name, url in old.items())
        self.assertEqual(hub.parse_link_txt(link_txt), old)
        self.assertEqual(hub.import_changes(old, new),
                         {'new': ['Added'], 'changed': ['Notes'], 'removed': ['Gone']})

    def test_live_rebuild_reports_only_changed_imports(self):
        self.fill_live_contract()
        with patch.object(hub, 'check'):
            with patch.object(sys, 'argv', ['hub', '--kit', str(self.kit)]):
                with contextlib.redirect_stdout(io.StringIO()) as first:
                    hub.main()
                self.assertIn('every button is a first import', first.getvalue())
                html = (self.kit / 'T-Editable-GoodNotes.html').read_text()
                self.assertIn('Week 01 → 1.1 Data Basics → Map', html)
                with contextlib.redirect_stdout(io.StringIO()) as second:
                    hub.main()
                self.assertIn('nothing to re-import', second.getvalue())
                (self.section / 'N-Study-Notes.md').write_text('# Core\nRevised\n')
                with contextlib.redirect_stdout(io.StringIO()) as third:
                    hub.main()
                self.assertIn('Changed imports: 1.1 Notes', third.getvalue())

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
        parts = dict(hub.split_overall(self.OVERALL))
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
            hub.split_overall(self.OVERALL + '  subgraph X\n')
        with self.assertRaisesRegex(ValueError, 'fewer than two chapters'):
            hub.split_overall('flowchart LR\n  S(["S"])\n  S --> CH1_1\n')

    def test_oversized_overall_map_becomes_chapter_buttons(self):
        self.fill_live_contract()
        (self.kit / 'overall-flow.mmd').write_text(self.OVERALL)
        whole = len(hub.mermaid_url(self.OVERALL, 'T Overall Map'))
        with patch.object(hub, 'check'):
            with patch.object(sys, 'argv', ['hub', '--kit', str(self.kit),
                                            '--max-url-chars', str(whole - 1)]):
                with contextlib.redirect_stdout(io.StringIO()) as out:
                    hub.main()
        self.assertIn('splitting it by chapter', out.getvalue())
        links = (self.kit / 'T-Editable-GoodNotes-link.txt').read_text()
        self.assertIn('Overall Map Ch 1:', links)
        self.assertIn('Overall Map Ch 2:', links)
        self.assertNotIn('Overall Map:', links)

    def test_live_hub_refuses_incomplete_kit(self):
        with patch.object(sys, 'argv', ['hub', '--kit', str(self.kit)]):
            with self.assertRaisesRegex(ValueError, 'Kit contract failed'):
                hub.main()

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


if __name__ == '__main__':
    unittest.main()
