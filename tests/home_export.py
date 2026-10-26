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
 assert page.locator('#offline-html-source').input_value()==''
 with TemporaryDirectory(prefix='home-export-') as directory:
  with page.expect_download() as dl:page.locator('#save-app-dialog [data-action="download-app-file"]').click()
  dl.value.save_as(Path(directory)/'index.html')
  markers=['id="home-art-snapshot"','window.FROG_HOME_ART="data:image/png;base64,','id="scene-art-snapshot"','window.FROG_SCENE_IMAGES=','id="category-art-snapshot"','window.FROG_CATEGORY_IMAGES=']
  found=set()
  with (Path(directory)/'index.html').open() as source:
   for line in source:
    found.update(marker for marker in markers if marker in line)
  assert found==set(markers)
  page.locator('#source-fallback>summary').click()
  # The full media archive is about 395 MB; source-editor layout can take
  # longer than navigation on a shared runner. Keep the full-value/hash checks.
  page.wait_for_function('document.querySelector("#offline-html-source").value.length>1000000',timeout=180000)
  page.locator('[data-action="select-html-source"]').click()
  assert page.locator('#offline-html-source').evaluate('e=>e.selectionStart===0&&e.selectionEnd===e.value.length&&e.wrap==="off"')
  page.locator('#offline-html-source').evaluate('e=>e.value=""')
  page.locator('#save-app-dialog .dialog-back').click()
  print('PASS: real Blob download and on-demand complete source selection; generated HTML carries all artwork maps',flush=True)
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
   assert exported.evaluate('Object.keys(FROG_SCENE_IMAGES).length')==110
   assert exported.evaluate('Object.keys(FROG_CATEGORY_IMAGES).length')==4
   # Validate every decoded recording/image after script line-continuation formatting.
   verified=exported.evaluate('''async()=>{
    const rows=[...Object.entries(LOCAL_AUDIO_BANK.clips).map(([key,data])=>({data,hash:LOCAL_AUDIO_BANK.sha256[key]})),...FROG_SCENE_LIBRARY.sheets.map(s=>({data:FROG_SCENE_IMAGES[s.path].split(',')[1],hash:s.sha256})),...FROG_CATEGORY_ART.sheets.map(s=>({data:FROG_CATEGORY_IMAGES[s.path].split(',')[1],hash:s.sha256}))];
    let next=0;
    await Promise.all(Array.from({length:3},async()=>{while(next<rows.length){const row=rows[next++],bytes=Uint8Array.from(atob(row.data),c=>c.charCodeAt(0)),hash=Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',bytes)),n=>n.toString(16).padStart(2,'0')).join('');if(hash!==row.hash)throw new Error('Exported media bytes changed');}}));
    return rows.length;
   }''')
   assert verified==2169+110+4
   assert exported.locator('.startup-screen').is_hidden()
   isolated.set_offline(True)
   for category in range(1,9):
    exported.goto(f'http://127.0.0.1:{server.server_port}/#words/C{category:02}')
    exported.wait_for_function('document.querySelectorAll(".mvp-subcategory-art img").length===4&&[...document.querySelectorAll(".mvp-subcategory-art img")].every(img=>img.complete&&img.naturalWidth>0)')
    assert all(src.startswith('data:image/webp;base64,') for src in exported.locator('.mvp-subcategory-art img').evaluate_all('(images)=>images.map(img=>img.src)'))
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
   assert exported.evaluate('FROG_MEANING_LIBRARY.entries.length')==972
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
   assert exported.locator('.word-context-meaning .meaning-dictionary').inner_text()=='词义：一些；任何（依语境）'
   assert exported.locator('.word-example-prompt [data-meaning-target]').count()==0
   exported.evaluate("window.packClosed=false;document.querySelector('#lesson-dialog').addEventListener('close',()=>packClosed=true,{once:true})")
   exported.locator('.practice-back').click();exported.wait_for_function('packClosed')
   exported.goto(f'http://127.0.0.1:{server.server_port}/#words/C02/C02-S01')
   exported.locator('.translation-blank').first.wait_for()
   exported.wait_for_function('document.querySelector(".translation-picture img")?.naturalWidth>0')
   assert exported.locator('.translation-picture img').get_attribute('src').startswith('data:image/webp;base64,')
   exported.locator('.translation-blank').fill('time');exported.locator('#translation-submit').click()
   exported.wait_for_function('document.querySelector("#question-audio").dataset.audioKey==="time"&&document.querySelector("#question-audio").currentTime>0')
   exported.locator('.practice-back').click();exported.wait_for_function('!document.querySelector("#lesson-dialog").open')
   exported.goto(f'http://127.0.0.1:{server.server_port}/#words/C03/C03-S01')
   exported.locator('.translation-blank').first.wait_for()
   exported.wait_for_function('document.querySelector(".translation-picture img")?.naturalWidth>0')
   assert exported.locator('.translation-picture img').get_attribute('src').startswith('data:image/webp;base64,')
   exported.locator('.translation-blank').first.fill('schoolbag');exported.locator('#translation-submit').click()
   exported.wait_for_function('document.querySelector("#question-audio").dataset.audioKey==="schoolbag"&&document.querySelector("#question-audio").currentTime>0')
   exported.locator('.practice-back').click();exported.wait_for_function('!document.querySelector("#lesson-dialog").open')
   exported.goto(f'http://127.0.0.1:{server.server_port}/#words/C04/C04-S01')
   exported.locator('.translation-blank').first.wait_for()
   exported.wait_for_function('document.querySelector(".translation-picture img")?.naturalWidth>0')
   assert exported.locator('.translation-picture img').get_attribute('src').startswith('data:image/webp;base64,')
   exported.locator('.translation-blank').first.fill('family');exported.locator('#translation-submit').click()
   exported.wait_for_function('document.querySelector("#question-audio").dataset.audioKey==="family"&&document.querySelector("#question-audio").currentTime>0')
   exported.locator('.practice-back').click();exported.wait_for_function('!document.querySelector("#lesson-dialog").open')
   exported.goto(f'http://127.0.0.1:{server.server_port}/#words/C05')
   exported.locator('.mvp-subcategory[data-subcategory-id="C05-S04"]').click()
   assert exported.locator('#practice-group-dialog .practice-group-choice').count()==3
   assert exported.locator('#practice-group-dialog .practice-group-all b').inner_text()=='44'
   exported.locator('#practice-group-dialog [data-practice-group="medical-care-and-recovery"]').click()
   assert exported.locator('#practice-jump option').count()==15
   assert exported.locator('.translation-picture').get_attribute('data-scene-id')=='C05-S06-030'
   exported.locator('.practice-back').click();exported.wait_for_function('!document.querySelector("#lesson-dialog").open')
   exported.goto(f'http://127.0.0.1:{server.server_port}/#words/C05/C05-S01')
   exported.locator('.translation-blank').first.wait_for()
   exported.wait_for_function('document.querySelector(".translation-picture img")?.naturalWidth>0')
   assert exported.locator('.translation-picture img').get_attribute('src').startswith('data:image/webp;base64,')
   exported.locator('.translation-blank').first.fill('apple');exported.locator('#translation-submit').click()
   exported.wait_for_function('document.querySelector("#question-audio").dataset.audioKey==="apple"&&document.querySelector("#question-audio").currentTime>0')
   assert not errors,errors
   print('PASS: home menu exports one HTML with the new hero, saved name/notes/progress and MP3 playback without original assets',flush=True)
  finally:
   isolated.close();server.shutdown();server.server_close()
 context.close();browser.close()
print('COMPLETE: home illustration and personal single-file export passed',flush=True)
