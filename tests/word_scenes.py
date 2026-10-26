"""All 136 built-in examples resolve to their own generated cartoon scene."""
import hashlib
import json
from pathlib import Path
from PIL import Image
from playwright.sync_api import sync_playwright, expect

ROOT=Path(__file__).resolve().parents[1]
catalog=json.loads((ROOT/'data/scene-catalog.json').read_text())
groups=json.loads((ROOT/'data/basic-vocabulary.json').read_text())['subcategories']
scenes={scene['id']:scene for scene in catalog['scenes'] if scene['id'].startswith('C01-')}
assert len(scenes)==136
assert len({(s['sheet'],s['column'],s['row']) for s in scenes.values()})==136
assert len(catalog['sheets'])==82
for sheet in catalog['sheets']:
    path=ROOT/sheet['path']
    with Image.open(path) as im:assert im.size==(sheet['width'],sheet['height'])
    assert hashlib.sha256(path.read_bytes()).hexdigest()==sheet['sha256']
print('PASS: 136 distinct scene regions and all 82 image dimensions/hashes',flush=True)

with sync_playwright() as p:
    browser=p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox'])
    context=browser.new_context(viewport={'width':1886,'height':930})
    context.add_init_script("Object.defineProperty(window,'speechSynthesis',{get(){throw new Error('TTS forbidden')}})")
    page=context.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
    saved=lambda:page.evaluate('JSON.parse(localStorage.getItem(document.body.dataset.storageKey))')
    for group in groups:
        page.goto('http://127.0.0.1:8000/#words/C01/'+group['id'])
        page.locator('.translation-blank').first.wait_for()
        for index,word in enumerate(group['items']):
            scene=scenes[word['id']]
            picture=page.locator('.translation-picture')
            expect(picture).to_have_attribute('data-scene-id',word['id'])
            assert picture.get_attribute('aria-label')==word['example_zh']
            page.wait_for_function('document.querySelector(".translation-picture img")?.naturalWidth>0')
            assert scene['sheet'] in picture.locator('img').get_attribute('src')
            sheet=next(s for s in catalog['sheets'] if s['path']==scene['sheet'])
            style=picture.locator('img').get_attribute('style')
            assert style.endswith(f'transform:translate(-{scene["column"]*100/sheet["columns"]:g}%,-{scene["row"]*100/sheet["rows"]:g}%)')
            if sheet['columns']==1:assert style.startswith('width:100%;height:100%;')
            if scene.get('visual'):
                visual=scene['visual'];overlay=picture.locator('.scene-quantity')
                assert overlay.get_attribute('data-quantity-type')==visual['type']
                if visual['type'] in ['count','fingers','calendar','clock']:
                    expect(overlay.locator('[data-count-item]')).to_have_count(visual['value'])
                for text in overlay.locator('text').all():
                    assert text.evaluate('e=>getComputedStyle(e).fill')!='none'
            # The answer shows this same scene and never grades the question.
            page.locator('#translation-form [data-action="translation-answer"]').click()
            expect(page.locator('#practice-answer-dialog .scene-art-stage')).to_have_attribute('data-scene-id',word['id'])
            page.locator('#practice-answer-dialog [data-answer-close]').click()
            assert saved()['wordStatus']=={}
            if index<len(group['items'])-1:page.keyboard.press('Shift+ArrowRight')
        page.locator('.practice-back').click()
        page.wait_for_function('!document.querySelector("#lesson-dialog").open')
        print('PASS: every question and answer scene in '+group['name']+', read-only answers and exact quantities',flush=True)
    # Matching follows both word and sentence, including imported copies.
    matching=page.evaluate('''()=>{const w=FROG_WORD_CATALOG.words.find(w=>w.id==='C01-S03-001');return {copy:FrogScenes.match({...w,id:'custom-red'})?.id,changed:FrogScenes.match({...w,example:'The car is red.'}),unknown:FrogScenes.match({id:'custom',word:'unmapped',example:'No matching art.'})}}''')
    assert matching=={'copy':'C01-S03-001','changed':None,'unknown':None}
    page.goto('http://127.0.0.1:8000/#words/C01/C01-S03');page.locator('.translation-blank').first.fill('red')
    page.locator('#translation-submit').click()
    expect(page.locator('.mvp-solved .translation-picture')).to_have_attribute('data-scene-id','C01-S03-001')
    assert saved()['wordStatus']['C01-S03-001']=='mastered'
    page.locator('.mvp-solved-actions [data-action="next-item"]').click()
    expect(page.locator('.translation-picture')).to_have_attribute('data-scene-id','C01-S03-002')
    page.locator('.mvp-session-settings>summary').click()
    page.locator('.mvp-session-settings [data-session-setting="showPicture"]').uncheck()
    assert page.locator('.translation-picture').count()==0
    page.locator('.mvp-session-settings>summary').click()
    page.locator('.mvp-session-settings [data-session-setting="showPicture"]').check()
    expect(page.locator('.translation-picture')).to_have_attribute('data-scene-id','C01-S03-002')
    for width in (1024,1440,1886):
        page.set_viewport_size({'width':width,'height':930})
        assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
        bounds=page.locator('.translation-picture .scene-tile').bounding_box();outer=page.locator('.translation-picture').bounding_box()
        assert bounds['width']<=outer['width']+1 and bounds['height']<=outer['height']+1
    assert not errors,errors
    print('PASS: sentence-sensitive matching, solved/next scenes, picture toggle, grading and desktop sizes',flush=True)
    context.close();browser.close()
print('COMPLETE: every built-in cartoon scene passed',flush=True)
