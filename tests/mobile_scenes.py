"""Scene changes, phone keyboard, picture switch and offline warehouse practice."""
from playwright.sync_api import sync_playwright,expect

BASE='http://127.0.0.1:8000/'
with sync_playwright() as p:
    browser=p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox'])
    context=browser.new_context(viewport={'width':390,'height':844},is_mobile=True,has_touch=True)
    context.add_init_script("Object.defineProperty(window,'speechSynthesis',{get(){throw new Error('TTS forbidden')}})")
    page=context.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
    page.goto(BASE+'#words/C01/C01-S01')
    page.locator('.translation-blank').first.wait_for()
    page.wait_for_function('document.querySelector(".translation-picture img")?.naturalWidth>0')
    expect(page.locator('.translation-picture')).to_have_attribute('data-scene-id','C01-S01-001')
    page.locator('.mobile-controls [data-action="next-item"]').click()
    expect(page.locator('.translation-picture')).to_have_attribute('data-scene-id','C01-S01-002')
    for width,height in [(320,568),(390,844),(428,926),(760,390)]:
        page.set_viewport_size({'width':width,'height':height})
        page.evaluate('()=>new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve)))')
        assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
        buttons=page.locator('.mobile-controls button').evaluate_all('buttons=>buttons.map(b=>b.getBoundingClientRect().toJSON())')
        assert len(buttons)==7
        assert all(b['left']>=0 and b['right']<=width+1 and b['bottom']<=height+1 for b in buttons),(width,height,buttons)
    page.set_viewport_size({'width':390,'height':844})
    page.locator('.translation-blank').first.focus()
    page.evaluate("Object.defineProperty(visualViewport,'height',{value:420,configurable:true});visualViewport.dispatchEvent(new Event('resize'))")
    expect(page.locator('.translation-picture')).to_be_hidden()
    page.evaluate("delete visualViewport.height;visualViewport.dispatchEvent(new Event('resize'))")
    expect(page.locator('.translation-picture')).to_be_visible()
    page.locator('.practice-back').click();page.wait_for_function('!document.querySelector("#lesson-dialog").open')
    page.goto(BASE+'#settings')
    page.wait_for_function('document.querySelector("[data-mobile-status]").textContent.startsWith("已保存离线内容")',timeout=120000)
    context.set_offline(True)
    for sub,scene in [('C01-S01','C01-S01-001'),('C01-S02','C01-S02-001'),('C01-S03','C01-S03-001'),('C01-S04','C01-S04-001')]:
        page.goto(BASE+'#words/C01/'+sub)
        page.locator('.translation-blank').first.wait_for()
        page.wait_for_function('document.querySelector(".translation-picture img")?.naturalWidth>0')
        expect(page.locator('.translation-picture')).to_have_attribute('data-scene-id',scene)
        if sub=='C01-S03':
            page.locator('.translation-blank').first.fill('red')
            page.locator('.mobile-controls [data-action="translation-submit"]').click()
            page.wait_for_function('document.querySelector("#question-audio").dataset.sourceText==="red"&&document.querySelector("#question-audio").currentTime>0')
            assert page.evaluate('JSON.parse(localStorage.getItem(document.body.dataset.storageKey)).wordStatus["C01-S03-001"]')=='mastered'
        page.locator('.practice-back').click();page.wait_for_function('!document.querySelector("#lesson-dialog").open')
    assert not errors,errors
    print('PASS: phone scene changes, four screen sizes, keyboard hiding, all four groups offline, grading and original MP3',flush=True)
    context.close();browser.close()
print('COMPLETE: phone cartoon scenes passed',flush=True)
