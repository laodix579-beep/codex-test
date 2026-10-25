"""A saved review position must not be inferred from lifetime mastery."""
import json
from pathlib import Path
from playwright.sync_api import sync_playwright, expect

BASE = 'http://127.0.0.1:8000/'
with sync_playwright() as p:
    browser = p.chromium.launch(executable_path='/usr/bin/chromium', headless=True, args=['--no-sandbox'])
    context = browser.new_context(viewport={'width': 1900, 'height': 1000}, accept_downloads=True)
    context.add_init_script("Object.defineProperty(window,'speechSynthesis',{get(){throw new Error('TTS forbidden')}})")
    page = context.new_page()
    errors = []
    page.on('pageerror', lambda e: errors.append(str(e)))
    saved = lambda: page.evaluate('JSON.parse(localStorage.getItem(document.body.dataset.storageKey))')

    def position(number):
        expect(page.locator('.mvp-resume-title')).to_contain_text(f'第 {number} / 22 词')

    def resume(number):
        page.locator('.home-resume-card [data-action="resume-desktop"]').click()
        expect(page.locator('#lesson-course')).to_contain_text(f'· {number}/22')
        page.locator('.translation-blank').first.wait_for()

    def leave():
        page.locator('.practice-back').click()
        page.wait_for_function('!document.querySelector("#lesson-dialog").open')

    def jump(index):
        page.locator('.mvp-practice-info .practice-options>summary').click()
        page.locator('#practice-jump').select_option(str(index))

    page.goto(BASE + '#home')
    page.locator('.home-dashboard').wait_for()
    # Reproduce the screenshot: a previously mastered group, now reviewing question 4.
    page.evaluate('''()=>{const key=document.body.dataset.storageKey,s=JSON.parse(localStorage.getItem(key)),ids=FROG_WORD_CATALOG.words.filter(w=>w.subcategoryId==='C01-S01').map(w=>w.id);
      ids.forEach(id=>s.wordStatus[id]='mastered');s.practiceResume={ids,wordId:ids[0]};
      s.notes=[{id:'resume-note',title:'保留手账',body:'原有内容',createdAt:'2026-10-01T00:00:00Z',updatedAt:'2026-10-01T00:00:00Z'}];
      s.settings.volume=.35;s.plan.words=50;localStorage.setItem(key,JSON.stringify(s));}''')
    page.reload()
    baseline = saved()
    resume(1)
    jump(3)
    expect(page.locator('#lesson-course')).to_contain_text('· 4/22')
    assert saved()['practiceResume']['wordId'] == 'C01-S01-004'
    leave()
    position(4)
    page.reload()
    position(4)
    page.screenshot(path='/tmp/resume-position-fourth.png')
    assert '继续' in page.locator('.home-resume-card [data-action="resume-desktop"]').inner_text()
    page.locator('[data-action="resume-details"]').click()
    expect(page.locator('.resume-details-summary')).to_contain_text('下次从第 4 词开始')
    page.locator('#resume-details-dialog .dialog-back').click()
    resume(4)
    for field, value in zip(page.locator('.translation-blank').all(), ['good', 'afternoon']):
        field.fill(value)
    page.locator('#translation-submit').click()
    leave()
    position(5)
    page.reload()
    position(5)
    print('PASS: mastered-group review returns to question 4; a correct submission continues to question 5', flush=True)

    resume(5)
    page.locator('[data-action="translation-answer"]').first.click()
    page.locator('#practice-answer-dialog').wait_for()
    page.locator('#practice-answer-dialog [data-answer-close]').click()
    leave()
    position(5)
    resume(5)
    page.keyboard.press('Shift+ArrowRight')
    expect(page.locator('#lesson-course')).to_contain_text('· 6/22')
    page.keyboard.press('Shift+ArrowLeft')
    expect(page.locator('#lesson-course')).to_contain_text('· 5/22')
    page.locator('.mvp-practice-info>[data-action="pause-practice"]').click()
    leave()
    page.reload()
    position(5)
    assert saved()['wordStatus'] == baseline['wordStatus']
    print('PASS: viewing answers, previous/next navigation and pausing retain the actual review cursor', flush=True)

    # A legacy saved cursor without the new round flags must also be honoured.
    page.evaluate('''()=>{const key=document.body.dataset.storageKey,s=JSON.parse(localStorage.getItem(key));s.practiceResume={ids:s.practiceResume.ids,wordId:'C01-S01-004'};localStorage.setItem(key,JSON.stringify(s));}''')
    page.reload()
    position(4)
    context.storage_state(path='/tmp/resume-position-state.json')
    context.close()
    context = browser.new_context(viewport={'width': 1900, 'height': 1000}, storage_state='/tmp/resume-position-state.json', accept_downloads=True)
    context.add_init_script("Object.defineProperty(window,'speechSynthesis',{get(){throw new Error('TTS forbidden')}})")
    page = context.new_page()
    page.on('pageerror', lambda e: errors.append(str(e)))
    page.goto(BASE + '#home')
    position(4)
    resume(4)
    jump(21)
    page.keyboard.press('Control+m')
    leave()
    position(1)
    expect(page.locator('.home-resume-card [data-action="resume-desktop"]')).to_have_text('复习本组')
    page.reload()
    position(1)
    resume(1)
    jump(3)
    leave()
    position(4)
    page.locator('#home-user-menu>summary').click()
    with page.expect_download() as dl:
        page.locator('#home-user-menu [data-action="backup"]').click()
    path = Path('/tmp/resume-position-backup.json')
    dl.value.save_as(path)
    backup = json.loads(path.read_text())
    assert backup['practiceResume']['wordId'] == 'C01-S01-004'
    assert backup['practiceResume']['answered'] is False
    assert backup['practiceResume']['finished'] is False
    assert all(backup['wordStatus'][id] == 'mastered' for id in backup['practiceResume']['ids'])
    for key in ['notes', 'settings', 'plan']:
        assert backup[key] == baseline[key]
    page.evaluate('''()=>{const key=document.body.dataset.storageKey,s=JSON.parse(localStorage.getItem(key));s.practiceResume.wordId='C01-S01-001';localStorage.setItem(key,JSON.stringify(s));}''')
    page.reload()
    position(1)
    page.locator('#restore-file').set_input_files(path)
    page.locator('#confirm-dialog button[value="yes"]').click()
    position(4)
    page.reload()
    position(4)
    assert saved()['practiceResume'] == backup['practiceResume']
    assert not errors, errors
    print('PASS: legacy cursor, browser reopening, completed-pass restart and backup/import preserve position and lifetime records', flush=True)
    context.close()
    browser.close()
print('COMPLETE: review-position regression passed', flush=True)
