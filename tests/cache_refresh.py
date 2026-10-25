"""Online navigation revalidates fresh HTTP cache; offline startup keeps new UI."""
import threading
from functools import partial
from http.server import SimpleHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]
state={'revision':1,'requests':0}
class Handler(SimpleHTTPRequestHandler):
 def log_message(self,*args):pass
 def translate_path(self,path):return super().translate_path(urlsplit(path).path.removeprefix('/project'))
 def do_GET(self):
  path=urlsplit(self.path).path
  if path in ['/project/revision.html','/project/away.html']:
   revision=state['revision']
   if path.endswith('revision.html'):state['requests']+=1
   etag=f'"revision-{revision}"'
   if self.headers.get('If-None-Match')==etag:
    self.send_response(304);self.send_header('Cache-Control','public, max-age=3600');self.send_header('ETag',etag);self.end_headers();return
   body=f'<!doctype html><html data-revision="{revision}"><meta charset="utf-8"><title>Cache test</title><p>Revision {revision}</p></html>'.encode()
   self.send_response(200);self.send_header('Content-Type','text/html; charset=utf-8');self.send_header('Content-Length',str(len(body)));self.send_header('Cache-Control','public, max-age=3600');self.send_header('ETag',etag);self.end_headers();self.wfile.write(body);return
  super().do_GET()

server=ThreadingHTTPServer(('127.0.0.1',0),partial(Handler,directory=str(ROOT)))
threading.Thread(target=server.serve_forever,daemon=True).start()
try:
 with sync_playwright() as p:
  browser=p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox'])
  context=browser.new_context(viewport={'width':1440,'height':960})
  context.add_init_script("Object.defineProperty(window,'speechSynthesis',{get(){throw new Error('TTS forbidden')}})")
  page=context.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
  base=f'http://127.0.0.1:{server.server_port}/project/'
  page.goto(base+'#settings')
  page.wait_for_function('document.querySelector("[data-mobile-status]").textContent.startsWith("已保存离线内容")',timeout=90000)
  assert page.evaluate('!!navigator.serviceWorker.controller')
  page.evaluate('''()=>{const key=document.body.dataset.storageKey,s=JSON.parse(localStorage.getItem(key));s.wordStatus['C01-S01-001']='mastered';s.settings.volume=.35;localStorage.setItem(key,JSON.stringify(s));}''')
  page.goto(base+'revision.html');assert page.locator('html').get_attribute('data-revision')=='1'
  page.goto(base+'away.html');before=state['requests'];state['revision']=2
  page.goto(base+'revision.html')
  assert page.locator('html').get_attribute('data-revision')=='2'
  assert state['requests']>before
  print('PASS: controlled navigation revalidates an otherwise-fresh one-hour HTTP cache and returns revision 2',flush=True)
  context.set_offline(True);page.goto(base+'#home')
  page.locator('.mvp-resume').wait_for()
  assert page.locator('body').evaluate('e=>e.classList.contains("desktop-mvp")')
  assert page.locator('html').evaluate('e=>e.classList.contains("desktop-mvp")&&!e.classList.contains("app-booting")')
  assert page.locator('.startup-screen').is_hidden()
  assert page.locator('.brand-frog').is_hidden()
  saved=page.evaluate('JSON.parse(localStorage.getItem(document.body.dataset.storageKey))')
  assert saved['wordStatus']['C01-S01-001']=='mastered' and saved['settings']['volume']==.35
  page.goto(base+'#words/C01/C01-S01');page.locator('.translation-blank').fill('hello');page.locator('#translation-submit').click()
  page.wait_for_function('document.querySelector("#question-audio").dataset.sourceText==="hello"&&document.querySelector("#question-audio").currentTime>0')
  assert not errors,errors
  print('PASS: offline cached new UI starts, boot screen releases, original MP3 plays and records/settings survive',flush=True)
  context.close();browser.close()
finally:
 server.shutdown();server.server_close()
print('COMPLETE: navigation freshness and offline startup passed',flush=True)
