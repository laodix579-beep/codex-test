"""C06 additive integration, all 238 source entries and unchanged learning flows."""
import csv
import hashlib
import json
from pathlib import Path
import re
import subprocess
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
BASE = 'http://127.0.0.1:8000/'
BASELINE = '2e7eca2dfbb6d85f5f0cddb67146692df958e441'
marker = 'window.FROG_WORD_CATALOG = '
def previous(path):return subprocess.check_output(['git','show',BASELINE+':'+path],cwd=ROOT)
html = (ROOT/'index.html').read_text();old_html=previous('index.html').decode()
catalog=json.JSONDecoder().raw_decode(html.split(marker,1)[1])[0]
old_catalog=json.JSONDecoder().raw_decode(old_html.split(marker,1)[1])[0]
assert catalog['version']==old_catalog['version']=='basic-us-v1'
assert len(catalog['words'])==1210 and len(old_catalog['words'])==972
assert [w for w in catalog['words'] if w['categoryId']!='C06']==old_catalog['words']
assert [c for c in catalog['categories'] if c['id']!='C06']==[c for c in old_catalog['categories'] if c['id']!='C06']
assert catalog['packs'][:-1]==old_catalog['packs'] and catalog['packs'][-1]['id']=='animal-nature-v1'
# Data-only addition: executable scripts and styles must be identical to v41.
def application(text):
 for prefix in [marker,'window.LOCAL_AUDIO_BANK=']:
  start=text.index(prefix)+len(prefix);_,size=json.JSONDecoder().raw_decode(text[start:]);text=text[:start]+'{}'+text[start+size:]
 text=re.sub(r'<script id="(?:meaning-library|scene-library|practice-group-library)">[\s\S]*?</script>\s*','',text)
 return text.replace('frog-practice-balance-v41','frog-animal-nature-v42')
assert application(html)==application(old_html)
for filename,key in [('data/meaning-catalog.json','entries'),('data/scene-catalog.json','scenes'),('data/practice-groups.json','subcategories')]:
 before=json.loads(previous(filename));now=json.loads((ROOT/filename).read_text())
 assert [r for r in now[key] if not r.get('id',r.get('subcategoryId','')).startswith('C06-')]==before[key]
for filename in ['data/basic-vocabulary.json','data/category-art.json','assets/home-hero.png','tools/scene-runtime.js','data/practice-group-policy.json','reports/food-scene-source-sha256.json','reports/food-source-sha256.json','reports/school-scene-source-sha256.json','reports/family-scene-source-sha256.json']:
 assert (ROOT/filename).read_bytes()==previous(filename)
for folder in ['time-nature','school-learning','family-daily','food-health']:
 for file in (ROOT/'data'/folder).glob('*.json'):assert file.read_bytes()==previous(file.relative_to(ROOT).as_posix())
old_audio=json.loads(previous('reports/all-audio-sha256.json'));assert len(old_audio)==2169
for path,row in old_audio.items():assert hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==row['sha256']
for filename in ['data/scene-catalog.json','data/category-art.json']:
 for sheet in json.loads(previous(filename))['sheets']:
  assert hashlib.sha256((ROOT/sheet['path']).read_bytes()).hexdigest()==sheet['sha256']
groups=[json.loads(p.read_text()) for p in sorted((ROOT/'data/animal-nature').glob('0*.json'))]
assert [len(g['items']) for g in groups]==[72,75,42,49]
words=[w for group in groups for w in group['items']]
source_hashes=json.loads((ROOT/'reports/animal-source-sha256.json').read_text())
for name,row in source_hashes.items():
 path=ROOT/'data/animal-nature'/('index.json' if '分类目录' in name else name)
 assert hashlib.sha256(path.read_bytes()).hexdigest()==row['sha256']
generation=json.loads((ROOT/'data/animal-nature-audio-generation.json').read_text())
assert len(generation['clips'])==447 and generation['voice']=='af_bella' and generation['locale']=='en-US'
sections=json.loads((ROOT/'data/animal-nature-practice-sections.json').read_text())['subcategories']
assert sum(len(s['groups']) for s in sections)==15
assert all(10<=len(g['wordIds'])<=25 for s in sections for g in s['groups'])
audit=json.loads((ROOT/'reports/practice-group-audit.json').read_text())
assert [audit[k] for k in ['totalWords','populatedEntrances','practiceGroups','chooserEntrances','directEntrances','emptyEntrances']]==[1210,24,76,22,2,8]
map_rows=list(csv.DictReader((ROOT/'data/animal-nature-audio-map.csv').open(encoding='utf-8-sig')))
assert len(map_rows)==238 and {r['id'] for r in map_rows}=={w['id'] for w in words}
print('PASS: data-only additive 238 words, exact DJ/source files, four UI slots, 15 balanced groups; old 972 words, all 2169 MP3 and all old images/application code unchanged',flush=True)

