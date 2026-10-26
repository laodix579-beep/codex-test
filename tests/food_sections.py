"""Exercise every refined C05 choice and preserve actual v38 learner state."""
import hashlib
import json
from pathlib import Path
import re
import subprocess
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
BASE = 'http://127.0.0.1:8000/'
BASELINE = 'c6f59f735f3afefa51862a3d8b3169c182232289'
old_html = subprocess.check_output(['git', 'show', BASELINE + ':index.html'], text=True)
html = (ROOT / 'index.html').read_text()
pattern = r'<script id="practice-group-library">.*?</script>\s*'
assert re.sub(pattern, '', html, flags=re.S) == re.sub(pattern, '', old_html, flags=re.S).replace('frog-food-health-v38', 'frog-food-sections-v39')
sections = json.loads((ROOT / 'data/food-health-practice-sections.json').read_text())['subcategories']
assert [len(s['groups']) for s in sections] == [11, 11, 6, 9]
assert sum(len(g['wordIds']) for s in sections for g in s['groups']) == 218
old_groups = json.loads(subprocess.check_output(['git', 'show', BASELINE + ':data/practice-groups.json']))
groups = json.loads((ROOT / 'data/practice-groups.json').read_text())
assert [s for s in groups['subcategories'] if not s['subcategoryId'].startswith('C05-')] == [s for s in old_groups['subcategories'] if not s['subcategoryId'].startswith('C05-')]
for file in ['data/food-health-windows.json', 'data/meaning-catalog.json', 'data/scene-catalog.json', 'audio-manifest.json', 'audio-files.js', 'data/catalog-packs.json']:
    assert (ROOT / file).read_bytes() == subprocess.check_output(['git', 'show', BASELINE + ':' + file])
media = json.loads((ROOT / 'reports/all-audio-sha256.json').read_text())
assert len(media) == 2169
for path, row in media.items():
    assert hashlib.sha256((ROOT / path).read_bytes()).hexdigest() == row['sha256']
for folder in ['food-health', 'time-nature', 'school-learning', 'family-daily']:
    for file in (ROOT / 'data' / folder).glob('*.json'):
        assert file.read_bytes() == subprocess.check_output(['git', 'show', BASELINE + ':' + file.relative_to(ROOT).as_posix()])
print('PASS: only practice definitions/cache changed; all 972 words, raw sources, IPA/meanings, scenes and 2169 recordings preserved', flush=True)

