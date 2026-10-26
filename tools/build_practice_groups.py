"""Validate optional practice sections and embed them without changing words."""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
path = ROOT / 'index.html'
html = path.read_text()
start = html.index('window.FROG_WORD_CATALOG = ') + len('window.FROG_WORD_CATALOG = ')
words = json.JSONDecoder().raw_decode(html[start:])[0]['words']
catalog = json.loads((ROOT / 'data/practice-groups.json').read_text())
assert len({r['subcategoryId'] for r in catalog['subcategories']}) == len(catalog['subcategories'])
for section in catalog['subcategories']:
    groups = section['groups']
    assert len(groups) >= 2
    assert len({g['id'] for g in groups}) == len(groups)
    assert all(re.fullmatch(r'[a-z0-9-]+', g['id']) and g['id'] not in ('all', 'other') and g['name'] for g in groups)
    ids = [i for group in groups for i in group['wordIds']]
    expected = {w['id'] for w in words if w['subcategoryId'] == section['subcategoryId']}
    assert len(ids) == len(set(ids)) and set(ids) == expected, section['subcategoryId']
script = '<script id="practice-group-library">\nwindow.FROG_PRACTICE_GROUPS=' + json.dumps(catalog, ensure_ascii=False, separators=(',', ':')).replace('<', '\\u003c') + ';\n</script>\n'
pattern = r'<script id="practice-group-library">.*?</script>\s*'
if re.search(pattern, html, re.S):
    html = re.sub(pattern, lambda _: script, html, count=1, flags=re.S)
else:
    marker = '<script data-embedded-audio="">'
    assert marker in html
    html = html.replace(marker, script + marker, 1)
path.write_text(html)
print('Validated and embedded', len(catalog['subcategories']), 'composite subcategories; all other entries stay direct.')
