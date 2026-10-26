"""Losslessly encode new authoring images and append C03 sprite mappings.

The generated source PNGs stay intact. No image content editing or cropping is
performed: the existing browser renderer selects each square atlas cell.
"""
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from pathlib import Path
import subprocess
import sys
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
sources = json.loads(Path(sys.argv[1]).read_text())
assert [r['index'] for r in sources] == list(range(25))
words = [r for p in sorted((ROOT / 'data/school-learning').glob('0*.json'))
         for r in json.loads(p.read_text())['items']]
assert [i for r in sources for i in r['ids']] == [w['id'] for w in words]
def encode(row):
    source = Path(row['source'])
    destination = ROOT / f"assets/scenes/school-{row['index'] + 1:02}.webp"
    valid = False
    if destination.exists():
        try:
            with Image.open(source) as before, Image.open(destination) as after:
                valid = before.convert('RGBA').tobytes() == after.convert('RGBA').tobytes()
        except OSError:
            pass
    if not valid:
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', str(source),
                        '-c:v', 'libwebp', '-lossless', '1', '-compression_level', '6',
                        '-q:v', '100', '-pix_fmt', 'bgra', str(destination)], check=True)
    return row

with ThreadPoolExecutor(max_workers=4) as pool:
    list(pool.map(encode, sources))
sheets, scenes = [], []
for row in sources:
    source = Path(row['source'])
    destination = ROOT / f"assets/scenes/school-{row['index'] + 1:02}.webp"
    with Image.open(source) as before, Image.open(destination) as after:
        assert before.size == after.size
        assert before.convert('RGBA').tobytes() == after.convert('RGBA').tobytes()
        width, height = after.size
        assert abs(width / height - 2) < .015
        rgba_sha = hashlib.sha256(after.convert('RGBA').tobytes()).hexdigest()
    path = destination.relative_to(ROOT).as_posix()
    sheets.append({'path': path, 'columns': 4, 'rows': 2, 'width': width, 'height': height,
                   'sha256': hashlib.sha256(destination.read_bytes()).hexdigest(),
                   'sourcePng': source.name, 'sourceSha256': hashlib.sha256(source.read_bytes()).hexdigest(),
                   'rgbaSha256': rgba_sha, 'encoding': 'lossless WebP; decoded RGBA identical to generated PNG',
                   'prompt': row['prompt']})
    for offset, word_id in enumerate(row['ids']):
        w = next(w for w in words if w['id'] == word_id)
        scenes.append({'id': word_id, 'word': w['english'], 'example': w['example_en'],
                       'chinese': w['example_zh'], 'sheet': path, 'column': offset % 4,
                       'row': offset // 4, 'kind': 'school',
                       'description': '与词条及例句对应的学校场景，沿用首页人物。'})
path = ROOT / 'data/scene-catalog.json'
catalog = json.loads(path.read_text())
catalog['sheets'] = [r for r in catalog['sheets'] if not r['path'].startswith('assets/scenes/school-')] + sheets
catalog['scenes'] = [r for r in catalog['scenes'] if not r['id'].startswith('C03-')] + scenes
path.write_text(json.dumps(catalog, ensure_ascii=False, indent=2) + '\n')
(ROOT / 'reports/school-scene-source-sha256.json').write_text(json.dumps({'pack': 'school-learning-v1', 'sheets': sheets}, ensure_ascii=False, indent=2) + '\n')
print('Appended 198 distinct C03 scene cells in 25 lossless atlases; previous scenes unchanged.')
