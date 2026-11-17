"""Shared tools for the Pucksley film's Blender sets: the puck itself, materials, lights, camera and render.

Everything is in metres at true size (the puck is 49 mm across), the camera sits low, each shot has one
motivated light, and the picture is finished afterwards by finish.py. The recipe is the one the Dimpkin
Kickstarter film used (D:/git/www.dimpkin.com/design/kickstarter-film-drafts/blender), which follows
"The Fable of Clawd".

The puck's screen is never drawn by hand: it is one of the simulator's own pictures of the real faces
(film/screens/NN_name.png, drawn by the simulator in NimbleHive/Pucksley, firmware/tools/sim), shown as light on the glass.

Importing this module empties the Blender scene. Options every script that uses it understands:
  --scale 50      percent of 1920x1080
  --samples 64
  --device gpu    render on the graphics card (the default is the processor, so a film render that is
                  already using the card is left alone)
"""
import ctypes
import math
import os
import random
import sys

import bpy
import bmesh
from mathutils import Matrix, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
PH = os.path.join(HERE, 'cache', 'polyhaven')
CUT = os.path.join(HERE, 'cache', 'cut')
SCREENS = os.path.join(HERE, '..', 'screens')
FONTS = os.path.join(HERE, '..', 'fonts')

argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []


def arg(name, default):
    return argv[argv.index('--' + name) + 1] if '--' + name in argv else default


bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
random.seed(7)

# the colours of the puck's own faces (firmware/main/ui)
YELLOW = (1.0, 0.70, 0.0)
TERRACOTTA = (0.72, 0.19, 0.08)
GREEN = (0.05, 0.75, 0.13)
WHITE = (1.0, 1.0, 1.0)


# ------------------------------------------------------------------ materials

def image(path, noncolor=False):
    im = bpy.data.images.load(path, check_existing=True)
    if noncolor:
        im.colorspace_settings.name = 'Non-Color'
    return im


def new_mat(name):
    m = bpy.data.materials.new(name)
    if not m.node_tree:
        m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new('ShaderNodeOutputMaterial')
    bsdf = nt.nodes.new('ShaderNodeBsdfPrincipled')
    nt.links.new(bsdf.outputs['BSDF'], out.inputs['Surface'])
    return m, nt, bsdf, out


_solids = {}


def solid(name, color, rough=0.5, metal=0.0, emit=0.0, emit_color=None, coat=0.0, sheen=0.0):
    """A plain material. Asking for the same name twice gives the same one."""
    if name in _solids:
        return _solids[name]
    m, nt, bsdf, _ = new_mat(name)
    bsdf.inputs['Base Color'].default_value = (*color, 1)
    bsdf.inputs['Roughness'].default_value = rough
    bsdf.inputs['Metallic'].default_value = metal
    bsdf.inputs['Coat Weight'].default_value = coat
    bsdf.inputs['Sheen Weight'].default_value = sheen
    if emit:
        bsdf.inputs['Emission Color'].default_value = (*(emit_color or color), 1)
        bsdf.inputs['Emission Strength'].default_value = emit
    _solids[name] = m
    return m


def glow(name, color, strength):
    """Something that is only light: a neon tube, a lit floor."""
    return solid(name, (0, 0, 0), rough=0.4, emit=strength, emit_color=color)


def card(name='Card', color=(0.86, 0.85, 0.82)):
    """White model-making card: matt, with a fine tooth."""
    if name in _solids:
        return _solids[name]
    m, nt, bsdf, _ = new_mat(name)
    bsdf.inputs['Base Color'].default_value = (*color, 1)
    bsdf.inputs['Roughness'].default_value = 0.7
    bsdf.inputs['Specular IOR Level'].default_value = 0.3
    noise = nt.nodes.new('ShaderNodeTexNoise')
    noise.inputs['Scale'].default_value = 1800
    noise.inputs['Detail'].default_value = 3
    bump = nt.nodes.new('ShaderNodeBump')
    bump.inputs['Strength'].default_value = 0.06
    bump.inputs['Distance'].default_value = 0.0002
    nt.links.new(noise.outputs['Fac'], bump.inputs['Height'])
    nt.links.new(bump.outputs['Normal'], bsdf.inputs['Normal'])
    _solids[name] = m
    return m


