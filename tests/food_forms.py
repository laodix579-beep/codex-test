"""Preserve 754 old clozes and grade C05 noun plurals from source sentences."""
import json
from pathlib import Path
import subprocess
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
baseline = subprocess.check_output(['git', 'show', '234ae2e:index.html'], cwd=ROOT, text=True)
old_function = baseline.split('  function wordCloze(item) {', 1)[1].split('  function translationPlan', 1)[0]
old_function = 'function wordCloze(item) {' + old_function
old_words = json.JSONDecoder().raw_decode(baseline.split('window.FROG_WORD_CATALOG = ', 1)[1])[0]['words']

with sync_playwright() as p:
    browser = p.chromium.launch(executable_path='/usr/bin/chromium', args=['--no-sandbox'])
    context = browser.new_context(viewport={'width': 1440, 'height': 960}, service_workers='block')
    page = context.new_page();page.goto('http://127.0.0.1:8000/')
    assert page.evaluate('''({source,words})=>{
      const previous=new Function('sentenceTokens','normalize','return ('+source+')')(FrogPractice.sentenceTokens,FrogPractice.normalize);
      return words.every(w=>JSON.stringify(previous(w))===JSON.stringify(FrogPractice.wordCloze(w)));
    }''', {'source': old_function, 'words': old_words})
    assert len(old_words) == 754
    cases = [('C05-S02-014', ['green','beans'], ['green','bean']), ('C05-S02-030', ['Bean','sprouts'], ['bean','sprout'])]
    page.goto('http://127.0.0.1:8000/#words/C05/C05-S01')
    page.locator('.translation-blank').first.wait_for()
    for word_id, correct, wrong in cases:
        word=page.evaluate('(id)=>FROG_WORD_CATALOG.words.find(w=>w.id===id)',word_id)
        index=str(page.evaluate('(id)=>FROG_WORD_CATALOG.words.filter(w=>w.subcategoryId==="C05-S01").findIndex(w=>w.id===id)',word_id))
        page.locator('#practice-jump').evaluate('(e,value)=>{e.value=value;e.dispatchEvent(new Event("change",{bubbles:true}))}',index)
        for field,text in zip(page.locator('.translation-blank').all(),wrong):field.fill(text)
        page.locator('#translation-submit').click()
        assert page.evaluate('(id)=>JSON.parse(localStorage.getItem(document.body.dataset.storageKey)).wordStatus[id]',word_id)!='mastered'
        for field,text in zip(page.locator('.translation-blank').all(),correct):field.fill(text)
        page.locator('#translation-submit').click()
        assert page.evaluate('(id)=>JSON.parse(localStorage.getItem(document.body.dataset.storageKey)).wordStatus[id]',word_id)=='mastered'
        assert page.evaluate('(id)=>JSON.parse(localStorage.getItem(document.body.dataset.storageKey)).words.find(w=>w.id===id).word',word_id)==word['word']
    for phrase, example in [('play with toys', 'The child displays with toys.'),
                            ('wash the dishes', 'My brother washes dishes.'),
                            ('do the washing', 'Mum does the homework.'),
                            ('mop the floor', 'Dad mops the car.'), ('green bean','The screen beans are red.'), ('bean sprout','The bean grows sprouts.')]:
        assert page.evaluate('(w)=>FrogPractice.wordCloze(w)', {'word': phrase, 'example': example, 'exampleZh': '不能误判匹配。'}) is None
    browser.close()
print('PASS: all 754 old clozes identical; C05 noun phrases require supplied plural endings and reject partial matches',flush=True)
