"""Sentence once, target word twice; replay and navigation must cancel old drills."""
import os
import sys
from playwright.sync_api import sync_playwright

BASE=(sys.argv[1] if len(sys.argv)>1 else 'http://127.0.0.1:8000/').rstrip('/')+'/'
with sync_playwright() as p:
    launch=dict(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox'])
    proxy=os.environ.get('HTTPS_PROXY') or os.environ.get('https_proxy')
    if BASE.startswith('https:') and proxy:launch['proxy']={'server':proxy}
    browser=p.chromium.launch(**launch)
    for mobile in (False,True):
        context=browser.new_context(viewport={'width':390 if mobile else 1440,'height':844 if mobile else 1000},is_mobile=mobile,has_touch=mobile,user_agent='Mozilla/5.0 (Linux; Android 11) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.198 Mobile Safari/537.36 MicroMessenger/8.0.32' if mobile else None)
        context.add_init_script('''{
          delete window.structuredClone;delete Object.hasOwn;delete Array.prototype.at;
          window.playedClips=[];
          document.addEventListener('playing',event=>{
            if(event.target.id==='question-audio')playedClips.push(event.target.dataset.sourceText);
          },true);
        }''')
        page=context.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
        page.goto(BASE+'#words',wait_until='networkidle',timeout=120000)
        page.locator('.vocab-category-heading[data-category-id="C01"]' if mobile else '.mvp-category-card[data-category-id="C01"]').click()
        page.locator('#word-category-dialog button[data-subcategory-id="C01-S03"]' if mobile else '.mvp-subcategory[data-subcategory-id="C01-S03"]').click()
        page.locator('.translation-blank').first.wait_for()
        red=page.evaluate('FROG_WORD_CATALOG.words.find(w=>w.word==="red")')
        expected=[red['example'],'red','red']
        assert page.locator('.word-spelling-hint').count()==0
        assert page.locator('.word-context-meaning').inner_text()=='词义：'+red['meaning']
        assert page.locator('.word-context-meaning').evaluate('(el)=>el.previousElementSibling.matches(".word-example-prompt")&&(el.nextElementSibling.id==="translation-form"||el.nextElementSibling.matches(".translation-slots"))')
        meaning=page.locator('.word-context-meaning').bounding_box();slots=page.locator('.translation-slots').bounding_box()
        assert meaning['y']+meaning['height']<=slots['y']
        page.wait_for_function('playedClips.length>=3&&document.querySelector("#question-audio").ended',timeout=30000)
        assert page.evaluate('playedClips')==expected
        replay='.mobile-controls [data-action="speak-lesson"]' if mobile else '#translation-form [data-action="speak-lesson"]'
        page.evaluate('playedClips=[]');page.locator(replay).click()
        page.wait_for_function('playedClips.length>=3&&document.querySelector("#question-audio").ended',timeout=30000)
        assert page.evaluate('playedClips')==expected
        if not mobile:
            # The native player's play control also restarts the complete drill.
            page.evaluate('playedClips=[]');page.locator('#question-audio').click(position={'x':20,'y':16})
            page.wait_for_function('playedClips.length>=3&&document.querySelector("#question-audio").ended',timeout=30000)
            assert page.evaluate('playedClips')==expected
        # Switch questions while the sentence is playing; its pending word repeats
        # must not run after the new question starts.
        page.evaluate('playedClips=[]');page.locator(replay).click()
        page.wait_for_function('playedClips.length===1')
        page.evaluate('playedClips=[]')
        page.locator('.mobile-controls [data-action="next-item"]' if mobile else '.translation-shortcuts [data-action="next-item"]').last.click()
        next_word=page.locator('#practice-jump option:checked').text_content().split('. ',1)[1]
        blue=page.evaluate('(word)=>FROG_WORD_CATALOG.words.find(w=>w.word===word)',next_word)
        page.wait_for_function('playedClips.length>=3&&document.querySelector("#question-audio").ended',timeout=30000)
        assert page.evaluate('playedClips')==[blue['example'],blue['word'],blue['word']]
        # Close during the pause between sentence and words.
        page.evaluate('playedClips=[]');page.locator(replay).click()
        page.wait_for_function('playedClips.length===1&&document.querySelector("#question-audio").ended',timeout=15000)
        page.locator('.practice-back').click()
        page.wait_for_timeout(1000)
        assert page.evaluate('playedClips')==[blue['example']]
        assert page.locator('#question-audio').evaluate('(a)=>a.paused&&!a.hasAttribute("src")')
        assert not errors,errors
        assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
        print(f'PASS {"phone" if mobile else "desktop"}: meaning above blanks, no instruction line, exact sentence→word→word playback, replay, question switch and exit cancellation',flush=True)
        context.close()
    browser.close()
print('COMPLETE: sentence and word audio drills passed',flush=True)
