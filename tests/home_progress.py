"""Home card hierarchy and real saved progress, resume, review and word links."""
import json
from pathlib import Path
from playwright.sync_api import sync_playwright,expect

BASE='http://127.0.0.1:8000/'
with sync_playwright() as p:
 browser=p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox'])
 context=browser.new_context(viewport={'width':1900,'height':1000},accept_downloads=True)
 context.add_init_script("Object.defineProperty(window,'speechSynthesis',{get(){throw new Error('TTS forbidden')}})")
 page=context.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
 saved=lambda:page.evaluate('JSON.parse(localStorage.getItem(document.body.dataset.storageKey))')
 def close_practice():
  page.locator('.practice-back').click();page.wait_for_function('!document.querySelector("#lesson-dialog").open')
  page.locator('.mvp-resume').wait_for()
 page.goto(BASE+'#home');page.locator('.mvp-resume').wait_for()
 assert page.locator('.mvp-resume-name').inner_text()=='问候与礼貌用语 · 单词中译英'
 assert page.locator('.mvp-resume-title').inner_text()=='上次学习进度'
 assert '上次学习到哪里' not in page.locator('.mvp-resume').inner_text()
 assert page.locator('.mvp-resume h2').bounding_box()['y']<page.locator('.mvp-resume-title').bounding_box()['y']
 assert page.locator('.mvp-resume-name').evaluate('e=>parseFloat(getComputedStyle(e).fontSize)')>page.locator('.mvp-resume-title').evaluate('e=>parseFloat(getComputedStyle(e).fontSize)')
 assert page.get_by_role('progressbar',name='上次学习进度').get_attribute('aria-valuenow')=='0'
 expect(page.locator('.mvp-resume-progress-count')).to_have_text('已掌握 0 / 22 个词条')
 assert page.locator('.mvp-preview .done').count()==0
 assert page.locator('[data-action="resume-desktop"]').inner_text().strip()=='开始学习'
 # Clicking a usage label opens that word inside its original 22-word group.
 page.get_by_role('button',name='练习 good morning 的用法',exact=True).click()
 page.locator('.translation-blank').first.wait_for()
 assert '3/22' in page.locator('#lesson-course').inner_text()
 assert len(saved()['practiceResume']['ids'])==22
 assert saved()['wordStatus']=={}
 for field,answer in zip(page.locator('.translation-blank').all(),['good','morning']):field.fill(answer)
 page.locator('#translation-submit').click();close_practice()
 expect(page.locator('.mvp-resume-progress-count')).to_have_text('已掌握 1 / 22 个词条')
 assert page.locator('.mvp-preview .done').count()==1
 assert page.locator('.mvp-preview .done').inner_text()=='good morning 的用法'
 page.reload();expect(page.locator('.mvp-resume-progress-count')).to_have_text('已掌握 1 / 22 个词条')
 page.locator('[data-action="resume-desktop"]').click();page.locator('.translation-blank').first.wait_for()
 assert '4/22' in page.locator('#lesson-course').inner_text()
 close_practice()
 print('PASS: large category title, small progress label, live progress, clickable usage labels and resume after reload',flush=True)
 # A previously mastered cursor advances to the next word needing practice.
 page.evaluate('''()=>{const key=document.body.dataset.storageKey,s=JSON.parse(localStorage.getItem(key)),ids=FROG_WORD_CATALOG.words.filter(w=>w.subcategoryId==='C01-S01').map(w=>w.id);
  s.wordStatus[ids[0]]='mastered';s.wordStatus[ids[1]]='wrong';s.practiceResume={ids,wordId:ids[0]};
  s.notes=[{id:'keep-home-note',title:'保留记录',body:'原有内容',createdAt:'2026-10-01T00:00:00Z',updatedAt:'2026-10-01T00:00:00Z'}];s.settings.volume=.35;s.plan.words=15;
  localStorage.setItem(key,JSON.stringify(s));}''')
 page.reload();baseline=saved()
 expect(page.locator('.mvp-resume-progress-count')).to_have_text('已掌握 2 / 22 个词条')
 assert page.get_by_role('progressbar',name='上次学习进度').get_attribute('aria-valuenow')=='9'
 assert page.locator('.mvp-preview .wrong').inner_text()=='hi 的用法'
 page.locator('[data-action="resume-desktop"]').click();page.locator('.translation-blank').first.wait_for()
 assert '2/22' in page.locator('#lesson-course').inner_text();close_practice()
 # A finished group is explicitly offered as review; starting it keeps mastery.
 page.evaluate('''()=>{const key=document.body.dataset.storageKey,s=JSON.parse(localStorage.getItem(key));s.practiceResume.ids.forEach(id=>s.wordStatus[id]='mastered');localStorage.setItem(key,JSON.stringify(s));}''')
 page.reload()
 assert page.locator('[data-action="resume-desktop"]').inner_text().strip()=='复习本组'
 expect(page.locator('.mvp-resume-progress-count')).to_have_text('已掌握 22 / 22 个词条')
 assert page.get_by_role('progressbar',name='上次学习进度').get_attribute('aria-valuenow')=='100'
 page.screenshot(path='/tmp/home-progress-complete.png')
 page.locator('[data-action="resume-desktop"]').click();page.locator('.translation-blank').first.wait_for()
 assert '1/22' in page.locator('#lesson-course').inner_text()
 assert all(saved()['wordStatus'][id]=='mastered' for id in saved()['practiceResume']['ids'])
 close_practice();page.reload();expect(page.locator('.mvp-resume-progress-count')).to_have_text('已掌握 22 / 22 个词条')
 print('PASS: real partial/full counts, status icons, correct continuation and full-group review without resetting mastery',flush=True)
 # The heading, progress and links must follow the actual latest category.
 page.goto(BASE+'#words/C01/C01-S03');page.locator('.translation-blank').first.wait_for()
 page.locator('.practice-back').click();page.wait_for_function('!document.querySelector("#lesson-dialog").open')
 page.goto(BASE+'#home')
 assert page.locator('.mvp-resume-name').inner_text()=='颜色 · 单词中译英'
 expect(page.locator('.mvp-resume-progress-count')).to_have_text('已掌握 0 / 19 个词条')
 blue=page.evaluate('FROG_WORD_CATALOG.words.filter(w=>w.subcategoryId==="C01-S03")[1]')
 page.locator(f'.mvp-preview [data-id="{blue["id"]}"]').click();page.locator('.translation-blank').first.wait_for()
 assert '2/19' in page.locator('#lesson-course').inner_text()
 page.wait_for_function('(text)=>{const a=document.querySelector("#question-audio");return a.dataset.sourceText===text&&a.currentTime>0}',arg=blue['example'])
 page.locator('.practice-back').click();page.wait_for_function('!document.querySelector("#lesson-dialog").open')
 assert saved()['notes']==baseline['notes'] and saved()['settings']==baseline['settings'] and saved()['plan']==baseline['plan']
 page.goto(BASE+'#home')
 with page.expect_download() as dl:page.locator('.top-actions [data-action="backup"]').click()
 backup_path=Path('/tmp/home-progress-backup.json');dl.value.save_as(backup_path);backup=json.loads(backup_path.read_text())
 assert backup['practiceResume']['wordId']==blue['id'] and len(backup['practiceResume']['ids'])==19
 assert backup['notes']==baseline['notes'] and backup['settings']==baseline['settings'] and backup['plan']==baseline['plan']
 assert sum(backup['wordStatus'].get(w['id'])=='mastered' for w in backup['words'] if w['subcategoryId']=='C01-S01')==22
 for width in (1024,1280,1440,1900):
  page.set_viewport_size({'width':width,'height':960})
  assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
  assert page.locator('.mvp-resume-name').is_visible()
  assert page.locator('.mvp-resume-title').is_visible()
  page.screenshot(path=f'/tmp/home-progress-{width}.png')
 assert not errors,errors
 print('PASS: latest-category heading and links, original MP3, preserved records/settings/backup and four desktop sizes',flush=True)
 context.close();browser.close()
print('COMPLETE: home progress and usage functions passed',flush=True)
