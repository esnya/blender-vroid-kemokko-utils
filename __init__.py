bl_info = {
  'name': 'VRoid Kemokko Utils',
  'author': 'esnya',
  'version': (0, 0, 1),
  'blender': (2, 80, 0),
  'location': '',
  'description': 'Kemokkonize utilities for VRoid',
  'warning': '',
  'support': 'TESTING',
  'wiki_url': '',
  'tracker_url': '',
  'category': 'Object'
}

import bpy
from .vku import ui
from .vku.ops import cats_enhance, kemo_fix, optimize

classes = (
  *ui.classes,
  *cats_enhance.classes,
  *kemo_fix.classes,
  *optimize.classes,
)

def register():
  print('Regitering VKU')
  for c in classes:
    bpy.utils.register_class(c)

def unregister():
  print('Unregitering VKU')
  for c in classes:
    bpy.utils.unregister_class(c)

if __name__ == '__main__':
  register()
