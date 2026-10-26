"""C03 source fidelity, additive installation, unchanged practice and GA media."""
import hashlib
import json
from pathlib import Path
import re
import subprocess
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
BASE = 'http://127.0.0.1:8000/'
BASELINE = 'c2aacbaa5228570ae6011d6b51829fa43d2fa42b'
marker = 'window.FROG_WORD_CATALOG = '
catalog = json.JSONDecoder().raw_decode((ROOT / 'index.html').read_text().split(marker, 1)[1])[0]
previous = json.JSONDecoder().raw_decode(subprocess.check_output(['git', 'show', BASELINE + ':index.html'], text=True).split(marker, 1)[1])[0]
assert catalog['version'] == previous['version'] == 'basic-us-v1'
assert [w for w in catalog['words'] if w['categoryId'] in ('C01', 'C02')] == previous['words']
assert len(catalog['words']) == 972
for file, key in [('data/meaning-catalog.json', 'entries'), ('data/scene-catalog.json', 'scenes')]:
    old = json.loads(subprocess.check_output(['git', 'show', BASELINE + ':' + file]))
    current = json.loads((ROOT / file).read_text())
    assert [r for r in current[key] if r['id'].startswith(('C01-', 'C02-'))] == old[key]
for file in ['data/basic-vocabulary.json', 'data/category-art.json']:
    assert (ROOT / file).read_bytes() == subprocess.check_output(['git', 'show', BASELINE + ':' + file])
old_audio = json.loads(subprocess.check_output(['git', 'show', BASELINE + ':reports/all-audio-sha256.json']))
assert len(old_audio) == 1028
for path, row in old_audio.items():
    assert hashlib.sha256((ROOT / path).read_bytes()).hexdigest() == row['sha256']
groups = [json.loads(p.read_text()) for p in sorted((ROOT / 'data/school-learning').glob('0*.json'))]
assert [len(g['items']) for g in groups] == [43, 45, 31, 79]
generation = json.loads((ROOT / 'data/school-learning-audio-generation.json').read_text())
assert len(generation['clips']) == 359 and generation['voice'] == 'af_bella' and generation['locale'] == 'en-US'
assert next(r for r in generation['clips'] if r['key'] == 'pe')['phonemes'] == 'pˈi ˈi'
assert all('ɹˈɛd' not in r['phonemes'] for r in generation['clips'] if re.search(r'\bread\b', r['text'], re.I))

