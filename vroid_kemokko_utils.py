import bpy
import re
import os
import importlib

bl_info = {
  'name': 'VRoid Kemokko Utils',
  'author': 'esnya',
  'version': (0, 0, 1),
  'blender': (2, 82, 0),
  'location': '',
  'description': 'Kemokkonize utilities for VRoid',
  'warning': '',
  'support': 'TESTING',
  'wiki_url': '',
  'tracker_url': '',
  'category': 'Object'
}

version = 0 if bpy.app.version < (2, 80, 0) else 2 if bpy.app.version > (2, 80, 99) else 1

mat_table = {
  'Face_Transparent_Noline_Front': re.compile(r'_EyeExtra'),
  'Face_Cutout_Noline_Front': re.compile(r'Eye(Highlight|Iris|White)|Face(Brow|Eyelash|Eyeline|Mouth)'),
  'Face_Cutout_Outline_Front': re.compile(r'_Face_|Shiitake'),
  'Body_Cutout_Outline_Front': re.compile(r'HairBack|HAIR_0[12]|Body|Ribbon'),
  'Body_Cutout_Outline_Both': re.compile(r'HAIR_0[34]|CLOTH'),
}
mat_layers = sorted(mat_table.keys())

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

class BipassUpperChest(bpy.types.Operator):
  bl_idname = 'vku.bipass_upper_chest'
  bl_label = 'Rename Kemo Bones'
  bl_options = {'REGISTER', 'UNDO'}

  def execute(self, context):
    state = None

    armature = bpy.context.scene.objects['Armature']
    set_active_object(armature)
    bpy.ops.object.mode_set(mode='EDIT')
    edit_bones = armature.data.edit_bones

    neck_bone = edit_bones['Neck']
    chest_bone = edit_bones['Chest']
    upper_chest_bone = edit_bones['Upper Chest']

    next_state = neck_bone.parent == upper_chest_bone if state == None else state
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
    eye_shiitake.name = 'EyeShiitake'

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
    eye_shiitake_mat.name = 'EyeShiitake'
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

class FixTextures(bpy.types.Operator):
  bl_idname = 'vku.fix_textures'
  bl_label = 'Fix textures'
  bl_options = {'REGISTER', 'UNDO'}

  def execute(self, context):
    bpy.data.images['F00_000_HairBack_00.png'].filepath_raw = '//F00_000_HairBack_00.png'

    return {'FINISHED'}


class SetupLayers(bpy.types.Operator):
  bl_idname = 'vku.setup_layers'
  bl_label = 'Setup atlas layers'
  bl_options = {'REGISTER', 'UNDO'}

  def execute(self, context):
    bpy.ops.smc.refresh_ob_data()
    mat_list = [mat for mat in bpy.context.scene.smc_ob_data if mat.mat and mat.type != 0]

    for mat in mat_list:
      for layer_name, mat_pattern in mat_table.items():
        if mat_pattern.search(mat.mat.name):
          mat.layer = mat_layers.index(layer_name) + 2
          mat.used = True
          break
    return {'FINISHED'}

  def invoke(self, context, event):
    return self.execute(context)

class RenameAtlas(bpy.types.Operator):
  bl_idname = 'vku.rename_atlas'
  bl_label = 'Rename atlas materials'
  bl_options = {'REGISTER', 'UNDO'}

  def execute(self, context):
    for i, layer_name in enumerate(mat_layers):
      for mat in bpy.data.materials:
        if re.match(f'^material_atlas_[0-9]+_{i + 2}$', mat.name):
          mat.name = layer_name

    for img in bpy.data.images:
      if re.match(r'^Atlas(_[0-9]+)?\.png$', img.name):
        img.name = 'Atlas.png'

    atlas = bpy.data.images['Atlas.png']
    atlas.pack()
    atlas.unpack(method='WRITE_LOCAL')
    atlas.pack()
    atlas.filepath_raw = '//textures/Atlas.png'
    atlas.save()
    atlas.unpack(method='WRITE_LOCAL')

    if bpy.data.materials.find('Body_Cutout_Outline_Both') >= 0:
      bpy.data.materials['Body_Cutout_Outline_Both'].use_backface_culling = False

    return {'FINISHED'}

  def invoke(self, context, event):
    return self.execute(context)

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

    for n in range(1, 5):
      try:
        bpy.ops.cats_armature.fix()
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.object.mode_set(mode='OBJECT')
        break
      except:
        print('Error')

    bpy.ops.vku.bipass_upper_chest()
    bpy.ops.cats_eyes.create_eye_tracking()
    bpy.ops.cats_viseme.create()
    bpy.ops.vku.bipass_upper_chest()
    bpy.ops.vku.rename_kemo_bones()
    bpy.ops.cats_manual.separate_by_materials()
    bpy.ops.vku.remove_suffix()
    bpy.ops.vku.shiitake()
    bpy.ops.vku.kemokkonize()
    bpy.ops.vku.fix_textures()
    bpy.ops.cats_manual.join_meshes()
    bpy.ops.vku.setup_layers()
    combine_materials()
    bpy.ops.vku.rename_atlas()

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
    layout.column(align=True).operator('vku.bipass_upper_chest', text='(2) Bipass Upper Chest')
    layout.column(align=True).operator('cats_eyes.create_eye_tracking', text='(3) Create eye tracking [CATS]')
    layout.column(align=True).operator('cats_viseme.create', text='(4) Create viseme [CATS]')
    layout.column(align=True).operator('vku.bipass_upper_chest', text='(5) Bipass Upper Chest')
    layout.column(align=True).operator('vku.rename_kemo_bones', text='(6) Rename kemo bones')
    layout.column(align=True).operator('cats_manual.separate_by_materials', text='(7) Separate by materials [CATS]')
    layout.column(align=True).operator('vku.remove_suffix', text='(8) Remove suffix')
    layout.column(align=True).operator('vku.shiitake', text='(9) Shiitake')
    layout.column(align=True).operator('vku.kemokkonize', text='(10) Kemokkonize')
    layout.column(align=True).operator('cats_manual.join_meshes', text='(11) Join all [CATS]')
    layout.column(align=True).operator('vku.fix_textures', text='(12) Fix textures')
    layout.column(align=True).operator('vku.setup_layers', text='(13) Setup layers')
    layout.column(align=True).operator('smc.combiner', text='(14) Generate atlas [CATS]').cats = True
    layout.column(align=True).operator('vku.rename_atlas', text='(15) Rename atlas materials')
    layout.column(align=True).separator()
    layout.column(align=True).operator('vku.do_everything', text='Do evernything')

classes = [
  RenameKemoBones,
  BipassUpperChest,
  RemoveSuffix,
  Shiitake,
  FixTextures,
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
