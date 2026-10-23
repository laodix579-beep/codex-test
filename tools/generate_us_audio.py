"""Build GA audio: clear isolated words and natural connected sentences.

Optional authoring dependencies: kokoro-onnx==0.6.0, misaki-fork[en]==0.9.6,
en_core_web_sm==3.8.0, praat-parselmouth==0.4.7 and ffmpeg. Model/voice release: AUDIO_CREDITS.md.
  python tools/generate_us_audio.py --model /path/kokoro-v1.0.onnx \
      --voices /path/voices-v1.0.bin --cache /tmp/frog-clear-us
The website requires none of these packages or model files at runtime.
"""
import argparse
import base64
import hashlib
import json
from pathlib import Path
import re
import subprocess
import time
import unicodedata
import wave
import numpy as np
import onnxruntime as ort
from kokoro_onnx import Kokoro
from kokoro_onnx.tokenizer import Tokenizer
from misaki import en, espeak
from ga_intonation import PROSODY, terminal_contour


def normalize(text):
    text=unicodedata.normalize('NFKC',text).lower().replace('’',"'").replace('‘',"'")
    return re.sub(r'\s+',' ',re.sub(r"[^a-z0-9'\s]",'',text)).strip()


def digest(path):
    with path.open('rb') as source:
        return hashlib.file_digest(source,'sha256').hexdigest()


