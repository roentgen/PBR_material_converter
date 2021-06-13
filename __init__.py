from bpy.types import Operator, Panel, PropertyGroup

bl_info = {
    "name" : "PBR Material Converter",
    "author" : "roentgen",
    "version" : (0, 1),
    "blender" : (2, 91, 0),
    "location" : "Material > Conversion",
    "description" : "",
    "warning" : "",
    "wiki_url" : "",
    "category" : "Material",
    "support": "TESTING"
}

if "bpy" in locals():
    print("Reload material_converter")
    from importlib import reload
    reload(material_converter)
else:
    print("Import material_converter")
    from . import material_converter

import bpy

class PBRMaterialConverterPanel(bpy.types.Panel):
    """Main Panel of Materal Conversion: ExtremePBR to Octane"""
    bl_label = "Conversion ExtPBR to Octane"
    bl_idname = "pbr_to_octane.panel"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "material"
    # bl_context = "object"

    @classmethod
    def poll(self, context):
        return True
        #return context.active_object != None and context.active_object.active_material != None

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        layout.label(text=" Option:")
        row = layout.row()
        layout.label(text="Conversion:")
        row = layout.row()
        row.scale_y = 3.0
        row.operator("pbr_to_octane.conv")

class MATERIAL_OT_ConvPBRToOctane(bpy.types.Operator):
    bl_idname = "pbr_to_octane.conv"
    bl_label = "Convert"

    def execute(self, context):
        material_converter.start(context.active_object.active_material)
        #dryrun(context.active_object.active_material)
        return{'FINISHED'}

classes = [PBRMaterialConverterPanel, MATERIAL_OT_ConvPBRToOctane]

def register():
    [bpy.utils.register_class(c) for c in classes]

def unregister():
    [bpy.utils.unregister_class(c) for c in classes]

if __name__ == "__main__":
    register()

