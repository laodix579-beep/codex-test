"""Screenshot home entries, real counters and dual-goal daily check-in."""
import json
from pathlib import Path
from playwright.sync_api import sync_playwright,expect

BASE='http://127.0.0.1:8000/'
with sync_playwright() as p:
 browser=p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox'])
 context=browser.new_context(viewport={'width':1824,'height':1000},accept_downloads=True)
 context.add_init_script("Object.defineProperty(window,'speechSynthesis',{get(){throw new Error('TTS forbidden')}})")
 page=context.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
 saved=lambda:page.evaluate('JSON.parse(localStorage.getItem(document.body.dataset.storageKey))')
 current_day=lambda:page.evaluate('''()=>{const d=new Date(),key=d.getFullYear()+'-'+String(d.getMonth()+1).padStart(2,'0')+'-'+String(d.getDate()).padStart(2,'0');return JSON.parse(localStorage.getItem(document.body.dataset.storageKey)).days[key];}''')
 def home():
  page.goto(BASE+'#home');page.locator('.home-dashboard').wait_for()
 def close_practice():
  page.locator('.practice-back').click();page.wait_for_function('!document.querySelector("#lesson-dialog").open')
 def menu():page.locator('#home-user-menu>summary').click()
 def day_fixture(seconds,count,checked=False):
  page.evaluate('''v=>{const key=document.body.dataset.storageKey,s=JSON.parse(localStorage.getItem(key)),d=new Date(),today=d.getFullYear()+'-'+String(d.getMonth()+1).padStart(2,'0')+'-'+String(d.getDate()).padStart(2,'0');s.days[today]={seconds:v.seconds,words:s.words.slice(0,v.count).map(w=>w.id),sentences:[],mistakes:0,checked:v.checked};localStorage.setItem(key,JSON.stringify(s));}''',{'seconds':seconds,'count':count,'checked':checked})
  page.reload();page.locator('.home-dashboard').wait_for()
 home();page.wait_for_function('document.querySelector(".home-hero-illustration img").naturalWidth>0')
 assert page.locator('.home-category-tile').count()==8
 assert [s.inner_text() for s in page.locator('.home-category-tile>small').all()]==['136 个单词','220 个单词']+['0 个单词']*6
 assert page.locator('[data-daily-time]').inner_text()=='0 / 20 分钟'
 assert page.locator('[data-daily-words]').inner_text()=='0 / 10 个'
 assert len(saved()['words'])==356
 # Every category opens its actual subcategories, including empty categories.
 for i in range(1,9):
  home();page.locator(f'.home-category-tile[data-category-id="C{i:02}"]').click()
  page.locator('.mvp-subcategory').first.wait_for();assert page.locator('.mvp-subcategory').count()==4
  assert page.url.endswith(f'#words/C{i:02}')
  if i==3:
   page.locator('.mvp-subcategory').first.click();page.get_by_role('heading',name='这个分类正在准备中').wait_for()
   assert page.locator('[data-action="add-word"]').first.is_enabled()
 home();page.locator('.home-section-heading [data-route="words"]').click();expect(page.locator('.mvp-category-card')).to_have_count(8)
 home();page.locator('#global-search').fill('早上好');page.locator('#global-search').press('Enter')
 page.wait_for_function('location.hash.startsWith("#search/")');page.locator('.search-results .word-card').first.wait_for()
 home();page.locator('.home-category-tile[data-category-id="C01"]').click();page.locator('.mvp-subcategory').first.wait_for()
 assert page.locator('.mvp-subcategory').count()==4
 print('PASS: all eight actual category entries, empty states, view-all and search-to-category navigation',flush=True)
 # Resume details are read-only; choosing a row preserves the full group.
 home();before=saved();page.locator('[data-action="resume-details"]').click()
 assert page.locator('.resume-detail-row').count()==22
 for key in ['wordStatus','notes','plan','settings']:assert saved()[key]==before[key]
 page.locator('#resume-details-dialog [data-action="resume-word"][data-id="C01-S01-003"]').click()
 page.locator('.translation-blank').first.wait_for();assert '3/22' in page.locator('#lesson-course').inner_text()
 assert page.locator('#resume-details-dialog').is_hidden()
 for f,v in zip(page.locator('.translation-blank').all(),['good','morning']):f.fill(v)
 page.locator('#translation-submit').click();close_practice()
 expect(page.locator('.mvp-resume-progress-count')).to_have_text('已掌握 1 / 22 个单词')
 page.locator('.home-resume-card [data-action="resume-desktop"]').click();page.locator('.translation-blank').first.wait_for()
 assert '4/22' in page.locator('#lesson-course').inner_text();close_practice()
 print('PASS: read-only resume details, word entry inside full group, real mastery and continuation',flush=True)
 # Profile and existing data actions are enabled in the user menu.
 menu();assert page.locator('#home-user-menu').evaluate('e=>e.open')
 page.keyboard.press('Escape');assert page.locator('#home-user-menu').evaluate('e=>!e.open')
 menu();page.locator('.home-hero h1').click();assert page.locator('#home-user-menu').evaluate('e=>!e.open')
 menu();page.locator('#home-user-menu [data-route="profile"]').click()
 page.locator('#profile-name').fill('首页学习者');page.locator('#profile-grade').fill('三年级');page.locator('#profile-form button[type="submit"]').click();home()
 assert '首页学习者' in page.locator('#home-user-menu>summary').inner_text()
 menu();page.locator('#home-user-menu [data-route="plan"]').click()
 page.locator('#plan-minutes').fill('20');page.locator('#plan-words').fill('50');page.locator('#plan-form button[type="submit"]').click();home()
 assert page.locator('[data-daily-words]').inner_text()=='1 / 50 个'
 menu()
 with page.expect_file_chooser() as chooser:page.locator('#home-user-menu [data-action="restore"]').click()
 chooser.value.set_files([])
 assert saved()['settings']['userName']=='首页学习者'
 menu()
 with page.expect_download() as dl:page.locator('#home-user-menu [data-action="backup"]').click()
 file=Path('/tmp/home-dashboard-backup.json');dl.value.save_as(file);backup=json.loads(file.read_text())
 assert backup['plan']['words']==50 and backup['wordStatus']['C01-S01-003']=='mastered'
 print('PASS: user menu, Escape/outside dismissal, profile, configurable goals, import picker and real backup',flush=True)
 # Existing historical check-ins must remain credited under the new rules.
 history=page.evaluate('''()=>{const key=document.body.dataset.storageKey,s=JSON.parse(localStorage.getItem(key)),d=new Date();d.setDate(d.getDate()-1);const old=d.getFullYear()+'-'+String(d.getMonth()+1).padStart(2,'0')+'-'+String(d.getDate()).padStart(2,'0');s.days[old]={seconds:1500,words:['C01-S01-001'],sentences:[],mistakes:0,checked:true};localStorage.setItem(key,JSON.stringify(s));return {key:old,day:s.days[old]};}''')
 # Both conditions must be enforced in the action, not just the button styling.
 day_fixture(9*60,24)
 assert page.locator('[data-daily-time]').inner_text()=='9 / 20 分钟'
 assert page.locator('[data-daily-words]').inner_text()=='24 / 50 个'
 assert '11 分钟' in page.locator('#home-checkin-hint').inner_text() and '26 个单词' in page.locator('#home-checkin-hint').inner_text()
 page.screenshot(path='/tmp/home-dashboard-progress.png')
 page.locator('.home-checkin-bottom [data-action="checkin"]').click()
 assert page.locator('#checkin-rules-dialog').evaluate('e=>e.open')
 assert not current_day()['checked']
 page.locator('#checkin-rules-dialog [data-route="plan"]').click();assert page.locator('#checkin-rules-dialog').is_hidden();home()
 day_fixture(1199,50);page.locator('.home-checkin-bottom [data-action="checkin"]').click()
 assert page.locator('#checkin-rules-dialog').is_visible()
 assert not current_day()['checked'];page.locator('#checkin-rules-dialog .dialog-back').click()
 day_fixture(1200,49);page.locator('.home-checkin-bottom [data-action="checkin"]').click()
 assert page.locator('#checkin-rules-dialog').is_visible()
 assert not current_day()['checked'];page.locator('#checkin-rules-dialog .dialog-back').click()
 day_fixture(1200,50);page.locator('.home-checkin-bottom [data-action="checkin"]').click()
 expect(page.locator('.home-checkin-bottom [data-action="checkin"]')).to_be_disabled()
 assert current_day()['checked']
 page.reload();expect(page.locator('.home-checkin-bottom [data-action="checkin"]')).to_be_disabled()
 menu();page.locator('#home-user-menu [data-route="plan"]').click();page.locator('#plan-minutes').fill('30');page.locator('#plan-form button[type="submit"]').click();home()
 assert page.locator('.home-checkin-bottom [data-action="checkin"]').is_disabled()
 assert current_day()['checked']
 page.locator('.mvp-old-dashboard>summary').click();assert page.locator('.calendar-day.today.checked').is_visible()
 page.locator('.mvp-old-dashboard>summary').click()
 menu();page.locator('#home-user-menu [data-route="records"]').click();expect(page.locator('.progress-records')).to_contain_text('已打卡');home()
 assert saved()['days'][history['key']]==history['day']
 print('PASS: dual-goal guard, real progress, missing-time/missing-word cases, persistent check-in, goal changes and calendar/history',flush=True)
 for width in (1024,1280,1440,1824,1920):
  page.set_viewport_size({'width':width,'height':1000})
  assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
  assert page.locator('.home-category-tile').count()==8
  page.screenshot(path=f'/tmp/home-dashboard-{width}.png')
 assert not errors,errors
 context.close();browser.close()
print('COMPLETE: screenshot home entry and check-in functions passed',flush=True)
