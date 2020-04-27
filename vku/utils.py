import bpy
import re
import os
from importlib import import_module
from itertools import chain

def get_default_prefix():
  return re.sub(r'\.blend$', '', bpy.path.basename(bpy.data.filepath))

# (Pattern, Prefix, Fade, Outline, DoubleSided, Fade)
def gen_mat_pattern(pattern, fade=False, outline=False, doubleSided=False, prefix=None):
  return (re.compile(pattern), prefix, fade, outline, doubleSided)

def get_mat_name(pattern):
  _, prefix, fade, outline, doubleSided = pattern
  return '_'.join((
    prefix if prefix else get_default_prefix(),
    'Fade' if fade else 'Cutout',
    'Outline' if outline else 'NoOutline',
    'DoubleSided' if doubleSided else 'SingleSided',
  ))

mat_patterns = [
  gen_mat_pattern(r'_EyeExtra_', fade=True, prefix='Face'),
  gen_mat_pattern(r'_FACE$|_EYE$', prefix='Face'),
  gen_mat_pattern(r'_SKIN$', outline=True, prefix='Skin'),
  gen_mat_pattern(r'_Body_[0-9]+$', outline=True, doubleSided=True, prefix='Body'),
  gen_mat_pattern(r'_HAIR_0[34]$', outline=True, doubleSided=True, prefix='Hair'),
  gen_mat_pattern(r'_HAIR_[0-9]+$|_HairBack_[0-9]+_HAIR$', outline=True, prefix='Hair'),
  gen_mat_pattern(r'_CLOTH$', outline=True, doubleSided=True),
]

def get_mesh_objects(context = bpy.context):
  return [o for o in context.scene.objects if o.type == 'MESH']

def get_materials(context = bpy.context):
  material_slots = list(chain.from_iterable([o.material_slots for o in get_mesh_objects(context)]))
  return [slot.material for slot in material_slots]

def combine_materials():
  smc = import_module('material-combiner-addon-master')
  combiner = smc.operators.combiner
  cats = True
  scn = bpy.context.scene
  bpy.ops.smc.refresh_ob_data()
  if cats:
      scn.smc_size = 'PO2'
      scn.smc_gaps = 16.0
  combiner.set_ob_mode(bpy.context.view_layer if combiner.globs.version > 0 else scn)
  data = combiner.get_data(scn.smc_ob_data)
  mats_uv = combiner.get_mats_uv(data)
  combiner.clear_empty_mats(data, mats_uv)
  #combiner.get_duplicates(mats_uv)
  structure = combiner.get_structure(data, mats_uv)
  if combiner.globs.version == 0:
      bpy.context.space_data.viewport_shade = 'MATERIAL'
  if (len(structure) == 1) and next(iter(structure.values()))['dup']:
      combiner.clear_duplicates(structure)
      bpy.ops.smc.refresh_ob_data()
      print('FINISHED')
  elif not structure or (len(structure) == 1):
      bpy.ops.smc.refresh_ob_data()
      print('ERROR: No unique materials selected')
      print('FINISHED')

  directory = os.getcwd()
  scn = bpy.context.scene
  scn.smc_save_path = directory
  structure = combiner.BinPacker(combiner.get_size(scn, structure)).fit()
  size = (max([i['gfx']['fit']['x'] + i['gfx']['size'][0] for i in structure.values()]),
          max([i['gfx']['fit']['y'] + i['gfx']['size'][1] for i in structure.values()]))
  if any(size) > 20000:
    return print('ERROR: Output image size is too large')
  atlas = combiner.get_atlas(scn, structure, size)
  combiner.get_aligned_uv(scn, structure, atlas.size)
  combiner.assign_comb_mats(scn, data, mats_uv, atlas)
  combiner.clear_mats(mats_uv)
  bpy.ops.smc.refresh_ob_data()
  return print('FINISHED')

def rename_hierarcy(target, name, n = 1):
  target.name = f'{name}_{n}'
  if len(target.children) >= 1:
    rename_hierarcy(target.children[0], name, n + 1)

def set_active_object(target):
  bpy.ops.object.mode_set(mode='OBJECT')
  bpy.ops.object.select_all(action='DESELECT')
  bpy.context.view_layer.objects.active = target
  target.select_set(True)

def select_vertices(obj, pred):
  bpy.ops.object.mode_set(mode='EDIT')
  bpy.ops.mesh.select_all(action='DESELECT')
  bpy.ops.object.mode_set(mode='OBJECT')
  for v in obj.data.vertices:
    v.select = pred(v)
  bpy.ops.object.mode_set(mode='EDIT')
