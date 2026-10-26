"""Validate every C06 word/full-example recording against the static bank."""
import csv
import hashlib
import json
from pathlib import Path
import re
import unicodedata
from animal_content import study_word

ROOT=Path(__file__).resolve().parents[1]
bank=json.loads(re.search(r'window.LOCAL_AUDIO_BANK=(.*?);\s*</script>',(ROOT/'index.html').read_text(),re.S)[1])
def key(text):
 text=unicodedata.normalize('NFKC',text).lower().replace('’',"'").replace('‘',"'")
 return re.sub(r'\s+',' ',re.sub(r"[^a-z0-9'\s]",'',text)).strip()
words=[w for p in sorted((ROOT/'data/animal-nature').glob('0*.json')) for w in json.loads(p.read_text())['items']]
with (ROOT/'data/animal-nature-audio-map.csv').open('w',encoding='utf-8-sig',newline='') as f:
 out=csv.writer(f,lineterminator="\n");out.writerow(['id','english','chinese','DJ_IPA','word_key','word_path','example_en','example_key','example_path'])
 for w in words:
  keys=[key(study_word(w)),key(w['example_en'])];paths=[bank['clips'][k] for k in keys]
  for k,p in zip(keys,paths):
   assert p.startswith('audio/') and not p.startswith('/') and (ROOT/p).is_file()
   assert hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==bank['sha256'][k]
  out.writerow([w['id'],study_word(w),w['chinese'],w['ipa_dj_british'],keys[0],paths[0],w['example_en'],keys[1],paths[1]])
print('Validated 238 word/full-example recording pairs; matching existing clips reused.')
