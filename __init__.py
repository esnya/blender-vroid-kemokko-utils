from vroid_kemokko_utils import *

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

from . import vroid_kemokko_uitils

register = vroid_kemokko_uitils.register
unregister = vroid_kemokko_uitils.unregister

if __name__ == '__main__':
  vroid_kemokko_uitils.register()
