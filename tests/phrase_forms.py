"""Preserve old clozes and grade inflected C04 verb phrases in their sentence."""
import json
from pathlib import Path
import subprocess
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
baseline = subprocess.check_output(['git', 'show', 'd9d7e71:index.html'], cwd=ROOT, text=True)
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
    assert len(old_words) == 554
    cases = [('026', 'play', 'plays'), ('033', 'wash', 'washes'), ('034', 'do', 'does'),
             ('038', 'mop', 'mops'), ('048', 'take', 'takes')]
    page.goto('http://127.0.0.1:8000/#words/C04/C04-S04')
    page.locator('.translation-blank').first.wait_for()
    for suffix, wrong, correct in cases:
        index = str(int(suffix) - 1)
        page.locator('#practice-jump').evaluate('(e,value)=>{e.value=value;e.dispatchEvent(new Event("change",{bubbles:true}))}', index)
        word = page.evaluate('(id)=>FROG_WORD_CATALOG.words.find(w=>w.id===id)', 'C04-S04-' + suffix)
        answers = page.evaluate('''w=>{const c=FrogPractice.wordCloze(w);return FrogPractice.sentenceTokens(c.english).filter(t=>t.word&&c.blankIndices.includes(t.index)).map(t=>t.text)}''', word)
        assert answers[0].lower() == correct
        for field, text in zip(page.locator('.translation-blank').all(), answers):
            field.fill(text)
        page.locator('.translation-blank').first.fill(wrong)
        page.locator('#translation-submit').click()
        assert page.evaluate('(id)=>JSON.parse(localStorage.getItem(document.body.dataset.storageKey)).wordStatus[id]', word['id']) != 'mastered'
        page.locator('.translation-blank').first.fill(correct)
        page.locator('#translation-submit').click()
        assert page.evaluate('(id)=>JSON.parse(localStorage.getItem(document.body.dataset.storageKey)).wordStatus[id]', word['id']) == 'mastered'
        assert page.evaluate('(id)=>JSON.parse(localStorage.getItem(document.body.dataset.storageKey)).words.find(w=>w.id===id).word', word['id']) == word['word']
    for phrase, example in [('play with toys', 'The child displays with toys.'),
                            ('wash the dishes', 'My brother washes dishes.'),
                            ('do the washing', 'Mum does the homework.'),
                            ('mop the floor', 'Dad mops the car.')]:
        assert page.evaluate('(w)=>FrogPractice.wordCloze(w)', {'word': phrase, 'example': example, 'exampleZh': '不能误判匹配。'}) is None
    browser.close()
print('PASS: all 554 old clozes identical; five C04 phrases require the supplied grammatical form, preserve base word and reject partial mismatches', flush=True)
