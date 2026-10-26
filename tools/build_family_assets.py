"""Build the existing vocabulary bundle from four independent C04 JSON files."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
directory = ROOT / 'data/family-daily'
index = json.loads((directory / 'index.json').read_text())
assert index['category_id'] == 'C04' and index['subcategory_count'] == 4
words = []
sources = []
for sub in index['subcategories']:
    path = directory / sub['filename']
    group = json.loads(path.read_text())
    assert group['subcategory_id'] == sub['id'] and len(group['items']) == sub['item_count']
    assert [w['sort_order'] for w in group['items']] == list(range(1, len(group['items']) + 1))
    sources.append({'path': path.relative_to(ROOT).as_posix(), 'sha256': hashlib.sha256(path.read_bytes()).hexdigest(), 'count': len(group['items'])})
    for row in group['items']:
        assert row['category_id'] == 'C04' and row['subcategory_id'] == sub['id']
        # Whole-sentence entries use the existing phrase controls; raw source
        # files retain their original item_type without adding a new UI mode.
        words.append({'id': row['id'], 'word': row['english'], 'meaning': row['chinese'], 'ipa': row['ipa_dj_british'], 'example': row.get('example_en', ''), 'exampleZh': row.get('example_zh', ''), 'categoryId': 'C04', 'subcategoryId': sub['id'], 'itemType': 'word' if row.get('item_type', 'word') == 'word' else 'phrase', 'level': row.get('level', 1), 'notes': row.get('notes', '')})
assert len(words) == index['item_count'] == 200 and len({w['id'] for w in words}) == 200
html = (ROOT / 'index.html').read_text()
marker = 'window.FROG_WORD_CATALOG = '
start = html.index(marker) + len(marker)
catalog, size = json.JSONDecoder().raw_decode(html[start:])
assert catalog['version'] == 'basic-us-v1'  # Do not trigger the old replacement migration.
catalog['words'] = [w for w in catalog['words'] if w.get('categoryId') != 'C04'] + words
category = next(c for c in catalog['categories'] if c['id'] == 'C04')
category['subcategories'] = [{'id': s['id'], 'name': s['name']} for s in index['subcategories']]
pack = {'id': 'family-daily-v1', 'categoryId': 'C04', 'wordIds': [w['id'] for w in words], 'sources': sources}
catalog['packs'] = [p for p in catalog.get('packs', []) if p['id'] != pack['id']] + [pack]
(ROOT / 'index.html').write_text(html[:start] + json.dumps(catalog, ensure_ascii=False, separators=(',', ':')).replace('<', '\\u003c') + html[start + size:])
(ROOT / 'data/catalog-packs.json').write_text(json.dumps({'packs': catalog['packs']}, ensure_ascii=False, indent=2) + '\n')
print(json.dumps({'total': len(catalog['words']), 'addedPack': len(words), 'subcategories': [s['item_count'] for s in index['subcategories']]}))
