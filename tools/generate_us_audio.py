"""Build embedded US teaching audio using the model's English phoneme dictionary.

Optional authoring dependencies: kokoro-onnx==0.6.0, misaki-fork[en]==0.9.6,
en_core_web_sm==3.8.0 and ffmpeg. Model/voice release: AUDIO_CREDITS.md.
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
    Tokenizer()  # Configure the verified bundled eSpeak library for name fallback.
    g2p=en.G2P(british=False,fallback=espeak.EspeakFallback(british=False))
    plan=[]
    for key,text in prompts.items():
        text=re.sub(r'\bi\b','I',text)
        # Keep isolated words free of extra punctuation; sentences retain their original marks.
        synthesis=text
        phonemes,_=g2p(synthesis)
        if '❓' in phonemes or not phonemes.strip():
            raise ValueError(f'Unresolved pronunciation: {text}')
        assert normalize(text)==key
        plan.append({'key':key,'text':text,'phonemes':phonemes})
    return plan


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--model',type=Path,required=True)
    parser.add_argument('--voices',type=Path,required=True)
    parser.add_argument('--cache',type=Path,required=True)
    args=parser.parse_args()
    root=Path(__file__).resolve().parents[1]
    source=(root/'index.html').read_text()
    bank=json.loads(re.search(r'window.LOCAL_AUDIO_BANK=(.*?);\s*</script>',source,re.S).group(1))
    plan=make_plan(root,bank)
    config={'revision':'clear-us-dj-v4','engine':'Kokoro-82M v1.0 FP32',
        'voice':'af_bella','locale':'en-US','phonemizer':'Misaki-fork en-US 0.9.6',
        'speed':1.0,'sampleRate':24000,'bitrate':'96k','trim':True,
        'leadingPaddingSeconds':0.12,'trailingPaddingSeconds':0.18,
        'sourceRelease':'https://github.com/thewh1teagle/kokoro-onnx/releases/tag/model-files-v1.1',
        'files':{args.model.name:digest(args.model),args.voices.name:digest(args.voices)}}
    signature=hashlib.sha256(json.dumps(config,sort_keys=True).encode()).hexdigest()
    args.cache.mkdir(parents=True,exist_ok=True)
    (args.cache/'plan.json').write_text(json.dumps(plan,ensure_ascii=False,indent=2)+'\n')
    options=ort.SessionOptions();options.intra_op_num_threads=3;options.inter_op_num_threads=1
    session=ort.InferenceSession(str(args.model),sess_options=options,providers=['CPUExecutionProvider'])
    voice=Kokoro.from_session(session,str(args.voices))
    clips={};texts={};start=time.time()
    for number,row in enumerate(plan,1):
        # Include text, phonemes AND model/voice/encoding settings in cache identity.
        fingerprint=hashlib.sha256((signature+json.dumps(row,sort_keys=True)).encode()).hexdigest()
        target=args.cache/(fingerprint+'.mp3')
        if not target.exists():
            samples,rate=voice.create(row['phonemes'],voice=config['voice'],speed=1.0,is_phonemes=True,trim=True)
            assert rate==24000 and len(samples)>rate*.08 and np.isfinite(samples).all(),row['text']
            peak=float(np.abs(samples).max());assert peak>.01,row['text']
            samples=np.pad(samples,(int(rate*.12),int(rate*.18)))
            samples=samples*min(4.0,.88/peak)
            temporary=args.cache/'current.wav'
            with wave.open(str(temporary),'wb') as wav:
                wav.setnchannels(1);wav.setsampwidth(2);wav.setframerate(rate)
                wav.writeframes((np.clip(samples,-1,1)*32767).astype('<i2').tobytes())
            subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-y','-i',str(temporary),
                '-codec:a','libmp3lame','-b:a','96k',str(target)],check=True)
        clips[row['key']]=base64.b64encode(target.read_bytes()).decode()
        texts[row['key']]=row['text']
        if number%25==0:print(f'{number}/{len(plan)} clear US recordings ({time.time()-start:.0f}s)',flush=True)
    result={'voice':'Bella · 清晰美式英语','locale':'en-US','revision':config['revision'],
        'mime':'audio/mpeg','engine':config['engine'],'texts':texts,'clips':clips}
    replacement='<script data-embedded-audio="">\n/* Clear US recordings; DJ symbols are display references only. See AUDIO_CREDITS.md. */\nwindow.LOCAL_AUDIO_BANK='+json.dumps(result,ensure_ascii=False,separators=(',',':'))+';\n</script>'
    source=(root/'index.html').read_text()
    source=re.sub(r'<script data-embedded-audio="">.*?</script>',lambda _:replacement,source,count=1,flags=re.S)
    (root/'index.html').write_text(source)
    (root/'data/audio-generation.json').write_text(json.dumps({**config,'clipCount':len(plan),'generationSignature':signature},ensure_ascii=False,indent=2)+'\n')
    print(f'COMPLETE: {len(clips)} clear US recordings; {time.time()-start:.0f}s',flush=True)


if __name__=='__main__':
    main()
