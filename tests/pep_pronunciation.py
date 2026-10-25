"""PEP-oriented GA consonants, stress, homographs and full-sentence playback."""
import base64,hashlib,json,re
from pathlib import Path
from playwright.sync_api import sync_playwright
root=Path(__file__).resolve().parents[1]
guide=json.loads((root/'data/pep-pronunciation.json').read_text())
bank=json.loads(re.search(r'window.LOCAL_AUDIO_BANK=(.*?);\s*</script>',(root/'index.html').read_text(),re.S).group(1))
phones=bank['phonemes']
prosody=json.loads((root/'data/prosody-review.json').read_text())
assert prosody['speechRevision']==bank['revision']
supplied=json.loads((root/'reports/source-audio-sha256.json').read_text())
for case in prosody['cases']:
 assert hashlib.sha256((root/bank['clips'][case['audioKey']]).read_bytes()).hexdigest()==supplied[bank['clips'][case['audioKey']]]['sha256']
 assert (case['ratio']>1.03 if case['target']=='rise' else case['ratio']<.97)
for word in ['please','is','has','these']:assert phones[word].endswith('z'),word
assert phones['pleased'].endswith('zd') and not phones['please'].endswith('zd')
assert phones['three'].startswith('θ') and phones['this'].startswith('ð')
assert phones['five'].endswith('v') and phones['very'].startswith('v')
assert 'æ' in phones['class'] and 'ɑ' in phones['dog'] and 'ɑ' in phones['hot']
assert 'O' in phones['robot'] and not any(c in phones['robot'] for c in ('Q','ɒ'))
assert phones['thirteen'].index('ˈ')>phones['thirteen'].index('t')
assert phones['thirty'].index('ˈ')<phones['thirty'].index('ɜ')
assert phones['close::verb'].endswith('z') and phones['close::adjective'].endswith('s')
assert phones['raise your hand please'].rstrip('.').endswith('z')
assert phones['can you help me please'].rstrip('?').endswith('z')
assert bank['intonations']['raise your hand please']=='fall'
assert bank['intonations']['can you help me please']=='rise'
assert bank['profiles']['sentence']['speed']<=.9
print('PASS: GA consonant and stress inputs; close senses; final please; elementary pace and intonation targets',flush=True)

with sync_playwright() as p:
 browser=p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox'])
 page=browser.new_page(viewport={'width':1440,'height':1000});errors=[]
 page.on('pageerror',lambda e:errors.append(str(e)))
 page.goto('http://127.0.0.1:8000/#phonetics')
 assert page.locator('.pronunciation-check').count()==len(guide['words'])
 for i,row in enumerate(guide['words']):
  card=page.locator('.pronunciation-check').nth(i)
  assert card.locator('.ipa').inner_text()=='DJ '+row['dj']
  card.locator('button').click()
  page.wait_for_function('(key)=>{const a=document.querySelector("#question-audio");return a.dataset.audioKey===key&&a.currentTime>0}',arg=row['audioKey'])
 for i,row in enumerate(guide['sentences']):
  page.locator('.sentence-check').nth(i).locator('button').click()
  page.wait_for_function('(text)=>{const a=document.querySelector("#question-audio");return a.dataset.sourceText===text&&a.currentTime>0}',arg=row['english'])
  assert page.locator('#question-audio').get_attribute('data-delivery')=='sentence'
 print('PASS: every reference word and full sentence plays its own recording with DJ-only IPA labels',flush=True)
 notes=page.evaluate('''()=>({verb:FrogPractice.sentenceTokens('Close your book.').find(x=>x.text==='Close').ipa,
  adjective:FrogPractice.sentenceTokens('We are close friends.').find(x=>x.text==='close').ipa})''')
 assert notes=={'verb':'/kləʊz/','adjective':'/kləʊs/'}
 page.evaluate('''()=>{const key=document.body.dataset.storageKey,s=JSON.parse(localStorage.getItem(key));
  s.wordStatus[s.words[0].id]='mastered';
  for(const [id,meaning]of [['close-v','关闭'],['close-adj','亲密的']])s.words.push({id,word:'close',meaning,ipa:'/kloʊs/',example:'',categoryId:'C01',subcategoryId:'C01-S01'});
  localStorage.setItem(key,JSON.stringify(s));}''')
 page.goto('http://127.0.0.1:8000/#words/manage/C01/C01-S01');page.reload()
 for id,suffix,ipa in [('close-v','verb','/kləʊz/'),('close-adj','adjective','/kləʊs/')]:
  card=page.locator('.word-card').filter(has=page.locator(f'[data-action="speak-word"][data-id="{id}"]'))
  assert card.locator('.ipa').inner_text()=='DJ '+ipa
  card.locator('[data-action="speak-word"]').click()
  page.wait_for_function('(key)=>{const a=document.querySelector("#question-audio");return a.dataset.audioKey===key&&a.currentTime>0}',arg='close::'+suffix)
  card.locator('[data-action="learn-word"]').click();page.locator('.translation-blank').wait_for()
  assert page.locator('#question-audio').get_attribute('data-audio-key')=='close::'+suffix
  page.locator('#lesson-dialog [data-close]').click()
 assert page.evaluate('JSON.parse(localStorage.getItem(document.body.dataset.storageKey)).wordStatus["C01-S01-001"]')=='mastered'
 assert not errors,errors
 print('PASS: custom close senses use correct DJ IPA and /z/ or /s/ recordings in cards and spelling practice; progress survives',flush=True)
 browser.close()
print('COMPLETE: 3 PEP pronunciation regression groups passed',flush=True)
