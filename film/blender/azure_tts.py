"""Azure Speech, for the film's voices: list the voices, and speak a line to a file.

  python azure_tts.py voices          the US English voices, and which are children's
  python azure_tts.py say en-US-AnaNeural "Wake gently." out.wav

The key is never in this repo. It is read when needed from the file named by the environment variable
FILM_KEYS, or D:/tmp/Keys.txt, from the line that starts "azure": the key, then the region. Each line
spoken is sent to Microsoft.
"""
import json
import os
import sys
import urllib.error
import urllib.request
from xml.sax.saxutils import escape


def creds():
    path = os.environ.get('FILM_KEYS', 'D:/tmp/Keys.txt')
    for line in open(path, encoding='utf-8'):
        name, _, value = line.partition(':')
        if name.strip().lower().startswith('azure'):
            parts = value.split()
            if len(parts) < 2:
                raise SystemExit(f'the azure line in {path} needs the key and then the region')
            return parts[0], parts[1]
    raise SystemExit(f'no "azure" line in {path}')


def call(path, body=None, headers=None):
    key, region = creds()
    req = urllib.request.Request(f'https://{region}.tts.speech.microsoft.com/cognitiveservices/{path}', data=body, headers={'Ocp-Apim-Subscription-Key': key, 'User-Agent': 'film-tools', **(headers or {})})
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            return r.read()
    except urllib.error.HTTPError as e:                      # say what Azure said; it does not repeat the key
        raise SystemExit(f'Azure refused {path}: {e.code} {e.reason} {e.read().decode(errors="replace")[:300]}')


def voices(locale='en-US'):
    return [v for v in json.loads(call('voices/list')) if v['Locale'] == locale]


def speak(text, voice, path, rate='0%', pitch='0%'):
    """Say text in the voice into a WAV at path (44.1 kHz, mono). rate and pitch as SSML takes them: '+8%', '-5%'."""
    ssml = f"<speak version='1.0' xml:lang='en-US'><voice name='{voice}'><prosody rate='{rate}' pitch='{pitch}'>{escape(text)}</prosody></voice></speak>"
    audio = call('v1', ssml.encode('utf-8'), {'Content-Type': 'application/ssml+xml', 'X-Microsoft-OutputFormat': 'riff-44100hz-16bit-mono-pcm'})
    with open(path, 'wb') as f:
        f.write(audio)
    return path


if __name__ == '__main__':
    if len(sys.argv) > 4 and sys.argv[1] == 'say':
        print(speak(sys.argv[3], sys.argv[2], sys.argv[4]))
    else:
        for v in voices():
            tags = v.get('VoiceTag') or {}
            words = ' '.join(tags.get('VoicePersonalities', []) + tags.get('TailoredScenarios', []))
            child = 'CHILD' if 'child' in (words + v.get('LocalName', '') + ' '.join(v.get('StyleList', []))).lower() or v['ShortName'] in ('en-US-AnaNeural',) else ''
            print(f"{v['ShortName']:<44} {v['Gender']:<8} {child:<6} {words[:90]}")
