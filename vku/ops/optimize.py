import bpy
import re
from . import utils
from itertools import chain
from importlib import import_module

# (Pattern, Prefix, Fade, Outline, DoubleSided, Fade)
def gen_mat_pattern(pattern, fade=False, outline=False, doubleSided=False, prefix=None, normal=False):
  return (re.compile(pattern), prefix, fade, outline, doubleSided, normal)

def get_mat_name(pattern):
  _, prefix, fade, outline, doubleSided, normal = pattern
  return '_'.join((
    prefix if prefix else utils.get_default_prefix(),
    'Fade' if fade else 'Cutout',
    'Outline' if outline else 'NoOutline',
    'DoubleSided' if doubleSided else 'SingleSided',
    'Nml' if normal else '',
  ))

mat_patterns = [
  gen_mat_pattern(r'_EyeExtra_', fade=True, prefix='Face'),
  gen_mat_pattern(r'_FACE$|_EYE$', prefix='Face'),
  gen_mat_pattern(r'_SKIN$', outline=True, prefix='Skin', normal=True),
  gen_mat_pattern(r'_Body_[0-9]+$', outline=True, doubleSided=True, prefix='Body'),
  gen_mat_pattern(r'_HAIR_[0-9]+$|_HairBack_[0-9]+_HAIR$', outline=True, prefix='Hair', normal=True),
  gen_mat_pattern(r'_CLOTH$', outline=True, doubleSided=True),
]

def combine_materials(context=bpy.context):
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
  (re.compile(r'_Body_[0-9]+_SKIN$|_HAIR_[0-9]+$|_HairBack_[0-9]+_HAIR$'), 'Body')
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
      utils.set_active_object(targets[0])
      for o in targets:
        o.select_set(True)
      bpy.ops.cats_manual.join_meshes_selected()
      context.active_object.name = name

    bpy.ops.object.mode_set(mode='OBJECT')
    return {'FINISHED'}

def setup_layers(context, prefix = None):
  bpy.ops.smc.refresh_ob_data()
  smc_list = [item for item in context.scene.smc_ob_data if item.mat and item.type != 0]
  for item in smc_list:
    item.used = False
  for item in [item for item in smc_list if prefix == None or re.search(rf'{prefix}$', item.mat.name)]:
    original_name = re.sub(r'_nml$', '', item.mat.name) if prefix else item.mat.name
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

def rename(context, prefix = None):
  name = utils.get_default_prefix()
  if prefix:
    name = f'{name}{prefix}'
  img_name = f'{name}.png'
  img_path = f'//textures/{img_name}'

  materials = utils.get_materials(context)
  for material in materials:
    m = re.match(r'^material_atlas_[0-9]+_([0-9]+)$', material.name)
    if m:
      mat_index = int(m[1]) - 1
      name = get_mat_name(mat_patterns[mat_index])
      material.name = f'{name}{prefix}' if prefix else name

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

class GenarateNormalAtlas(bpy.types.Operator):
  bl_idname = 'vku.generate_normal_atlas'
  bl_label = 'Generate normal atlas'
  bl_options = {'REGISTER', 'UNDO'}

  def execute(self, context):
    mesh_objects = [o for o in context.scene.objects if o.type == 'MESH']
    for obj in mesh_objects:
      copied = obj.copy()
      copied.data = obj.data.copy()
      copied.name = f'{obj.name}_nml'
      context.scene.collection.objects.link(copied)
      for slot in copied.material_slots:
        material = slot.material
        material_nml = material.copy()
        material_nml.name = f'{material.name}_nml'
        slot.material = material_nml

        main_node = next(filter(lambda node: node.label == 'MainTexture', material_nml.node_tree.nodes))
        normal_node = next(filter(lambda node: node.label == 'NomalmapTexture', material_nml.node_tree.nodes))
        main_texture = main_node.image
        normal_texture = normal_node.image

        image = normal_texture.copy()
        image.name = f'{material_nml.name}.png'
        image.scale(main_texture.size[0], main_texture.size[1])
        move_image(image, f'//textures/{image.name}')
        main_node.image = image

    setup_layers(context, '_nml')
    combine_materials()
    rename(context, '_nml')

    objects_nml = [o for o in context.scene.objects if re.search(r'_nml$', o.name)]
    for obj in objects_nml:
      context.scene.collection.objects.unlink(obj)

    return {'FINISHED'}

def add_normal_atlas(context):
  for obj in utils.get_mesh_objects(context):
    for slot in obj.material_slots:
      material = slot.material
      if not material or not re.search('Nml', material.name):
        break

      shader_node = material.node_tree.nodes['Principled BSDF']
      normal_node = material.node_tree.nodes.new(type='ShaderNodeTexImage')
      normal_node.image = bpy.data.images[f'{utils.get_default_prefix()}_nml.png']
      material.node_tree.links.new(normal_node.outputs['Color'], shader_node.inputs['Normal'])

class GenarateAtlas(bpy.types.Operator):
  bl_idname = 'vku.generate_atlas'
  bl_label = 'Rename atlas materials'
  bl_options = {'REGISTER', 'UNDO'}

  def execute(self, context):
    setup_layers(context)
    combine_materials()
    rename(context)
    add_normal_atlas(context)
    return {'FINISHED'}


classes = (
  Merge,
  GenarateNormalAtlas,
  GenarateAtlas,
)
