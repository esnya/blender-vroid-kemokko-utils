import bpy
import re
import os
from itertools import chain

def get_default_prefix():
  return re.sub(r'\.blend$', '', bpy.path.basename(bpy.data.filepath))

def get_mesh_objects(context = bpy.context):
  return [o for o in context.scene.objects if o.type == 'MESH']

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

def get_materials(context = bpy.context):
  material_slots = list(chain.from_iterable([o.material_slots for o in get_mesh_objects(context)]))
  return [slot.material for slot in material_slots]