def surface(asset, size=0.9, turn=8.0, name=None, tint=None, rough_scale=1.0):
    """A scanned Poly Haven surface, tiled every `size` metres so the grain holds up close."""
    m, nt, bsdf, _ = new_mat(name or asset)
    co = nt.nodes.new('ShaderNodeTexCoord')
    mp = nt.nodes.new('ShaderNodeMapping')
    mp.inputs['Scale'].default_value = (1 / size, 1 / size, 1)
    mp.inputs['Rotation'].default_value = (0, 0, math.radians(turn))
    nt.links.new(co.outputs['Object'], mp.inputs['Vector'])

    def tex(file, noncolor):
        t = nt.nodes.new('ShaderNodeTexImage')
        t.image = image(os.path.join(PH, asset, file), noncolor)
        nt.links.new(mp.outputs['Vector'], t.inputs['Vector'])
        return t
    col = tex('Diffuse.jpg', False).outputs['Color']
    if tint:
        mul = nt.nodes.new('ShaderNodeMixRGB')
        mul.blend_type = 'MULTIPLY'
        mul.inputs['Fac'].default_value = 1
        mul.inputs['Color2'].default_value = (*tint, 1)
        nt.links.new(col, mul.inputs['Color1'])
        col = mul.outputs['Color']
    nt.links.new(col, bsdf.inputs['Base Color'])
    rough = tex('Rough.jpg', True).outputs['Color']
    if rough_scale != 1.0:
        mul = nt.nodes.new('ShaderNodeMath')
        mul.operation = 'MULTIPLY'
        mul.inputs[1].default_value = rough_scale
        nt.links.new(rough, mul.inputs[0])
        rough = mul.outputs[0]
    nt.links.new(rough, bsdf.inputs['Roughness'])
    nm = nt.nodes.new('ShaderNodeNormalMap')
    nt.links.new(tex('nor_gl.jpg', True).outputs['Color'], nm.inputs['Color'])
    nt.links.new(nm.outputs['Normal'], bsdf.inputs['Normal'])
    return m


def print_mat(name, path, rough=0.6, emit=0.0, coat=0.0):
    """A printed picture on card or plastic. emit: how much it shines by itself (a screen, a lit sign)."""
    m, nt, bsdf, _ = new_mat(name)
    t = nt.nodes.new('ShaderNodeTexImage')
    t.image = image(path)
    t.extension = 'EXTEND'
    nt.links.new(t.outputs['Color'], bsdf.inputs['Base Color'])
    bsdf.inputs['Roughness'].default_value = rough
    bsdf.inputs['Coat Weight'].default_value = coat
    if emit:
        nt.links.new(t.outputs['Color'], bsdf.inputs['Emission Color'])
        bsdf.inputs['Emission Strength'].default_value = emit
    return m


# ------------------------------------------------------------------ shapes

def link(ob):
    scene.collection.objects.link(ob)
    return ob


def place(ob, loc=(0, 0, 0), rot=(0, 0, 0)):
    """rot in degrees, about X then Y then Z."""
    ob.location = loc
    ob.rotation_euler = tuple(math.radians(a) for a in rot)
    return ob


def box(size, loc, mat, rot=(0, 0, 0), bevel=0.0, name='Box'):
    """A box of size (x, y, z) centred on loc, its edges rounded by bevel."""
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=Vector(size), verts=bm.verts)
    if bevel:
        bmesh.ops.bevel(bm, geom=list(bm.edges), offset=bevel, segments=3, profile=0.5, affect='EDGES')
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    if bevel:
        for p in me.polygons:
            p.use_smooth = True
    me.materials.append(mat)
    return place(link(bpy.data.objects.new(name, me)), loc, rot)


