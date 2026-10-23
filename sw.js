// Cache only this app's public static files. Learning data stays in localStorage.
const CACHE="frog-pep-ga-v7";
const ROOT=new URL('./',self.location.href);
const FILES=['index.html','manifest.webmanifest','icon-192.png','icon-512.png','apple-touch-icon.png'];
self.addEventListener('install',event=>event.waitUntil(
  caches.open(CACHE).then(cache=>cache.addAll(FILES.map(file=>new Request(new URL(file,ROOT).href,{cache:'reload'})))).then(()=>self.skipWaiting())
));
self.addEventListener('activate',event=>event.waitUntil((async()=>{
  // Old versions may still be serving open tabs, so retain them until the next upgrade.
  await self.clients.claim();
})()));
self.addEventListener('fetch',event=>{
  const request=event.request,url=new URL(request.url);
  if(request.method!=='GET'||url.origin!==ROOT.origin||!url.pathname.startsWith(ROOT.pathname))return;
  if(request.mode==='navigate'){
    event.respondWith(fetch(request).catch(async()=>{
      const cache=await caches.open(CACHE);
      return await cache.match(new URL('index.html',ROOT).href)||Response.error();
    }));
    return;
  }
  if(FILES.some(file=>new URL(file,ROOT).href===url.href))
    event.respondWith(caches.open(CACHE).then(async cache=>await cache.match(request)||fetch(request)));
});
