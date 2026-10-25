"""Word catalog, upgrade, backup and GA audio regression checks.

Run with the local server on port 8000: python3 tests/word_catalog.py
"""
from pathlib import Path
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
import tempfile
import threading
from playwright.sync_api import sync_playwright

BASE = 'http://127.0.0.1:8000/'


def stored(page):
    return page.evaluate('JSON.parse(localStorage.getItem(document.body.dataset.storageKey))')


with sync_playwright() as p:
    browser = p.chromium.launch(executable_path='/usr/bin/chromium', headless=True, args=['--no-sandbox'])
    context = browser.new_context(viewport={'width':1440,'height':1000})
    page = context.new_page()
    # Apply upgrade fixtures after the old document's pagehide time flush.
    # Writing storage immediately before reload races with that legitimate save.
    page.add_init_script('''{
      const pending=sessionStorage.getItem('catalog-next-state');
      if(pending){const {key,state}=JSON.parse(pending);sessionStorage.removeItem('catalog-next-state');localStorage.setItem(key,state);}
    }''')
    errors = []
    page.on('pageerror', lambda error: errors.append(str(error)))
    page.goto(BASE+'#words')
    # Reload once to use the same validated representation as an existing install.
    page.reload()
    assert page.locator('.vocab-category').count() == 1
    assert page.locator('.vocab-subcategories button').count() == 4
    initial = stored(page)
    assert len(initial['words']) == 136
    assert not any(w['id'].startswith('word-') for w in initial['words'])
    assert [sum(w['subcategoryId']==f'C01-S{i:02}' for w in initial['words']) for i in range(1,5)] == [22,62,19,33]
    print('PASS: one populated theme, four category entrances and exactly 136 imported entries', flush=True)

    page.goto(BASE+'#words/manage/C01')
    groups=page.locator('.word-subcategory-group')
    assert groups.count()==4
    assert [groups.nth(i).locator('.word-card').count() for i in range(4)]==[22,62,19,33]
    for i in range(4):
        expected={w['id'] for w in initial['words'] if w['subcategoryId']==f'C01-S{i+1:02}'}
        actual=set(groups.nth(i).locator('[data-action="learn-word"]').evaluate_all('(buttons)=>buttons.map(b=>b.dataset.id)'))
        assert actual==expected
    groups.first.locator('[data-action="learn-word-group"]').click()
    assert '1 / 22' in page.locator('.lesson-progress').inner_text()
    assert page.locator('#practice-jump option').count()==22
    assert page.locator('#practice-jump option').all_text_contents()==[f'{i+1}. {w["word"]}' for i,w in enumerate(initial['words'][:22])]
    page.locator('#lesson-dialog [data-close]').click()
    print('PASS: all entries appear in their matching groups; greeting group practice contains all 22 entries in order',flush=True)

    page.evaluate('''()=>{
      const key=document.body.dataset.storageKey,s=JSON.parse(localStorage.getItem(key));
      s.words[0].categoryId='';s.words[0].subcategoryId='';
      s.words[1].categoryId='C02';s.words[1].subcategoryId='C01-S02';
      s.wordStatus[s.words[0].id]='mastered';sessionStorage.setItem('catalog-next-state',JSON.stringify({key,state:JSON.stringify(s)}));
    }''')
    page.reload()
    repaired=stored(page)
    assert repaired['words'][0]['subcategoryId']=='C01-S01' and repaired['words'][1]['subcategoryId']=='C01-S01'
    assert repaired['words'][1]['categoryId']=='C01'
    assert repaired['wordStatus'][repaired['words'][0]['id']]=='mastered'
    assert len(repaired['words'])==136
    page.evaluate("(s)=>sessionStorage.setItem('catalog-next-state',JSON.stringify({key:document.body.dataset.storageKey,state:JSON.stringify(s)}))",initial)
    page.reload()
    print('PASS: existing saved classification is repaired without losing entries or learning progress',flush=True)

    for i, count in enumerate([22,62,19,33],1):
        page.goto(BASE+f'#words/manage/C01/C01-S{i:02}')
        page.wait_for_function('(n)=>document.querySelectorAll(".word-card").length===n', arg=count)
        assert page.locator('.word-example-speak').count() == count
    page.goto(BASE+'#words/C02/C02-S01')
    page.wait_for_url('**/#words')
    assert page.locator('.vocab-category').count()==1
    print('PASS: all four populated lists and old empty category routes redirect', flush=True)

    page.goto(BASE+'#words/manage/C01/C01-S03')
    page.get_by_role('button',name='开始背词').click()
    assert page.locator('#lesson-dialog').get_attribute('open') is not None
    assert '1 / 10' in page.locator('.lesson-progress').inner_text()
    page.locator('#lesson-dialog [data-close]').click()
    page.get_by_role('button',name='+ 添加单词').click()
    assert page.locator('#new-subcategory').input_value() == 'C01-S03'
    page.locator('#new-word').fill('scarlet')
    page.locator('#new-meaning').fill('猩红色')
    page.locator('#new-example').fill('This is a scarlet flower.')
    page.get_by_role('button',name='保存单词',exact=True).click()
    page.reload()
    custom = next(w for w in stored(page)['words'] if w['word']=='scarlet')
    assert custom['categoryId']=='C01' and custom['subcategoryId']=='C01-S03'
    with page.expect_download() as event:
        page.locator('[data-action="backup"]').first.click()
    backup_path = '/tmp/frog-catalog-backup-test.json'
    event.value.save_as(backup_path)
    backup = json.loads(Path(backup_path).read_text())
    assert next(w for w in backup['words'] if w['word']=='scarlet')['subcategoryId']=='C01-S03'
    print('PASS: category practice, manual additions, reload and backup preserve classification', flush=True)

    # Mimic a real old installation with a custom word and existing non-word progress.
    legacy = initial
    legacy.pop('vocabularyVersion', None)
    legacy['words']=[{'id':'word-old','word':'obsolete','meaning':'旧词','ipa':'','example':''}]
    legacy['wordStatus']={'word-old':'mastered'}
    legacy['courses']=[{'id':'archived-course','title':'历史课程','description':'保留资料','category':'daily','level':'A1','color':'purple','createdAt':'2026-01-01T00:00:00.000Z','sample':False,'sentences':[{'id':'archived-sentence','english':'Archived sentence.','chinese':'历史句子。','section':''}]}]
    sentence_id=legacy['courses'][0]['sentences'][0]['id']
    legacy['sentenceStatus']={sentence_id:'mastered'}
    legacy['favorites']=['word-old',sentence_id]
    legacy['settings']['voice']='old-UK-voice'
    legacy['notes']=[{'id':'note-keep','title':'保留手账','body':'内容不能丢失','createdAt':'2026-01-01T00:00:00Z','updatedAt':'2026-01-01T00:00:00Z'}]
    page.evaluate("(s)=>sessionStorage.setItem('catalog-next-state',JSON.stringify({key:document.body.dataset.storageKey,state:JSON.stringify(s)}))",legacy)
    page.reload()
    migrated=stored(page)
    assert len(migrated['words'])==136 and migrated['wordStatus']=={}
    assert migrated['courses']==legacy['courses'] and migrated['notes']==legacy['notes']
    assert migrated['sentenceStatus']==legacy['sentenceStatus'] and migrated['favorites']==[sentence_id]
    assert migrated['settings']['voice']==''
    recovery=page.evaluate('JSON.parse(localStorage.getItem(document.body.dataset.storageKey+":before-basic-us-v1"))')
    assert recovery['words'][0]['id']=='word-old'
    page.reload()
    assert stored(page)==migrated
    print('PASS: legacy words are replaced once; recovery copy, courses, notes and sentence progress survive', flush=True)

    voice_selection=page.evaluate('''()=>{
      const uk={lang:'en-GB',name:'British',voiceURI:'uk',localService:true};
      const us={lang:'en-US',name:'Samantha',voiceURI:'us',localService:true};
      return {locale:FrogPractice.speechProfile.locale,selected:FrogPractice.selectPracticeVoice([uk,us],'uk')?.voiceURI,
        ukOnly:FrogPractice.selectPracticeVoice([uk]),bank:LOCAL_AUDIO_BANK.locale};
    }''')
    assert voice_selection=={'locale':'en-US','selected':'us','ukOnly':None,'bank':'en-US'}
    decoded=page.evaluate('''async()=>{
      const ac=new AudioContext(),bank=LOCAL_AUDIO_BANK;
      const texts=FROG_WORD_CATALOG.words.flatMap(w=>[w.word,w.example]);
      texts.push(...LOCAL_TEXTBOOK.sections.flatMap(s=>s.items.map(i=>i.english)));
      texts.push(...LOCAL_SAMPLES.courses.flatMap(c=>c.sentences.map(i=>i[0])));
      texts.push(...LOCAL_SAMPLES.phonetics.map(i=>i[2]));
      let total=0;
      for(const text of new Set(texts)){
        const key=FrogPractice.normalize(text),payload=bank.clips[key];
        if(!payload)throw new Error('Missing GA audio: '+text);
        const bytes=bank.storage==='files'?await (await fetch(payload)).arrayBuffer():Uint8Array.from(atob(payload),c=>c.charCodeAt(0)).buffer;
        const buffer=await ac.decodeAudioData(bytes);
        if(buffer.duration<=.08||!buffer.getChannelData(0).some(n=>Math.abs(n)>.001))throw new Error('Silent audio: '+text);
        total++;
      }
      await ac.close();return total;
    }''')
    page.goto(BASE+'#words/manage/C01/C01-S01')
    page.locator('[data-action="speak-word"]').first.click()
    page.wait_for_function('document.getElementById("question-audio").currentTime>0')
    assert page.locator('#question-audio').get_attribute('data-prompt')=='hello'
    page.locator('.word-example-speak').first.click()
    page.wait_for_function('document.getElementById("question-audio").currentTime>0')
    assert page.locator('#question-audio').get_attribute('data-prompt')=='hello anna'
    print(f'PASS: GA US voice selection; {decoded} word, example, course and phonetic recordings decode; word/example buttons play', flush=True)

    page.locator('[data-action="save-app"]').click()
    with page.expect_download() as event:
        page.locator('[data-action="download-app-file"]').click()
    standalone_path=Path('/tmp/frog-word-catalog-export.html')
    event.value.save_as(standalone_path)
    page.locator('#save-app-dialog [data-close]').click()
    # Managed Chromium blocks file://. Serve only the exported HTML in an isolated
    # directory to verify that no original-checkout assets are required.
    class QuietHandler(SimpleHTTPRequestHandler):
        def log_message(self,*args):
            pass
    with tempfile.TemporaryDirectory(prefix='frog-export-') as directory:
        Path(directory,'index.html').write_bytes(standalone_path.read_bytes())
        server=ThreadingHTTPServer(('127.0.0.1',0),partial(QuietHandler,directory=directory))
        threading.Thread(target=server.serve_forever,daemon=True).start()
        local_context=browser.new_context()
        try:
            local=local_context.new_page()
            local.goto(f'http://127.0.0.1:{server.server_port}/#words/manage/C01/C01-S01')
            assert local.locator('.word-card').count()==22
            assert len(stored(local)['words'])==136 and stored(local)['notes']==legacy['notes']
            local_context.set_offline(True)
            local.locator('[data-action="speak-word"]').first.click()
            local.wait_for_function('document.getElementById("question-audio").currentTime>0')
        finally:
            local_context.close()
            server.shutdown()
            server.server_close()
    print('PASS: exported single HTML retains categories, progress and playable GA audio without checkout assets',flush=True)

    page.goto(BASE+'#settings')
    page.wait_for_function("document.querySelector('[data-mobile-status]')?.textContent.startsWith('已保存离线内容')")
    context.set_offline(True)
    page.goto(BASE+'#words/manage/C01/C01-S01')
    page.reload()
    page.locator('[data-action="speak-word"]').first.click()
    page.wait_for_function('document.getElementById("question-audio").currentTime>0')
    assert page.locator('.word-card').count()==22
    context.set_offline(False)
    print('PASS: offline reload keeps the category and playable new GA word audio', flush=True)

    for width in [320,390,768,1440,1894]:
        page.set_viewport_size({'width':width,'height':900})
        for route in ['words','words/all','words/C01','words/C01/C01-S01']:
            page.goto(BASE+'#'+route)
            assert page.evaluate('document.documentElement.scrollWidth<=innerWidth'),(width,route)
    assert not errors,errors
    print('PASS: catalog and word lists fit phone/tablet/desktop widths without JavaScript errors', flush=True)
    browser.close()

print('COMPLETE: 10 word catalog regression groups passed', flush=True)