def lathe(segments, mat, n=128, name='Lathe', uv_radius=None):
    """A turned shape, about Z. segments: lists of (radius, height) points; each list is smooth along its
    length and there is a hard edge between one list and the next. uv_radius: lay a picture over it as
    seen from above, its edges at that radius (for the screen)."""
    verts, faces = [], []
    for seg in segments:
        rings = []
        for r, z in seg:
            if r < 1e-9:
                rings.append([len(verts)])
                verts.append((0, 0, z))
            else:
                rings.append(list(range(len(verts), len(verts) + n)))
                verts.extend((r * math.cos(2 * math.pi * k / n), r * math.sin(2 * math.pi * k / n), z) for k in range(n))
        for a, b in zip(rings, rings[1:]):
            for k in range(n):
                k2 = (k + 1) % n
                if len(a) == 1 and len(b) == 1:
                    continue
                if len(a) == 1:
                    faces.append((a[0], b[k], b[k2]))
                elif len(b) == 1:
                    faces.append((a[k], b[0], a[k2]))
                else:
                    faces.append((a[k], b[k], b[k2], a[k2]))
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], faces)
    bm = bmesh.new()
    bm.from_mesh(me)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(me)
    bm.free()
    for p in me.polygons:
        p.use_smooth = True
    if uv_radius:
        uv = me.uv_layers.new(name='UVMap')
        for p in me.polygons:
            for li in p.loop_indices:
                x, y, _ = me.vertices[me.loops[li].vertex_index].co
                uv.data[li].uv = (0.5 + 0.5 * x / uv_radius, 0.5 + 0.5 * y / uv_radius)
    me.materials.append(mat)
    return link(bpy.data.objects.new(name, me))


def corner(cr, cz, r, a0, a1, n=6):
    """Points round a fillet: centre (cr, cz), from angle a0 to a1 in degrees."""
    return [(cr + r * math.cos(math.radians(a0 + (a1 - a0) * i / n)), cz + r * math.sin(math.radians(a0 + (a1 - a0) * i / n))) for i in range(n + 1)]


def disc(r, h, loc, mat, bevel=0.0, n=96, rot=(0, 0, 0), name='Disc'):
    """A cylinder standing on loc (loc is the centre of its foot)."""
    b = min(bevel, r / 2, h / 2)
    seg = [(0, 0)] + (corner(r - b, b, b, -90, 0) + corner(r - b, h - b, b, 0, 90) if b else [(r, 0), (r, h)]) + [(0, h)]
    segs = [seg] if b else [[(0, 0), (r, 0)], [(r, 0), (r, h)], [(r, h), (0, h)]]
    return place(lathe(segs, mat, n=n, name=name), loc, rot)


def sheet(width, depth, loc, mat, turn=0.0, back=None, thick=0.0004, name='Sheet'):
    """A printed sheet lying flat, its picture facing up, centred on loc. turn: degrees about Z."""
    me = bpy.data.meshes.new(name)
    w, d = width / 2, depth / 2
    me.from_pydata([(-w, -d, 0), (w, -d, 0), (w, d, 0), (-w, d, 0)], [], [(0, 1, 2, 3)])
    uv = me.uv_layers.new(name='UVMap')
    for li, c in zip(me.polygons[0].loop_indices, ((0, 0), (1, 0), (1, 1), (0, 1))):
        uv.data[li].uv = c
    me.materials.append(mat)
    me.materials.append(back or mat)
    ob = link(bpy.data.objects.new(name, me))
    so = ob.modifiers.new('Thickness', 'SOLIDIFY')
    so.thickness, so.offset, so.material_offset, so.material_offset_rim = thick, -1, 1, 1
    return place(ob, (loc[0], loc[1], loc[2] + thick), (0, 0, turn))


def stand(width, height, loc, mat, turn=0.0, lean=0.0, back=None, thick=0.0008, name='Stand'):
    """A printed card standing on its bottom edge at loc, facing -Y (the camera) when turn is 0.
    lean: degrees it tips back from upright."""
    me = bpy.data.meshes.new(name)
    w = width / 2
    me.from_pydata([(-w, 0, 0), (w, 0, 0), (w, 0, height), (-w, 0, height)], [], [(0, 1, 2, 3)])
    uv = me.uv_layers.new(name='UVMap')
    for li, c in zip(me.polygons[0].loop_indices, ((0, 0), (1, 0), (1, 1), (0, 1))):
        uv.data[li].uv = c
    me.materials.append(mat)
    me.materials.append(back or card())
    ob = link(bpy.data.objects.new(name, me))
    so = ob.modifiers.new('Thickness', 'SOLIDIFY')
    so.thickness, so.offset, so.material_offset, so.material_offset_rim = thick, -1, 1, 1
    return place(ob, loc, (-lean, 0, turn))


