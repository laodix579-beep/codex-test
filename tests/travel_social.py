"""C07 additive content, all 218 entries, exact media and unchanged study flows."""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import re
import subprocess
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]
BASE='http://127.0.0.1:8000/'
BASELINE='98be4c99abe18db3bfa53da2b4e8bb7c0d98e8b7'
parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--from-window',type=int,choices=range(1,5),default=1);args=parser.parse_args()
def before(path):return subprocess.check_output(['git','show',BASELINE+':'+path],cwd=ROOT)
marker='window.FROG_WORD_CATALOG = '
html=(ROOT/'index.html').read_text();old_html=before('index.html').decode()
catalog=json.JSONDecoder().raw_decode(html.split(marker,1)[1])[0]
old_catalog=json.JSONDecoder().raw_decode(old_html.split(marker,1)[1])[0]
assert catalog['version']==old_catalog['version']=='basic-us-v1'
assert len(catalog['words'])==1428 and len(old_catalog['words'])==1210
assert [w for w in catalog['words'] if w['categoryId']!='C07']==old_catalog['words']
assert [c for c in catalog['categories'] if c['id']!='C07']==[c for c in old_catalog['categories'] if c['id']!='C07']
assert catalog['packs'][:-1]==old_catalog['packs'] and catalog['packs'][-1]['id']=='travel-social-v1'
def application(text):
 for prefix in [marker,'window.LOCAL_AUDIO_BANK=']:
  start=text.index(prefix)+len(prefix);_,size=json.JSONDecoder().raw_decode(text[start:]);text=text[:start]+'{}'+text[start+size:]
 text=re.sub(r'<script id="(?:meaning-library|scene-library|practice-group-library)">[\s\S]*?</script>\s*','',text)
 # Only café compatibility widens the Latin-letter token ranges.
 # The offline serializer also gains lossless packing for archives > 512 MB;
 # the actual full download/source editor/offline media hashes are tested.
 start=text.index('  function offlineProgramHTML() {')
 end=text.index('  function offlineHTML() {',start)
 text=text[:start]+'  /* offline serializer */\n'+text[end:]
 helpers=text.find('  // Pack binary bytes into safe BMP characters.')
 if helpers>=0:
  end=text.index('  /* offline serializer */',helpers)
  text=text[:helpers]+text[end:]
 text=text.replace("field.placeholder='正在准备完整源码…';field.style.fontFamily='monospace';field.style.fontVariantLigatures='none';","field.placeholder='正在准备完整源码…';")
 return text.replace('frog-mobile-light-v43','frog-travel-social-v44').replace('A-Za-zÀ-ÖØ-öø-ÿ0-9','A-Za-z0-9')
assert application(html)==application(old_html),'Unexpected executable application/style change'
assert (ROOT/'小蛙自习室.html').read_bytes()==(ROOT/'index.html').read_bytes()
for filename,key in [('data/meaning-catalog.json','entries'),('data/scene-catalog.json','scenes'),('data/practice-groups.json','subcategories')]:
 now=json.loads((ROOT/filename).read_text());old=json.loads(before(filename))
 assert [r for r in now[key] if not r.get('id',r.get('subcategoryId','')).startswith('C07-')]==old[key]
for filename in ['data/basic-vocabulary.json','data/category-art.json','assets/home-hero.png','tools/scene-runtime.js','data/practice-group-policy.json','manifest.webmanifest','category-files.js']:
 assert (ROOT/filename).read_bytes()==before(filename),filename
for folder in ['time-nature','school-learning','family-daily','food-health','animal-nature']:
 for file in (ROOT/'data'/folder).iterdir():assert file.read_bytes()==before(file.relative_to(ROOT).as_posix())
old_audio=json.loads(before('reports/all-audio-sha256.json'));assert len(old_audio)==2616
for path,row in old_audio.items():assert hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==row['sha256']
for filename in ['data/scene-catalog.json','data/category-art.json']:
 for sheet in json.loads(before(filename))['sheets']:assert hashlib.sha256((ROOT/sheet['path']).read_bytes()).hexdigest()==sheet['sha256']
source_hashes=json.loads((ROOT/'reports/travel-source-sha256.json').read_text())
for name,row in source_hashes.items():
 path=ROOT/'data/travel-social'/('index.json' if '分类目录' in name else 'source-review.md' if name.endswith('.md') else name)
 assert hashlib.sha256(path.read_bytes()).hexdigest()==row['sha256']
