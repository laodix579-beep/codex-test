"""Review Chinese alignments and balanced sections for the C07 source pack."""
import json,pathlib,re
R=pathlib.Path(__file__).resolve().parents[1]
words=[w for p in sorted((R/'data/travel-social').glob('0*.json')) for w in json.loads(p.read_text())['items']]
def ids(s,ns):return [f'C07-S{s:02}-{n:03}' for n in ns]
def group(key,name,s,ns):return {'id':key,'name':name,'wordIds':ids(s,ns)}
sections=[{'subcategoryId':'C07-S01','groups':[
 group('vehicles','陆海空交通工具',1,range(1,25)),
 group('journey-safety','车站出行与交通安全',1,range(25,47)),
 group('directions-relations','方向指引与相对位置',3,range(1,20)),
 group('spaces-routes','空间位置与路线',3,range(20,40))]},
 {'subcategoryId':'C07-S02','groups':[]},
 {'subcategoryId':'C07-S03','groups':[]},
 {'subcategoryId':'C07-S04','groups':[]}]
public=[1,2,3,4,5,6,9,10,11,12,13,14,15,16,17,31,33,36,38,39]
sections[1]['groups']=[group('civic-services','城市空间与公共服务',2,public),group('leisure-transport','购物休闲与交通场所',2,[i for i in range(1,40) if i not in public])]
jobs=[1,2,3,4,5,6,7,8,9,16,17,29,30,31,45]
services=[10,11,12,13,14,15,18,19,20,21,22,23,24,25,26,27,28,32]
sections[2]['groups']=[group('public-service-jobs','教育医疗与公共服务职业',4,jobs),group('practical-jobs','餐饮运输与建筑技能',4,services),group('creative-technical-jobs','文艺科技与办公室工作',4,[i for i in range(1,46) if i not in jobs+services])]
sections[3]['groups']=[group('goods-clothing','购物用品与试穿选购',5,[*range(1,9),*range(38,45)]),group('money-payment','货币票据与支付工具',5,[*range(9,23),47,48]),group('transactions-services','买卖优惠与购物服务',5,[*range(23,38),45,46,49])]
(R/'data/travel-social-practice-sections.json').write_text(json.dumps({'pack':'travel-social-v1','groupSizePolicy':{'min':10,'max':25},'subcategories':sections},ensure_ascii=False,indent=2)+'\n')
overrides={'C07-S01-026':['公交车站'],'C07-S01-038':['马路'],'C07-S01-039':['街'],'C07-S01-046':['堵车'],
'C07-S03-004':['直走'],'C07-S03-007':['一直往前走'],'C07-S03-012':['附近'],'C07-S03-013':['远'],'C07-S03-015':['旁边'],'C07-S03-016':['之间'],'C07-S03-017':['对面'],'C07-S03-018':['前面'],'C07-S03-019':['后面'],'C07-S03-020':['上方'],'C07-S03-021':['下方'],'C07-S03-022':['下面'],'C07-S03-023':['飞过','上空'],'C07-S03-024':['里面'],'C07-S03-028':['对面'],'C07-S03-030':['尽头'],
'C07-S04-002':['上班'],'C07-S04-003':['老师'],'C07-S05-008':['件商品'],'C07-S05-009':['多少钱'],'C07-S05-010':['要多少钱'],'C07-S05-023':['打折'],'C07-S05-024':['打九折'],'C07-S05-025':['便宜'],'C07-S05-026':['太贵'],'C07-S05-030':['花'],'C07-S05-031':['存'],'C07-S05-032':['借'],'C07-S05-033':['借给'],'C07-S05-042':['鞋']}
usage={'C07-S05-045':'delivery 在本句中指货物的配送；中文用“货物明天送到”表达配送到达，通常不再单独加上“配送”二字。请结合完整例句理解。'}
notes={'C07-S02-021':'源词 café 带重音符号 é；练习时填写完整的 café，保留该词写法与例句。',
'C07-S05-048':'penny 的复数可用 pence，源例句使用 pence。本题沿用原有词条拼写练习，填写 penny；例句中保留 pence。',
'C07-S03-023':'本句中 over 与 flew 一起表示“飞过……上空”；中文高亮两处共同表达空间关系。',
'C07-S05-009':'price 在问价句中，中文自然表达为“多少钱”，不是把 price 的每个字直译。',
'C07-S05-010':'cost 在本句作动词，问句 how much does it cost 整体问“要多少钱”。',
'C07-S05-024':'a ten per cent discount 表示减价百分之十，即打九折。',
'C07-S04-033':'本句中文“美发师”对应 hairdresser，区别于常指男士理发的 barber。'}
for w in words:
 if any(t in w['chinese'] for t in ['英式','英镑','便士']):notes.setdefault(w['id'],'保留源词及 DJ 英式音标；录音使用 GA 美式读音，不替换词条或英国文化中的货币单位。')
entries=[]
for w in words:
 candidates=[re.sub(r'[（(].*?[)）]','',s).strip(' 。！？；') for s in re.split('[；;]',w['chinese'])]
 matches=sorted((s for s in candidates if s and s in w['example_zh']),key=len,reverse=True)
 targets=overrides.get(w['id'],matches[:1]);spans=[];cursor=0
 if w['id'] not in usage:
  assert targets,(w['id'],w['chinese'],w['example_zh'])
  for text in targets:
   start=w['example_zh'].index(text,cursor);spans.append({'start':start,'end':start+len(text),'text':text});cursor=start+len(text)
 entries.append({'id':w['id'],'word':w['english'],'meaning':w['chinese'],'english':w['example_en'],'chinese':w['example_zh'],'mode':'aligned' if spans else 'usage','spans':spans,'usage':usage.get(w['id'],''),'note':notes.get(w['id'],'')})
p=R/'data/meaning-catalog.json';d=json.loads(p.read_text());d['entries']=[e for e in d['entries'] if not e['id'].startswith('C07-')]+entries;p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
p=R/'data/practice-groups.json';d=json.loads(p.read_text());d['subcategories']=[s for s in d['subcategories'] if not s['subcategoryId'].startswith('C07-')]+sections;p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')

windows={d['window_id']:d for p in sorted((R/'data/travel-social').glob('0*.json')) for d in [json.loads(p.read_text())]}
for section in sections:
    window=windows['C07-W'+section['subcategoryId'][-2:]]
    expected={w['id'] for w in window['items']}
    actual=[i for g in section['groups'] for i in g['wordIds']]
    assert len(actual)==len(set(actual)) and set(actual)==expected
    assert all(10<=len(g['wordIds'])<=25 for g in section['groups'])
print('Reviewed 218 Chinese targets and 12 balanced C07 practice sections.')