with sync_playwright() as p:
    browser = p.chromium.launch(executable_path='/usr/bin/chromium', args=['--no-sandbox'])
    context = browser.new_context(viewport={'width': 1696, 'height': 1000}, service_workers='block')
    context.add_init_script("Object.defineProperty(window,'speechSynthesis',{get(){throw new Error('Runtime TTS forbidden')}})")
    page = context.new_page()
    errors = []
    page.on('pageerror', lambda e: errors.append(str(e)))
    page.goto(BASE + '#home')
    legacy = page.evaluate('''()=>{const k=document.body.dataset.storageKey,s=JSON.parse(localStorage.getItem(k));
      s.words=s.words.filter(w=>w.categoryId!=='C03');s.contentPacks=['time-nature-v1'];
      s.words[0].notes='旧词自定义笔记';s.words.push({...s.words[0],id:'custom-school-read',word:'read',meaning:'读（过去式）',ipa:'/red/',categoryId:'C08',subcategoryId:'C08-S01'});
      s.wordStatus={'C01-S01-001':'mastered','C02-S01-001':'unfamiliar','custom-school-read':'mastered'};
      s.settings.userName='已有学习者';s.settings.grade='四年级';s.settings.rate=.9;
      s.favorites=['C01-S01-001','C02-S01-001','custom-school-read'];
      s.notes=[{id:'school-legacy-note',title:'原笔记',body:'必须保留',createdAt:'2026-10-01T00:00:00Z',updatedAt:'2026-10-01T00:00:00Z'}];
      s.days['2026-10-01']={seconds:1234,words:['C02-S01-001'],sentences:[],mistakes:2,checked:true};
      const ids=s.words.filter(w=>w.subcategoryId==='C02-S01').map(w=>w.id);s.practiceResume={ids,wordId:ids[3],answered:false,finished:false};
      localStorage.setItem(k,JSON.stringify(s));return s;}''')
    def saved():
        return page.evaluate('JSON.parse(localStorage.getItem(document.body.dataset.storageKey))')
    page.reload();page.locator('.home-dashboard').wait_for()
    now = saved()
    assert len(now['words']) == 973 and now['contentPacks'] == ['time-nature-v1', 'school-learning-v1', 'family-daily-v1', 'food-health-v1']
    for word in legacy['words']:
        assert next(w for w in now['words'] if w['id'] == word['id']) == word
    for key in ['wordStatus', 'favorites', 'notes', 'settings', 'plan', 'practiceResume']:
        assert now[key] == legacy[key], key
    assert now['days']['2026-10-01'] == legacy['days']['2026-10-01']
    assert page.evaluate("FrogPractice.speechKey('close','关闭')") == 'close::verb'
    assert page.evaluate("FrogPractice.speechKey('read','读（过去式）')") == 'read::past'
    assert page.evaluate("FrogPractice.referenceNote('read','读（过去式）')") is None
    page.reload();assert len(saved()['words']) == 973
    page.evaluate('''()=>{const k=document.body.dataset.storageKey,s=JSON.parse(localStorage.getItem(k));s.words=s.words.filter(w=>w.id!=='C03-S01-001');localStorage.setItem(k,JSON.stringify(s));}''')
    page.reload();assert not any(w['id'] == 'C03-S01-001' for w in saved()['words'])
    page.goto(BASE + '#settings')
    page.locator('#restore-file').set_input_files({'name': 'before-school.json', 'mimeType': 'application/json', 'buffer': json.dumps(legacy, ensure_ascii=False).encode()})
    page.locator('#confirm-dialog button[value="yes"]').click()
    page.wait_for_function('JSON.parse(localStorage.getItem(document.body.dataset.storageKey)).words.some(w=>w.id==="C03-S01-001")')
    assert len(saved()['words']) == 973 and saved()['wordStatus'] == legacy['wordStatus']
    context.close()
    print('PASS: all 356 old words, custom homograph, profile, status, backup, notes, favorites and resume preserved; C03 installs once and respects deletion', flush=True)

    context = browser.new_context(viewport={'width': 1696, 'height': 1000}, service_workers='block')
    context.add_init_script("Object.defineProperty(window,'speechSynthesis',{get(){throw new Error('Runtime TTS forbidden')}})")
    page = context.new_page();page.on('pageerror', lambda e: errors.append(str(e)))
    page.goto(BASE + '#home')
    assert page.locator('.home-category-tile[data-category-id="C03"]>small').inner_text() == '198 个单词'
    page.locator('.home-category-tile[data-category-id="C03"]').click()
    assert page.locator('.mvp-subcategory').count() == 4
    definitions = json.loads((ROOT / 'data/practice-groups.json').read_text())['subcategories']
    meanings = {r['id']: r for r in json.loads((ROOT / 'data/meaning-catalog.json').read_text())['entries']}
    for group in groups:
        subid = group['subcategory_id']
        page.goto(BASE + '#words/C03')
        page.locator(f'.mvp-subcategory[data-subcategory-id="{subid}"]').click()
        dialog = page.locator('#practice-group-dialog')
        assert int(dialog.locator('.practice-group-all b').inner_text()) == len(group['items'])
        section = next(s for s in definitions if s['subcategoryId'] == subid)
        for part in section['groups']:
            assert int(dialog.locator(f'[data-practice-group="{part["id"]}"] b').inner_text()) == len(part['wordIds'])
        part = section['groups'][0]
        dialog.locator(f'[data-practice-group="{part["id"]}"]').click()
        assert page.locator('#practice-jump option').count() == len(part['wordIds'])
        assert page.locator('.translation-picture').get_attribute('data-scene-id') == part['wordIds'][0]
        page.locator('.practice-back').click();page.wait_for_function('!document.querySelector("#lesson-dialog").open')
        page.goto(BASE + '#words/C03/' + subid)
        page.locator('.translation-blank').first.wait_for()
        for i, row in enumerate(group['items']):
            page.wait_for_function('document.querySelector(".translation-picture img")?.naturalWidth>0')
            assert page.locator('.translation-picture').get_attribute('data-scene-id') == row['id']
            canonical = page.evaluate('(id)=>FROG_WORD_CATALOG.words.find(w=>w.id===id)', row['id'])
            assert (canonical['word'], canonical['meaning'], canonical['ipa'], canonical['example'], canonical['exampleZh']) == (row['english'], row['chinese'], row['ipa_dj_british'], row['example_en'], row['example_zh'])
            assert page.evaluate('(w)=>!!FrogPractice.wordCloze(w)', canonical)
            assert page.locator('.word-example-prompt').inner_text() == row['example_zh']
            assert page.locator('.word-example-prompt [data-meaning-target="chinese"]').all_text_contents() == [s['text'] for s in meanings[row['id']]['spans']]
            assert row['chinese'] in page.locator('.word-context-meaning').inner_text()
            page.locator('#translation-form [data-action="translation-answer"]').click()
            answer = page.locator('#practice-answer-dialog')
            assert answer.locator('.mvp-answer-line>span:not(.mvp-dj)').inner_text() == row['ipa_dj_british']
            expected = page.evaluate('(s)=>s.trim().replace(/[\\s\\p{P}\\p{S}]+$/u,"")', row['example_en'])
            assert answer.locator('.mvp-answer-english strong').inner_text() == expected
            if i in (0, len(group['items']) - 1) or row['english'] in ('PE', 'read', 'project', 'close'):
                for role, text in [('word', row['english']), ('example', row['example_en'])]:
                    answer.locator(f'[data-answer-audio="{role}"]').click()
                    page.wait_for_function('(text)=>{const a=document.querySelector("#question-audio");return FrogPractice.normalize(a.dataset.sourceText)===FrogPractice.normalize(text)&&a.currentTime>0&&!a.paused}', arg=text)
                    assert answer.evaluate('e=>e.open')
            answer.locator('[data-answer-close]').click()
            if i < len(group['items']) - 1:
                page.keyboard.press('Shift+ArrowRight')
        page.locator('.practice-back').click();page.wait_for_function('!document.querySelector("#lesson-dialog").open')
        print('PASS: every source example, DJ IPA, scene, meaning, group count and answer flow in ' + group['subcategory_name'], flush=True)
    assert not saved()['wordStatus']
    decoded = page.evaluate('''async()=>{const ctx=new AudioContext(),rows=Object.entries(LOCAL_AUDIO_BANK.clips).filter(([k,p])=>p.includes('/school/'));let n=0,total=0;
      await Promise.all(Array.from({length:6},async()=>{while(n<rows.length){const [key,path]=rows[n++],r=await fetch(path),bytes=await r.arrayBuffer();
        const hash=Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',bytes)),n=>n.toString(16).padStart(2,'0')).join('');if(hash!==LOCAL_AUDIO_BANK.sha256[key])throw Error('Hash '+key);
        const b=await ctx.decodeAudioData(bytes);let peak=0;for(const s of b.getChannelData(0))peak=Math.max(peak,Math.abs(s));
        if(b.duration<.1||peak<.005||peak>=1)throw Error('Invalid recording '+key);total++;}}));await ctx.close();return total;}''')
    assert decoded == 359
    assert not errors, errors
    context.close()
    for mobile in (False, True):
        context = browser.new_context(viewport={'width': 390 if mobile else 1440, 'height': 844 if mobile else 960}, is_mobile=mobile, has_touch=mobile, service_workers='block')
        page = context.new_page();page.goto(BASE + '#words/C03/C03-S01')
        page.locator('.translation-blank').first.fill('schoolbag')
        page.locator('.mobile-controls [data-action="translation-submit"]' if mobile else '#translation-submit').click()
        assert saved()['wordStatus']['C03-S01-001'] == 'mastered'
        page.locator('.mobile-controls [data-action="next-item"]' if mobile else '.mvp-solved-actions [data-action="next-item"]').last.click()
        assert page.locator('.translation-picture').get_attribute('data-scene-id') == 'C03-S01-002'
        assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
        if not mobile:
            page.locator('#translation-previous').click();assert page.locator('.translation-picture').get_attribute('data-scene-id') == 'C03-S01-001'
            page.locator('#restart-practice-group').click();assert page.locator('#translation-previous').is_disabled()
        context.close()
    browser.close()
print('COMPLETE: C03 integration, all 359 new MP3 hashes/decodes and desktop/mobile submit/next passed', flush=True)
