"""Desktop category pages and existing phone dialogs offer practice sections while phone entries stay direct."""
from playwright.sync_api import sync_playwright
BASE='http://127.0.0.1:8000/'
with sync_playwright() as p:
 browser=p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox'])
 for mobile in [False,True]:
  context=browser.new_context(viewport={'width':390 if mobile else 1440,'height':844 if mobile else 1000},is_mobile=mobile,has_touch=mobile)
  page=context.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
  page.goto(BASE+'#words')
  page.locator('.vocab-category-heading[data-category-id="C01"]' if mobile else '.mvp-category-card[data-category-id="C01"]').click()
  assert not page.locator('#lesson-dialog').evaluate('d=>d.open')
  if mobile:
   assert page.locator('#word-category-dialog').is_visible()
   assert page.locator('#word-category-dialog .word-category-choices button').count()==4
   entry=page.locator('#word-category-dialog button[data-subcategory-id="C01-S01"]')
   assert '22 个词条' in entry.inner_text()
  else:
   page.locator('.mvp-subcategory').first.wait_for()
   assert page.locator('.mvp-subcategory').count()==4
   entry=page.locator('.mvp-subcategory[data-subcategory-id="C01-S01"]')
   assert '/ 22 个词条' in entry.inner_text()
  entry.click()
  if not mobile:page.locator('#practice-group-dialog [data-practice-group="all"]').click()
  page.locator('.translation-blank').first.wait_for()
  heading='.lesson-progress' if mobile else '.mvp-question-heading'
  assert '1 / 22' in page.locator(heading).inner_text()
  assert page.locator('#practice-jump option').count()==22
  assert page.locator('#content .word-card').count()==0
  assert page.locator('[data-session-setting="showPicture"]').first.is_checked()
  page.wait_for_function('document.querySelector(".translation-picture img")?.naturalWidth>0')
  page.locator('.practice-back').click()
  page.wait_for_function('!document.querySelector("#lesson-dialog").open')
  if mobile:
   assert page.url.endswith('#words') and page.locator('.vocab-category').count()==2
   page.locator('.vocab-subcategories [data-route="words/C01/C01-S01"]').click()
  else:
   assert page.url.endswith('#words/C01') and page.locator('.mvp-subcategory').count()==4
   page.locator('.mvp-subcategory[data-subcategory-id="C01-S01"]').click()
   page.locator('#practice-group-dialog [data-practice-group="all"]').click()
  page.locator('.translation-blank').first.wait_for()
  assert '1 / 22' in page.locator(heading).inner_text()
  options=page.locator('#practice-jump option').all_text_contents()
  assert len(options)==22 and options[0]=='1. hello' and options[-1]=='22. welcome'
  if not mobile:page.locator('.mvp-session-settings>summary').click()
  page.locator('[data-session-setting="showPicture"]').first.uncheck()
  assert page.locator('.translation-picture').count()==0
  page.locator('.practice-back').click()
  page.goto(BASE+'#words/C01/C01-S01');page.locator('.translation-blank').first.wait_for()
  assert '1 / 22' in page.locator(heading).inner_text()
  assert page.locator('[data-session-setting="showPicture"]').first.is_checked()
  assert page.locator('.translation-picture').count()==1
  page.locator('.practice-back').click();page.goto(BASE+'#words/C03/C03-S01')
  if mobile:page.wait_for_url('**/#words');assert page.locator('.vocab-category').count()==2
  else:page.get_by_role('heading',name='这个分类正在准备中').wait_for()
  assert not page.locator('#lesson-dialog').evaluate('d=>d.open')
  page.goto(BASE+'#words/all');page.locator('.word-card').first.wait_for()
  assert page.locator('.word-card').count()==356
  assert not errors,errors
  print(f'PASS: {"phone" if mobile else "desktop"} category entry, greeting=22, return destination, picture default, empty category and management',flush=True)
  context.close()
 browser.close()
print('COMPLETE: word entry checks passed',flush=True)
