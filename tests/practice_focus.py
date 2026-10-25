"""Desktop background/replay clicks retain the live blank and caret, not fake focus."""
from playwright.sync_api import sync_playwright

BASE='http://127.0.0.1:8000/'
with sync_playwright() as p:
 browser=p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox'])
 context=browser.new_context(viewport={'width':1900,'height':1050})
 context.add_init_script('''
  Object.defineProperty(window,'speechSynthesis',{get(){throw new Error('TTS forbidden')}});
  window.keyHits=[];const original=AudioBufferSourceNode.prototype.start;
  AudioBufferSourceNode.prototype.start=function(...args){keyHits.push(1);return original.apply(this,args);};
 ''')
 page=context.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
 page.goto(BASE+'#words/C01/C01-S01');page.locator('.translation-blank').first.wait_for()
 page.locator('.translation-shortcuts [data-action="next-item"]').click()
 page.locator('.translation-shortcuts [data-action="next-item"]').click()
 assert '3/22' in page.locator('#lesson-course').inner_text()
 fields=page.locator('.translation-blank');assert fields.count()==2
 fields.first.fill('good');fields.nth(1).fill('mornxng')
 fields.nth(1).evaluate('e=>e.setSelectionRange(4,5)')
 def intact():
  assert fields.first.input_value()=='good' and fields.nth(1).input_value()=='mornxng'
  page.wait_for_function('''()=>{const f=document.querySelectorAll('.translation-blank')[1];return document.activeElement===f&&f.selectionStart===4&&f.selectionEnd===5}''')
  assert '3/22' in page.locator('#lesson-course').inner_text()
  assert page.evaluate('JSON.parse(localStorage.getItem(document.body.dataset.storageKey)).wordStatus')=={}
 # Non-interactive content across the full practice window restores the same blank.
 for target in ['.translation-picture img','.translation-chinese','.word-context-meaning','.given-word','.mvp-practice-info h2','.mvp-session-label','.mvp-stat.time','.mvp-practice-nav .privacy-note','.mvp-question-heading','#practice-speech-status']:
  page.locator(target).click();intact()
 page.mouse.click(1890,1000);intact()
 # The next real key replaces the old selection, and edits sound exactly once.
 page.evaluate('keyHits=[]');page.keyboard.type('i')
 assert fields.nth(1).input_value()=='morning' and fields.first.input_value()=='good'
 assert page.evaluate('keyHits.length')==1
 page.keyboard.press('Backspace');assert fields.nth(1).input_value()=='mornng'
 assert page.evaluate('keyHits.length')==2
 fields.nth(1).fill('mornxng');fields.nth(1).evaluate('e=>e.setSelectionRange(4,5)')
 # Replay executes normally and returns the caret without grading or switching.
 page.locator('#translation-form [data-action="speak-lesson"]').click();intact()
 page.wait_for_function('document.querySelector("#question-audio").currentTime>0&&!document.querySelector("#question-audio").paused')
 page.locator('#question-audio').click(position={'x':20,'y':16});intact()
 assert page.locator('#question-audio').evaluate('a=>a.paused')
 page.locator('#question-audio').click(position={'x':20,'y':16});intact()
 page.wait_for_function('document.querySelector("#question-audio").currentTime>0&&!document.querySelector("#question-audio").paused')
 page.locator('.question-audio-player [data-action="speak-lesson"]').click();intact()
 # Native player controls remain keyboard-accessible through deliberate Tab use.
 fields.first.focus();page.keyboard.press('Shift+Tab');page.keyboard.press('Shift+Tab')
 assert page.locator('#question-audio').evaluate('e=>document.activeElement===e')
 fields.nth(1).focus();fields.nth(1).evaluate('e=>e.setSelectionRange(4,5)')
 print('PASS: image/text/blank area/sidebar/replay/native audio preserve the live second blank, selection and single edit sounds',flush=True)
 # Real controls and keyboard navigation keep their own focus and behavior.
 summary=page.locator('.mvp-session-settings>summary');summary.click()
 assert summary.evaluate('e=>document.activeElement===e')
 checkbox=page.locator('.mvp-session-settings [data-practice-setting="keySounds"]')
 checkbox.click();assert checkbox.evaluate('e=>document.activeElement===e')
 assert not page.evaluate('JSON.parse(localStorage.getItem(document.body.dataset.storageKey)).settings.keySounds')
 settings=page.locator('.mvp-practice-info>.practice-options');settings.locator('summary').click()
 rate=settings.locator('[data-practice-setting="rate"]');rate.select_option('0.9');rate.focus()
 page.keyboard.press('ArrowDown');assert rate.evaluate('e=>document.activeElement===e')
 volume=settings.locator('[data-practice-setting="volume"]');volume.click()
 assert volume.evaluate('e=>document.activeElement===e')
 page.locator('.translation-chinese').click();intact()
 # Settings that re-render the question still preserve its saved answer and caret.
 page.locator('.mvp-session-settings [data-session-setting="showPicture"]').uncheck()
 assert page.locator('.translation-picture').count()==0
 page.locator('.translation-chinese').click();intact()
 fields.first.click();assert fields.first.evaluate('e=>document.activeElement===e')
 page.keyboard.press('Tab');assert fields.nth(1).evaluate('e=>document.activeElement===e')
 fields.nth(1).evaluate('e=>e.setSelectionRange(4,5)')
 page.locator('#translation-form [data-action="translation-answer"]').click()
 assert page.locator('#practice-answer-dialog').evaluate('e=>e.open&&e.contains(document.activeElement)')
 page.locator('[data-answer-audio="word"]').click()
 assert page.locator('#practice-answer-dialog').evaluate('e=>e.open&&e.contains(document.activeElement)')
 page.locator('#practice-answer-title').click();intact()
 print('PASS: settings, checkbox, volume, rate, Tab, another blank and answer popup keep their intended focus behavior',flush=True)
 # Pause, submit and question navigation are not overridden by the focus keeper.
 page.locator('.mvp-practice-info>[data-action="pause-practice"]').click()
 assert page.locator('.translation-blank').count()==0
 page.locator('.mvp-practice-info h2').click()
 page.locator('.mvp-practice-info>[data-action="pause-practice"]').click()
 fields.nth(1).fill('morning');page.locator('#translation-submit').click()
 assert page.locator('.mvp-correct-feedback h3').inner_text()=='回答正确！'
 assert page.locator('.translation-blank').count()==0
 page.locator('.mvp-practice-info h2').click();page.keyboard.press('Space')
 page.locator('.translation-blank').first.wait_for()
 assert '4/22' in page.locator('#lesson-course').inner_text()
 assert page.locator('.translation-blank').first.evaluate('e=>document.activeElement===e')
 page.locator('.translation-chinese').click()
 assert page.locator('.translation-blank').first.evaluate('e=>document.activeElement===e')
 page.locator('.mvp-practice-info>details').last.locator('summary').click()
 page.locator('.mvp-practice-modes [data-mode="typing"]').click()
 assert page.locator('.translation-blank').count()==0
 assert page.locator('#lesson-answer').is_visible()
 page.locator('.practice-back').click();page.wait_for_function('!document.querySelector("#lesson-dialog").open')
 assert page.locator('.mvp-subcategory').count()==4
 assert not errors,errors
 print('PASS: pause/resume, correct grading, next question, other mode and exit work without stale focus',flush=True)
 context.close();browser.close()
print('COMPLETE: desktop practice focus retention passed',flush=True)
