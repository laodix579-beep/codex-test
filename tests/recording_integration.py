"""Provided MP3 integrity, project-path search/playback, state and offline regression."""
import csv
import hashlib
import json
import re
from functools import partial
from http.server import SimpleHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path
from threading import Thread
from urllib.parse import urlparse
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]
manifest=json.loads((ROOT/'audio-manifest.json').read_text())
audit=json.loads((ROOT/'reports/source-audio-sha256.json').read_text())
clips=manifest['clips'];assert len(clips)==610==len(audit)
for row in clips:
 path=ROOT/row['path'];assert path.is_file()
 assert hashlib.sha256(path.read_bytes()).hexdigest()==audit[row['path']]['sha256'],row['path']
assert sum(1 for p in (ROOT/'audio').rglob('*.mp3'))==610
provided=list(csv.DictReader((ROOT/'vocabulary-audio-map.csv').open(encoding='utf-8-sig')))
assert len(provided)==136 and all(row['audio_path'] in audit for row in provided)
source=(ROOT/'index.html').read_text()
assert not re.search(r'\bspeechSynthesis\b|\bSpeechSynthesisUtterance\b',source)
results={'audioFilesByteIdentical':610,'formalVocabularyMappings':136,'profiles':[]}
class Quiet(SimpleHTTPRequestHandler):
 def log_message(self,*args):pass
