"""Site-wide coverage/media invariants and every historical small-group resume."""
import hashlib
import json
from pathlib import Path
import re
import subprocess
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
BASE = 'http://127.0.0.1:8000/'
BASELINE = 'c9487d016cfa526d242563d7f8dcf755ce96aa5e'
old_html = subprocess.check_output(['git', 'show', BASELINE + ':index.html'], text=True)
new_html = (ROOT / 'index.html').read_text()
pattern = r'<script id="practice-group-library">.*?</script>\s*'
# Application/source immutability is checked against v41 by animal_nature.py;
# this file also exercises every pre-merge v40 historical subset.
old_groups = json.loads(subprocess.check_output(['git', 'show', BASELINE + ':data/practice-groups.json']))
new_groups = json.loads((ROOT / 'data/practice-groups.json').read_text())
assert [s for s in old_groups['subcategories'] if s['subcategoryId'].startswith('C05-')] == [s for s in new_groups['subcategories'] if s['subcategoryId'].startswith('C05-')]
small = [(s['subcategoryId'], g) for s in old_groups['subcategories'] for g in s['groups'] if len(g['wordIds']) < 10]
assert len(small) == 25
audit = json.loads((ROOT / 'reports/practice-group-audit.json').read_text())
assert (audit['totalWords'], audit['populatedEntrances'], audit['practiceGroups'], audit['chooserEntrances'], audit['directEntrances'], audit['emptyEntrances']) == (1210, 24, 76, 22, 2, 8)
sizes = [g['words'] for s in audit['subcategories'] for g in s['groups']]
assert min(sizes) == 10 and max(sizes) == 24
for file in ['data/basic-vocabulary.json', 'data/category-art.json', 'data/food-health-practice-sections.json', 'category-files.js']:
    assert (ROOT / file).read_bytes() == subprocess.check_output(['git', 'show', BASELINE + ':' + file])
for folder in ['time-nature', 'school-learning', 'family-daily', 'food-health']:
    for file in (ROOT / 'data' / folder).glob('*.json'):
        assert file.read_bytes() == subprocess.check_output(['git', 'show', BASELINE + ':' + file.relative_to(ROOT).as_posix()])
recordings = json.loads((ROOT / 'reports/all-audio-sha256.json').read_text())
assert len(recordings) == 2616
for path, row in recordings.items():
    assert hashlib.sha256((ROOT / path).read_bytes()).hexdigest() == row['sha256']
for catalog in ['data/scene-catalog.json', 'data/category-art.json']:
    for sheet in json.loads((ROOT / catalog).read_text())['sheets']:
        assert hashlib.sha256((ROOT / sheet['path']).read_bytes()).hexdigest() == sheet['sha256']
print('PASS: 1210 words across 24 populated entrances, all 76 study groups are 10–24 words; every original recording/image/source and application function preserved', flush=True)

with sync_playwright() as p:
    browser = p.chromium.launch(executable_path='/usr/bin/chromium', args=['--no-sandbox'])
    old_context = browser.new_context(viewport={'width': 1440, 'height': 960}, service_workers='block')
    page = old_context.new_page()
    page.route(BASE + '?previous-site-v40', lambda route: route.fulfill(body=old_html, content_type='text/html; charset=utf-8'), times=1)
    page.goto(BASE + '?previous-site-v40#home')
    fixture = page.evaluate('''()=>{const key=document.body.dataset.storageKey,s=JSON.parse(localStorage.getItem(key));
      s.settings.userName='原站学习者';s.settings.grade='五年级';s.settings.volume=.35;
      s.words.push({...s.words[0],id:'custom-site-history',word:'legacy word',meaning:'用户历史词条',categoryId:'C08',subcategoryId:'C08-S01'});
      s.wordStatus={'C01-S01-001':'mastered','C04-S01-001':'unfamiliar','custom-site-history':'mastered'};
      s.favorites=['C01-S01-001','custom-site-history'];s.notes=[{id:'site-audit-note',title:'原手账',body:'全部保留',createdAt:'2026-10-01T00:00:00Z',updatedAt:'2026-10-01T00:00:00Z'}];
      s.days['2020-01-01']={seconds:1234,words:['C01-S01-001'],sentences:[],mistakes:1,checked:true};
      return {key,state:s};}''')
    old_context.close()
    errors = []
    for sub, group in small:
        state = json.loads(json.dumps(fixture['state']))
        ids = [w['id'] for w in state['words'] if w['id'] in group['wordIds']]
        state['practiceResume'] = {'ids': ids, 'wordId': ids[-1], 'answered': False, 'finished': False}
        context = browser.new_context(viewport={'width': 1440, 'height': 960}, service_workers='block')
        context.add_init_script('localStorage.setItem(' + json.dumps(fixture['key']) + ',' + json.dumps(json.dumps(state, ensure_ascii=False)) + ');')
        context.add_init_script("Object.defineProperty(window,'speechSynthesis',{get(){throw new Error('Runtime TTS forbidden')}})")
        page = context.new_page();page.on('pageerror', lambda e: errors.append(str(e)))
        page.goto(BASE + '#home')
        current = page.evaluate('JSON.parse(localStorage.getItem(document.body.dataset.storageKey))')
        assert [w for w in current['words'] if w['categoryId'] != 'C06'] == state['words']
        assert current['contentPacks'] == state['contentPacks'] + ['animal-nature-v1']
        for key in ['wordStatus', 'settings', 'favorites', 'notes', 'plan', 'practiceResume']:
            assert current[key] == state[key], (sub, group['id'], key)
        assert current['days']['2020-01-01'] == state['days']['2020-01-01']
        page.locator('.home-resume-card [data-action="resume-desktop"]').click()
        page.locator('.translation-blank').first.wait_for()
        assert page.locator('#practice-jump option').count() == len(ids)
        assert page.locator('.translation-picture').get_attribute('data-scene-id') == ids[-1]
        context.close()
        print('PASS: preserved old subset resume and all learner data in ' + sub + '/' + group['id'], flush=True)
    assert not errors, errors
    browser.close()
print('COMPLETE: all 25 old small-group resumes preserved after the site-wide merges', flush=True)
