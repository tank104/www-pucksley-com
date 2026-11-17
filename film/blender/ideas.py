"""Five ideas for the Pucksley film, each as three frames: an establishing shot, a beat by day and a beat
by night. One set an idea, built from puckkit.py.

  blender -b -P ideas.py -- --idea house --shot day --out cache/idea-house-day.png
  ideas:  house    One puck, the whole house: a white card model of a house that answers in light
          bench    A day on the bench: the real kitchen, from breakfast to bedtime, told by the light
          remotes  The last remote: a domino run of every grey controller in the house, ending at the puck
          apart    Taken apart: on the workbench, what is inside, the plugins, and the hub at home
          rings    Turn it: a black studio where the screen's rings of light are as big as the room
  ideas 1 and 2 together, three ways (mix.sh): zoomin, zoomout, together
  shots:  wide day night
  options: --scale 50 --samples 64 --device gpu   (see puckkit.py)

Run them all, finished and laid out as a sheet, with ideas.sh. pieces.py draws the printed cards first.
"""
import math
import os
import sys

import bpy
from mathutils import Matrix, Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import puckkit as K

IDEA = K.arg('idea', 'house')
SHOT = K.arg('shot', 'wide')
OUT = K.arg('out', os.path.join(K.HERE, 'cache', f'idea-{IDEA}-{SHOT}.png'))
cut = lambda name: os.path.join(K.CUT, name + '.png')


# ------------------------------------------------------------------ 1. the model house

