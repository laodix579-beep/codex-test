"""C02 source fidelity, non-destructive installation and existing practice flow."""
import hashlib
import json
from pathlib import Path
import re
import subprocess
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]
BASE='http://127.0.0.1:8000/'
groups=[json.loads(p.read_text()) for p in sorted((ROOT/'data/time-nature').glob('0*.json'))]
assert [len(g['items']) for g in groups]==[52,61,56,51]
rows=[w for g in groups for w in g['items']]
original=json.loads((ROOT/'reports/source-audio-sha256.json').read_text())
for path,row in original.items():assert hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==row['sha256']
source=(ROOT/'index.html').read_text();marker='window.FROG_WORD_CATALOG = '
catalog=json.JSONDecoder().raw_decode(source.split(marker,1)[1])[0]
old=subprocess.check_output(['git','show','1d4f963:index.html'],text=True)
previous=json.JSONDecoder().raw_decode(old.split(marker,1)[1])[0]
assert catalog['version']==previous['version']=='basic-us-v1'
assert [w for w in catalog['words'] if w['categoryId']=='C01']==previous['words']
assert len(catalog['words'])==356
generation=json.loads((ROOT/'data/time-nature-audio-generation.json').read_text())
assert len(generation['clips'])==418 and generation['voice']=='af_bella' and generation['locale']=='en-US'
assert next(r for r in generation['clips'] if r['key']=='wind')['phonemes']=='wˈɪnd'

