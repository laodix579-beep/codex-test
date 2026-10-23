"""DJ display references and US word/example playback regression checks.

Requires the development server on port 8000, Playwright and Chromium.
"""
import base64
import hashlib
import json
from pathlib import Path
import re
from playwright.sync_api import sync_playwright

BASE='http://127.0.0.1:8000/'

root=Path(__file__).resolve().parents[1]
source=(root/'index.html').read_text()
bank=json.loads(re.search(r'window.LOCAL_AUDIO_BANK=(.*?);\s*</script>',source,re.S).group(1))
review=json.loads((root/'data/speech-review.json').read_text())
assert review['speechRevision']==bank['revision']
for case in review['cases']:
    assert bank['texts'][case['audioKey']]==case['displayedText']
    assert hashlib.sha256(base64.b64decode(bank['clips'][case['audioKey']])).hexdigest()==case['audioSha256']

with sync_playwright() as p:
    browser=p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox'])
    context=browser.new_context(viewport={'width':1440,'height':900})
    page=context.new_page();errors=[]
    page.on('pageerror',lambda e:errors.append(str(e)))
    page.goto(BASE+'#words/C01/C01-S01')
    info=page.evaluate('''()=>({ipa:FROG_WORD_CATALOG.ipaSystem,ipaLocale:FROG_WORD_CATALOG.ipaLocale,
        voice:FrogPractice.speechProfile.locale,bank:LOCAL_AUDIO_BANK.locale,
        revision:LOCAL_AUDIO_BANK.revision,hello:FROG_WORD_CATALOG.words.find(w=>w.word==='hello').ipa,
        please:FROG_WORD_CATALOG.words.find(w=>w.word==='please').ipa})''')
    assert info=={'ipa':'DJ','ipaLocale':'en-GB','voice':'en-US','bank':'en-US',
        'revision':'clear-us-dj-v4','hello':'/həˈləʊ/','please':'/pliːz/'}
    assert 'DJ /pliːz/' in page.locator('.word-card').filter(has=page.locator('[data-action="speak-word"][data-id="C01-S01-011"]')).inner_text()
    print('PASS: DJ written references are separate from US recordings and US system-voice selection',flush=True)

    page.evaluate('''()=>{
        const key=document.body.dataset.storageKey,s=JSON.parse(localStorage.getItem(key));
        s.settings.rate=.65;
        const hello=s.words.find(w=>w.word==='hello');hello.ipa='/həˈloʊ/';
        s.wordStatus[hello.id]='mastered';localStorage.setItem(key,JSON.stringify(s));
    }''')
    page.reload()
    repaired=page.evaluate('JSON.parse(localStorage.getItem(document.body.dataset.storageKey))')
    assert next(w for w in repaired['words'] if w['word']=='hello')['ipa']=='/həˈləʊ/'
    assert repaired['wordStatus']['C01-S01-001']=='mastered'
    print('PASS: saved built-in IPA updates to DJ while preserving study progress and chosen practice speed',flush=True)

    card=page.locator('.word-card').filter(has=page.locator('[data-action="speak-word"][data-id="C01-S01-011"]'))
    word=card.locator('[data-action="speak-word"]');example=card.locator('.word-example-speak')
    word.click()
    page.wait_for_function('document.getElementById("question-audio").currentTime>0')
    assert page.locator('#question-audio').get_attribute('data-source-text')=='please'
    assert page.locator('#question-audio').evaluate('a=>a.playbackRate')==1
    example.click()
    page.wait_for_function('document.getElementById("question-audio").currentTime>0')
    assert page.locator('#question-audio').get_attribute('data-source-text')=='Please sit down.'
    assert page.locator('#question-audio').get_attribute('data-prompt')=='please sit down'
    assert page.locator('#question-audio').evaluate('a=>a.playbackRate')==1
    word.click();example.click();word.click()
    page.wait_for_function('document.getElementById("question-audio").currentTime>0')
    assert page.locator('#question-audio').get_attribute('data-source-text')=='please'
    print('PASS: please and Please sit down use their exact separate recordings at standard speed, including rapid switching',flush=True)

    card.locator('[data-action="learn-word"]').click()
    page.locator('.translation-blank').wait_for()
    assert page.locator('#question-audio').evaluate('a=>a.playbackRate')==.65
    page.locator('#lesson-dialog [data-close]').click()
    page.goto(BASE+'#phonetics')
    assert 'DJ' in page.locator('#content').inner_text() and '美式' in page.locator('#content').inner_text()
    assert page.locator('.phonetic-card').filter(has_text='near').locator('.symbol').inner_text()=='/ɪə/'
    assert not errors,errors
    print('PASS: practice retains the selected rate; phonetic lessons show DJ references and explain the US example audio',flush=True)
    browser.close()

print('COMPLETE: 4 speech reference regression groups passed',flush=True)