def card_house(music=False, heating=False, lamp=False, tiny=(), film=False):
    """A white card model of a house, cut open at the front (-Y), standing on the origin. Nothing in it has
    any colour until the house does something: music lights the kitchen yellow and sends notes up out of
    its speaker, heating glows terracotta under every floor, lamp lights a bedside lamp.
    tiny: (room across, floor, colour) for each room that has a tiny puck of its own.
    film: build everything the film switches on and off (the ensuite's speaker, the television and the
    study's screen alight, a lamp in the lounge, the heating a room at a time) and hand it all back."""
    if film:
        music = heating = True
    made = {}
    white = K.card()
    grey = K.card('GreyCard', (0.42, 0.42, 0.43))
    T, RW, RH, RD = 0.003, 0.085, 0.062, 0.075                 # card thickness; a room's width, height, depth
    W = 3 * RW + 4 * T
    top = T + 2 * RH + 2 * T                                   # the top of the upper ceiling
    room = lambda ix, fl: (-W / 2 + T + RW / 2 + ix * (RW + T), T + fl * (RH + T))      # a room's centre across, and its floor
    K.box((W + 0.06, RD + 0.06, T), (0, RD / 2, T / 2), grey, name='Base')
    for fl in (1, 2):                                          # the upper floor and the ceiling
        K.box((W, RD, T), (0, RD / 2, T + fl * RH + (fl - 1) * T + T / 2), white)
    for i in range(4):                                         # the walls between rooms
        K.box((T, RD, top - T), (-W / 2 + T / 2 + i * (RW + T), RD / 2, T + (top - T) / 2), white)
    back = K.box((W, T, top - T), (0, RD - T / 2, T + (top - T) / 2), white, name='Back')
    for ix in range(3):                                        # a window in the back of every room
        for fl in range(2):
            x, z = room(ix, fl)
            hole = K.box((0.03, 0.02, 0.026), (x, RD - T / 2, z + RH * 0.56), white, name='Hole')
            hole.hide_render = True
            b = back.modifiers.new('Window', 'BOOLEAN')
            b.operation, b.object = 'DIFFERENCE', hole
    rise, half = 0.062, W / 2 + 0.012                          # the roof: two slopes and the gable behind them
    slope = math.hypot(half, rise)
    a = math.degrees(math.atan2(rise, half))
    for side in (-1, 1):
        K.box((slope, RD + 0.02, T), (side * half / 2, RD / 2, top + rise / 2 + T / 2), white, rot=(0, side * a, 0))
    me = bpy.data.meshes.new('Gable')
    me.from_pydata([(-W / 2, RD, top), (W / 2, RD, top), (0, RD, top + rise * (W / 2) / half), (-W / 2, RD - T, top), (W / 2, RD - T, top), (0, RD - T, top + rise * (W / 2) / half)],
                   [], [(0, 1, 2), (5, 4, 3), (0, 3, 4, 1), (1, 4, 5, 2), (2, 5, 3, 0)])
    me.materials.append(white)
    K.link(bpy.data.objects.new('Gable', me))
    K.box((0.018, 0.018, 0.05), (W * 0.27, RD * 0.6, top + 0.045), white)       # the chimney

    def put(size, ix, fl, dx, dy, dz=0.0, mat=white, bevel=0.0):
        x, z = room(ix, fl)
        return K.box(size, (x + dx, dy, z + dz + size[2] / 2), mat, bevel=bevel)
    # kitchen: a counter along the back with a pot on it, a table and two stools, a speaker
    kx, kz = room(0, 0)
    put((0.07, 0.02, 0.024), 0, 0, 0, RD - 0.014)
    K.disc(0.0055, 0.007, (kx - 0.018, RD - 0.015, kz + 0.024), white)
    K.disc(0.013, 0.017, (kx - 0.012, 0.03, T), white)
    for dx in (-0.034, 0.012):
        K.disc(0.005, 0.01, (kx + dx, 0.022, T), white)
    speaker = put((0.012, 0.011, 0.02), 0, 0, 0.024, RD - 0.016, 0.024, K.solid('SpeakerOn', (0.9, 0.6, 0.0), emit=3.0, emit_color=K.YELLOW) if music else white)
    # lounge: a sofa, a rug and the television on the wall
    put((0.046, 0.02, 0.01), 1, 0, -0.006, 0.03)
    put((0.046, 0.006, 0.022), 1, 0, -0.006, 0.043)
    put((0.036, 0.002, 0.021), 1, 0, -0.022, RD - T - 0.001, 0.008, K.solid('Telly', (0.03, 0.03, 0.035), rough=0.2))
    # study: a desk, a screen and a chair
    put((0.05, 0.022, 0.003), 2, 0, 0.006, RD - 0.02, 0.024)
    for dx in (-0.016, 0.028):
        put((0.003, 0.02, 0.024), 2, 0, dx, RD - 0.02)
    put((0.022, 0.002, 0.014), 2, 0, 0.004, RD - 0.016, 0.031, K.solid('Telly', (0.03, 0.03, 0.035)))
    put((0.012, 0.012, 0.012), 2, 0, 0.002, 0.03)
    # bedrooms either side upstairs, the bathroom between
    for ix, dx in ((0, -0.012), (2, 0.012)):
        put((0.034, 0.05, 0.01), ix, 1, dx, RD - 0.03)
        put((0.034, 0.004, 0.024), ix, 1, dx, RD - 0.006)
        put((0.022, 0.012, 0.004), ix, 1, dx, RD - 0.014, 0.01)
        put((0.012, 0.012, 0.014), ix, 1, dx + (0.03 if ix == 0 else -0.03), RD - 0.012)
    put((0.05, 0.024, 0.016), 1, 1, -0.008, RD - 0.018, bevel=0.004)
    put((0.012, 0.012, 0.03), 1, 1, 0.03, RD - 0.012)

    wire = K.solid('Wire', (0.75, 0.75, 0.75), rough=0.4, metal=1.0)
    note = K.solid('Note', (0.9, 0.6, 0.0), emit=2.2, emit_color=K.YELLOW)

    def notes(at, offsets):
        """Notes on wires out of a speaker at `at`. Each hangs from a handle there, which the film scales."""
        handles = []
        for dx, dy, h in offsets:
            hold = K.link(bpy.data.objects.new('NoteHandle', None))
            hold.location = at
            p = Vector((at[0] + dx, at[1] + dy, at[2] + h))
            bits = [K.rod(at, p, 0.00025, wire), K.disc(0.0042, 0.0016, p + Vector((0, 0.0008, -0.003)), note, rot=(90, 0, 20)),
                    K.rod(p + Vector((0.0036, 0, 0)), p + Vector((0.0036, 0, 0.013)), 0.0005, note), K.box((0.006, 0.001, 0.003), p + Vector((0.0062, 0, 0.0118)), note, rot=(0, 20, 0))]
            for b in bits:
                b.parent = hold
                b.matrix_parent_inverse = Matrix.Translation(Vector(at)).inverted()
            handles.append(hold)
        return handles
    if music:
        made['kitchen_light'] = K.point((kx, 0.03, kz + 0.045), 0.22, K.YELLOW, soft=0.006, name='KitchenLight')
        sx, sy, sz = speaker.location
        made['kitchen_notes'] = notes((sx, sy, sz + 0.01), ((-0.02, -0.03, 0.03), (0.01, -0.052, 0.058), (-0.045, -0.062, 0.09)))
    if film:
        ex, ez = room(1, 1)                                    # the ensuite: its own speaker on the tall cupboard, its own light
        K.box((0.01, 0.01, 0.014), (ex + 0.03, RD - 0.012, ez + 0.037), K.solid('EnsuiteSpeaker', (0.9, 0.6, 0.0), emit=3.0, emit_color=K.YELLOW))
        made['ensuite_light'] = K.point((ex, 0.03, ez + 0.045), 0.16, K.YELLOW, soft=0.006, name='EnsuiteLight')
        made['ensuite_notes'] = notes((ex + 0.03, RD - 0.012, ez + 0.044), ((-0.03, -0.04, 0.02), (0.004, -0.06, 0.004)))
        lx, lz = room(1, 0)                                    # the lounge: the television alight, and a standing lamp
        K.box((0.034, 0.0006, 0.019), (lx - 0.022, RD - T - 0.0024, lz + 0.0185), K.glow('TellyOn', (0.25, 0.5, 1.0), 4.0))
        made['tv_light'] = K.point((lx - 0.02, RD - 0.02, lz + 0.02), 0.05, (0.3, 0.55, 1.0), soft=0.01, name='TellyLight')
        K.rod((lx + 0.03, 0.05, lz), (lx + 0.03, 0.05, lz + 0.034), 0.0006, wire)
        K.disc(0.006, 0.008, (lx + 0.03, 0.05, lz + 0.032), K.solid('LampShade', (0.9, 0.8, 0.62), emit=3.0, emit_color=(1.0, 0.72, 0.42)), n=24)
        made['lamp_light'] = K.point((lx + 0.03, 0.05, lz + 0.03), 0.12, (1.0, 0.72, 0.42), soft=0.005, name='LoungeLamp')
        px_, pz_ = room(2, 0)                                  # the study: its screen alight
        K.box((0.02, 0.0006, 0.012), (px_ + 0.004, RD - 0.0174, pz_ + 0.038), K.glow('PcOn', (0.6, 0.75, 1.0), 4.0))
        made['pc_light'] = K.point((px_ + 0.004, RD - 0.03, pz_ + 0.04), 0.03, (0.6, 0.75, 1.0), soft=0.008, name='PcLight')
    if heating:
        for ix in range(3):                                    # the heating, under every floor
            for fl in range(2):
                x, z = room(ix, fl)
                K.box((RW - 0.008, RD - 0.012, 0.0006), (x, RD / 2 - 0.002, z + 0.0004), K.glow(f'Underfloor{ix}{fl}' if film else 'Underfloor', K.TERRACOTTA, 2.6))
    if lamp:
        x, z = room(0, 1)
        K.point((x + 0.018, RD - 0.014, z + 0.024), 0.012, (1.0, 0.72, 0.42), soft=0.004, name='BedsideLamp')
    for n, (ix, fl, colour) in enumerate(tiny):                # a tiny puck: on the kitchen table, on a bedside table
        x, z = room(ix, fl)
        at = (x - 0.012, 0.03, z + 0.017) if fl == 0 else (x - 0.012 + (0.03 if ix == 0 else -0.03), RD - 0.012, z + 0.014)
        K.disc(0.0034, 0.0017, at, K.aluminium(), n=32)
        K.disc(0.003, 0.0003, (at[0], at[1], at[2] + 0.0017), K.glow(f'TinyScreen{n}', colour, 9.0), n=32)
    return dict(room=room, RD=RD, W=W, **made)


