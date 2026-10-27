"""All populated entrances: balanced choices, direct groups, edits and resume."""
import json
from pathlib import Path
from playwright.sync_api import sync_playwright

BASE='http://127.0.0.1:8000/'
catalog=json.loads(Path('data/practice-groups.json').read_text())
with sync_playwright() as p:
    browser=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
    context=browser.new_context(viewport={'width':1625,'height':900},service_workers='block')
    context.add_init_script("Object.defineProperty(window,'speechSynthesis',{get(){throw new Error('Runtime TTS forbidden')}})")
    page=context.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
    def stored():return page.evaluate('JSON.parse(localStorage.getItem(document.body.dataset.storageKey))')
    def closed():
        page.locator('.practice-back').click();page.wait_for_function('!document.querySelector("#lesson-dialog").open')
    def enter(sub):
        page.goto(BASE+'#words/'+sub.split('-')[0]);page.locator(f'.mvp-subcategory[data-subcategory-id="{sub}"]').click()
    def choose(sub):
        enter(sub);page.locator('#practice-group-dialog').wait_for(state='visible')
    page.goto(BASE+'#home');initial=stored()
    for dismiss in ('button','Escape','backdrop'):
        choose('C01-S04');dialog=page.locator('#practice-group-dialog');box=dialog.bounding_box()
        assert dialog.evaluate('e=>e.matches(":modal")')
        assert abs(box['x']+box['width']/2-812.5)<2 and abs(box['y']+box['height']/2-450)<2
        assert dialog.locator('.practice-group-all b').inner_text()=='33'
        assert dialog.locator('[data-practice-group="shapes"] b').inner_text()=='16'
        assert dialog.locator('[data-practice-group="size"] b').inner_text()=='17'
        assert not page.locator('#lesson-dialog').evaluate('e=>e.open')
        if dismiss=='button':dialog.locator('[data-close]').click()
        elif dismiss=='Escape':page.keyboard.press('Escape')
        else:page.mouse.click(10,10)
        assert not dialog.evaluate('e=>e.open')
        assert stored().get('practiceResume')==initial.get('practiceResume') and stored()['wordStatus']==initial['wordStatus']
    print('PASS: centered selection, exact counts and cancellation without changing progress',flush=True)
    for section in catalog['subcategories']:
        sub=section['subcategoryId'];rows=[w for w in initial['words'] if w['subcategoryId']==sub]
        assert sum(len(g['wordIds']) for g in section['groups'])==len(rows)
        assert all(10<=len(g['wordIds'])<=25 for g in section['groups'])
        if len(section['groups'])==1:
            enter(sub);page.locator('.translation-blank').first.wait_for()
            assert page.evaluate("!document.querySelector('#practice-group-dialog')?.open")
            assert page.locator('#practice-jump option').count()==len(rows)
            assert stored()['practiceResume']['ids']==[w['id'] for w in rows]
            closed()
        else:
            for group in [{'id':'all','wordIds':[w['id'] for w in rows]},*section['groups']]:
                choose(sub);button=page.locator(f'#practice-group-dialog [data-practice-group="{group["id"]}"]')
                expected=[w for w in rows if w['id'] in group['wordIds']]
                assert int(button.locator('b').inner_text())==len(expected)
                button.click();page.locator('.translation-blank').first.wait_for()
                assert page.locator('#practice-jump option').all_text_contents()==[f'{i+1}. {w["word"]}' for i,w in enumerate(expected)]
                assert stored()['practiceResume']['ids']==[w['id'] for w in expected]
                assert page.locator('.translation-picture').get_attribute('data-scene-id')==expected[0]['id']
                closed()
        print('PASS: whole group and all balanced sections in '+sub,flush=True)
    assert stored()['wordStatus']==initial['wordStatus'] and stored()['words']==initial['words']
    choose('C01-S02');page.locator('[data-practice-group="numbers-basic"]').click()
    page.wait_for_function('document.querySelector("#question-audio").currentTime>0')
    assert page.locator('.translation-picture').get_attribute('data-scene-id')=='C01-S02-001'
    page.locator('#translation-form [data-action="translation-answer"]').click()
    assert page.locator('#practice-answer-dialog .mvp-answer-line>span:not(.mvp-dj)').inner_text()=='/ˈzɪərəʊ/'
    assert stored()['wordStatus']==initial['wordStatus']
    page.locator('#practice-answer-dialog [data-answer-close]').click()
    page.locator('.translation-blank').first.fill('zero');page.locator('#translation-submit').click()
    assert stored()['wordStatus']['C01-S02-001']=='mastered'
    page.locator('.mvp-solved-actions [data-action="next-item"]').click()
    assert '2/21' in page.locator('#lesson-course').inner_text()
    closed();page.goto(BASE+'#home');page.reload()
    assert '第 2 / 21 词' in page.locator('.mvp-resume-title').inner_text()
    page.locator('.home-resume-card [data-action="resume-desktop"]').click()
    assert page.locator('.translation-picture').get_attribute('data-scene-id')=='C01-S02-002'
    closed()
    for sub,count in [('C01-S01',22),('C01-S03',19)]:
        enter(sub);page.locator('.translation-blank').first.wait_for()
        assert page.locator('#practice-jump option').count()==count
        assert page.evaluate("!document.querySelector('#practice-group-dialog')?.open")
        closed()
    page.goto(BASE+'#words/C08');page.locator('.mvp-subcategory').first.click()
    page.get_by_role('heading',name='这个分类正在准备中').wait_for()
    assert not page.locator('#lesson-dialog').evaluate('e=>e.open')
    print('PASS: media, read-only answer, grading, subset resume, direct greetings/colors and empty entrances',flush=True)
    page.goto(BASE+'#words/C01')
    page.evaluate('''()=>{const k=document.body.dataset.storageKey,s=JSON.parse(localStorage.getItem(k));
      s.words=s.words.filter(w=>!['C01-S04-001','C01-S04-017'].includes(w.id));
      s.words.push({...s.words.find(w=>w.id==='C01-S04-002'),id:'custom-shape',word:'custom geometry',meaning:'用户自己的形状',ipa:'/自定义/',notes:'保留笔记'});
      s.settings.userName='原学习者';s.notes=[{id:'keep-note',title:'原笔记',body:'不改动',createdAt:'2026-10-01T00:00:00Z',updatedAt:'2026-10-01T00:00:00Z'}];
      s.favorites=['C01-S02-001','custom-shape'];s.days['2020-01-01']={seconds:1234,words:['C01-S02-001'],sentences:[],mistakes:1,checked:true};localStorage.setItem(k,JSON.stringify(s));}''')
    page.reload();before=stored();choose('C01-S04')
    assert page.locator('.practice-group-all b').inner_text()=='32'
    for key,count in [('shapes',15),('size',16),('other',1)]:assert page.locator(f'#practice-group-dialog [data-practice-group="{key}"] b').inner_text()==str(count)
    page.locator('[data-practice-group="other"]').click();page.locator('.translation-blank').first.wait_for()
    assert stored()['practiceResume']['ids']==['custom-shape'];closed()
    for key in ['words','wordStatus','notes','favorites','settings','plan']:assert stored()[key]==before[key],key
    assert stored()['days']['2020-01-01']==before['days']['2020-01-01']
    page.evaluate('''()=>{const k=document.body.dataset.storageKey,s=JSON.parse(localStorage.getItem(k)),keep=new Set(FROG_PRACTICE_GROUPS.subcategories.find(g=>g.subcategoryId==='C01-S04').groups[0].wordIds);s.words=s.words.filter(w=>w.subcategoryId!=='C01-S04'||keep.has(w.id));localStorage.setItem(k,JSON.stringify(s));}''')
    page.reload();enter('C01-S04');page.locator('.translation-blank').first.wait_for()
    assert page.locator('#practice-jump option').count()==15
    assert page.evaluate("!document.querySelector('#practice-group-dialog')?.open");closed()
    assert not errors,errors
    print('PASS: dynamic deletion/custom words, remaining single-group direct entry and unchanged learner records',flush=True)
    context.close()
    context=browser.new_context(viewport={'width':1440,'height':960},service_workers='block')
    page=context.new_page();page.goto(BASE+'#home');choose('C01-S04');page.set_viewport_size({'width':980,'height':800})
    page.wait_for_function('document.body.classList.contains("mobile-mvp")')
    assert not page.locator('#lesson-dialog').evaluate('e=>e.open') and page.evaluate("!document.querySelector('#practice-group-dialog')?.open")
    context.close()
    context=browser.new_context(viewport={'width':390,'height':844},is_mobile=True,has_touch=True,service_workers='block')
    page=context.new_page();page.goto(BASE+'#words/C01');page.locator('.mvp-subcategory[data-subcategory-id="C01-S01"]').click()
    page.locator('.translation-blank').first.wait_for();assert page.locator('#practice-jump option').count()==22
    assert page.locator('#practice-group-dialog').count()==0 and page.evaluate('document.documentElement.scrollWidth<=innerWidth')
    context.close();browser.close()
print('COMPLETE: all populated practice choices/direct entrances and responsive phone behavior passed',flush=True)
