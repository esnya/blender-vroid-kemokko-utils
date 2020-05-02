import bpy
import os
import re
from . import utils
from itertools import chain
from importlib import import_module

# (Pattern, Prefix, Fade, Outline, DoubleSided, Normal)
def gen_mat_pattern(pattern, fade=False, outline=False, doubleSided=False, prefix=None, normal=False):
  return (re.compile(pattern), prefix, fade, outline, doubleSided, normal)

def get_mat_name(pattern):
  _, prefix, _, _, _, _ = pattern
  return prefix
  # _, prefix, fade, outline, doubleSided, normal = pattern
  # return '_'.join((
  #   prefix if prefix else utils.get_default_prefix(),
  #   'Fade' if fade else 'Cutout',
  #   'Outline' if outline else 'NoOutline',
  #   'DoubleSided' if doubleSided else 'SingleSided',
  #   'Nml' if normal else '',
  # ))

mat_patterns = [
  gen_mat_pattern(r'EyeIris|EyeHighlight|EyeShiitake', fade=True, prefix='Eye'),
  gen_mat_pattern(r'_EyeExtra_$|_FACE$|_EYE$', fade=True, prefix='Face'),
  gen_mat_pattern(r'_SKIN$', outline=True, normal=True, prefix='Skin'),
  gen_mat_pattern(r'_HAIR_[0-9]+$|_HairBack_[0-9]+_HAIR$', outline=True, normal=True, prefix='Hair'),
  gen_mat_pattern(r'_CLOTH$', outline=True, doubleSided=True, prefix='Cloth'),
]

def combine_materials(context):
  smc = import_module('material-combiner-addon-master')
  combiner = smc.operators.combiner
  cats = True
  scn = context.scene
  bpy.ops.smc.refresh_ob_data()
  if cats:
      scn.smc_size = 'PO2'
      scn.smc_gaps = 16.0
  combiner.set_ob_mode(context.view_layer if combiner.globs.version > 0 else scn)
  data = combiner.get_data(scn.smc_ob_data)
  mats_uv = combiner.get_mats_uv(data)
  combiner.clear_empty_mats(data, mats_uv)
  #combiner.get_duplicates(mats_uv)
  structure = combiner.get_structure(data, mats_uv)
  if combiner.globs.version == 0:
      context.space_data.viewport_shade = 'MATERIAL'
  if (len(structure) == 1) and next(iter(structure.values()))['dup']:
      combiner.clear_duplicates(structure)
      bpy.ops.smc.refresh_ob_data()
      print('FINISHED')
  elif not structure or (len(structure) == 1):
      bpy.ops.smc.refresh_ob_data()
      print('ERROR: No unique materials selected')
      print('FINISHED')

  directory = bpy.path.abspath('//')
  scn = context.scene
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

mesh_patterns = [
  (re.compile(r'_FACE$|_EYE$|_Face_[0-9]+_SKIN$|^Face$'), 'Face'),
  (re.compile(r'_Body_[0-9]+_SKIN$|_HAIR_[0-9]+$|_HairBack_[0-9]+_HAIR$|_CLOTH$'), 'Body')
]
class Merge(bpy.types.Operator):
  bl_idname = 'vku.merge'
  bl_label = 'Merge objects'

  bl_options = {'REGISTER', 'UNDO'}

  def execute(self, context):
    bpy.ops.object.mode_set(mode='OBJECT')

    groups = {}
    for mesh in utils.get_mesh_objects(context):
      key = next(map(lambda a: a[1], filter(lambda a: a[0].search(mesh.name), mesh_patterns)), utils.get_default_prefix())
      if not key in groups:
        groups[key] = []
      groups[key].append(mesh)

    for name, targets in groups.items():
      bpy.ops.object.select_all(action='DESELECT')
      utils.set_active_object(context, targets[0])
      for o in targets:
        o.select_set(True)
      bpy.ops.cats_manual.join_meshes_selected()
      context.active_object.name = name

    bpy.ops.object.mode_set(mode='OBJECT')
    return {'FINISHED'}

def setup_layers(context, suffix = None):
  bpy.ops.smc.refresh_ob_data()
  smc_list = [item for item in context.scene.smc_ob_data if item.mat and item.type != 0]
  for item in smc_list:
    item.used = False
  for item in [item for item in smc_list if suffix == None or re.search(f'{suffix}$', item.mat.name)]:
    original_name = re.sub(f'{suffix}$', '', item.mat.name) if suffix else item.mat.name
    matched_index = next(map(lambda a: a[0], filter(lambda a: a[1][0].search(original_name), enumerate(mat_patterns))), None)
    if matched_index != None:
      item.layer = matched_index + 1
      item.used = True