def rod(p0, p1, r, mat, sides=12, name='Rod'):
    p0, p1 = Vector(p0), Vector(p1)
    d = p1 - p0
    bpy.ops.mesh.primitive_cylinder_add(vertices=sides, radius=r, depth=d.length, location=(p0 + p1) / 2)
    o = bpy.context.object
    o.name = name
    o.rotation_euler = d.to_track_quat('Z', 'Y').to_euler()
    o.data.materials.append(mat)
    for p in o.data.polygons:
        p.use_smooth = True
    return o


def arc(radius, a0, a1, tube, loc, mat, rot=(0, 0, 0), n=160, sides=16, name='Arc'):
    """Part of a ring: a tube bent round a circle of the given radius, from angle a0 to a1 (degrees,
    anticlockwise from +X, in the ring's own XY plane), with rounded ends."""
    verts, faces = [], []
    steps = max(2, int(n * abs(a1 - a0) / 360))
    for i in range(steps + 1):
        a = math.radians(a0 + (a1 - a0) * i / steps)
        c = Vector((math.cos(a), math.sin(a), 0))
        for k in range(sides):
            b = 2 * math.pi * k / sides
            verts.append(tuple(c * (radius + tube * math.cos(b)) + Vector((0, 0, tube * math.sin(b)))))
    for i in range(steps):
        for k in range(sides):
            k2 = (k + 1) % sides
            faces.append((i * sides + k, (i + 1) * sides + k, (i + 1) * sides + k2, i * sides + k2))
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], faces)
    for p in me.polygons:
        p.use_smooth = True
    me.materials.append(mat)
    ob = place(link(bpy.data.objects.new(name, me)), loc, rot)
    for a in (a0, a1):                                                   # a ball closes each end
        bpy.ops.mesh.primitive_uv_sphere_add(segments=sides, ring_count=8, radius=tube)
        s = bpy.context.object
        s.data.materials.append(mat)
        for p in s.data.polygons:
            p.use_smooth = True
        s.parent = ob
        s.location = (radius * math.cos(math.radians(a)), radius * math.sin(math.radians(a)), 0)
    return ob


def text(body, size, loc, mat, rot=(90, 0, 0), depth=0.0, weight=800, align='CENTER', spacing=1.0, name='Text'):
    """Letters in the puck's own typeface (Nunito). With rot (90, 0, 0) they stand facing the camera;
    with (0, 0, 0) they lie on the table. depth: how thick they are cut."""
    cu = bpy.data.curves.new(name, 'FONT')
    cu.body = body
    cu.font = bpy.data.fonts.load(os.path.join(FONTS, f'Nunito-w{weight}.ttf'), check_existing=True)
    cu.size = size
    cu.align_x = align
    cu.space_character = spacing
    cu.extrude = depth / 2
    cu.bevel_depth = min(depth / 6, size * 0.01) if depth else 0
    cu.materials.append(mat)
    return place(link(bpy.data.objects.new(name, cu)), loc, rot)


def prop(asset, names, loc, rot_z=0.0, height=None, tilt=0.0):
    """Bring in a Poly Haven model and stand it on the table at loc. names: which of its objects to keep
    (None for all). tilt turns it about X first, to lay down something the model has standing up."""
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=os.path.join(PH, asset, asset + '.gltf'))
    new = [o for o in bpy.data.objects if o not in before]
    keep = [o for o in new if o.type == 'MESH' and (names is None or o.name in names)]
    for o in new:
        if o not in keep:
            bpy.data.objects.remove(o, do_unlink=True)
    bpy.context.view_layer.update()
    for o in keep:                                   # free them from whatever they were parented to
        mw = o.matrix_world.copy()
        o.parent = None
        o.matrix_world = mw
    turn = Matrix.Rotation(rot_z, 4, 'Z') @ Matrix.Rotation(tilt, 4, 'X')
    pts = [turn @ (o.matrix_world @ Vector(c)) for o in keep for c in o.bound_box]
    lo = Vector([min(p[i] for p in pts) for i in range(3)])
    hi = Vector([max(p[i] for p in pts) for i in range(3)])
    s = (height / (hi.z - lo.z)) if height else 1.0
    base = Vector(((lo.x + hi.x) / 2, (lo.y + hi.y) / 2, lo.z))
    m = Matrix.Translation(Vector(loc)) @ Matrix.Scale(s, 4) @ Matrix.Translation(-base) @ turn
    for o in keep:
        o.matrix_world = m @ o.matrix_world
    return keep


