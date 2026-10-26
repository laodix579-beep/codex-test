"""Author only the new C05 recordings with the existing Bella GA model.

The user explicitly requested new GA recordings for this pack. Never regenerate
or modify a pre-existing clip. Model files and dependencies stay outside Pages.
"""
import argparse
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
from food_content import study_word

ROOT = Path(__file__).resolve().parents[1]


def normalize(text):
    text = unicodedata.normalize('NFKC', text).lower().replace('’', "'").replace('‘', "'")
    return re.sub(r'\s+', ' ', re.sub(r"[^a-z0-9'\s]", '', text)).strip()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--model', type=Path, required=True)
    parser.add_argument('--voices', type=Path, required=True)
    parser.add_argument('--cache', type=Path, required=True)
    args = parser.parse_args()
    args.cache.mkdir(parents=True, exist_ok=True)
    html = (ROOT / 'index.html').read_text()
    bank = json.loads(re.search(r'window.LOCAL_AUDIO_BANK=(.*?);\s*</script>', html, re.S)[1])
    previous = ROOT / 'data/food-health-audio-generation.json'
    pack_keys = {row['key'] for row in json.loads(previous.read_text())['clips']} if previous.exists() else set()
    prompts = {}
    for file in sorted((ROOT / 'data/food-health').glob('0*.json')):
        for row in json.loads(file.read_text())['items']:
            for role, text in [('word', study_word(row)), ('sentence', row['example_en'])]:
                key = 'close::verb' if role == 'word' and normalize(text) == 'close' else normalize(text)
                if key not in bank['clips'] or key in pack_keys:
                    prompts.setdefault(key, {'key': key, 'text': text, 'role': role,
                        'style': 'word' if role == 'word' and row['item_type'] == 'word' else 'sentence'})
    Tokenizer()
    g2p = en.G2P(british=False, fallback=espeak.EspeakFallback(british=False))
    plan = []
    for row in prompts.values():
        phonemes, tokens = g2p(row['text'])
        # All supplied C05 'read' examples are present/imperative, not past.
        if re.search(r'\bread\b', row['text'], re.I):
            phonemes = phonemes.replace('ɹˈɛd', 'ɹˈid')
        # Standard GA herbal has a silent h; DJ remains the uploaded British form.
        if re.search(r'\bherbal\b', row['text'], re.I):
            phonemes = re.sub(r'h(?=[ˈˌ]?ɜɹb)', '', phonemes)
        if row['key'] == 'pe':
            phonemes = g2p('P. E.')[0]
        if row['key'] == 'read':
            phonemes = 'ɹˈid'
        if row['key'] == 'project':
            phonemes = 'pɹˈɑdʒɛkt'
        if row['key'] == 'wind':
            phonemes = 'wˈɪnd'  # Air movement, never the verb /waɪnd/.
        if not phonemes.strip() or '❓' in phonemes:
            raise ValueError('Unresolved GA pronunciation: ' + row['text'])
        question = row['text'].strip().endswith('?')
        yesno = bool(re.match(r'^(am|is|are|was|were|do|does|did|can|could|will|would|shall|should|have|has|had|may|might|must)\b', row['text'], re.I))
        plan.append({**row, 'phonemes': phonemes, 'intonation': 'rise' if question and yesno else 'fall' if row['style'] == 'sentence' else 'neutral'})
    (args.cache / 'plan.json').write_text(json.dumps(plan, ensure_ascii=False, indent=2) + '\n')
    options = ort.SessionOptions()
    options.intra_op_num_threads = 2
    options.inter_op_num_threads = 1
    session = ort.InferenceSession(str(args.model), sess_options=options, providers=['CPUExecutionProvider'])
    voice = Kokoro.from_session(session, str(args.voices))
    started = time.time()
    outputs = []
    for index, row in enumerate(plan, 1):
        fingerprint = hashlib.sha256(json.dumps(row, sort_keys=True).encode()).hexdigest()
        file = args.cache / (fingerprint + '.mp3')
        if not file.exists():
            samples, rate = voice.create(row['phonemes'], voice='af_bella', speed=.92 if row['style'] == 'word' else .9, is_phonemes=True, trim=False)
            assert rate == 24000 and len(samples) > rate * .08 and np.isfinite(samples).all(), row
            samples = terminal_contour(samples, rate, row['intonation'])
            samples = np.pad(samples, (int(rate * .12), int(rate * .24)))
            peak = float(np.max(np.abs(samples)))
            assert peak > .01
            samples *= min(4, .88 / peak)
            wav = args.cache / 'current.wav'
            with wave.open(str(wav), 'wb') as f:
                f.setnchannels(1)
                f.setsampwidth(2)
                f.setframerate(rate)
                f.writeframes((np.clip(samples, -1, 1) * 32767).astype('<i2').tobytes())
            subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', str(wav), '-af', 'loudnorm=I=-16:TP=-1.5:LRA=11', '-ar', '24000', '-ac', '1', '-codec:a', 'libmp3lame', '-b:a', '96k' if row['style'] == 'word' else '128k', str(file)], check=True)
        slug = re.sub(r'[^a-z0-9]+', '-', row['key']).strip('-')
        destination = ROOT / 'audio/en-us/food' / row['role'] / (slug + '.mp3')
        destination.parent.mkdir(parents=True, exist_ok=True)
        if destination.exists():
            assert destination.read_bytes() == file.read_bytes(), destination
        else:
            destination.write_bytes(file.read_bytes())
        outputs.append({**row, 'path': destination.relative_to(ROOT).as_posix(), 'sha256': hashlib.sha256(file.read_bytes()).hexdigest()})
        if index % 20 == 0 or index == len(plan):
            print(f'{index}/{len(plan)} new Bella GA clips ({time.time()-started:.0f}s)', flush=True)
    metadata = {'pack': 'food-health-v1', 'voice': 'af_bella', 'locale': 'en-US', 'engine': 'Kokoro-82M v1.0 FP32', 'phonemizer': 'Misaki-fork en-US 0.9.6', 'sampleRate': 24000, 'prosody': PROSODY,
        'models': {p.name: hashlib.file_digest(p.open('rb'), 'sha256').hexdigest() for p in [args.model, args.voices]}, 'clips': outputs}
    (ROOT / 'data/food-health-audio-generation.json').write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + '\n')
    print('COMPLETE: new C05 audio generated; all previous files left untouched', flush=True)


if __name__ == '__main__':
    main()
