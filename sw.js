// Public static resources only; personal study data stays in localStorage.
importScripts('./audio-files.js');
const CACHE="frog-learning-progress-v24";
const ROOT=new URL('./',self.location.href);
const FILES=['index.html','assets/home-hero.png','audio-files.js','audio-manifest.json','data/pronunciation-test-words.json','manifest.webmanifest','icon-192.png','icon-512.png','apple-touch-icon.png',...self.FROG_AUDIO_FILES];
self.addEventListener('install',event=>event.waitUntil((async()=>{
  const cache=await caches.open(CACHE);let next=0;
  await Promise.all(Array.from({length:6},async()=>{
    while(next<FILES.length){
      const request=new Request(new URL(FILES[next++],ROOT).href,{cache:'reload'});
      const response=await fetch(request);
      if(!response.ok)throw new Error('An offline resource could not be downloaded.');
      await cache.put(request,response);
    }
  }));
  const page=await cache.match(new URL('index.html',ROOT).href);
  if(!page||!(await page.text()).includes('window.FROG_OFFLINE_CACHE="'+CACHE+'"'))
    throw new Error('The offline page does not match this update.');
  await self.skipWaiting();
})()));
self.addEventListener('message',event=>{
  if(event.data?.type==='FROG_CACHE_VERSION')event.ports[0]?.postMessage({cache:CACHE});
});
self.addEventListener('activate',event=>event.waitUntil(self.clients.claim()));
async function fromCache(request){
  const cache=await caches.open(CACHE),cached=await cache.match(request);
  if(!cached)return fetch(request);
  const range=request.headers.get('Range');
  if(!range||!new URL(request.url).pathname.endsWith('.mp3'))return cached;
  const bytes=await cached.arrayBuffer(),match=/^bytes=(\d*)-(\d*)$/.exec(range);
  let start=match&&match[1]?Number(match[1]):0;
  let end=match&&match[2]?Number(match[2]):bytes.byteLength-1;
  if(match&&!match[1]&&match[2]){start=Math.max(0,bytes.byteLength-Number(match[2]));end=bytes.byteLength-1;}
  if(!match||start>end||start>=bytes.byteLength)return new Response(null,{status:416,headers:{'Content-Range':`bytes */${bytes.byteLength}`}});
  end=Math.min(end,bytes.byteLength-1);
  return new Response(bytes.slice(start,end+1),{status:206,headers:{'Content-Type':'audio/mpeg','Accept-Ranges':'bytes','Content-Range':`bytes ${start}-${end}/${bytes.byteLength}`,'Content-Length':String(end-start+1)}});
}
self.addEventListener('fetch',event=>{
  const request=event.request,url=new URL(request.url);
  if(request.method!=='GET'||url.origin!==ROOT.origin||!url.pathname.startsWith(ROOT.pathname))return;
  if(request.mode==='navigate'){
    event.respondWith(fetch(request,{cache:'no-cache'}).catch(async()=>{
      const cache=await caches.open(CACHE);
      return await cache.match(new URL('index.html',ROOT).href)||Response.error();
    }));return;
  }
  if(FILES.some(file=>new URL(file,ROOT).href===url.href))event.respondWith(fromCache(request));
});