def moved(loc, turn, build, *args, **kw):
    """Build something at the origin, then put all of it at loc, turned by turn degrees."""
    before = set(bpy.data.objects)
    out = build(*args, **kw)
    root = K.link(bpy.data.objects.new('Group', None))
    for o in bpy.data.objects:
        if o not in before and o is not root and o.parent is None:
            o.parent = root
    root.location, root.rotation_euler = loc, (0, 0, math.radians(turn))
    return out


def desk():
    K.table(K.surface('oak_veneer_01', size=0.7, turn=4))


def house(shot=None):
    """A white card model of a house, cut open at the front, on a desk. The puck lies in front of it, as
    big as a room. Ask for something and that room answers in light: yellow for the music in the
    kitchen, terracotta for the heating under every floor. Nothing else in the house has any colour."""
    shot = shot or SHOT
    desk()
    room = card_house(music=shot == 'day', heating=shot == 'night', lamp=shot == 'night')['room']
    px = room(0, 0)[0] + 0.03                                  # the puck, in front of the kitchen
    if shot == 'wide':
        K.puck((px, -0.075, 0), '05_assistant_idle', glow_by=3.0)
        K.daylight(az=-58, el=27, at=(0, 0, 0.05), w=0.9, h=0.5, oy=0.06, bars=((-0.2, None), (0.12, None), (None, 0.05)), fill=0.5)
        K.prop('potted_plant_04', None, (0.42, 0.34, 0), rot_z=0.7)
        K.prop('book_encyclopedia_set_01', None, (-0.47, 0.3, 0), rot_z=0.35)
        K.camera((0.0, 0.0, 0.075), 0.74, -16, 15, lens=40, fstop=5.6, focus=(0, 0, 0.07))
        return 0.1
    if shot == 'day':
        K.puck((px, -0.075, 0), '13_home_playing', glow_by=3.2)
        kx = room(0, 0)[0]
        K.daylight(az=-42, el=30, at=(kx, 0, 0.04), w=0.7, h=0.4, oy=0.05, bars=((-0.12, None), (None, 0.04)), energy=4.2, fill=0.4)
        K.camera((kx + 0.04, -0.02, 0.06), 0.56, -14, 20, lens=50, fstop=6.3, focus=(px, -0.05, 0.02))
        return 0.0
    K.puck((px, -0.075, 0), '16_controls_heating', glow_by=1.6)
    K.moonlight(energy=16, fill=0.03)
    K.camera((0.0, 0.0, 0.065), 0.56, 12, 14, lens=45, fstop=4.5, focus=(0, 0, 0.06))
    return 0.3


# ------------------------------------------------------------------ 2. a day on the bench

