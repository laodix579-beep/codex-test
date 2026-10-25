"""Only existing warehouse words are exposed; historical data remains recoverable."""
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from playwright.sync_api import sync_playwright
BASE='http://127.0.0.1:8000/'
results=[]
with sync_playwright() as p:
 browser=p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox'])
 for mobile in (False,True):
  context=browser.new_context(viewport={'width':390 if mobile else 1440,'height':844 if mobile else 1000},is_mobile=mobile,has_touch=mobile,user_agent='Mozilla/5.0 (Linux; Android 11) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.198 Mobile Safari/537.36 MicroMessenger/8.0.32' if mobile else None)
  context.add_init_script("delete window.structuredClone;delete Object.hasOwn;delete Array.prototype.at;Object.defineProperty(window,'speechSynthesis',{get(){throw new Error('TTS forbidden')}});Object.defineProperty(window,'SpeechSynthesisUtterance',{get(){throw new Error('TTS forbidden')}})")
  page=context.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
  page.goto(BASE+'#words',wait_until='networkidle');page.reload(wait_until='networkidle')
  stored=lambda:page.evaluate('JSON.parse(localStorage.getItem(document.body.dataset.storageKey))')
  initial=stored();ids=[w['id'] for w in initial['words']]
  assert len(ids)==136 and initial['courses']==[]
  assert page.locator('#navigation [data-route="courses"],#navigation [data-route="textbooks"],#navigation [data-route="phonetics"]').count()==0
  assert page.locator('.vocab-category').count()==1
  assert page.locator('.vocab-category h3').inner_text()=='基础入门'
  assert page.locator('.vocab-subcategories button').count()==4
  assert [int(t.split()[0]) for t in page.locator('.vocab-subcategories small').all_text_contents()]==[22,62,19,33]
  assert '1 个主题 · 4 个分类' in page.locator('.vocab-summary p').inner_text()
  assert page.locator('[data-route="phonetics"]').count()==0
  assert '待添加' not in page.locator('#content').inner_text()
  for route in ['courses','textbooks','phonetics','course/old','review/sentence/wrong','words/C02','words/manage/C02']:
   page.goto(BASE+'#'+route)
   page.wait_for_url('**/#words');assert page.locator('.vocab-category').count()==1
  # Prior courses remain in the storage and backup, never as active material.
  page.evaluate('''()=>{
   const key=document.body.dataset.storageKey,s=JSON.parse(localStorage.getItem(key));
   s.courses=[{id:'old-course',title:'ARCHIVED OUTSIDE COURSE',description:'out-of-warehouse fixture',category:'daily',level:'A1',color:'purple',createdAt:'2026-10-01T00:00:00.000Z',sample:true,sentences:[{id:'old-sentence',english:'Archived outside vocabulary.',chinese:'历史课程句子。'}]}];
   s.sentenceStatus['old-sentence']='mastered';s.wordStatus['C01-S01-001']='mastered';
   s.favorites=['old-sentence','C01-S01-001'];s.courseFavorites=['old-course'];s.plan.courseIds=['old-course'];
   s.notes=[{id:'old-note',title:'保留笔记',body:'既有记录',createdAt:'2026-10-01T00:00:00.000Z',updatedAt:'2026-10-01T00:00:00.000Z'}];
   s.days['2026-10-01']={seconds:1500,sentences:['old-sentence'],words:['C01-S01-001'],mistakes:1,checked:true};
   s.words.push({...s.words[0],id:'user-existing',word:'customword',meaning:'用户已有词',categoryId:'C08',subcategoryId:'C08-S01'});
   localStorage.setItem(key,JSON.stringify(s));
  }''')
  page.reload(wait_until='networkidle');baseline=stored()
  assert baseline['courses'][0]['title']=='ARCHIVED OUTSIDE COURSE'
  assert page.locator('.vocab-category').count()==2
  assert page.locator('.vocab-subcategories button').count()==5
  for route in ['home','plan','favorites','words','search/ARCHIVED','review/sentence/mastered','courses','textbooks','phonetics']:
   page.goto(BASE+'#'+route)
   assert 'ARCHIVED OUTSIDE COURSE' not in page.locator('#content').inner_text()
   assert 'Archived outside vocabulary.' not in page.locator('#content').inner_text()
   assert page.locator('#content .course-card').count()==0
  for term in ['apple','book','hello','customword','ARCHIVED']:
   page.locator('#global-search').fill(term);page.locator('#global-search').press('Enter')
   page.wait_for_function('(q)=>location.hash==="#search/"+encodeURIComponent(q)',arg=term)
   found=page.locator('.search-results [data-action="learn-word"]').evaluate_all('(rows)=>rows.map(r=>r.dataset.id)')
   assert set(found).issubset({w['id'] for w in baseline['words']})
   assert page.locator('.word-card[data-word="apple"],.word-card[data-word="book"]').count()==0
   if term=='customword':assert page.locator('.word-card[data-word="customword"]').is_visible()
   if term=='ARCHIVED':assert page.get_by_role('heading',name='没有找到相关内容').is_visible()
  page.locator('#clear-global-search').click()
  page.goto(BASE+'#favorites');assert page.locator('.word-title').all_text_contents()==['hello']
  page.goto(BASE+'#settings')
  assert page.locator('#content [data-action="import"]').count()==0
  page.wait_for_function('document.querySelector("[data-mobile-status]").textContent.startsWith("已保存离线内容")',timeout=90000)
  for key in ['words','courses','wordStatus','sentenceStatus','favorites','courseFavorites','notes','plan','settings','days']:
   assert stored()[key]==baseline[key],key
  with TemporaryDirectory() as tmp:
   with page.expect_download() as dl:page.locator('#content [data-action="backup"]').click()
   path=Path(tmp)/'backup.json';dl.value.save_as(path);backup=json.loads(path.read_text())
   assert backup['courses']==baseline['courses'] and backup['sentenceStatus']==baseline['sentenceStatus']
  if not mobile:
   # Saving a personal copy must not automatically re-add the textbook.
   page.locator('[data-action="save-app"]').click()
   page.locator('#save-app-dialog [data-action="download-app-file"]').wait_for(timeout=90000)
   assert stored()['courses']==baseline['courses']
   html=page.locator('#offline-html-source').input_value()
   assert page.evaluate('FROG_OFFLINE_CACHE') in html
   page.locator('#save-app-dialog .dialog-back').click()
  page.goto(BASE+'#words');context.set_offline(True);page.reload(wait_until='networkidle')
  assert page.locator('.vocab-category').count()==2
  assert [w['id'] for w in stored()['words'][:136]]==ids
  page.locator('.vocab-category-heading[data-category-id="C01"]').click()
  page.locator('#word-category-dialog [data-subcategory-id="C01-S01"]').click()
  page.locator('.translation-blank').first.fill('hello')
  page.locator('.mobile-controls [data-action="translation-submit"]' if mobile else '#translation-submit').click()
  page.wait_for_function('document.querySelector("#question-audio").dataset.sourceText==="hello"&&document.querySelector("#question-audio").currentTime>0')
  assert not errors,errors
  assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
  results.append({'profile':'phone' if mobile else 'desktop','builtins':136,'onlyPopulatedGroups':True,'retiredRoutesRedirect':True,'searchOnlyWarehouse':True,'historyAndBackupPreserved':True,'existingCustomWordPreserved':True,'offlineWordPractice':True})
  print('PASS',results[-1]['profile'],'warehouse-only navigation, catalog, search, old-route redirect, archive preservation, backup and offline practice',flush=True)
  context.close()
 browser.close()
Path('reports/warehouse-scope-results.json').write_text(json.dumps(results,ensure_ascii=False,indent=2)+'\n')
print('COMPLETE: warehouse-only scope passed',flush=True)
