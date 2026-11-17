"""The film's sound effects: real recordings from Epidemic Sound's library, each put on the thing in the
picture that makes it, and two longer ones under the day: birds at first light, crickets at night.

  python film_effects.py          → cache/film-effects.wav   (film_voice.py mixes it in with the music and voices)

Each is downloaded once, through the user's subscription (epidemic.py), into cache/sfx, which is not in git.
Times are film seconds, counted from clock.py's. Levels are set low and by eye: nobody has heard this mix
but the user.
"""
import os
import subprocess
import urllib.request
import wave

import numpy as np

import clock
import epidemic

HERE = os.path.dirname(os.path.abspath(__file__))
SFX = os.path.join(HERE, 'cache', 'sfx')
SR, END, B = 44100, clock.END + clock.CARD, clock.BEAT

# what each sound is in Epidemic Sound's library
SOUNDS = {
    'tap': '4e4a1062-fc72-4eb8-af0f-48dba8755d3d',        # Glass, Handle, Touch, Vase, Hollow, Hand, Fingers, Tap 02
    'chime': 'ca606dde-a0ba-4749-beb3-40e412003ce6',      # User Interface, Alert, Tonal, Soft Confirm Chime
    'switch': '2b2e2214-2f82-4614-a840-75eb7bff59b7',     # Mechanical, Switch, Light Switch, On, Off
    'tvoff': 'a843e07b-ba27-4e31-a979-acae95c7cd22',      # Communications, Television, Switch Off, Noise
    'pcoff': '15acac69-af75-441b-9c91-aa00ef67235e',      # Scifi, Computer, Shut Down 03
    'knob': 'c122f976-5e6e-47b7-8d92-1cb3bea23477',       # Communications, Transceiver, VHF Radio, Sailboat, Knob, Turn, Clicks, Medium Speed 01
    'heater': '93d7448a-0a28-4769-aa45-75743a9fbace',     # Mechanical, Click, Portable Heater, Radiator, Switch Click
    'birds': 'e82709aa-cf20-42fe-9f10-4f7439b10597',      # Ambience, Birdsong, Calm, Small Birds Chirping, Distant Water 01
    'crickets': '68d815aa-c2d9-4076-94b6-49d5ac87b53f',   # Ambience, Insect, Cricket, Tonal
}

#          when, which sound, how loud (1 is the recording's own peak), how much of it (seconds)
EVENTS = [(B[k], 'tap', 0.32, 0.3) for k in ('weather', 'music', 'group', 'timer', 'tv', 'lamp', 'heating', 'pc', 'night')]      # every tap that starts it listening
EVENTS += [
    (B['turn'] + 0.2, 'knob', 0.22, 1.3),                 # turned up
    (B['done'], 'chime', 0.5, 2.0),                       # the timer finishes
    (B['tv'] + 2.2, 'tvoff', 0.4, 0.4),                   # the television goes off
    (B['lamp'] + 1.2, 'switch', 0.45, 0.35),              # the lamp comes on
    (B['heating'] + 2.6, 'heater', 0.4, 1.0),             # the heating comes on
    (B['pc'] + 4.4, 'knob', 0.2, 0.8),                    # turned to Yes
    (B['pc'] + 5.6, 'tap', 0.32, 0.3),                    # and tapped
    (B['pc'] + 6.0, 'pcoff', 0.22, 1.6),                  # the PC shuts down
    (B['night'] + 2.1, 'switch', 0.35, 0.35),             # the lamp goes off
]
#        when, which sound, how loud (its average level), from where in the recording, for how long, fade in, fade out
BEDS = [(0.2, 'birds', 0.05, 1.0, B['music'] + 5.0, 1.2, 4.0),                                # first light, until the music is under way
        (clock.SUNSET[1], 'crickets', 0.028, 1.0, END - clock.SUNSET[1] - 0.3, 3.0, 2.5)]    # night, to the end of the card


def asset_url(answer):
    """The signed URL in a download answer, wherever it sits."""
    if isinstance(answer, dict):
        for k, v in answer.items():
            if k == 'assetUrl':
                return v
            found = asset_url(v)
            if found:
                return found
    return None


def sound(name, server=[]):
    """The effect as mono floats at SR, trimmed and at full level. Downloaded the first time."""
    raw, wav = os.path.join(SFX, f'{name}.wav'), os.path.join(SFX, f'{name}-16.wav')
    if not os.path.exists(raw):
        os.makedirs(SFX, exist_ok=True)
        if not server:
            server.append(epidemic.Server())
        urllib.request.urlretrieve(asset_url(server[0].call('DownloadSoundEffect', {'id': SOUNDS[name], 'options': {'fileType': 'WAV'}})), raw)
        print('downloaded', name)
    if not os.path.exists(wav):
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', raw, '-ar', str(SR), '-ac', '1', '-c:a', 'pcm_s16le', wav], check=True)
    with wave.open(wav, 'rb') as w:
        a = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768.0
    loud = np.nonzero(np.abs(a) > 0.02 * (np.max(np.abs(a)) or 1))[0]
    a = a[max(0, loud[0] - 200):loud[-1] + 2000] if len(loud) else a
    return a / (np.max(np.abs(a)) or 1)


if __name__ == '__main__':
    track = np.zeros(int(END * SR), np.float32)
    for t, name, gain, length in sorted(EVENTS):
        a = sound(name)[:int(length * SR)].copy()
        a *= gain / (np.max(np.abs(a)) or 1)
        a *= np.clip((len(a) - np.arange(len(a))) / (0.08 * SR), 0, 1)       # the cut end fades out
        k = int(t * SR)
        track[k:k + len(a)] += a[:max(0, len(track) - k)]
    for t, name, level, start, length, fade_in, fade_out in BEDS:
        a = sound(name)
        a = np.tile(a, int(np.ceil((start + length) * SR / len(a))))[int(start * SR):int((start + length) * SR)].copy()
        a *= level / (float(np.sqrt(np.mean(a * a))) or 1)
        n = np.arange(len(a)) / SR
        a *= np.clip(n / fade_in, 0, 1) * np.clip((length - n) / fade_out, 0, 1)
        k = int(t * SR)
        track[k:k + len(a)] += a[:max(0, len(track) - k)]
    pcm = (np.clip(track, -1, 1) * 32767).astype(np.int16)
    out = os.path.join(HERE, 'cache', 'film-effects.wav')
    with wave.open(out, 'wb') as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(np.stack([pcm, pcm], 1).tobytes())
    print(f'wrote {out}: {len(EVENTS)} effects and {len(BEDS)} longer sounds, from {len(SOUNDS)} recordings')
