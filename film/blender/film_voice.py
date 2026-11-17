"""The voices of the Pucksley film: speak each line, put it at its place, and mix it with the music
(film_music.py), which fades down under each line and up again after it, and the effects (film_effects.py).

  python film_voice.py                 → cache/voice/*.wav, cache/film-voice.wav, cache/film-mix.wav
                                         and a table of when each line was meant to start, and when it could
  python film_voice.py --no-effects    music and voices only

Two voices, both synthetic:
  Y  the person talking to the puck: ElevenLabs' stock voice "Brian" (eleven.py sends each line to ElevenLabs)
  P  the puck: Azure's "en-AU-AnnetteNeural", which is the voice the real puck speaks with by default
     (azure_tts.py sends each line to Microsoft)
A line is only spoken once: it is kept in cache/voice under a name made from the voice and the words.

Times are film seconds, counted from clock.py's beats. A line never starts before the one before it has
finished, so a line that is too long for its place pushes the next one late, and the table says by how much.
"""
import hashlib
import os
import subprocess
import sys
import wave

import numpy as np

import azure_tts
import clock
import eleven

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'cache', 'voice')
SR = 44100
END = clock.END + clock.CARD
B = clock.BEAT
YOU, PUCK = 'nPczCjzI2devNBz1zQrb', 'en-AU-AnnetteNeural'      # ElevenLabs "Brian"; Azure "Annette"

#        the earliest it starts, who, what
LINES = [
    (B['weather'] + 0.4, 'Y', "What's the weather doing this afternoon?"),
    (B['weather'] + 3.0, 'P', 'Clearing by two. Take a jacket till then.'),
    (B['music'] + 0.4, 'Y', 'Play some jazz in the kitchen.'),
    (B['music'] + 2.8, 'P', 'Jazz, in the kitchen.'),
    (B['group'] + 0.4, 'Y', 'Group the kitchen with the ensuite.'),
    (B['group'] + 2.8, 'P', 'Done. Both rooms.'),
    (B['timer'] + 0.4, 'Y', 'Set a timer for pasta. Ten minutes.'),
    (B['timer'] + 2.6, 'P', 'Ten minutes. Starting now.'),
    (B['done'] + 0.7, 'P', "Your pasta's ready."),
    (B['tv'] + 0.4, 'Y', 'Turn off the downstairs TV.'),
    (B['tv'] + 2.4, 'P', "It's off."),
    (B['lamp'] + 0.4, 'Y', 'Lamp on.'),
    (B['heating'] + 0.4, 'Y', 'Turn the heating up half a degree.'),
    (B['heating'] + 2.8, 'P', 'Twenty-one and a half.'),
    (B['pc'] + 0.4, 'Y', 'Shut down the PC.'),
    (B['pc'] + 1.9, 'P', 'Shut down the PC? Turn for yes.'),
    (B['night'] + 0.4, 'Y', 'Everything off. Good night.'),
    (B['night'] + 2.6, 'P', 'Good night.'),
]


def speak(text, who):
    """The line as a WAV in cache/voice, spoken the first time it is asked for."""
    path = os.path.join(OUT, f'{who}-{hashlib.md5(((YOU if who == "Y" else PUCK) + "|" + text).encode()).hexdigest()[:10]}.wav')
    if os.path.exists(path):
        return path
    if who == 'Y':
        mp3 = path[:-4] + '.mp3'
        eleven.speak(text, YOU, mp3, stability=0.6)
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', mp3, '-ar', str(SR), '-ac', '1', '-c:a', 'pcm_s16le', path], check=True)
        os.remove(mp3)
    else:
        azure_tts.speak(text, PUCK, path)
    return path


def load(path):
    """A WAV as mono floats at SR, with the silence trimmed off both ends."""
    with wave.open(path, 'rb') as w:
        rate, ch = w.getframerate(), w.getnchannels()
        a = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768.0
    a = a.reshape(-1, ch).mean(axis=1)
    loud = np.nonzero(np.abs(a) > 0.01)[0]
    if len(loud):
        a = a[max(0, loud[0] - int(rate * 0.02)):loud[-1] + int(rate * 0.05)]
    if rate != SR:
        a = np.interp(np.arange(0, len(a), rate / SR), np.arange(len(a)), a).astype(np.float32)
    return a


def track(name, n):
    """A stereo track from cache, n samples long."""
    with wave.open(os.path.join(HERE, 'cache', name), 'rb') as w:
        a = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32).reshape(-1, 2) / 32768.0
    return np.pad(a, ((0, max(0, n - len(a))), (0, 0)))[:n]


def save(name, a):
    a = a if a.ndim == 2 else np.stack([a, a], 1)
    with wave.open(os.path.join(HERE, 'cache', name), 'wb') as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((np.clip(a, -1, 1) * 32767).astype(np.int16).tobytes())


if __name__ == '__main__':
    os.makedirs(OUT, exist_ok=True)
    voice = np.zeros(int(END * SR), np.float32)
    print(f"{'meant':>6} {'starts':>7} {'ends':>6}  who  line")
    late, free, said = 0, 0.0, []
    for t, who, text in LINES:
        a = load(speak(text, who))
        a = a / (np.max(np.abs(a)) or 1) * (0.8 if who == 'Y' else 0.72)
        start = max(t, free + 0.25)                          # never over the line before
        k = int(start * SR)
        voice[k:k + len(a)] += a[:len(voice) - k]
        free = start + len(a) / SR
        said.append((start, free))
        late += start - t > 0.4
        print(f'{t:6.1f} {start:7.1f} {free:6.1f}   {who}   {text}' + (f'    <- {start - t:.1f} s late' if start - t > 0.4 else ''))
    print(f'{late} of {len(LINES)} lines start late' if late else 'every line starts when it was meant to')

    # The music fades down for each line and up again after it: down over DOWN seconds, finishing as the
    # line starts; held for HOLD after its last word; up over UP. Eased, so it is a fade and not a cut.
    DOWN, HOLD, UP = 0.4, 0.2, 0.6
    seconds = np.arange(len(voice), dtype=np.float32) / SR
    level = np.zeros(len(voice), np.float32)                 # 0 between lines, 1 under them
    for a, b in said:
        ramp = np.minimum(np.clip((seconds - (a - DOWN)) / DOWN, 0, 1), np.clip((b + HOLD + UP - seconds) / UP, 0, 1))
        level = np.maximum(level, ramp * ramp * (3 - 2 * ramp))
    effects = '--no-effects' not in sys.argv and os.path.exists(os.path.join(HERE, 'cache', 'film-effects.wav'))
    mix = track('film-music.wav', len(voice)) * (0.8 - 0.5 * level)[:, None] + voice[:, None] + (track('film-effects.wav', len(voice)) * 0.5 if effects else 0)
    mix = np.tanh(mix * 1.1) * 0.9
    save('film-voice.wav', voice)
    save('film-mix.wav', mix)
    print('wrote cache/film-voice.wav and cache/film-mix.wav (music, voices' + (', effects)' if effects else ')'))