with sync_playwright() as p:
    browser = p.chromium.launch(executable_path='/usr/bin/chromium', args=['--no-sandbox'])
    context = browser.new_context(viewport={'width': 1440, 'height': 900}, service_workers='block')
    context.add_init_script("Object.defineProperty(window,'speechSynthesis',{get(){throw new Error('Runtime TTS forbidden')}})")
    page = context.new_page()
    errors = []
    page.on('pageerror', lambda e: errors.append(str(e)))
    page.goto(BASE + '#home')
    words = page.evaluate('FROG_WORD_CATALOG.words')
    def stored():
        return page.evaluate('JSON.parse(localStorage.getItem(document.body.dataset.storageKey))')
    def choose(sub):
        page.goto(BASE + '#words/C05')
        page.locator(f'.mvp-subcategory[data-subcategory-id="{sub}"]').click()
        page.locator('#practice-group-dialog').wait_for(state='visible')
    def close_practice():
        page.locator('.practice-back').click()
        page.wait_for_function('!document.querySelector("#lesson-dialog").open')
    for section, count in zip(sections, [64, 69, 41, 44]):
        sub = section['subcategoryId']
        expected_all = [w for w in words if w['subcategoryId'] == sub]
        ids = [i for g in section['groups'] for i in g['wordIds']]
        assert len(ids) == len(set(ids)) == count and set(ids) == {w['id'] for w in expected_all}
        for group in [{'id': 'all', 'wordIds': ids}, *section['groups']]:
            choose(sub)
            dialog = page.locator('#practice-group-dialog')
            assert dialog.locator('.practice-group-choice').count() == len(section['groups'])
            assert dialog.locator('.practice-group-all b').inner_text() == str(count)
            box = dialog.bounding_box()
            assert box['y'] >= 0 and box['y'] + box['height'] <= 900
            expected = [w for w in expected_all if w['id'] in group['wordIds']]
            button = dialog.locator(f'[data-practice-group="{group["id"]}"]')
            assert button.locator('b').inner_text() == str(len(expected))
            button.click()  # Also checks choices below the fold scroll into view.
            page.locator('.translation-blank').first.wait_for()
            assert page.locator('#practice-jump option').all_text_contents() == [f'{i+1}. {w["word"]}' for i, w in enumerate(expected)]
            assert stored()['practiceResume']['ids'] == [w['id'] for w in expected]
            assert page.locator('.translation-picture').get_attribute('data-scene-id') == expected[0]['id']
            if sub == 'C05-S04' and group['id'] != 'all':
                page.locator('#translation-form [data-action="translation-answer"]').click()
                answer = page.locator('#practice-answer-dialog')
                assert answer.locator('.mvp-answer-line>span:not(.mvp-dj)').inner_text() == expected[0]['ipa']
                answer.locator('[data-answer-audio="word"]').click()
                page.wait_for_function('(word)=>{const a=document.querySelector("#question-audio");return a.dataset.sourceText===word&&a.currentTime>0}', arg=expected[0]['word'])
                assert answer.evaluate('e=>e.open')
                page.keyboard.press('Escape')
                assert not answer.evaluate('e=>e.open')
                assert not stored()['wordStatus']
            close_practice()
        print('PASS: ' + sub + ' whole group and ' + str(len(section['groups'])) + ' detailed sections; exact words, counts, pictures and scroll access', flush=True)
    context.close()

    # Seed the state with the real old application, then load the updated one.
    context = browser.new_context(viewport={'width': 1440, 'height': 900}, service_workers='block')
    page = context.new_page()
    page.route(BASE + '?legacy-food-v38', lambda route: route.fulfill(body=old_html, content_type='text/html; charset=utf-8'), times=1)
    page.goto(BASE + '?legacy-food-v38#home')
    legacy = page.evaluate('''()=>{const k=document.body.dataset.storageKey,s=JSON.parse(localStorage.getItem(k));
      const ids=s.words.filter(w=>w.id.startsWith('C05-S03-')).map(w=>w.id);
      s.practiceResume={ids,wordId:ids[5],answered:false,finished:false};
      s.wordStatus['C05-S06-001']='mastered';s.wordStatus['C05-S05-002']='unfamiliar';
      s.settings.userName='原健康学习者';s.settings.grade='四年级';s.settings.volume=.35;
      s.favorites=['C05-S06-001'];s.notes=[{id:'keep-food-note',title:'原笔记',body:'细分后仍保留',createdAt:'2026-10-01T00:00:00Z',updatedAt:'2026-10-01T00:00:00Z'}];
      s.days['2020-01-01']={seconds:1234,words:['C05-S06-001'],sentences:[],mistakes:1,checked:true};
      localStorage.setItem(k,JSON.stringify(s));return s;}''')
    page.goto(BASE + '#home')
    current = stored()
    for key in ['words', 'wordStatus', 'settings', 'favorites', 'notes', 'plan', 'contentPacks', 'practiceResume']:
        assert current[key] == legacy[key], key
    assert current['days']['2020-01-01'] == legacy['days']['2020-01-01']
    choose('C05-S04')
    page.locator('#practice-group-dialog [data-close]').click()
    assert stored()['practiceResume'] == legacy['practiceResume']
    page.goto(BASE + '#home')
    page.locator('.home-resume-card [data-action="resume-desktop"]').click()
    assert page.locator('#practice-jump option').count() == 43
    assert page.locator('.translation-picture').get_attribute('data-scene-id') == legacy['practiceResume']['wordId']
    close_practice()
    choose('C05-S04')
    page.locator('[data-practice-group="health-status"]').click()
    page.locator('.translation-blank').first.fill('healthy')
    page.locator('#translation-submit').click()
    page.locator('.mvp-solved-actions [data-action="next-item"]').click()
    assert page.locator('.translation-picture').get_attribute('data-scene-id') == 'C05-S06-002'
    close_practice()
    page.goto(BASE + '#home');page.reload()
    page.locator('.home-resume-card [data-action="resume-desktop"]').click()
    assert page.locator('#practice-jump option').count() == 4
    assert page.locator('.translation-picture').get_attribute('data-scene-id') == 'C05-S06-002'
    page.locator('#translation-previous').click()
    page.locator('#restart-practice-group').click()
    assert page.locator('#translation-previous').is_disabled()
    assert stored()['wordStatus']['C05-S06-001'] == 'mastered'
    close_practice()
    # Deleted canonical words and user additions keep accurate choices/counts.
    page.evaluate('''()=>{const k=document.body.dataset.storageKey,s=JSON.parse(localStorage.getItem(k));
      s.words=s.words.filter(w=>w.id!=='C05-S06-004');
      const w=s.words.find(w=>w.id==='C05-S06-001');s.words.push({...w,id:'custom-food-health',word:'wellness',meaning:'用户自定义健康词'});
      localStorage.setItem(k,JSON.stringify(s));}''')
    page.reload();before = stored();choose('C05-S04')
    assert page.locator('.practice-group-all b').inner_text() == '44'
    assert page.locator('[data-practice-group="health-status"] b').inner_text() == '3'
    assert page.locator('[data-practice-group="other"] b').inner_text() == '1'
    page.locator('[data-practice-group="other"]').click()
    assert stored()['practiceResume']['ids'] == ['custom-food-health']
    for key in ['words', 'wordStatus', 'settings', 'favorites', 'notes', 'plan', 'contentPacks']:
        assert stored()[key] == before[key], key
    print('PASS: real v38 records and old 43-word subset resume retained; refined subset grading, reload/resume, previous/restart and dynamic user edits work', flush=True)
    assert not errors, errors
    context.close();browser.close()
print('COMPLETE: all 37 detailed C05 sections and learner-state preservation passed', flush=True)
