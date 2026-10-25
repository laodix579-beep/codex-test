"""Reuse verified old MP3s, repair corrupt/partial cache entries and serve ranges."""
import json
import threading
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
requests = []


class Handler(SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def do_GET(self):
        path = urlsplit(self.path).path.lstrip('/')
        if path == 'bootstrap.html':
            self.send_response(200)
            self.send_header('Content-Type', 'text/html')
            self.end_headers()
            self.wfile.write(b'<!doctype html><title>Cache fixture</title>')
            return
        if path.endswith('.mp3'):
            requests.append(path)
        super().do_GET()


server = ThreadingHTTPServer(('127.0.0.1', 0), partial(Handler, directory=str(ROOT)))
threading.Thread(target=server.serve_forever, daemon=True).start()
BASE = f'http://127.0.0.1:{server.server_port}/'
try:
    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path='/usr/bin/chromium', headless=True, args=['--no-sandbox'])
        page = browser.new_page(viewport={'width': 1440, 'height': 960})
        errors = []
        page.on('pageerror', lambda e: errors.append(str(e)))
        page.goto(BASE + 'bootstrap.html')
        page.evaluate('''async()=>{
            const rows=(await (await fetch('audio-manifest.json')).json()).clips,cache=await caches.open('frog-audio-test-previous');let next=0;
            await Promise.all(Array.from({length:6},async()=>{while(next<rows.length){const row=rows[next++];await cache.put(row.path,await fetch(row.path));}}));
            await cache.put('audio/en-us/word/hello.mp3',new Response('corrupt full response',{headers:{'Content-Type':'audio/mpeg'}}));
            // Cache.put disallows 206; a truncated legacy 200 still must fail hash validation.
            const source=await (await cache.match('audio/en-us/word/hi.mp3')).arrayBuffer();
            await cache.put('audio/en-us/word/hi.mp3',new Response(source.slice(0,128),{headers:{'Content-Type':'audio/mpeg'}}));
        }''')
        requests.clear()
        page.goto(BASE + '#settings')
        page.wait_for_function('document.querySelector("[data-mobile-status]").textContent.startsWith("已保存离线内容")', timeout=90000)
        assert sorted(requests) == ['audio/en-us/word/hello.mp3', 'audio/en-us/word/hi.mp3'], requests
        assert page.evaluate('!!navigator.serviceWorker.controller')
        print('PASS: cache update reuses 608 complete original MP3s and refetches two corrupt/truncated files', flush=True)
        requests.clear()
        page.evaluate('''async()=>{const c=await caches.open(FROG_OFFLINE_CACHE);await c.put('audio/en-us/word/hello.mp3',new Response('bad cached bytes',{headers:{'Content-Type':'audio/mpeg'}}));}''')
        page.locator('#global-search').fill('hello')
        page.locator('#global-search').press('Enter')
        page.locator('.word-card[data-word="hello"] [data-action="speak-word"]').click()
        page.wait_for_function('document.querySelector("#question-audio").currentTime>0')
        assert requests == ['audio/en-us/word/hello.mp3'], requests
        actual = page.evaluate('''async()=>{
            const a=document.querySelector('#question-audio'),bytes=await (await fetch(a.src)).arrayBuffer();
            return Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',bytes)),n=>n.toString(16).padStart(2,'0')).join('')===LOCAL_AUDIO_BANK.sha256.hello;
        }''')
        assert actual
        print('PASS: playback repairs a corrupt current cache entry and delivers original verified bytes', flush=True)
        page.context.set_offline(True)
        page.reload()
        page.locator('.word-card[data-word="hello"] [data-action="speak-word"]').click()
        page.wait_for_function('document.querySelector("#question-audio").currentTime>0')
        ranges = page.evaluate('''async()=>{
            const out=[];for(const range of ['bytes=0-127','bytes=10-40','bytes=-128','bytes=99999999-']){
                const r=await fetch(LOCAL_AUDIO_BANK.clips.hello,{headers:{Range:range}});out.push({range,status:r.status,bytes:(await r.arrayBuffer()).byteLength,contentRange:r.headers.get('Content-Range')});
            }return out;
        }''')
        assert [(r['status'], r['bytes']) for r in ranges] == [(206, 128), (206, 31), (206, 128), (416, 0)], ranges
        assert not errors, errors
        browser.close()
finally:
    server.shutdown()
    server.server_close()
print('COMPLETE: verified MP3 cache reuse, automatic repair and offline playback/ranges passed', flush=True)