def table(mat, size=(3.2, 2.2), at=(0, 0.35, 0)):
    bpy.ops.mesh.primitive_plane_add(size=1, location=at)
    t = bpy.context.object
    t.name = 'Table'
    t.scale = (size[0], size[1], 1)
    t.data.materials.append(mat)
    return t


# ------------------------------------------------------------------ the puck

R_CASE, H_CASE, R_GLASS, R_SCREEN = 0.02448, 0.0118, 0.0226, 0.0222      # 48.96 mm across; a 1.75 inch screen


def aluminium():
    return solid('Anodised', (0.045, 0.047, 0.052), rough=0.34, metal=1.0)


def screen_mat(screen, glow_by=2.2):
    """The glass with one of the simulator's pictures alight on it."""
    m, nt, bsdf, _ = new_mat('Screen-' + screen)
    t = nt.nodes.new('ShaderNodeTexImage')
    t.image = image(os.path.join(SCREENS, screen + '.png'))
    t.extension = 'CLIP'
    bsdf.inputs['Base Color'].default_value = (0.004, 0.004, 0.005, 1)
    bsdf.inputs['Roughness'].default_value = 0.06
    bsdf.inputs['Coat Weight'].default_value = 0.6
    bsdf.inputs['Coat Roughness'].default_value = 0.03
    nt.links.new(t.outputs['Color'], bsdf.inputs['Emission Color'])
    bsdf.inputs['Emission Strength'].default_value = glow_by
    return m


def puck_glass(screen, glow_by=2.2, name='Glass'):
    """The puck's glass with a screen alight on it, in the puck's own coordinates. A film gives one puck
    several, parented to it, and keeps all but the one showing out of sight."""
    k = 0.001
    return lathe([[(0, H_CASE + 0.25 * k), (R_GLASS - 0.35 * k, H_CASE + 0.25 * k)] + corner(R_GLASS - 0.35 * k, H_CASE - 0.1 * k, 0.35 * k, 90, 0, 4)],
                 screen_mat(screen, glow_by), name=name, uv_radius=R_SCREEN)


def puck(loc=(0, 0, 0), screen='05_assistant_idle', turn=0.0, tilt=(0.0, 0.0), glow_by=2.2, name='Puck'):
    """The puck, lying on loc with its screen up. The screen's top is away from the camera (+Y) when turn
    is 0; turn is degrees about Z. tilt: degrees about X and Y, for a puck that is being lifted."""
    root = link(bpy.data.objects.new(name, None))
    k = 0.001
    case = lathe([[(0, 0)] + corner(R_CASE - 1.6 * k, 1.6 * k, 1.6 * k, -90, 0) + corner(R_CASE - 1.2 * k, H_CASE - 1.2 * k, 1.2 * k, 0, 90) + [(R_GLASS + 0.15 * k, H_CASE)],
                  [(R_GLASS + 0.15 * k, H_CASE), (R_GLASS + 0.15 * k, H_CASE - 0.6 * k)]], aluminium(), name=name + 'Case')
    glass = puck_glass(screen, glow_by, name + 'Glass')
    button = box((0.0016, 0.0075, 0.0028), (R_CASE + 0.0002, 0, H_CASE * 0.52), aluminium(), bevel=0.0005, name=name + 'Button')
    port = box((0.009, 0.001, 0.0032), (0, R_CASE - 0.0003, H_CASE * 0.45), solid('Port', (0.01, 0.01, 0.01), rough=0.5), bevel=0.0004, name=name + 'Port')
    for o in (case, glass, button, port):
        o.parent = root
    root.location = loc
    root.rotation_euler = (math.radians(tilt[0]), math.radians(tilt[1]), math.radians(turn))
    return root


# ------------------------------------------------------------------ light

def aim(ob, to):
    ob.rotation_euler = (Vector(to) - ob.location).to_track_quat('-Z', 'Y').to_euler()


