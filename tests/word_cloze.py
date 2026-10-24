"""Word examples supply context; only the target is editable; solved view stays intact."""
from playwright.sync_api import sync_playwright
BASE='http://127.0.0.1:8000/'

def open_word(page,word_id):
 page.goto(BASE+'#words/all')
 page.locator(f'[data-action="learn-word"][data-id="{word_id}"]').click()
 page.locator('.translation-blank').first.wait_for()

with sync_playwright() as p:
 browser=p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox'])
 page=browser.new_page(viewport={'width':1440,'height':1000});errors=[]
 page.on('pageerror',lambda e:errors.append(str(e)))
 page.goto(BASE+'#words')
 coverage=page.evaluate('''()=>FROG_WORD_CATALOG.words.map(w=>{
  const c=FrogPractice.wordCloze(w);return {word:w.word,valid:!!c&&c.english===w.example&&c.chinese===w.exampleZh&&c.blankIndices.length>0};})''')
 assert len(coverage)==136 and all(w['valid'] for w in coverage),[w for w in coverage if not w['valid']]
 assert page.evaluate("FrogPractice.wordCloze({word:'red',example:'One hundred.',exampleZh:'一百。'})") is None
 assert page.evaluate("FrogPractice.wordCloze({word:'custom',example:'A custom example.'})") is None
 print('PASS: all 136 built-in targets have bilingual example contexts; unmatched substrings and untranslated examples fall back safely',flush=True)
 open_word(page,'C01-S01-001')
 assert page.locator('.word-example-prompt').inner_text()=='你好，安娜。'
 assert page.locator('.word-context-meaning').inner_text()=='词义：你好；喂'
 assert page.locator('.given-word').all_text_contents()==['Anna']
 assert page.locator('.translation-blank').count()==1
 page.wait_for_function('document.querySelector("#question-audio").dataset.prompt==="hello anna"')
 assert page.locator('#question-audio').get_attribute('data-source-text')=='Hello, Anna.'
 assert page.locator('#question-audio').get_attribute('data-delivery')=='sentence'
 page.locator('#translation-form [data-action="speak-lesson"]').click()
 page.wait_for_function('document.querySelector("#question-audio").currentTime>0')
 assert page.locator('#question-audio').get_attribute('data-source-text')=='Hello, Anna.'
 assert page.locator('.word-context-meaning').evaluate('(el)=>!!el.previousElementSibling.matches(".word-example-prompt")')
 assert page.locator('.word-context-meaning').bounding_box()['y']+page.locator('.word-context-meaning').bounding_box()['height']<=page.locator('.translation-slots').bounding_box()['y']
 assert page.locator('.word-spelling-hint').count()==0
 assert 'Hello' not in page.locator('.translation-slots').inner_text()
 page.screenshot(path='/tmp/frog-word-cloze-desktop.png')
 page.locator('.translation-blank').fill('hello');page.locator('#translation-submit').click()
 assert page.locator('.grammar-card strong').inner_text()=='hello'
 assert page.locator('.translation-chinese').inner_text()=='你好；喂'
 assert page.locator('.word-practice-example p').all_text_contents()==['Hello, Anna.','你好，安娜。']
 assert page.locator('.word-practice-example [data-action="speak"]').get_attribute('data-text')=='Hello, Anna.'
 assert page.locator('.word-example-prompt').count()==0
 assert page.locator('.translation-blank').count()==0
 page.locator('#lesson-dialog [data-close]').click()
 print('PASS: hello renders Chinese sentence and blank + Anna; the existing solved word card, meaning and bilingual example remain unchanged',flush=True)
 words=page.evaluate('FROG_WORD_CATALOG.words')
 for word,expected in [('good morning',['Mom']),("I'm fine.",['thank','you']),('corner',['The','paper','has','four']),('side',['A','square','has','four'])]:
  row=next(w for w in words if w['word']==word);open_word(page,row['id'])
  assert page.locator('.word-example-prompt').inner_text()==row['exampleZh']
  assert page.locator('.given-word').all_text_contents()==expected
  answers=page.evaluate('''w=>{const c=FrogPractice.wordCloze(w);return FrogPractice.sentenceTokens(c.english).filter(t=>t.word&&c.blankIndices.includes(t.index)).map(t=>t.text);}''',row)
  for field,answer in zip(page.locator('.translation-blank').all(),answers):field.fill(answer)
  page.locator('#translation-submit').click()
  assert '回答正确' in page.locator('.translation-question').inner_text()
  assert page.locator('.word-practice-example p').all_text_contents()==[row['example'],row['exampleZh']]
  page.locator('#lesson-dialog [data-close]').click()
 assert not errors,errors
 print('PASS: phrases, contractions and plural target forms preserve sentence context and accept only their target blanks',flush=True)
 phone=browser.new_context(viewport={'width':390,'height':844},is_mobile=True,has_touch=True)
 mobile=phone.new_page();open_word(mobile,'C01-S01-001')
 assert mobile.locator('.word-example-prompt').inner_text()=='你好，安娜。'
 assert mobile.locator('.given-word').all_text_contents()==['Anna']
 assert mobile.locator('.translation-slots .sentence-punctuation').filter(has_text=',').is_visible()
 mobile.screenshot(path='/tmp/frog-word-cloze-phone.png')
 assert mobile.evaluate('document.documentElement.scrollWidth<=innerWidth')
 mobile.locator('.translation-blank').fill('hello');mobile.locator('.mobile-controls [data-action="translation-submit"]').click()
 assert mobile.locator('.word-practice-example p').all_text_contents()==['Hello, Anna.','你好，安娜。']
 print('PASS: phone cloze fits the viewport and keeps the existing solved bilingual block',flush=True)
 browser.close()
print('COMPLETE: word example cloze checks passed',flush=True)
