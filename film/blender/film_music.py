"""The film's music: there is none until somebody asks the puck for it. "Play some jazz in the kitchen" is
where it starts, sounding like one small speaker; turning the puck makes it louder and fuller; grouping a
second room fills it out; "Everything off" stops it. So the score is what the house is playing.

  python film_music.py            → cache/film-music.wav   (film_voice.py mixes the voices over it)
  python film_music.py --track ID  another Epidemic Sound recording (search with epidemic.py)

The track is "Simply Joyful" by William Claeson (Epidemic Sound: contemporary jazz, happy, laid back, no
vocals). Chosen from its tags, not by ear: nobody has heard this mix but the user. It is downloaded once,
through the user's subscription (epidemic.py), into cache/music, which is not in git.

Times are film seconds, from clock.py.
"""
import os
import subprocess
import sys
import urllib.request
import wave

import numpy as np

import clock
import epidemic

HERE = os.path.dirname(os.path.abspath(__file__))
MUSIC = os.path.join(HERE, 'cache', 'music')
arg = lambda name, default: sys.argv[sys.argv.index('--' + name) + 1] if '--' + name in sys.argv else default
TRACK = arg('track', 'b37ffe50-74da-404b-a356-57f6ff8aa4df')             # Simply Joyful, William Claeson
OUT = arg('out', 'film-music.wav')
SR, END, B = 44100, clock.END + clock.CARD, clock.BEAT
START = B['music'] + 2.6                                     # the kitchen lights, and the music starts
LOUDER = (B['turn'] + 0.2, B['turn'] + 1.5)                  # the puck is turned
FULLER = (B['group'] + 2.8, B['group'] + 3.6)                # the second room joins
STOP = (B['night'] + 1.7, B['night'] + 2.4)                  # everything off


def wav(path):
    with wave.open(path, 'rb') as w:
        return np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32).reshape(-1, 2) / 32768.0


def recording():
    """The track as stereo floats at SR, twice: as it is, and as a small speaker would play it."""
    raw, full, small = (os.path.join(MUSIC, f'{TRACK}{s}.wav') for s in ('', '-16', '-small'))
    if not os.path.exists(raw):
        os.makedirs(MUSIC, exist_ok=True)
        res = epidemic.Server().call('DownloadRecording', {'id': TRACK, 'options': {'fileType': 'WAV', 'stemType': 'FULL'}})
        urllib.request.urlretrieve(res['data']['recordingDownload']['assetUrl'], raw)
        print('downloaded the track')
    if not os.path.exists(full):
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', raw, '-af', 'silenceremove=start_periods=1:start_threshold=-50dB', '-ar', str(SR), '-ac', '2', '-c:a', 'pcm_s16le', full], check=True)
    if not os.path.exists(small):                            # no bass, no top, and in the middle: one small speaker
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', full, '-af', 'highpass=f=320,lowpass=f=3600,pan=stereo|c0=0.5*c0+0.5*c1|c1=0.5*c0+0.5*c1', '-c:a', 'pcm_s16le', small], check=True)
    return wav(full), wav(small)


if __name__ == '__main__':
    full, small = recording()
    n = int(END * SR)
    t = np.arange(n) / SR
    ease = lambda a, b: (lambda u: u * u * (3 - 2 * u))(np.clip((t - a) / (b - a), 0, 1))
    k = int(START * SR)
    lay = lambda a: np.pad(a[:n - k], ((k, max(0, n - k - len(a))), (0, 0)))[:n]
    wide = ease(*LOUDER)                                     # 0 a small speaker, 1 the whole recording
    level = (0.42 + 0.3 * wide + 0.18 * ease(*FULLER)) * np.clip((t - START) / 0.25, 0, 1) * (1 - ease(*STOP))
    mix = (lay(small) * (1 - wide)[:, None] + lay(full) * wide[:, None]) * level[:, None]
    mix = mix / (np.max(np.abs(mix)) or 1) * 0.9
    with wave.open(os.path.join(HERE, 'cache', OUT), 'wb') as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((np.clip(mix, -1, 1) * 32767).astype(np.int16).tobytes())
    print(f'wrote cache/{OUT}: music from {START:.1f} s to {STOP[1]:.1f} s')
