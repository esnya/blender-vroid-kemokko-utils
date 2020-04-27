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
import bpy
import os
import sys

sys.path.append(f'{os.path.dirname(__file__)}/vku')

import ui
import ops

classes = [
  ops.RenameKemoBones,
  ops.ToggleUpperChest,
  ops.RemoveSuffix,
  ops.Shiitake,
  ops.FixMisc,
  ops.Merge,
  ops.GenarateAtlas,
  ops.GenarateNormalAtlas,
  ops.Kemokkonize,
  ops.DoEverything,
  ui.MainPanel,
]

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
