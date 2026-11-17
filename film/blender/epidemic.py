"""Epidemic Sound, for the film's music: a small client for its MCP server (the way it lets a subscriber's
tools search and download), used here straight from Python.

  python epidemic.py tools                         the tools the server offers and what each takes
  python epidemic.py call SearchRecordings '{"...": "..."}'       call one, print what comes back

The API key is never in this repo. It is read when needed from the file named by the environment variable
FILM_KEYS, or D:/tmp/Keys.txt, from the line that starts "epidemicsound:". It is the key made under
Account -> API keys on epidemicsound.com, not a Developer Portal key.
"""
import json
import os
import sys
import urllib.error
import urllib.request

URL = 'https://www.epidemicsound.com/a/mcp-service/mcp'


def key():
    path = os.environ.get('FILM_KEYS', 'D:/tmp/Keys.txt')
    for line in open(path, encoding='utf-8'):
        name, _, value = line.partition(':')
        if name.strip().lower().replace(' ', '') == 'epidemicsound':
            return value.strip()
    raise SystemExit(f'no "epidemicsound:" line in {path}')


class Server:
    def __init__(self):
        self.session, self.n = None, 0
        self.send('initialize', {'protocolVersion': '2025-03-26', 'capabilities': {}, 'clientInfo': {'name': 'film-tools', 'version': '0.1'}})
        self.send('notifications/initialized', notify=True)

    def send(self, method, params=None, notify=False):
        body = {'jsonrpc': '2.0', 'method': method}
        if params is not None:
            body['params'] = params
        if not notify:
            self.n += 1
            body['id'] = self.n
        headers = {'Authorization': 'Bearer ' + key(), 'Content-Type': 'application/json', 'Accept': 'application/json, text/event-stream'}
        if self.session:
            headers['Mcp-Session-Id'] = self.session
        req = urllib.request.Request(URL, data=json.dumps(body).encode(), headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=180) as r:
                self.session = r.headers.get('Mcp-Session-Id') or self.session
                raw = r.read().decode('utf-8', errors='replace')
        except urllib.error.HTTPError as e:                  # say what the server said; it does not repeat the key
            raise SystemExit(f'Epidemic Sound refused {method}: {e.code} {e.read().decode(errors="replace")[:400]}')
        if notify or not raw.strip():
            return None
        if raw.lstrip().startswith('{'):
            msg = json.loads(raw)
        else:                                                # a stream of events: the answer is the last data line
            data = [ln[5:].strip() for ln in raw.splitlines() if ln.startswith('data:')]
            msg = json.loads(data[-1])
        if 'error' in msg:
            raise SystemExit(f'Epidemic Sound: {method}: {json.dumps(msg["error"])[:400]}')
        return msg.get('result')

    def tools(self):
        return self.send('tools/list')['tools']

    def call(self, name, args):
        """Call a tool. Returns its structured answer if it gives one, else its text."""
        res = self.send('tools/call', {'name': name, 'arguments': args})
        if res.get('structuredContent') is not None:
            return res['structuredContent']
        text = '\n'.join(c.get('text', '') for c in res.get('content', []) if c.get('type') == 'text')
        try:
            return json.loads(text)
        except ValueError:
            return text


if __name__ == '__main__':
    s = Server()
    if len(sys.argv) > 2 and sys.argv[1] == 'call':
        print(json.dumps(s.call(sys.argv[2], json.loads(sys.argv[3]) if len(sys.argv) > 3 else {}), indent=1)[:6000])
    else:
        for t in s.tools():
            props = (t.get('inputSchema') or {}).get('properties', {})
            print(f"\n{t['name']}: {(t.get('description') or '').strip()[:300]}")
            for name, p in props.items():
                print(f"    {name}: {p.get('type', p.get('anyOf', ''))}  {str(p.get('description', ''))[:160]}" + (f"  one of {p['enum']}" if 'enum' in p else ''))
