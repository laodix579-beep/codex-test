"""Original MP3 integrity, full buffering, races, pitch and quieter feedback."""
import hashlib
import json
import threading
import time
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
manifest = json.loads((ROOT / 'audio-manifest.json').read_text())
audit = json.loads((ROOT / 'reports/all-audio-sha256.json').read_text())
assert len(json.loads((ROOT / 'reports/source-audio-sha256.json').read_text())) == 610
assert len(manifest['clips']) == len(audit) == 1387
for row in manifest['clips']:
    assert hashlib.sha256((ROOT / row['path']).read_bytes()).hexdigest() == row['sha256'] == audit[row['path']]['sha256']

control = {'slow': set(), 'corrupt': set(), 'missing': set(), 'requests': {}}


class Handler(SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def end_headers(self):
        if urlsplit(self.path).path.endswith('.mp3'):
            self.send_header('Cache-Control', 'no-store')
        super().end_headers()

    def do_GET(self):
        path = urlsplit(self.path).path.lstrip('/')
        if path.startswith('audio/'):
            control['requests'][path] = control['requests'].get(path, 0) + 1
        if path in control['missing']:
            self.send_error(404)
            return
        if path in control['slow'] or path in control['corrupt']:
            data = (ROOT / path).read_bytes()
            if path in control['corrupt']:
                control['corrupt'].remove(path)
                data = data[:100] + b'bad recording bytes' + data[119:]
            self.send_response(200)
            self.send_header('Content-Type', 'audio/mpeg')
            self.send_header('Content-Length', str(len(data)))
            self.end_headers()
            self.wfile.write(data[:1024])
            self.wfile.flush()
            if path in control['slow']:
                time.sleep(1.25)
            try:
                self.wfile.write(data[1024:])
            except (BrokenPipeError, ConnectionResetError):
                pass
            return
        super().do_GET()


server = ThreadingHTTPServer(('127.0.0.1', 0), partial(Handler, directory=str(ROOT)))
threading.Thread(target=server.serve_forever, daemon=True).start()
BASE = f'http://127.0.0.1:{server.server_port}/'
results = {'originalMp3HashMatches': 610, 'profiles': []}
try:
    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path='/usr/bin/chromium', headless=True, args=['--no-sandbox'])
        for mobile in (False, True):
            context = browser.new_context(viewport={'width': 390 if mobile else 1440, 'height': 844 if mobile else 960}, is_mobile=mobile, has_touch=mobile, service_workers='block')
            context.add_init_script('''{
                Object.defineProperty(window,'speechSynthesis',{get(){throw new Error('TTS forbidden')}});
                Object.defineProperty(window,'SpeechSynthesisUtterance',{get(){throw new Error('TTS forbidden')}});
                delete window.structuredClone;delete Object.hasOwn;delete Array.prototype.at;
                window.played=[];window.stalls=[];window.loads=0;
                document.addEventListener('playing',e=>{if(e.target.id==='question-audio')played.push(e.target.dataset.sourceText)},true);
                document.addEventListener('loadstart',e=>{if(e.target.id==='question-audio')loads++},true);
                ['waiting','stalled'].forEach(type=>document.addEventListener(type,e=>{if(e.target.id==='question-audio'&&e.target.currentTime>0)stalls.push(type)},true));
            }''')
            page = context.new_page()
            errors = []
            page.on('pageerror', lambda e: errors.append(str(e)))
            page.goto(BASE + '#home', wait_until='networkidle')
            snapshot = page.evaluate('localStorage.getItem(document.body.dataset.storageKey)')
            if not mobile:
                decoded = page.evaluate('''async()=>{
                    const ctx=new AudioContext(),rows=Object.entries(LOCAL_AUDIO_BANK.clips);let next=0,count=0,peak=0;
                    await Promise.all(Array.from({length:6},async()=>{while(next<rows.length){
                        const [key,path]=rows[next++],response=await fetch(path),bytes=await response.arrayBuffer();
                        const hash=Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',bytes)),n=>n.toString(16).padStart(2,'0')).join('');
                        if(hash!==LOCAL_AUDIO_BANK.sha256[key])throw new Error('Wrong source bytes '+key);
                        const buffer=await ctx.decodeAudioData(bytes);let max=0;
                        for(let c=0;c<buffer.numberOfChannels;c++)for(const sample of buffer.getChannelData(c))max=Math.max(max,Math.abs(sample));
                        if(buffer.duration<.05||max<.001||max>=1)throw new Error('Invalid/silent/clipped recording '+key);
                        peak=Math.max(peak,max);count++;
                    }}));await ctx.close();return {count,peak};
                }''')
                assert decoded['count'] == 1387
                results['browserDecodedOriginals'] = decoded
                print('PASS: 1387 MP3 hashes, including 610 unchanged originals, complete browser decode, valid durations and no silence/clipping', flush=True)
            assert page.evaluate('localStorage.getItem(document.body.dataset.storageKey)') == snapshot

            # Search uses separate, byte-accurate word and sentence recordings.
            words = page.evaluate('FROG_WORD_CATALOG.words.slice(0,10)')
            for word in words:
                page.locator('#global-search').fill(word['word'])
                page.locator('#global-search').press('Enter')
                card = page.locator(f'.search-results .word-card[data-word="{word["word"]}"]')
                for selector, text in [('[data-action="speak-word"]', word['word']), ('.word-example-speak', word['example'])]:
                    card.locator(selector).click()
                    page.wait_for_function('(text)=>{const a=document.querySelector("#question-audio");return FrogPractice.normalize(a.dataset.sourceText)===FrogPractice.normalize(text)&&a.currentTime>0&&!a.paused}', arg=text)
                    delivered = page.evaluate('''async()=>{
                        const a=document.querySelector('#question-audio'),bytes=await (await fetch(a.src)).arrayBuffer();
                        const hash=Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',bytes)),n=>n.toString(16).padStart(2,'0')).join('');
                        return {blob:a.src.startsWith('blob:'),hash,expected:LOCAL_AUDIO_BANK.sha256[a.dataset.audioKey],pitch:a.preservesPitch,rate:a.playbackRate};
                    }''')
                    assert delivered['blob'] and delivered['hash'] == delivered['expected']
                    assert delivered['pitch'] and delivered['rate'] == 1

            # Start a deliberately slow fresh sentence, then leave before its
            # complete body arrives. Its promise must not start stale speech.
            target = 'audio/en-us/sentence/the-apple-is-red.mp3'
            control['slow'].add(target)
            page.goto(BASE + '#words/C01/C01-S03')
            page.locator('.translation-blank').first.wait_for()
            page.wait_for_function('document.querySelector("#question-audio").dataset.buffering==="true"')
            assert page.locator('#question-audio').evaluate('a=>a.paused&&!a.hasAttribute("src")')
            # A speed change during loading must not revert when the complete
            # MP3 arrives. Use the real setting/change handler.
            page.locator('[data-practice-setting="rate"]').last.evaluate("e=>{e.value='0.9';e.dispatchEvent(new Event('change',{bubbles:true}));}")
            page.wait_for_function('document.querySelector("#question-audio").currentTime>0')
            assert page.locator('#question-audio').evaluate('a=>a.playbackRate') == .9
            # Another uncached, deliberately slow clip is canceled on navigation.
            second_slow = 'audio/en-us/sentence/the-sun-is-yellow.mp3'
            control['slow'].add(second_slow)
            page.locator('#practice-jump').evaluate("e=>{e.value=String(FROG_WORD_CATALOG.words.filter(w=>w.subcategoryId==='C01-S03').findIndex(w=>w.word==='yellow'));e.dispatchEvent(new Event('change',{bubbles:true}));}")
            page.wait_for_function('document.querySelector("#question-audio").dataset.sourceText==="The sun is yellow."&&document.querySelector("#question-audio").dataset.buffering==="true"')
            page.evaluate('played=[]')
            page.locator('.mobile-controls [data-action="next-item"]' if mobile else '.translation-shortcuts [data-action="next-item"]').last.click()
            page.wait_for_function('played.length>0')
            page.wait_for_timeout(1500)
            assert 'The sun is yellow.' not in page.evaluate('played')
            control['slow'].clear()

            # Voice settings apply immediately and survive source changes.
            if mobile:
                page.locator('#practice-mobile-menu>summary').click()
                speed = page.locator('#practice-mobile-menu [data-practice-setting="rate"]')
            else:
                page.locator('.mvp-practice-info .practice-options>summary').click()
                speed = page.locator('.mvp-practice-info [data-practice-setting="rate"]')
            for rate in ('0.65', '0.9', '1.2', '1'):
                speed.select_option(rate)
                assert page.locator('#question-audio').evaluate('a=>a.playbackRate') == float(rate)
                assert page.locator('#question-audio').evaluate('a=>a.preservesPitch&&a.webkitPreservesPitch&&a.mozPreservesPitch')
            if mobile:
                page.locator('#practice-mobile-menu>summary').click()
            replay = page.locator('.mobile-controls [data-action="speak-lesson"]' if mobile else '#translation-form [data-action="speak-lesson"]')
            page.evaluate('''()=>{const original=FrogPractice.sound;window.effectLevels=[];FrogPractice.sound=(kind,volume)=>{effectLevels.push(volume);return original(kind,volume)};document.querySelector('#question-audio').volume=.6;}''')
            replay.click()
            page.wait_for_function('!document.querySelector("#question-audio").paused&&document.querySelector("#question-audio").currentTime>0')
            page.locator('.translation-blank').first.fill('b')
            page.locator('.translation-blank').first.press('l')
            assert page.evaluate('effectLevels.at?effectLevels.at(-1):effectLevels[effectLevels.length-1]') <= .04
            assert page.locator('#question-audio').evaluate('a=>a.volume') == .6

            # Pausing/replaying at time zero used to trigger another drill/load.
            load_before = page.evaluate('loads')
            page.evaluate('''async()=>{const a=document.querySelector('#question-audio');a.pause();a.currentTime=0;await a.play();}''')
            page.wait_for_timeout(120)
            assert page.evaluate('loads') == load_before

            # A complete corrupt response must be rejected, fetched again and
            # verified before audio.play. This path is not in the warehouse.
            page.evaluate("window.fixtureClosed=false;document.querySelector('#lesson-dialog').addEventListener('close',()=>window.fixtureClosed=true,{once:true})")
            page.locator('.practice-back').click()
            page.wait_for_function('fixtureClosed')
            page.goto(BASE + '#settings')
            page.locator('#settings-form').wait_for()
            corrupt = 'audio/en-us/sentence/speak-in-a-clear-voice.mp3'
            control['corrupt'].add(corrupt)
            before = control['requests'].get(corrupt, 0)
            page.evaluate('''()=>{const b=document.createElement('button');b.id='audio-fixture';b.dataset.action='speak';b.dataset.text='Speak in a clear voice.';b.textContent='Test existing recording';b.style.cssText='position:fixed;bottom:20px;right:20px;z-index:9999';document.body.append(b);}''')
            page.locator('#audio-fixture').click()
            page.wait_for_function('document.querySelector("#question-audio").dataset.sourceText==="Speak in a clear voice."&&document.querySelector("#question-audio").currentTime>0')
            assert control['requests'][corrupt] - before == 2

            # Failed downloads display a retry message; the existing replay
            # control succeeds once the same provided recording is available.
            missing = 'audio/en-us/sentence/what-is-the-deadline-for-this-task.mp3'
            control['missing'].add(missing)
            page.locator('#audio-fixture').evaluate("b=>b.dataset.text='What is the deadline for this task?'")
            page.locator('#audio-fixture').click()
            page.wait_for_function('document.querySelector("#toast").textContent.includes("录音未能完整加载")')
            assert page.locator('#question-audio').evaluate('a=>a.paused&&!a.hasAttribute("src")')
            control['missing'].clear()
            page.locator('#audio-fixture').click()
            page.wait_for_function('document.querySelector("#question-audio").currentTime>0&&!document.querySelector("#question-audio").paused')

            # Keep one foreground voice even with a learner recording player.
            page.evaluate('''async()=>{const a=document.querySelector('#question-audio'),v=document.createElement('audio');v.id='voice-playback';v.src=a.src;document.body.append(v);await v.play();}''')
            assert page.locator('#question-audio').evaluate('a=>a.paused&&!a.hasAttribute("src")')
            page.locator('#audio-fixture').click()
            page.wait_for_function('!document.querySelector("#question-audio").paused')
            assert page.locator('#voice-playback').evaluate('a=>a.paused')
            page.locator('#voice-playback').evaluate('a=>a.remove()')
            page.goto(BASE + '#words/C01/C01-S01')
            page.locator('.translation-blank').first.wait_for()
            page.wait_for_function('document.querySelector("#question-audio").currentTime>0')
            page.evaluate('''async()=>{const a=document.querySelector('#question-audio'),v=document.createElement('audio');v.id='voice-playback';v.src=a.src;window.fixtureVoice=v;document.querySelector('#lesson-dialog').append(v);await v.play();}''')
            page.evaluate("window.fixtureClosed=false;document.querySelector('#lesson-dialog').addEventListener('close',()=>window.fixtureClosed=true,{once:true})")
            page.locator('.practice-back').click()
            page.wait_for_function('fixtureClosed')
            assert page.evaluate('fixtureVoice.paused')
            assert not page.evaluate('stalls'), page.evaluate('stalls')
            assert not errors, errors
            results['profiles'].append({'mobile': mobile, 'wordAndSentenceUiChecks': 20, 'fullBufferHash': True, 'slowNetworkCancellation': True, 'pitchAndLiveRate': True, 'quietFeedback': True, 'nativePauseNoRestart': True, 'corruptResponseRecovery': True, 'failedDownloadRetry': True, 'exclusiveVoice': True, 'midClipStalls': 0})
            print(f'PASS: {"phone" if mobile else "desktop"} 20 source-accurate UI plays, slow response, cancellation, pitch/rate, feedback, retry and exclusive voice', flush=True)
            context.close()
        browser.close()
finally:
    server.shutdown()
    server.server_close()
(ROOT / 'reports/audio-quality-results.json').write_text(json.dumps(results, ensure_ascii=False, indent=2) + '\n')
print('COMPLETE: audio quality and complete-buffer playback checks passed', flush=True)
