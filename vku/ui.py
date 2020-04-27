import bpy

region_flag = 0 if bpy.app.version < (2, 80, 0) else 2 if bpy.app.version > (2, 80, 99) else 1

class MainPanel(bpy.types.Panel):
  bl_label = 'VKU'
  bl_idname = 'main_panel'
  bl_space_type = 'VIEW_3D'
  bl_region_type = 'UI' if region_flag else 'TOOLS'
  bl_category = 'VKU'

  def draw(self, context):
    layout = self.layout

    layout.column(align=True).operator('cats_armature.fix', text='(1) Fix [CATS]')
    layout.column(align=True).operator('vku.toggle_upper_chest', text='(2) Disable Upper Chest').action = 'DISABLE'
    layout.column(align=True).operator('cats_eyes.create_eye_tracking', text='(3) Create eye tracking [CATS]')
    layout.column(align=True).operator('cats_viseme.create', text='(4) Create viseme [CATS]')
    layout.column(align=True).operator('vku.toggle_upper_chest', text='(5) Enable Upper Chest').action = 'ENABLE'
    layout.column(align=True).operator('vku.rename_kemo_bones', text='(6) Rename kemo bones')
    layout.column(align=True).operator('cats_manual.separate_by_materials', text='(7) Separate by materials [CATS]')
    layout.column(align=True).operator('vku.remove_suffix', text='(8) Remove suffix')
    layout.column(align=True).operator('vku.shiitake', text='(9) Shiitake')
    layout.column(align=True).operator('vku.kemokkonize', text='(10) Kemokkonize')
    layout.column(align=True).operator('vku.fix_misc', text='(11) Fix misc')
    layout.column(align=True).operator('vku.merge', text='(12) Join meshes')
    layout.column(align=True).operator('vku.generate_normal_atlas', text='(13) Generate normal Atlas')
    layout.column(align=True).operator('vku.generate_atlas', text='(14) Generate  Atlas')
    layout.column(align=True).operator('file.pack_all', text='(15) Pack all externals [Blender]')
    layout.column(align=True).separator()
    layout.column(align=True).operator('vku.do_everything', text='Do evernything')
