"""Regression checks for phone and desktop Space shortcuts.

Run against the development server: python3 tests/space_shortcuts.py
"""
from pathlib import Path
import re
from playwright.sync_api import sync_playwright

BASE='http://127.0.0.1:8000/'


def open_practice(page,mode='translate'):
    if page.locator('#lesson-dialog[open]').count():
        page.locator('#lesson-dialog .practice-back').click()
    page.goto(BASE+'#textbooks')
    page.get_by_role('button',name='进入 27 小课').click()
    page.locator('[data-action="book-lesson"]').first.click()
    page.locator(f'[data-start-mode="{mode}"]').click()
    page.locator('[data-action="start-selected-mode"]').click()


def phone_space(page,mode='cancelable',commit=None,space=' '):
    """Send actual IME edit sequences; honor cancellation of native insertion."""
    return page.evaluate('''edit=>{
      const el=document.activeElement,previous=el.value;
      const start=el.selectionStart,end=el.selectionEnd;
      const composition=edit.mode.startsWith('composition');
      const options={bubbles:true,cancelable:!['uncancelable','composition'].includes(edit.mode),
        inputType:composition?'insertCompositionText':'insertText',
        data:edit.mode==='null-data'?null:(edit.commit??edit.space),isComposing:composition};
      el.dispatchEvent(new KeyboardEvent('keydown',{key:'Unidentified',keyCode:229,isComposing:composition,bubbles:true}));
      const insert=edit.mode==='input-only'||el.dispatchEvent(new InputEvent('beforeinput',options));
      if(insert&&el.isConnected){
        el.value=edit.commit??(previous.slice(0,start)+edit.space+previous.slice(end));
        el.dispatchEvent(new InputEvent('input',options));
      }
      document.activeElement.dispatchEvent(new KeyboardEvent('keyup',{key:'Unidentified',bubbles:true}));
      return {prevented:!insert};
    }''',{'mode':mode,'commit':commit,'space':space})


def expect_one_sound(page):
    sounds=page.evaluate('keySounds')
    assert len(sounds)==1,sounds
    assert sounds[0]>0,sounds


