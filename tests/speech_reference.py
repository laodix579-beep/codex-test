"""DJ-only written references and GA word/sentence playback regression checks.

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

# Check GA synthesis inputs while retaining the independently maintained DJ display.
# Kokoro uses O for GA /oʊ/; rhotic vowels must not use the British phones.
for key,phones in {'hello':'həlˈO','half':'hˈæf','four':'fˈɔɹ',
        'bird':'bˈɜɹd','hot':'hˈɑt','hair':'hˈɛɹ','square':'skwˈɛɹ'}.items():
    assert bank['phonemes'][key]==phones,(key,bank['phonemes'][key])
assert bank['voiceLocale']=='en-US'  # Retain the original voice's timbre.
assert bank['pronunciation']=='GA'
assert bank['styles']['please']=='word' and bank['styles']['please sit down']=='sentence'
assert bank['profiles']['word']['speed']==.92 and bank['profiles']['sentence']['speed']==.9

with sync_playwright() as p:
    browser=p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox'])
    context=browser.new_context(viewport={'width':1440,'height':900})
    page=context.new_page();errors=[]
    page.on('pageerror',lambda e:errors.append(str(e)))
    page.goto(BASE+'#words/manage/C01/C01-S01')
    info=page.evaluate('''()=>({ipa:FROG_WORD_CATALOG.ipaSystem,ipaLocale:FROG_WORD_CATALOG.ipaLocale,
        voice:FrogPractice.speechProfile.locale,bank:LOCAL_AUDIO_BANK.locale,
        revision:LOCAL_AUDIO_BANK.revision,hello:FROG_WORD_CATALOG.words.find(w=>w.word==='hello').ipa,
        please:FROG_WORD_CATALOG.words.find(w=>w.word==='please').ipa})''')
    assert info=={'ipa':'DJ','ipaLocale':'en-GB','voice':'en-US','bank':'en-US',
        'revision':'pep-ga-v7','hello':'/həˈləʊ/','please':'/pliːz/'}
    assert 'DJ /pliːz/' in page.locator('.word-card').filter(has=page.locator('[data-action="speak-word"][data-id="C01-S01-011"]')).inner_text()
    print('PASS: DJ written references remain British while recordings and system fallback use GA',flush=True)

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
    assert page.locator('#question-audio').get_attribute('data-delivery')=='word'
    assert page.locator('#question-audio').evaluate('a=>a.playbackRate')==1
    example.click()
    page.wait_for_function('document.getElementById("question-audio").currentTime>0')
    assert page.locator('#question-audio').get_attribute('data-source-text')=='Please sit down.'
    assert page.locator('#question-audio').get_attribute('data-delivery')=='sentence'
    assert page.locator('#question-audio').get_attribute('data-prompt')=='please sit down'
    assert page.locator('#question-audio').evaluate('a=>a.playbackRate')==1
    word.click();example.click();word.click()
    page.wait_for_function('document.getElementById("question-audio").currentTime>0')
    assert page.locator('#question-audio').get_attribute('data-source-text')=='please'
    assert page.locator('#question-audio').get_attribute('data-delivery')=='word'
    print('PASS: please and Please sit down use their exact separate recordings at standard speed, including rapid switching',flush=True)

    card.locator('[data-action="learn-word"]').click()
    page.locator('.translation-blank').wait_for()
    assert page.locator('#question-audio').evaluate('a=>a.playbackRate')==.65
    page.locator('#lesson-dialog [data-close]').click()
    page.goto(BASE+'#phonetics')
    assert 'DJ' in page.locator('#content').inner_text() and 'GA 美式' in page.locator('#content').inner_text()
    assert page.locator('.phonetic-card').filter(has_text='near').locator('.symbol').inner_text()=='/ɪə/'
    assert not errors,errors
    print('PASS: practice retains the selected rate; phonetic lessons show DJ references and explain GA example audio and accent differences',flush=True)
    # New content follows the same delivery rules through the US system fallback.
    page.goto(BASE+'#words/manage/C01/C01-S01')
    page.evaluate("""()=>{
        window.fallbackCalls=[];
        window.SpeechSynthesisUtterance=class{constructor(text){this.text=text;}};
        speechSynthesis.getVoices=()=>[{lang:'en-GB',name:'UK',voiceURI:'uk',localService:true},
            {lang:'en-US',name:'Samantha',voiceURI:'us',localService:true}];
        speechSynthesis.speak=u=>{fallbackCalls.push({text:u.text,lang:u.lang,rate:u.rate,voice:u.voice.voiceURI});u.onend?.();};
        delete LOCAL_AUDIO_BANK.clips['please'];delete LOCAL_AUDIO_BANK.clips['please sit down'];
    }""")
    card=page.locator('.word-card').filter(has=page.locator('[data-action="speak-word"][data-id="C01-S01-011"]'))
    card.locator('[data-action="speak-word"]').click();card.locator('.word-example-speak').click()
    calls=page.evaluate('fallbackCalls')
    assert calls==[{'text':'please','lang':'en-US','rate':.92,'voice':'us'},
        {'text':'Please sit down.','lang':'en-US','rate':.9,'voice':'us'}],calls
    assert not errors,errors
    print('PASS: system fallback uses a US voice, clear word delivery and whole-sentence natural delivery',flush=True)
    browser.close()

print('COMPLETE: 5 speech reference regression groups passed',flush=True)
