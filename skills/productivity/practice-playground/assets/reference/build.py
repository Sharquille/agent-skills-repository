#!/usr/bin/env python3
"""Build Playground.html (the Card Desk playground) from the story sources.

Reads ../story/story_cards.py (45 reviewed cards), ../story/mock.py (follow-ups, opener, STAR)
and ../story/story.html (the ten "If they ask" answers, recall blocks, questions to ask),
then inlines styles.css, content.js and engine.js into shell.html.
"""
import html, json, re, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
STORY = HERE.parent / 'story'
OUT = HERE.parent.parent / 'Playground.html'   # local copy, opens offline
ART = HERE / 'dist' / 'card-desk.html'                               # artifact source (no skeleton)
sys.path.insert(0, str(STORY))
from story_cards import CARDS  # noqa: E402
import mock  # noqa: E402

src = (STORY / 'story.html').read_text()
clean = lambda s: html.unescape(re.sub(r'<[^>]+>', '', s)).strip()

say = {}
for ch, (q, a) in enumerate(re.findall(r'<div class="say"><div class="q">If they ask: "(.*?)"</div>\s*<p>"(.*?)"</p></div>', src, re.S), 1):
    say[ch] = {'q': clean(q), 'a': clean(a)}
assert len(say) == 10, len(say)

recall = {}
for ch, blk in enumerate(re.findall(r'<div class="recall">(.*?)</div>', src, re.S), 1):
    parts = dict((clean(k), clean(v)) for k, v in re.findall(r'<b>(.*?)</b><span>(.*?)</span>', blk))
    recall[ch] = {'remember': parts['Remember'], 'picture': parts['Picture it'], 'use': parts['Use it']}
assert len(recall) == 10, len(recall)

ask_block = re.search(r'Questions to ask the panel</h3>\s*<ul>(.*?)</ul>', src, re.S).group(1)
ask = [clean(x) for x in re.findall(r'<li>(.*?)</li>', ask_block, re.S)]
assert len(ask) == 3, ask

base = {
    'cards': [{'id': i, 'ch': ch, 'q': q, 'opts': opts, 'why': why} for i, ch, q, opts, why in CARDS],
    'say': say, 'recall': recall, 'ask': ask,
    'follow': {ch: list(v) for ch, v in mock.FOLLOW.items()},
    'opener': list(mock.OPENER), 'star': mock.STAR, 'starPoints': mock.STAR_POINTS,
}
assert len(base['cards']) == 45

shell = (HERE / 'shell.html').read_text()
page = (shell.replace('/*STYLES*/', (HERE / 'styles.css').read_text())
             .replace('/*BASE*/null', json.dumps(base, ensure_ascii=False).replace('</', '<\\/'))
             .replace('/*CONTENT*/', (HERE / 'content.js').read_text())
             .replace('/*ENGINE*/', (HERE / 'engine.js').read_text()))
ART.parent.mkdir(exist_ok=True)
ART.write_text(page)
OUT.write_text('<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover"></head><body>' + page + '</body></html>')
print(f'{OUT.name}: {len(page):,} bytes, {len(base["cards"])} cards, {len(say)} answers')
