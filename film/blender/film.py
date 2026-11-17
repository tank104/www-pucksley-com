"""The Pucksley film: one shot, one day. The card house stands on the real kitchen bench among the real
things, the puck in front of it. Somebody talks to the puck from first light to lights out, and the house
answers in light. Every time is clock.py's.

  blender -b -P film.py -- --scale 50 --samples 32 --device gpu                  # the low-quality cut's frames
  blender -b -P film.py -- --still 3,13,18,23,30,37,43,49,56,62 --scale 50       # single moments, to check
  options: --fps 12   --from 0 --to 64 (seconds)   --folder film   --resume (keep the frames already there)
           --reverse (last frame first, so a second Blender can meet the first in the middle)
           and puckkit.py's own: --scale --samples --device

Frames go to cache/<folder>/f0001.png and on; film_join.py finishes them and makes the film.
"""
import math
import os
import sys

import bpy
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import puckkit as K
import clock
import ideas

FPS = int(K.arg('fps', 12))
B = clock.BEAT
scene = K.scene
scene.render.fps = FPS
frame = lambda t: int(round(t * FPS)) + 1
smooth = lambda u: (lambda x: x * x * (3 - 2 * x))(min(1.0, max(0.0, u)))
mix = lambda a, b, u: tuple(x + (y - x) * u for x, y in zip(a, b)) if isinstance(a, tuple) else a + (b - a) * u
bpy.context.preferences.edit.keyframe_new_interpolation_type = 'LINEAR'


# ------------------------------------------------------------------ keyframes

def keys(owner, prop, pairs, index=-1):
    """Set owner.prop to each value at each time (seconds), a straight line between."""
    for t, v in pairs:
        if index >= 0:
            getattr(owner, prop)[index] = v
        else:
            setattr(owner, prop, v)
        owner.keyframe_insert(prop, frame=frame(t), index=index)


def steps(owner, prop, pairs, index=-1):
    """owner.prop jumps to each value at each time, and holds it until the next."""
    before = None
    for t, v in pairs:
        if before is not None and before != v and frame(t) > 1:        # hold the old value up to the frame before
            if index >= 0:
                getattr(owner, prop)[index] = before
            else:
                setattr(owner, prop, before)
            owner.keyframe_insert(prop, frame=frame(t) - 1, index=index)
        keys(owner, prop, [(t, v)], index)
        before = v


def eased(owner, prop, moves, index=-1, start=None):
    """owner.prop moves between values, easing in and out. moves: (from time, to time, value it arrives at).
    start: the value before the first move (what it is now, if not given)."""
    v0 = start if start is not None else (getattr(owner, prop)[index] if index >= 0 else getattr(owner, prop))
    pairs = [(0.0, v0)]
    for t0, t1, v1 in moves:
        n = max(1, int(round((t1 - t0) * FPS)))
        pairs += [(t0 + (t1 - t0) * i / n, mix(v0, v1, smooth(i / n))) for i in range(n + 1)]
        v0 = v1
    keys(owner, prop, pairs, index)