def move_image(image, path):
  image.pack()
  image.unpack(method='WRITE_LOCAL')
  image.pack()
  image.filepath = path
  image.save()
  image.unpack(method='WRITE_LOCAL')
  image.filepath = path

def rename(context, suffix = None):
  name = utils.get_default_prefix()
  if suffix:
    name = f'{name}{suffix}'
  img_name = f'{name}.png'
  img_path = f'//textures/{img_name}'

  materials = utils.get_materials(context)
  for material in materials:
    m = re.match(r'^material_atlas_[0-9]+_([0-9]+)$', material.name)
    if m:
      mat_index = int(m[1]) - 1
      name = get_mat_name(mat_patterns[mat_index])
      material.name = f'{name}{suffix}' if suffix else name

  nodes = list(chain.from_iterable([material.node_tree.nodes for material in materials]))
  image_names = set([node.image.name for node in nodes if node.type == 'TEX_IMAGE'])
  atlas_images = [bpy.data.images[name] for name in image_names if re.match(r'^Atlas(_[0-9]+)?\.png$', name)]

  for image in atlas_images:
    image.name = img_name

  atlas_image = bpy.data.images[img_name]
  move_image(atlas_image, img_path)

  for mat in bpy.data.materials:
    if re.search(r'DoubleSided', mat.name):
      mat.use_backface_culling = False

extra_textures = (
  {
    'node_label': 'NomalmapTexture',
    'shader_slot': 'Normal',
    'suffix': '_nml',
  },
  {
    'node_label': 'Emission_Texture',
    'shader_slot': 'Emission',
    'suffix': '_emit',
  },
  {
    'node_label': 'OutlineWidthTexture',
    'shader_slot': None,
    'suffix': '_out',
  },
)

def generate_extra_atlas(context, node_label, shader_slot, suffix):
  print('Generating extra atlas', node_label, shader_slot, suffix)

  if not os.path.exists(bpy.path.abspath('//textures')):
    os.mkdir(bpy.path.abspath('//textures'))
  if not os.path.exists(bpy.path.abspath('//tmp')):
    os.mkdir(bpy.path.abspath('//tmp'))

  for obj in [o for o in context.scene.objects if o.type == 'MESH']:
    obj_copy = obj.copy()
    obj_copy.data = obj.data.copy()
    obj_copy.name = f'{obj.name}{suffix}'
    context.scene.collection.objects.link(obj_copy)

    for slot in [slot for slot in obj_copy.material_slots if slot.material]:
      material = slot.material
      material_copy = material.copy()
      material_copy.name = f'{material.name}{suffix}'
      slot.material = material_copy

      main_node = next(filter(lambda node: node.label == 'MainTexture', material_copy.node_tree.nodes))
      target_node = next(filter(lambda node: node.label == node_label, material_copy.node_tree.nodes), None)
      main_texture = main_node.image
      target_texture = target_node.image if target_node else None

      image_name = f'{material_copy.name}.png'
      image = target_texture.copy() if target_texture else bpy.data.images.new(image_name, *main_texture.size, alpha=True)
      image.name = image_name
      image.scale(*main_texture.size)
      move_image(image, f'//tmp/{image.name}')
      main_node.image = image

  setup_layers(context, suffix)
  combine_materials(context)
  rename(context, suffix)

  target_objects = [o for o in context.scene.objects if re.search(f'{suffix}$', o.name)]
  for obj in target_objects:
    context.scene.collection.objects.unlink(obj)

def connect_normal_atlas(context, suffix, shader_slot, node_label=None):
  for obj in utils.get_mesh_objects(context):
    for material in [slot.material for slot in obj.material_slots if slot.material]:
      shader_node = material.node_tree.nodes['Principled BSDF']
      target_node = material.node_tree.nodes.new(type='ShaderNodeTexImage')
      target_node.image = bpy.data.images[f'{utils.get_default_prefix()}{suffix}.png']
      if next(filter(lambda pattern: pattern[1] == material.name and pattern[5], mat_patterns), False):
        material.node_tree.links.new(target_node.outputs['Color'], shader_node.inputs[shader_slot])

class GenarateAtlas(bpy.types.Operator):
  bl_idname = 'vku.generate_atlas'
  bl_label = 'Rename atlas materials'
  bl_options = {'REGISTER', 'UNDO'}

  def execute(self, context):
    for options in [options for options in extra_textures]:
      generate_extra_atlas(context, **options)

    setup_layers(context)
    combine_materials(context)
    rename(context)

    for options in [options for options in extra_textures if options['shader_slot']]:
      connect_normal_atlas(context, **options)
    return {'FINISHED'}

classes = (
  Merge,
  GenarateAtlas,
)
