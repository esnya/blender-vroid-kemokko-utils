import bpy
import re
import os
import importlib
from itertools import chain

version = 0 if bpy.app.version < (2, 80, 0) else 2 if bpy.app.version > (2, 80, 99) else 1

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
  smc = importlib.import_module('material-combiner-addon-master')
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
  combiner.get_duplicates(mats_uv)
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

class RenameKemoBones(bpy.types.Operator):
  bl_idname = 'vku.rename_kemo_bones'
  bl_label = 'Rename Kemo Bones'
  bl_options = {'REGISTER', 'UNDO'}

  def execute(self, context):
    ahoge=True

    armature = bpy.context.scene.objects['Armature']
    set_active_object(armature)
    bpy.ops.object.mode_set(mode='EDIT')
    edit_bones = armature.data.edit_bones

    tail_bone = sorted(edit_bones['Head'].children, key=lambda b: b.head.z)[0]
    rename_hierarcy(tail_bone, 'Tail')
    tail_bone.parent = edit_bones['Hips']

    top_bones = sorted(edit_bones['Head'].children, key=lambda b: -b.head.z)[0:3]
    if ahoge:
      rename_hierarcy(top_bones[0], 'Ahoge')

    for ear_bone in top_bones[(1 if ahoge else 0):][:2]:
      side = 'Left' if ear_bone.head.x > 0 else 'Right'
      rename_hierarcy(ear_bone, f'Ear{side}')

    bpy.ops.object.mode_set(mode='OBJECT')

    return {'FINISHED'}

  def invoke(self, context, event):
    return self.execute(context)

class ToggleUpperChest(bpy.types.Operator):
  bl_idname = 'vku.toggle_upper_chest'
  bl_label = 'Rename Kemo Bones'
  bl_options = {'REGISTER', 'UNDO'}

  state = bpy.props.BoolProperty(default=None)

  def execute(self, context):
    armature = bpy.context.scene.objects['Armature']
    set_active_object(armature)
    bpy.ops.object.mode_set(mode='EDIT')
    edit_bones = armature.data.edit_bones

    neck_bone = edit_bones['Neck']
    chest_bone = edit_bones['Chest']
    upper_chest_bone = edit_bones['Upper Chest']

    next_state = neck_bone.parent == upper_chest_bone if self.state == None else self.state
    neck_bone.parent = chest_bone if next_state else upper_chest_bone

    bpy.ops.object.mode_set(mode='OBJECT')

    return {'FINISHED'}

  def invoke(self, context, state=None):
    return self.execute(state)

class RemoveSuffix(bpy.types.Operator):
  bl_idname = 'vku.remove_suffix'
  bl_label = 'Remove suffix such as "xxx.001"'
  bl_options = {'REGISTER', 'UNDO'}

  def execute(self, context):
    for obj in bpy.context.scene.objects:
      obj.name = re.sub(r'\.[0-9]+$', '', obj.name)
      for slot in obj.material_slots:
        slot.material.name = re.sub(r'\.[0-9]+$', '', slot.material.name)

    return {'FINISHED'}

  def invoke(self, context, event):
    return self.execute(context)

class Shiitake(bpy.types.Operator):
  bl_idname = 'vku.shiitake'
  bl_label = 'Append shiitake'
  bl_options = {'REGISTER', 'UNDO'}

  def execute(self, context):
    # Duplicate Eye Extra
    eye_extra = bpy.context.scene.objects['F00_000_00_EyeExtra_01_EYE']
    set_active_object(eye_extra)
    bpy.ops.object.duplicate()

    # Rename
    eye_shiitake = bpy.context.scene.objects[next(reversed(sorted([o.name for o in bpy.context.scene.objects if o.name.startswith(eye_extra.name)])))]
    eye_shiitake.name = 'EyeShiitake_FACE'

    # Add shape key
    eye_shiitake.active_shape_key_index = eye_shiitake.to_mesh().shape_keys.key_blocks.find('EyeExtra 01.M F00 000 00 EyeExtra On')
    eye_shiitake.active_shape_key.name = 'Eye Shiitake'

    # Assign weights
    set_active_object(eye_shiitake)
    select_vertices(eye_shiitake, lambda v: v.co[0] > 0)
    bpy.ops.object.vertex_group_set_active(group='Eye_L')
    bpy.ops.object.vertex_group_assign()
    bpy.ops.object.vertex_group_set_active(group='LeftEye')
    bpy.ops.object.vertex_group_assign()
    select_vertices(eye_shiitake, lambda v: v.co[0] < 0)
    bpy.ops.object.vertex_group_set_active(group='Eye_R')
    bpy.ops.object.vertex_group_assign()
    bpy.ops.object.vertex_group_set_active(group='RightEye')
    bpy.ops.object.vertex_group_assign()

    # Create material
    bpy.ops.object.mode_set(mode='OBJECT')
    eye_shiitake_mat = bpy.context.active_object.material_slots[0].material.copy()
    bpy.context.active_object.material_slots[0].material = eye_shiitake_mat
    eye_shiitake_mat.name = 'EyeShiitake_FACE'
    bpy.ops.image.open(filepath='//EyeShiitake.png', files=[{ 'name': 'EyeShiitake.png' }], relative_path=True, show_multiview=False)
    eye_shiitake_mat.node_tree.nodes['Image Texture'].image = bpy.data.images['EyeShiitake.png']

    # Add shape key into highlight
    highlight = bpy.context.scene.objects['F00_000_00_EyeHighlight_00_EYE']
    set_active_object(highlight)
    highlight.shape_key_add(name='Eye Shiitake')
    highlight.active_shape_key_index = highlight.to_mesh().shape_keys.key_blocks.find('Eye Shiitake')
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.transform.translate(value=(0, 0.005, 0))

    bpy.ops.object.mode_set(mode='OBJECT')

    return {'FINISHED'}

  def invoke(self, context, event):
    return self.execute(context)

