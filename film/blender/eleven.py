"""ElevenLabs, for the film's voice-over: list the account's voices, and speak a line to a file.

  python eleven.py voices            the voices on the account, with how ElevenLabs describes each
  python eleven.py account           the plan, and how many characters are left this month

The API key is never in this repo. It is read when needed from the file named by the environment variable
FILM_KEYS, or D:/tmp/Keys.txt, from the line that starts "eleven labs:". Each line spoken is sent to
ElevenLabs.
"""
import json
import os
import sys
import urllib.error
import urllib.request

API = 'https://api.elevenlabs.io/v1'


def key():
    path = os.environ.get('FILM_KEYS', 'D:/tmp/Keys.txt')
    for line in open(path, encoding='utf-8'):
        name, _, value = line.partition(':')
        if name.strip().lower().replace(' ', '') == 'elevenlabs':
            return value.strip()
    raise SystemExit(f'no "eleven labs:" line in {path}')


def call(path, body=None):
    req = urllib.request.Request(API + path, data=None if body is None else json.dumps(body).encode(), headers={'xi-api-key': key(), 'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            return r.read()
    except urllib.error.HTTPError as e:                      # say what ElevenLabs said; it does not repeat the key
        raise SystemExit(f'ElevenLabs refused {path.split("?")[0]}: {e.code} {e.read().decode(errors="replace")[:400]}')


def voices():
    return json.loads(call('/voices'))['voices']


def speak(text, voice_id, path, model='eleven_multilingual_v2', stability=0.5, similarity=0.75, style=0.0, speed=1.0):
    """Say text in the voice into an MP3 at path."""
    body = {'text': text, 'model_id': model, 'voice_settings': {'stability': stability, 'similarity_boost': similarity, 'style': style, 'speed': speed}}
    audio = call(f'/text-to-speech/{voice_id}?output_format=mp3_44100_128', body)
    with open(path, 'wb') as f:
        f.write(audio)
    return path


if __name__ == '__main__':
    what = sys.argv[1] if len(sys.argv) > 1 else 'voices'
    if what == 'account':
        sub = json.loads(call('/user/subscription'))
        print(f"plan: {sub.get('tier')}   characters used: {sub.get('character_count')} of {sub.get('character_limit')}")
    else:
        for v in sorted(voices(), key=lambda v: v['name']):
            lab = v.get('labels') or {}
            print(f"{v['name']:<28} {v['voice_id']}  {lab.get('gender', ''):<8} {lab.get('age', ''):<12} {lab.get('accent', ''):<14} {lab.get('description', lab.get('descriptive', ''))}  [{v.get('category', '')}]")