def emission(material):
    m = bpy.data.materials[material]
    return next(n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED').inputs['Emission Strength']


def glows(material, moves):
    eased(emission(material), 'default_value', moves, start=0.0)


def shines(light, moves):
    eased(light.data, 'energy', moves, start=0.0)


# ------------------------------------------------------------------ the set

K.table(K.surface('marble_01', size=1.4, turn=3, rough_scale=0.7))
H = ideas.moved((0.04, 0.2, 0), -7, ideas.card_house, film=True)
K.prop('pot_enamel_01', None, (-0.34, 0.3, 0), rot_z=2.6)
K.prop('wooden_spoon', None, (-0.3, 0.08, 0), rot_z=-0.5)
K.prop('tea_set_01', {'tea_set_01_saucer_circular_04'}, (0.26, 0.0, 0), rot_z=0.4)
K.prop('tea_set_01', {'tea_set_01_cup_small_01'}, (0.26, 0.0, 0.006), rot_z=2.2)
K.prop('potted_plant_04', None, (0.4, 0.42, 0), rot_z=0.7)

# ---- the puck, and what its screen shows when
PUCK = (-0.04, 0.085, 0)
puck = K.puck(PUCK, '31_film_idle_morning', glow_by=2.6)
FACE = '30_talking_face'                                     # the talking face: what the puck shows while it speaks
MORNING, PLAYING, TIMER, BANNER, NIGHT = '31_film_idle_morning', '32_film_home_playing', '34_film_timer', '35_film_banner', '05_assistant_idle'
SCREENS = [(0.0, MORNING),
           (B['weather'], '06_assistant_listening'), (B['weather'] + 3.0, FACE), (B['weather'] + 6.5, MORNING),
           (B['music'], '06_assistant_listening'), (B['music'] + 2.8, FACE), (B['music'] + 4.4, PLAYING),
           (B['turn'], '14_home_volume'), (B['turn'] + 2.6, PLAYING),
           (B['group'], '06_assistant_listening'), (B['group'] + 2.8, FACE), (B['group'] + 5.1, PLAYING),
           (B['timer'], '06_assistant_listening'), (B['timer'] + 2.6, FACE), (B['timer'] + 5.6, TIMER),
           (B['done'], BANNER), (B['done'] + 0.7, FACE), (B['done'] + 1.9, BANNER),
           (B['tv'], '06_assistant_listening'), (B['tv'] + 2.4, FACE), (B['tv'] + 3.2, '18_controls_action'),
           (B['lamp'], '06_assistant_listening'), (B['lamp'] + 1.2, '17_controls_lamp'),
           (B['heating'], '06_assistant_listening'), (B['heating'] + 2.8, FACE), (B['heating'] + 4.4, '16_controls_heating'),
           (B['pc'], '06_assistant_listening'), (B['pc'] + 1.9, FACE), (B['pc'] + 3.4, '22_confirm'), (B['pc'] + 5.2, '23_confirm_yes'), (B['pc'] + 6.4, NIGHT),
           (B['night'], '06_assistant_listening'), (B['night'] + 1.6, NIGHT), (B['night'] + 2.6, FACE), (B['night'] + 3.5, NIGHT)]
glass = {MORNING: next(o for o in puck.children if o.name.endswith('Glass'))}
for name in sorted({s for _, s in SCREENS}):                # one glass a screen; all but the one showing wait under the bench
    g = glass.get(name) or K.puck_glass(name, 2.6, 'Glass-' + name)
    g.parent = puck
    glass[name] = g
    steps(g, 'location', [(t, 0.0 if s == name else -0.5) for t, s in SCREENS], index=2)
talking = os.path.join(HERE, 'cache', f'face-seq-{FPS}')     # the face moving with the words (face_frames.py), if it has been made
if os.path.isdir(talking):
    node = next(n for n in glass[FACE].data.materials[0].node_tree.nodes if n.type == 'TEX_IMAGE')
    node.image = bpy.data.images.load(os.path.join(talking, 'f0001.jpg'))
    node.image.source = 'SEQUENCE'
    node.image_user.frame_start, node.image_user.frame_offset = 1, 0
    node.image_user.frame_duration = len(os.listdir(talking))
    node.image_user.use_auto_refresh = True
# The puck is turned like a dial, and springs back: its screen turns with it (the real one's does), and a
# face left lying on its side reads badly.
eased(puck, 'rotation_euler', [(B['turn'] + 0.2, B['turn'] + 1.5, math.radians(-42)), (B['turn'] + 2.2, B['turn'] + 3.2, 0.0),          # turned up
                                (B['pc'] + 4.4, B['pc'] + 5.2, math.radians(-28)), (B['pc'] + 6.3, B['pc'] + 7.0, 0.0)], index=2, start=0.0)      # turned to Yes

# ---- the house answering
shines(H['kitchen_light'], [(B['music'] + 2.6, B['music'] + 3.1, 0.22), (B['turn'] + 0.2, B['turn'] + 1.5, 0.32), (B['night'] + 1.7, B['night'] + 2.4, 0.0)])
glows('SpeakerOn', [(B['music'] + 2.6, B['music'] + 3.1, 3.0), (B['night'] + 1.7, B['night'] + 2.4, 0.0)])
for i, h in enumerate(H['kitchen_notes']):
    for axis in range(3):
        eased(h, 'scale', [(B['music'] + 2.6 + 0.3 * i, B['music'] + 3.5 + 0.3 * i, 1.0), (B['turn'] + 0.2, B['turn'] + 1.5, 1.3),
                           (B['night'] + 1.7 + 0.12 * i, B['night'] + 2.2 + 0.12 * i, 0.001)], index=axis, start=0.001)
shines(H['ensuite_light'], [(B['group'] + 2.8, B['group'] + 3.3, 0.16), (B['night'] + 1.9, B['night'] + 2.6, 0.0)])
glows('EnsuiteSpeaker', [(B['group'] + 2.8, B['group'] + 3.3, 3.0), (B['night'] + 1.9, B['night'] + 2.6, 0.0)])
for i, h in enumerate(H['ensuite_notes']):
    for axis in range(3):
        eased(h, 'scale', [(B['group'] + 2.8 + 0.3 * i, B['group'] + 3.7 + 0.3 * i, 1.0), (B['night'] + 1.9, B['night'] + 2.4, 0.001)], index=axis, start=0.001)
glows('TellyOn', [(29.0, 30.0, 4.0), (B['tv'] + 2.2, B['tv'] + 2.32, 0.0)])                    # left on in the afternoon
shines(H['tv_light'], [(29.0, 30.0, 0.05), (B['tv'] + 2.2, B['tv'] + 2.32, 0.0)])
glows('PcOn', [(33.0, 34.0, 4.0), (B['pc'] + 6.0, B['pc'] + 6.12, 0.0)])
shines(H['pc_light'], [(33.0, 34.0, 0.03), (B['pc'] + 6.0, B['pc'] + 6.12, 0.0)])
glows('LampShade', [(B['lamp'] + 1.2, B['lamp'] + 1.32, 3.0), (B['night'] + 2.1, B['night'] + 2.3, 0.0)])
shines(H['lamp_light'], [(B['lamp'] + 1.2, B['lamp'] + 1.32, 0.12), (B['night'] + 2.1, B['night'] + 2.3, 0.0)])
for k, (ix, fl) in enumerate(((0, 0), (1, 0), (2, 0), (0, 1), (1, 1), (2, 1))):                # the heating, a room at a time
    glows(f'Underfloor{ix}{fl}', [(B['heating'] + 2.6 + 0.3 * k, B['heating'] + 3.5 + 0.3 * k, 2.6)])

# ---- the day's light: the sun through the morning window, then the afternoon one, then the night
AT = (0, 0.15, 0.04)
direction = lambda az, el: Vector((math.cos(math.radians(el)) * math.sin(math.radians(az)), -math.cos(math.radians(el)) * math.cos(math.radians(az)), math.sin(math.radians(el))))
K.window(direction(150, 17), at=AT, w=1.2, h=0.7, ox=-0.2, oy=0.08, bar=0.03, bars=((-0.2, None), (0.18, None), (None, 0.0)))
K.window(direction(-46, 30), at=AT, w=0.8, h=0.6, oy=0.05, bars=((-0.14, None), (None, 0.04)))
M0, M1 = clock.MIDDAY
S0, S1 = clock.SUNSET
RISE = clock.SUNRISE


def morning_sun(t):
    """Through the back window: where it is, how strong and what colour, at film second t."""
    u = t / M1
    return 160 - 20 * u, 13 + 9 * u, 5.0 * smooth((t - RISE + 1.0) / 2.5) * (1 - smooth((t - M0) / (M1 - M0))), mix((1.0, 0.7, 0.46), (1.0, 0.9, 0.76), smooth(t / 6))


def afternoon_sun(t):
    """Through the side window. It comes in as the morning sun goes, so the bench is never without sun by day."""
    u = (t - M0) / (S1 - M0)
    return -40 - 14 * u, 32 - 8 * u, 3.3 * smooth((t - M0) / (M1 - M0)) * (1 - smooth((t - S0) / (S1 - S0))), mix((1.0, 0.86, 0.68), (1.0, 0.52, 0.28), smooth((t - (S0 - 7)) / 9))


for name, where in (('MorningSun', morning_sun), ('AfternoonSun', afternoon_sun)):
    li = bpy.data.lights.new(name, 'SUN')
    li.angle = math.radians(0.8)
    sun = K.link(bpy.data.objects.new(name, li))
    sun.rotation_mode = 'QUATERNION'
    last = None
    for i in range(int(clock.END * 4) + 1):                 # four times a second
        t = i / 4
        az, el, energy, colour = where(min(max(t, 0.0), S1))
        q = (-direction(az, el)).to_track_quat('-Z', 'Y')
        if last is not None and q.dot(last) < 0:
            q.negate()
        last = q
        sun.rotation_quaternion = q
        sun.keyframe_insert('rotation_quaternion', frame=frame(t))
        li.energy, li.color = max(0.0, energy), colour
        li.keyframe_insert('energy', frame=frame(t))
        li.keyframe_insert('color', frame=frame(t))

K.world(0.04, (0.38, 0.52, 1.0))
room = scene.world.node_tree.nodes
back = next(n for n in room if n.type == 'BACKGROUND').inputs['Strength']
tint = next(n for n in room if n.type == 'MIX_RGB').inputs['Color2']
NIGHT, DAY = (0.38, 0.52, 1.0, 1.0), (0.92, 0.96, 1.0, 1.0)
eased(back, 'default_value', [(RISE - 1.0, RISE + 2.5, 0.6), (M0, M1, 0.45), (S0, S1 + 1.5, 0.035)], start=0.05)
for c in range(4):
    eased(tint, 'default_value', [(RISE - 1.0, RISE + 2.5, DAY[c]), (S0, S1 + 1.5, NIGHT[c])], index=c, start=NIGHT[c])
moon = K.area((-1.5, 1.5, 1.2), (0, 0, 0), 12, size=1.2, color=(0.42, 0.58, 1.0), name='Moon')
eased(moon.data, 'energy', [(RISE - 1.0, RISE + 2.5, 0.0), (S0, S1 + 2.0, 16.0)], start=12.0)

# ---- the camera: one slow move through the day
#        when, what it looks at, from how far, how far round, how high
POSES = [(0.0, (0.0, 0.16, 0.07), 0.92, -12, 15), (8.5, (0.0, 0.16, 0.07), 0.86, -12, 15),
         (14.0, (-0.02, 0.15, 0.06), 0.62, -14, 19), (24.5, (-0.02, 0.15, 0.06), 0.6, -12, 19),          # in on the kitchen, for the music
         (28.5, (-0.06, 0.13, 0.045), 0.52, -18, 21), (34.0, (-0.06, 0.13, 0.045), 0.52, -16, 21),       # the puck and the pot, for the timer
         (38.5, (0.03, 0.17, 0.06), 0.62, -2, 17), (44.0, (0.03, 0.17, 0.065), 0.66, 4, 16),             # the lounge
         (48.5, (0.02, 0.17, 0.07), 0.72, 10, 15), (clock.END, (0.02, 0.17, 0.07), 0.8, 12, 15)]         # the whole house, at night
cd = bpy.data.cameras.new('Camera')
cd.lens, cd.sensor_width = 42, 36
cd.clip_start, cd.clip_end = 0.01, 100
cd.dof.use_dof, cd.dof.aperture_fstop, cd.dof.aperture_blades = True, 8.0, 7
cam = K.link(bpy.data.objects.new('Camera', cd))
look = K.link(bpy.data.objects.new('Look', None))
focus = K.link(bpy.data.objects.new('Focus', None))
focus.location = (-0.01, 0.14, 0.03)                        # between the puck and the house
cd.dof.focus_object = focus
track = cam.constraints.new('TRACK_TO')
track.target, track.track_axis, track.up_axis = look, 'TRACK_NEGATIVE_Z', 'UP_Y'
scene.camera = cam
for i in range(int(clock.END * 4) + 1):
    t = i / 4
    k = max(j for j, p in enumerate(POSES) if p[0] <= t)
    a, b = POSES[k], POSES[min(k + 1, len(POSES) - 1)]
    u = smooth((t - a[0]) / (b[0] - a[0])) if b[0] > a[0] else 0.0
    target, dist, az, el = Vector(mix(a[1], b[1], u)), mix(a[2], b[2], u), math.radians(mix(a[3], b[3], u)), math.radians(mix(a[4], b[4], u))
    look.location = target
    cam.location = target + Vector((math.cos(el) * math.sin(az), -math.cos(el) * math.cos(az), math.sin(el))) * dist
    look.keyframe_insert('location', frame=frame(t))
    cam.keyframe_insert('location', frame=frame(t))

# ---- render
K.setup(0.0)
scene.frame_start, scene.frame_end = 1, frame(clock.END)
scene.render.use_persistent_data = True
scene.render.use_motion_blur = True
scene.render.motion_blur_shutter = 0.5
scene.render.image_settings.color_depth = '8'
for t, v in [(0.0, 0.5), (RISE + 2.5, 0.45), (M0, 0.45), (M1 + 1.5, 0.0), (S0, 0.0), (S1 + 2.0, 0.35), (clock.END, 0.35)]:
    scene.view_settings.exposure = v
    scene.keyframe_insert('view_settings.exposure', frame=frame(t))

stills = K.arg('still', '')
if stills:
    for t in stills.split(','):
        scene.frame_set(frame(float(t)))
        scene.render.filepath = os.path.join(HERE, 'cache', f'film-still-{t}.png')
        bpy.ops.render.render(write_still=True)
        print('STILL', t)
else:
    folder = os.path.join(HERE, 'cache', K.arg('folder', 'film'))
    os.makedirs(folder, exist_ok=True)
    todo = range(frame(float(K.arg('from', 0))), frame(float(K.arg('to', clock.END))) + 1)
    for f in (reversed(todo) if '--reverse' in K.argv else todo):       # --reverse: a second Blender can work back from the end
        path = os.path.join(folder, f'f{f:04d}.png')
        if '--resume' in K.argv and os.path.exists(path) and os.path.getsize(path) > 1000:
            continue
        scene.frame_set(f)
        scene.render.filepath = path
        bpy.ops.render.render(write_still=True)
        print('FRAME', f, flush=True)
