"""The talking face for the film: have Openspline animate the puck's face to each of the puck's lines, the
way the hub does live, and keep the frames.

  python face_capture.py            → cache/face/<n>/0001.jpg and on, 25 a second, one folder a line
  python face_capture.py --borrow   Openspline has one worker, and a running hub keeps it. This ends the
                                    hub's session first (from the hub's own session.json) and takes the
                                    worker for under a minute; the hub opens a new session by itself
                                    within seconds of this finishing. While it runs, a puck that speaks
                                    shows its usual face instead of the talking one.

It speaks Openspline's own wire protocol, as hub/src/Plugins/Pucksley.Plugins.Speech/Openspline does:
POST /v1/sessions with the portrait; a websocket for the audio going in; one for the frames coming out,
each acknowledged. The portrait is the plugin's default face. The lines and their sound are film_voice.py's.
"""
import asyncio
import base64
import json
import os
import sys
import uuid

import numpy as np
import requests
import websockets

import film_voice

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'cache', 'face')
PORTRAIT = os.path.join(HERE, '..', '..', 'hub', 'src', 'Plugins', 'Pucksley.Plugins.Speech', 'Openspline', 'Faces', 'face-01.jpg')
URL = 'http://127.0.0.1:7860'
RATE = 24000


def hub_session():
    path = os.path.expandvars(r'%APPDATA%\Pucksley\plugin-data\openspline\session.json')
    return json.load(open(path)) if os.path.exists(path) else None


def end(session_id, token):
    requests.delete(f'{URL}/v1/sessions/{session_id}', headers={'Authorization': 'Bearer ' + token}, timeout=5)


async def capture(lines):
    if '--borrow' in sys.argv and (theirs := hub_session()):
        end(theirs['id'], theirs['token'])
    r = requests.post(f'{URL}/v1/sessions', files={'portrait': ('portrait', open(PORTRAIT, 'rb'), 'application/octet-stream')}, data={'quality': 'low'}, timeout=90)
    if r.status_code == 429:
        raise SystemExit('Openspline has no free worker (a hub is holding it): run again with --borrow')
    r.raise_for_status()
    body = r.json()
    sid, publisher = body['id'], body['publisher_token']
    viewer = body.get('viewer_url', '').partition('#')[2].partition(':')[2] or publisher
    ws = URL.replace('http', 'ws')
    try:
        async with websockets.connect(f'{ws}/v1/sessions/{sid}/audio', max_size=None) as audio, websockets.connect(f'{ws}/v1/sessions/{sid}/playback', max_size=None) as playback:
            await audio.send(json.dumps({'token': publisher}))
            await playback.send(json.dumps({'token': viewer}))
            state = {'epoch': 0, 'frames': None, 'target': None, 'last': 0, 'done': asyncio.Event(), 'ready': asyncio.Event()}
            answers = {}

            async def from_audio():
                async for raw in audio:
                    e = json.loads(raw)
                    if e.get('type') == 'error':
                        print('  openspline (audio):', e.get('message'))
                    if e.get('id') in answers:
                        answers.pop(e['id']).set_result(e)

            async def from_playback():
                async for raw in playback:
                    e = json.loads(raw)
                    kind = e.get('type')
                    if kind == 'connected':
                        state['epoch'] = e.get('epoch', 0)
                        await playback.send(json.dumps({'type': 'ready'}))
                        state['ready'].set()
                    elif kind == 'media':
                        samples = e.get('samples', 0)
                        await playback.send(json.dumps({'type': 'played', 'samples': samples, 'epoch': e.get('epoch', state['epoch'])}))
                        if state['frames'] is not None:
                            state['frames'].append(base64.b64decode(e.get('image', '')))
                            state['last'] = samples
                            if state['target'] is not None and samples >= state['target']:
                                state['done'].set()
                    elif kind == 'turn_end':
                        state['target'] = e.get('target_samples', 0)
                        if state['last'] >= state['target']:
                            state['done'].set()
                    elif kind == 'error':
                        print('  openspline (playback):', e.get('message'))

            async def ask(message):
                message['id'] = uuid.uuid4().hex
                answers[message['id']] = asyncio.get_running_loop().create_future()
                await audio.send(json.dumps(message))
                return await asyncio.wait_for(answers[message['id']], 30)

            readers = [asyncio.create_task(from_audio()), asyncio.create_task(from_playback())]
            await asyncio.wait_for(state['ready'].wait(), 30)
            for n, pcm in lines:
                state.update(frames=[], target=None, last=0)
                state['done'].clear()
                for off in range(0, len(pcm), RATE // 10):                 # a tenth of a second a request, as the hub does
                    await ask({'type': 'audio', 'epoch': state['epoch'], 'data': base64.b64encode(pcm[off:off + RATE // 10].tobytes()).decode(),
                               'format': {'sample_rate': RATE, 'channels': 1, 'encoding': 'pcm_s16le'}})
                await ask({'type': 'end_turn', 'drain': True})
                await asyncio.wait_for(state['done'].wait(), 60)
                folder = os.path.join(OUT, str(n))
                os.makedirs(folder, exist_ok=True)
                for old in os.listdir(folder):
                    os.remove(os.path.join(folder, old))
                for i, jpeg in enumerate(state['frames']):
                    open(os.path.join(folder, f'{i + 1:04d}.jpg'), 'wb').write(jpeg)
                print(f'line {n}: {len(pcm) / RATE:.2f} s of speech, {len(state["frames"])} frames')
                state['frames'] = None
            for t in readers:
                t.cancel()
    finally:
        end(sid, publisher)


if __name__ == '__main__':
    lines = []
    for n, (t, who, text) in enumerate(film_voice.LINES):
        if who == 'P':
            a = film_voice.load(film_voice.speak(text, who))            # the same sound the film plays, trimmed the same way
            a = a / (np.max(np.abs(a)) or 1) * 0.8
            a = np.interp(np.arange(0, len(a), film_voice.SR / RATE), np.arange(len(a)), a)
            lines.append((n, (a * 32767).astype('<i2')))
    asyncio.run(capture(lines))
