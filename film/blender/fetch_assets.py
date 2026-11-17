"""Download the free (CC0) Poly Haven assets the film's sets use into blender/cache/polyhaven.

  python film/blender/fetch_assets.py

Files already there are skipped. Uses curl, which ships with Windows 10 and later.
"""
import json
import os
import subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'cache', 'polyhaven')
API = 'https://api.polyhaven.com/files/'

# the surfaces the sets stand on, one a set
TEXTURES = {'wood_table_worn': '2k', 'oak_veneer_01': '2k', 'marble_01': '2k', 'black_walnut_veneer_01': '2k', 'plywood': '2k'}
HDRIS = {'lebombo': '2k'}                      # a room with windows, for the fill light and reflections
MODELS = {'desk_lamp_arm_01': '2k', 'food_apple_01': '1k', 'tea_set_01': '1k', 'croissant': '1k', 'potted_plant_02': '1k', 'potted_plant_04': '1k',
          'pot_enamel_01': '1k', 'wooden_spoon': '1k', 'wooden_cutting_board': '1k', 'screwdriver': '1k', 'pliers': '1k', 'book_encyclopedia_set_01': '1k'}


def curl(url, dest=None):
    if dest:
        if os.path.exists(dest) and os.path.getsize(dest) > 0:
            return None
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        subprocess.run(['curl', '-sSL', '--fail', '-m', '300', '-A', 'film-tools', '-o', dest, url], check=True)
        print('  ', os.path.relpath(dest, OUT), f'{os.path.getsize(dest) / 1e6:.1f} MB')
        return None
    return subprocess.run(['curl', '-sSL', '--fail', '-m', '60', '-A', 'film-tools', url], check=True, capture_output=True).stdout


def files(asset):
    return json.loads(curl(API + asset))


for name, res in TEXTURES.items():
    if os.path.exists(os.path.join(OUT, name, 'Rough.jpg')):
        continue
    print(name)
    f = files(name)
    for key in ('Diffuse', 'nor_gl', 'Rough'):
        curl(f[key][res]['jpg']['url'], os.path.join(OUT, name, f'{key}.jpg'))

for name, res in HDRIS.items():
    curl(files(name)['hdri'][res]['hdr']['url'], os.path.join(OUT, name, f'{name}.hdr'))

for name, res in MODELS.items():
    if os.path.exists(os.path.join(OUT, name, f'{name}.gltf')):
        continue
    print(name)
    g = files(name)['gltf'][res]['gltf']
    for rel, inc in g.get('include', {}).items():
        curl(inc['url'], os.path.join(OUT, name, rel))
    curl(g['url'], os.path.join(OUT, name, f'{name}.gltf'))

print('done:', OUT)
