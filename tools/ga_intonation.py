"""Conservative terminal pitch contours; articulation and timing stay intact.

Authoring only: praat-parselmouth==0.4.7, numpy and ffmpeg.
"""
import numpy as np
import parselmouth
from parselmouth.praat import call

PROSODY={'method':'Praat PSOLA terminal contour v1','windowSeconds':0.5,
    'riseRatio':1.22,'fallRatio':0.82}


def terminal_contour(samples,rate,direction):
    if direction not in ('rise','fall'):return samples
    sound=parselmouth.Sound(np.asarray(samples,dtype=float),rate)
    pitch=sound.to_pitch_ac(time_step=.01,pitch_floor=90,pitch_ceiling=450)
    frequencies=pitch.selected_array['frequency'];times=pitch.xs()
    voiced=frequencies>0;times=times[voiced];frequencies=frequencies[voiced]
    if len(times)<12:return samples
    end=float(times[-1]);start=max(float(times[0]),end-PROSODY['windowSeconds'])
    near=frequencies[(times>=start)&(times<start+.15)]
    # A clause pause can occupy the start of this window; interpolate across it.
    anchor=float(np.median(near)) if len(near) else float(np.interp(start,times,frequencies))
    target=float(np.clip(anchor*PROSODY[direction+'Ratio'],95,400))
    manipulation=call(sound,'To Manipulation',.01,90,450)
    tier=call(manipulation,'Extract pitch tier')
    call(tier,'Remove points between',start,sound.xmax)
    for fraction in (0,.2,.4,.6,.8,1):
        call(tier,'Add point',start+(end-start)*fraction,anchor+(target-anchor)*fraction)
    call([tier,manipulation],'Replace pitch tier')
    result=call(manipulation,'Get resynthesis (overlap-add)').values[0]
    assert len(result)==len(samples) and np.isfinite(result).all()
    # PSOLA edits pitch without changing phoneme timing or adding terminal vowels.
    return result.astype(np.float32)


def refine_embedded(root):
    """Upgrade an existing authoring output once, without regenerating word clips."""
    import base64,hashlib,json,re,subprocess
    source=(root/'index.html').read_text()
    match=re.search(r'window.LOCAL_AUDIO_BANK=(.*?);\s*</script>',source,re.S)
    bank=json.loads(match.group(1))
    if bank.get('prosody')==PROSODY:
        print('Terminal contours already applied');return
    assert bank['revision']=='pep-ga-v7'
    for number,(key,payload) in enumerate(list(bank['clips'].items()),1):
        direction=bank['intonations'].get(key,'neutral')
        if direction=='neutral':continue
        raw=subprocess.check_output(['ffmpeg','-v','error','-i','pipe:0','-f','f32le','-ac','1','-ar','24000','pipe:1'],input=base64.b64decode(payload))
        samples=terminal_contour(np.frombuffer(raw,dtype='<f4'),24000,direction)
        peak=float(np.abs(samples).max())
        if peak>.98:samples=samples*(.98/peak)
        encoded=subprocess.check_output(['ffmpeg','-v','error','-f','f32le','-ac','1','-ar','24000','-i','pipe:0','-codec:a','libmp3lame','-b:a','128k','-f','mp3','pipe:1'],input=samples.astype('<f4').tobytes())
        bank['clips'][key]=base64.b64encode(encoded).decode()
        if number%25==0:print('Terminal contours:',number,'/',len(bank['clips']),flush=True)
    config=json.loads((root/'data/audio-generation.json').read_text())
    config.pop('generationSignature');config.pop('clipCount')
    config['profiles']['sentence']['bitrate']='128k';config['prosody']=PROSODY
    signature=hashlib.sha256(json.dumps(config,sort_keys=True).encode()).hexdigest()
    bank['prosody']=PROSODY;bank['profiles']=config['profiles']
    source=source[:match.start(1)]+json.dumps(bank,ensure_ascii=False,separators=(',',':'))+source[match.end(1):]
    (root/'index.html').write_text(source)
    (root/'data/audio-generation.json').write_text(json.dumps({**config,'clipCount':len(bank['clips']),'generationSignature':signature},ensure_ascii=False,indent=2)+'\n')
    print('COMPLETE: terminal contours applied; isolated word clips preserved',flush=True)


if __name__=='__main__':
    from pathlib import Path
    refine_embedded(Path(__file__).resolve().parents[1])
