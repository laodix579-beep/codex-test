// Immutable static assets + cached navigation first. No blocking audio manifest.
const CACHE="frog-static-fast-v3-c5000f0a42fb",MEDIA='frog-static-media-v2',ROOT=new URL('./',self.location.href),SHELL=["index.html", "runtime/styles.0c032bb585e03d071a68f176.css", "runtime/app.1bacd9f79efe112aa8155bce.js", "manifest.webmanifest", "icon-192.png", "icon-512.png", "apple-touch-icon.png"],APP="runtime/app.1bacd9f79efe112aa8155bce.js";
self.addEventListener('install',event=>event.waitUntil((async()=>{
 const cache=await caches.open(CACHE);
 // Default HTTP caching reuses resources already fetched for the first page.
 await cache.addAll(SHELL.map(path=>new Request(new URL(path,ROOT))));self.skipWaiting();
})()));
self.addEventListener('activate',event=>event.waitUntil((async()=>{
 const media=await caches.open(MEDIA);
 for(const name of await caches.keys()){
  if(name==='frog-static-v1-media'){
   const old=await caches.open(name);for(const request of await old.keys()){const response=await old.match(request);if(response)try{await media.put(request,response);}catch{}}
  }
  if(name.startsWith('frog-')&&name!==CACHE&&name!==MEDIA)await caches.delete(name);
 }
 await self.clients.claim();
})()));
self.addEventListener('message',event=>{if(event.data?.type==='FROG_CACHE_VERSION')event.ports[0]?.postMessage({cache:CACHE});if(event.data?.type==='FROG_ACTIVATE_UPDATE')self.skipWaiting();});
async function valid(response,url){
 if(!response||response.status!==200)return false;
 const expected=new URL(url).pathname.match(/\/([0-9a-f]{64})\.mp3$/)?.[1];if(!expected)return true;
 const hash=Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',await response.clone().arrayBuffer())),n=>n.toString(16).padStart(2,'0')).join('');return hash===expected;
}
async function ranged(response,range){
 if(!range)return response;
 const bytes=await response.arrayBuffer(),m=/^bytes=(\d*)-(\d*)$/.exec(range);let a=m?.[1]?Number(m[1]):0,b=m?.[2]?Number(m[2]):bytes.byteLength-1;
 if(m&&!m[1]&&m[2]){a=Math.max(0,bytes.byteLength-Number(m[2]));b=bytes.byteLength-1;}
 if(!m||a>b||a>=bytes.byteLength)return new Response(null,{status:416,headers:{'Content-Range':`bytes */${bytes.byteLength}`}});
 b=Math.min(b,bytes.byteLength-1);return new Response(bytes.slice(a,b+1),{status:206,headers:{'Content-Type':'audio/mpeg','Accept-Ranges':'bytes','Content-Range':`bytes ${a}-${b}/${bytes.byteLength}`,'Content-Length':String(b-a+1)}});
}
self.addEventListener('fetch',event=>{
 const request=event.request,url=new URL(request.url);
 if(request.method!=='GET'||url.origin!==ROOT.origin||!url.pathname.startsWith(ROOT.pathname))return;
 const relative=decodeURIComponent(url.pathname.slice(ROOT.pathname.length));
 if(request.mode==='navigate'){
  event.respondWith((async()=>{
   const cache=await caches.open(CACHE),key=new URL('index.html',ROOT);
   const cached=await cache.match(key);
   if(cached){
    event.waitUntil((async()=>{try{const response=await fetch(request,{cache:'no-cache'});if(response.ok){const html=await response.clone().text();if(html.includes(APP))await cache.put(key,response);}}catch{}})());
    return cached;
   }
   const response=await fetch(request);if(response.ok)await cache.put(key,response.clone());return response;
  })());return;
 }
 if(SHELL.includes(relative)){
  event.respondWith((async()=>{const cache=await caches.open(CACHE);const hit=await cache.match(url.href);if(hit)return hit;const response=await fetch(request);if(response.ok)await cache.put(url.href,response.clone());return response;})());return;
 }
 if(!relative.startsWith('assets/')&&!relative.startsWith('audio/')&&!relative.startsWith('runtime/'))return;
 event.respondWith((async()=>{
  const cache=await caches.open(MEDIA);let response=await cache.match(url.href);
  if(!await valid(response,url.href)||request.cache==='reload'){
   response=await fetch(new Request(url.href,{cache:request.cache==='reload'?'reload':'default'}));if(!response.ok)return response;
   if(!await valid(response,url.href))return Response.error();
   try{await cache.put(url.href,response.clone());const keys=await cache.keys();for(const old of keys.slice(0,Math.max(0,keys.length-160)))await cache.delete(old);}catch{}
  }
  return relative.startsWith('audio/')?ranged(response,request.headers.get('Range')):response;
 })());
});
