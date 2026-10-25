"""Reference answers omit trailing symbols without changing words or recordings."""
import json
from pathlib import Path
from playwright.sync_api import sync_playwright
BASE='http://127.0.0.1:8000/'
results=[]
with sync_playwright() as p:
 browser=p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox'])
 for mobile in (False,True):
  context=browser.new_context(viewport={'width':390 if mobile else 1440,'height':844 if mobile else 1000},is_mobile=mobile,has_touch=mobile,user_agent='Mozilla/5.0 (Linux; Android 11) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.198 Mobile Safari/537.36 MicroMessenger/8.0.32' if mobile else None)
  context.add_init_script("delete window.structuredClone;delete Object.hasOwn;delete Array.prototype.at;Object.defineProperty(window,'speechSynthesis',{get(){throw new Error('TTS forbidden')}})")
  page=context.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
  page.goto(BASE+'#words/all');rows=page.evaluate('FROG_WORD_CATALOG.words')
  cases=[('see you later','See you later'),('how are you?','How are you today'),("I'm fine.","I'm fine, thank you"),('red','The apple is red')]
  checked=[]
  for word,expected in cases:
   row=next(w for w in rows if w['word']==word)
   page.goto(BASE+'#words/all')
   page.locator(f'[data-action="learn-word"][data-id="{row["id"]}"]').click()
   page.locator('.translation-blank').first.wait_for()
   button='.mobile-controls [data-action="translation-answer"]' if mobile else '#translation-form [data-action="translation-answer"]'
   page.locator(button).click()
   assert page.locator('.translation-answer strong').inner_text()==expected
   assert page.locator('.translation-answer>span').inner_text()==row['ipa']
   page.locator('.mobile-controls [data-action="speak-lesson"]' if mobile else '#translation-form [data-action="speak-lesson"]').click()
   page.wait_for_function('(text)=>{const a=document.querySelector("#question-audio");return a.dataset.sourceText===text&&a.currentTime>0}',arg=row['example'])
   assert page.evaluate('(id)=>JSON.parse(localStorage.getItem(document.body.dataset.storageKey)).words.find(w=>w.id===id).example',row['id'])==row['example']
   answers=page.evaluate('''w=>{const c=FrogPractice.wordCloze(w);return FrogPractice.sentenceTokens(c.english).filter(t=>t.word&&c.blankIndices.includes(t.index)).map(t=>t.text)}''',row)
   for field,answer in zip(page.locator('.translation-blank').all(),answers):field.fill(answer)
   page.locator('.mobile-controls [data-action="translation-submit"]' if mobile else '#translation-submit').click()
   assert '回答正确' in page.locator('.translation-question').inner_text()
   assert page.locator('.word-practice-example p').all_text_contents()==[row['example'],row['exampleZh']]
   page.locator('.practice-back').click();page.wait_for_function('!document.querySelector("#lesson-dialog").open')
   checked.append({'word':word,'answer':expected,'sourceExample':row['example']})
  # Existing custom example punctuation also changes only in the hint display.
  page.evaluate('''()=>{const key=document.body.dataset.storageKey,s=JSON.parse(localStorage.getItem(key));s.words.find(w=>w.word==='see you later').example='See you later!?!…）】★';localStorage.setItem(key,JSON.stringify(s));}''')
  page.reload();page.locator('[data-action="learn-word"][data-id="C01-S01-010"]').click()
  page.locator('.translation-blank').first.wait_for()
  page.locator('.mobile-controls [data-action="translation-answer"]' if mobile else '#translation-form [data-action="translation-answer"]').click()
  assert page.locator('.translation-answer strong').inner_text()=='See you later'
  assert page.evaluate('JSON.parse(localStorage.getItem(document.body.dataset.storageKey)).words.find(w=>w.word==="see you later").example')=='See you later!?!…）】★'
  assert not errors,errors
  assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
  page.screenshot(path='/tmp/answer-punctuation-'+('phone' if mobile else 'desktop')+'.png')
  results.append({'profile':'phone' if mobile else 'desktop','cases':checked,'mixedTrailingSymbols':True,'internalApostropheAndCommaPreserved':True,'ipaUnchanged':True,'originalMp3LookupTextPreserved':True,'gradingWithLettersOnly':True})
  print('PASS',results[-1]['profile'],'clean answer endings, original MP3s, internal apostrophe/comma, DJ IPA and correct grading',flush=True)
  context.close()
 browser.close()
Path('reports/answer-punctuation-results.json').write_text(json.dumps(results,ensure_ascii=False,indent=2)+'\n')
print('COMPLETE: answer punctuation checks passed',flush=True)
