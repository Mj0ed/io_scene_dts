import os
import bpy
from colorsys import hsv_to_rgb
from itertools import count
from fractions import Fraction

texture_extensions = ("png", "jpg")

default_materials_src = {
    "black": (0, 0, 0),
    "black25": (191, 191, 191),
    "black50": (128, 128, 128),
    "black75": (64, 64, 64),
    "blank": (255, 255, 255),
    "blue": (0, 0, 255),
    "darkRed": (128, 0, 0),
    "gray25": (64, 64, 64),
    "gray50": (128, 128, 128),
    "gray75": (191, 191, 191),
    "green": (26, 128, 64),
    "lightBlue": (10, 186, 245),
    "lightYellow": (249, 249, 99),
    "palegreen": (125, 136, 104),
    "red": (213, 0, 0),
    "white": (255, 255, 255),
    "yellow": (255, 255, 0)
}

default_materials = {}

for name, color in default_materials_src.items():
    default_materials[name.lower()] = (color[0] / 255, color[1] / 255, color[2] / 255, 1.0)

def resolve_texture(filepath, name):
    dirname = os.path.dirname(filepath)

    while True:
        texbase = os.path.join(dirname, name)

        for extension in texture_extensions:
            texname = texbase + "." + extension

            if os.path.isfile(texname):
                return texname

        if os.path.ismount(dirname):
            break

        prevdir, dirname = dirname, os.path.dirname(dirname)

        if prevdir == dirname:
            break

def fractions():
    yield 0

    for k in count():
        i = 2 ** k

        for j in range(1, i, 2):
            yield j / i

def get_hsv_colors():
    for h in fractions():
        yield (h, 0.75, 0.75)

def get_rgb_colors():
    return map(lambda hsv: hsv_to_rgb(*hsv), get_hsv_colors())

def action_get_or_new(ob):
  if not ob.animation_data:
    ob.animation_data_create()

  if ob.animation_data.action:
    return ob.animation_data.action

  action = bpy.data.actions.new(ob.name + "Action")
  ob.animation_data.action = action

  return action

# Blender 4.4 reworked Actions into "slotted actions": Action.fcurves was
# removed and F-Curves now live in a channelbag bound to a slot. These helpers
# return the relevant FCurve collection while staying compatible with the
# legacy (Blender < 4.4) Action.fcurves API.
def action_fcurves_ensure(ob, action):
  if hasattr(action, "fcurves"):
    return action.fcurves

  anim_data = ob.animation_data
  slot = anim_data.action_slot
  if slot is None:
    slot = action.slots.new(id_type='OBJECT', name=ob.name)
    anim_data.action_slot = slot

  layer = action.layers[0] if action.layers else action.layers.new("Layer")
  strip = layer.strips[0] if layer.strips else layer.strips.new(type='KEYFRAME')
  return strip.channelbag(slot, ensure=True).fcurves

def action_fcurves_read(anim_data):
  action = anim_data.action
  if action is None:
    return []
  if hasattr(action, "fcurves"):
    return action.fcurves

  slot = anim_data.action_slot
  if slot is None:
    return []
  for layer in action.layers:
    for strip in layer.strips:
      channelbag = strip.channelbag(slot)
      if channelbag is not None:
        return channelbag.fcurves
  return []

def ob_curves_array(ob, data_path, array_count):
  action = action_get_or_new(ob)
  fcurves = action_fcurves_ensure(ob, action)
  curves = [None] * array_count

  for curve in fcurves:
    if curve.data_path != data_path or curve.array_index < 0 or curve.array_index >= array_count:
      continue

    if curves[curve.array_index]:
      pass # TODO: warn if more than one curve for an array slot

    curves[curve.array_index] = curve

  for index, curve in enumerate(curves):
    if curve is None:
      curves[index] = fcurves.new(data_path, index=index)

  return curves

def insert_keyframes(curves, frames, values):
  """Batch-insert LINEAR keyframes into each f-curve.

  frames: sequence of frame numbers.
  values: sequence aligned with frames; each item must be indexable by a
          curve's array_index.

  Adding all of a sequence's keyframe points in one ``add(n)`` call avoids the
  O(n^2) reallocation that one-keyframe-at-a-time insertion causes on curves
  that accumulate keyframes across many sequences. Frames are appended in
  increasing order, so the curve stays sorted; with LINEAR interpolation the
  handles are ignored, so no per-curve update()/recalculation is required.
  """
  for curve in curves:
    points = curve.keyframe_points
    base = len(points)
    points.add(len(frames))
    array_index = curve.array_index

    for offset, frame in enumerate(frames):
      point = points[base + offset]
      point.interpolation = "LINEAR"
      point.co = (frame, values[offset][array_index])

def ob_location_curves(ob):
  return ob_curves_array(ob, "location", 3)

def ob_scale_curves(ob):
  return ob_curves_array(ob, "scale", 3)

def fcurves_path_from_rotation(ob):
    if ob.rotation_mode == 'QUATERNION':
        return ('rotation_quaternion', 4)
    elif ob.rotation_mode == 'AXIS_ANGLE':
        return ('rotation_axis_angle', 4)
    else:
        return ('rotation_euler', 3)

def ob_rotation_data(ob):
    if ob.rotation_mode == 'QUATERNION':
        return ob.rotation_quaternion
    elif ob.rotation_mode == 'AXIS_ANGLE':
        return ob.rotation_axis_angle
    else:
        return ob.rotation_euler

def ob_rotation_curves(ob):
    data_path, array_count = fcurves_path_from_rotation(ob)
    return ob.rotation_mode, ob_curves_array(ob, data_path, array_count)

def evaluate_all(curves, frame):
    return tuple(map(lambda c: c.evaluate(frame), curves))

def array_from_fcurves(curves, data_path, array_size):
    found = False
    array = [None] * array_size

    for curve in curves:
        if curve.data_path == data_path and curve.array_index != -1:
            array[curve.array_index] = curve
            found = True

    if found:
        return tuple(array)

def array_from_fcurves_rotation(curves, ob):
    data_path, array_count = fcurves_path_from_rotation(ob)
    return array_from_fcurves(curves, data_path, array_count)

def fcurves_keyframe_in_range(curves, start, end):
    for curve in curves:
        for keyframe in curve.keyframe_points:
            frame = keyframe.co[0]
            if frame >= start and frame <= end:
                return True

    return False

def find_reference(scene):
    reference_marker = scene.timeline_markers.get("reference")
    if reference_marker is not None:
        return reference_marker.frame

def fail(operator, message):
    print("Error:", message)
    operator.report({"ERROR"}, message)
    return {"FINISHED"}