def world(strength, tint=(1, 1, 1), rot_z=200):
    """The room around the set: a Poly Haven interior, for the fill light and what the glass reflects."""
    w = bpy.data.worlds.new('Room')
    if not w.node_tree:
        w.use_nodes = True
    scene.world = w
    nt = w.node_tree
    nt.nodes.clear()
    out = nt.nodes.new('ShaderNodeOutputWorld')
    bg = nt.nodes.new('ShaderNodeBackground')
    env = nt.nodes.new('ShaderNodeTexEnvironment')
    env.image = image(os.path.join(PH, 'lebombo', 'lebombo.hdr'))
    mp = nt.nodes.new('ShaderNodeMapping')
    mp.inputs['Rotation'].default_value = (0, 0, math.radians(rot_z))
    co = nt.nodes.new('ShaderNodeTexCoord')
    mul = nt.nodes.new('ShaderNodeMixRGB')
    mul.blend_type = 'MULTIPLY'
    mul.inputs['Fac'].default_value = 1
    mul.inputs['Color2'].default_value = (*tint, 1)
    nt.links.new(co.outputs['Generated'], mp.inputs['Vector'])
    nt.links.new(mp.outputs['Vector'], env.inputs['Vector'])
    nt.links.new(env.outputs['Color'], mul.inputs['Color1'])
    nt.links.new(mul.outputs['Color'], bg.inputs['Color'])
    bg.inputs['Strength'].default_value = strength
    nt.links.new(bg.outputs['Background'], out.inputs['Surface'])


def black_world(level=0.0):
    w = bpy.data.worlds.new('Void')
    if not w.node_tree:
        w.use_nodes = True
    scene.world = w
    bg = w.node_tree.nodes.get('Background') or w.node_tree.nodes.new('ShaderNodeBackground')
    bg.inputs['Color'].default_value = (level, level, level, 1)
    bg.inputs['Strength'].default_value = 1.0


def sun(az, el, energy=6.0, color=(1.0, 0.86, 0.68), angle=0.8, at=(0, 0, 0)):
    """az: degrees round from straight in front of the set (negative is camera left, 180 is behind it);
    el: above the table. Returns the direction from the set to the sun."""
    a, e = math.radians(az), math.radians(el)
    toward = Vector((math.cos(e) * math.sin(a), -math.cos(e) * math.cos(a), math.sin(e)))
    li = bpy.data.lights.new('Sun', 'SUN')
    li.energy, li.color, li.angle = energy, color, math.radians(angle)
    ob = link(bpy.data.objects.new('Sun', li))
    ob.location = Vector(at) + toward * 3
    aim(ob, at)
    return toward


def window(toward, at=(0, 0, 0.04), dist=1.6, w=0.5, h=0.34, ox=0.0, oy=0.03, bar=0.02, bars=((-0.08, None), (None, 0.02))):
    """A wall with a window in it between the sun and the set, so the light arrives as a window's.
    w, h: the opening; ox, oy: where its centre is, across and up; bars: glazing bars as (across, None)
    for an upright one or (None, up) for a level one."""
    q = (-toward).to_track_quat('-Z', 'Y')
    centre = Vector(at) + toward * dist + q @ Vector((ox, oy, 0))
    m = solid('WindowWall', (0.02, 0.02, 0.02))

    def slab(x, y, sx, sy):
        bpy.ops.mesh.primitive_plane_add(size=1)
        o = bpy.context.object
        o.scale = (sx, sy, 1)
        o.rotation_euler = q.to_euler()
        o.location = centre + q @ Vector((x, y, 0))
        o.data.materials.append(m)
        o.visible_camera = False
        o.visible_glossy = False
    big = 6
    slab(-(w / 2 + big / 2), 0, big, big * 2)
    slab(w / 2 + big / 2, 0, big, big * 2)
    slab(0, h / 2 + big / 2, w, big)
    slab(0, -(h / 2 + big / 2), w, big)
    for bx, by in bars:
        if bx is not None:
            slab(bx, 0, bar, h)
        else:
            slab(0, by, w, bar)


def daylight(az=-50, el=30, at=(0, 0, 0), energy=6.0, fill=0.45, color=(1.0, 0.86, 0.68), tint=(0.9, 0.95, 1.0), **win):
    """The sun through a window, and the room's own light as fill."""
    toward = sun(az, el, energy, color, at=at)
    window(toward, at=(at[0], at[1], at[2] + 0.04), **win)
    world(fill, tint)


