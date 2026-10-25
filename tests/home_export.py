"""The home user-menu export carries its new illustration and original MP3s."""
import threading
import base64
import hashlib
from functools import partial
from http.server import SimpleHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path
from tempfile import TemporaryDirectory
from playwright.sync_api import sync_playwright

class Quiet(SimpleHTTPRequestHandler):
 def log_message(self,*args):pass

with sync_playwright() as p:
 browser=p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox'])
 context=browser.new_context(viewport={'width':1440,'height':960},accept_downloads=True)
 context.add_init_script("Object.defineProperty(window,'speechSynthesis',{get(){throw new Error('TTS forbidden')}})")
 page=context.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
 page.goto('http://127.0.0.1:8000/#home')
 page.evaluate('''()=>{const key=document.body.dataset.storageKey,s=JSON.parse(localStorage.getItem(key)),ids=FROG_WORD_CATALOG.words.filter(w=>w.subcategoryId==='C01-S01').map(w=>w.id);ids.forEach(id=>s.wordStatus[id]='mastered');s.practiceResume={ids,wordId:ids[2],answered:true,finished:false};s.settings.userName='导出学习者';s.settings.grade='四年级';s.notes=[{id:'export-home-note',title:'原有手账',body:'需要保留的记录',createdAt:'2026-10-01T00:00:00Z',updatedAt:'2026-10-01T00:00:00Z'}];localStorage.setItem(key,JSON.stringify(s));}''')
 page.reload();page.locator('#home-user-menu>summary').click()
 page.locator('#home-user-menu [data-action="save-app"]').click()
 page.locator('#save-app-dialog [data-action="download-app-file"]').wait_for(timeout=90000)
 html=page.locator('#offline-html-source').input_value()
 assert 'id="home-art-snapshot"' in html and 'window.FROG_HOME_ART="data:image/png;base64,' in html
 assert 'id="scene-art-snapshot"' in html and 'window.FROG_SCENE_IMAGES=' in html
 with TemporaryDirectory(prefix='home-export-') as directory:
  with page.expect_download() as dl:page.locator('#save-app-dialog [data-action="download-app-file"]').click()
  dl.value.save_as(Path(directory)/'index.html')
  server=ThreadingHTTPServer(('127.0.0.1',0),partial(Quiet,directory=directory))
  threading.Thread(target=server.serve_forever,daemon=True).start()
  isolated=browser.new_context(viewport={'width':1440,'height':960},service_workers='block')
  isolated.add_init_script("Object.defineProperty(window,'speechSynthesis',{get(){throw new Error('TTS forbidden')}})")
  try:
   exported=isolated.new_page();exported.on('pageerror',lambda e:errors.append(str(e)))
   exported.goto(f'http://127.0.0.1:{server.server_port}/#home',timeout=90000)
   exported.wait_for_function('document.querySelector(".home-hero-illustration img")?.naturalWidth>0')
   assert exported.locator('.home-hero-illustration img').get_attribute('src').startswith('data:image/png;base64,')
   assert '导出学习者' in exported.locator('#home-user-menu>summary').inner_text()
   stored=exported.evaluate('JSON.parse(localStorage.getItem(document.body.dataset.storageKey))')
   assert stored['wordStatus']['C01-S01-001']=='mastered' and stored['notes'][0]['body']=='需要保留的记录'
   assert stored['practiceResume']['answered'] is True
   assert stored['settings']['grade']=='四年级'
   assert exported.evaluate('Object.keys(FROG_SCENE_IMAGES).length')==18
   assert exported.locator('.startup-screen').is_hidden()
   isolated.set_offline(True)
   exported.goto(f'http://127.0.0.1:{server.server_port}/#records')
   exported.locator('.progress-dashboard').wait_for()
   assert exported.locator('[data-progress-total-words]').inner_text()=='22个'
   exported.locator('[data-progress-trend="words"]').click()
   assert exported.locator('.progress-chart-bar').count()==7
   exported.goto(f'http://127.0.0.1:{server.server_port}/#home')
   exported.locator('.home-resume-card [data-action="resume-desktop"]').click()
   exported.locator('.translation-blank').first.wait_for()
   assert '4/22' in exported.locator('#lesson-course').inner_text()
   exported.wait_for_function('document.querySelector(".translation-picture img")?.naturalWidth>0')
   assert exported.locator('.translation-picture').get_attribute('data-scene-id')=='C01-S01-004'
   assert exported.locator('.translation-picture img').get_attribute('src').startswith('data:image/png;base64,')
   for field,value in zip(exported.locator('.translation-blank').all(),['good','afternoon']):field.fill(value)
   exported.locator('#translation-submit').click()
   exported.wait_for_function('document.querySelector("#question-audio").dataset.sourceText==="good afternoon"&&document.querySelector("#question-audio").currentTime>0')
   exported.locator('.mvp-practice-info .practice-options>summary').click()
   exported.locator('#practice-jump').select_option('8')
   exported.wait_for_function('document.querySelector(".translation-picture img")?.naturalWidth>0')
   assert exported.locator('.translation-picture').get_attribute('data-scene-id')=='C01-S01-009'
   art=exported.locator('.translation-picture img').get_attribute('src')
   assert art.startswith('data:image/png;base64,')
   assert hashlib.sha256(base64.b64decode(art.split(',',1)[1])).digest()==hashlib.sha256((Path(__file__).resolve().parents[1]/'assets/scenes/see-you-tomorrow.png').read_bytes()).digest()
   assert exported.evaluate('FROG_MEANING_LIBRARY.entries.length')==136
   exported.evaluate("window.meaningClosed=false;document.querySelector('#lesson-dialog').addEventListener('close',()=>window.meaningClosed=true,{once:true})")
   exported.locator('.practice-back').click();exported.wait_for_function('meaningClosed')
   exported.goto(f'http://127.0.0.1:{server.server_port}/#words/C01/C01-S02')
   exported.locator('.translation-blank').first.wait_for()
   exported.locator('#practice-jump').evaluate('e=>{e.value="49";e.dispatchEvent(new Event("change",{bubbles:true}))}')
   assert exported.locator('.word-example-prompt [data-meaning-target="chinese"]').inner_text()=='半个'
   exported.locator('#translation-form [data-action="translation-answer"]').click()
   assert exported.locator('#practice-answer-dialog [data-meaning-target="english"]').inner_text()=='half'
   exported.locator('#practice-answer-dialog [data-answer-close]').click()
   exported.locator('#practice-jump').evaluate('e=>{e.value="47";e.dispatchEvent(new Event("change",{bubbles:true}))}')
   assert '中文通常不单独翻译' in exported.locator('.word-context-meaning').inner_text()
   assert exported.locator('.word-example-prompt [data-meaning-target]').count()==0
   assert not errors,errors
   print('PASS: home menu exports one HTML with the new hero, saved name/notes/progress and MP3 playback without original assets',flush=True)
  finally:
   isolated.close();server.shutdown();server.server_close()
 context.close();browser.close()
print('COMPLETE: home illustration and personal single-file export passed',flush=True)