windows=[json.loads(p.read_text()) for p in sorted((ROOT/'data/travel-social').glob('0*.json'))]
assert [len(w['items']) for w in windows]==[85,39,45,49]
words=[w for window in windows for w in window['items']]
for window in windows:
 for raw in window['items']:
  row=next(w for w in catalog['words'] if w['id']==raw['id'])
  assert (row['word'],row['ipa'],row['meaning'],row['example'],row['exampleZh'])==(raw['english'],raw['ipa_dj_british'],raw['chinese'],raw['example_en'],raw['example_zh'])
  assert row['subcategoryId']=='C07-S'+window['window_id'][-2:]
sections=json.loads((ROOT/'data/travel-social-practice-sections.json').read_text())['subcategories']
assert [len(s['groups']) for s in sections]==[4,2,3,3]
assert min(len(g['wordIds']) for s in sections for g in s['groups'])==12
assert max(len(g['wordIds']) for s in sections for g in s['groups'])==24
assert len(list(csv.DictReader((ROOT/'data/travel-social-audio-map.csv').open(encoding='utf-8-sig'))))==218
generation=json.loads((ROOT/'data/travel-social-audio-generation.json').read_text())
assert len(generation['clips'])==401 and generation['voice']=='af_bella' and generation['locale']=='en-US'
audit=json.loads((ROOT/'reports/practice-group-audit.json').read_text())
assert [audit[k] for k in ['totalWords','populatedEntrances','practiceGroups','chooserEntrances','directEntrances','emptyEntrances']]==[1428,28,88,26,2,4]
print('PASS: exact 218 source words/DJ/examples, four entrances, 12 balanced sections; all old words/media/styles retained; only café tokens and lossless offline serialization adjusted',flush=True)

