"""Validate the existing deployment ZIP under a GitHub Pages-style subdirectory."""
import hashlib
import json
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
 with zipfile.ZipFile(ROOT/'downloads/frog-study-offline.zip') as archive:
  assert archive.testzip() is None
  assert archive.read('index.html')==archive.read('小蛙自习室.html')==(ROOT/'index.html').read_bytes()
  assert archive.read('assets/home-hero.png')==(ROOT/'assets/home-hero.png').read_bytes()
  scenes=json.loads(archive.read('data/scene-catalog.json'))
  assert len(scenes['scenes'])==136 and len(scenes['sheets'])==17
  for sheet in scenes['sheets']:assert hashlib.sha256(archive.read(sheet['path'])).hexdigest()==sheet['sha256']
  audit=json.loads(archive.read('reports/source-audio-sha256.json'))
  assert len(audit)==610
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
    context.add_init_script("Object.defineProperty(window,'speechSynthesis',{get(){throw new Error('TTS forbidden')}})")
    page=context.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
    base=f'http://127.0.0.1:{server.server_port}/codex-test/'
    page.goto(base+'#home')
    assert page.locator('.mvp-resume').is_visible() if not mobile else page.locator('.dashboard-header').is_visible()
    page.goto(base+'#settings')
    page.wait_for_function('document.querySelector("[data-mobile-status]").textContent.startsWith("已保存离线内容")',timeout=90000)
    context.set_offline(True)
    if not mobile:
     page.goto(base+'#home');page.reload()
     page.wait_for_function('document.querySelector(".home-hero-illustration img")?.naturalWidth>0')
     assert page.locator('.home-category-tile').count()==8
     assert page.locator('#home-user-menu>summary').is_visible()
    page.goto(base+'#words');page.reload()
    assert page.locator('.vocab-category').count()==(1 if mobile else 8)
    page.goto(base+'#words/C01/C01-S01');page.locator('.translation-blank').wait_for()
    page.wait_for_function('document.querySelector(".translation-picture img")?.naturalWidth>0')
    assert page.locator('.translation-picture').get_attribute('data-scene-id')=='C01-S01-001'
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
    assert '/codex-test/audio/' in page.locator('#question-audio').get_attribute('src')
    ranged=page.evaluate('''async()=>{const r=await fetch(new URL(LOCAL_AUDIO_BANK.clips.hello,document.baseURI),{headers:{Range:'bytes=10-40'}});return {status:r.status,bytes:(await r.arrayBuffer()).byteLength,range:r.headers.get('Content-Range')}}''')
    assert ranged['status']==206 and ranged['bytes']==31 and ranged['range'].startswith('bytes 10-40/')
    page.locator('.practice-back').click();page.wait_for_function('!document.querySelector("#lesson-dialog").open')
    if not mobile:
     page.evaluate('''()=>{const key=document.body.dataset.storageKey,s=JSON.parse(localStorage.getItem(key)),ids=FROG_WORD_CATALOG.words.filter(w=>w.subcategoryId==='C01-S01').map(w=>w.id);ids.forEach(id=>s.wordStatus[id]='mastered');s.practiceResume={ids,wordId:ids[3],answered:false,finished:false};localStorage.setItem(key,JSON.stringify(s));}''')
     page.goto(base+'#home');page.reload()
     page.wait_for_function('document.querySelector(".mvp-resume-title")?.textContent.includes("第 4 / 22 词")')
     page.locator('.home-resume-card [data-action="resume-desktop"]').click()
     assert '4/22' in page.locator('#lesson-course').inner_text()
     page.wait_for_function('document.querySelector(".translation-picture img")?.naturalWidth>0')
     assert page.locator('.translation-picture').get_attribute('data-scene-id')=='C01-S01-004'
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
    page.goto(base+'小蛙自习室.html#words');page.wait_for_selector('.vocab-category')
    assert page.locator('.vocab-category').count()==(1 if mobile else 8)
    assert not errors,errors
    print(f'PASS: extracted ZIP {"phone" if mobile else "desktop"}, subdirectory routes, offline UI, original MP3, byte range, compatibility entry and key repeats',flush=True)
    context.close()
   browser.close()
 finally:
  server.shutdown();server.server_close()
print('COMPLETE: existing deployment ZIP passed structural, 610 MP3 hash and browser checks',flush=True)