server=ThreadingHTTPServer(('127.0.0.1',0),partial(Quiet,directory=str(ROOT.parent)))
Thread(target=server.serve_forever,daemon=True).start()
BASE=f'http://127.0.0.1:{server.server_port}/{ROOT.name}/'
blocked_api='''
Object.defineProperty(window,'speechSynthesis',{get(){throw new Error('Forbidden TTS access')},configurable:true});
Object.defineProperty(window,'SpeechSynthesisUtterance',{get(){throw new Error('Forbidden TTS construction')},configurable:true});
delete window.structuredClone;delete Object.hasOwn;delete Array.prototype.at;
'''
with sync_playwright() as p:
 browser=p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox'])
 for mobile in (False,True):
  context=browser.new_context(viewport={'width':390 if mobile else 1440,'height':844 if mobile else 1000},is_mobile=mobile,has_touch=mobile,user_agent='Mozilla/5.0 (Linux; Android 11) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.198 Mobile Safari/537.36 MicroMessenger/8.0.32' if mobile else None)
  context.add_init_script(blocked_api)
  page=context.new_page();errors=[];bad=[]
  page.on('pageerror',lambda e:errors.append(str(e)))
  page.on('request',lambda r:bad.append(r.url) if r.url.startswith('http') and not r.url.startswith(BASE) else None)
  page.goto(BASE,wait_until='networkidle');page.reload(wait_until='networkidle');assert page.locator('#global-search').is_visible()
  # Insert representative user data through the existing storage contract.
  preserved=page.evaluate('''()=>{
    const key=document.body.dataset.storageKey,s=JSON.parse(localStorage.getItem(key)),id=s.courses[0].sentences[0].id;
    s.wordStatus['C01-S01-001']='mastered';s.sentenceStatus[id]='unfamiliar';s.favorites=['C01-S01-001',id];
    s.courseFavorites=[s.courses[0].id];s.plan={minutes:37,sentences:7,words:11,courseIds:[s.courses[0].id]};
    s.days['2026-10-01']={seconds:1250,words:['C01-S01-001'],sentences:[id],mistakes:2,checked:true};
    s.settings.userName='保留用户';s.settings.voice='legacy-user-voice';
    s.notes=[{id:'note-preserved',title:'已有笔记',body:'请保留学习记录',createdAt:'2026-10-01T00:00:00.000Z',updatedAt:'2026-10-01T00:00:00.000Z'}];
    s.words.push({...s.words[0],id:'word-custom',word:'customword',meaning:'自定义词',itemType:'word',ipa:'/kʌstəm/',example:'A customword is here.',exampleZh:'这是自定义词。',categoryId:'C08',subcategoryId:'C08-S01'});
    s.wordStatus['word-custom']='unfamiliar';s.courses.push({...s.courses[0],id:'course-preserved',title:'我的导入课程',description:'原课程',category:'daily',level:'A1',color:'blue',sample:false,createdAt:'2026-10-01T00:00:00.000Z',sentences:[{...s.courses[0].sentences[0],id:'sentence-preserved',english:'My own course.',chinese:'我的课程。'}]});
    localStorage.setItem(key,JSON.stringify(s));return s;
  }''')
  page.reload(wait_until='networkidle')
  def search(text):
   page.locator('#global-search').fill(text);page.locator('#global-search').press('Enter')
   page.wait_for_function('(term)=>document.querySelector("#global-search").value===term&&location.hash.startsWith("#search")',arg=text)
   page.locator('#content h1').wait_for()
  def play(card,path,example=False):
   card.locator('.word-example-speak' if example else '[data-action="speak-word"]').click()
   page.wait_for_function('(path)=>{const a=document.querySelector("#question-audio");return a.currentSrc.endsWith(path)&&a.currentTime>0}',arg=path,timeout=15000)
   assert page.locator('#question-audio').get_attribute('data-delivery') in ('word','sentence')
  test_rows=list(csv.DictReader((ROOT/'pronunciation-test-words.csv').open(encoding='utf-8-sig')))
  checked=[]
  for row in test_rows:
   search(row['word']);word=row['word'].lower();card=page.locator(f'.search-results .word-card[data-word="{word}"]')
   card.wait_for();assert 'DJ /' in card.locator('.ipa').inner_text()
   play(card,row['audio_path']);checked.append(word)
   if word=='apple':assert 'eSpeak' in card.locator('.audio-source-note').inner_text()
  for term in ['APP','苹果','The apple is red']:
   search(term);assert page.locator('.word-card[data-word="apple"]').is_visible()
  search('zzzz-no-such-vocabulary-934');assert page.get_by_role('heading',name='没有找到相关内容').is_visible()
  page.locator('#clear-global-search').click();assert page.locator('#global-search').input_value()==''
  assert page.get_by_role('heading',name='输入要查找的内容').is_visible()
  old=[];sentences=[]
  by_key={r['audio_key']:r for r in clips}
  if not mobile:
   words=page.evaluate('FROG_WORD_CATALOG.words.slice(0,10)')
   for w in words:
    search(w['word']);card=page.locator(f'.word-card[data-word="{w["word"]}"]')
    key=page.evaluate('(w)=>FrogPractice.speechKey(w.word,w.meaning)',w)
    play(card,by_key[key]['path']);old.append(w['word'])
    sentence_key=page.evaluate('(w)=>FrogPractice.speechKey(w.example)',w)
    play(card,by_key[sentence_key]['path'],True);sentences.append(w['example'])
   decoded=page.evaluate('''async()=>{
     const audio=new AudioContext(),entries=Object.entries(LOCAL_AUDIO_BANK.clips);let next=0,total=0;
     await Promise.all(Array.from({length:6},async()=>{while(next<entries.length){
       const [key,path]=entries[next++],r=await fetch(path);if(!r.ok)throw new Error('Unavailable MP3: '+key);
       const sound=await audio.decodeAudioData(await r.arrayBuffer());
       if(sound.duration<.05||!sound.getChannelData(0).some(v=>Math.abs(v)>.001))throw new Error('Invalid or silent MP3: '+key);
       total++;
     }}));await audio.close();return total;
   }''')
   assert decoded==610;results['browserDecodedMp3']=decoded
  if page.locator('#global-search').input_value():page.locator('#clear-global-search').click()
  page.goto(BASE+'#settings');page.locator('#settings-form button[type="submit"]').click()
  page.wait_for_function('document.querySelector("[data-mobile-status]")?.textContent.startsWith("已保存离线内容")',timeout=90000)
  current=page.evaluate('JSON.parse(localStorage.getItem(document.body.dataset.storageKey))')
  for key in ['words','courses','notes','wordStatus','sentenceStatus','favorites','courseFavorites','plan','settings','days','chat']:
   assert current[key]==preserved[key],(key,[(a,b) for a,b in zip(current[key],preserved[key]) if a!=b][:1] if isinstance(current[key],list) else None)
  assert len(current['words'])==137 and not any(w['word'] in ('apple','book') for w in current['words'])
  context.set_offline(True);page.reload(wait_until='networkidle')
  assert page.locator('#content h1').inner_text()=='设置与备份'
  search('apple');play(page.locator('.word-card[data-word="apple"]'),'audio/en-us/word/apple.mp3')
  partial=page.evaluate('''async()=>{const r=await fetch('audio/en-us/word/apple.mp3',{headers:{Range:'bytes=0-127'}});return {status:r.status,bytes:(await r.arrayBuffer()).byteLength,range:r.headers.get('Content-Range')};}''')
  assert partial['status']==206 and partial['bytes']==128 and partial['range'].startswith('bytes 0-127/')
  search('customword');page.locator('.word-card[data-word="customword"] [data-action="speak-word"]').click()
  assert '暂无对应录音' in page.locator('#toast').inner_text()
  assert not errors,errors
  assert not bad,bad
  assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
  profile={'profile':'phone' if mobile else 'desktop','fourTestWordSearchAndPlayback':checked,'oldWords':old,'sentences':sentences,'partialSearch':True,'caseInsensitive':True,'chineseSearch':True,'exampleSearch':True,'clearAndNoResults':True,'statePreserved':True,'projectSubpath':True,'offlinePlayback':True,'offlineRange206':True,'missingRecordingNoTts':True}
  results['profiles'].append(profile)
  print('PASS',profile['profile'],'search/playback, preserved records, project path, offline playback and Range 206',flush=True)
  context.close()
 browser.close()
server.shutdown()
(ROOT/'reports/recording-integration-results.json').write_text(json.dumps(results,ensure_ascii=False,indent=2)+'\n')
print('COMPLETE: supplied MP3 integration passed',flush=True)
