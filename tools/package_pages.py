"""Package static Pages files and supplied MP3 bytes; never generate audio."""
import hashlib
import json
import re
import sys
import zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
out=Path(sys.argv[1]) if len(sys.argv)>1 else Path('/workspace/output/xiaowa-pages-recordings.zip')
manifest=json.loads((ROOT/'audio-manifest.json').read_text())
audit=json.loads((ROOT/'reports/all-audio-sha256.json').read_text())
original=json.loads((ROOT/'reports/source-audio-sha256.json').read_text())
assert len(original)==610 and all(audit[p]['sha256']==r['sha256'] for p,r in original.items())
assert len(manifest['clips'])==len(audit)
for row in manifest['clips']:
 path=ROOT/row['path'];assert hashlib.sha256(path.read_bytes()).hexdigest()==row['sha256']==audit[row['path']]['sha256']
assert len(list((ROOT/'audio').rglob('*.mp3')))==len(audit)
scenes=json.loads((ROOT/'data/scene-catalog.json').read_text())
assert len(scenes['scenes'])==1210 and len(scenes['sheets'])==140
for sheet in scenes['sheets']:
 assert hashlib.sha256((ROOT/sheet['path']).read_bytes()).hexdigest()==sheet['sha256']
meanings=json.loads((ROOT/'data/meaning-catalog.json').read_text())
embedded=re.search(r'window.FROG_MEANING_LIBRARY=(.*?);\s*</script>',(ROOT/'index.html').read_text(),re.S)
assert len(meanings['entries'])==1210 and embedded and json.loads(embedded[1])==meanings
groups=json.loads((ROOT/'data/practice-groups.json').read_text())
embedded_groups=re.search(r'window.FROG_PRACTICE_GROUPS=(.*?);\s*</script>',(ROOT/'index.html').read_text(),re.S)
assert embedded_groups and json.loads(embedded_groups[1])==groups
category_art=json.loads((ROOT/'data/category-art.json').read_text())
embedded_art=re.search(r'window.FROG_CATEGORY_ART=(.*?);\s*</script>',(ROOT/'index.html').read_text(),re.S)
assert embedded_art and json.loads(embedded_art[1])==category_art
assert len(category_art['entries'])==32 and len(category_art['sheets'])==4
for sheet in category_art['sheets']:
 assert hashlib.sha256((ROOT/sheet['path']).read_bytes()).hexdigest()==sheet['sha256']
(ROOT/'小蛙自习室.html').write_bytes((ROOT/'index.html').read_bytes())
names=['.nojekyll','index.html','小蛙自习室.html','sw.js','scene-files.js','category-files.js','audio-files.js','audio-manifest.json','vocabulary-audio-map.csv','pronunciation-test-words.csv','audio-source-report.csv','CODEX_只接入录音.md','README.md','DEPLOY_WINDOWS.md','AUDIO_CREDITS.md','manifest.webmanifest','supabase-config.js','icon-192.png','icon-512.png','apple-touch-icon.png']
files=[ROOT/n for n in names]
for directory in ['assets','audio','data','licenses','reports','downloads']:
 files.extend(p for p in (ROOT/directory).rglob('*') if p.is_file())
files.extend((ROOT/'tests').glob('*.py'))
files.extend((ROOT/'tools').glob('*.py'))
files.extend((ROOT/'tools').glob('*.js'))
assert len(files)==len(set(files)) and all(f.is_file() for f in files)
out.parent.mkdir(parents=True,exist_ok=True)
with zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
 for f in sorted(files):z.write(f,f.relative_to(ROOT).as_posix())
with zipfile.ZipFile(out) as z:
 assert z.testzip() is None
 assert len([n for n in z.namelist() if n.endswith('.mp3')])==len(audit)
 for row in manifest['clips']:
  assert hashlib.sha256(z.read(row['path'])).hexdigest()==audit[row['path']]['sha256']
 for sheet in scenes['sheets']:
  assert hashlib.sha256(z.read(sheet['path'])).hexdigest()==sheet['sha256']
 for sheet in category_art['sheets']:
  assert hashlib.sha256(z.read(sheet['path'])).hexdigest()==sheet['sha256']
# Public full-package downloads use GitHub's current gh-pages source archive.
# This flat review ZIP stays outside the repository and has no committed-blob limit.
print(json.dumps({'zip':str(out),'bytes':out.stat().st_size,'files':len(files),'mp3':len(audit),'sha256':hashlib.sha256(out.read_bytes()).hexdigest()},ensure_ascii=False))