def spot(loc, target, watts, color=(1.0, 0.78, 0.55), cone=62, blend=0.9, soft=0.035, name='Key'):
    li = bpy.data.lights.new(name, 'SPOT')
    li.energy, li.color = watts, color
    li.spot_size, li.spot_blend, li.shadow_soft_size = math.radians(cone), blend, soft
    ob = link(bpy.data.objects.new(name, li))
    ob.location = loc
    aim(ob, target)
    return ob


def area(loc, target, watts, size=1.0, color=(1, 1, 1), name='Area'):
    li = bpy.data.lights.new(name, 'AREA')
    li.energy, li.color, li.size = watts, color, size
    ob = link(bpy.data.objects.new(name, li))
    ob.location = loc
    aim(ob, target)
    return ob


def point(loc, watts, color=(1.0, 0.75, 0.5), soft=0.01, name='Point'):
    li = bpy.data.lights.new(name, 'POINT')
    li.energy, li.color, li.shadow_soft_size = watts, color, soft
    ob = link(bpy.data.objects.new(name, li))
    ob.location = loc
    return ob


def moonlight(energy=12, fill=0.03):
    """Night: a little blue from the window, and the room nearly dark."""
    world(fill, (0.38, 0.52, 1.0))
    return area((-1.5, 1.5, 1.2), (0, 0, 0), energy, size=1.2, color=(0.42, 0.58, 1.0), name='Moon')


# ------------------------------------------------------------------ camera and render

def camera(target, dist, az, el, lens=50, fstop=4.0, focus=None, shift_y=0.0):
    """Looking at target from dist metres away; az degrees round from straight in front (negative is to
    the left), el degrees above the table. focus: the point that is sharp (target if not given)."""
    cd = bpy.data.cameras.new('Camera')
    cd.lens, cd.sensor_width = lens, 36
    cd.shift_y = shift_y
    cd.clip_start, cd.clip_end = 0.01, 100
    cd.dof.use_dof = True
    cd.dof.aperture_fstop = fstop
    cd.dof.aperture_blades = 7
    ob = link(bpy.data.objects.new('Camera', cd))
    a, e = math.radians(az), math.radians(el)
    target = Vector(target)
    ob.location = target + Vector((math.cos(e) * math.sin(a), -math.cos(e) * math.cos(a), math.sin(e))) * dist
    aim(ob, target)
    cd.dof.focus_distance = (Vector(focus) - ob.location).length if focus else dist
    scene.camera = ob
    return ob


def setup(exposure=0.0):
    """The render settings every still and every film frame shares."""
    scale, samples = int(arg('scale', 100)), int(arg('samples', 256))
    scene.render.engine = 'CYCLES'
    if arg('device', 'cpu') == 'gpu':
        prefs = bpy.context.preferences.addons['cycles'].preferences
        prefs.compute_device_type = 'OPTIX'
        prefs.get_devices()
        for d in prefs.devices:
            d.use = d.type == 'OPTIX'
        scene.cycles.device = 'GPU'
    else:
        scene.cycles.device = 'CPU'
        scene.render.threads_mode = 'FIXED'
        scene.render.threads = int(arg('threads', 20))
        try:                                         # below normal priority: other renders keep their share
            ctypes.windll.kernel32.SetPriorityClass(ctypes.windll.kernel32.GetCurrentProcess(), 0x00004000)
        except Exception:
            pass
    scene.cycles.samples = samples
    scene.cycles.use_adaptive_sampling = True
    scene.cycles.adaptive_threshold = 0.015
    scene.cycles.use_denoising = True
    scene.cycles.caustics_reflective = False
    scene.cycles.caustics_refractive = False
    scene.render.resolution_x, scene.render.resolution_y = 1920, 1080
    scene.render.resolution_percentage = scale
    scene.view_settings.view_transform = 'AgX'
    scene.view_settings.exposure = float(arg('exposure', exposure))
    for look in ('AgX - Medium High Contrast', 'Medium High Contrast'):
        try:
            scene.view_settings.look = look
            break
        except TypeError:
            pass
    scene.render.image_settings.file_format = 'PNG'
    scene.render.image_settings.color_depth = '16'


def render(out, exposure=0.0):
    setup(exposure)
    scene.render.filepath = os.path.abspath(out)
    bpy.ops.render.render(write_still=True)
    print('WROTE', scene.render.filepath)
