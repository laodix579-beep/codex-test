"""Append reviewed C03 meaning alignments and existing-style practice groups.

Source vocabulary remains unchanged. Non-literal Chinese translations receive
usage notes rather than invented word-for-word correspondences.
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
words = [r for p in sorted((ROOT / 'data/school-learning').glob('0*.json'))
         for r in json.loads(p.read_text())['items']]
overrides = {
    'C03-S02-035': ['地面'],
    'C03-S03-011': ['计算机课'], 'C03-S03-012': ['计算机课'],
    'C03-S03-015': ['宗教教育课'], 'C03-S03-016': ['设计与技术课'],
    'C03-S03-017': ['现代外语'], 'C03-S03-021': ['字迹'],
    'C03-S03-025': ['家政课'],
    'C03-S04-006': ['读'], 'C03-S04-007': ['说'],
    'C03-S04-012': ['数'], 'C03-S04-016': ['在', '下面画线'],
    'C03-S04-026': ['给', '看'], 'C03-S04-028': ['涂成'],
    'C03-S04-030': ['贴'], 'C03-S04-031': ['折'],
    'C03-S04-047': ['注意'], 'C03-S04-048': ['试着做'],
    'C03-S04-050': ['做得很好'], 'C03-S04-053': ['课题'],
    'C03-S04-054': ['任务要求'], 'C03-S04-057': ['错'],
    'C03-S04-058': ['题'], 'C03-S04-062': ['组'],
    'C03-S04-066': ['课间休息'], 'C03-S04-069': ['成绩'],
    'C03-S04-072': ['准备好'], 'C03-S04-074': ['你能帮我看看', '吗'],
    'C03-S04-079': ['请再', '说一遍'],
}
usage = {'C03-S04-032': 'open 在这里用于翻书指令；整句译为“把书翻到第十页”，中文没有逐字单独译出“打开”。'}
notes = {
    'C03-S04-006': 'say the word 在本句中译为“读这个单词”；词义仍保留“说；讲”。',
    'C03-S04-028': 'colour 在本句中是动词，表示涂色；黄色对应句中已给出的 yellow。',
    'C03-S04-031': 'fold 表示“折”，in half 表示“对半”；词义仍保留“折叠”。',
    'C03-S04-058': 'problem 在这道练习的中文例句中译为“题”。',
    'C03-S04-069': 'mark 在本句中指老师给出的成绩。',
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
catalog['entries'] = [r for r in catalog['entries'] if not r['id'].startswith('C03-')] + entries
path.write_text(json.dumps(catalog, ensure_ascii=False, indent=2) + '\n')

def span(a, b):
    return list(range(a, b + 1))

definitions = [
    [('writing-art', '书写与美术', [2, 3, 5, 6] + span(22, 27)),
     ('books-paper', '书本与纸张', span(12, 19) + [21, 37]),
     ('tools-storage', '工具与收纳', [4] + span(7, 11) + [20] + span(28, 36)),
     ('daily-electronics', '日常与电子用品', [1] + span(38, 43))],
    [('teaching-spaces', '学校与教学空间', span(1, 14)),
     ('campus-places', '校园日常场所', span(15, 23)),
     ('facilities', '设施与物品', span(24, 38)),
     ('people-life', '师生与校园生活', span(39, 45))],
    [('core-subjects', '常见学科', span(1, 12)),
     ('more-subjects', '拓展学科', span(13, 17) + [23, 25]),
     ('learning-skills', '学习技能与练习', span(18, 22) + [24]),
     ('schedule-expression', '课程安排与表达', span(26, 31))],
    [('language-interaction', '听说读写与互动', span(1, 11)),
     ('answer-check', '答题与检查', span(12, 26)),
     ('hands-on', '动手与操作指令', span(27, 38)),
     ('classroom-routines', '合作与课堂规范', span(39, 50)),
     ('learning-activities', '作业与学习活动', span(51, 64)),
     ('break-tests', '休息、测验与成绩', span(65, 72)),
     ('classroom-phrases', '课堂交流句型', span(73, 79))],
]
path = ROOT / 'data/practice-groups.json'
catalog = json.loads(path.read_text())
catalog['subcategories'] = [r for r in catalog['subcategories'] if not r['subcategoryId'].startswith('C03-')]
for index, groups in enumerate(definitions, 1):
    prefix = f'C03-S{index:02}'
    catalog['subcategories'].append({'subcategoryId': prefix, 'groups': [
        {'id': key, 'name': name, 'wordIds': [f'{prefix}-{i:03}' for i in indices]}
        for key, name, indices in groups]})
path.write_text(json.dumps(catalog, ensure_ascii=False, indent=2) + '\n')
print('Reviewed 198 C03 meanings; defined 19 optional practice groups in four existing entrances.')
