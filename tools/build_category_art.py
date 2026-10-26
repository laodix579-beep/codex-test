"""Validate category-card artwork and embed its read-only resource map."""
import hashlib
import json
import re
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
catalog=json.loads((ROOT/'data/category-art.json').read_text())
path=ROOT/'index.html'
html=path.read_text()
marker='window.FROG_WORD_CATALOG = '
words=json.JSONDecoder().raw_decode(html[html.index(marker)+len(marker):])[0]
ids={sub['id'] for category in words['categories'] for sub in category['subcategories']}
assert len(catalog['entries'])==32 and {row['subcategoryId'] for row in catalog['entries']}==ids
sheets={sheet['path']:sheet for sheet in catalog['sheets']}
assert len(sheets)==4
seen=set()
for sheet in sheets.values():
    assert sheet['columns']==2 and sheet['rows']==4 and sheet['width']>0 and sheet['height']>0
    assert hashlib.sha256((ROOT/sheet['path']).read_bytes()).hexdigest()==sheet['sha256']
for row in catalog['entries']:
    sheet=sheets[row['sheet']]
    assert 0<=row['column']<sheet['columns'] and 0<=row['row']<sheet['rows']
    key=(row['sheet'],row['column'],row['row'])
    assert key not in seen
    seen.add(key)
script='<script id="category-art-library">\nwindow.FROG_CATEGORY_ART='+json.dumps(catalog,ensure_ascii=False,separators=(',',':')).replace('<','\\u003c')+';\n</script>\n'
pattern=r'<script id="category-art-library">.*?</script>\s*'
if re.search(pattern,html,re.S):
    html=re.sub(pattern,lambda _:script,html,count=1,flags=re.S)
else:
    marker='<script data-embedded-audio="">'
    assert marker in html
    html=html.replace(marker,script+marker,1)
path.write_text(html)
(ROOT/'category-files.js').write_text('/* Decorative category-card resources for the existing offline cache. */\nself.FROG_CATEGORY_FILES='+json.dumps(list(sheets),separators=(',',':'))+';\n')
print('Validated 32 category backgrounds in four atlases; embedded resource map and offline file list.')
