/* Public loader. Contains no data service credentials or complete word bank. */
(() => {
  'use strict';
  const api = window.LAOK_DELIVERY.api;
  const loaded = new Set(), pending = new Map();
  let applying = () => {};
  async function request(path) {
    const response = await fetch(api + path, {cache:'no-store', signal:AbortSignal.timeout(20000)});
    if (!response.ok) throw new Error(response.status === 429 ? '请求较频繁，请稍后重试' : '学习内容暂时无法加载，请检查网络后重试');
    return response.json();
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
    onApply(callback) { applying = callback; },
    async window(id) {
      if (loaded.has(id)) return;
      if (!pending.has(id)) pending.set(id, request('/window/' + encodeURIComponent(id)).then(bundle => {apply(bundle);loaded.add(id);}).finally(() => pending.delete(id)));
      return pending.get(id);
    },
    async search(query) { const bundle=await request('/search?q=' + encodeURIComponent(query)); apply(bundle); return bundle.words.map(w=>w.id); },
  };
  function failure(error) {
    document.documentElement.classList.add('app-booting');
    const screen=document.querySelector('.startup-screen') || document.getElementById('content');
    screen.replaceChildren();
    const text=document.createElement('p');text.textContent=error.message+'。已有学习记录不会被清除。';
    const retry=document.createElement('button');retry.className='button primary';retry.textContent='重新加载';retry.onclick=()=>location.reload();
    screen.append(text,retry);screen.style.pointerEvents='auto';
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
