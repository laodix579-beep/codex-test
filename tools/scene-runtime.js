/* Generated scene atlases are displayed intact; exact quantities are UI overlays. */
(() => {
  'use strict';
  const library=window.FROG_SCENE_LIBRARY;
  const clean=value=>String(value||'').trim().toLowerCase().replace(/[’]/g,"'").replace(/\s+/g,' ').replace(/[.!?]+$/,'');
  const escape=value=>String(value).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const byId=new Map(library.scenes.map(scene=>[scene.id,scene]));
  const byText=new Map(library.scenes.map(scene=>[clean(scene.word)+'\n'+clean(scene.example),scene]));
  const sheets=new Map(library.sheets.map(sheet=>[sheet.path,sheet]));
  function match(item) {
    if(!item)return null;
    const word=clean(item.word||item.english),example=clean(item.example||item.cloze?.english);
    const exact=byId.get(item.id);
    return exact&&clean(exact.word)===word&&clean(exact.example)===example?exact:byText.get(word+'\n'+example)||null;
  }
  const text=(x,y,value,size=70,color='#5d5270')=>`<text x="${x}" y="${y}" text-anchor="middle" dominant-baseline="middle" font-family="Segoe UI,Arial,sans-serif" font-size="${size}" font-weight="700" fill="${color}">${escape(value)}</text>`;
  const emoji=(x,y,value,size=80)=>`<text x="${x}" y="${y}" text-anchor="middle" dominant-baseline="central" font-family="Apple Color Emoji,Noto Color Emoji,Segoe UI Emoji,sans-serif" font-size="${size}" fill="#4d4658">${value}</text>`;
  function objects(count,object,{x=590,y=535,width=600,height=440,columns=0}={}) {
    if(!count)return '<ellipse cx="590" cy="555" rx="185" ry="60" fill="#ede6f5" stroke="#d5c5df" stroke-width="8"/><ellipse cx="590" cy="550" rx="148" ry="36" fill="#fffdf5"/>';
    const cols=columns||Math.min(10,Math.ceil(Math.sqrt(count*1.2))),rows=Math.ceil(count/cols);
    const step=Math.min(width/cols,height/rows,175),size=Math.min(step*.83,160);
    return Array.from({length:count},(_,i)=>{
      const row=Math.floor(i/cols),inRow=Math.min(cols,count-row*cols),px=x+(i%cols-(inRow-1)/2)*step,py=y+(row-(rows-1)/2)*step;
      return `<g data-count-item="${i+1}">${emoji(px,py,object,size)}</g>`;
    }).join('');
  }
  function glass(x,fill,color='#9adcf7',width=140,height=250,box=false) {
    const top=700-height;
    if(box)return `<rect x="${x-width/2}" y="${top}" width="${width}" height="${height}" rx="12" fill="#eefbff" stroke="#80abc2" stroke-width="6"/><rect x="${x-width/2+7}" y="${700-height*fill}" width="${width-14}" height="${height*fill-7}" rx="5" fill="${color}"/>`;
    return `<path d="M${x-width/2} ${top}h${width}l-15 ${height}h${30-width}Z" fill="#eefbff" stroke="#80abc2" stroke-width="6"/><path d="M${x-width/2+8+15*(1-fill)} ${700-height*fill}h${width-16-30*(1-fill)}l-${15*fill} ${height*fill-7}h${30-width+16}Z" fill="${color}" opacity=".9"/>`;
  }
  function fingerHands() {
    return [410,735].map(cx=>`<g><rect x="${cx-75}" y="490" width="150" height="175" rx="65" fill="#ffcfaa" stroke="#d79b76" stroke-width="6"/>${[-55,-17,22,59].map((dx,i)=>`<g data-count-item="finger"><rect x="${cx+dx-15}" y="${330+[25,0,12,45][i]}" width="31" height="210" rx="16" fill="#ffcfaa" stroke="#d79b76" stroke-width="5"/></g>`).join('')}<g data-count-item="finger"><rect x="${cx-125}" y="500" width="40" height="130" rx="20" transform="rotate(-35 ${cx-100} 565)" fill="#ffcfaa" stroke="#d79b76" stroke-width="5"/></g></g>`).join('');
  }
  function calendar() {
    return '<rect x="300" y="280" width="580" height="440" rx="24" fill="white" stroke="#c1b0e7" stroke-width="8"/><path d="M300 355h580" stroke="#c1b0e7" stroke-width="6"/>'+text(590,320,'2',65,'#ae78d6')+Array.from({length:28},(_,i)=>`<g data-count-item="${i+1}">${text(347+(i%7)*81,407+Math.floor(i/7)*84,i+1,34,'#6d6a86')}</g>`).join('');
  }
  function ordinal(value,kind='box') {
    return [1,2,3].map((n,i)=>{
      const x=370+i*220,color=n===value?'#75b8fa':'#e8dcbf';
      return `<g data-count-item="${n}"><rect x="${x-80}" y="410" width="160" height="180" rx="15" fill="${color}" stroke="${n===value?'#5d92c9':'#baa88c'}" stroke-width="6"/>${kind==='book'?`<path d="M${x-53} 415v170M${x-48} 568h115" stroke="#fff9eb" stroke-width="8"/>`:''}${text(x,500,n,76,n===value?'white':'#a99b85')}${n===value?text(x,350,kind==='answer'?'✓':'↓',90,kind==='answer'?'#58b28c':'#9b75ee'):''}</g>`;
    }).join('');
  }
  function quantity(visual) {
    let body='';
    switch(visual.type){
      case 'count':body=text(590,225,visual.value,108,'#8c6cc6')+objects(visual.value,visual.object);break;
      case 'fingers':body=text(590,225,'10',108,'#8c6cc6')+fingerHands();break;
      case 'calendar':body=text(590,210,'28',100,'#8c6cc6')+calendar();break;
      case 'clock':body=`<circle cx="590" cy="510" r="172" fill="#f3f0ff" stroke="#a18acb" stroke-width="12"/>${Array.from({length:60},(_,i)=>{const a=i*Math.PI/30;return `<path data-count-item="${i+1}" d="M${590+Math.sin(a)*150} ${510-Math.cos(a)*150}l${Math.sin(a)*(i%5===0?-18:-8)} ${Math.cos(a)*(i%5===0?18:8)}" stroke="#8e77b3" stroke-width="4"/>`;}).join('')}<path d="M590 375v135l75 35" fill="none" stroke="#ffb253" stroke-width="12" stroke-linecap="round"/>${text(590,230,'60',100,'#8c6cc6')}${text(590,770,'60 s → 1 min',55,'#8d87a3')}`;break;
      case 'comparison':body=text(590,470,'70 > 60',110,'#8c6cc6')+emoji(590,660,'⚖️',160);break;
      case 'numeral':body=emoji(590,660,'🔢',160)+text(590,440,'80',220,'#8c6cc6');break;
      case 'difference':body=text(590,420,'100 − 10',94,'#8c6cc6')+text(590,610,'= 90',140,'#ebac54');break;
      case 'number':body=emoji(590,550,'🎟️',270)+text(590,220,'7',110,'#8c6cc6');break;
      case 'sequence':body=Array.from({length:10},(_,i)=>`<g data-count-item="${i+1}"><circle cx="${380+i%5*105}" cy="${430+Math.floor(i/5)*170}" r="43" fill="${i%2?'#f5d7ae':'#d7cdf5'}"/>${text(380+i%5*105,430+Math.floor(i/5)*170,i+1,47)}</g>`).join('')+text(590,220,'1 → 10',85,'#8c6cc6');break;
      case 'howmany':body=text(590,225,'?',120,'#8c6cc6')+objects(3,'📕');break;
      case 'howmuch':body=text(590,225,'?',120,'#8c6cc6')+glass(590,.55);break;
      case 'many':body=objects(12,'🧸');break;
      case 'much':body=emoji(590,490,'⏳',250)+text(590,755,'…',90,'#c68a78');break;
      case 'more':body=glass(420,.25,'#fff6d7')+glass(765,.85,'#fff6d7')+text(590,480,'→',100,'#b398e2')+emoji(590,240,'🥛',110);break;
      case 'less':body=glass(420,.25,'#9adcf7',170,250,true)+glass(765,.8,'#9adcf7',170,250,true)+text(590,480,'<',110,'#b398e2');break;
      case 'some':body=objects(4,'✏️');break;
      case 'any':body=emoji(590,530,'🙋',220)+text(590,235,'?',110,'#8c6cc6');break;
      case 'all':body=objects(4,'🧒')+text(590,235,'✓',110,'#58b28c');break;
      case 'half':body='<path d="M590 350a180 180 0 0 1 0 360Z" fill="#fff0c1" stroke="#e16d64" stroke-width="16"/><path d="M590 350v360" stroke="#edaa7b" stroke-width="8"/><ellipse cx="622" cy="530" rx="11" ry="24" fill="#815f50"/>'+text(590,225,'½',110,'#8c6cc6');break;
      case 'first':body=ordinal(1,'book');break;
      case 'second':body=ordinal(2,'answer');break;
      case 'third':body=ordinal(3);break;
      case 'each':body=[0,1,2,3].map(i=>`<g data-count-item="${i+1}">${emoji(370+i%2*390,375+Math.floor(i/2)*280,'🧒',130)}${emoji(455+i%2*390,430+Math.floor(i/2)*280,'📖',90)}</g>`).join('');break;
      case 'every':body=emoji(590,310,'📖',150)+Array.from({length:7},(_,i)=>`<g data-count-item="${i+1}"><rect x="${320+i%4*150}" y="${485+Math.floor(i/4)*160}" width="115" height="120" rx="15" fill="#e9e1fb"/>${text(378+i%4*150,545+Math.floor(i/4)*160,'✓',65,'#64b08c')}</g>`).join('');break;
      case 'alot':body=objects(30,'📕');break;
      case 'few':body=objects(12,'🪑')+emoji(385,370,'🧒',95)+emoji(790,650,'🧒',95);break;
      case 'afew':body=objects(3,'🧸');break;
      case 'little':body=glass(590,.1,'#fff6d7');break;
      case 'alittle':body=glass(590,.22);break;
      case 'enough':body=[0,1,2,3].map(i=>`<g data-count-item="${i+1}">${emoji(370+i%2*390,410+Math.floor(i/2)*260,'🪑',130)}${emoji(370+i%2*390,350+Math.floor(i/2)*260,'🧒',110)}</g>`).join('')+text(590,210,'✓',90,'#58b28c');break;
      case 'total':body=objects(10,'🔵',{y:470,height:340,columns:5})+text(590,740,'5 + 5 = 10',73,'#8c6cc6');break;
    }
    return `<svg class="scene-quantity" viewBox="0 0 1000 1000" preserveAspectRatio="none" aria-hidden="true" data-quantity-type="${visual.type}"${visual.value!==undefined?` data-quantity-value="${visual.value}"`:''}><g transform="translate(145 60) scale(.85)"><rect x="245" y="120" width="710" height="760" rx="33" fill="#fffaf1" stroke="#e5d6bb" stroke-width="6"/>${body}</g></svg>`;
  }
  function art(item) {
    const scene=match(item);
    if(!scene)return '<div class="scene-unavailable"><span aria-hidden="true">📖</span><small>暂无对应场景图</small></div>';
    const sheet=sheets.get(scene.sheet),src=window.FROG_SCENE_IMAGES?.[scene.sheet]||new URL(scene.sheet,document.baseURI).href;
    const ratio=(sheet.width/sheet.columns)/(sheet.height/sheet.rows);
    return `<div class="scene-art-stage" data-scene-id="${scene.id}"><div class="scene-tile" style="--scene-aspect:${ratio}"><img src="${escape(src)}" alt="" draggable="false" decoding="async" data-scene-sheet="${escape(scene.sheet)}" style="transform:translate(-${scene.column*25}%,-${scene.row*50}%)"/>${scene.visual?quantity(scene.visual):''}</div></div>`;
  }
  function picture(item) {
    const scene=match(item);
    return `<div class="translation-picture scene-picture" data-scene-id="${scene?.id||''}" role="img" aria-label="${escape(scene?.chinese||'暂无对应场景图')}">${art(item)}</div>`;
  }
  window.FrogScenes={match,art,picture};
})();
