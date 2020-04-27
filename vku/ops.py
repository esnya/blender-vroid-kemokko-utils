import bpy
import os
import utils
import re
from itertools import chain

class RenameKemoBones(bpy.types.Operator):
  bl_idname = 'vku.rename_kemo_bones'
  bl_label = 'Rename Kemo Bones'
  bl_options = {'REGISTER', 'UNDO'}

  def execute(self, context):
    ahoge=True

    armature = bpy.context.scene.objects['Armature']
    utils.set_active_object(armature)
    bpy.ops.object.mode_set(mode='EDIT')
    edit_bones = armature.data.edit_bones

    tail_bone = sorted(edit_bones['Head'].children, key=lambda b: b.head.z)[0]
    utils.rename_hierarcy(tail_bone, 'Tail')
    tail_bone.parent = edit_bones['Hips']

    top_bones = sorted(edit_bones['Head'].children, key=lambda b: -b.head.z)[0:3]
    if ahoge:
      utils.rename_hierarcy(top_bones[0], 'Ahoge')

    for ear_bone in top_bones[(1 if ahoge else 0):][:2]:
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

    bpy.ops.object.mode_set(mode='OBJECT')

    return {'FINISHED'}

  def invoke(self, context, event):
    return self.execute(context)

class ToggleUpperChest(bpy.types.Operator):
  bl_idname = 'vku.toggle_upper_chest'
  bl_label = 'Rename Kemo Bones'
  bl_options = {'REGISTER', 'UNDO'}

  action = bpy.props.StringProperty(default='TOGGLE')

  def execute(self, context):
    armature = bpy.context.scene.objects['Armature']
    utils.set_active_object(armature)
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
    bpy.ops.image.open(filepath=f'{os.path.dirname(__file__)}/..//EyeShiitake.png', files=[{ 'name': 'EyeShiitake.png' }], relative_path=True, show_multiview=False)
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

  def invoke(self, context, event):
    return self.execute(context)

class Kemokkonize(bpy.types.Operator):
  bl_idname = 'vku.kemokkonize'
  bl_label = 'More kemokko'
  bl_options = {'REGISTER', 'UNDO'}

  def execute(self, context):
    face = bpy.context.scene.objects['F00_000_00_Face_00_SKIN']
    utils.set_active_object(face)
    utils.select_vertices(face, lambda v: v.co[1] > 0)
    bpy.context.scene.tool_settings.transform_pivot_point = 'MEDIAN_POINT'
    bpy.ops.transform.resize(value=(0, 0, 0))

    bpy.ops.object.mode_set(mode='OBJECT')

    return {'FINISHED'}

class FixMisc(bpy.types.Operator):
  bl_idname = 'vku.fix_misc'
  bl_label = 'Fix textures, meshes, ...'
  bl_options = {'REGISTER', 'UNDO'}

  def execute(self, context):
    bpy.ops.image.open(filepath=f'{os.path.dirname(__file__)}/..//F00_000_HairBack_00.png', files=[{ 'name': 'F00_000_HairBack_00.png' }], relative_path=True, show_multiview=False)
    bpy.data.images['F00_000_HairBack_00.png'].filepath_raw = '//F00_000_HairBack_00.png'

    # Fix EyeExtra
    eye_extra = bpy.context.scene.objects['F00_000_00_EyeExtra_01_EYE']
    eye_extra.active_shape_key_index = 0
    utils.set_active_object(eye_extra)
    utils.select_vertices(eye_extra, lambda v: v.co[0] > 0)
    bpy.ops.transform.translate(value=(0.002, 0, 0))
    bpy.ops.transform.resize(value=(1, 1, 0.8))
    utils.select_vertices(eye_extra, lambda v: v.co[0] < 0)
    bpy.ops.transform.translate(value=(-0.002, 0, 0))
    bpy.ops.transform.resize(value=(1, 1, 0.8))

    # Fix LowerArm/Leg is not first child of UppderArm/Leg
    bpy.ops.object.mode_set(mode='OBJECT')
    utils.set_active_object(bpy.context.scene.objects['Armature'])
    bpy.ops.object.mode_set(mode='EDIT')
    bones = context.object.data.edit_bones
    joint_bones = [b for b in bones if re.search('^J_', b.name)]
    for b in joint_bones:
      b.name = f'ZZ_{b.name}'

    # for o in [o for o in get_mesh_objects(context) if re.search(r'_SKIN|_CLOTH$' , o.name)]:
    #   bpy.ops.object.mode_set(mode='OBJECT')
    #   set_active_object(o)
    #   bpy.ops.object.mode_set(mode='EDIT')
    #   bpy.ops.mesh.select_all(action='SELECT')
    #   bpy.ops.mesh.remove_doubles()
    #   bpy.ops.mesh.normals_make_consistent()

    # bpy.ops.object.mode_set(mode='OBJECT')
    # for mat in bpy.data.materials:
    #   mainNode = next(filter(lambda node: node.label == 'MainTexture', mat.node_tree.nodes), None)
    #   normalNode = next(filter(lambda node: node.label == 'NomalmapTexture', mat.node_tree.nodes), None)
    #   shaderGroup = mainNode.outputs['Color'].links[0].to_node if mainNode else None
    #   if mainNode and normalNode and shaderGroup and not re.search(r'NoneNormal', normalNode.image.name):
    #     mat.node_tree.links.new(normalNode.outputs['Color'], shaderGroup.inputs['NomalmapTexture'])

    bpy.ops.object.mode_set(mode='OBJECT')
    return {'FINISHED'}

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
    matched_index = next(map(lambda a: a[0], filter(lambda a: a[1][0].search(original_name), enumerate(utils.mat_patterns))), None)
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
      name = utils.get_mat_name(utils.mat_patterns[mat_index])
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
    utils.combine_materials()
    rename(context, '_nml')

    objects_nml = [o for o in context.scene.objects if re.search(r'_nml$', o.name)]
    for obj in objects_nml:
      context.scene.collection.objects.unlink(obj)

    return {'FINISHED'}

def add_normal_atlas(context):
  for obj in utils.get_mesh_objects(context):
    for slot in obj.material_slots:
      material = slot.material
      if not material:
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
    utils.combine_materials()
    rename(context)
    add_normal_atlas(context)
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
    bpy.ops.vku.toggle_upper_chest(action='DISABLE')
    bpy.ops.cats_eyes.create_eye_tracking()
    bpy.ops.cats_viseme.create()
    bpy.ops.vku.toggle_upper_chest(action='ENABLE')
    bpy.ops.vku.rename_kemo_bones()
    bpy.ops.cats_manual.separate_by_materials()
    bpy.ops.vku.remove_suffix()
    bpy.ops.vku.shiitake()
    bpy.ops.vku.kemokkonize()
    bpy.ops.vku.fix_misc()
    bpy.ops.vku.merge()
    bpy.ops.vku.generate_normal_atlas()
    bpy.ops.vku.generate_atlas()

    return {'FINISHED'}

  def invoke(self, context, event):
    return self.execute(context)
