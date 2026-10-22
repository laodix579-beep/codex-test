"""Mobile practice regression checks. Requires Playwright and Chromium.

Run with a local static server on port 8000: python3 tests/mobile_practice.py
"""
from pathlib import Path
import json
import re
from playwright.sync_api import sync_playwright

BASE = 'http://127.0.0.1:8000/'
RESULTS = []


def passed(name):
    RESULTS.append(name)
    print('PASS', name, flush=True)


def open_practice(page):
    page.goto(BASE + '#textbooks')
    page.get_by_role('button', name='进入 27 小课').click()
    page.locator('[data-action="book-lesson"]').first.click()
    page.locator('[data-action="start-selected-mode"]').click()
    page.locator('.translation-blank').first.wait_for()
    page.wait_for_function("document.querySelector('.translation-picture img')?.complete")


def sound_count(page):
    return page.evaluate('window.keyAudioStarts.length')


def reset_sounds(page):
    page.locator('.translation-blank').first.fill('')
    page.evaluate('window.keyAudioStarts=[]')


def soft_edit(page, value, input_type='insertText', data=None, composing=False, before=True):
    page.locator('.translation-blank').first.evaluate('''(el,edit)=>{
      const options={bubbles:true,cancelable:true,inputType:edit.inputType,data:edit.data,isComposing:edit.composing};
      el.dispatchEvent(new KeyboardEvent('keydown',{key:'Unidentified',keyCode:229,isComposing:edit.composing,bubbles:true}));
      if(edit.before)el.dispatchEvent(new InputEvent('beforeinput',options));
      el.value=edit.value;
      el.dispatchEvent(new InputEvent('input',options));
      el.dispatchEvent(new KeyboardEvent('keyup',{key:'Unidentified',bubbles:true}));
    }''', {'value':value,'inputType':input_type,'data':data,'composing':composing,'before':before})


