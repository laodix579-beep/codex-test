"""Shared light dashboard on phones; touch inputs, data, routes and desktop intact."""
import hashlib
import json
from pathlib import Path
import re
import subprocess
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]
BASE='http://127.0.0.1:8000/'
BASELINE='98be4c99abe18db3bfa53da2b4e8bb7c0d98e8b7'
def before(path):return subprocess.check_output(['git','show',BASELINE+':'+path],cwd=ROOT)
html=(ROOT/'index.html').read_text();old_html=before('index.html').decode()
# The shared mobile template stays intact while a new C07 data pack is added.
old_catalog=json.JSONDecoder().raw_decode(old_html.split('window.FROG_WORD_CATALOG = ',1)[1])[0]
catalog=json.JSONDecoder().raw_decode(html.split('window.FROG_WORD_CATALOG = ',1)[1])[0]
assert [w for w in catalog['words'] if w['categoryId']!='C07']==old_catalog['words']
assert len(catalog['words'])==1428
assert (ROOT/'data/category-art.json').read_bytes()==before('data/category-art.json')
for path,row in json.loads((ROOT/'reports/all-audio-sha256.json').read_text()).items():assert hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==row['sha256']
assert (ROOT/'小蛙自习室.html').read_bytes()==(ROOT/'index.html').read_bytes()
assert json.loads((ROOT/'manifest.webmanifest').read_text())['theme_color']=='#f6f7ff'
print('PASS: all 1210 earlier words/media retained; additive C07 catalog, light theme and compatibility entry match',flush=True)

