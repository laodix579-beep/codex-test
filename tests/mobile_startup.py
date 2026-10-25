"""Exercise startup and saved records with APIs absent from older mobile WebViews.

Optionally pass the deployed HTTPS URL as the first argument.
"""
import os
import sys
from playwright.sync_api import sync_playwright

BASE=(sys.argv[1] if len(sys.argv)>1 else 'http://127.0.0.1:8000/').rstrip('/')+'/'
LEGACY='delete window.structuredClone;delete Object.hasOwn;delete Array.prototype.at;'
AGENTS={
 'Android WeChat': 'Mozilla/5.0 (Linux; Android 11; Mobile) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/86.0.4240.198 Mobile Safari/537.36 MicroMessenger/8.0.32',
 'iPhone WeChat': 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_8 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 MicroMessenger/8.0.32',
}
with sync_playwright() as p:
    launch=dict(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox'])
    proxy=os.environ.get('HTTPS_PROXY') or os.environ.get('https_proxy')
    if BASE.startswith('https:') and proxy:launch['proxy']={'server':proxy}
    browser=p.chromium.launch(**launch)
    for name,agent in AGENTS.items():
        context=browser.new_context(viewport={'width':390,'height':844},is_mobile=True,has_touch=True,user_agent=agent)
        context.add_init_script(LEGACY)
        page=context.new_page();errors=[]
        page.on('pageerror',lambda error:errors.append(str(error)))
        page.goto(BASE,wait_until='networkidle',timeout=120000)
        assert page.locator('#content').get_attribute('data-app-ready')=='true'
        assert page.locator('#content h1').is_visible()
        assert page.locator('[data-startup-loading]').count()==0
        page.goto(BASE+'#notes')
        page.locator('[data-action="new-note"]').first.click()
        page.locator('#note-title').fill('手机保留记录')
        page.locator('#note-body').fill('兼容模式下保存，并在刷新后保留。')
        page.locator('#note-form button[type="submit"]').click()
        page.locator('.note-card').first.wait_for()
        page.reload(wait_until='networkidle')
        assert '手机保留记录' in page.locator('.note-card').inner_text()
        page.goto(BASE+'#words')
        assert page.locator('.vocab-category').count()==1
        page.locator('.vocab-category-heading[data-category-id="C01"]').click()
        page.locator('#word-category-dialog button[data-subcategory-id="C01-S01"]').click()
        page.locator('.translation-blank').first.fill('hello')
        page.locator('.mobile-controls [data-action="translation-submit"]').click()
        page.wait_for_function('document.querySelector("#question-audio").dataset.sourceText==="hello"&&document.querySelector("#question-audio").currentTime>0')
        assert page.locator('.grammar-card strong').inner_text()=='hello'
        page.locator('.practice-back').click()
        page.wait_for_function('!document.querySelector("#lesson-dialog").open')
        page.reload(wait_until='networkidle')
        saved=page.evaluate('JSON.parse(localStorage.getItem(document.body.dataset.storageKey))')
        assert saved['wordStatus']['C01-S01-001']=='mastered'
        assert saved['notes'][0]['title']=='手机保留记录'
        assert page.locator('#content').get_attribute('data-app-ready')=='true'
        assert not errors,errors
        assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
        page.screenshot(path=f'/tmp/frog-startup-{name.split()[0].lower()}.png')
        print(f'PASS {name} profile without modern APIs: home, notes, reload, category dialog, spelling, audio and preserved progress',flush=True)
        context.close()
    # A storage denial must still render a usable page without overwriting data.
    context=browser.new_context(viewport={'width':390,'height':844})
    context.add_init_script(LEGACY+'''Object.defineProperty(window,'localStorage',{get:function(){throw new DOMException('Storage blocked','SecurityError');}});''')
    page=context.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
    page.goto(BASE,timeout=120000)
    assert page.locator('#content h1').is_visible()
    assert '浏览器存储暂不可用' in page.locator('#content').inner_text()
    assert not errors,errors
    context.close()
    # Even a failure before application initialization must not leave a blank body.
    context=browser.new_context()
    context.add_init_script('''Object.defineProperty(window,'FROG_WORD_CATALOG',{get:function(){throw new Error('Forced startup failure');},set:function(){},configurable:true});''')
    page=context.new_page();page.goto(BASE,timeout=120000)
    assert page.locator('[data-startup-error]').is_visible()
    assert page.locator('[data-startup-error] button').inner_text()=='重新加载'
    context.close();browser.close()
print('COMPLETE: older mobile startup, storage denial and visible failure fallback passed',flush=True)
