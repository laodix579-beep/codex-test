"""Review C06 Chinese targets and balanced sections in the existing UI slots."""
import json
import re
from pathlib import Path
from animal_content import study_word

ROOT = Path(__file__).resolve().parents[1]
words = [w for p in sorted((ROOT / 'data/animal-nature').glob('0*.json'))
         for w in json.loads(p.read_text())['items']]
overrides = {
    'C06-S01-011': ['宠物鼠'], 'C06-S01-027': ['毛'],
    'C06-S01-029': ['笼'], 'C06-S01-031': ['宠物碗'], 'C06-S01-038': ['喂'],
    'C06-S04-035': ['腕'], 'C06-S05-005': ['叶'], 'C06-S05-006': ['树叶'],
    'C06-S06-020': ['岛'],
}
usage = {'C06-S05-023': 'poppy 指罂粟花或虞美人；本句中文用“一朵红花”概括该花，不能把所有红花都叫作 poppy。请结合完整英文例句填写。'}
notes = {
    'C06-S01-011': 'rat 是体型较大的鼠；本句用“宠物鼠”表达，注意与 mouse 区分。',
    'C06-S01-016': 'budgie 是虎皮鹦鹉的英式常用名称；单词保留源词形，朗读使用 GA。',
    'C06-S01-033': 'lead 在本句中指牵引绳，读 /liːd/，不是金属铅 /led/。',
    'C06-S02-012': 'kid 在本句中是小山羊，不是人类小孩。',
    'C06-S04-035': '源词使用 tentacle（触手）；章鱼的附肢在本例句中文译为“腕”。',
    'C06-S05-005': 'leaf 为单数；leaves 为复数，本题按例句实际词形填写。',
    'C06-S05-006': 'leaves 是 leaf 的复数；本句指多片树叶。',
    'C06-S06-016': 'wood 在本句中指树林，不是木材。',
}
entries = []
for w in words:
    candidates = [re.sub(r'[（(].*?[)）]', '', s).strip(' 。！？；') for s in re.split('[；;]', w['chinese'])]
    matches = sorted((s for s in candidates if s and s in w['example_zh']), key=len, reverse=True)
    targets = overrides.get(w['id'], matches[:1]); spans = []; cursor = 0
    if w['id'] not in usage:
        assert targets, (w['id'], w['chinese'], w['example_zh'])
        for text in targets:
            start = w['example_zh'].index(text, cursor)
            spans.append({'start': start, 'end': start + len(text), 'text': text}); cursor = start + len(text)
    entries.append({'id': w['id'], 'word': study_word(w), 'meaning': w['chinese'],
                    'english': w['example_en'], 'chinese': w['example_zh'],
                    'mode': 'aligned' if spans else 'usage', 'spans': spans,
                    'usage': usage.get(w['id'], ''), 'note': notes.get(w['id'], '')})
path = ROOT / 'data/meaning-catalog.json'; catalog = json.loads(path.read_text())
catalog['entries'] = [r for r in catalog['entries'] if not r['id'].startswith('C06-')] + entries
path.write_text(json.dumps(catalog, ensure_ascii=False, indent=2) + '\n')
windows = json.loads((ROOT / 'data/animal-nature-windows.json').read_text())['windows']
definition = json.loads((ROOT / 'data/animal-nature-practice-sections.json').read_text())
sections = definition['subcategories']
assert definition['groupSizePolicy'] == {'min': 10, 'max': 25}
assert {s['subcategoryId'] for s in sections} == {w['subcategoryId'] for w in windows}
for section in sections:
    window = next(w for w in windows if w['subcategoryId'] == section['subcategoryId'])
    expected = {i for group in window['groups'] for i in group['wordIds']}
    actual = [i for group in section['groups'] for i in group['wordIds']]
    assert len(actual) == len(set(actual)) and set(actual) == expected
    assert all(10 <= len(g['wordIds']) <= 25 for g in section['groups'])
path = ROOT / 'data/practice-groups.json'; catalog = json.loads(path.read_text())
catalog['subcategories'] = [r for r in catalog['subcategories'] if not r['subcategoryId'].startswith('C06-')] + sections
path.write_text(json.dumps(catalog, ensure_ascii=False, indent=2) + '\n')
print('Reviewed 238 meaning targets and 15 balanced practice sections in four C06 entrances.')
