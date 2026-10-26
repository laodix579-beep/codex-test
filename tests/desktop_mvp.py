"""Desktop MVP flow, modal isolation, existing MP3 playback and data preservation."""
import json
from pathlib import Path
from playwright.sync_api import sync_playwright

BASE='http://127.0.0.1:8000/'
results=[]
with sync_playwright() as p:
 browser=p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox'])
 context=browser.new_context(viewport={'width':1440,'height':960},accept_downloads=True)
 context.add_init_script("Object.defineProperty(window,'speechSynthesis',{get(){throw new Error('TTS forbidden')}});Object.defineProperty(window,'SpeechSynthesisUtterance',{get(){throw new Error('TTS forbidden')}})")
 page=context.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
 page.goto(BASE+'#home');page.locator('.mvp-resume').wait_for()
 saved=lambda:page.evaluate('JSON.parse(localStorage.getItem(document.body.dataset.storageKey))')
 assert len(saved()['words'])==356
 assert page.locator('.brand-frog').is_hidden()
 assert page.locator('.brand-book').is_visible()
 # Existing study data and settings are fixtures from the same schema, not replaced.
 page.evaluate('''()=>{const key=document.body.dataset.storageKey,s=JSON.parse(localStorage.getItem(key));
  s.courses=[{id:'existing-course',title:'历史课程',description:'保留资料',category:'daily',level:'A1',color:'purple',createdAt:'2026-10-01T00:00:00Z',sample:false,sentences:[{id:'existing-sentence',english:'Keep my history.',chinese:'保留历史。'}]}];
  s.sentenceStatus['existing-sentence']='mastered';s.wordStatus['C01-S03-001']='wrong';
  s.notes=[{id:'existing-note',title:'原有手账',body:'原有记录不丢失',createdAt:'2026-10-01T00:00:00Z',updatedAt:'2026-10-01T00:00:00Z'}];
  s.favorites=['existing-sentence','C01-S03-001'];s.courseFavorites=['existing-course'];s.plan={minutes:30,words:12,sentences:15,courseIds:['existing-course']};
  s.settings={...s.settings,rate:.9,userName:'原有用户',volume:.4};
  s.days['2026-10-01']={seconds:1500,sentences:['existing-sentence'],words:['C01-S03-001'],mistakes:1,checked:true};
  localStorage.setItem(key,JSON.stringify(s));}''')
 page.reload();baseline=saved()
 assert '原有用户' in page.locator('#home-user-menu>summary').inner_text()
 page.screenshot(path='/tmp/mvp-home-final.png')
 # All prior non-curriculum functions remain reachable in the existing navigation.
 page.locator('.nav-extras>summary').click()
 for route in ['chat','challenge','plan','notes','favorites','creator']:
  assert page.locator(f'#navigation [data-route="{route}"]').is_visible()
 page.locator('#navigation [data-route="words"]').click();page.locator('.mvp-category-card').first.wait_for()
 assert page.locator('.mvp-category-card').count()==8
 assert page.locator('.mvp-category-card h3').all_text_contents()==page.evaluate('FROG_WORD_CATALOG.categories.map(c=>c.name)')
 assert len(saved()['words'])==356
 page.screenshot(path='/tmp/mvp-categories-final.png')
 page.locator('.mvp-category-card[data-category-id="C03"]').click();page.locator('.mvp-subcategory').first.wait_for()
 assert page.locator('.mvp-subcategory').count()==4
 assert '暂无词条' in page.locator('.mvp-subcategory').first.inner_text()
 page.locator('.mvp-subcategory').first.click();page.get_by_role('heading',name='这个分类正在准备中').wait_for()
 assert page.locator('#lesson-dialog').evaluate('e=>!e.open')
 page.goto(BASE+'#words');page.locator('.mvp-category-card[data-category-id="C01"]').click()
 page.locator('.mvp-subcategory').first.wait_for();assert page.locator('.mvp-subcategory').count()==4
 assert [int(s.split('/')[1].split()[0]) for s in page.locator('.mvp-subcategory>small').all_text_contents()]==[22,62,19,33]
 page.screenshot(path='/tmp/mvp-subcategories-final.png')
 page.locator('.mvp-subcategory[data-subcategory-id="C01-S01"]').click()
 page.locator('#practice-group-dialog [data-practice-group="all"]').click();page.locator('.translation-blank').wait_for()
 assert page.url.endswith('#words/C01')
 assert page.locator('[data-session-completed]').inner_text()=='0 / 22'
 assert page.locator('[data-session-accuracy]').inner_text()=='—'
 assert page.locator('.mvp-practice-info').is_visible()
 page.screenshot(path='/tmp/mvp-practice-final.png')
 field=page.locator('.translation-blank');field.fill('he')
 field.evaluate('e=>e.setSelectionRange(1,2)')
 def show():
  page.locator('#translation-form [data-action="translation-answer"]').click()
  page.locator('#practice-answer-dialog').wait_for(state='visible')
 def intact():
  assert page.locator('#practice-answer-dialog').evaluate('e=>!e.open')
  assert page.locator('.translation-blank').input_value()=='he'
  assert page.locator('.translation-blank').evaluate('e=>document.activeElement===e&&e.selectionStart===1&&e.selectionEnd===2')
  assert 'C01-S01-001' not in saved()['wordStatus']
  assert page.locator('[data-session-completed]').inner_text()=='0 / 22'
  assert '1/22' in page.locator('#lesson-course').inner_text()
 show();box=page.locator('#practice-answer-dialog').bounding_box()
 assert abs(box['x']+box['width']/2-720)<2 and abs(box['y']+box['height']/2-480)<2
 assert page.locator('#practice-answer-dialog').evaluate('e=>e.matches(":modal")')
 assert page.locator('#practice-answer-dialog button:not([data-answer-audio])').count()==1
 assert page.locator('#practice-answer-dialog button:not([data-answer-audio])').inner_text()=='关闭'
 assert page.locator('#practice-answer-dialog strong').inner_text()=='Hello, Anna'
 page.screenshot(path='/tmp/mvp-answer-final.png')
 for target,source in [('example','Hello, Anna.'),('word','hello')]:
  page.locator(f'[data-answer-audio="{target}"]').click()
  page.wait_for_function('(source)=>{const a=document.querySelector("#question-audio");return a.dataset.sourceText===source&&a.currentTime>0}',arg=source)
  assert page.locator('#practice-answer-dialog').evaluate('e=>e.open')
  assert 'C01-S01-001' not in saved()['wordStatus']
 page.locator('[data-answer-close]').click();intact()
 for key in ['a','Space','Enter','ArrowDown','Shift+ArrowRight','Control+a','Escape','Tab','F5']:
  show();page.keyboard.press(key);intact();print('PASS: modal consumes',key,flush=True)
 show();page.keyboard.down('a');page.keyboard.down('a');page.keyboard.down('a');page.keyboard.up('a');intact()
 for target in ['#practice-answer-title','.mvp-answer-note','.mvp-answer-illustration']:
  show();page.locator(target).click();intact()
 show();page.mouse.click(12,12);intact()
 # Changing the desktop breakpoint must keep the same live group and inputs.
 show();page.set_viewport_size({'width':980,'height':800});page.wait_for_function('!document.body.classList.contains("desktop-mvp")')
 assert page.locator('#lesson-dialog').evaluate('e=>e.open')
 assert page.locator('.translation-blank').input_value()=='he'
 assert '1/22' in page.locator('#lesson-course').inner_text()
 page.set_viewport_size({'width':1440,'height':960});page.wait_for_function('document.body.classList.contains("desktop-mvp")');intact()
 # Answer viewing is separate from submission; a wrong answer cannot become correct.
 field.fill('wrong');page.locator('#translation-submit').click()
 assert saved()['wordStatus']['C01-S01-001']=='wrong'
 assert page.locator('[data-session-completed]').inner_text()=='0 / 22'
 show();page.keyboard.press('Enter')
 assert saved()['wordStatus']['C01-S01-001']=='wrong'
 assert page.locator('.translation-blank').input_value()=='wrong'
 page.locator('.translation-blank').fill('hello');page.locator('#translation-submit').click()
 assert saved()['wordStatus']['C01-S01-001']=='mastered'
 assert page.locator('.mvp-correct-feedback h3').inner_text()=='回答正确！'
 assert page.locator('[data-session-completed]').inner_text()=='1 / 22'
 assert page.locator('[data-session-remaining]').inner_text()=='21 题'
 assert page.locator('[data-session-accuracy]').inner_text()=='50%'
 assert page.locator('.mvp-complete-sentence').inner_text()=='Hello, Anna.'
 page.screenshot(path='/tmp/mvp-correct-final.png')
 page.locator('.mvp-solved-actions [data-action="next-item"]').click();page.locator('.translation-blank').wait_for()
 assert '2/22' in page.locator('#lesson-course').inner_text()
 assert page.locator('.translation-blank').input_value()==''
 # All alternative practice modes remain usable on the same word group.
 page.locator('.mvp-practice-info>details').last.locator('summary').click()
 page.locator('.mvp-practice-modes [data-mode="typing"]').click();page.locator('#lesson-answer').wait_for()
 assert page.locator('#lesson-dialog>.mvp-practice-nav').count()==0
 page.locator('.lesson-mode [data-mode="listen"]').click();assert page.locator('#listen-repeat').is_visible()
 page.locator('.lesson-mode [data-mode="flash"]').click();assert page.locator('[data-action="reveal"]').is_visible()
 page.locator('.lesson-mode [data-mode="dictation"]').click();assert page.locator('#lesson-answer').is_visible()
 page.locator('.lesson-mode [data-mode="oral"]').click();assert page.locator('[data-action="record-voice"]').is_visible()
 page.locator('.lesson-mode [data-mode="translate"]').click();assert page.locator('.mvp-practice-info').is_visible()
 page.locator('.practice-back').click();page.wait_for_function('!document.querySelector("#lesson-dialog").open')
 assert page.locator('.mvp-subcategory').count()==4
 page.goto(BASE+'#home');page.locator('[data-action="resume-desktop"]').click();page.locator('.translation-blank').wait_for()
 assert '2/22' in page.locator('#lesson-course').inner_text()
 page.locator('.practice-back').click();page.goto(BASE+'#settings')
 for key in ['courses','sentenceStatus','notes','favorites','courseFavorites','plan','settings','words','challenges']:
  assert saved()[key]==baseline[key],key
 assert saved()['days']['2026-10-01']==baseline['days']['2026-10-01']
 with page.expect_download() as dl:page.locator('#content [data-action="backup"]').click()
 file=Path('/tmp/mvp-learning-backup.json');dl.value.save_as(file);backup=json.loads(file.read_text())
 assert backup['courses']==baseline['courses'] and backup['notes']==baseline['notes']
 assert backup['practiceResume']['wordId']=='C01-S01-002'
 assert backup['wordStatus']['C01-S01-001']=='mastered'
 assert not errors,errors
 print('PASS: complete desktop flow, centered modal, every dismissal path, MP3-only speakers, correct grading, modes, resume and all prior data/settings/backup',flush=True)
 results.append({'profile':'desktop-1440x960','eightCategories':True,'fourSubcategories':True,'modalCentered':True,'singleCloseButton':True,'anyKeyConsumed':True,'backdropAndContentClicksConsumed':True,'speakerKeepsModalOpen':True,'originalMp3sPlay':True,'inputAndSelectionPreserved':True,'viewingNeverGrades':True,'correctFeedbackThenNext':True,'oldModesAndSettingsPreserved':True,'historyAndBackupPreserved':True,'resumeAfterExit':True})
 context.close()
 for width,height in [(1024,768),(1280,800),(1366,768),(1920,1080)]:
  c=browser.new_context(viewport={'width':width,'height':height});page=c.new_page();page.goto(BASE+'#home')
  assert page.locator('.mvp-resume').is_visible()
  page.goto(BASE+'#words');assert page.locator('.mvp-category-card').count()==8
  page.goto(BASE+'#words/C01/C01-S01');page.locator('.translation-blank').wait_for()
  page.locator('#translation-form [data-action="translation-answer"]').click()
  box=page.locator('#practice-answer-dialog').bounding_box()
  assert abs(box['x']+box['width']/2-width/2)<2 and abs(box['y']+box['height']/2-height/2)<2
  assert box['y']>=20 and box['y']+box['height']<=height-20
  page.locator('[data-answer-close]').click();page.locator('.translation-blank').fill('hello');page.locator('#translation-submit').click()
  assert page.locator('.mvp-solved-actions [data-action="next-item"]').is_visible()
  assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
  assert page.locator('#lesson-dialog').evaluate('e=>e.scrollWidth<=e.clientWidth')
  page.screenshot(path=f'/tmp/mvp-desktop-{width}.png')
  results.append({'profile':f'desktop-{width}x{height}','homeAndEightCategories':True,'modalCenteredAndFits':True,'practiceAndFeedbackNoHorizontalOverflow':True})
  print('PASS: desktop layout',width,height,flush=True);c.close()
 browser.close()
Path('reports/desktop-mvp-results.json').write_text(json.dumps(results,ensure_ascii=False,indent=2)+'\n')