def bench(shot=None):
    """The real kitchen bench, at true size, the camera down among the things on it. One day, told by the
    light: a question over breakfast, the pasta timer at dinner, the house asleep. Photographic, the way
    "The Fable of Clawd" is."""
    shot = shot or SHOT
    K.table(K.surface('marble_01', size=1.4, turn=3, rough_scale=0.7))
    if shot == 'wide':
        K.puck((0, 0, 0), '06_assistant_listening', glow_by=3.4)
        K.prop('tea_set_01', {'tea_set_01_saucer_circular_04'}, (0.2, 0.06, 0), rot_z=0.4)
        K.prop('tea_set_01', {'tea_set_01_cup_small_01'}, (0.2, 0.06, 0.006), rot_z=2.2)
        K.prop('tea_set_01', {'tea_set_01_plate_large_circular_03'}, (-0.15, 0.2, 0), rot_z=0.1)
        K.prop('croissant', None, (-0.15, 0.2, 0.01), rot_z=0.6)
        K.prop('potted_plant_04', None, (0.36, 0.5, 0), rot_z=0.7)
        K.prop('food_apple_01', None, (-0.05, 0.4, 0), rot_z=1.1)
        K.daylight(az=150, el=15, energy=5.0, color=(1.0, 0.9, 0.76), fill=0.6, tint=(0.92, 0.96, 1.0), w=1.1, h=0.7, ox=-0.25, oy=0.05, bar=0.03, bars=((-0.2, None), (0.18, None), (None, 0.0)))
        K.camera((0.02, 0.08, 0.02), 0.46, -12, 20, lens=40, fstop=4.0, focus=(0, 0, 0.012))
        return 0.45
    if shot == 'day':
        K.puck((-0.05, -0.02, 0), '20_timer_running', glow_by=3.2)
        K.prop('wooden_cutting_board', None, (0.2, 0.3, 0), rot_z=0.25)
        K.prop('pot_enamel_01', None, (-0.12, 0.3, 0), rot_z=2.6)
        K.prop('wooden_spoon', None, (0.19, 0.1, 0), rot_z=-1.0)
        K.prop('potted_plant_04', None, (-0.34, 0.5, 0), rot_z=0.3)
        K.daylight(az=62, el=20, energy=5.2, color=(1.0, 0.74, 0.5), fill=0.34, w=0.7, h=0.4, oy=0.05, bars=((0.1, None), (None, 0.03)))
        K.camera((0.0, 0.07, 0.03), 0.5, -8, 22, lens=45, fstop=4.0, focus=(-0.05, -0.02, 0.012))
        return 0.1
    K.puck((0, 0, 0), '05_assistant_idle', glow_by=1.5)
    K.prop('tea_set_01', {'tea_set_01_cup_small_01'}, (0.1, 0.11, 0), rot_z=0.8)
    K.prop('potted_plant_04', None, (-0.2, 0.36, 0), rot_z=0.3)
    K.prop('pot_enamel_01', None, (0.34, 0.42, 0), rot_z=2.6)
    K.moonlight(energy=14, fill=0.03)
    K.area((0.5, 0.9, 0.35), (0.1, 0.3, 0), 3.0, size=0.5, color=(1.0, 0.7, 0.42), name='HallLight')      # a light left on down the hall
    K.camera((0.02, 0.05, 0.02), 0.3, 7, 24, lens=45, fstop=3.2, focus=(0, 0, 0.012))
    return 0.4


# ------------------------------------------------------------------ 3. the last remote

REMOTES = [  # width, thickness, height, grey, rows of buttons, columns
    (0.046, 0.015, 0.17, 0.16, 6, 3), (0.04, 0.014, 0.155, 0.34, 5, 3), (0.05, 0.016, 0.185, 0.09, 7, 3), (0.036, 0.013, 0.14, 0.24, 4, 2), (0.044, 0.015, 0.165, 0.5, 6, 3)]


def remote(kind):
    """One remote control standing on its end: local Y is the way it will fall, Z is up, the buttons face +Y."""
    w, t, h, g, rows, cols = REMOTES[kind]
    body = K.box((w, t, h), (0, 0, 0), K.solid(f'Remote{kind}', (g, g, g * 1.03), rough=0.42), bevel=min(0.004, t * 0.3), name='Remote')
    body.data.transform(Matrix.Translation((0, 0, h / 2)))
    knob = K.solid(f'RemoteButton{kind}', (g * 0.55 + 0.03,) * 3, rough=0.6)
    bits = [K.disc(w * 0.27, 0.0012, (0, t / 2, h * 0.76), knob, rot=(-90, 0, 0), n=32)]       # the round pad near the top
    for r in range(rows):
        for c in range(cols):
            x = (c - (cols - 1) / 2) * w * 0.26
            bits.append(K.box((w * 0.17, 0.0016, w * 0.11), (x, t / 2, h * 0.56 - r * h * 0.085), knob, bevel=0.0006))
    for b in bits:
        b.parent = body
    return body, t, h


def phone():
    w, t, h = 0.071, 0.008, 0.146
    body = K.box((w, t, h), (0, 0, 0), K.solid('PhoneBody', (0.07, 0.07, 0.075), rough=0.3, metal=0.6), bevel=0.003, name='Phone')
    body.data.transform(Matrix.Translation((0, 0, h / 2)))
    scr = K.stand(w - 0.006, h - 0.008, (0, t / 2 + 0.0002, 0.004), K.print_mat('PhoneScreen', cut('phone'), rough=0.08, emit=0.15, coat=0.5), turn=180, thick=0.0002)
    scr.parent = body
    return body, t, h


def switch():
    w, t, h = 0.086, 0.011, 0.086
    body = K.box((w, t, h), (0, 0, 0), K.solid('SwitchPlate', (0.55, 0.55, 0.56), rough=0.35), bevel=0.003, name='Switch')
    body.data.transform(Matrix.Translation((0, 0, h / 2)))
    rocker = K.box((0.026, 0.004, 0.04), (0, t / 2, h / 2), K.solid('Rocker', (0.42, 0.42, 0.43), rough=0.3), rot=(6, 0, 0), bevel=0.001)
    rocker.parent = body
    return body, t, h


