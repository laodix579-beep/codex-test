// Public static resources only; personal study data stays in localStorage.
importScripts('./audio-files.js','./scene-files.js','./category-files.js');
const CACHE="frog-food-groups-v40";
const ROOT=new URL('./',self.location.href);
const FILES=['index.html','assets/home-hero.png',...self.FROG_SCENE_FILES,...self.FROG_CATEGORY_FILES,'category-files.js','data/category-art.json','data/scene-catalog.json','data/meaning-catalog.json','data/practice-groups.json','data/catalog-packs.json','data/food-health-practice-sections.json','data/food-health-windows.json','data/food-health/index.json',...['01_水果与蔬菜.json','02_食物、主食与饮料.json','03_身体部位.json','04_健康与身体感受.json'].map(name=>'data/food-health/'+name),'data/family-daily/index.json',...['01_家庭成员.json','02_房间与家具.json','03_家居用品.json','04_日常生活与作息.json'].map(name=>'data/family-daily/'+name),'data/school-learning/index.json',...['01_学习用品.json','02_教室与校园.json','03_学科名称.json','04_课堂常用词.json'].map(name=>'data/school-learning/'+name),'data/time-nature/index.json',...['01_时间与钟表.json','02_星期与日期.json','03_月份与四季.json','04_天气与气候.json'].map(name=>'data/time-nature/'+name),'scene-files.js','audio-files.js','audio-manifest.json','data/pronunciation-test-words.json','manifest.webmanifest','icon-192.png','icon-512.png','apple-touch-icon.png',...self.FROG_AUDIO_FILES];
const FILE_URLS=new Map(FILES.map(file=>[new URL(file,ROOT).href,file]));
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
  const cache=await caches.open(CACHE),file=FILE_URLS.get(request.url);
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
  if(FILE_URLS.has(url.href))event.respondWith(fromCache(request));
});
