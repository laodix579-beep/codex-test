/* Public loader. Contains no data service credentials or complete word bank. */
(() => {
  'use strict';
  const api = window.LAOK_DELIVERY.api;
  const loaded = new Set(), pending = new Map();
  let applying = () => {};
  let preferred='fetch';
  const attempts=[];
  function httpFailure(status) {
    const error=new Error(status===429?'请求较频繁，请稍后重试':'学习内容暂时无法加载，请稍后重试');error.status=status;return error;
  }
  function xhr(url, binary=false, signal=null) {
    return new Promise((resolve,reject)=>{
      const x=new XMLHttpRequest();x.open('GET',url);x.timeout=20000;if(binary)x.responseType='arraybuffer';
      const abort=()=>x.abort();
      const cleanup=()=>signal?.removeEventListener('abort',abort);
      x.onload=()=>{cleanup();if(x.status<200||x.status>=300){reject(httpFailure(x.status));return;}
        try{resolve(binary?{ok:true,status:x.status,arrayBuffer:async()=>x.response}:JSON.parse(x.responseText));}catch(error){reject(error);}};
      x.onerror=()=>{cleanup();reject(new TypeError('XHR network failure'));};
      x.ontimeout=x.onabort=()=>{cleanup();const e=new Error('连接超时');e.name='TimeoutError';reject(e);};
      if(signal?.aborted){abort();const e=new Error('连接超时');e.name='TimeoutError';reject(e);return;}
      signal?.addEventListener('abort',abort,{once:true});x.send();
    });
  }
  function scriptData(path) {
    return new Promise((resolve,reject)=>{
      const key='__laok_data_'+Date.now().toString(36)+'_'+Math.random().toString(36).slice(2);
      const script=document.createElement('script');let done=false;
      const finish=(error,data)=>{if(done)return;done=true;clearTimeout(timer);script.remove();window[key]=()=>{};setTimeout(()=>delete window[key],60000);error?reject(error):resolve(data);};
      window[key]=data=>finish(null,data);
      const timer=setTimeout(()=>finish(new Error('备用连接超时，请检查网络后重试')),25000);
      script.onerror=()=>finish(new Error('备用连接未完成，请检查网络后重试'));
      script.onload=()=>{if(!done)finish(new Error('词库响应不完整，请重试'));};
      script.src=api+path+(path.includes('?')?'&':'?')+'callback='+key;
      document.head.append(script);
    });
  }
  function progress(mode) {
    const screen=document.querySelector('.startup-screen');if(!screen||!document.documentElement.classList.contains('app-booting'))return;
    let line=screen.querySelector('[data-connection-status]');
    if(!line){line=document.createElement('p');line.dataset.connectionStatus='';screen.append(line);}
    line.textContent=mode==='fetch'?'正在联网加载学习内容…':'正在尝试备用连接，请稍候…';
  }
  async function request(path) {
    const modes=[preferred,...['fetch','xhr','script'].filter(mode=>mode!==preferred)];
    for(const mode of modes){
      progress(mode);const started=Date.now();
      try{
        let data;
        if(mode==='script')data=await scriptData(path);
        else if(mode==='xhr')data=await xhr(api+path);
        else{
          const controller=new AbortController(),timer=setTimeout(()=>controller.abort(),12000);
          try{const response=await fetch(api+path,{cache:'no-store',signal:controller.signal});if(!response.ok)throw httpFailure(response.status);data=await response.json();}finally{clearTimeout(timer);}
        }
        if(!data||typeof data!=='object'||(path==='/catalog'&&(!Array.isArray(data.catalog?.words)||!Array.isArray(data.catalog?.categories)))||(path.startsWith('/window/')&&!Array.isArray(data.words)))throw new Error('词库响应格式不正确');
        preferred=mode;return data;
      }catch(error){
        attempts.push({path:path.split('?')[0],transport:mode,name:error.name,status:error.status||null,milliseconds:Date.now()-started});
        if(error.status||error instanceof SyntaxError)throw error;
      }
    }
    throw new Error('暂时无法连接词库，请重试。学习记录仍保留在当前浏览器。');
  }
  function mergeRows(target, rows, key = 'id') {
    const map = new Map(target.map(row => [row[key], row]));
    for (const row of rows) map.set(row[key], row);
    target.splice(0, target.length, ...map.values());
  }
  function apply(bundle) {
    mergeRows(window.FROG_WORD_CATALOG.words, bundle.words);
    mergeRows(window.FROG_MEANING_LIBRARY.entries, bundle.meanings);
    mergeRows(window.FROG_SCENE_LIBRARY.scenes, bundle.scenes);
    mergeRows(window.FROG_SCENE_LIBRARY.sheets, bundle.sheets, 'path');
    mergeRows(window.FROG_PRONUNCIATION_GUIDE.words, bundle.guideWords, 'word');
    Object.assign(window.FROG_SCENE_IMAGES, bundle.images);
    for (const field of ['clips','texts','sha256','styles','intonations']) Object.assign(window.LOCAL_AUDIO_BANK[field], bundle.audio[field]);
    applying(bundle);
  }
  const delivery = window.FrogDelivery = {
    loaded,
    get transport(){return preferred;},
    async fetchMedia(url,options){
      if(preferred==='script')throw new TypeError('Use native media transport');
      if(preferred==='xhr')return xhr(url,true,options?.signal);
      try{return await fetch(url,options);}catch(error){if(error instanceof TypeError)return xhr(url,true,options?.signal);throw error;}
    },
    onApply(callback) { applying = callback; },
    async window(id) {
      if (loaded.has(id)) return;
      if (!pending.has(id)) pending.set(id, request('/window/' + encodeURIComponent(id)).then(bundle => {apply(bundle);loaded.add(id);}).finally(() => pending.delete(id)));
      return pending.get(id);
    },
    async search(query) { const bundle=await request('/search?q=' + encodeURIComponent(query)); apply(bundle); return bundle.words.map(w=>w.id); },
  };
  function failure(error) {
    window.FrogStartup?.complete();
    const screen=document.getElementById('content');
    screen.replaceChildren();
    const title=document.createElement('h1');title.textContent='学习内容暂时无法连接';
    const text=document.createElement('p');text.textContent=error.message+'。已有学习记录不会被清除。';
    const retry=document.createElement('button');retry.className='button primary';retry.textContent='重新加载';retry.onclick=()=>location.reload();
    const detail=document.createElement('details'),summary=document.createElement('summary'),pre=document.createElement('pre');summary.textContent='连接详情';pre.style.whiteSpace='pre-wrap';pre.textContent=JSON.stringify({origin:location.origin,attempts},null,2);detail.append(summary,pre);
    screen.append(title,text,retry,detail);screen.setAttribute('role','alert');screen.setAttribute('data-connection-failure','');screen.style.pointerEvents='auto';
  }
  async function boot() {
    try {
      const data=await request('/catalog');
      window.FROG_WORD_CATALOG=data.catalog;
      window.FROG_PRACTICE_GROUPS=data.groups;
      window.FROG_CATEGORY_ART=data.categories;
      window.FROG_CATEGORY_IMAGES=data.categoryImages;
      window.FROG_HOME_ART=data.hero;
      window.FROG_SCENE_IMAGES={};
      window.FROG_MEANING_LIBRARY={entries:[]};
      window.FROG_SCENE_LIBRARY={scenes:[],sheets:[]};
      window.LOCAL_AUDIO_BANK=data.audio;
      window.FROG_PRONUNCIATION_GUIDE=data.guide;
      // These routes were retired in the original application; retain identifiers
      // needed to validate old backups without shipping old sample collections.
      window.LOCAL_SAMPLES={courses:[],words:[],phonetics:[]};
      window.LOCAL_TEXTBOOK={id:'pep-g1-upper-local',sections:[]};
      for(const script of document.querySelectorAll('script[data-online-runtime]')) (0,eval)(script.textContent);
      document.addEventListener('error',event=>{
        if(event.target instanceof HTMLImageElement){
          event.target.alt='图片加载失败，请联网后重新打开本题';
          const toast=document.getElementById('toast');
          toast.textContent='图片加载失败，请检查网络后重新打开本题';toast.hidden=false;
        }
      },true);
    } catch(error) {failure(error);}
  }
  boot();
})();