def remotes():
    """Every controller in the house, all grey, standing on end in one long domino run across the table.
    At the end of the run lies the puck. They go down, one into the next, and the last one taps it awake.
    The one colour in the film is the puck's screen."""
    K.table(K.surface('black_walnut_veneer_01', size=1.1, turn=86, rough_scale=0.85, tint=(0.34, 0.3, 0.29)), size=(4.0, 3.2), at=(0, 0.6, 0))
    step, first = 0.055, 0.205                                  # between pieces; from the puck to the nearest

    def path(t):                                                # the run, t from the puck's end to the far end
        return Vector((0.2 * math.sin(2.0 * math.pi * t) * t ** 0.7, first + 1.0 * t, 0))
    pts, t, last = [path(0)], 0.0, path(0)
    while t < 1.0:                                              # walk it in equal steps
        t += 0.0005
        if (path(t) - last).length >= step:
            last = path(t)
            pts.append(last)
    # how far each has fallen, in degrees from upright: by shot, counted from the puck's end
    fallen = lambda front_t: 90 - math.degrees(math.atan2(front_t + 0.0005, step))
    lean = {'wide': {}, 'day': {1: 9, 2: 21, 3: 33, 4: 45, 5: 55, 6: 66}, 'night': {}}[SHOT]
    order = [0, 1, 0, 4, 2, 0, 1, 'phone', 3, 0, 2, 'switch', 4, 1, 0, 'phone', 2, 3, 0, 1, 4, 'switch', 2, 0, 1, 3]
    front_t = 0.0
    for i, p in enumerate(pts):
        kind = order[i % len(order)]
        body, th, h = phone() if kind == 'phone' else switch() if kind == 'switch' else remote(kind)
        nxt = pts[i + 1] if i + 1 < len(pts) else p + (p - pts[i - 1])
        d = (p - nxt).normalized()                              # the way it falls: towards the puck
        heading = math.atan2(-d.x, d.y)
        if SHOT == 'night':
            tilt = 90.0 if i == 0 else fallen(front_t)
        elif SHOT == 'day':
            tilt = lean.get(i, 0 if i < 1 else fallen(front_t)) if i <= 6 else fallen(front_t)
        else:
            tilt = 0.0
        pivot = Matrix.Translation((0, th / 2, 0))
        body.matrix_world = Matrix.Translation(p) @ Matrix.Rotation(heading, 4, 'Z') @ pivot @ Matrix.Rotation(-math.radians(tilt), 4, 'X') @ pivot.inverted()
        front_t = th

    if SHOT == 'wide':
        K.puck((0, 0, 0), '05_assistant_idle', glow_by=3.2)
        K.daylight(az=128, el=17, at=(0, 0.4, 0), energy=5.5, color=(1.0, 0.86, 0.66), fill=0.5, w=1.6, h=0.8, oy=0.1, bar=0.035, bars=((-0.4, None), (0.2, None)))
        K.camera((0.03, 0.31, 0.0), 1.05, -6, 31, lens=35, fstop=5.6, focus=(0, 0.1, 0.03))
        return 0.5
    if SHOT == 'day':
        K.puck((0, 0, 0), '05_assistant_idle', glow_by=3.2)
        K.daylight(az=128, el=28, at=(0, 0.2, 0), energy=5.5, fill=0.55, w=1.2, h=0.6, oy=0.08, bars=((-0.25, None), (0.2, None), (None, 0.06)))
        K.camera((0.0, 0.2, 0.06), 0.62, -78, 11, lens=40, fstop=5.6, focus=(0, 0.2, 0.06))
        return 0.1
    K.puck((0, 0, 0), '17_controls_lamp', glow_by=1.8)
    K.moonlight(energy=10, fill=0.025)
    K.spot((-0.3, -0.12, 0.42), (0.0, 0.05, 0), 9, cone=40, blend=0.8, soft=0.03, name='Lamp')
    K.camera((0.0, 0.14, 0.01), 0.52, 15, 19, lens=40, fstop=3.5, focus=(0, 0, 0.012))
    return 0.6


# ------------------------------------------------------------------ 4. taken apart

