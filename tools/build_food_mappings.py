"""Reviewed C05 meanings; curated practice sections within four existing entrances."""
import json
import re
from pathlib import Path
from food_content import study_word

ROOT = Path(__file__).resolve().parents[1]
words = [r for p in sorted((ROOT / 'data/food-health').glob('0*.json'))
         for r in json.loads(p.read_text())['items']]
overrides = {
    'C05-S01-031': ['籽'], 'C05-S03-004': ['面'], 'C05-S03-012': ['蛋'],
    'C05-S03-027': ['汉堡'], 'C05-S03-041': ['一顿', '饭'],
    'C05-S04-015': ['热巧克力'], 'C05-S04-026': ['口渴'],
    'C05-S05-015': ['牙'], 'C05-S05-016': ['牙'], 'C05-S05-028': ['胸'],
    'C05-S05-030': ['肚子'], 'C05-S06-001': ['健康'],
    'C05-S06-002': ['不舒服'], 'C05-S06-003': ['恶心'],
    'C05-S06-004': ['不舒服'], 'C05-S06-019': ['累'], 'C05-S06-020': ['困'],
    'C05-S06-021': ['饿'], 'C05-S06-022': ['口渴'], 'C05-S06-023': ['热'],
    'C05-S06-024': ['冷'], 'C05-S06-025': ['头晕'], 'C05-S06-041': ['好起来'],
}
usage = {'C05-S05-014': 'a smile on her lips 在本句中整体表示“嘴角带着微笑”；lip 本义是嘴唇，例句使用复数 lips。'}
notes = {
    'C05-S03-004': '蔬菜面里的“面”对应 noodles，蔬菜对应已给出的 vegetables。',
    'C05-S03-012': '水煮蛋里的“蛋”对应 egg；水煮对应已给出的 boiled。',
    'C05-S03-041': 'meal 在本句中表示“一顿饭”；中间的“健康的”对应已给出的 healthy。',
    'C05-S05-015': 'baby tooth 表示乳牙；tooth 指单颗牙齿，teeth 是复数。',
    'C05-S05-026': 'thumb 表示拇指；例句 thumbs-up 整体表示竖拇指的手势，沿用单词拼写练习，不把复合表达当成单词原型。',
    'C05-S05-028': 'on his chest 在本句中译为在他的胸前；chest 本义是胸部。',
    'C05-S06-024': '原词库括号 feeling 为词义标签，用于区分冷的感觉与感冒；实际学习和发音是 cold。',
}
entries = []
for w in words:
    candidates = [re.sub(r'[（(].*?[)）]', '', s).strip(' 。！？；') for s in re.split('[；;]', w['chinese'])]
    matches = sorted((s for s in candidates if s and s in w['example_zh']), key=len, reverse=True)
    texts = overrides.get(w['id'], matches[:1]);spans, cursor = [], 0
    if w['id'] not in usage:
        assert texts, (w['id'], w['chinese'], w['example_zh'])
        for text in texts:
            start = w['example_zh'].index(text, cursor)
            spans.append({'start': start, 'end': start + len(text), 'text': text});cursor = start + len(text)
    entries.append({'id': w['id'], 'word': study_word(w), 'meaning': w['chinese'],
                    'english': w['example_en'], 'chinese': w['example_zh'],
                    'mode': 'aligned' if spans else 'usage', 'spans': spans,
                    'usage': usage.get(w['id'], ''), 'note': notes.get(w['id'], '')})
path = ROOT / 'data/meaning-catalog.json';catalog = json.loads(path.read_text())
catalog['entries'] = [r for r in catalog['entries'] if not r['id'].startswith('C05-')] + entries
path.write_text(json.dumps(catalog, ensure_ascii=False, indent=2) + '\n')
windows = json.loads((ROOT / 'data/food-health-windows.json').read_text())['windows']
path = ROOT / 'data/practice-groups.json';catalog = json.loads(path.read_text())
catalog['subcategories'] = [r for r in catalog['subcategories'] if not r['subcategoryId'].startswith('C05-')]
definition = json.loads((ROOT / 'data/food-health-practice-sections.json').read_text())
sections = definition['subcategories']
size = definition['groupSizePolicy']
assert size == {'min': 10, 'max': 25}
assert all(size['min'] <= len(g['wordIds']) <= size['max'] for section in sections for g in section['groups'])
assert {s['subcategoryId'] for s in sections} == {w['subcategoryId'] for w in windows}
for section in sections:
    window = next(w for w in windows if w['subcategoryId'] == section['subcategoryId'])
    expected = {i for group in window['groups'] for i in group['wordIds']}
    actual = [i for group in section['groups'] for i in group['wordIds']]
    assert len(actual) == len(set(actual)) and set(actual) == expected
    catalog['subcategories'].append(section)
path.write_text(json.dumps(catalog, ensure_ascii=False, indent=2) + '\n')
print('Reviewed 218 meanings;', sum(len(s['groups']) for s in sections), 'practice sections across all four C05 entrances.')
