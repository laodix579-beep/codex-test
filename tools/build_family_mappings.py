"""Append C04 reviewed meaning spans and optional groups; keep source text intact."""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
words = [r for p in sorted((ROOT / 'data/family-daily').glob('0*.json'))
         for r in json.loads(p.read_text())['items']]
overrides = {
    'C04-S01-004': ['妈妈'], 'C04-S01-006': ['爸爸'],
    'C04-S01-008': ['哥哥／弟弟'], 'C04-S01-009': ['姐姐／妹妹'],
    'C04-S01-010': ['兄弟姐妹'], 'C04-S01-021': ['奶奶／外婆'],
    'C04-S01-022': ['奶奶／外婆'], 'C04-S01-023': ['爷爷／外公'],
    'C04-S01-024': ['爷爷／外公'], 'C04-S01-025': ['姨妈／姑妈'],
    'C04-S01-026': ['叔叔／舅舅'],
    'C04-S03-003': ['杯'], 'C04-S03-007': ['餐具'],
    'C04-S03-023': ['烘干机'],
    'C04-S04-002': ['起'], 'C04-S04-004': ['刷', '牙'],
    'C04-S04-011': ['脱'], 'C04-S04-013': ['准备'],
    'C04-S04-016': ['吃晚饭'], 'C04-S04-031': ['摆好', '餐具'],
    'C04-S04-035': ['把洗好的衣服晾'], 'C04-S04-036': ['把它们叠好'],
    'C04-S04-037': ['扫', '地'], 'C04-S04-041': ['把垃圾拿出去'],
    'C04-S04-044': ['散步'], 'C04-S04-050': ['睡着'],
    'C04-S04-051': ['睡眠'], 'C04-S04-055': ['早上'],
    'C04-S04-056': ['下午'], 'C04-S04-057': ['晚上'],
    'C04-S04-058': ['晚上'], 'C04-S04-059': ['前'],
    'C04-S04-060': ['后'],
}
usage = {
    'C04-S04-053': 'stay up late 在本句中整体译为“熬夜”；late 表示“到很晚”，中文通常不把它单独翻译，不需要再补一个“晚”。',
}
notes = {
    'C04-S03-003': 'a glass of water 表示一杯水；glass 在这里以容器表示份量，中文译为“杯”。',
    'C04-S03-007': 'dishes 在这里泛指餐具，而不是“一道菜”；洗餐具也常说洗碗。',
    'C04-S04-002': 'get up 表示起床；本句“起得很早”中的“早”对应已给出的 early。',
    'C04-S04-004': '刷……牙对应 brush my teeth；两次对应已给出的 twice，中文不必逐字译出 my。',
    'C04-S04-031': 'set the table 表示摆放餐具；晚餐对应已给出的 for dinner。',
    'C04-S04-036': '本句用“它们”指前面的衣服，fold the clothes 表示把衣服叠好。',
    'C04-S04-051': 'sleep 在本例句中是名词，表示睡眠；原词义“睡觉”保留。',
}
entries = []
for w in words:
    candidates = [re.sub(r'[（(].*?[)）]', '', s).strip(' 。！？；')
                  for s in re.split('[；;]', w['chinese'])]
    matches = sorted((s for s in candidates if s and s in w['example_zh']), key=len, reverse=True)
    texts = overrides.get(w['id'], matches[:1])
    spans, cursor = [], 0
    if w['id'] not in usage:
        assert texts, (w['id'], w['chinese'], w['example_zh'])
        for text in texts:
            start = w['example_zh'].index(text, cursor)
            spans.append({'start': start, 'end': start + len(text), 'text': text})
            cursor = start + len(text)
    entries.append({'id': w['id'], 'word': w['english'], 'meaning': w['chinese'],
                    'english': w['example_en'], 'chinese': w['example_zh'],
                    'mode': 'aligned' if spans else 'usage', 'spans': spans,
                    'usage': usage.get(w['id'], ''), 'note': notes.get(w['id'], '')})
path = ROOT / 'data/meaning-catalog.json'
catalog = json.loads(path.read_text())
catalog['entries'] = [r for r in catalog['entries'] if not r['id'].startswith('C04-')] + entries
path.write_text(json.dumps(catalog, ensure_ascii=False, indent=2) + '\n')

def span(a, b):
    return list(range(a, b + 1))

definitions = [
    [('family-introductions', '父母与家庭介绍', span(1, 7) + span(31, 33)),
     ('children-siblings', '孩子与兄弟姐妹', span(8, 19) + [29, 30]),
     ('grandparents', '祖辈称呼', span(20, 24)),
     ('relatives', '其他亲属', span(25, 28))],
    [('rooms-spaces', '房间与空间', span(1, 17)),
     ('fixed-features', '门窗与固定设施', span(18, 22) + [44]),
     ('tables-seats-beds', '桌椅与床', span(23, 30)),
     ('bedding-storage', '寝具与收纳', span(31, 38)),
     ('lights-decoration', '灯饰与装饰', span(39, 43))],
    [('tableware-containers', '餐具与容器', span(1, 11)),
     ('kitchen-cooking', '厨房烹饪', span(12, 18)),
     ('home-appliances', '家用电器', span(19, 30)),
     ('personal-care', '洗漱护理', span(31, 37)),
     ('cleaning-laundry', '清洁与衣物', span(38, 48)),
     ('repair-first-aid', '维修与应急', span(49, 53))],
    [('wake-up-care', '起床与洗漱', span(1, 13)),
     ('meals-travel', '用餐与往返', span(14, 21)),
     ('study-play', '学习与娱乐', span(22, 28)),
     ('chores-care', '家务与照料', span(29, 41)),
     ('outings-rest', '出行与休息', span(42, 51)),
     ('time-sequence', '时间与顺序', span(52, 64)),
     ('routine-phrases', '作息交流句型', span(65, 70))],
]
path = ROOT / 'data/practice-groups.json'
catalog = json.loads(path.read_text())
catalog['subcategories'] = [r for r in catalog['subcategories'] if not r['subcategoryId'].startswith('C04-')]
for index, groups in enumerate(definitions, 1):
    prefix = f'C04-S{index:02}'
    catalog['subcategories'].append({'subcategoryId': prefix, 'groups': [
        {'id': key, 'name': name, 'wordIds': [f'{prefix}-{i:03}' for i in indices]}
        for key, name, indices in groups]})
path.write_text(json.dumps(catalog, ensure_ascii=False, indent=2) + '\n')
print('Reviewed 200 C04 meanings; defined 22 optional groups in four existing entrances.')
