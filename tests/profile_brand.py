"""Real profile form, header updates, backup compatibility and preserved records."""
import json
from pathlib import Path
from playwright.sync_api import sync_playwright,expect

BASE='http://127.0.0.1:8000/'
with sync_playwright() as p:
    browser=p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox'])
    context=browser.new_context(viewport={'width':1895,'height':940},accept_downloads=True)
    context.add_init_script("Object.defineProperty(window,'speechSynthesis',{get(){throw new Error('TTS forbidden')}})")
    page=context.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
    saved=lambda:page.evaluate('JSON.parse(localStorage.getItem(document.body.dataset.storageKey))')
    def menu():page.locator('#home-user-menu>summary').click()
    def profile():
        menu();page.get_by_role('button',name='个人资料填写',exact=True).click()
        page.locator('#profile-form').wait_for()
    def header(name):expect(page.locator('#home-user-menu>summary')).to_contain_text('你好，'+name)
    page.goto(BASE+'#home')
    expect(page.locator('.sidebar .brand')).to_contain_text('老K学英语')
    assert '老K学英语' in page.title()
    page.evaluate('''()=>{const key=document.body.dataset.storageKey,s=JSON.parse(localStorage.getItem(key));s.wordStatus['C01-S01-001']='mastered';s.practiceResume={ids:s.words.filter(w=>w.subcategoryId==='C01-S01').map(w=>w.id),wordId:'C01-S01-009',answered:false,finished:false};s.notes=[{id:'profile-note',title:'原有手账',body:'姓名更新仍保留的学习记录',createdAt:'2026-10-01T00:00:00Z',updatedAt:'2026-10-01T00:00:00Z'}];s.settings.volume=.35;localStorage.setItem(key,JSON.stringify(s));}''')
    page.reload();baseline=saved()
    profile()
    assert page.locator('#page-name').inner_text()=='个人资料填写'
    page.locator('#profile-name').fill('  林小K  ')
    page.locator('#profile-grade').fill('')
    page.locator('#profile-form button[type="submit"]').click()
    assert page.locator('#profile-grade').evaluate('e=>!e.checkValidity()')
    assert saved()==baseline
    page.locator('#profile-grade').fill('  三年级  ')
    page.locator('#profile-form button[type="submit"]').click()
    header('林小K')
    assert page.locator('#home-user-menu>summary').get_attribute('title')=='林小K · 三年级'
    page.reload();header('林小K')
    profile()
    expect(page.locator('#profile-name')).to_have_value('林小K')
    expect(page.locator('#profile-grade')).to_have_value('三年级')
    assert saved()['settings']['volume']==.35
    for key in ['words','wordStatus','notes','practiceResume','plan']:
        assert saved()[key]==baseline[key]
    page.locator('#profile-form [data-route="home"]').click();header('林小K')
    other=context.new_page();other.on('pageerror',lambda e:errors.append(str(e)))
    other.goto(BASE+'#profile')
    other.locator('#profile-name').fill('小林')
    other.locator('#profile-grade').fill('四年级')
    other.locator('#profile-form button[type="submit"]').click()
    header('小林')
    assert saved()['settings']['grade']=='四年级'
    other.close()
    menu()
    with page.expect_download() as dl:page.locator('#home-user-menu [data-action="backup"]').click()
    path=Path('/tmp/profile-v26-backup.json');dl.value.save_as(path);backup=json.loads(path.read_text())
    assert backup['settings']['userName']=='小林' and backup['settings']['grade']=='四年级'
    for key in ['words','wordStatus','notes','practiceResume','plan']:
        assert backup[key]==baseline[key]
    profile();page.locator('#profile-name').fill('临时姓名');page.locator('#profile-grade').fill('五年级')
    page.locator('#profile-form button[type="submit"]').click();header('临时姓名')
    page.locator('#restore-file').set_input_files(path)
    page.locator('#confirm-dialog button[value="yes"]').click();header('小林')
    assert saved()['settings']['grade']=='四年级'
    legacy=json.loads(path.read_text());del legacy['settings']['grade'];legacy['settings']['userName']='旧记录用户'
    legacy_path=Path('/tmp/profile-legacy-backup.json');legacy_path.write_text(json.dumps(legacy,ensure_ascii=False))
    page.locator('#restore-file').set_input_files(legacy_path)
    page.locator('#confirm-dialog button[value="yes"]').click();header('旧记录用户')
    assert saved()['settings']['grade']==''
    profile();expect(page.locator('#profile-grade')).to_have_value('')
    page.locator('#profile-grade').fill('初一');page.locator('#profile-form button[type="submit"]').click()
    page.goto(BASE+'#settings')
    page.locator('#settings-form button[type="submit"]').click()
    assert saved()['settings']['grade']=='初一'
    page.goto(BASE+'#home');header('旧记录用户')
    page.screenshot(path='/tmp/profile-v26-home.png')
    profile();page.screenshot(path='/tmp/profile-v26-form.png')
    assert not errors,errors
    print('PASS: renamed brand, required name/grade, header and cross-tab updates, reload, real backup/import and legacy grade compatibility; learning/settings preserved',flush=True)
    context.close();browser.close()
print('COMPLETE: personal profile passed',flush=True)