with sync_playwright() as p:
 browser=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
 errors=[]
 context=browser.new_context(viewport={'width':1696,'height':1000},service_workers='block')
 context.add_init_script("Object.defineProperty(window,'speechSynthesis',{get(){throw new Error('Runtime TTS forbidden')}})")
 # Apply fixtures in the next document, after legitimate pagehide saves.
 context.add_init_script("{const pending=sessionStorage.getItem('travel-fixture');if(pending){const {k,s}=JSON.parse(pending);sessionStorage.removeItem('travel-fixture');localStorage.setItem(k,JSON.stringify(s));}}")
 page=context.new_page();page.on('pageerror',lambda e:errors.append(str(e)))
 def saved():return page.evaluate('JSON.parse(localStorage.getItem(document.body.dataset.storageKey))')
 page.route(BASE+'?before-travel',lambda r:r.fulfill(body=old_html,content_type='text/html; charset=utf-8'),times=1)
 page.goto(BASE+'?before-travel#home')
 old_tokens=page.evaluate('()=>FROG_WORD_CATALOG.words.map(w=>({id:w.id,word:FrogPractice.sentenceTokens(w.word).map(({text,word,index})=>({text,word,index})),example:FrogPractice.sentenceTokens(w.example).map(({text,word,index})=>({text,word,index})),cloze:FrogPractice.wordCloze(w)}))')
 legacy=page.evaluate('''()=>{const k=document.body.dataset.storageKey,s=JSON.parse(localStorage.getItem(k));s.words[0].notes='旧词笔记';s.words.push({...s.words[0],id:'custom-travel-word',word:'my own word',meaning:'用户词条',categoryId:'C08',subcategoryId:'C08-S01'});
 s.wordStatus={'C01-S01-001':'mastered','C06-S01-001':'unfamiliar','custom-travel-word':'mastered'};s.settings.userName='原站学习者';s.settings.grade='五年级';s.settings.rate=.9;s.favorites=['C01-S01-001','custom-travel-word'];s.notes=[{id:'travel-note',title:'原笔记',body:'保留记录',createdAt:'2026-10-01T00:00:00Z',updatedAt:'2026-10-01T00:00:00Z'}];s.days['2020-01-01']={seconds:1234,words:['C06-S01-001'],sentences:[],mistakes:2,checked:true};
 const ids=s.words.filter(w=>w.subcategoryId==='C06-S01').map(w=>w.id);s.practiceResume={ids,wordId:ids[3],answered:false,finished:false};sessionStorage.setItem('travel-fixture',JSON.stringify({k,s}));return s;}''')
 page.goto(BASE+'#home');page.locator('.home-dashboard').wait_for();now=saved()
 assert page.evaluate('()=>FROG_WORD_CATALOG.words.filter(w=>w.categoryId!=="C07").map(w=>({id:w.id,word:FrogPractice.sentenceTokens(w.word).map(({text,word,index})=>({text,word,index})),example:FrogPractice.sentenceTokens(w.example).map(({text,word,index})=>({text,word,index})),cloze:FrogPractice.wordCloze(w)}))')==old_tokens
 assert len(now['words'])==1429 and now['contentPacks']==legacy['contentPacks']+['travel-social-v1']
 for row in legacy['words']:assert next(w for w in now['words'] if w['id']==row['id'])==row
 for key in ['wordStatus','settings','favorites','notes','plan','practiceResume']:assert now[key]==legacy[key],key
 assert now['days']['2020-01-01']==legacy['days']['2020-01-01']
 page.locator('.home-resume-card [data-action="resume-desktop"]').click()
 assert page.locator('.translation-picture').get_attribute('data-scene-id')==legacy['practiceResume']['wordId']
 page.locator('.practice-back').click();page.wait_for_function('!document.querySelector("#lesson-dialog").open')
 page.reload();assert len(saved()['words'])==1429
 page.evaluate('''()=>{const k=document.body.dataset.storageKey,s=JSON.parse(localStorage.getItem(k));s.words=s.words.filter(w=>w.id!=='C07-S01-001');sessionStorage.setItem('travel-fixture',JSON.stringify({k,s}));}''')
 page.reload();assert not any(w['id']=='C07-S01-001' for w in saved()['words'])
 page.goto(BASE+'#settings');page.locator('#restore-file').set_input_files({'name':'before-travel.json','mimeType':'application/json','buffer':json.dumps(legacy,ensure_ascii=False).encode()})
 page.locator('#confirm-dialog button[value="yes"]').click()
 page.wait_for_function('JSON.parse(localStorage.getItem(document.body.dataset.storageKey)).words.some(w=>w.id==="C07-S01-001")')
 assert len(saved()['words'])==1429 and saved()['wordStatus']==legacy['wordStatus']
 context.close()
 print('PASS: actual v43 state upgrades once; old edits/custom/status/profile/history/resume/settings retained; deletion and old backup work',flush=True)
 context=browser.new_context(viewport={'width':1696,'height':1000},service_workers='block')
 context.add_init_script("Object.defineProperty(window,'speechSynthesis',{get(){throw new Error('Runtime TTS forbidden')}})")
 page=context.new_page();page.on('pageerror',lambda e:errors.append(str(e)));page.goto(BASE+'#home')
 assert page.locator('.home-category-tile[data-category-id="C07"]>small').inner_text()=='218 个单词'
 page.locator('.home-category-tile[data-category-id="C07"]').click();assert page.locator('.mvp-subcategory').count()==4
 meanings={r['id']:r for r in json.loads((ROOT/'data/meaning-catalog.json').read_text())['entries']}
 for i,window in enumerate(windows):
  if i+1<args.from_window:continue
  sub=f'C07-S{i+1:02}';page.goto(BASE+'#words/C07');page.locator(f'.mvp-subcategory[data-subcategory-id="{sub}"]').click()
  dialog=page.locator('#practice-group-dialog');assert int(dialog.locator('.practice-group-all b').inner_text())==len(window['items'])
  for part in sections[i]['groups']:assert int(dialog.locator(f'[data-practice-group="{part["id"]}"] b').inner_text())==len(part['wordIds'])
  dialog.locator('[data-close]').click();assert not dialog.evaluate('e=>e.open')
  page.goto(BASE+'#words/C07/'+sub);page.locator('.translation-blank').first.wait_for()
  for j,raw in enumerate(window['items']):
   page.wait_for_function('document.querySelector(".translation-picture img")?.naturalWidth>0')
   assert page.locator('.translation-picture').get_attribute('data-scene-id')==raw['id']
   row=next(w for w in catalog['words'] if w['id']==raw['id'])
   cloze=page.evaluate('(w)=>FrogPractice.wordCloze(w)',row)
   if raw['english']=='penny':assert cloze is None # Existing spelling fallback; never rewrite pence or the supplied example.
   else:
    assert cloze,row
    if raw['english']=='café':
     assert not any('é' in text for text in page.locator('.translation-slots .sentence-punctuation').all_text_contents())
     assert page.evaluate('w=>FrogPractice.sentenceTokens(w.word).filter(t=>t.word).map(t=>t.text)',row)==['café']
    assert page.locator('.word-example-prompt').inner_text()==raw['example_zh']
    assert page.locator('.word-example-prompt [data-meaning-target="chinese"]').all_text_contents()==[s['text'] for s in meanings[raw['id']]['spans']]
   assert raw['chinese'] in page.locator('.word-context-meaning' if cloze else '.translation-chinese').inner_text()
   status=saved()['wordStatus'].copy()
   page.locator('#translation-form [data-action="translation-answer"]').click();answer=page.locator('#practice-answer-dialog')
   assert answer.locator('.mvp-answer-line>span:not(.mvp-dj)').inner_text()==raw['ipa_dj_british']
   expected=re.sub(r'[^\w\s]+$','',raw['example_en'] if cloze else raw['english']).strip()
   assert answer.locator('.mvp-answer-english strong').inner_text()==expected
   assert saved()['wordStatus']==status
   if j in (0,len(window['items'])-1) or raw['english'] in ['refund','discount','entrance','penny','café','traffic lights']:
    for role,text in [('word',raw['english']),('example',raw['example_en'] if cloze else raw['english'])]:
     answer.locator(f'[data-answer-audio="{role}"]').click()
     page.wait_for_function('(text)=>{const a=document.querySelector("#question-audio");return FrogPractice.normalize(a.dataset.sourceText)===FrogPractice.normalize(text)&&a.currentTime>0&&!a.paused}',arg=text)
     assert answer.evaluate('e=>e.open')
   answer.locator('[data-answer-close]').click()
   tokens=page.evaluate('w=>{const c=FrogPractice.wordCloze(w);return FrogPractice.sentenceTokens(c?.english||w.word).filter(t=>t.word&&(!c||c.blankIndices.includes(t.index))).map(t=>t.text)}',row)
   for field,text in zip(page.locator('.translation-blank').all(),tokens):field.fill(text)
   page.locator('#translation-submit').click()
   assert saved()['wordStatus'][raw['id']]=='mastered',raw['id']
   if j<len(window['items'])-1:page.locator('.mvp-solved-actions [data-action="next-item"]').click()
  page.locator('.practice-back').click();page.wait_for_function('!document.querySelector("#lesson-dialog").open')
  print('PASS: all source examples, DJ, Chinese targets, scenes, modal, read-only answer, grading and next in '+window['window_name'],flush=True)
 for query,english in [('TRAFFIC JAM','traffic jam'),('消防员','firefighter'),('One hundred pence make one pound','penny')]:
  page.locator('#global-search').fill(query);page.locator('#global-search').press('Enter');card=page.locator(f'.search-results .word-card[data-word="{english}"]');card.wait_for()
  row=next(w for w in words if w['english']==english)
  for selector,text in [('[data-action="speak-word"]',row['english']),('.word-example-speak',row['example_en'])]:
   card.locator(selector).click();page.wait_for_function('(text)=>{const a=document.querySelector("#question-audio");return a.dataset.sourceText===text&&a.currentTime>0&&!a.paused}',arg=text)
 context.close()
 for width in (320,390,768):
  context=browser.new_context(viewport={'width':width,'height':844},is_mobile=True,has_touch=True,color_scheme='dark',service_workers='block',user_agent=p.devices['iPhone 13']['user_agent'])
  context.add_init_script("Object.defineProperty(window,'speechSynthesis',{get(){throw new Error('Runtime TTS forbidden')}})")
  page=context.new_page();page.on('pageerror',lambda e:errors.append(str(e)));page.goto(BASE+'#words/C07')
  assert page.evaluate('getComputedStyle(document.body).backgroundColor')=='rgb(246, 247, 255)'
  page.locator('.mvp-subcategory').first.tap();page.locator('#practice-group-dialog [data-practice-group="vehicles"]').tap()
  field=page.locator('.translation-blank').first;field.fill('car')
  page.locator('.mobile-controls [data-action="translation-answer"]').last.tap();assert not saved()['wordStatus']
  page.locator('.mobile-controls [data-action="translation-submit"]').last.tap();assert saved()['wordStatus']['C07-S01-001']=='mastered'
  page.locator('.mobile-controls [data-action="next-item"]').last.tap();assert page.locator('.translation-picture').get_attribute('data-scene-id')=='C07-S01-002'
  page.locator('.practice-back').tap();page.wait_for_function('!document.querySelector("#lesson-dialog").open')
  page.goto(BASE+'#home');page.reload();assert '第 2 / 24 词' in page.locator('.mvp-resume-title').inner_text()
  page.locator('.home-resume-card [data-action="resume-desktop"]').tap();assert page.locator('.translation-picture').get_attribute('data-scene-id')=='C07-S01-002'
  assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
  context.close();print('PASS: mobile light layout, group selection, touch answer/grade/next and exact cursor at '+str(width)+'px',flush=True)
 assert not errors,errors
 browser.close()
print(f'COMPLETE: C07 source, additive migration, {sum(len(w["items"]) for w in windows[args.from_window-1:])} entries from window {args.from_window}, desktop/mobile search/practice/audio passed',flush=True)