with sync_playwright() as p:
 browser=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
 context=browser.new_context(viewport={'width':1696,'height':1000},service_workers='block')
 context.add_init_script("Object.defineProperty(window,'speechSynthesis',{get(){throw new Error('Runtime TTS forbidden')}})")
 page=context.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
 # Obtain a real pre-update state from the actual v41 page.
 page.route(BASE+'?previous-animal',lambda route:route.fulfill(body=old_html,content_type='text/html; charset=utf-8'),times=1)
 page.goto(BASE+'?previous-animal#home')
 legacy=page.evaluate('''()=>{const k=document.body.dataset.storageKey,s=JSON.parse(localStorage.getItem(k));
 s.words[0].notes='旧词笔记';s.words.push({...s.words[0],id:'custom-animal-word',word:'my word',meaning:'用户词条',categoryId:'C08',subcategoryId:'C08-S01'});
 s.wordStatus={'C01-S01-001':'mastered','C05-S06-001':'unfamiliar','custom-animal-word':'mastered'};
 s.settings.userName='原站学习者';s.settings.grade='五年级';s.settings.rate=.9;s.favorites=['C01-S01-001','custom-animal-word'];
 s.notes=[{id:'animal-note',title:'原笔记',body:'必须保留',createdAt:'2026-10-01T00:00:00Z',updatedAt:'2026-10-01T00:00:00Z'}];
 s.days['2020-01-01']={seconds:1234,words:['C05-S06-001'],sentences:[],mistakes:2,checked:true};
 const ids=s.words.filter(w=>w.subcategoryId==='C05-S04').map(w=>w.id);s.practiceResume={ids,wordId:ids[3],answered:false,finished:false};
 localStorage.setItem(k,JSON.stringify(s));return s;}''')
 def saved():return page.evaluate('JSON.parse(localStorage.getItem(document.body.dataset.storageKey))')
 page.goto(BASE+'#home');page.locator('.home-dashboard').wait_for();now=saved()
 assert len(now['words'])==1211 and now['contentPacks']==legacy['contentPacks']+['animal-nature-v1']
 for w in legacy['words']:assert next(x for x in now['words'] if x['id']==w['id'])==w
 for key in ['wordStatus','favorites','notes','settings','plan','practiceResume']:assert now[key]==legacy[key],key
 assert now['days']['2020-01-01']==legacy['days']['2020-01-01']
 page.locator('.home-resume-card [data-action="resume-desktop"]').click()
 assert page.locator('.translation-picture').get_attribute('data-scene-id')==legacy['practiceResume']['wordId']
 page.locator('.practice-back').click();page.wait_for_function('!document.querySelector("#lesson-dialog").open')
 page.reload();assert len(saved()['words'])==1211
 page.evaluate('''()=>{const k=document.body.dataset.storageKey,s=JSON.parse(localStorage.getItem(k));s.words=s.words.filter(w=>w.id!=='C06-S01-001');localStorage.setItem(k,JSON.stringify(s));}''')
 page.reload();assert not any(w['id']=='C06-S01-001' for w in saved()['words'])
 page.goto(BASE+'#settings');page.locator('#restore-file').set_input_files({'name':'before-animal.json','mimeType':'application/json','buffer':json.dumps(legacy,ensure_ascii=False).encode()})
 page.locator('#confirm-dialog button[value="yes"]').click()
 page.wait_for_function('JSON.parse(localStorage.getItem(document.body.dataset.storageKey)).words.some(w=>w.id==="C06-S01-001")')
 assert len(saved()['words'])==1211 and saved()['wordStatus']==legacy['wordStatus']
 context.close()
 print('PASS: actual v41 state updates once, preserves profile/custom words/status/history/settings/resume; deletion respected and old backup installs new pack',flush=True)

 context=browser.new_context(viewport={'width':1696,'height':1000},service_workers='block')
 context.add_init_script("Object.defineProperty(window,'speechSynthesis',{get(){throw new Error('Runtime TTS forbidden')}})")
 page=context.new_page();page.on('pageerror',lambda e:errors.append(str(e)));page.goto(BASE+'#home')
 assert page.locator('.home-category-tile[data-category-id="C06"]>small').inner_text()=='238 个单词'
 page.locator('.home-category-tile[data-category-id="C06"]').click();assert page.locator('.mvp-subcategory').count()==4
 meanings={r['id']:r for r in json.loads((ROOT/'data/meaning-catalog.json').read_text())['entries']}
 for gi,group in enumerate(groups):
  sub=f'C06-S{gi+1:02}';page.goto(BASE+'#words/C06');page.locator(f'.mvp-subcategory[data-subcategory-id="{sub}"]').click()
  dialog=page.locator('#practice-group-dialog');assert int(dialog.locator('.practice-group-all b').inner_text())==len(group['items'])
  section=next(s for s in sections if s['subcategoryId']==sub)
  for part in section['groups']:assert int(dialog.locator(f'[data-practice-group="{part["id"]}"] b').inner_text())==len(part['wordIds'])
  dialog.locator('[data-close]').click();assert not dialog.evaluate('e=>e.open')
  page.goto(BASE+'#words/C06/'+sub);page.locator('.translation-blank').first.wait_for()
  for i,row in enumerate(group['items']):
   page.wait_for_function('document.querySelector(".translation-picture img")?.naturalWidth>0')
   assert page.locator('.translation-picture').get_attribute('data-scene-id')==row['id']
   canonical=page.evaluate('(id)=>FROG_WORD_CATALOG.words.find(w=>w.id===id)',row['id'])
   assert (canonical['word'],canonical['meaning'],canonical['ipa'],canonical['example'],canonical['exampleZh'])==(row['english'],row['chinese'],row['ipa_dj_british'],row['example_en'],row['example_zh'])
   assert page.evaluate('(w)=>!!FrogPractice.wordCloze(w)',canonical)
   assert page.locator('.word-example-prompt').inner_text()==row['example_zh']
   assert page.locator('.word-example-prompt [data-meaning-target="chinese"]').all_text_contents()==[s['text'] for s in meanings[row['id']]['spans']]
   assert row['chinese'] in page.locator('.word-context-meaning').inner_text()
   page.locator('#translation-form [data-action="translation-answer"]').click();answer=page.locator('#practice-answer-dialog')
   assert answer.locator('.mvp-answer-line>span:not(.mvp-dj)').inner_text()==row['ipa_dj_british']
   expected=page.evaluate('(s)=>s.trim().replace(/[\\s\\p{P}\\p{S}]+$/u,"")',row['example_en'])
   assert answer.locator('.mvp-answer-english strong').inner_text()==expected
   if i in (0,len(group['items'])-1) or row['english'] in ('lead','kid','ewe','poppy','sea anemone'):
    for role,text in [('word',row['english']),('example',row['example_en'])]:
     answer.locator(f'[data-answer-audio="{role}"]').click()
     page.wait_for_function('(text)=>{const a=document.querySelector("#question-audio");return FrogPractice.normalize(a.dataset.sourceText)===FrogPractice.normalize(text)&&a.currentTime>0&&!a.paused}',arg=text)
     assert answer.evaluate('e=>e.open')
   answer.locator('[data-answer-close]').click()
   if i<len(group['items'])-1:page.keyboard.press('Shift+ArrowRight')
  page.locator('.practice-back').click();page.wait_for_function('!document.querySelector("#lesson-dialog").open')
  print('PASS: all source DJ, examples, Chinese targets, scenes, answer and audio flow in '+group['window_name'],flush=True)
 assert not saved()['wordStatus']
 # Same existing search controls; exercise distinct words, Chinese and example text.
 for query,english in [('HAMSTER','hamster'),('长颈鹿','giraffe'),('A clownfish may live near','sea anemone')]:
  page.locator('#global-search').fill(query);page.locator('#global-search').press('Enter')
  card=page.locator(f'.search-results .word-card[data-word="{english}"]');card.wait_for(state='visible')
  row=next(w for w in words if w['english']==english)
  for selector,text in [('[data-action="speak-word"]',row['english']),('.word-example-speak',row['example_en'])]:
   card.locator(selector).click();page.wait_for_function('(text)=>{const a=document.querySelector("#question-audio");return a.dataset.sourceText===text&&a.currentTime>0&&!a.paused}',arg=text)
 assert not errors,errors
 context.close()
 for mobile in (False,True):
  context=browser.new_context(viewport={'width':390 if mobile else 1440,'height':844 if mobile else 960},is_mobile=mobile,has_touch=mobile,service_workers='block')
  page=context.new_page();page.goto(BASE+'#words/C06/C06-S01');page.locator('.translation-blank').first.fill('pet')
  page.locator('.mobile-controls [data-action="translation-submit"]' if mobile else '#translation-submit').click()
  assert saved()['wordStatus']['C06-S01-001']=='mastered'
  page.locator('.mobile-controls [data-action="next-item"]' if mobile else '.mvp-solved-actions [data-action="next-item"]').last.click()
  assert page.locator('.translation-picture').get_attribute('data-scene-id')=='C06-S01-002'
  assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
  if not mobile:
   page.locator('#translation-previous').click();assert page.locator('.translation-picture').get_attribute('data-scene-id')=='C06-S01-001'
   page.locator('#restart-practice-group').click();assert page.locator('#translation-previous').is_disabled()
  context.close()
 browser.close()
print('COMPLETE: C06 source, additive migration, all 238 entries and desktop/mobile search/practice/audio passed',flush=True)
