"""Embed the scene map and renderer; read atlas metadata without editing PNGs."""
import hashlib
import json
import re
from pathlib import Path
from PIL import Image

ROOT=Path(__file__).resolve().parents[1]
catalog=json.loads((ROOT/'data/scene-catalog.json').read_text())
groups=json.loads((ROOT/'data/basic-vocabulary.json').read_text())['subcategories']
words=[w for group in groups for w in group['items']]
for folder in ['time-nature','school-learning','family-daily', 'food-health']:
    for file in sorted((ROOT/'data'/folder).glob('0*.json')):words.extend(json.loads(file.read_text())['items'])
assert {s['id'] for s in catalog['scenes']}=={w['id'] for w in words}
numeric=[*range(30),30,40,50,60,70,80,90,100]
icons=['🍪','🖊️','🐦','📕','🐈','🍎','🦆','⭐','🖍️','🌸','🖐️','🃏','🥚','🔵','🐦','🧒','🌟','⭐','✏️','🧱','🧱','🌟','🐦','📕','🃏','🧒','🖍️','⭐','📅','🔮','🌟','📕','⭐','🕒','⚖️','🔢','🔢','🔵']
special=['number','sequence','howmany','howmuch','many','much','more','less','some','any','all','half','first','second','third','each','every','alot','few','afew','little','alittle','enough','total']
for scene in catalog['scenes']:
    if scene['kind']!='quantity':continue
    index=int(scene['id'].split('-')[-1])-1
    if index<len(numeric):
        scene['visual']={'type':{10:'fingers',28:'calendar',33:'clock',34:'comparison',35:'numeral',36:'difference'}.get(index,'count'),'value':numeric[index],'object':icons[index]}
    else:scene['visual']={'type':special[index-len(numeric)]}
for sheet in catalog['sheets']:
    path=ROOT/sheet['path']
    assert path.is_file(),f'Missing generated scene atlas: {path}'
    with Image.open(path) as im:sheet['width'],sheet['height']=im.size
    sheet['sha256']=hashlib.sha256(path.read_bytes()).hexdigest()
(ROOT/'data/scene-catalog.json').write_text(json.dumps(catalog,ensure_ascii=False,indent=2)+'\n')
bank={'version':catalog['version'],'sheets':[{k:v for k,v in s.items() if k!='prompt'} for s in catalog['sheets']],'scenes':[{k:v for k,v in s.items() if k!='description'} for s in catalog['scenes']]}
html=(ROOT/'index.html').read_text()
html=re.sub(r'<script id="scene-(?:library|runtime)">[\s\S]*?</script>\n?','',html)
runtime=(ROOT/'tools/scene-runtime.js').read_text()
assert '</script' not in runtime.lower()
injection='<script id="scene-library">\nwindow.FROG_SCENE_LIBRARY='+json.dumps(bank,ensure_ascii=False,separators=(',',':')).replace('<','\\u003c')+';\n</script>\n<script id="scene-runtime">\n'+runtime+'\n</script>\n'
marker='<script data-embedded-audio="">'
assert html.count(marker)==1
html=html.replace(marker,injection+marker)
(ROOT/'index.html').write_text(html)
(ROOT/'scene-files.js').write_text('/* Scene resources for the existing offline cache. */\nself.FROG_SCENE_FILES='+json.dumps([s['path'] for s in catalog['sheets']],separators=(',',':'))+';\n')
print(json.dumps({'scenes':len(bank['scenes']),'atlases':len(bank['sheets']),'files_present':sum((ROOT/s['path']).exists() for s in catalog['sheets'])}))
