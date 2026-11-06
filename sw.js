// Same-origin shell + on-demand media. Never prefetch the entire library.
importScripts('./audio-files.js');
const CACHE='frog-static-v1',MEDIA=CACHE+'-media',ROOT=new URL('./',self.location.href);
const SHELL=['index.html','manifest.webmanifest','icon-192.png','icon-512.png','apple-touch-icon.png','assets/home-hero.webp','audio-files.js'];
self.addEventListener('install',event=>event.waitUntil((async()=>{
 const cache=await caches.open(CACHE);await cache.addAll(SHELL.map(path=>new Request(new URL(path,ROOT),{cache:'reload'})));await self.skipWaiting();
})()));
self.addEventListener('activate',event=>event.waitUntil((async()=>{
 for(const name of await caches.keys())if(name.startsWith('frog-')&&name!==CACHE&&name!==MEDIA)await caches.delete(name);
 await self.clients.claim();
})()));
self.addEventListener('message',event=>{if(event.data?.type==='FROG_CACHE_VERSION')event.ports[0]?.postMessage({cache:CACHE});});
async function valid(response,file){
 if(!response||response.status!==200)return false;
 const expected=self.FROG_AUDIO_HASHES[file];if(!expected)return true;
 const hash=Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',await response.clone().arrayBuffer())),n=>n.toString(16).padStart(2,'0')).join('');return hash===expected;
}
function ranged(response,range){
 if(!range)return response;
 return response.arrayBuffer().then(bytes=>{
  const m=/^bytes=(\d*)-(\d*)$/.exec(range);let a=m?.[1]?Number(m[1]):0,b=m?.[2]?Number(m[2]):bytes.byteLength-1;
  if(m&&!m[1]&&m[2]){a=Math.max(0,bytes.byteLength-Number(m[2]));b=bytes.byteLength-1;}
  if(!m||a>b||a>=bytes.byteLength)return new Response(null,{status:416,headers:{'Content-Range':`bytes */${bytes.byteLength}`}});
  b=Math.min(b,bytes.byteLength-1);return new Response(bytes.slice(a,b+1),{status:206,headers:{'Content-Type':'audio/mpeg','Accept-Ranges':'bytes','Content-Range':`bytes ${a}-${b}/${bytes.byteLength}`,'Content-Length':String(b-a+1)}});
 });
}
self.addEventListener('fetch',event=>{
 const request=event.request,url=new URL(request.url);
 if(request.method!=='GET'||url.origin!==ROOT.origin||!url.pathname.startsWith(ROOT.pathname))return;
 const relative=decodeURIComponent(url.pathname.slice(ROOT.pathname.length));
 if(request.mode==='navigate'||SHELL.includes(relative)){
  const file=request.mode==='navigate'?'index.html':relative;
  event.respondWith((async()=>{
   const cache=await caches.open(CACHE);
   try{const response=await fetch(request);if(response.ok)await cache.put(new URL(file,ROOT),response.clone());return response;}
   catch{return await cache.match(new URL(file,ROOT))||Response.error();}
  })());return;
 }
 if(!relative.startsWith('assets/')&&!self.FROG_AUDIO_HASHES[relative])return;
 event.respondWith((async()=>{
  const cache=await caches.open(MEDIA);let response=await cache.match(url.href);
  if(!await valid(response,relative)||request.cache==='reload'){
   response=await fetch(new Request(url.href,{cache:request.cache==='reload'?'reload':'default'}));
   if(!response.ok)return response;
   if(!await valid(response,relative))return Response.error();
   try{await cache.put(url.href,response.clone());const keys=await cache.keys();for(const old of keys.slice(0,Math.max(0,keys.length-160)))await cache.delete(old);}catch{/* Storage pressure must not stop online learning. */}
  }
  return self.FROG_AUDIO_HASHES[relative]?ranged(response,request.headers.get('Range')):response;
 })());
});