def apart():
    """On the workbench, for people who make things. The puck comes apart in the air above a cutting mat,
    each part with its label; put back together, the plugins stand round it like a hand of cards, with
    one left blank for yours; at night it is on the shelf with the hub it talks to."""
    K.table(K.surface('plywood', size=1.0, turn=2))
    K.sheet(0.6, 0.425, (0, 0.06, 0), K.print_mat('Mat', cut('mat'), rough=0.75), thick=0.003, back=K.solid('MatEdge', (0.02, 0.09, 0.07), rough=0.8))
    Z = 0.0032                                                  # the top of the mat
    wire = K.solid('Wire', (0.75, 0.75, 0.75), rough=0.4, metal=1.0)

    if SHOT == 'wide':
        alu, k = K.aluminium(), 0.001
        # the case, an empty cup
        K.place(K.lathe([[(0, 0)] + K.corner(K.R_CASE - 1.6 * k, 1.6 * k, 1.6 * k, -90, 0) + K.corner(K.R_CASE - 1.0 * k, K.H_CASE - 1.0 * k, 1.0 * k, 0, 90),
                         [(K.R_CASE - 1.0 * k, K.H_CASE), (K.R_CASE - 1.6 * k, K.H_CASE)], [(K.R_CASE - 1.6 * k, K.H_CASE), (K.R_CASE - 1.6 * k, 1.4 * k)],
                         [(K.R_CASE - 1.6 * k, 1.4 * k), (0, 1.4 * k)]], alu, name='Cup'), (0, 0, Z))
        zs = dict(battery=0.034, speaker=0.058, board=0.082, glass=0.112)
        K.box((0.032, 0.024, 0.0052), (-0.002, 0, Z + zs['battery']), K.solid('Pouch', (0.62, 0.64, 0.68), rough=0.3, metal=1.0), bevel=0.0016, name='Battery')
        K.box((0.03, 0.0245, 0.001), (-0.002, 0, Z + zs['battery'] + 0.0031), K.solid('PouchLabel', (0.85, 0.62, 0.1), rough=0.5))
        K.disc(0.0095, 0.0042, (0.004, 0.002, Z + zs['speaker']), K.solid('SpeakerCan', (0.3, 0.3, 0.31), rough=0.35, metal=1.0), bevel=0.0008, name='Speaker')
        K.disc(0.0075, 0.0006, (0.004, 0.002, Z + zs['speaker'] + 0.0042), K.solid('Cone', (0.02, 0.02, 0.02), rough=0.8))
        zb = Z + zs['board']
        K.disc(0.0225, 0.0012, (0, 0, zb), K.solid('Board', (0.012, 0.03, 0.022), rough=0.45, coat=0.4), name='Board')
        chip = K.solid('Chip', (0.02, 0.02, 0.022), rough=0.4)
        can = K.solid('Can', (0.7, 0.7, 0.72), rough=0.3, metal=1.0)
        gold = K.solid('Gold', (0.9, 0.62, 0.2), rough=0.3, metal=1.0)
        K.box((0.013, 0.0115, 0.0022), (-0.004, 0.006, zb + 0.0023), can, bevel=0.0004)
        for x, y, sx, sy in ((0.009, -0.004, 0.006, 0.006), (-0.008, -0.01, 0.005, 0.004), (0.011, 0.01, 0.004, 0.004), (0.001, -0.014, 0.004, 0.003)):
            K.box((sx, sy, 0.0009), (x, y, zb + 0.00165), chip)
        for x in (-0.016, 0.016):                               # the two microphones
            K.box((0.0035, 0.0026, 0.001), (x, 0.013, zb + 0.0017), can)
        K.box((0.009, 0.0035, 0.0028), (0, 0.0203, zb + 0.0026), can, bevel=0.0005)        # the USB socket
        for a in range(0, 360, 30):
            K.disc(0.0006, 0.0003, (0.0205 * math.cos(math.radians(a + 15)), 0.0205 * math.sin(math.radians(a + 15)), zb + 0.0012), gold, n=12)
        glass = K.lathe([[(0, 0.0012), (K.R_GLASS - 0.35 * k, 0.0012)] + K.corner(K.R_GLASS - 0.35 * k, 0.00085, 0.35 * k, 90, 0, 4), [(K.R_GLASS, 0.00085), (K.R_GLASS, 0)], [(K.R_GLASS, 0), (0, 0)]],
                        K.screen_mat('05_assistant_idle', 3.0), name='Glass', uv_radius=K.R_SCREEN)
        glass.location = (0, 0, Z + zs['glass'])
        for a in (90, 210, 330):                                # three wires the parts are threaded on
            x, y = 0.0212 * math.cos(math.radians(a)), 0.0212 * math.sin(math.radians(a))
            K.rod((x, y, Z + 0.004), (x, y, Z + zs['glass']), 0.0002, wire)

        def label(key, z, side):
            x = side * 0.082
            K.rod((x, 0.012, Z), (x, 0.012, Z + z), 0.0005, wire)
            K.stand(0.058, 0.0242, (x, 0.011, Z + z - 0.012), K.print_mat('Label-' + key, cut('label-' + key)), turn=side * -14)
            K.rod((x - side * 0.03, 0.011, Z + z), (side * 0.028, 0.004, Z + z + 0.001), 0.00022, wire)
        label('screen', zs['glass'] + 0.002, 1)
        label('board', zs['board'] + 0.001, -1)
        label('speaker', zs['speaker'] + 0.002, 1)
        label('battery', zs['battery'] + 0.002, -1)
        label('case', 0.012, 1)
        K.prop('screwdriver', None, (0.17, 0.1, Z), rot_z=1.9, tilt=math.radians(90))
        K.prop('pliers', None, (-0.17, 0.12, Z), rot_z=-0.5, tilt=math.radians(90))
        K.daylight(az=-52, el=34, at=(0, 0, 0.05), energy=5.0, fill=0.55, w=0.9, h=0.5, oy=0.06, bars=((-0.18, None), (None, 0.05)))
        K.camera((0.0, 0.0, 0.06), 0.45, -9, 17, lens=50, fstop=6.3, focus=(0, 0, 0.07))
        return 0.0
    if SHOT == 'day':
        K.puck((0, -0.045, Z), '08_assistant_speaking', glow_by=3.2)
        keys = ['sonos', 'spotify', 'tv', 'plugs', 'heating', 'yours', 'weather', 'timers', 'pc', 'lists']
        for i, key in enumerate(keys):                          # the plugins, in an arc round the puck
            a = math.radians(-58 + 116 * i / (len(keys) - 1))
            r = 0.15
            x, y = r * math.sin(a), -0.045 + r * math.cos(a)
            K.stand(0.046, 0.0644, (x, y, Z), K.print_mat('Plugin-' + key, cut('plugin-' + key)), turn=-math.degrees(a), lean=9, thick=0.0008)
            K.box((0.01, 0.012, 0.012), (x + 0.012 * math.sin(a), y + 0.012 * math.cos(a), Z + 0.006), K.card('Foot', (0.8, 0.79, 0.76)), rot=(0, 0, -math.degrees(a)))
        K.prop('screwdriver', None, (0.2, 0.22, Z), rot_z=2.2, tilt=math.radians(90))
        K.daylight(az=-46, el=38, at=(0, 0.05, 0.03), energy=4.6, fill=0.55, w=0.9, h=0.5, oy=0.06, bars=((-0.18, None), (None, 0.05)))
        K.camera((0.0, 0.02, 0.022), 0.4, 0, 30, lens=45, fstop=8.0, focus=(0, 0.02, 0.02))
        return 0.0
    # night: the hub at home, and the puck beside it
    K.puck((-0.07, -0.02, Z), '05_assistant_idle', glow_by=1.6)
    nas = (0.13, 0.3)
    dark = K.solid('NasBody', (0.02, 0.02, 0.022), rough=0.4)
    K.box((0.11, 0.2, 0.16), (nas[0], nas[1], Z + 0.08), dark, bevel=0.004, name='Nas')
    for i in range(2):                                          # two drive bays, and a light for each
        K.box((0.04, 0.002, 0.12), (nas[0] - 0.022 + i * 0.046, nas[1] - 0.1, Z + 0.086), K.solid('Bay', (0.035, 0.035, 0.04), rough=0.3), bevel=0.0008)
        K.disc(0.0016, 0.0006, (nas[0] - 0.036 + i * 0.046, nas[1] - 0.1012, Z + 0.154), K.glow('Led', K.GREEN, 8.0), rot=(90, 0, 0), n=16)
    K.disc(0.002, 0.0006, (nas[0] + 0.046, nas[1] - 0.1012, Z + 0.016), K.glow('LedBlue', (0.1, 0.4, 1.0), 8.0), rot=(90, 0, 0), n=16)
    bead = K.glow('Bead', K.TERRACOTTA, 9.0)
    a, b = Vector((-0.045, -0.006, Z + 0.0016)), Vector((nas[0] - 0.03, nas[1] - 0.105, Z + 0.0016))
    for i in range(1, 13):                                      # the link between them: a dotted line of light
        u = i / 13
        p = a.lerp(b, u) + Vector((0.03 * math.sin(u * math.pi), -0.02 * math.sin(u * math.pi), 0))
        bpy.ops.mesh.primitive_uv_sphere_add(segments=16, ring_count=8, radius=0.0016, location=p)
        bpy.context.object.data.materials.append(bead)
    K.stand(0.058, 0.0242, (0.0, 0.16, Z + 0.03), K.print_mat('Label-hub', cut('label-hub')), turn=-10)
    K.rod((0.0, 0.161, Z), (0.0, 0.161, Z + 0.042), 0.0005, wire)
    K.prop('screwdriver', None, (-0.22, 0.12, Z), rot_z=0.5, tilt=math.radians(90))
    K.moonlight(energy=12, fill=0.03)
    K.spot((-0.36, -0.1, 0.4), (0.02, 0.08, 0.03), 18, cone=50, blend=0.85, soft=0.03, name='Lamp')
    K.camera((0.03, 0.1, 0.05), 0.58, -5, 21, lens=45, fstop=5.6, focus=(-0.04, 0.03, 0.012))
    return 0.2


