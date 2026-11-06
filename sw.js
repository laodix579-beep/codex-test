// Cache only the Pages shell. Never bulk-fetch vocabulary, images, or audio.
const CACHE='frog-online-v2-network';
const ROOT=new URL('./',self.location.href);
const FILES=['index.html','delivery-client.js','delivery-config.js','manifest.webmanifest','icon-192.png','icon-512.png','apple-touch-icon.png'];
self.addEventListener('install',event=>event.waitUntil((async()=>{
  const cache=await caches.open(CACHE);
  await cache.addAll(FILES.map(path=>new Request(new URL(path,ROOT),{cache:'reload'})));
  await self.skipWaiting();
})()));
self.addEventListener('activate',event=>event.waitUntil((async()=>{
  // Old service workers previously cached the complete bank. Clear only this
  // application's caches; leave localStorage/IndexedDB and other apps untouched.
  for(const name of await caches.keys())if(name.startsWith('frog-')&&name!==CACHE)await caches.delete(name);
  await self.clients.claim();
})()));
self.addEventListener('message',event=>{
  if(event.data?.type==='FROG_CACHE_VERSION')event.ports[0]?.postMessage({cache:CACHE});
});
self.addEventListener('fetch',event=>{
  const url=new URL(event.request.url);
  if(url.origin!==ROOT.origin||event.request.method!=='GET')return;
  const relative=url.pathname.slice(ROOT.pathname.length);
  const file=event.request.mode==='navigate'?'index.html':relative;
  if(!FILES.includes(file))return;
  event.respondWith((async()=>{
    const cache=await caches.open(CACHE);
    try{
      const response=await fetch(event.request);
      if(response.ok)await cache.put(new URL(file,ROOT),response.clone());
      return response;
    }catch{
      return await cache.match(new URL(file,ROOT))||Response.error();
    }
  })());
});