with sync_playwright() as p:
 browser=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
 errors=[]
 for width in [320,360,390,430,768,1024]:
  context=browser.new_context(viewport={'width':width,'height':844},is_mobile=True,has_touch=True,user_agent=p.devices['iPhone 13']['user_agent'],color_scheme='dark',service_workers='block')
  context.add_init_script("Object.defineProperty(window,'speechSynthesis',{get(){throw new Error('Runtime TTS forbidden')}})")
  page=context.new_page();page.on('pageerror',lambda e:errors.append(str(e)))
  for route,selector in [('home','.home-hero'),('words','.mvp-catalog-grid'),('words/C06','.mvp-subcategory'),('records','.progress-dashboard'),('profile','#profile-form'),('plan','#plan-form'),('settings','#settings-form')]:
   page.goto(BASE+'#'+route);page.locator(selector).first.wait_for()
   assert page.evaluate('document.body.classList.contains("mobile-mvp")')
   assert page.evaluate('getComputedStyle(document.body).backgroundColor')=='rgb(246, 247, 255)'
   assert page.evaluate('document.documentElement.scrollWidth<=innerWidth'),(width,route,page.evaluate('document.documentElement.scrollWidth'))
   assert page.locator('.startup-screen').is_hidden()
  page.goto(BASE+'#home');assert page.locator('.home-category-tile').count()==8
  assert page.locator('#home-user-menu>summary').is_visible()
  page.locator('#menu-button').click();page.wait_for_function('document.querySelector("#sidebar").getBoundingClientRect().x>=-.5')
  page.locator('#navigation [data-route="words"]').first.click();page.locator('.mvp-catalog-grid').wait_for()
  assert page.locator('#scrim').is_hidden()
  page.goto(BASE+'#words/C06');page.locator('.mvp-subcategory').first.click()
  page.locator('#practice-group-dialog').wait_for();assert page.locator('#practice-group-dialog .practice-group-all b').inner_text()=='72'
  page.locator('#practice-group-dialog .practice-group-choice').first.click();page.locator('.translation-blank').first.wait_for()
  assert page.locator('#practice-jump option').count()==13
  assert page.locator('.mobile-controls').is_visible()
  assert page.locator('#question-audio').is_visible()
  assert page.locator('.mobile-controls').evaluate('e=>{const r=e.getBoundingClientRect();return r.y>=0&&r.bottom<=innerHeight+1&&r.width<=innerWidth}')
  assert page.locator('.translation-slots').evaluate('e=>e.scrollWidth<=e.clientWidth+1')
  page.locator('.mobile-controls [data-action="translation-answer"]').click()
  assert page.locator('.translation-answer').is_visible()
  assert page.evaluate('!JSON.parse(localStorage.getItem(document.body.dataset.storageKey)).wordStatus["C06-S01-001"]')
  page.locator('.mobile-controls [data-action="translation-answer"]').click()
  page.locator('.translation-blank').first.fill('pet');page.locator('.mobile-controls [data-action="translation-submit"]').click()
  assert page.evaluate('JSON.parse(localStorage.getItem(document.body.dataset.storageKey)).wordStatus["C06-S01-001"]')=='mastered'
  page.locator('.mobile-controls [data-action="next-item"]').last.click()
  assert page.locator('.translation-picture').get_attribute('data-scene-id')=='C06-S01-002'
  page.locator('.practice-back').click();page.wait_for_function('!document.querySelector("#lesson-dialog").open')
  page.goto(BASE+'#home');page.reload()
  assert '第 2 / 13 词' in page.locator('.mvp-resume-title').inner_text()
  page.locator('.home-resume-card [data-action="resume-desktop"]').click()
  assert page.locator('.translation-picture').get_attribute('data-scene-id')=='C06-S01-002'
  # Emulate a reduced visual viewport, without replacing input nodes.
  field=page.locator('.translation-blank').first;field.fill('do')
  page.evaluate("document.documentElement.classList.add('phone-keyboard');document.documentElement.style.setProperty('--phone-height','420px')")
  assert page.locator('.translation-picture').is_hidden()
  assert page.locator('.mobile-controls').is_visible()
  assert field.input_value()=='do'
  page.locator('.mobile-controls [data-action="previous-item"]').click()
  assert page.locator('.translation-slots').is_visible()
  context.close();print('PASS: light pages, drawer, categories, selection, GA player, touch controls, answers, grading, cursor and keyboard at '+str(width)+'px',flush=True)
 assert not errors,errors
 # Actual v43 mobile storage retains records during the additive content update.
 context=browser.new_context(**p.devices['iPhone 13'],service_workers='block')
 context.add_init_script("{const pending=sessionStorage.getItem('mobile-v43-fixture');if(pending){const {k,s}=JSON.parse(pending);localStorage.setItem(k,JSON.stringify(s));sessionStorage.removeItem('mobile-v43-fixture');}}")
 page=context.new_page();page.route(BASE+'?previous-mobile',lambda r:r.fulfill(body=old_html,content_type='text/html; charset=utf-8'),times=1)
 page.goto(BASE+'?previous-mobile#home')
 fixture=page.evaluate('''()=>{const k=document.body.dataset.storageKey,s=JSON.parse(localStorage.getItem(k));s.settings.userName='手机原学习者';s.settings.grade='四年级';s.settings.rate=.9;
 s.wordStatus={'C01-S01-001':'mastered','C06-S01-001':'unfamiliar'};s.favorites=['C01-S01-001'];s.words[0].notes='原手机笔记';s.notes=[{id:'mobile-note',title:'手机笔记',body:'保留内容',createdAt:'2026-10-01T00:00:00Z',updatedAt:'2026-10-01T00:00:00Z'}];s.days['2020-01-01']={seconds:456,words:['C01-S01-001'],sentences:[],checked:true,mistakes:1};
 const ids=s.words.filter(w=>w.subcategoryId==='C06-S01').map(w=>w.id);s.practiceResume={ids,wordId:ids[3],answered:false,finished:false};sessionStorage.setItem('mobile-v43-fixture',JSON.stringify({k,s}));return s;}''')
 page.goto(BASE+'#home');page.locator('.home-hero').wait_for()
 current=page.evaluate('JSON.parse(localStorage.getItem(document.body.dataset.storageKey))')
 for key in ['wordStatus','settings','favorites','notes','plan','practiceResume']:assert current[key]==fixture[key],key
 assert [w for w in current['words'] if w['categoryId']!='C07']==fixture['words']
 assert current['contentPacks']==fixture['contentPacks']+['travel-social-v1']
 assert current['days']['2020-01-01']==fixture['days']['2020-01-01']
 assert '手机原学习者' in page.locator('#home-user-menu>summary').inner_text()
 page.locator('#home-user-menu>summary').click()
 with page.expect_download() as download:page.locator('#home-user-menu [data-action="backup"]').click()
 backup=json.loads(Path(download.value.path()).read_text())
 assert backup['settings']['userName']=='手机原学习者' and backup['wordStatus']==fixture['wordStatus']
 context.close()
 browser.close()
print('COMPLETE: responsive mobile light template and existing learner records passed',flush=True)