# ------------------------------------------------------------------ 5. turn it

def rings():
    """A black studio, nothing in it but the puck. Whatever ring is on its screen stands behind it as big
    as the room, the number inside: turn the puck and the big ring turns. No props, no house, no words
    but the ones on the screen: a product film."""
    bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 0.5, 0))
    floor = bpy.context.object
    floor.scale = (8, 8, 1)
    floor.data.materials.append(K.solid('Gloss', (0.006, 0.006, 0.007), rough=0.16, coat=0.3))
    K.black_world(0.0)
    track = K.solid('Track', (0.02, 0.022, 0.02), rough=0.35)
    K.area((0.0, -0.3, 0.6), (0, 0, 0), 2.2, size=0.5, color=(0.8, 0.88, 1.0), name='Top')          # just enough to find the case

    if SHOT == 'wide':
        K.puck((0, 0, 0), '05_assistant_idle', glow_by=2.4)
        for r, col, a0, a1, name in ((0.075, K.TERRACOTTA, 250, -40, 'A'), (0.135, K.YELLOW, 200, 80, 'B'), (0.2, K.WHITE, 120, -70, 'C'), (0.275, K.GREEN, 205, 150, 'D')):
            K.arc(r, 0, 360, 0.0016, (0, 0, 0.0016), track, name='Track' + name)
            K.arc(r, a0, a1, 0.0024, (0, 0, 0.0024), K.glow('Ring' + name, col, 14.0), name='Ring' + name)
        K.camera((0, 0.03, 0.0), 0.7, 0, 33, lens=40, fstop=5.6, focus=(0, 0, 0.012))
        return 0.0
    screen, colour, to, big, small = ('14_home_volume', K.YELLOW, 112, '42', 'VOLUME') if SHOT == 'day' else ('16_controls_heating', K.TERRACOTTA, 45, '21.5', '°C')
    K.puck((0, 0, 0), screen, glow_by=2.4)
    R, tube, y = 0.09, 0.0032, 0.115
    c = (0, y, R + tube)
    K.arc(R, 225, -45, tube * 0.8, c, track, rot=(90, 0, 0), name='BigTrack')
    K.arc(R, 225, to, tube, c, K.glow('BigRing', colour, 16.0), rot=(90, 0, 0), name='BigRing')
    K.text(big, 0.068 if SHOT == 'day' else 0.05, (0, y, R + tube - 0.02), K.glow('Number', K.WHITE, 3.0), depth=0.004, weight=900)
    K.text(small, 0.011, (0, y, R + tube - 0.046), K.glow('Word', (0.6, 0.6, 0.6), 1.6), depth=0.001, weight=700, spacing=1.25)
    K.camera((0, 0.05, 0.09), 0.47, -10, 28, lens=35, fstop=8.0, focus=(0, 0.03, 0.03))
    return 0.0


# ------------------------------------------------------------------ ideas 1 and 2 together, three ways

