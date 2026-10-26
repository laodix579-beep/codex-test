"""Validate and embed reviewed Chinese meaning spans; keep source words intact."""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
catalog = json.loads((ROOT / 'data/meaning-catalog.json').read_text())
words = [w for group in json.loads((ROOT / 'data/basic-vocabulary.json').read_text())['subcategories'] for w in group['items']]
for folder in ['time-nature', 'school-learning']:
    for file in sorted((ROOT / 'data' / folder).glob('0*.json')):
        words.extend(json.loads(file.read_text())['items'])
assert len(catalog['entries']) == len(words)
assert {row['id'] for row in catalog['entries']} == {w['id'] for w in words}
for row, word in zip(catalog['entries'], words):
    assert (row['word'], row['meaning'], row['english'], row['chinese']) == (word['english'], word['chinese'], word['example_en'], word['example_zh'])
    end = 0
    for span in row['spans']:
        assert end <= span['start'] < span['end'] <= len(row['chinese'])
        assert row['chinese'][span['start']:span['end']] == span['text']
        end = span['end']
    assert row['mode'] == ('aligned' if row['spans'] else 'usage')
    assert row['mode'] != 'usage' or row['usage']
html = (ROOT / 'index.html').read_text()
html = re.sub(r'<script id="meaning-library">[\s\S]*?</script>\n?', '', html)
script = '<script id="meaning-library">\nwindow.FROG_MEANING_LIBRARY=' + json.dumps(catalog, ensure_ascii=False, separators=(',', ':')).replace('<', '\\u003c') + ';\n</script>\n'
marker = '<script data-embedded-audio="">'
assert html.count(marker) == 1
(ROOT / 'index.html').write_text(html.replace(marker, script + marker))
print(f"Embedded {len(catalog['entries'])} reviewed sentence meaning mappings")
