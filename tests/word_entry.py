"""Theme dialogs, category practice, full-group counts and default pictures."""
from playwright.sync_api import sync_playwright
BASE='http://127.0.0.1:8000/'
with sync_playwright() as p:
 browser=p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox'])
 for mobile in [False,True]:
  context=browser.new_context(viewport={'width':390 if mobile else 1440,'height':844 if mobile else 1000},is_mobile=mobile,has_touch=mobile)
  page=context.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
  page.goto(BASE+'#words')
  for i in range(1,2):
   page.locator(f'.vocab-category-heading[data-category-id="C{i:02}"]').click()
   assert page.locator('#word-category-dialog').is_visible()
   assert page.locator('#word-category-dialog .word-category-choices button').count()==4
   assert not page.locator('#lesson-dialog').evaluate('d=>d.open')
   page.keyboard.press('Escape')
  page.locator('.vocab-category-heading[data-category-id="C01"]').click()
  assert '22 个词条' in page.locator('#word-category-dialog button[data-subcategory-id="C01-S01"]').inner_text()
  page.locator('#word-category-dialog button[data-subcategory-id="C01-S01"]').click()
  assert not page.locator('#word-category-dialog').is_visible()
  page.locator('.translation-blank').first.wait_for()
  assert '1 / 22' in page.locator('.lesson-progress').inner_text()
  assert page.locator('#practice-jump option').count()==22
  assert page.locator('#content .word-card').count()==0
  assert page.locator('[data-session-setting="showPicture"]').first.is_checked()
  page.wait_for_function('document.querySelector(".translation-picture img")?.naturalWidth>0')
  page.locator('#lesson-dialog [data-close]').click()
  page.wait_for_function('!document.querySelector("#lesson-dialog").open')
  assert page.url.endswith('#words') and page.locator('.vocab-category').count()==1
  page.locator('.vocab-subcategories [data-route="words/C01/C01-S01"]').click()
  page.locator('.translation-blank').first.wait_for()
  assert '1 / 22' in page.locator('.lesson-progress').inner_text()
  options=page.locator('#practice-jump option').all_text_contents()
  assert len(options)==22 and options[0]=='1. hello' and options[-1]=='22. welcome'
  page.locator('[data-session-setting="showPicture"]').first.uncheck()
  assert page.locator('.translation-picture').count()==0
  page.locator('#lesson-dialog [data-close]').click()
  page.goto(BASE+'#words/C01/C01-S01')
  page.locator('.translation-blank').first.wait_for()
  assert '1 / 22' in page.locator('.lesson-progress').inner_text()
  assert page.locator('[data-session-setting="showPicture"]').first.is_checked()
  assert page.locator('.translation-picture').count()==1
  page.locator('#lesson-dialog [data-close]').click()
  page.goto(BASE+'#words/C02/C02-S01')
  page.wait_for_url('**/#words')
  assert page.locator('.vocab-category').count()==1
  assert not page.locator('#lesson-dialog').evaluate('d=>d.open')
  page.goto(BASE+'#words/all')
  page.locator('.word-card').first.wait_for()
  assert page.locator('.word-card').count()==136
  assert not errors,errors
  print(f'PASS: {"phone" if mobile else "desktop"} populated theme dialog, greeting=22, no list detour, picture defaults on, empty old routes redirect and management works',flush=True)
  context.close()
 browser.close()
print('COMPLETE: direct word entry checks passed',flush=True)