class Kemokkonize(bpy.types.Operator):
  bl_idname = 'vku.kemokkonize'
  bl_label = 'More kemokko'
  bl_options = {'REGISTER', 'UNDO'}

  def execute(self, context):
    face = bpy.context.scene.objects['F00_000_00_Face_00_SKIN']
    set_active_object(face)
    select_vertices(face, lambda v: v.co[1] > 0)
    bpy.context.scene.tool_settings.transform_pivot_point = 'MEDIAN_POINT'
    bpy.ops.transform.resize(value=(0, 0, 0))

    bpy.ops.object.mode_set(mode='OBJECT')

    return {'FINISHED'}

class FixMisc(bpy.types.Operator):
  bl_idname = 'vku.fix_misc'
  bl_label = 'Fix textures, meshes, ...'
  bl_options = {'REGISTER', 'UNDO'}

  def execute(self, context):
    bpy.data.images['F00_000_HairBack_00.png'].filepath_raw = '//F00_000_HairBack_00.png'

    eye_extra = bpy.context.scene.objects['F00_000_00_EyeExtra_01_EYE']
    eye_extra.active_shape_key_index = 0
    set_active_object(eye_extra)
    select_vertices(eye_extra, lambda v: v.co[0] > 0)
    bpy.ops.transform.translate(value=(0.002, 0, 0))
    select_vertices(eye_extra, lambda v: v.co[0] < 0)
    bpy.ops.transform.translate(value=(-0.002, 0, 0))

    for o in [o for o in get_mesh_objects(context) if re.search(r'_SKIN|_CLOTH$' , o.name)]:
      bpy.ops.object.mode_set(mode='OBJECT')
      set_active_object(o)
      bpy.ops.object.mode_set(mode='EDIT')
      bpy.ops.mesh.select_all(action='SELECT')
      bpy.ops.mesh.remove_doubles()
      bpy.ops.mesh.normals_make_consistent()

    bpy.ops.object.mode_set(mode='OBJECT')
    return {'FINISHED'}

mesh_patterns = [
  (re.compile(r'_FACE$|_EYE$|_Face_[0-9]+_SKIN$|^Face$'), 'Face'),
  (re.compile(r'_Body_[0-9]+_SKIN$_HAIR_[0-9]+$|_HairBack_[0-9]+_HAIR$'), 'Body')
]
class Merge(bpy.types.Operator):
  bl_idname = 'vku.merge'
  bl_label = 'Merge objects'

  bl_options = {'REGISTER', 'UNDO'}

  def execute(self, context):
    bpy.ops.object.mode_set(mode='OBJECT')

    groups = {}
    for mesh in get_mesh_objects(context):
      key = next(map(lambda a: a[1], filter(lambda a: a[0].search(mesh.name), mesh_patterns)), get_default_prefix())
      if not key in groups:
        groups[key] = []
      groups[key].append(mesh)

    for name, targets in groups.items():
      bpy.ops.object.select_all(action='DESELECT')
      set_active_object(targets[0])
      for o in targets:
        o.select_set(True)
      bpy.ops.cats_manual.join_meshes_selected()
      context.active_object.name = name

    bpy.ops.object.mode_set(mode='OBJECT')
    return {'FINISHED'}

class SetupLayers(bpy.types.Operator):
  bl_idname = 'vku.setup_layers'
  bl_label = 'Setup atlas layers'
  bl_options = {'REGISTER', 'UNDO'}

  def execute(self, context):
    bpy.ops.smc.refresh_ob_data()
    mat_list = [mat for mat in bpy.context.scene.smc_ob_data if mat.mat and mat.type != 0]

    for mat in mat_list:
      matched_index = next(map(lambda a: a[0], filter(lambda a: a[1][0].search(mat.mat.name), enumerate(mat_patterns))), None)
      if matched_index == None:
        mat.used = False
      else:
        mat.layer = matched_index + 1
        mat.used = True

    return {'FINISHED'}

  def invoke(self, context, event):
    return self.execute(context)

