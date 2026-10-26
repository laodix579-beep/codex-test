"""Append generated C02 recordings to the original immutable MP3 bank."""
import hashlib
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
source = (ROOT / 'index.html').read_text()
match = re.search(r'window.LOCAL_AUDIO_BANK=(.*?);\s*</script>', source, re.S)
bank = json.loads(match[1])
manifest = json.loads((ROOT / 'audio-manifest.json').read_text())
provided = json.loads((ROOT / 'reports/source-audio-sha256.json').read_text())
generation = json.loads((ROOT / 'data/time-nature-audio-generation.json').read_text())
audit = dict(provided)
for path, entry in provided.items():
    assert hashlib.sha256((ROOT / path).read_bytes()).hexdigest() == entry['sha256']
by_key = {row['audio_key']: row for row in manifest['clips']}
for row in generation['clips']:
    path, key = row['path'], row['key']
    sha = hashlib.sha256((ROOT / path).read_bytes()).hexdigest()
    assert sha == row['sha256']
    if key in bank['clips']:
        assert bank['clips'][key] == path and bank['sha256'][key] == sha
    for field, value in [('clips', path), ('texts', row['text']), ('styles', row['style']), ('intonations', row['intonation']), ('phonemes', row['phonemes']), ('sha256', sha)]:
        bank.setdefault(field, {})[key] = value
    by_key[key] = {'audio_key': key, 'text': row['text'], 'style': row['style'], 'path': path, 'intonation': row['intonation'], 'sha256': sha, 'source': generation['pack']}
    audit[path] = {'sha256': sha, 'bytes': (ROOT / path).stat().st_size, 'source': 'generated-time-nature-v1'}
bank['contentPacks'] = ['time-nature-v1']
manifest['clips'] = list(by_key.values())
manifest['additions'] = [{'pack': generation['pack'], 'clips': len(generation['clips']), 'voice': generation['voice'], 'locale': generation['locale'], 'source': 'data/time-nature-audio-generation.json'}]
(ROOT / 'audio-manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
(ROOT / 'reports/all-audio-sha256.json').write_text(json.dumps(audit, ensure_ascii=False, indent=2) + '\n')
source = source[:match.start(1)] + json.dumps(bank, ensure_ascii=False, separators=(',', ':')).replace('<', '\\u003c') + source[match.end(1):]
(ROOT / 'index.html').write_text(source)
(ROOT / 'audio-files.js').write_text('/* Original supplied MP3s plus explicitly requested new C02 GA recordings. */\nself.FROG_AUDIO_FILES=' + json.dumps([r['path'] for r in manifest['clips']], separators=(',', ':')) + ';\nself.FROG_AUDIO_HASHES=' + json.dumps({r['path']: r['sha256'] for r in manifest['clips']}, separators=(',', ':')) + ';\n')
assert len(manifest['clips']) == len(bank['clips']) == len(audit)
print(json.dumps({'providedUnchanged': len(provided), 'generated': len(generation['clips']), 'total': len(audit)}))