def make_plan(root,bank):
    # Read actual displayed wording, including punctuation and capitalization.
    js=r"""const fs=require('fs'),vm=require('vm');const s=fs.readFileSync('index.html','utf8');const code=[...s.matchAll(/<script[^>]*>([\s\S]*?)<\/script>/g)].find(m=>m[1].includes('window.FROG_WORD_CATALOG ='));const x={window:{}};vm.runInNewContext(code[1],x);process.stdout.write(JSON.stringify(x.window));"""
    source=json.loads(subprocess.check_output(['node','-e',js],cwd=root,text=True))
    prompts={key:bank.get('texts',{}).get(key,key) for key in bank['clips']}
    for course in source['LOCAL_SAMPLES']['courses']:
        for english,_ in course['sentences']:
            prompts[normalize(english)]=english
    for section in source['LOCAL_TEXTBOOK']['sections']:
        for row in section['items']:
            prompts[normalize(row['english'])]=row['english']
    for row in source['FROG_WORD_CATALOG']['words']:
        for text in [row['word'],row['example']]:
            if text:prompts[normalize(text)]=text
    for row in source['LOCAL_SAMPLES']['phonetics']:
        prompts[normalize(row[2])]=row[2]
    guide=source['FROG_PRONUNCIATION_GUIDE']
    references={row['audioKey']:row for row in guide['words']}
    for row in guide['words']:prompts[row['audioKey']]=row['word']
    for row in guide['sentences']:prompts[normalize(row['english'])]=row['english']
    Tokenizer()  # Configure the verified bundled eSpeak library for name fallback.
    g2p=en.G2P(british=False,fallback=espeak.EspeakFallback(british=False))
    plan=[]
    for key,text in prompts.items():
        text=re.sub(r'\bi\b','I',text)
        # Keep isolated words free of extra punctuation; sentences retain their original marks.
        synthesis=text
        phonemes,tokens=g2p(synthesis)
        if any(token.phonemes is None and re.search('[A-Za-z]',token.text) for token in tokens):
            raise ValueError(f'Unresolved word in pronunciation: {text}')
        # Use GA lexical decisions; DJ notation is never used as synthesis input.
        if key in references:phonemes=references[key]['gaPhonemes']
        else:
            for token in tokens:
                if token.text.lower() in ('dog','dogs') and token.phonemes:
                    token.phonemes=token.phonemes.replace('ɔ','ɑ')
            phonemes=''.join((token.phonemes or '')+token.whitespace for token in tokens)
        # Audit consonants in context without replacing sentence weak forms by
        # isolated, fully stressed word recordings.
        for token in tokens:
            name=token.text.lower();phones=(token.phonemes or '').rstrip('.!?,;:')
            if name in ('please','is','has','these'):assert phones.endswith('z'),(text,name,phones)
            if name=='pleased':assert phones.endswith('zd'),(text,phones)
            if name=='three':assert phones.startswith('θ'),(text,phones)
            if name in ('this','these'):assert phones.startswith('ð'),(text,phones)
            if name=='five':assert phones.endswith('v'),(text,phones)
            if name=='very':assert phones.startswith('v'),(text,phones)
        # The written DJ reference never controls GA synthesis. Process a full
        # sentence in one pass so its stress, reductions and linking retain context.
        words=re.findall(r"[A-Za-z]+(?:['’\-][A-Za-z]+)*",text)
        style='word' if len(words)==1 else 'sentence'
        if '❓' in phonemes or not phonemes.strip():
            raise ValueError(f'Unresolved pronunciation: {text}')
        assert normalize(text)==key.split('::')[0]
        question=text.strip().endswith('?')
        yesno=bool(re.match(r'^(am|is|are|was|were|do|does|did|can|could|will|would|shall|should|have|has|had|may|might|must)\b',text,re.I))
        intonation='rise' if question and yesno else 'fall' if style=='sentence' else 'neutral'
        plan.append({'key':key,'text':text,'phonemes':phonemes,'style':style,'intonation':intonation})
    return plan


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--model',type=Path,required=True)
    parser.add_argument('--voices',type=Path,required=True)
    parser.add_argument('--cache',type=Path,required=True)
    parser.add_argument('--reuse-cache',type=Path,help='Previous cache; reuse only identical phonemes and synthesis settings')
    parser.add_argument('--reuse-manifest',type=Path,help='Generation manifest belonging to the previous cache')
    args=parser.parse_args()
    root=Path(__file__).resolve().parents[1]
    source=(root/'index.html').read_text()
    bank=json.loads(re.search(r'window.LOCAL_AUDIO_BANK=(.*?);\s*</script>',source,re.S).group(1))
    plan=make_plan(root,bank)
    config={'revision':'pep-ga-v7','engine':'Kokoro-82M v1.0 FP32',
        'voice':'af_bella','voiceLocale':'en-US','locale':'en-US','pronunciation':'GA','phonemizer':'Misaki-fork en-US 0.9.6',
        'speed':1.0,'sampleRate':24000,'bitrate':'96k','trim':False,
        'profiles':{'word':{'speed':0.92,'delivery':'clear isolated word'},
            'sentence':{'speed':0.9,'bitrate':'128k','delivery':'elementary pace, contextual linking and punctuation-based intonation'}},
        'prosody':PROSODY,
        'leadingPaddingSeconds':0.12,'trailingPaddingSeconds':0.24,
        'sourceRelease':'https://github.com/thewh1teagle/kokoro-onnx/releases/tag/model-files-v1.1',
        'files':{args.model.name:digest(args.model),args.voices.name:digest(args.voices)}}
    signature=hashlib.sha256(json.dumps(config,sort_keys=True).encode()).hexdigest()
    reusable={}
    if args.reuse_cache:
        previous=json.loads((args.reuse_manifest or root/'data/audio-generation.json').read_text())
        physical=('engine','voice','speed','sampleRate','bitrate','trim',
            'leadingPaddingSeconds','trailingPaddingSeconds','files')
        if any(previous.get(k)!=config[k] for k in physical):
            raise ValueError('Previous cache uses different synthesis or encoding settings')
        for row in json.loads((args.reuse_cache/'plan.json').read_text()):
            old_hash=hashlib.sha256((previous['generationSignature']+json.dumps(row,sort_keys=True)).encode()).hexdigest()
            cached=args.reuse_cache/(old_hash+'.mp3')
            identity=json.dumps({k:row[k] for k in ('key','text','phonemes')},sort_keys=True)
            old_speed=previous.get('profiles',{}).get(row.get('style'),{}).get('speed',previous['speed'])
            if cached.exists():reusable[(identity,old_speed)]=cached
    args.cache.mkdir(parents=True,exist_ok=True)
    (args.cache/'plan.json').write_text(json.dumps(plan,ensure_ascii=False,indent=2)+'\n')
    (args.cache/'manifest.json').write_text(json.dumps({**config,'generationSignature':signature},indent=2)+'\n')
    options=ort.SessionOptions();options.intra_op_num_threads=3;options.inter_op_num_threads=1
    session=ort.InferenceSession(str(args.model),sess_options=options,providers=['CPUExecutionProvider'])
    voice=Kokoro.from_session(session,str(args.voices))
    clips={};texts={};start=time.time();reused=0
    for number,row in enumerate(plan,1):
        # Include text, phonemes AND model/voice/encoding settings in cache identity.
        fingerprint=hashlib.sha256((signature+json.dumps(row,sort_keys=True)).encode()).hexdigest()
        target=args.cache/(fingerprint+'.mp3')
        speed=config['profiles'][row['style']]['speed']
        reuse_identity=json.dumps({k:row[k] for k in ('key','text','phonemes')},sort_keys=True)
        previous_clip=reusable.get((reuse_identity,speed))
        can_reuse=bool(args.reuse_cache) and (row['style']=='word' or previous.get('prosody')==config['prosody'])
        if not target.exists() and previous_clip and can_reuse:
            target.write_bytes(previous_clip.read_bytes());reused+=1
        if not target.exists():
            samples,rate=voice.create(row['phonemes'],voice=config['voice'],speed=speed,is_phonemes=True,trim=False)
            assert rate==24000 and len(samples)>rate*.08 and np.isfinite(samples).all(),row['text']
            samples=terminal_contour(samples,rate,row['intonation'])
            peak=float(np.abs(samples).max());assert peak>.01,row['text']
            samples=np.pad(samples,(int(rate*.12),int(rate*.24)))
            samples=samples*min(4.0,.88/peak)
            temporary=args.cache/'current.wav'
            with wave.open(str(temporary),'wb') as wav:
                wav.setnchannels(1);wav.setsampwidth(2);wav.setframerate(rate)
                wav.writeframes((np.clip(samples,-1,1)*32767).astype('<i2').tobytes())
            subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-y','-i',str(temporary),
                '-codec:a','libmp3lame','-b:a',config['profiles'][row['style']].get('bitrate',config['bitrate']),str(target)],check=True)
        clips[row['key']]=base64.b64encode(target.read_bytes()).decode()
        texts[row['key']]=row['text']
        if number%25==0:print(f'{number}/{len(plan)} GA recordings; {reused} identical clips reused ({time.time()-start:.0f}s)',flush=True)
    result={'voice':'Bella · GA 美式英语','voiceLocale':'en-US','locale':'en-US','pronunciation':'GA','revision':config['revision'],
        'mime':'audio/mpeg','engine':config['engine'],'texts':texts,
        'profiles':config['profiles'],'styles':{row['key']:row['style'] for row in plan},
        'prosody':PROSODY,
        'intonations':{row['key']:row['intonation'] for row in plan},
        'phonemes':{row['key']:row['phonemes'] for row in plan},'clips':clips}
    replacement='<script data-embedded-audio="">\n/* GA audio; written DJ references are maintained separately. See AUDIO_CREDITS.md. */\nwindow.LOCAL_AUDIO_BANK='+json.dumps(result,ensure_ascii=False,separators=(',',':'))+';\n</script>'
    source=(root/'index.html').read_text()
    source=re.sub(r'<script data-embedded-audio="">.*?</script>',lambda _:replacement,source,count=1,flags=re.S)
    (root/'index.html').write_text(source)
    (root/'data/audio-generation.json').write_text(json.dumps({**config,'clipCount':len(plan),'generationSignature':signature},ensure_ascii=False,indent=2)+'\n')
    print(f'COMPLETE: {len(clips)} GA recordings; {reused} identical clips reused; {time.time()-start:.0f}s',flush=True)


if __name__=='__main__':
    main()
