import bpy
import os
import re
from . import utils
from importlib import import_module
from itertools import chain

class CatsArmatureFix(bpy.types.Operator):
  bl_idname = 'vku.cats_armature_fix'
  bl_label = 'Cats Armature Fix'
  bl_ooptions = {'REGISETR', 'UNDO'}

  def execute(self, context):
    context.scene.keep_end_bones = True
    context.scene.keep_upper_chest = True
    bpy.ops.cats_armature.fix()
    return {'FINISHED'}

class FixBoneNames(bpy.types.Operator):
  bl_idname = 'vku.rename_bone_names'
  bl_label = 'Fix name of bones'
  bl_options = {'REGISTER', 'UNDO'}
  ahoge = bpy.props.BoolProperty(default=True)

  def execute(self, context):
    armature = context.scene.objects['Armature']
    utils.set_active_object(context, armature)
    bpy.ops.object.mode_set(mode='EDIT')
    edit_bones = armature.data.edit_bones

    # Rename Ahoge/Ears/Tail

    tail_bone = sorted(edit_bones['Head'].children, key=lambda b: b.head.z)[0]
    utils.rename_hierarcy(tail_bone, 'Tail')
    tail_bone.parent = edit_bones['Hips']

    top_bones = sorted(edit_bones['Head'].children, key=lambda b: -b.head.z)[0:3]
    if self.ahoge:
      utils.rename_hierarcy(top_bones[0], 'Ahoge')

    for ear_bone in top_bones[(1 if self.ahoge else 0):][:2]:
      side = 'Left' if ear_bone.head.x > 0 else 'Right'
      utils.rename_hierarcy(ear_bone, f'Ear{side}')

    tail_z_threshold = edit_bones['Spine'].tail.z
    bpy.ops.object.mode_set(mode='OBJECT')

    for obj in utils.get_mesh_objects(context):
      vertices = [v for v in obj.data.vertices if v.co[2] < tail_z_threshold]
      head_index = obj.vertex_groups['Head'].index
      targets = chain.from_iterable([(v.index, g.weight) for g in v.groups if g.group == head_index] for v in vertices)
      for index, weight in targets:
        obj.vertex_groups['Head'].remove([index])
        obj.vertex_groups['Hips'].add([index], weight, 'ADD')

    # Fix LowerArm/Leg is not first child of UppderArm/Leg
    bpy.ops.object.mode_set(mode='OBJECT')
    utils.set_active_object(context, context.scene.objects['Armature'])
    bpy.ops.object.mode_set(mode='EDIT')
    bones = context.object.data.edit_bones
    joint_bones = [b for b in bones if re.search('^J_', b.name)]
    for b in joint_bones:
      b.name = f'ZZ_{b.name}'

    bpy.ops.object.mode_set(mode='OBJECT')

    return {'FINISHED'}

  def invoke(self, context, event):
    return self.execute(context)

class ToggleUpperChest(bpy.types.Operator):
  bl_idname = 'vku.toggle_upper_chest'
  bl_label = 'Toggle "Upper Chest"'
  bl_options = {'REGISTER', 'UNDO'}

  action = bpy.props.StringProperty(default='TOGGLE')

  def execute(self, context):
    armature = context.scene.objects['Armature']
    utils.set_active_object(context, armature)
    bpy.ops.object.mode_set(mode='EDIT')
    edit_bones = armature.data.edit_bones

    neck_bone = edit_bones['Neck']
    chest_bone = edit_bones['Chest']
    upper_chest_bone = edit_bones['Upper Chest']

    next_state = neck_bone.parent == chest_bone if self.action == 'TOGGLE' else False if self.action == 'DISABLE' else True
    neck_bone.parent = upper_chest_bone if next_state else chest_bone

    bpy.ops.object.mode_set(mode='OBJECT')

    return {'FINISHED'}

  def invoke(self, context, state=None):
    return self.execute(state)

def get_addon_texture_path(path):
  return f'{os.path.dirname(__file__)}/../../{path}'

class FixMaterials(bpy.types.Operator):
  bl_idname = 'vku.fix_materials'
  bl_label = 'Fix materials'
  bl_options = {'REGISTER', 'UNDO'}

  def execute(self, context):
    image = bpy.data.images['F00_000_00_Face_00_nml.png']
    if len(image.packed_files) > 0:
      image.unpack(method='WRITE_LOCAL')
    image.filepath = get_addon_texture_path('//F00_000_00_Face_00_nml_fix.png')

    for pattern, source in [(r'^F[0-9]+_[0-9]+_Hair_[0-9]+_HAIR_[0-9]+$', '//F00_000_Hair_00_00_out_fix.png'), (r'^F[0-9]+_[0-9]+_[0-9]+_Body_[0-9]+_SKIN$', '//F00_001_01_Body_00_out_fix.png')]:
      for material in [m for m in bpy.data.materials if re.search(pattern, m.name)]:
        node = material.node_tree.nodes.new(type='ShaderNodeTexImage')
        node.label = 'OutlineWidthTexture'
        node.image = bpy.data.images.load(get_addon_texture_path(source))
        node.image.name = f'{material.name}_out.png'

    if os.path.exists(bpy.path.abspath('//F00_000_HairBack_00.png')):
      image = bpy.data.images['F00_000_HairBack_00.png']
      if len(image.packed_files) > 0:
        image.unpack(method='WRITE_LOCAL')
      image.filepath = '//F00_000_HairBack_00.png'
    else:
      print('F00_000_HairBack_00.png not found')

    return {'FINISHED'}

class FixMeshes(bpy.types.Operator):
  bl_idname = 'vku.fix_meshes'
  bl_label = 'Fix meshes'

  def execute(self, context):
    # Fix EyeExtra
    eye_extra = context.scene.objects['F00_000_00_EyeExtra_01_EYE']
    eye_extra.active_shape_key_index = 0
    utils.set_active_object(context, eye_extra)
    utils.select_vertices(eye_extra, lambda v: v.co[0] > 0)
    bpy.ops.transform.translate(value=(0.002, 0, 0))
    bpy.ops.transform.resize(value=(1, 1, 0.6))
    utils.select_vertices(eye_extra, lambda v: v.co[0] < 0)
    bpy.ops.transform.translate(value=(-0.002, 0, 0))
    bpy.ops.transform.resize(value=(1, 1, 0.6))

    # Merge by discance
    targets = [o for o in context.scene.objects if re.search(r'_SKIN$', o.name)]
    for target in targets:
      utils.set_active_object(context, target)
      bpy.ops.object.mode_set(mode='EDIT')
      bpy.ops.mesh.select_all(action='SELECT')
      bpy.ops.mesh.remove_doubles()

    bpy.ops.object.mode_set(mode='OBJECT')

    return {'FINISHED'}

classes = (
  CatsArmatureFix,
  FixBoneNames,
  ToggleUpperChest,
  FixMaterials,
  FixMeshes,
)
