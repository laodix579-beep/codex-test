"""Validate the existing deployment ZIP under a GitHub Pages-style subdirectory."""
import hashlib
import json
import sys
import threading
import zipfile
from functools import partial
from http.server import SimpleHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path
from tempfile import TemporaryDirectory
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]
class Quiet(SimpleHTTPRequestHandler):
 def log_message(self,*args):pass

with TemporaryDirectory(prefix='mvp-pages-') as directory:
 target=Path(directory)/'codex-test';target.mkdir()
 with zipfile.ZipFile(Path(sys.argv[1]) if len(sys.argv)>1 else Path('/workspace/output/laok-pages-v37.zip')) as archive:
  assert archive.testzip() is None
  assert archive.read('index.html')==archive.read('小蛙自习室.html')==(ROOT/'index.html').read_bytes()
  assert archive.read('assets/home-hero.png')==(ROOT/'assets/home-hero.png').read_bytes()
  scenes=json.loads(archive.read('data/scene-catalog.json'))
  assert len(scenes['scenes'])==754 and len(scenes['sheets'])==82
  assert len(json.loads(archive.read('data/meaning-catalog.json'))['entries'])==754
  for sheet in scenes['sheets']:assert hashlib.sha256(archive.read(sheet['path'])).hexdigest()==sheet['sha256']
  backgrounds=json.loads(archive.read('data/category-art.json'))
  assert len(backgrounds['entries'])==32 and len(backgrounds['sheets'])==4
  for sheet in backgrounds['sheets']:assert hashlib.sha256(archive.read(sheet['path'])).hexdigest()==sheet['sha256']
  audit=json.loads(archive.read('reports/all-audio-sha256.json'))
  assert len(audit)==1752
  for path,row in audit.items():assert hashlib.sha256(archive.read(path)).hexdigest()==row['sha256']
  for name in archive.namelist():assert (target/name).resolve().is_relative_to(target.resolve())
  archive.extractall(target)
 server=ThreadingHTTPServer(('127.0.0.1',0),partial(Quiet,directory=directory))
 threading.Thread(target=server.serve_forever,daemon=True).start()
 try:
  with sync_playwright() as p:
   browser=p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox'])
   for mobile in (False,True):
    context=browser.new_context(viewport={'width':390 if mobile else 1440,'height':844 if mobile else 960},is_mobile=mobile,has_touch=mobile)
    context.add_init_script('''{
     Object.defineProperty(window,'speechSynthesis',{get(){throw new Error('TTS forbidden')}});
     const pending=sessionStorage.getItem('pages-next-state');
     if(pending){const fixture=JSON.parse(pending);sessionStorage.removeItem('pages-next-state');localStorage.setItem(fixture.key,fixture.value);}
    }''')
    page=context.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
    base=f'http://127.0.0.1:{server.server_port}/codex-test/'
    page.goto(base+'#home')
    assert page.locator('.mvp-resume').is_visible() if not mobile else page.locator('.dashboard-header').is_visible()
    page.goto(base+'#settings')
    page.wait_for_function('document.querySelector("[data-mobile-status]").textContent.startsWith("已保存离线内容")',timeout=90000)
    context.set_offline(True)
    page.goto(base+'#profile');page.reload();page.locator('#profile-form').wait_for()
    page.locator('#profile-name').fill('离线学习者');page.locator('#profile-grade').fill('三年级')
    page.locator('#profile-form button[type="submit"]').click()
    page.wait_for_function('location.hash==="#home"')
    assert page.evaluate('JSON.parse(localStorage.getItem(document.body.dataset.storageKey)).settings.grade')=='三年级'
    if not mobile:
     page.goto(base+'#home');page.reload()
     page.wait_for_function('document.querySelector(".home-hero-illustration img")?.naturalWidth>0')
     assert page.locator('.home-category-tile').count()==8
     assert page.locator('#home-user-menu>summary').is_visible()
    page.goto(base+'#words');page.reload()
    assert page.locator('.vocab-category').count()==(4 if mobile else 8)
    if not mobile:
     page.goto(base+'#words/C01')
     page.wait_for_function('document.querySelectorAll(".mvp-subcategory-art img").length===4&&[...document.querySelectorAll(".mvp-subcategory-art img")].every(img=>img.complete&&img.naturalWidth>0)')
     assert page.evaluate('async()=>{const r=await fetch("data/category-art.json");return (await r.json()).entries.length}')==32
     page.locator('.mvp-subcategory[data-subcategory-id="C01-S01"]').click()
     assert page.locator('#practice-group-dialog .practice-group-all b').inner_text()=='22'
     assert page.locator('#practice-group-dialog [data-practice-group="politeness"] b').inner_text()=='8'
     page.locator('#practice-group-dialog [data-practice-group="politeness"]').click()
     page.locator('.translation-blank').first.wait_for();assert page.locator('#practice-jump option').count()==8
     assert page.locator('.translation-picture').get_attribute('data-scene-id')=='C01-S01-011'
     page.locator('.translation-blank').first.fill('draft')
     page.locator('#translation-form [data-action="next-item"]').click()
     page.locator('#translation-previous').click()
     assert page.locator('.translation-blank').first.input_value()=='draft'
     page.locator('#restart-practice-group').click()
     assert '1/8' in page.locator('#lesson-course').inner_text()
     assert page.locator('.translation-blank').first.input_value()==''
     assert page.locator('#translation-previous').is_disabled()
     page.locator('.practice-back').click();page.wait_for_function('!document.querySelector("#lesson-dialog").open')
     assert page.evaluate('async()=>{const r=await fetch("data/practice-groups.json");return (await r.json()).subcategories.length}')==15
    page.goto(base+'#words/C01/C01-S01');page.locator('.translation-blank').wait_for()
    page.wait_for_function('document.querySelector(".translation-picture img")?.naturalWidth>0')
    assert page.locator('.translation-picture').get_attribute('data-scene-id')=='C01-S01-001'
    page.locator('#practice-jump').evaluate('e=>{e.value="19";e.dispatchEvent(new Event("change",{bubbles:true}))}')
    assert page.locator('.contraction-hint svg').is_visible()
    assert page.locator('.contraction-hint').evaluate('e=>e.previousElementSibling.matches(".translation-slots")')
    assert '缩写形式' in page.locator('.contraction-hint').inner_text()
    page.locator('#practice-jump').evaluate('e=>{e.value="0";e.dispatchEvent(new Event("change",{bubbles:true}))}')
    assert page.locator('.contraction-hint').count()==0
    if not mobile:
     page.locator('#translation-form [data-action="translation-answer"]').click()
     assert page.locator('#practice-answer-dialog strong').inner_text()=='Hello, Anna'
     page.keyboard.down('a');page.keyboard.down('a');page.keyboard.down('a');page.keyboard.up('a')
     assert page.locator('.translation-blank').input_value()==''
     assert page.locator('#practice-answer-dialog').evaluate('e=>!e.open')
    if not mobile:
     page.locator('.translation-blank').fill('he');page.locator('.translation-picture').click();page.keyboard.type('llo')
     assert page.locator('.translation-blank').input_value()=='hello'
     assert page.locator('.translation-blank').evaluate('e=>document.activeElement===e')
    else:page.locator('.translation-blank').fill('hello')
    page.locator('.mobile-controls [data-action="translation-submit"]' if mobile else '#translation-submit').click()
    page.wait_for_function('document.querySelector("#question-audio").dataset.sourceText==="hello"&&document.querySelector("#question-audio").currentTime>0')
    assert '/codex-test/audio/' in page.locator('#question-audio').get_attribute('data-recording-path')
    assert page.locator('#question-audio').get_attribute('src').startswith('blob:')
    ranged=page.evaluate('''async()=>{const r=await fetch(new URL(LOCAL_AUDIO_BANK.clips.hello,document.baseURI),{headers:{Range:'bytes=10-40'}});return {status:r.status,bytes:(await r.arrayBuffer()).byteLength,range:r.headers.get('Content-Range')}}''')
    assert ranged['status']==206 and ranged['bytes']==31 and ranged['range'].startswith('bytes 10-40/')
    page.locator('.practice-back').click();page.wait_for_function('!document.querySelector("#lesson-dialog").open')
    if not mobile:
     # Apply this fixture after the old page's legitimate unload/time save.
     page.evaluate('''()=>{const key=document.body.dataset.storageKey,s=JSON.parse(localStorage.getItem(key)),ids=FROG_WORD_CATALOG.words.filter(w=>w.subcategoryId==='C01-S01').map(w=>w.id);ids.forEach(id=>s.wordStatus[id]='mastered');s.practiceResume={ids,wordId:ids[3],answered:false,finished:false};sessionStorage.setItem('pages-next-state',JSON.stringify({key,value:JSON.stringify(s)}));}''')
     page.goto(base+'#home');page.reload()
     page.wait_for_function('document.querySelector(".mvp-resume-title")?.textContent.includes("第 4 / 22 词")')
     page.locator('.home-resume-card [data-action="resume-desktop"]').click()
     assert '4/22' in page.locator('#lesson-course').inner_text()
     page.wait_for_function('document.querySelector(".translation-picture img")?.naturalWidth>0')
     assert page.locator('.translation-picture').get_attribute('data-scene-id')=='C01-S01-004'
     page.locator('.mvp-practice-info .practice-options>summary').click();page.locator('#practice-jump').select_option('8')
     page.wait_for_function('document.querySelector(".translation-picture img")?.naturalWidth>0')
     assert page.locator('.translation-picture').get_attribute('data-scene-id')=='C01-S01-009'
     assert page.locator('.translation-picture img').get_attribute('src').endswith('/assets/scenes/see-you-tomorrow.png')
     page.locator('.practice-back').click();page.wait_for_function('!document.querySelector("#lesson-dialog").open')
     page.goto(base+'#records');page.reload()
     page.locator('.progress-dashboard').wait_for()
     assert page.locator('.progress-metric').count()==4
     assert page.locator('[data-progress-category="C01"] .progress-category-count').inner_text()=='22 / 136'
     page.locator('[data-progress-trend="words"]').click()
     assert page.locator('.progress-chart-bar').count()==7
     page.locator('.progress-chart-bar.today').click()
     assert page.locator('#progress-day-dialog').is_visible()
     page.locator('#progress-day-dialog [data-close]').click()
     page.locator('.progress-records [data-route="records/history"]').click()
     page.locator('.progress-history').wait_for()
     assert page.locator('.progress-record-table tbody tr').count()==1
    page.goto(base+'#words/C01/C01-S02');page.locator('.translation-blank').first.wait_for()
    page.locator('#practice-jump').evaluate('e=>{e.value="49";e.dispatchEvent(new Event("change",{bubbles:true}))}')
    assert page.locator('.word-example-prompt [data-meaning-target="chinese"]').inner_text()=='半个'
    page.locator('.mobile-controls [data-action="translation-answer"]' if mobile else '#translation-form [data-action="translation-answer"]').click()
    assert page.locator('.translation-answer [data-meaning-target="english"]' if mobile else '#practice-answer-dialog [data-meaning-target="english"]').inner_text()=='half'
    if not mobile:page.locator('#practice-answer-dialog [data-answer-close]').click()
    page.locator('#practice-jump').evaluate('e=>{e.value="47";e.dispatchEvent(new Event("change",{bubbles:true}))}')
    assert '中文通常不单独翻译' in page.locator('.word-context-meaning').inner_text()
    assert page.locator('.word-context-meaning .meaning-dictionary').inner_text()=='词义：一些；任何（依语境）'
    assert page.locator('.word-example-prompt [data-meaning-target]').count()==0
    cached_meanings=page.evaluate('async()=>{const r=await fetch("data/meaning-catalog.json");return (await r.json()).entries.length}')
    assert cached_meanings==754
    page.evaluate("window.packClosed=false;document.querySelector('#lesson-dialog').addEventListener('close',()=>packClosed=true,{once:true})")
    page.locator('.practice-back').click();page.wait_for_function('packClosed')
    for sub,filename,count in [('C02-S01','01_时间与钟表.json',52),('C02-S02','02_星期与日期.json',61),('C02-S03','03_月份与四季.json',56),('C02-S04','04_天气与气候.json',51),('C03-S01','01_学习用品.json',43),('C03-S02','02_教室与校园.json',45),('C03-S03','03_学科名称.json',31),('C03-S04','04_课堂常用词.json',79),('C04-S01','01_家庭成员.json',33),('C04-S02','02_房间与家具.json',44),('C04-S03','03_家居用品.json',53),('C04-S04','04_日常生活与作息.json',70)]:
     raw=page.evaluate('async path=>(await(await fetch(path)).json())',({'C02':'data/time-nature/','C03':'data/school-learning/','C04':'data/family-daily/'}[sub[:3]])+filename)
     assert len(raw['items'])==count
     page.goto(base+'#words/'+sub[:3]+'/'+sub);page.locator('.translation-blank').first.wait_for()
     page.wait_for_function('document.querySelector(".translation-picture img")?.naturalWidth>0')
     word=page.evaluate('(id)=>FROG_WORD_CATALOG.words.find(w=>w.id===id)',sub+'-001')
     assert page.locator('.translation-picture').get_attribute('data-scene-id')==word['id']
     assert page.locator('.translation-picture img').get_attribute('src').endswith('.webp')
     blanks=page.evaluate('w=>{const c=FrogPractice.wordCloze(w);return FrogPractice.sentenceTokens(c.english).filter(t=>t.word&&c.blankIndices.includes(t.index)).map(t=>t.text)}',word)
     for field,text in zip(page.locator('.translation-blank').all(),blanks):field.fill(text)
     page.locator('.mobile-controls [data-action="translation-submit"]' if mobile else '#translation-submit').click()
     page.wait_for_function('(text)=>{const a=document.querySelector("#question-audio");return FrogPractice.normalize(a.dataset.sourceText)===FrogPractice.normalize(text)&&a.currentTime>0}',arg=word['word'])
     assert page.evaluate('(id)=>JSON.parse(localStorage.getItem(document.body.dataset.storageKey)).wordStatus[id]',word['id'])=='mastered'
     page.evaluate("window.packClosed=false;document.querySelector('#lesson-dialog').addEventListener('close',()=>packClosed=true,{once:true})")
     page.locator('.practice-back').click();page.wait_for_function('packClosed')
    page.goto(base+'小蛙自习室.html#words');page.wait_for_selector('.vocab-category')
    assert page.locator('.vocab-category').count()==(4 if mobile else 8)
    assert not errors,errors
    print(f'PASS: extracted ZIP {"phone" if mobile else "desktop"}, subdirectory routes, offline UI, original MP3, byte range, compatibility entry and key repeats',flush=True)
    context.close()
   browser.close()
 finally:
  server.shutdown();server.server_close()
print('COMPLETE: existing deployment ZIP passed structural, 1752 MP3 hash and browser checks',flush=True)
