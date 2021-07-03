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
    "support": "COMMUNITY"
}

if "bpy" in locals():
    print("Reload material_converter")
    from importlib import reload
    reload(material_converter)
else:
    print("Import material_converter")
    from . import material_converter

import bpy

class Props(bpy.types.PropertyGroup):
    only_active_material : bpy.props.BoolProperty(
        name="Only Active Material",
        description="convert only an active material, or all materials of the object if unchecked",
        default=True)
    create_new_material : bpy.props.BoolProperty(
        name="Create New Material",
        description="whether conversion will create new material or not",
        default=False)
    gamma_revice: bpy.props.BoolProperty(
        name="Add Bias to Gamma/Power",
        description="Add a bias to gamma/power on textures so that it gets the result closer to EEVEE of",
        default=True)

class PBRMATERIALCONVERTER_PT_Panel(bpy.types.Panel):
    """Main Panel of Materal Conversion: ExtremePBR to Octane"""
    bl_label = "Conversion ExtPBR to Octane"
    bl_idname = "PBRMATERIALCONVERTER_PT_Panel"
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
        layout.label(text="Option:")
        layout.prop(scene.pbr_oct_cvt_setting, "only_active_material")
        layout.prop(scene.pbr_oct_cvt_setting, "create_new_material")
        layout.prop(scene.pbr_oct_cvt_setting, "gamma_revice")
        
        row = layout.row()
        layout.label(text="Conversion:")
        row = layout.row()
        row.scale_y = 2.0
        row.operator("pbr_to_octane.conv")
        row.enabled = bpy.context.scene.render.engine == 'octane'

class MATERIAL_OT_ConvPBRToOctane(bpy.types.Operator):
    """Do Conversion: Need Octane Renderer's Enabled"""
    bl_idname = "pbr_to_octane.conv"
    bl_label = "Convert"

    def execute(self, context):
        if bpy.context.scene['pbr_oct_cvt_setting']['only_active_material'] == 1:
            material_converter.start(context.active_object.active_material)
        else:
            for m in bpy.context.active_object.material_slots:
                material_converter.start(m.material)
        #dryrun(context.active_object.active_material)
        return{'FINISHED'}

classes = [Props, PBRMATERIALCONVERTER_PT_Panel, MATERIAL_OT_ConvPBRToOctane]

def register():
    [bpy.utils.register_class(c) for c in classes]
    bpy.types.Scene.pbr_oct_cvt_setting = bpy.props.PointerProperty(type=Props)

def unregister():
    [bpy.utils.unregister_class(c) for c in classes]
    del bpy.types.Scene.pbr_oct_cvt_setting

if __name__ == "__main__":
    register()

