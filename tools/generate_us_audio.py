"""Regenerate the embedded US recordings (optional authoring tool).

Requires Python packages kokoro-onnx==0.4.9 and ffmpeg on PATH.
Use the model and voice files linked in AUDIO_CREDITS.md:
  python tools/generate_us_audio.py --model /path/kokoro-v1.0.int8.onnx \
      --voices /path/voices-v1.0.bin --cache /tmp/frog-us-audio
Model files and inference dependencies are not needed to run the website.
"""
import base64,hashlib,json,re,subprocess,time,wave
from pathlib import Path
import numpy as np
import onnxruntime as ort
from kokoro_onnx import Kokoro

import argparse
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--model',type=Path,required=True)
parser.add_argument('--voices',type=Path,required=True)
parser.add_argument('--cache',type=Path,required=True)
args=parser.parse_args()
root=Path(__file__).resolve().parents[1]
s=(root/'index.html').read_text()
bank=json.loads(re.search(r'window.LOCAL_AUDIO_BANK=(.*?);\s*</script>',s,re.S).group(1))
catalog=json.loads(re.search(r'window.FROG_WORD_CATALOG = (.*?);\n',s).group(1))
def normalize(t):
 import unicodedata
 t=unicodedata.normalize('NFKC',t).lower().replace('’',"'").replace('‘',"'")
 return re.sub(r'\s+',' ',re.sub(r"[^a-z0-9'\s]",'',t)).strip()
prompts={k:k for k in bank['clips']}
for w in catalog['words']:
 for text in [w['word'],w['example']]:
  if text:prompts[normalize(text)]=text
for text in ['father','teacher','Hello! Let us practice English together.']:
 prompts[normalize(text)]=text
cache=args.cache;cache.mkdir(exist_ok=True)
options=ort.SessionOptions();options.intra_op_num_threads=3;options.inter_op_num_threads=1
session=ort.InferenceSession(str(args.model),sess_options=options,providers=['CPUExecutionProvider'])
voice=Kokoro.from_session(session,str(args.voices))
clips={};start=time.time()
for n,(key,text) in enumerate(prompts.items(),1):
 path=cache/(hashlib.sha256(key.encode()).hexdigest()+'.mp3')
 if not path.exists():
  samples,rate=voice.create(text,voice='af_heart',speed=0.92,lang='en-us')
  assert len(samples)>rate*.08 and np.isfinite(samples).all() and float(np.abs(samples).max())>0.01,text
  wav=cache/'current.wav'
  with wave.open(str(wav),'wb') as f:
   f.setnchannels(1);f.setsampwidth(2);f.setframerate(rate);f.writeframes((np.clip(samples,-1,1)*32767).astype('<i2').tobytes())
  subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-y','-i',str(wav),'-codec:a','libmp3lame','-b:a','48k',str(path)],check=True)
 clips[key]=base64.b64encode(path.read_bytes()).decode()
 if n%25==0:print(f'{n}/{len(prompts)} US clips ({time.time()-start:.0f}s)',flush=True)
bank={'voice':'Kokoro Heart · 美式英语','locale':'en-US','mime':'audio/mpeg','engine':'Kokoro-82M v1.0 / af_heart / en-us','clips':clips}
replacement='<script data-embedded-audio="">\n/* US English prompts generated with Kokoro Heart; see AUDIO_CREDITS.md. */\nwindow.LOCAL_AUDIO_BANK='+json.dumps(bank,ensure_ascii=False,separators=(',',':'))+';\n</script>'
# Reload so independent edits to other scripts are preserved.
s=(root/'index.html').read_text()
s=re.sub(r'<script data-embedded-audio="">.*?</script>',lambda _:replacement,s,count=1,flags=re.S)
(root/'index.html').write_text(s)
print(f'COMPLETE {len(clips)} US audio clips, {time.time()-start:.0f}s',flush=True)
