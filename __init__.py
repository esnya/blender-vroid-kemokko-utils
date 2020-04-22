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


# Append files to sys path
import sys
import bpy
from . import vroid_kemokko_utils

def register():
  print('Regitering VKU')
  vroid_kemokko_utils.register()
  for c in vroid_kemokko_utils.classes:
    bpy.utils.register_class(c)

def unregister():
  print('Unregitering VKU')
  vroid_kemokko_utils.unregister()

if __name__ == '__main__':
  register()
