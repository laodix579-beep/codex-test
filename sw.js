// Public static resources only; personal study data stays in localStorage.
importScripts('./audio-files.js');
const CACHE="frog-meaning-definition-v29";
const ROOT=new URL('./',self.location.href);
const FILES=['index.html','assets/home-hero.png','assets/scenes/see-you-tomorrow.png','data/scene-catalog.json','data/meaning-catalog.json',...Array.from({length:17},(_,i)=>`assets/scenes/sheet-${String(i+1).padStart(2,'0')}.png`),'audio-files.js','audio-manifest.json','data/pronunciation-test-words.json','manifest.webmanifest','icon-192.png','icon-512.png','apple-touch-icon.png',...self.FROG_AUDIO_FILES];
self.addEventListener('install',event=>event.waitUntil((async()=>{
  const cache=await caches.open(CACHE);let next=0;
  const previous=await Promise.all((await caches.keys()).filter(name=>name.startsWith('frog-')&&name!==CACHE).reverse().map(name=>caches.open(name)));
  await Promise.all(Array.from({length:6},async()=>{
    while(next<FILES.length){
      const file=FILES[next++],request=new Request(new URL(file,ROOT).href,{cache:'reload'});
      let response;
      // Supplied MP3 bytes are immutable. Reuse only a complete, verified copy.
      if(self.FROG_AUDIO_HASHES[file])for(const old of [cache,...previous]){
        const candidate=await old.match(request.url);
        if(await validRecording(candidate,file)){response=candidate;break;}
      }
      if(!response)response=await fetch(request);
      if(!response.ok)throw new Error('An offline resource could not be downloaded.');
      if(self.FROG_AUDIO_HASHES[file]&&!await validRecording(response,file))throw new Error('An offline recording is incomplete.');
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
async function validRecording(response,file){
  if(!response||response.status!==200)return false;
  const hash=Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',await response.clone().arrayBuffer())),n=>n.toString(16).padStart(2,'0')).join('');
  return hash===self.FROG_AUDIO_HASHES[file];
}
async function fromCache(request){
  const cache=await caches.open(CACHE),file=FILES.find(file=>new URL(file,ROOT).href===request.url);
  let cached=await cache.match(request.url);
  if(self.FROG_AUDIO_HASHES[file]){
    if(request.cache==='reload'||!await validRecording(cached,file)){
      const response=await fetch(new Request(request.url,{cache:'reload'}));
      if(!await validRecording(response,file))return Response.error();
      await cache.put(request.url,response.clone());cached=response;
    }
  }else if(!cached)return fetch(request);
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
