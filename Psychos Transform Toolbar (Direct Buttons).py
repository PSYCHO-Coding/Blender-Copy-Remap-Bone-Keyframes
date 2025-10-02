bl_info = {
    "name": "Psycho's Transform Toolbar (Direct Buttons)",
    "author": "You",
    "version": (1, 1),
    "blender": (4, 5, 0),
    "location": "3D View > Header (flip to bottom if you want)",
    "description": "Adds transform orientation & pivot buttons as direct icon buttons",
    "category": "3D View",
}

import bpy


def draw_transform_toolbar(self, context):
    layout = self.layout
    scene = context.scene
    tool_settings = context.tool_settings

    row = layout.row(align=True)

    # 🔹 Transform Orientation buttons
    orientations = [
        ("GLOBAL", "ORIENTATION_GLOBAL"),
        ("LOCAL", "ORIENTATION_LOCAL"),
        ("NORMAL", "ORIENTATION_NORMAL"),
        ("GIMBAL", "ORIENTATION_GIMBAL"),
        ("VIEW", "ORIENTATION_VIEW"),
        ("CURSOR", "ORIENTATION_CURSOR"),
    ]

    for value, icon in orientations:
        op = row.operator(
            "wm.context_set_enum",
            text="",
            icon=icon,
            depress=(scene.transform_orientation_slots[0].type == value)
        )
        op.data_path = "scene.transform_orientation_slots[0].type"
        op.value = value

    row.separator(factor=1.5)

    # 🔹 Pivot Point buttons
    pivots = [
        ("BOUNDING_BOX_CENTER", "PIVOT_BOUNDBOX"),
        ("CURSOR", "PIVOT_CURSOR"),
        ("INDIVIDUAL_ORIGINS", "PIVOT_INDIVIDUAL"),
        ("MEDIAN_POINT", "PIVOT_MEDIAN"),
        ("ACTIVE_ELEMENT", "PIVOT_ACTIVE"),
    ]

    for value, icon in pivots:
        op = row.operator(
            "wm.context_set_enum",
            text="",
            icon=icon,
            depress=(tool_settings.transform_pivot_point == value)
        )
        op.data_path = "tool_settings.transform_pivot_point"
        op.value = value


def register():
    bpy.types.VIEW3D_HT_header.append(draw_transform_toolbar)


def unregister():
    bpy.types.VIEW3D_HT_header.remove(draw_transform_toolbar)


if __name__ == "__main__":
    register()