class RenameAtlas(bpy.types.Operator):
  bl_idname = 'vku.rename_atlas'
  bl_label = 'Rename atlas materials'
  bl_options = {'REGISTER', 'UNDO'}

  def execute(self, context):
    name = get_default_prefix()
    img_name = f'{name}.png'
    img_path = f'//textures/{img_name}'

    materials = get_materials(context)
    for material in materials:
      m = re.match(r'^material_atlas_[0-9]+_([0-9]+)$', material.name)
      if m:
        mat_index = int(m[1]) - 1
        material.name = get_mat_name(mat_patterns[mat_index])

    nodes = list(chain.from_iterable([material.node_tree.nodes for material in materials]))
    image_names = set([node.image.name for node in nodes if node.type == 'TEX_IMAGE'])
    atlas_images = [bpy.data.images[name] for name in image_names if re.match(r'^Atlas(_[0-9]+)?\.png$', name)]

    for image in atlas_images:
      image.name = img_name

    atlas_image = bpy.data.images[img_name]
    atlas_image.pack()
    atlas_image.unpack(method='WRITE_LOCAL')
    atlas_image.pack()
    atlas_image.filepath = img_path
    atlas_image.save()
    atlas_image.unpack(method='WRITE_LOCAL')
    atlas_image.filepath = img_path

    for mat in bpy.data.materials:
      if re.search(r'DoubleSided', mat.name):
        mat.use_backface_culling = False

    return {'FINISHED'}

class DoEverything(bpy.types.Operator):
  bl_idname = 'vku.do_everything'
  bl_label = 'Do everything'
  bl_options = {'REGISTER', 'UNDO'}

  def execute(self, context):
    scene = bpy.context.scene

    scene.keep_end_bones = True
    scene.keep_end_bones = True
    scene.keep_upper_chest = True
    scene.join_meshes = True
    scene.connect_bones = True
    scene.fix_materials = True
    scene.combine_mats = True
    scene.remove_zero_weight = True

    bpy.ops.cats_armature.fix()
    bpy.ops.vku.toggle_upper_chest()
    bpy.ops.cats_eyes.create_eye_tracking()
    bpy.ops.cats_viseme.create()
    bpy.ops.vku.toggle_upper_chest()
    bpy.ops.vku.rename_kemo_bones()
    bpy.ops.cats_manual.separate_by_materials()
    bpy.ops.vku.remove_suffix()
    bpy.ops.vku.shiitake()
    bpy.ops.vku.kemokkonize()
    bpy.ops.vku.fix_misc()
    bpy.ops.vku.merge()
    bpy.ops.vku.setup_layers()
    combine_materials()
    bpy.ops.vku.rename_atlas()
    bpy.ops.file.pack_all()

    return {'FINISHED'}

  def invoke(self, context, event):
    return self.execute(context)

class MainPanel(bpy.types.Panel):
  bl_label = 'VKU'
  bl_idname = 'main_panel'
  bl_space_type = 'VIEW_3D'
  bl_region_type = 'UI' if version else 'TOOLS'
  bl_category = 'VKU'

  def draw(self, context):
    layout = self.layout

    layout.column(align=True).operator('cats_armature.fix', text='(1) Fix [CATS]')
    layout.column(align=True).operator('vku.toggle_upper_chest', text='(2) Disable Upper Chest')
    layout.column(align=True).operator('cats_eyes.create_eye_tracking', text='(3) Create eye tracking [CATS]')
    layout.column(align=True).operator('cats_viseme.create', text='(4) Create viseme [CATS]')
    layout.column(align=True).operator('vku.toggle_upper_chest', text='(5) Enable Upper Chest')
    layout.column(align=True).operator('vku.rename_kemo_bones', text='(6) Rename kemo bones')
    layout.column(align=True).operator('cats_manual.separate_by_materials', text='(7) Separate by materials [CATS]')
    layout.column(align=True).operator('vku.remove_suffix', text='(8) Remove suffix')
    layout.column(align=True).operator('vku.shiitake', text='(9) Shiitake')
    layout.column(align=True).operator('vku.kemokkonize', text='(10) Kemokkonize')
    layout.column(align=True).operator('vku.fix_misc', text='(11) Fix misc')
    layout.column(align=True).operator('vku.merge', text='(12) Join meshes')
    layout.column(align=True).operator('vku.setup_layers', text='(13) Setup layers')
    layout.column(align=True).operator('smc.combiner', text='(14) Generate atlas [CATS]').cats = True
    layout.column(align=True).operator('vku.rename_atlas', text='(15) Rename atlas materials')
    layout.column(align=True).operator('file.pack_all', text='(16) Pack all externals [Blender]')
    layout.column(align=True).separator()
    layout.column(align=True).operator('vku.do_everything', text='Do evernything')

classes = [
  RenameKemoBones,
  ToggleUpperChest,
  RemoveSuffix,
  Shiitake,
  FixMisc,
  Merge,
  SetupLayers,
  RenameAtlas,
  Kemokkonize,
  DoEverything,
  MainPanel,
]

def register():
  for c in classes:
    bpy.utils.register_class(c)

def unregister():
  for c in classes:
    bpy.utils.unregister_class(c)

if __name__ == '__main__':
  register()
