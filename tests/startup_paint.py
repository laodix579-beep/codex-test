"""Stream HTML in gated chunks to inspect real paint frames before app startup.

An optional old HTML path runs the control case and confirms the former flash.
"""
import json
import sys
import threading
from functools import partial
from http.server import SimpleHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit,parse_qs
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]
baseline=len(sys.argv)>1
source=(Path(sys.argv[1]) if baseline else ROOT/'index.html').read_bytes()
first=source.index(b'<script>\n/* Original example material')
second=source.index(b"<script>\n(() => {\n  'use strict';\n  const BASE_STORAGE_KEY")
chunks=[source[:first],source[first:second],source[second:]]
runs={};results=[]

class Run:
 def __init__(self):self.first=threading.Event();self.second=threading.Event()

class Stream(SimpleHTTPRequestHandler):
 def log_message(self,*args):pass
 def translate_path(self,path):return super().translate_path(urlsplit(path).path.removeprefix('/project'))
 def do_GET(self):
  parts=urlsplit(self.path)
  if parts.path!='/project/index.html':return super().do_GET()
  case=parse_qs(parts.query)['case'][0];run=runs[case]
  self.send_response(200);self.send_header('Content-Type','text/html; charset=utf-8');self.send_header('Content-Length',str(len(source)));self.send_header('Cache-Control','no-store');self.end_headers()
  try:
   self.wfile.write(chunks[0]);self.wfile.flush()
   if not run.first.wait(20):return
   self.wfile.write(chunks[1]);self.wfile.flush()
   if not run.second.wait(20):return
   self.wfile.write(chunks[2]);self.wfile.flush()
  except (BrokenPipeError,ConnectionResetError):pass

server=ThreadingHTTPServer(('127.0.0.1',0),partial(Stream,directory=str(ROOT)))
threading.Thread(target=server.serve_forever,daemon=True).start()
FRAME_SCRIPT='''
 window.__startupFrames=[];
 function collect(){
  const content=document.getElementById('content'),app=document.querySelector('.app-main'),body=document.body;
  if(content&&app&&body){
   const frog=document.querySelector('.brand-frog');
   __startupFrames.push({ready:content.dataset.appReady==='true',error:!!document.querySelector('[data-startup-error]'),appVisible:getComputedStyle(app).visibility!=='hidden',desktop:body.classList.contains('desktop-mvp'),bg:getComputedStyle(body).backgroundColor,frogVisible:!!frog&&getComputedStyle(frog).display!=='none'&&getComputedStyle(frog).visibility!=='hidden'});
  }
  requestAnimationFrame(collect);
 }
 requestAnimationFrame(collect);
 delete window.structuredClone;delete Object.hasOwn;delete Array.prototype.at;
 Object.defineProperty(window,'speechSynthesis',{get(){throw new Error('TTS forbidden')}});
'''
try:
 with sync_playwright() as p:
  browser=p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox'])
  profiles=[('desktop',False,False)] if baseline else [('desktop',False,False),('phone',True,False),('failure',False,True)]
  for name,mobile,failure in profiles:
   context=browser.new_context(viewport={'width':390 if mobile else 1440,'height':844 if mobile else 960},is_mobile=mobile,has_touch=mobile,service_workers='block',user_agent='Mozilla/5.0 (Linux; Android 11; Mobile) AppleWebKit/537.36 Chrome/86.0.4240.198 Mobile Safari/537.36 MicroMessenger/8.0.32' if mobile else None)
   context.add_init_script(FRAME_SCRIPT)
   if failure:context.add_init_script("Object.defineProperty(window,'FROG_WORD_CATALOG',{get(){throw new Error('Forced startup failure')},set(){},configurable:true})")
   page=context.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
   for cycle in range(1 if baseline or mobile or failure else 2):
    case=f'{name}-{cycle}';run=Run();runs[case]=run
    page.goto(f'http://127.0.0.1:{server.server_port}/project/index.html?case={case}#home',wait_until='commit')
    page.wait_for_function('document.querySelector("#content")&&__startupFrames.length>=3')
    if baseline:
     assert page.locator('.brand-frog').is_visible()
     assert page.locator('body').evaluate('e=>getComputedStyle(e).backgroundColor')=='rgb(16, 17, 20)'
     page.screenshot(path='/tmp/startup-baseline-old-flash.png')
     print('PASS control: old HTML visibly paints the dark frog shell before app initialization',flush=True)
    else:
     assert page.locator('.startup-screen').is_visible()
     assert page.locator('.app-main').is_hidden() and page.locator('#sidebar').is_hidden()
     assert page.locator('html').evaluate('e=>e.classList.contains("desktop-mvp")')== True
     assert page.locator('body').evaluate('e=>e.classList.contains("desktop-mvp")')== True
     assert page.locator('body').evaluate('e=>getComputedStyle(e).backgroundColor')=='rgb(246, 247, 255)'
     page.screenshot(path=f'/tmp/startup-boot-{case}.png')
    run.first.set();page.wait_for_function('!!window.FrogMobile&&__startupFrames.length>=6')
    if not baseline:assert page.locator('.startup-screen').is_visible() and page.locator('.app-main').is_hidden()
    run.second.set();page.wait_for_load_state('domcontentloaded')
    if failure:
     page.locator('[data-startup-error]').wait_for(state='visible')
     assert page.locator('.startup-screen').is_hidden()
     assert page.locator('.app-main').is_visible()
     assert page.get_by_role('button',name='重新加载',exact=True).is_visible()
    else:
     page.locator('.mvp-resume').wait_for(state='visible')
     if not baseline:
      assert page.locator('.startup-screen').is_hidden()
      assert page.locator('html').evaluate('e=>!e.classList.contains("app-booting")')
    page.wait_for_function('__startupFrames.some(f=>f.ready||f.error)')
    frames=page.evaluate('__startupFrames')
    if not baseline:
     assert not any(f['appVisible'] and not f['ready'] and not f['error'] for f in frames),frames
     assert not any(f['frogVisible'] or f['bg']=='rgb(16, 17, 20)' for f in frames),frames
     if not failure:assert not errors,errors
     page.screenshot(path=f'/tmp/startup-ready-{case}.png')
     results.append({'profile':case,'framesChecked':len(frames),'appHiddenUntilReady':True,'oldDesktopShellNeverPainted':True,'failureVisible':failure})
     print('PASS:',case,'gated slow-load frames, early layout, ready/failure reveal and no old desktop paint',flush=True)
   context.close()
  browser.close()
finally:
 for run in runs.values():run.first.set();run.second.set()
 server.shutdown();server.server_close()
if not baseline:
 (ROOT/'reports/startup-paint-results.json').write_text(json.dumps(results,ensure_ascii=False,indent=2)+'\n')
 print('COMPLETE: slow first-paint, repeat load, mobile and startup failure checks passed',flush=True)