def zoomin():
    """A. House, then into it. The film opens on the card house on the desk; a room lights; the camera
    goes in through the open front of the card kitchen, and the card kitchen becomes the real one."""
    if SHOT == 'night':                                         # frame 3: we are in the real kitchen
        return bench('day')
    desk()
    room = card_house(music=True, tiny=((0, 0, K.YELLOW),))['room']
    kx, kz = room(0, 0)
    if SHOT == 'wide':                                          # frame 1: the whole house, the kitchen answering
        K.puck((kx + 0.03, -0.075, 0), '13_home_playing', glow_by=3.2)
        K.daylight(az=-58, el=27, at=(0, 0, 0.05), w=0.9, h=0.5, oy=0.06, bars=((-0.2, None), (0.12, None), (None, 0.05)), fill=0.45, energy=4.6)
        K.prop('potted_plant_04', None, (0.42, 0.34, 0), rot_z=0.7)
        K.prop('book_encyclopedia_set_01', None, (-0.47, 0.3, 0), rot_z=0.35)
        K.camera((0.0, 0.0, 0.075), 0.74, -16, 15, lens=40, fstop=5.6, focus=(0, 0, 0.07))
        return 0.1
    K.daylight(az=-30, el=30, at=(kx, 0.03, 0.03), w=0.7, h=0.4, oy=0.05, bars=((-0.12, None),), energy=3.6, fill=0.5)      # frame 2: going in
    K.camera((kx - 0.002, 0.04, kz + 0.024), 0.155, -13, 10, lens=32, fstop=4.0, focus=(kx - 0.012, 0.03, kz + 0.018))
    return 0.0


def zoomout():
    """B. Bench, then out of it. The film lives on the real bench all day; at the end the camera pulls
    back and the kitchen turns out to be one room of a card house, every room answering in light."""
    if SHOT == 'wide':                                          # frame 1: the real kitchen, breakfast
        return bench('wide')
    desk()
    if SHOT == 'day':                                           # frame 2: pulling back, the kitchen is card
        room = card_house(music=True, tiny=((0, 0, K.YELLOW),))['room']
        kx, kz = room(0, 0)
        K.daylight(az=48, el=22, at=(kx, 0, 0.04), w=0.7, h=0.4, oy=0.05, bars=((0.1, None), (None, 0.04)), energy=4.2, color=(1.0, 0.76, 0.52), fill=0.36)
        K.camera((kx + 0.03, 0.02, kz + 0.04), 0.33, 8, 13, lens=40, fstop=5.6, focus=(kx, 0.03, kz + 0.02))
        return 0.0
    card_house(heating=True, lamp=True, tiny=((0, 0, K.YELLOW), (0, 1, K.TERRACOTTA), (2, 1, K.TERRACOTTA)))      # frame 3: the whole house, a puck a room
    K.moonlight(energy=16, fill=0.03)
    K.camera((0.0, 0.0, 0.075), 0.62, 12, 14, lens=45, fstop=4.5, focus=(0, 0, 0.06))
    return 0.3


def together():
    """C. Both at once, no cut. The card house stands on the real bench among the real things, the real
    puck in front of it. You talk to the puck in the real kitchen and watch the house answer."""
    K.table(K.surface('marble_01', size=1.4, turn=3, rough_scale=0.7))
    hx, hy, turn = 0.04, 0.2, -7
    moved((hx, hy, 0), turn, card_house, music=SHOT == 'day', heating=SHOT == 'night', lamp=SHOT == 'night')
    K.prop('pot_enamel_01', None, (-0.34, 0.3, 0), rot_z=2.6)
    K.prop('wooden_spoon', None, (-0.3, 0.08, 0), rot_z=-0.5)
    K.prop('tea_set_01', {'tea_set_01_saucer_circular_04'}, (0.26, 0.0, 0), rot_z=0.4)
    K.prop('tea_set_01', {'tea_set_01_cup_small_01'}, (0.26, 0.0, 0.006), rot_z=2.2)
    K.prop('potted_plant_04', None, (0.4, 0.42, 0), rot_z=0.7)
    px, py = -0.04, 0.085                                       # the puck, in front of the kitchen
    if SHOT == 'wide':
        K.puck((px, py, 0), '06_assistant_listening', glow_by=3.4)
        K.daylight(az=150, el=17, at=(0, 0.15, 0), energy=5.0, color=(1.0, 0.9, 0.76), fill=0.65, tint=(0.92, 0.96, 1.0), w=1.2, h=0.7, ox=-0.2, oy=0.08, bar=0.03, bars=((-0.2, None), (0.18, None), (None, 0.0)))
        K.camera((0.0, 0.16, 0.07), 0.86, -12, 15, lens=40, fstop=5.6, focus=(0, 0.15, 0.06))
        return 0.45
    if SHOT == 'day':
        K.puck((px, py, 0), '13_home_playing', glow_by=3.2)
        K.daylight(az=-46, el=30, at=(0, 0.15, 0.04), w=0.8, h=0.45, oy=0.05, bars=((-0.14, None), (None, 0.04)), energy=4.2, fill=0.4)
        K.camera((-0.02, 0.16, 0.06), 0.6, -13, 19, lens=45, fstop=6.3, focus=(px, py + 0.03, 0.02))
        return 0.0
    K.puck((px, py, 0), '16_controls_heating', glow_by=1.6)
    K.moonlight(energy=16, fill=0.03)
    K.camera((0.02, 0.17, 0.07), 0.7, 10, 15, lens=45, fstop=4.5, focus=(0, 0.2, 0.06))
    return 0.3


if __name__ == '__main__':
    exposure = {'house': house, 'bench': bench, 'remotes': remotes, 'apart': apart, 'rings': rings, 'zoomin': zoomin, 'zoomout': zoomout, 'together': together}[IDEA]()
    K.render(OUT, exposure)
