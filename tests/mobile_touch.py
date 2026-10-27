"""GA playback and touch controls in iPhone / Android-WeChat profiles."""
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
 b=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
 for name,ua in [('iPhone',p.devices['iPhone 13']['user_agent']),('Android-WeChat','Mozilla/5.0 (Linux; Android 11; Mobile) AppleWebKit/537.36 Chrome/86.0.4240.198 Mobile Safari/537.36 MicroMessenger/8.0.32')]:
  c=b.new_context(viewport={'width':390,'height':844},is_mobile=True,has_touch=True,user_agent=ua,service_workers='block',color_scheme='dark')
  c.add_init_script("Object.defineProperty(window,'speechSynthesis',{get(){throw Error('Runtime TTS forbidden')}});delete window.structuredClone;delete Object.hasOwn;delete Array.prototype.at;")
  q=c.new_page();errors=[];q.on('pageerror',lambda e:errors.append(str(e)))
  q.goto('http://127.0.0.1:8000/#words/C01/C01-S01');q.locator('.translation-blank').first.wait_for()
  q.locator('.mobile-controls [data-action="speak-lesson"]').tap();q.wait_for_function('document.querySelector("#question-audio").currentTime>0')
  assert q.locator('#question-audio').get_attribute('src').startswith('blob:')
  q.locator('#practice-mobile-menu>summary').tap()
  assert q.locator('.phone-practice-options').evaluate('e=>getComputedStyle(e).backgroundColor')=='rgb(255, 255, 255)'
  q.locator('.phone-practice-options [data-practice-setting="rate"]').select_option('.9' if q.locator('.phone-practice-options [data-practice-setting="rate"] option[value=".9"]').count() else '0.9')
  assert q.locator('#question-audio').evaluate('a=>a.playbackRate')==.9
  q.locator('#practice-mobile-menu>summary').tap()
  q.locator('.translation-blank').first.fill('hello');q.locator('.mobile-controls [data-action="translation-submit"]').tap()
  q.wait_for_function('document.querySelector("#question-audio").dataset.audioKey==="hello"&&document.querySelector("#question-audio").currentTime>0')
  q.locator('.mobile-controls [data-action="next-item"]').last.tap()
  q.locator('.translation-blank').first.fill('h')
  q.evaluate("document.documentElement.classList.add('phone-keyboard');document.documentElement.style.setProperty('--phone-height','420px')")
  assert q.locator('.mobile-controls').evaluate('e=>e.getBoundingClientRect().bottom<=421')
  assert q.locator('.translation-blank').first.input_value()=='h'
  q.locator('.mobile-controls [data-action="translation-answer"]').tap();q.locator('.translation-answer').wait_for(state='visible')
  assert q.locator('.translation-answer .practice-target').first.evaluate('e=>getComputedStyle(e).color')=='rgb(120, 96, 255)'
  q.locator('.mobile-controls [data-action="translation-answer"]').tap()
  q.locator('.translation-blank').first.fill('hi');q.locator('.mobile-controls [data-action="translation-submit"]').tap()
  assert q.evaluate('JSON.parse(localStorage.getItem(document.body.dataset.storageKey)).wordStatus["C01-S01-002"]')=='mastered'
  assert not errors,errors
  print('PASS:',name,'GA sentence/word audio, Blob/rate, light settings and reduced-height keyboard controls with old-browser fallbacks',flush=True)
  c.close()
 b.close()
print('COMPLETE: iPhone and Android-WeChat mobile controls passed',flush=True)
