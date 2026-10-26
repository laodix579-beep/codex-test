"""Reviewed bilingual targets, contextual usage, escaping and read-only answers."""
import json
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
BASE = 'http://127.0.0.1:8000/'
catalog = json.loads((ROOT / 'data/meaning-catalog.json').read_text())
rows = {row['id']: row for row in catalog['entries']}
groups = json.loads((ROOT / 'data/basic-vocabulary.json').read_text())['subcategories']
assert len(rows) == 136
assert [row['word'] for row in rows.values() if row['mode'] == 'usage'] == ['zero', 'any', 'size']

with sync_playwright() as p:
    browser = p.chromium.launch(executable_path='/usr/bin/chromium', headless=True, args=['--no-sandbox'])
    context = browser.new_context(viewport={'width': 1696, 'height': 1000}, service_workers='block')
    context.add_init_script("Object.defineProperty(window,'speechSynthesis',{get(){throw new Error('TTS forbidden')}})")
    page = context.new_page()
    errors = []
    page.on('pageerror', lambda e: errors.append(str(e)))
    page.goto(BASE + '#home')
    seed = page.evaluate('''()=>{const key=document.body.dataset.storageKey,s=JSON.parse(localStorage.getItem(key));
        s.wordStatus['C01-S04-033']='unfamiliar';s.favorites=['C01-S02-050'];
        s.settings.userName='对应标色测试';s.settings.grade='三年级';
        s.notes=[{id:'meaning-note',title:'保留',body:'已有学习记录',createdAt:'2026-10-25T00:00:00Z',updatedAt:'2026-10-25T00:00:00Z'}];
        localStorage.setItem(key,JSON.stringify(s));return s;}''')
    page.reload()
    for group in groups:
        page.goto(BASE + '#words/C01/' + group['id'])
        page.locator('.translation-blank').first.wait_for()
        for index, word in enumerate(group['items']):
            row = rows[word['id']]
            prompt = page.locator('.word-example-prompt')
            hint = page.locator('.word-context-meaning')
            assert prompt.inner_text() == row['chinese']
            targets = prompt.locator('[data-meaning-target="chinese"]')
            assert targets.all_text_contents() == [span['text'] for span in row['spans']], row['word']
            if row['mode'] == 'usage':
                assert hint.inner_text().startswith('本句用法：')
                assert row['usage'] in hint.inner_text()
                definition = hint.locator('.meaning-dictionary')
                assert definition.inner_text() == '词义：' + row['meaning']
                assert definition.bounding_box()['y'] > hint.locator('.meaning-usage').bounding_box()['y']
                bounds = definition.bounding_box()
                assert bounds['y'] + bounds['height'] <= page.locator('.translation-slots').bounding_box()['y']
                assert targets.count() == 0
            else:
                assert hint.inner_text().startswith('词义：' + row['meaning'])
                assert hint.locator('.practice-target').inner_text() == row['meaning']
            expected = page.evaluate('''w=>{const c=FrogPractice.wordCloze(w);return FrogPractice.sentenceTokens(c.english).filter(t=>t.word&&c.blankIndices.includes(t.index)).map(t=>t.text);}''', {'word': word['english'], 'example': word['example_en'], 'exampleZh': word['example_zh']})
            assert page.locator('.translation-slots').inner_text().strip().lower().find(word['english'].lower()) == -1 or not word['english'].strip()
            before = page.evaluate('JSON.parse(localStorage.getItem(document.body.dataset.storageKey)).wordStatus')
            page.locator('#translation-form [data-action="translation-answer"]').click()
            dialog = page.locator('#practice-answer-dialog')
            assert dialog.locator('.mvp-answer-english strong').inner_text() == page.evaluate('(text)=>text.trim().replace(/[\\s\\p{P}\\p{S}]+$/u,"")', row['english'])
            assert dialog.locator('[data-meaning-target="english"]').all_text_contents() == expected, row['word']
            if row['mode'] == 'usage':
                assert dialog.locator('.meaning-dictionary').inner_text() == '中文释义：' + row['meaning']
            if targets.count():
                assert dialog.locator('[data-meaning-target="english"]').first.evaluate('e=>getComputedStyle(e).color') == targets.first.evaluate('e=>getComputedStyle(e).color')
                assert dialog.locator('.mvp-answer-note [data-meaning-target="chinese"]').all_text_contents() == targets.all_text_contents()
            if row['word'] == 'half':
                page.screenshot(path='/tmp/meaning-v28-half-answer.png')
            dialog.locator('[data-answer-close]').click()
            assert page.evaluate('JSON.parse(localStorage.getItem(document.body.dataset.storageKey)).wordStatus') == before
            if row['word'] in ('half', 'any'):
                page.screenshot(path='/tmp/meaning-v28-' + row['word'] + '.png')
            if index < len(group['items']) - 1:
                page.keyboard.press('Shift+ArrowRight')
        page.evaluate("window.meaningClosed=false;document.querySelector('#lesson-dialog').addEventListener('close',()=>window.meaningClosed=true,{once:true})")
        page.locator('.practice-back').click()
        page.wait_for_function('meaningClosed')
        print('PASS: reviewed Chinese spans and exact answer targets in ' + group['name'], flush=True)
    actual = page.evaluate('JSON.parse(localStorage.getItem(document.body.dataset.storageKey))')
    for key in ['words', 'wordStatus', 'favorites', 'settings', 'notes', 'plan']:
        assert actual[key] == seed[key], key

    # Matching uses the actual bilingual sentence, not an ID or dictionary substring.
    page.evaluate('''()=>{const key=document.body.dataset.storageKey,s=JSON.parse(localStorage.getItem(key));
        const red=s.words.find(w=>w.word==='red');
        s.words.push({...red,id:'meaning-import-copy'});
        red.exampleZh='这个苹果是红色的。<img src=x onerror="window.meaningXss=true">';
        localStorage.setItem(key,JSON.stringify(s));}''')
    page.goto(BASE + '#words/all')
    page.reload()
    page.locator('[data-action="learn-word"][data-id="C01-S03-001"]').click()
    page.locator('.translation-blank').first.wait_for()
    assert page.locator('.word-example-prompt [data-meaning-target]').count() == 0
    assert '暂未确认逐字对应关系' in page.locator('.word-context-meaning').inner_text()
    assert page.locator('.word-example-prompt img').count() == 0
    assert page.evaluate('window.meaningXss') is None
    page.locator('#translation-form [data-action="translation-answer"]').click()
    assert page.locator('#practice-answer-dialog .mvp-answer-note img').count() == 0
    # A nested colored target is still a non-speaker close position.
    page.locator('#practice-answer-dialog [data-meaning-target="english"]').click()
    assert page.locator('#practice-answer-dialog').evaluate('e=>!e.open')
    page.evaluate("window.meaningClosed=false;document.querySelector('#lesson-dialog').addEventListener('close',()=>window.meaningClosed=true,{once:true})")
    page.locator('.practice-back').click()
    page.wait_for_function('meaningClosed')
    page.goto(BASE + '#words/all')
    page.locator('[data-action="learn-word"][data-id="meaning-import-copy"]').click()
    page.locator('.translation-blank').first.wait_for()
    assert page.locator('.word-example-prompt [data-meaning-target]').inner_text() == '红色的'
    assert not errors, errors
    print('PASS: read-only answers, all existing words/records/settings, imported exact copy, edited sentence fallback and HTML escaping', flush=True)
    context.close()

    for width in (320, 390, 760):
        mobile = browser.new_context(viewport={'width': width, 'height': 844}, is_mobile=True, has_touch=True, service_workers='block')
        phone = mobile.new_page()
        for group_id, index, target, expected in (('C01-S02',49,'half',['半个']),('C01-S02',47,'any',[]),('C01-S02',0,'zero',[]),('C01-S04',32,'size',[])):
            phone.goto(BASE + '#words/C01/' + group_id)
            phone.locator('.translation-blank').first.wait_for()
            phone.locator('#practice-jump').evaluate('(e,index)=>{e.value=String(index);e.dispatchEvent(new Event("change",{bubbles:true}))}', index)
            phone.wait_for_function('(index)=>document.querySelector("#practice-jump").value===String(index)', arg=index)
            assert phone.locator('.word-example-prompt [data-meaning-target]').all_text_contents() == expected
            if not expected:
                row = next(row for row in rows.values() if row['word'] == target)
                assert row['usage'] in phone.locator('.word-context-meaning').inner_text()
                definition = phone.locator('.word-context-meaning .meaning-dictionary')
                assert definition.inner_text() == '词义：' + row['meaning']
                bounds = definition.bounding_box()
                assert bounds['y'] + bounds['height'] <= phone.locator('.translation-slots').bounding_box()['y']
            phone.locator('.mobile-controls [data-action="translation-answer"]').click()
            assert phone.locator('.translation-answer [data-meaning-target="english"]').all_text_contents() == [target]
            assert phone.evaluate('document.documentElement.scrollWidth<=innerWidth')
            phone.evaluate("window.meaningClosed=false;document.querySelector('#lesson-dialog').addEventListener('close',()=>window.meaningClosed=true,{once:true})")
            phone.locator('.practice-back').click()
            phone.wait_for_function('meaningClosed')
        mobile.close()
    browser.close()
print('COMPLETE: 136 bilingual highlights, contextual usage, safe matching and phone sizes passed', flush=True)
