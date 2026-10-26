"""Real section choices, dynamic counts, single-section bypass and subset resume."""
import json
from pathlib import Path
from playwright.sync_api import sync_playwright

BASE='http://127.0.0.1:8000/'
catalog=json.loads(Path('data/practice-groups.json').read_text())
with sync_playwright() as p:
    browser=p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox'])
    context=browser.new_context(viewport={'width':1625,'height':900},service_workers='block')
    context.add_init_script("Object.defineProperty(window,'speechSynthesis',{get(){throw new Error('Runtime TTS forbidden')}})")
    page=context.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
    def stored():return page.evaluate('JSON.parse(localStorage.getItem(document.body.dataset.storageKey))')
    def closed():
        page.locator('.practice-back').click()
        page.wait_for_function('!document.querySelector("#lesson-dialog").open')
    def choose(sub):
        page.goto(BASE+'#words/'+sub.split('-')[0])
        page.locator(f'.mvp-subcategory[data-subcategory-id="{sub}"]').click()
        page.locator('#practice-group-dialog').wait_for(state='visible')
    page.goto(BASE+'#words/C01');initial=stored()
    # Merely inspecting or cancelling choices must not advance the saved question.
    for dismiss in ('button','Escape','backdrop'):
        choose('C01-S01')
        dialog=page.locator('#practice-group-dialog');box=dialog.bounding_box()
        assert dialog.evaluate('e=>e.matches(":modal")')
        assert abs(box['x']+box['width']/2-812.5)<2
        assert abs(box['y']+box['height']/2-450)<2
        assert dialog.locator('.practice-group-all b').inner_text()=='22'
        assert dialog.locator('[data-practice-group="greetings"] b').inner_text()=='14'
        assert dialog.locator('[data-practice-group="politeness"] b').inner_text()=='8'
        assert not page.locator('#lesson-dialog').evaluate('e=>e.open')
        if dismiss=='button':dialog.locator('[data-close]').click()
        elif dismiss=='Escape':page.keyboard.press('Escape')
        else:page.mouse.click(10,10)
        assert not dialog.evaluate('e=>e.open')
        assert stored().get('practiceResume')==initial.get('practiceResume')
        assert stored()['wordStatus']==initial['wordStatus']
    print('PASS: centered selection modal, real 22/14/8 counts and cancellation without starting/grading',flush=True)

    # Every configured section opens exactly its own ordered words; no omissions/duplicates.
    for section in catalog['subcategories']:
        sub=section['subcategoryId'];all_words=[w for w in initial['words'] if w['subcategoryId']==sub]
        assert sum(len(g['wordIds']) for g in section['groups'])==len(all_words)
        for group in [{'id':'all','wordIds':[w['id'] for w in all_words]},*section['groups']]:
            choose(sub);button=page.locator(f'#practice-group-dialog [data-practice-group="{group["id"]}"]')
            expected=[w for w in all_words if w['id'] in group['wordIds']]
            assert int(button.locator('b').inner_text())==len(expected)
            button.click();page.locator('.translation-blank').first.wait_for()
            assert page.locator('#practice-jump option').count()==len(expected)
            assert page.locator('#practice-jump option').all_text_contents()==[f'{i+1}. {w["word"]}' for i,w in enumerate(expected)]
            assert stored()['practiceResume']['ids']==[w['id'] for w in expected]
            assert page.locator('.translation-picture').get_attribute('data-scene-id')==expected[0]['id']
            closed()
        print('PASS: whole-group and every real section in '+sub,flush=True)
    assert stored()['wordStatus']==initial['wordStatus']
    assert stored()['words']==initial['words']

    # The selected section uses existing audio, answer modal, grading and saved cursor.
    choose('C01-S01');page.locator('[data-practice-group="politeness"]').click()
    page.wait_for_function('document.querySelector("#question-audio").currentTime>0')
    assert page.locator('.translation-picture').get_attribute('data-scene-id')=='C01-S01-011'
    page.locator('#translation-form [data-action="translation-answer"]').click()
    assert page.locator('#practice-answer-dialog .mvp-answer-line>span:not(.mvp-dj)').inner_text()=='/pliːz/'
    assert stored()['wordStatus']==initial['wordStatus']
    page.locator('#practice-answer-dialog [data-answer-close]').click()
    page.locator('.translation-blank').first.fill('please');page.locator('#translation-submit').click()
    assert stored()['wordStatus']['C01-S01-011']=='mastered'
    page.locator('.mvp-solved-actions [data-action="next-item"]').click()
    assert '2/8' in page.locator('#lesson-course').inner_text()
    closed();page.goto(BASE+'#home');page.reload()
    assert '第 2 / 8 词' in page.locator('.mvp-resume-title').inner_text()
    page.locator('.home-resume-card [data-action="resume-desktop"]').click()
    assert '2/8' in page.locator('#lesson-course').inner_text()
    assert page.locator('.translation-picture').get_attribute('data-scene-id')=='C01-S01-012'
    closed()
    page.goto(BASE+'#words/C01');page.locator('.mvp-subcategory[data-subcategory-id="C01-S03"]').click()
    page.locator('.translation-blank').first.wait_for()
    assert page.locator('#practice-jump option').count()==19
    assert page.evaluate("!document.querySelector('#practice-group-dialog')?.open")
    closed();page.goto(BASE+'#words/C05');page.locator('.mvp-subcategory').first.click()
    page.get_by_role('heading',name='这个分类正在准备中').wait_for()
    assert not page.locator('#lesson-dialog').evaluate('e=>e.open')
    print('PASS: DJ/MP3/scene/answer/grading, subset resume after reload, direct colors and empty category',flush=True)

    # Current user edits affect counts; custom words are never silently discarded.
    page.goto(BASE+'#words/C01')
    page.evaluate('''()=>{const k=document.body.dataset.storageKey,s=JSON.parse(localStorage.getItem(k));
      s.words=s.words.filter(w=>!['C01-S01-002','C01-S01-013'].includes(w.id));
      s.words.push({...s.words[0],id:'custom-greeting',word:'salutation',meaning:'用户自己的问候',ipa:'/用户自定义/',notes:'保留用户笔记'});
      s.settings.userName='原学习者';s.notes=[{id:'keep-group-note',title:'原笔记',body:'不改动',createdAt:'2026-10-01T00:00:00Z',updatedAt:'2026-10-01T00:00:00Z'}];
      s.favorites=['C01-S01-001','custom-greeting'];s.days['2020-01-01']={seconds:1234,words:['C01-S01-001'],sentences:[],mistakes:1,checked:true};localStorage.setItem(k,JSON.stringify(s));}''')
    page.reload();before=stored();choose('C01-S01')
    assert page.locator('.practice-group-all b').inner_text()=='21'
    for key,count in [('greetings',13),('politeness',7),('other',1)]:
        assert page.locator(f'#practice-group-dialog [data-practice-group="{key}"] b').inner_text()==str(count)
    page.locator('[data-practice-group="other"]').click();page.locator('.translation-blank').first.wait_for()
    assert stored()['practiceResume']['ids']==['custom-greeting']
    closed()
    for key in ['words','wordStatus','notes','favorites','settings','plan']:assert stored()[key]==before[key],key
    assert stored()['days']['2020-01-01']==before['days']['2020-01-01']
    page.evaluate('''()=>{const k=document.body.dataset.storageKey,s=JSON.parse(localStorage.getItem(k)),keep=new Set(FROG_PRACTICE_GROUPS.subcategories.find(g=>g.subcategoryId==='C01-S01').groups[0].wordIds);s.words=s.words.filter(w=>w.subcategoryId!=='C01-S01'||keep.has(w.id));localStorage.setItem(k,JSON.stringify(s));}''')
    page.reload();page.locator('.mvp-subcategory[data-subcategory-id="C01-S01"]').click()
    page.locator('.translation-blank').first.wait_for()
    assert page.locator('#practice-jump option').count()==13
    assert page.evaluate("!document.querySelector('#practice-group-dialog')?.open")
    closed()
    print('PASS: dynamic deletion/custom-word counts, other section, true single-section bypass and preserved records/settings',flush=True)
    assert not errors,errors
    context.close()

    context=browser.new_context(viewport={'width':1440,'height':960},service_workers='block')
    page=context.new_page();page.goto(BASE+'#words/C01');page.locator('.mvp-subcategory').first.click()
    page.locator('#practice-group-dialog').wait_for(state='visible');page.set_viewport_size({'width':980,'height':800})
    page.wait_for_function('!document.body.classList.contains("desktop-mvp")')
    assert not page.locator('#lesson-dialog').evaluate('e=>e.open')
    assert page.evaluate("!document.querySelector('#practice-group-dialog')?.open")
    context.close()
    context=browser.new_context(viewport={'width':390,'height':844},is_mobile=True,has_touch=True,service_workers='block')
    page=context.new_page();page.goto(BASE+'#words');page.locator('.vocab-subcategories [data-route="words/C01/C01-S01"]').click()
    page.locator('.translation-blank').first.wait_for();assert page.locator('#practice-jump option').count()==22
    assert page.locator('#practice-group-dialog').count()==0
    assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
    context.close();browser.close()
print('COMPLETE: practice sections passed; existing phone operation and direct deep links retained',flush=True)
