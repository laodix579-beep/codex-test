"""Package static Pages files and supplied MP3 bytes; never generate audio."""
import hashlib
import json
import shutil
import sys
import zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
out=Path(sys.argv[1]) if len(sys.argv)>1 else Path('/workspace/output/xiaowa-pages-recordings.zip')
manifest=json.loads((ROOT/'audio-manifest.json').read_text())
audit=json.loads((ROOT/'reports/source-audio-sha256.json').read_text())
assert len(manifest['clips'])==610==len(audit)
for row in manifest['clips']:
 path=ROOT/row['path'];assert hashlib.sha256(path.read_bytes()).hexdigest()==audit[row['path']]['sha256']
assert len(list((ROOT/'audio').rglob('*.mp3')))==610
scenes=json.loads((ROOT/'data/scene-catalog.json').read_text())
assert len(scenes['scenes'])==136 and len(scenes['sheets'])==17
for sheet in scenes['sheets']:
 assert hashlib.sha256((ROOT/sheet['path']).read_bytes()).hexdigest()==sheet['sha256']
(ROOT/'小蛙自习室.html').write_bytes((ROOT/'index.html').read_bytes())
names=['.nojekyll','index.html','小蛙自习室.html','sw.js','audio-files.js','audio-manifest.json','vocabulary-audio-map.csv','pronunciation-test-words.csv','audio-source-report.csv','CODEX_只接入录音.md','README.md','DEPLOY_WINDOWS.md','AUDIO_CREDITS.md','manifest.webmanifest','supabase-config.js','icon-192.png','icon-512.png','apple-touch-icon.png']
files=[ROOT/n for n in names]
for directory in ['assets','audio','data','licenses','reports']:
 files.extend(p for p in (ROOT/directory).rglob('*') if p.is_file())
files.extend((ROOT/'tests').glob('*.py'));files.extend([Path(__file__).resolve(),ROOT/'tools/build_scene_assets.py',ROOT/'tools/scene-runtime.js'])
assert len(files)==len(set(files)) and all(f.is_file() for f in files)
out.parent.mkdir(parents=True,exist_ok=True)
with zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED) as z:
 for f in sorted(files):z.write(f,f.relative_to(ROOT).as_posix())
with zipfile.ZipFile(out) as z:
 assert z.testzip() is None
 assert len([n for n in z.namelist() if n.endswith('.mp3')])==610
 for row in manifest['clips']:
  assert hashlib.sha256(z.read(row['path'])).hexdigest()==audit[row['path']]['sha256']
 for sheet in scenes['sheets']:
  assert hashlib.sha256(z.read(sheet['path'])).hexdigest()==sheet['sha256']
shutil.copyfile(out,ROOT/'downloads/frog-study-offline.zip')
print(json.dumps({'zip':str(out),'bytes':out.stat().st_size,'files':len(files),'mp3':610,'sha256':hashlib.sha256(out.read_bytes()).hexdigest()},ensure_ascii=False))
