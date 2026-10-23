"""Word-bank Chinese-to-English input, sound and progress regression checks.

Run against the development server: python3 tests/word_spelling.py
"""
from playwright.sync_api import sync_playwright

BASE='http://127.0.0.1:8000/'


def open_word(page,word_id):
    page.goto(BASE+'#words/all')
    page.locator(f'[data-action="learn-word"][data-id="{word_id}"]').click()
    page.locator('.translation-blank').first.wait_for()
    assert page.locator('.given-word').count()==0


def state(page):
    return page.evaluate('JSON.parse(localStorage.getItem(document.body.dataset.storageKey))')


def sounds(page):
    return page.evaluate('keySounds')


with sync_playwright() as p:
    browser=p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox'])
    context=browser.new_context(viewport={'width':1440,'height':900})
    context.add_init_script('''
      window.keySounds=[];
      const start=AudioBufferSourceNode.prototype.start;
      AudioBufferSourceNode.prototype.start=function(...args){
        const data=this.buffer?.getChannelData(0);
        keySounds.push(data?data.reduce((sum,n)=>sum+n*n,0):0);
        return start.apply(this,args);
      };
    ''')
    page=context.new_page();errors=[]
    page.on('pageerror',lambda e:errors.append(str(e)))
    open_word(page,'C01-S01-001')
    assert page.locator('#lesson-dialog').evaluate('e=>e.classList.contains("translation-practice")')
    assert '你好' in page.locator('.translation-chinese').inner_text()
    assert page.locator('.translation-blank').input_value()==''
    assert page.locator('.translation-answer').count()==0
    assert page.locator('.translation-picture').count()==1
    assert page.locator('[data-session-setting="showPicture"]').first.is_checked()
    field=page.locator('.translation-blank')
    page.evaluate('keySounds=[]')
    field.press_sequentially('hellx')
    assert field.input_value()=='hellx'
    assert len(sounds(page))==5 and all(n>0 for n in sounds(page))
    field.press('Backspace');field.press_sequentially('o')
    assert field.input_value()=='hello' and len(sounds(page))==7
    page.locator('#translation-submit').click()
    assert '回答正确' in page.locator('.translation-question').inner_text()
    saved=state(page)
    assert saved['wordStatus']['C01-S01-001']=='mastered'
    assert 'C01-S01-001' not in saved['sentenceStatus']
    assert 'Hello, Anna.' in page.locator('.word-practice-example').inner_text()
    print('PASS: word cards open Chinese-to-English; each typed/deleted letter sounds once and correct spelling saves word progress',flush=True)

    page.keyboard.press('Space')
    assert page.get_by_role('heading',name='本轮练习结束').is_visible()
    page.locator('[data-action="translation-again"]').click()
    field=page.locator('.translation-blank')
    field.press_sequentially('wrong')
    page.locator('#translation-submit').click()
    assert '还不正确' in page.locator('#translation-form .translation-message').inner_text()
    assert state(page)['wordStatus']['C01-S01-001']=='wrong'
    page.locator('#lesson-dialog .translation-shortcuts [data-action="next-item"]').click()
    page.locator('[data-action="translation-retry"]').click()
    page.locator('.translation-blank').press_sequentially('hello')
    page.locator('#translation-submit').click()
    assert state(page)['wordStatus']['C01-S01-001']=='mastered'
    assert 'C01-S01-001' not in state(page)['sentenceStatus']
    print('PASS: wrong spelling, restart and retry keep word status separate from sentence progress',flush=True)
    page.locator('#lesson-dialog [data-close]').click()

    open_word(page,'C01-S01-003')
    assert page.locator('.translation-blank').count()==2
    first=page.locator('.translation-blank').first
    first.press_sequentially('good');first.press('Space')
    assert page.locator('.translation-blank').first.get_attribute('class').find('accepted')>=0
    page.locator('.translation-blank').nth(1).press_sequentially('morning')
    page.locator('.translation-blank').nth(1).press('Space')
    assert state(page)['wordStatus']['C01-S01-003']=='mastered'
    page.locator('#lesson-dialog [data-close]').click()
    open_word(page,'C01-S01-020')
    assert page.locator('.translation-blank').count()==2
    assert page.locator('.translation-slots').inner_text().strip()=='.'
    page.locator('.translation-blank').first.press_sequentially("I'm")
    page.locator('.translation-blank').nth(1).press_sequentially('fine')
    page.locator('#translation-submit').click()
    assert state(page)['wordStatus']['C01-S01-020']=='mastered'
    print('PASS: phrases split into editable words; capitalized words and contractions require typing',flush=True)
    page.locator('#lesson-dialog [data-close]').click()

    page.goto(BASE+'#words/C01/C01-S03')
    page.locator('.translation-blank').first.wait_for()
    page.locator('#lesson-dialog .translation-shortcuts [data-action="translation-answer"]').click()
    answer=page.locator('.translation-answer strong').inner_text()
    colors=page.evaluate('FROG_WORD_CATALOG.words.filter(w=>w.subcategoryId==="C01-S03").map(w=>w.word)')
    assert answer in colors
    page.locator('.translation-blank').first.press_sequentially('x')
    assert page.locator('.translation-answer').count()==0
    page.locator('[data-practice-setting="keySounds"]').filter(visible=True).first.uncheck()
    page.evaluate('keySounds=[]')
    page.locator('.translation-blank').first.press_sequentially('a')
    assert sounds(page)==[]
    page.locator('[data-practice-setting="keySounds"]').filter(visible=True).first.check()
    print('PASS: category batch uses the spelling game; typing hides answers and the sound switch mutes typing',flush=True)
    page.locator('#lesson-dialog [data-close]').click()
    assert not errors,errors
    context.close()

    phone=browser.new_context(viewport={'width':390,'height':844},is_mobile=True,has_touch=True,user_agent=p.devices['Pixel 7']['user_agent'])
    phone.add_init_script('''window.keySounds=[];const start=AudioBufferSourceNode.prototype.start;AudioBufferSourceNode.prototype.start=function(...a){keySounds.push(1);return start.apply(this,a);};''')
    mobile=phone.new_page();open_word(mobile,'C01-S01-001')
    mobile.evaluate('keySounds=[]')
    for value in ['h','he','hel','hell','hello']:
        mobile.locator('.translation-blank').evaluate('''(el,value)=>{
          el.dispatchEvent(new KeyboardEvent('keydown',{key:'Unidentified',keyCode:229,bubbles:true}));
          el.dispatchEvent(new InputEvent('beforeinput',{bubbles:true,inputType:'insertText',data:null}));
          el.value=value;
          el.dispatchEvent(new InputEvent('input',{bubbles:true,inputType:'insertText',data:null}));
          el.dispatchEvent(new KeyboardEvent('keyup',{key:'Unidentified',bubbles:true}));
        }''',value)
    assert len(sounds(mobile))==5
    mobile.locator('.mobile-controls [data-action="translation-submit"]').click()
    assert state(mobile)['wordStatus']['C01-S01-001']=='mastered'
    assert mobile.evaluate('document.documentElement.scrollWidth<=innerWidth')
    assert mobile.locator('.translation-footer').evaluate('(e)=>e.getBoundingClientRect().bottom')<=845
    print('PASS: phone IME edits sound once per letter, touch submission grades correctly and controls stay visible',flush=True)
    phone.close();browser.close()

print('COMPLETE: 5 word spelling regression groups passed',flush=True)
