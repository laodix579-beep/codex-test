"""Validate optional practice sections and embed them without changing words."""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
path = ROOT / 'index.html'
html = path.read_text()
start = html.index('window.FROG_WORD_CATALOG = ') + len('window.FROG_WORD_CATALOG = ')
word_catalog = json.JSONDecoder().raw_decode(html[start:])[0]
words = word_catalog['words']
catalog = json.loads((ROOT / 'data/practice-groups.json').read_text())
policy = json.loads((ROOT / 'data/practice-group-policy.json').read_text())
size = policy['targetWords']
assert size == {'min': 10, 'max': 25}
sections = {s['subcategoryId']: s for s in catalog['subcategories']}
word_order = {w['id']: i for i, w in enumerate(words)}
for rule in policy['merges']:
    section = sections[rule['subcategoryId']]
    for merged in rule['groups']:
        sources = set(merged['sources'])
        assert merged['id'] in sources
        existing = [g for g in section['groups'] if g['id'] in sources]
        # A completed merge is valid on repeated builds. Coverage below still
        # detects missing IDs if an authoring tool supplied incomplete groups.
        assert {g['id'] for g in existing} in (sources, {merged['id']})
        ids = [i for group in existing for i in group['wordIds']]
        assert len(ids) == len(set(ids))
        replacement = {'id': merged['id'], 'name': merged['name'],
                       'wordIds': sorted(ids, key=word_order.__getitem__)}
        updated, inserted = [], False
        for group in section['groups']:
            if group['id'] in sources:
                if not inserted:
                    updated.append(replacement); inserted = True
            else:
                updated.append(group)
        section['groups'] = updated
assert len({r['subcategoryId'] for r in catalog['subcategories']}) == len(catalog['subcategories'])
for section in catalog['subcategories']:
    groups = section['groups']
    assert len(groups) >= 1
    assert len({g['id'] for g in groups}) == len(groups)
    assert all(re.fullmatch(r'[a-z0-9-]+', g['id']) and g['id'] not in ('all', 'other') and g['name'] for g in groups)
    ids = [i for group in groups for i in group['wordIds']]
    expected = {w['id'] for w in words if w['subcategoryId'] == section['subcategoryId']}
    assert len(ids) == len(set(ids)) and set(ids) == expected, section['subcategoryId']
    assert all(size['min'] <= len(g['wordIds']) <= size['max'] for g in groups), section['subcategoryId']
# Include implicit direct categories and empty entrances in the site-wide audit.
audit, covered = [], []
for category in word_catalog['categories']:
    for sub in category['subcategories']:
        ids = [w['id'] for w in words if w['subcategoryId'] == sub['id']]
        if not ids:
            audit.append({'id': sub['id'], 'name': sub['name'], 'words': 0, 'mode': 'empty', 'groups': []})
            continue
        groups = sections.get(sub['id'], {}).get('groups') or [{'id': 'all', 'name': sub['name'], 'wordIds': ids}]
        assert all(size['min'] <= len(g['wordIds']) <= size['max'] for g in groups), sub['id']
        covered.extend(i for g in groups for i in g['wordIds'])
        audit.append({'id': sub['id'], 'name': sub['name'], 'words': len(ids),
                      'mode': 'chooser' if len(groups) > 1 else 'direct',
                      'groups': [{'id': g['id'], 'name': g['name'], 'words': len(g['wordIds'])} for g in groups]})
assert len(covered) == len(set(covered)) == len(words)
report = {'targetWords': size, 'totalWords': len(words),
          'populatedEntrances': sum(s['mode'] != 'empty' for s in audit),
          'practiceGroups': sum(len(s['groups']) for s in audit),
          'chooserEntrances': sum(s['mode'] == 'chooser' for s in audit),
          'directEntrances': sum(s['mode'] == 'direct' for s in audit),
          'emptyEntrances': sum(s['mode'] == 'empty' for s in audit), 'subcategories': audit}
(ROOT / 'data/practice-groups.json').write_text(json.dumps(catalog, ensure_ascii=False, indent=2) + '\n')
(ROOT / 'reports/practice-group-audit.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
script = '<script id="practice-group-library">\nwindow.FROG_PRACTICE_GROUPS=' + json.dumps(catalog, ensure_ascii=False, separators=(',', ':')).replace('<', '\\u003c') + ';\n</script>\n'
pattern = r'<script id="practice-group-library">.*?</script>\s*'
if re.search(pattern, html, re.S):
    html = re.sub(pattern, lambda _: script, html, count=1, flags=re.S)
else:
    marker = '<script data-embedded-audio="">'
    assert marker in html
    html = html.replace(marker, script + marker, 1)
path.write_text(html)
print('Validated and embedded', report['practiceGroups'], 'groups across', report['populatedEntrances'], 'populated entrances;', report['directEntrances'], 'direct and', report['chooserEntrances'], 'with choices.')
