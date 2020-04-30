import bpy
import os
import re
from . import utils


class Shiitake(bpy.types.Operator):
  bl_idname = 'vku.shiitake'
  bl_label = 'Append shiitake'
  bl_options = {'REGISTER', 'UNDO'}

  @classmethod
  def poll(self, context):
    return not 'EyeShiitake_FACE' in context.scene.objects

  def execute(self, context):
    # Duplicate Eye Extra
    eye_extra = bpy.context.scene.objects['F00_000_00_EyeExtra_01_EYE']
    utils.set_active_object(eye_extra)
    bpy.ops.object.duplicate()

    # Rename
    eye_shiitake = bpy.context.scene.objects[next(reversed(sorted([o.name for o in bpy.context.scene.objects if o.name.startswith(eye_extra.name)])))]
    eye_shiitake.name = 'EyeShiitake_FACE'

    # Add shape key
    eye_shiitake.active_shape_key_index = eye_shiitake.to_mesh().shape_keys.key_blocks.find('EyeExtra 01.M F00 000 00 EyeExtra On')
    eye_shiitake.active_shape_key.name = 'Eye Shiitake'

    # Assign weights
    utils.set_active_object(eye_shiitake)
    utils.select_vertices(eye_shiitake, lambda v: v.co[0] > 0)
    bpy.ops.object.vertex_group_set_active(group='Eye_L')
    bpy.ops.object.vertex_group_assign()
    bpy.ops.object.vertex_group_set_active(group='LeftEye')
    bpy.ops.object.vertex_group_assign()
    utils.select_vertices(eye_shiitake, lambda v: v.co[0] < 0)
    bpy.ops.object.vertex_group_set_active(group='Eye_R')
    bpy.ops.object.vertex_group_assign()
    bpy.ops.object.vertex_group_set_active(group='RightEye')
    bpy.ops.object.vertex_group_assign()

    # Create material
    bpy.ops.object.mode_set(mode='OBJECT')
    eye_shiitake_mat = bpy.context.active_object.material_slots[0].material.copy()
    bpy.context.active_object.material_slots[0].material = eye_shiitake_mat
    eye_shiitake_mat.name = 'EyeShiitake_FACE'
    bpy.ops.image.open(filepath=f'{os.path.dirname(__file__)}/../..//EyeShiitake.png', files=[{ 'name': 'EyeShiitake.png' }], relative_path=True, show_multiview=False)
    eye_shiitake_mat.node_tree.nodes['Image Texture'].image = bpy.data.images['EyeShiitake.png']

    # Add shape key into highlight
    highlight = bpy.context.scene.objects['F00_000_00_EyeHighlight_00_EYE']
    utils.set_active_object(highlight)
    highlight.shape_key_add(name='Eye Shiitake')
    highlight.active_shape_key_index = highlight.to_mesh().shape_keys.key_blocks.find('Eye Shiitake')
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.transform.translate(value=(0, 0.005, 0))

    bpy.ops.object.mode_set(mode='OBJECT')

    return {'FINISHED'}

class RemoveHumanEars(bpy.types.Operator):
  bl_idname = 'vku.remove_human_ears'
  bl_label = 'Delete human ears'
  bl_options = {'REGISTER', 'UNDO'}

  def execute(self, context):
    face = context.scene.objects['F00_000_00_Face_00_SKIN']
    utils.set_active_object(face)
    utils.select_vertices(face, lambda v: v.co[1] > 0)
    bpy.ops.mesh.separate(type='SELECTED')
    bpy.ops.object.mode_set(mode='OBJECT')
    utils.set_active_object(context.scene.objects['F00_000_00_Face_00_SKIN.001'])
    bpy.ops.object.delete()

    return {'FINISHED'}

classes = (
  Shiitake,
  RemoveHumanEars,
)