with sync_playwright() as p:
    browser = p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox'])
    context = browser.new_context(viewport={'width':390,'height':844},is_mobile=True,has_touch=True,user_agent=p.devices['iPhone 13']['user_agent'])
    # Observe real non-silent audio buffers reaching Web Audio, rather than a mock callback.
    context.add_init_script('''
      window.keyAudioStarts=[];
      const start=AudioBufferSourceNode.prototype.start;
      AudioBufferSourceNode.prototype.start=function(...args){
        const samples=this.buffer?.getChannelData(0);
        const energy=samples?samples.reduce((sum,n)=>sum+n*n,0):0;
        window.keyAudioStarts.push({energy,state:this.context.state});
        return start.apply(this,args);
      };
    ''')
    page=context.new_page()
    errors=[]
    page.on('pageerror',lambda error:errors.append(str(error)))
    open_practice(page)
    for width,height in ((320,740),(390,844),(412,915),(667,375)):
        page.set_viewport_size({'width':width,'height':height})
        page.wait_for_timeout(80)
        metrics=page.locator('#lesson-dialog').evaluate('''e=>{
          const r=s=>document.querySelector(s).getBoundingClientRect();
          return {width:e.clientWidth,scroll:e.scrollWidth,height:e.clientHeight,scrollHeight:e.scrollHeight,
            header:r('.dialog-heading').height,footer:r('.translation-footer').toJSON(),
            buttons:[...document.querySelectorAll('.mobile-controls button')].map(e=>e.getBoundingClientRect().toJSON())};
        }''')
        assert metrics['scroll']<=width+1,metrics
        assert metrics['scrollHeight']<=metrics['height']+1,metrics
        assert metrics['header']<=66,metrics
        assert metrics['footer']['bottom']<=metrics['height']+1,metrics
        assert all(0<=r['left']<r['right']<=width for r in metrics['buttons']),metrics
    passed('Phone, small-screen and landscape layouts keep all seven actions inside the viewport')
    page.set_viewport_size({'width':390,'height':844})
    page.locator('.translation-blank').first.fill('hi')
    page.screenshot(path='/tmp/mobile-practice-reference.png')
    assert page.locator('.translation-picture img').evaluate('(e)=>e.naturalWidth')>1000
    assert page.locator('#practice-clock').inner_text().count(':')==2
    passed('Reference-style photo, full session clock and fixed toolbar render')

    reset_sounds(page)
    page.locator('.translation-blank').first.press_sequentially('hi')
    page.locator('.translation-blank').first.press('Backspace')
    assert sound_count(page)==3, page.evaluate('keyAudioStarts')
    assert page.evaluate("keyAudioStarts.every(s=>s.energy>0&&s.state==='running')")
    passed('Real keyboard events play one audible key buffer per character and delete, without duplicates')

    reset_sounds(page)
    for text in ('h','hi','hig'):
        soft_edit(page,text,'insertText',None)
    assert sound_count(page)==3
    soft_edit(page,'hi','deleteContentBackward',None)
    assert sound_count(page)==4
    passed('Android unidentified keys and null-data insert/delete events each play once')

    reset_sounds(page)
    for text in ('h','he','hel'):
        soft_edit(page,text,'insertCompositionText',text,True)
    assert sound_count(page)==3
    # IME commit can repeat the same value without a new user keystroke.
    soft_edit(page,'hel','insertText',None,False,False)
    assert sound_count(page)==3
    passed('Composition updates sound on each edit; the final unchanged IME commit does not double-play')

    reset_sounds(page)
    soft_edit(page,'h','insertText',None,False,False)
    soft_edit(page,'hi','insertText',None,False,False)
    assert sound_count(page)==2
    soft_edit(page,'hello','insertReplacementText','hello')
    assert sound_count(page)==3
    passed('Input-only fallback and predictive text replacements keep typing sounds')

    menu=page.locator('#practice-mobile-menu')
    menu.locator('summary').click()
    menu.locator('[data-practice-setting="keySounds"]').uncheck()
    reset_sounds(page)
    soft_edit(page,'hi')
    assert sound_count(page)==0
    menu.locator('[data-practice-setting="keySounds"]').check()
    menu.locator('[data-practice-setting="volume"]').press('Home')
    reset_sounds(page)
    soft_edit(page,'hi')
    assert sound_count(page)==0
    for _ in range(5):
        menu.locator('[data-practice-setting="volume"]').press('ArrowRight')
    menu.locator('summary').click()
    passed('Sound switch and volume respect mute preferences')

    page.locator('.mobile-controls [data-action="translation-answer"]').click()
    assert page.locator('.translation-answer').is_visible()
    expected=page.locator('.translation-answer strong').inner_text()
    assert page.locator('.mobile-controls [data-action="translation-answer"]').get_attribute('aria-pressed')=='true'
    page.locator('.translation-blank').first.fill('h')
    assert page.locator('.translation-answer').count()==0
    assert page.locator('.mobile-controls [data-action="translation-answer"]').get_attribute('aria-pressed')=='false'
    words=re.findall(r"[A-Za-z]+(?:['’-][A-Za-z]+)*",expected)
    for field in page.locator('.translation-blank').all():
        field.fill(words[int(field.get_attribute('data-token-index'))])
    page.locator('.mobile-controls [data-action="translation-submit"]').click()
    assert '回答正确' in page.locator('#lesson-content').inner_text()
    page.locator('.mobile-controls .nav-arrow[data-action="next-item"]').click()
    assert page.locator('.translation-blank').count()>0
    passed('Touch answers, automatic answer hiding, grading and next question still work')

    # Software keyboard Next should validate this blank and move focus to the next one.
    page.locator('.mobile-controls [data-action="translation-answer"]').click()
    expected=page.locator('.translation-answer strong').inner_text()
    words=re.findall(r"[A-Za-z]+(?:['’-][A-Za-z]+)*",expected)
    fields=page.locator('.translation-blank')
    first_index=fields.first.get_attribute('data-token-index')
    fields.first.fill(words[int(first_index)])
    fields.first.press('Enter')
    if page.locator('.translation-blank').count()>1:
        assert page.evaluate('document.activeElement.dataset.tokenIndex')!=first_index
    passed('Phone keyboard Enter advances through blanks')

    # Simulate a shrunken visual viewport: toolbar remains visible above the keyboard.
    page.locator('.translation-blank').first.focus()
    page.evaluate("Object.defineProperty(visualViewport,'height',{value:420,configurable:true});visualViewport.dispatchEvent(new Event('resize'))")
    assert page.evaluate("document.documentElement.classList.contains('phone-keyboard')")
    assert page.locator('.translation-picture').is_hidden()
    assert page.locator('.translation-footer').evaluate('(e)=>e.getBoundingClientRect().bottom')<=421
    page.screenshot(path='/tmp/mobile-practice-keyboard.png')
    page.evaluate("delete visualViewport.height;visualViewport.dispatchEvent(new Event('resize'))")
    assert not page.evaluate("document.documentElement.classList.contains('phone-keyboard')")
    passed('Keyboard viewport keeps answer controls visible and reduces the picture')

    page.locator('.practice-back').click()
    page.goto(BASE+'#settings')
    page.wait_for_function("document.querySelector('[data-mobile-status]')?.textContent.startsWith('已保存离线内容')")
    context.set_offline(True)
    open_practice(page)
    assert page.locator('.translation-picture img').evaluate('(e)=>e.complete&&e.naturalWidth>0')
    reset_sounds(page)
    soft_edit(page,'hi')
    assert sound_count(page)==1
    page.locator('.mobile-controls [data-action="speak-lesson"]').click()
    page.wait_for_function("document.getElementById('question-audio').currentTime>0",timeout=10000)
    passed('Offline reload retains the new illustration, typing sounds and embedded speech')
    assert not errors,errors
    passed('No JavaScript page errors')
    context.close()

    desktop=browser.new_context(viewport={'width':1440,'height':900})
    dp=desktop.new_page()
    open_practice(dp)
    assert dp.locator('.mobile-controls').is_hidden()
    assert dp.locator('.translation-shortcuts').is_visible()
    assert dp.locator('.practice-back .close-glyph').is_visible()
    assert dp.locator('#practice-mobile-menu').is_hidden()
    passed('Desktop shortcut layout remains available')
    browser.close()

Path('/tmp/mobile-practice-results.json').write_text(json.dumps({'passed':RESULTS,'browser':'Chromium phone profiles and desktop; synthetic soft-keyboard edit sequences'},ensure_ascii=False,indent=2))
print(f'COMPLETE: {len(RESULTS)} checks passed',flush=True)
