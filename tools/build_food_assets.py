"""Append the C05 four-window pack without replacing old words or UI slots."""
import hashlib
import json
from pathlib import Path
from food_content import UI_SUBCATEGORIES, study_word

ROOT = Path(__file__).resolve().parents[1]
directory = ROOT / 'data/food-health'
index = json.loads((directory / 'index.json').read_text())
assert index['category_id'] == 'C05' and index['window_count'] == 4
words, sources, windows = [], [], []
for window in index['windows']:
    path = directory / window['filename']
    group = json.loads(path.read_text())
    assert group['window_id'] == window['window_id']
    assert len(group['items']) == window['item_count'] == group['window_item_count']
    ui_id = UI_SUBCATEGORIES[window['window_id']]
    sources.append({'path': path.relative_to(ROOT).as_posix(), 'sha256': hashlib.sha256(path.read_bytes()).hexdigest(), 'count': len(group['items'])})
    parts = []
    for sub in window['subcategories']:
        items = [w for w in group['items'] if w['subcategory_id'] == sub['id']]
        assert len(items) == sub['item_count']
        assert [w['sort_order'] for w in items] == list(range(1, len(items) + 1))
        parts.append({'sourceSubcategoryId': sub['id'], 'name': sub['name'], 'wordIds': [w['id'] for w in items]})
    assert sum(len(s['wordIds']) for s in parts) == len(group['items'])
    windows.append({'windowId': window['window_id'], 'subcategoryId': ui_id,
                    'name': window['window_name'], 'groups': parts})
    for row in group['items']:
        assert row['category_id'] == 'C05'
        words.append({'id': row['id'], 'word': study_word(row), 'meaning': row['chinese'],
                      'ipa': row['ipa_dj_british'], 'example': row['example_en'],
                      'exampleZh': row['example_zh'], 'categoryId': 'C05', 'subcategoryId': ui_id,
                      'itemType': 'word' if row['item_type'] == 'word' else 'phrase',
                      'level': row.get('level', 1), 'notes': row.get('notes', '')})
assert len(words) == index['item_count'] == len({w['id'] for w in words}) == 218
path = ROOT / 'index.html';html = path.read_text()
marker = 'window.FROG_WORD_CATALOG = ';start = html.index(marker) + len(marker)
catalog, size = json.JSONDecoder().raw_decode(html[start:])
assert catalog['version'] == 'basic-us-v1'
catalog['words'] = [w for w in catalog['words'] if w.get('categoryId') != 'C05'] + words
category = next(c for c in catalog['categories'] if c['id'] == 'C05')
category['subcategories'] = [{'id': w['subcategoryId'], 'name': w['name']} for w in windows]
pack = {'id': 'food-health-v1', 'categoryId': 'C05', 'wordIds': [w['id'] for w in words], 'sources': sources}
catalog['packs'] = [p for p in catalog.get('packs', []) if p['id'] != pack['id']] + [pack]
path.write_text(html[:start] + json.dumps(catalog, ensure_ascii=False, separators=(',', ':')).replace('<', '\\u003c') + html[start + size:])
(ROOT / 'data/catalog-packs.json').write_text(json.dumps({'packs': catalog['packs']}, ensure_ascii=False, indent=2) + '\n')
(ROOT / 'data/food-health-windows.json').write_text(json.dumps({'pack': pack['id'], 'windows': windows,
    'studyWordAdaptations': [{'id': 'C05-S06-024', 'sourceEnglish': 'cold (feeling)', 'studyEnglish': 'cold',
                             'reason': '括号为词义消歧标签；实际朗读与填空使用 cold，词义仍保留冷的感觉。'}]}, ensure_ascii=False, indent=2) + '\n')
print(json.dumps({'total': len(catalog['words']), 'added': 218, 'windows': [len([w for w in words if w['subcategoryId'] == ui]) for ui in UI_SUBCATEGORIES.values()]}))
