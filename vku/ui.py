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

    layout.column(align=True).operator('vku.cats_armature_fix', text='Fix [CATS]')
    layout.column(align=True).operator('vku.toggle_upper_chest', text='Disable Upper Chest').action = 'DISABLE'
    layout.column(align=True).operator('cats_eyes.create_eye_tracking', text='Create eye tracking [CATS]')
    layout.column(align=True).operator('cats_viseme.create', text='Create viseme [CATS]')
    layout.column(align=True).operator('vku.toggle_upper_chest', text='Enable Upper Chest').action = 'ENABLE'
    layout.column(align=True).operator('vku.rename_bone_names', text='Rename bone names')
    layout.column(align=True).operator('cats_manual.separate_by_materials', text='Separate by materials [CATS]')
    layout.column(align=True).operator('vku.fix_materials', text='Fix materials')
    layout.column(align=True).operator('vku.fix_meshes', text='Fix meshes')
    layout.column().separator()
    layout.column(align=True).operator('vku.shiitake', text='Shiitake')
    layout.column(align=True).operator('vku.remove_human_ears', text='RemoveHumanEars')
    layout.column().separator()
    layout.column(align=True).operator('vku.merge', text='Merge')
    layout.column(align=True).operator('vku.generate_normal_atlas', text='Generate normal Atlas')
    layout.column(align=True).operator('vku.generate_atlas', text='Generate  Atlas')
    layout.column(align=True).separator()
    layout.column(align=True).operator('file.pack_all', text='Pack all externals [Blender]')

classes = (
  MainPanel,
)
