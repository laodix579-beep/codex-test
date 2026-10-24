"""Visible return navigation and one-shot solved-card speech on desktop and phone.

Run against localhost by default, or pass the deployed HTTPS base URL as argv[1].
"""
import os
import sys
from playwright.sync_api import sync_playwright

BASE=(sys.argv[1] if len(sys.argv)>1 else 'http://127.0.0.1:8000/').rstrip('/')+'/'
with sync_playwright() as p:
    launch=dict(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox'])
    proxy=os.environ.get('HTTPS_PROXY') or os.environ.get('https_proxy')
    if BASE.startswith('https:') and proxy:
        launch['proxy']={'server':proxy}
    browser=p.chromium.launch(**launch)
    for mobile in (False,True):
        context=browser.new_context(viewport={'width':390 if mobile else 1440,'height':844 if mobile else 1000},is_mobile=mobile,has_touch=mobile,user_agent='Mozilla/5.0 (iPhone; CPU iPhone OS 18_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.0 Mobile/15E148 Safari/604.1' if mobile else None)
        context.add_init_script('''{
          window.speechStarts=[];
          const original=HTMLMediaElement.prototype.play;
          HTMLMediaElement.prototype.play=function(...args){
            window.speechStarts.push(this.dataset.sourceText);
            return original.apply(this,args);
          };
        }''')
        page=context.new_page();errors=[]
        page.on('pageerror',lambda error:errors.append(str(error)))
        page.goto(BASE+'#words',wait_until='networkidle',timeout=120000)
        page.locator('.page-back').click()
        page.wait_for_url('**/#home')
        assert page.locator('.page-back').is_hidden()
        page.goto(BASE+'#words')
        page.locator('.vocab-category-heading[data-category-id="C01"]').click()
        category=page.locator('#word-category-dialog')
        assert category.locator('.dialog-back').is_visible()
        category.locator('.dialog-back').click()
        assert category.is_hidden() and page.url.endswith('#words')
        page.goto(BASE+'#words/all')
        page.locator('[data-action="add-word"]').click()
        page.locator('#word-dialog .dialog-back').click()
        assert page.locator('#word-dialog').is_hidden()
        page.goto(BASE+'#notes')
        page.locator('[data-action="new-note"]').first.click()
        page.locator('#note-title').fill('Unsubmitted return test')
        page.locator('#note-dialog .dialog-back').click()
        assert page.locator('#note-dialog').is_hidden()
        assert page.locator('.note-card').count()==0
        page.goto(BASE+'#settings')
        page.locator('#content [data-action="import"]').click()
        page.locator('#import-dialog .dialog-back').click()
        assert page.locator('#import-dialog').is_hidden()
        before=page.evaluate('localStorage.getItem(document.body.dataset.storageKey)')
        page.locator('[data-action="reset"]').click()
        page.locator('#confirm-dialog .dialog-back').click()
        assert page.locator('#confirm-dialog').is_hidden()
        assert page.evaluate('localStorage.getItem(document.body.dataset.storageKey)')==before
        page.goto(BASE+'#words/C01/C01-S01')
        page.locator('.translation-blank').first.wait_for()
        page.wait_for_function('document.querySelector("#question-audio").dataset.sourceText==="Hello, Anna."')
        assert page.locator('.practice-back').is_visible()
        assert page.locator('.practice-back').inner_text()=='返回'
        page.evaluate('speechStarts=[]')
        page.locator('.translation-blank').first.fill('hello')
        submit='.mobile-controls [data-action="translation-submit"]' if mobile else '#translation-submit'
        page.locator(submit).click()
        page.wait_for_function('document.querySelector("#question-audio").dataset.sourceText==="hello"&&document.querySelector("#question-audio").currentTime>0')
        assert page.evaluate('speechStarts')==['hello']
        # Changing result visibility re-renders without starting another playback.
        page.locator('.mobile-controls [data-action="translation-answer"]' if mobile else '.translation-shortcuts [data-action="translation-answer"]').click()
        assert page.evaluate('speechStarts')==['hello']
        page.locator('.grammar-card').click()
        page.wait_for_function('speechStarts.length===2')
        assert page.evaluate('speechStarts')==['hello','hello']
        page.locator('.mobile-controls [data-action="next-item"]' if mobile else '.translation-shortcuts [data-action="next-item"]').last.click()
        page.wait_for_function('document.querySelector("#question-audio").dataset.sourceText!=="hello"')
        page.locator('.mobile-controls [data-action="previous-item"]' if mobile else '.translation-shortcuts [data-action="previous-item"]').click()
        page.wait_for_function('document.querySelector("#question-audio").dataset.sourceText==="hello"&&document.querySelector("#question-audio").currentTime>0')
        assert page.evaluate('speechStarts.filter(t=>t==="hello").length')==3
        page.locator('.mobile-controls [data-action="next-item"]' if mobile else '.translation-shortcuts [data-action="next-item"]').last.click()
        page.locator('.translation-blank').first.wait_for()
        page.evaluate('speechStarts=[]')
        page.locator('.mobile-controls [data-action="translation-mastered"]' if mobile else '.translation-shortcuts [data-action="translation-mastered"]').click()
        page.wait_for_function('document.querySelector("#question-audio").dataset.sourceText==="hi"&&document.querySelector("#question-audio").currentTime>0')
        assert page.evaluate('speechStarts')==['hi']
        page.locator('.practice-back').click()
        page.wait_for_function('!document.querySelector("#lesson-dialog").open')
        assert page.locator('#question-audio').evaluate('(audio)=>audio.paused&&!audio.hasAttribute("src")')
        assert page.url.endswith('#words')
        page.goto(BASE+'#words/all')
        phrase_id=page.evaluate('FROG_WORD_CATALOG.words.find(w=>w.word==="good afternoon").id')
        page.locator(f'[data-action="learn-word"][data-id="{phrase_id}"]').click()
        fields=page.locator('.translation-blank');fields.first.wait_for()
        assert fields.count()==2
        for field,answer in zip(fields.all(),['good','afternoon']):field.fill(answer)
        page.evaluate('speechStarts=[]')
        page.locator(submit).click()
        page.wait_for_function('document.querySelector("#question-audio").dataset.sourceText==="good afternoon"&&document.querySelector("#question-audio").currentTime>0')
        assert page.evaluate('speechStarts')==['good afternoon']
        assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
        assert not errors,errors
        print(f'PASS {"phone" if mobile else "desktop"}: return controls, canceled forms, single automatic solved-word playback, manual replay, revisit and media cleanup',flush=True)
        context.close()
    browser.close()
print('COMPLETE: navigation and result audio passed',flush=True)