with sync_playwright() as p:
    browser=p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox'])
    phone=browser.new_context(viewport={'width':390,'height':844},is_mobile=True,has_touch=True,user_agent=p.devices['Pixel 7']['user_agent'])
    phone.add_init_script('''
      window.keySounds=[];
      const start=AudioBufferSourceNode.prototype.start;
      AudioBufferSourceNode.prototype.start=function(...args){
        const samples=this.buffer?.getChannelData(0);
        window.keySounds.push(samples?samples.reduce((n,v)=>n+v*v,0):0);
        return start.apply(this,args);
      };
    ''')
    page=phone.new_page();errors=[]
    page.on('pageerror',lambda error:errors.append(str(error)))
    open_practice(page)
    page.locator('.mobile-controls [data-action="translation-answer"]').click()
    expected=re.findall(r"[A-Za-z]+(?:['’-][A-Za-z]+)*",page.locator('.translation-answer strong').inner_text())
    fields=page.locator('.translation-blank')
    first_index=fields.first.get_attribute('data-token-index')
    fields.first.evaluate('(el)=>el.dataset.keepNode="yes"')

    for mode in ('cancelable','uncancelable','input-only','null-data','composition'):
        fields.first.focus()
        page.evaluate('keySounds=[]')
        result=phone_space(page,mode)
        assert page.evaluate('document.activeElement.dataset.tokenIndex')!=first_index,mode
        assert fields.first.input_value()=='',mode
        assert fields.first.get_attribute('data-keep-node')=='yes',mode
        if mode=='cancelable':assert result['prevented']
        expect_one_sound(page)
    print('PASS: phone Space skips empty blanks through all five IME event paths, keeps input nodes and sounds once',flush=True)

    fields.first.focus();page.evaluate('keySounds=[]')
    phone_space(page,space='\u3000')
    assert page.evaluate('document.activeElement.dataset.tokenIndex')!=first_index
    expect_one_sound(page)
    print('PASS: full-width keyboard Space also skips blanks',flush=True)

    fields.first.fill(expected[int(first_index)])
    page.evaluate('keySounds=[]')
    phone_space(page)
    assert 'accepted' in fields.first.get_attribute('class')
    assert page.evaluate('document.activeElement.dataset.tokenIndex')!=first_index
    assert not fields.first.input_value().endswith(' ')
    expect_one_sound(page)
    next_index=page.evaluate('document.activeElement.dataset.tokenIndex')
    # Some IMEs deliver a late composition commit to the field that just lost focus.
    fields.first.evaluate('''(el,text)=>{
      el.dispatchEvent(new InputEvent('beforeinput',{bubbles:true,inputType:'insertCompositionText',data:text+' ',isComposing:true}));
      el.value=text+' ';
      el.dispatchEvent(new InputEvent('input',{bubbles:true,inputType:'insertCompositionText',data:text+' ',isComposing:true}));
    }''',expected[int(first_index)])
    assert 'accepted' in fields.first.get_attribute('class')
    assert fields.first.input_value()==expected[int(first_index)]
    assert page.evaluate('document.activeElement.dataset.tokenIndex')==next_index
    expect_one_sound(page)
    print('PASS: Space validates the current word and ignores late IME echoes after focus advances',flush=True)

    current=page.locator('.translation-blank:focus')
    wrong_index=current.get_attribute('data-token-index')
    current.fill('mistake');page.evaluate('keySounds=[]')
    phone_space(page,'input-only')
    assert page.evaluate('document.activeElement.dataset.tokenIndex')==wrong_index
    assert '不正确' in page.locator('#translation-form .translation-message').inner_text()
    assert current.input_value()=='mistake'
    expect_one_sound(page)
    print('PASS: incorrect words stay selected for correction instead of skipping',flush=True)

    current.fill('');page.evaluate('keySounds=[]')
    phone_space(page,'uncancelable')
    assert page.evaluate('document.activeElement.dataset.tokenIndex')!=wrong_index
    expect_one_sound(page)
    print('PASS: a second Space on an empty blank skips onward',flush=True)

    remaining=page.locator('.translation-blank:not(.accepted)').evaluate_all('(els)=>els.map(el=>el.dataset.tokenIndex)')
    for index in remaining:
        field=page.locator(f'.translation-blank[data-token-index="{index}"]')
        field.fill(expected[int(index)])
        page.evaluate('keySounds=[]')
        phone_space(page,'null-data')
        expect_one_sound(page)
    assert '回答正确' in page.locator('#lesson-content').inner_text()
    assert page.evaluate('document.activeElement.id')=='translation-next-input'
    page.evaluate('keySounds=[]')
    phone_space(page,'input-only')
    assert page.locator('.translation-blank').count()>0
    assert page.evaluate('document.activeElement.classList.contains("translation-blank")')
    assert page.locator('.translation-blank').first.input_value()==''
    expect_one_sound(page)
    print('PASS: after completing the sentence, phone Space advances exactly one question and refocuses the next blank',flush=True)

    page.locator('.mobile-controls [data-action="translation-answer"]').click()
    expected=re.findall(r"[A-Za-z]+(?:['’-][A-Za-z]+)*",page.locator('.translation-answer strong').inner_text())
    first=page.locator('.translation-blank').first
    word=expected[int(first.get_attribute('data-token-index'))]
    first.fill(word[:-1]);page.evaluate('keySounds=[]')
    phone_space(page,'composition',commit=word+' ')
    assert 'accepted' in first.get_attribute('class')
    assert first.input_value()==word
    assert page.evaluate('document.activeElement.dataset.tokenIndex')!=first.get_attribute('data-token-index')
    expect_one_sound(page)
    print('PASS: Space committing an entire composed word validates that word once',flush=True)

    # Real spaces between words remain text in typing mode.
    open_practice(page,'typing')
    page.locator('#lesson-answer').fill('Hello');page.evaluate('keySounds=[]')
    phone_space(page)
    assert page.locator('#lesson-answer').input_value()=='Hello '
    expect_one_sound(page)
    print('PASS: normal sentence spaces in typing mode remain unchanged',flush=True)
    assert not errors,errors
    phone.close()

    desktop=browser.new_context(viewport={'width':1440,'height':900})
    dp=desktop.new_page();open_practice(dp)
    dp.locator('#translation-form [data-action="translation-answer"]').click()
    expected=re.findall(r"[A-Za-z]+(?:['’-][A-Za-z]+)*",dp.locator('.translation-answer strong').inner_text())
    first=dp.locator('.translation-blank').first
    first.fill(expected[int(first.get_attribute('data-token-index'))])
    dp.keyboard.press('Space')
    assert 'accepted' in first.get_attribute('class')
    second_index=dp.evaluate('document.activeElement.dataset.tokenIndex')
    dp.keyboard.press('Space')
    assert dp.evaluate('document.activeElement.dataset.tokenIndex')!=second_index
    remaining=dp.locator('.translation-blank:not(.accepted)').evaluate_all('(els)=>els.map(el=>el.dataset.tokenIndex)')
    for index in remaining:
        field=dp.locator(f'.translation-blank[data-token-index="{index}"]')
        field.fill(expected[int(index)])
        dp.keyboard.press('Space')
    assert '回答正确' in dp.locator('#lesson-content').inner_text()
    assert dp.locator('.translation-next-input').is_hidden()
    dp.keyboard.press('Space')
    assert dp.locator('.translation-blank').count()>0
    print('PASS: desktop Space validation, skipping and next-question shortcuts stay intact',flush=True)
    browser.close()

print('COMPLETE: phone and desktop Space shortcuts passed',flush=True)