with sync_playwright() as p:
    browser=p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox'])
    context=browser.new_context(viewport={'width':1440,'height':1000},service_workers='block',accept_downloads=True)
    context.add_init_script("Object.defineProperty(window,'speechSynthesis',{get(){throw new Error('Runtime TTS forbidden')}})")
    page=context.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
    page.goto(BASE+'#home')
    legacy=page.evaluate('''()=>{const key=document.body.dataset.storageKey,s=JSON.parse(localStorage.getItem(key));
      s.words=s.words.filter(w=>w.categoryId!=='C02');delete s.contentPacks;
      s.words[0].notes='用户修改过的旧词笔记';s.words.push({...s.words[0],id:'custom-preserved',word:'wind',meaning:'缠绕（用户自定义动词）',ipa:'/waɪnd/',categoryId:'C08',subcategoryId:'C08-S01'});
      s.wordStatus['C01-S01-001']='mastered';s.wordStatus['custom-preserved']='unfamiliar';
      s.settings.userName='已有学习者';s.settings.grade='四年级';s.settings.voice='original-voice';s.settings.rate=.9;
      s.favorites=['C01-S01-001','custom-preserved'];s.notes=[{id:'nature-legacy-note',title:'原笔记',body:'必须保留',createdAt:'2026-10-01T00:00:00Z',updatedAt:'2026-10-01T00:00:00Z'}];
      s.days['2026-10-01']={seconds:1234,words:['C01-S01-001'],sentences:[],mistakes:2,checked:true};
      const ids=s.words.filter(w=>w.subcategoryId==='C01-S01').map(w=>w.id);s.practiceResume={ids,wordId:ids[3],answered:false,finished:false};
      localStorage.setItem(key,JSON.stringify(s));return s;}''')
    page.reload();page.locator('.home-dashboard').wait_for()
    def saved():return page.evaluate('JSON.parse(localStorage.getItem(document.body.dataset.storageKey))')
    now=saved()
    assert len(now['words'])==357 and now['contentPacks']==['time-nature-v1']
    assert page.evaluate("FrogPractice.speechKey('wind','缠绕（动词）')")== 'wind::verb'
    assert page.evaluate("FrogPractice.speechKey('wind','风')")== 'wind'
    for word in legacy['words']:assert next(w for w in now['words'] if w['id']==word['id'])==word
    for key in ['wordStatus','favorites','notes','settings','plan','practiceResume']:assert now[key]==legacy[key],key
    assert now['days']['2026-10-01']==legacy['days']['2026-10-01']
    page.reload();assert len(saved()['words'])==357
    # Explicit deletion is respected after the one-time content installation.
    page.evaluate('''()=>{const k=document.body.dataset.storageKey,s=JSON.parse(localStorage.getItem(k));s.words=s.words.filter(w=>w.id!=='C02-S01-001');localStorage.setItem(k,JSON.stringify(s));}''')
    page.reload();assert not any(w['id']=='C02-S01-001' for w in saved()['words'])
    page.goto(BASE+'#settings');page.locator('#restore-file').set_input_files({'name':'legacy-before-C02.json','mimeType':'application/json','buffer':json.dumps(legacy,ensure_ascii=False).encode()})
    page.locator('#confirm-dialog button[value="yes"]').click()
    page.wait_for_function('JSON.parse(localStorage.getItem(document.body.dataset.storageKey)).words.some(w=>w.id==="C02-S01-001")')
    assert len(saved()['words'])==357 and saved()['wordStatus']==legacy['wordStatus']
    assert not errors,errors
    context.close();print('PASS: existing v29 state and old backup append C02 once; every old word, record, preference and resume survives; deletions remain deleted',flush=True)

    context=browser.new_context(viewport={'width':1696,'height':1000},service_workers='block')
    context.add_init_script("Object.defineProperty(window,'speechSynthesis',{get(){throw new Error('Runtime TTS forbidden')}})")
    page=context.new_page();page.on('pageerror',lambda e:errors.append(str(e)))
    page.goto(BASE+'#home');assert page.locator('.home-category-tile[data-category-id="C02"]>small').inner_text()=='220 个单词'
    page.locator('.home-category-tile[data-category-id="C02"]').click()
    assert page.locator('.mvp-subcategory').count()==4
    assert [int(s.split('/')[1].split()[0]) for s in page.locator('.mvp-subcategory>small').all_text_contents()]==[52,61,56,51]
    samples=[];fallback=[]
    for group in groups:
        page.goto(BASE+'#words/C02/'+group['subcategory_id']);page.locator('.translation-blank').first.wait_for()
        for i,row in enumerate(group['items']):
            page.wait_for_function('document.querySelector(".translation-picture img")?.naturalWidth>0')
            assert page.locator('.translation-picture').get_attribute('data-scene-id')==row['id']
            canonical=page.evaluate('(id)=>FROG_WORD_CATALOG.words.find(w=>w.id===id)',row['id'])
            assert (canonical['word'],canonical['meaning'],canonical['ipa'],canonical['example'],canonical['exampleZh'])==(row['english'],row['chinese'],row['ipa_dj_british'],row['example_en'],row['example_zh'])
            cloze=page.evaluate('(w)=>FrogPractice.wordCloze(w)',canonical)
            if cloze:assert page.locator('.word-example-prompt').inner_text()==row['example_zh']
            else:fallback.append(row['id'])
            page.locator('#translation-form [data-action="translation-answer"]').click()
            assert page.locator('#practice-answer-dialog .mvp-answer-line>span:not(.mvp-dj)').inner_text()==row['ipa_dj_british']
            expected=page.evaluate('(s)=>s.trim().replace(/[\\s\\p{P}\\p{S}]+$/u,"")',row['example_en'] if cloze else row['english'])
            assert page.locator('#practice-answer-dialog .mvp-answer-english strong').inner_text()==expected
            if i in (0,len(group['items'])-1):
                for role,text in [('word',row['english']),('example',row['example_en'] if cloze else row['english'])]:
                    page.locator(f'#practice-answer-dialog [data-answer-audio="{role}"]').click()
                    page.wait_for_function('(text)=>{const a=document.querySelector("#question-audio");return FrogPractice.normalize(a.dataset.sourceText)===FrogPractice.normalize(text)&&a.currentTime>0&&!a.paused}',arg=text)
                    assert page.locator('#question-audio').get_attribute('src').startswith('blob:')
                samples.append(row['id'])
            page.locator('#practice-answer-dialog [data-answer-close]').click()
            if row['id'] in ['C02-S01-009','C02-S02-061','C02-S03-006','C02-S04-022']:
                page.screenshot(path='/tmp/nature-'+row['id']+'.png')
            if i<len(group['items'])-1:page.keyboard.press('Shift+ArrowRight')
        page.evaluate("window.natureClosed=false;document.querySelector('#lesson-dialog').addEventListener('close',()=>natureClosed=true,{once:true})")
        page.locator('.practice-back').click();page.wait_for_function('natureClosed')
        print('PASS: all source entries, DJ IPA, existing answer flow, scene mappings and GA sample playback in '+group['subcategory_name'],flush=True)
    assert fallback==['C02-S02-058','C02-S02-059','C02-S02-061'],fallback
    assert page.evaluate('Object.keys(JSON.parse(localStorage.getItem(document.body.dataset.storageKey)).wordStatus).length')==0
    # Every new recording is actually decoded, including quiet/short word clips.
    decoded=page.evaluate('''async()=>{
      const ctx=new AudioContext(),rows=Object.entries(LOCAL_AUDIO_BANK.clips).filter(([k,p])=>p.includes('/nature/'));let next=0,total=0;
      await Promise.all(Array.from({length:6},async()=>{while(next<rows.length){const [key,path]=rows[next++],r=await fetch(path),bytes=await r.arrayBuffer();
        const hash=Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',bytes)),n=>n.toString(16).padStart(2,'0')).join('');if(hash!==LOCAL_AUDIO_BANK.sha256[key])throw new Error('Wrong audio '+key);
        const b=await ctx.decodeAudioData(bytes),samples=b.getChannelData(0);let peak=0;for(const n of samples)peak=Math.max(peak,Math.abs(n));
        if(b.duration<.1||peak<.005||peak>=1)throw new Error('Silent/invalid/clipped new audio '+key);total++;
      }}));await ctx.close();return total;
    }''')
    assert decoded==418
    assert not errors,errors
    context.close();print('PASS: all 418 generated GA MP3s match hashes and decode without silence/clipping; existing sentence-mismatch fallback handles exactly three supplied examples',flush=True)
    for mobile in (False,True):
        context=browser.new_context(viewport={'width':390 if mobile else 1440,'height':844 if mobile else 960},is_mobile=mobile,has_touch=mobile,service_workers='block')
        page=context.new_page();page.goto(BASE+'#words/C02/C02-S01');page.locator('.translation-blank').first.wait_for()
        # Use the existing submit controls and resume cursor, not a new workflow.
        page.locator('.translation-blank').first.fill('time')
        page.locator('.mobile-controls [data-action="translation-submit"]' if mobile else '#translation-submit').click()
        assert page.evaluate('JSON.parse(localStorage.getItem(document.body.dataset.storageKey)).wordStatus["C02-S01-001"]')=='mastered'
        page.locator('.mobile-controls [data-action="next-item"]' if mobile else '.mvp-solved-actions [data-action="next-item"]').last.click()
        assert page.locator('.translation-picture').get_attribute('data-scene-id')=='C02-S01-002'
        assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
        context.close()
    browser.close()
print('COMPLETE: time and nature content integration passed',flush=True)
