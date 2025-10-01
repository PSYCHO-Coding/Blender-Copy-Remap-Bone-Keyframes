# Blender Plugin: Copy Bone Keyframes with Axis Mapping
# This plugin allows users to copy keyframes from one bone to another with axis remapping.

bl_info = {
    "name": "Copy Bone Keyframes with Axis Mapping",
    "author": "Nesha",
    "version": (1, 0),
    "blender": (3, 0, 0),
    "location": "3D View > Tool Shelf",
    "description": "Copy keyframes from one bone to another with axis remapping. For now only location axis remapping is supported.",
    "category": "Animation",
}

import bpy

class CopyBoneKeyframesOperator(bpy.types.Operator):
    """Copy keyframes from one bone to another with axis remapping."""
    bl_idname = "object.copy_bone_keyframes"
    bl_label = "Copy Bone Keyframes"

    axis: bpy.props.StringProperty(name="Axis")
    use_secondary_mapping: bpy.props.BoolProperty(name="Use Secondary Mapping", default=False)

    def execute(self, context):
        # Get the selected bones
        obj = context.object
        if obj is None or obj.type != 'ARMATURE':
            self.report({'ERROR'}, "Active object is not an armature.")
            return {'CANCELLED'}

        selected_bones = context.selected_pose_bones
        if len(selected_bones) != 2:
            self.report({'ERROR'}, "Select exactly two bones.")
            return {'CANCELLED'}

        active_bone = context.active_pose_bone
        if active_bone not in selected_bones:
            self.report({'ERROR'}, "Active bone must be one of the selected bones.")
            return {'CANCELLED'}

        # Determine source and target bones
        source_bone = selected_bones[0] if selected_bones[1] == active_bone else selected_bones[1]
        target_bone = active_bone

        # Get axis mapping from the UI
        axis_mapping = {
            'X+': (0, 1), 'X-': (0, -1), 'Y+': (1, 1), 'Y-': (1, -1), 'Z+': (2, 1), 'Z-': (2, -1)
        }

        if self.use_secondary_mapping:
            source_axes = [
                context.scene.secondary_x_axis,
                context.scene.secondary_y_axis,
                context.scene.secondary_z_axis
            ]
            replace_all = context.scene.secondary_replace_all_keyframes
        else:
            source_axes = [
                context.scene.source_x_axis,
                context.scene.source_y_axis,
                context.scene.source_z_axis
            ]
            replace_all = context.scene.replace_all_keyframes

        # Copy keyframes with remapping
        action = obj.animation_data.action
        if action is None:
            self.report({'ERROR'}, "No animation data found.")
            return {'CANCELLED'}

        for fcurve in action.fcurves:
            # Only process location keyframes
            if not fcurve.data_path.startswith(f'pose.bones["{source_bone.name}"].location'):
                continue

            # Extract the property and axis index
            property_name = fcurve.data_path.split('.')[-1]
            source_axis_index = fcurve.array_index

            # Ensure the source_axis_index is within bounds
            if source_axis_index < 0 or source_axis_index >= len(source_axes):
                self.report({'WARNING'}, f"Skipping unexpected axis index {source_axis_index}.")
                continue

            # Map the source axis to the target axis
            target_axis = source_axes[source_axis_index]
            if target_axis not in axis_mapping:
                self.report({'WARNING'}, f"Invalid axis mapping: {target_axis}.")
                continue

            target_axis_index, scale = axis_mapping[target_axis]

            # Debugging: Log the mapping
            self.report({'INFO'}, f"Mapping source axis {source_axis_index} ({target_axis}) to target axis index {target_axis_index} with scale {scale}.")

            # Create or find the corresponding FCurve for the target bone
            target_path = f'pose.bones["{target_bone.name}"].{property_name}'
            target_fcurve = next((fc for fc in action.fcurves if fc.data_path == target_path and fc.array_index == target_axis_index), None)
            if target_fcurve is None:
                target_fcurve = action.fcurves.new(data_path=target_path, index=target_axis_index)

            # Replace all keyframes if the option is enabled
            if replace_all:
                target_fcurve.keyframe_points.clear()

            # Copy keyframe points if they exist
            if not fcurve.keyframe_points:
                self.report({'WARNING'}, f"No keyframe data found for axis index {source_axis_index}. Skipping.")
                continue

            for keyframe in fcurve.keyframe_points:
                scaled_value = keyframe.co[1] * scale
                self.report({'INFO'}, f"Source keyframe at frame {keyframe.co[0]} with value {keyframe.co[1]} scaled to {scaled_value}.")
                target_fcurve.keyframe_points.insert(keyframe.co[0], scaled_value)
                self.report({'INFO'}, f"Target keyframe at frame {keyframe.co[0]} set to value {scaled_value} on axis index {target_axis_index}.")

        self.report({'INFO'}, f"Keyframes for axis {self.axis} copied successfully!")
        return {'FINISHED'}

class CopyAllAxesKeyframesOperator(bpy.types.Operator):
    """Copy keyframes for all axes from one bone to another."""
    bl_idname = "object.copy_all_axes_keyframes"
    bl_label = "Copy All Axes Keyframes"

    use_secondary_mapping: bpy.props.BoolProperty(name="Use Secondary Mapping", default=False)

    def execute(self, context):
        # Get the selected bones
        obj = context.object
        if obj is None or obj.type != 'ARMATURE':
            self.report({'ERROR'}, "Active object is not an armature.")
            return {'CANCELLED'}

        selected_bones = context.selected_pose_bones
        if len(selected_bones) != 2:
            self.report({'ERROR'}, "Select exactly two bones.")
            return {'CANCELLED'}

        active_bone = context.active_pose_bone
        if active_bone not in selected_bones:
            self.report({'ERROR'}, "Active bone must be one of the selected bones.")
            return {'CANCELLED'}

        # Determine source and target bones
        source_bone = selected_bones[0] if selected_bones[1] == active_bone else selected_bones[1]
        target_bone = active_bone

        # Copy keyframes for all axes
        for axis in ['X', 'Y', 'Z']:
            bpy.ops.object.copy_bone_keyframes(axis=axis, use_secondary_mapping=self.use_secondary_mapping)

        self.report({'INFO'}, "Keyframes for all axes copied successfully!")
        return {'FINISHED'}

class CopyBoneKeyframesPanel(bpy.types.Panel):
    """Creates a Panel in the 3D Viewport for axis mapping."""
    bl_label = "Copy Bone Keyframes"
    bl_idname = "VIEW3D_PT_copy_bone_keyframes"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Tool'

    def draw(self, context):
        layout = self.layout

        # Primary Mapping Section
        layout.label(text="Primary Mapping:")
        row = layout.row()
        row.prop(context.scene, "primary_mapper", text="Primary Mapper")
        row.prop(context.scene, "primary_suffix", text="Suffix")

        row = layout.row()
        row.label(text="Source X+ > Target:")
        row.prop(context.scene, "source_x_axis", text="")
        row = layout.row()
        row.label(text="Source Y+ > Target:")
        row.prop(context.scene, "source_y_axis", text="")
        row = layout.row()
        row.label(text="Source Z+ > Target:")
        row.prop(context.scene, "source_z_axis", text="")
        layout.prop(context.scene, "replace_all_keyframes", text="Replace All Keyframes")

        row = layout.row()
        row.operator("object.copy_bone_keyframes", text="Copy X Axis").axis = "X"
        row.operator("object.copy_bone_keyframes", text="Copy Y Axis").axis = "Y"
        row.operator("object.copy_bone_keyframes", text="Copy Z Axis").axis = "Z"

        # Ensure primary 'Copy All Axes' uses primary mapping
        layout.operator("object.copy_all_axes_keyframes", text="Copy All Axes").use_secondary_mapping = False

        # Secondary Mapping Section
        layout.label(text="Secondary Mapping:")
        row = layout.row()
        row.prop(context.scene, "secondary_mapper", text="Secondary Mapper")
        row.prop(context.scene, "secondary_suffix", text="Suffix")

        row = layout.row()
        row.label(text="Source X+ > Target:")
        row.prop(context.scene, "secondary_x_axis", text="")
        row = layout.row()
        row.label(text="Source Y+ > Target:")
        row.prop(context.scene, "secondary_y_axis", text="")
        row = layout.row()
        row.label(text="Source Z+ > Target:")
        row.prop(context.scene, "secondary_z_axis", text="")
        layout.prop(context.scene, "secondary_replace_all_keyframes", text="Replace All Keyframes")

        # Ensure secondary buttons apply secondary mapping
        row = layout.row()
        row.operator("object.copy_bone_keyframes", text="Copy X Axis").use_secondary_mapping = True
        row.operator("object.copy_bone_keyframes", text="Copy Y Axis").use_secondary_mapping = True
        row.operator("object.copy_bone_keyframes", text="Copy Z Axis").use_secondary_mapping = True

        # Ensure 'Copy All Axes' uses secondary mapping
        layout.operator("object.copy_all_axes_keyframes", text="Copy All Axes").use_secondary_mapping = True

        # Remap All Button
        layout.operator("object.remap_all_bones", text="Remap All")

class RemapAllBonesOperator(bpy.types.Operator):
    """Remap all bones based on mapper and suffix rules."""
    bl_idname = "object.remap_all_bones"
    bl_label = "Remap All Bones"

    def execute(self, context):
        obj = context.object
        if obj is None or obj.type != 'ARMATURE':
            self.report({'ERROR'}, "Active object is not an armature.")
            return {'CANCELLED'}

        selected_bones = context.selected_pose_bones
        if not selected_bones:
            self.report({'ERROR'}, "No bones selected.")
            return {'CANCELLED'}

        # Retrieve mapper and suffix keywords
        primary_mapper = context.scene.primary_mapper
        primary_suffix = context.scene.primary_suffix
        secondary_mapper = context.scene.secondary_mapper
        secondary_suffix = context.scene.secondary_suffix

        # Pair bones based on suffix exclusion
        bone_pairs = []
        for bone in selected_bones:
            if bone.name.endswith(primary_suffix):
                base_name = bone.name[:-len(primary_suffix)]
                source_bone = obj.pose.bones.get(base_name)
                if source_bone and source_bone in selected_bones:
                    bone_pairs.append((source_bone, bone))

        # Debugging: Print paired bones
        if not bone_pairs:
            self.report({'WARNING'}, "No valid bone pairs found.")
            return {'CANCELLED'}

        """
        for source_bone, target_bone in bone_pairs:
            print(f"Pairing source: {source_bone.name} -> target: {target_bone.name}")
        """
        # Copy keyframes for each pair
        """
        action = obj.animation_data.action if obj.animation_data else None
        if action is None:
            self.report({'ERROR'}, "No animation data found.")
            return {'CANCELLED'}
        """
        for source_bone, target_bone in bone_pairs:
            """
            for fcurve in action.fcurves:
                if not fcurve.data_path.startswith(f'pose.bones["{source_bone.name}"].location'):
                    continue

                property_name = fcurve.data_path.split('.')[-1]
                source_axis_index = fcurve.array_index

                target_path = f'pose.bones["{target_bone.name}"].{property_name}'
                target_fcurve = next((fc for fc in action.fcurves if fc.data_path == target_path and fc.array_index == source_axis_index), None)
                if target_fcurve is None:
                    try:
                        target_fcurve = action.fcurves.new(data_path=target_path, index=source_axis_index)
                    except Exception as e:
                        self.report({'WARNING'}, f"Failed to create FCurve for {target_path}: {e}")
                        continue

                try:
                    target_fcurve.keyframe_points.clear()
                except Exception as e:
                    self.report({'WARNING'}, f"Failed to clear keyframes for {target_path}: {e}")
                    continue

                if not fcurve.keyframe_points:
                    self.report({'WARNING'}, f"No keyframe data found for {fcurve.data_path}. Skipping.")
                    continue

                for keyframe in fcurve.keyframe_points:
                    try:
                        target_fcurve.keyframe_points.insert(keyframe.co[0], keyframe.co[1])
                    except Exception as e:
                        self.report({'WARNING'}, f"Failed to insert keyframe at frame {keyframe.co[0]} for {target_path}: {e}")
                        continue
"""
            # Get axis mapping from the UI
            axis_mapping = {
                'X+': (0, 1), 'X-': (0, -1), 'Y+': (1, 1), 'Y-': (1, -1), 'Z+': (2, 1), 'Z-': (2, -1)
            }

            if secondary_mapper in source_bone.name:
                source_axes = [
                    context.scene.secondary_x_axis,
                    context.scene.secondary_y_axis,
                    context.scene.secondary_z_axis
                ]
                replace_all = context.scene.secondary_replace_all_keyframes
            else:
                source_axes = [
                    context.scene.source_x_axis,
                    context.scene.source_y_axis,
                    context.scene.source_z_axis
                ]
                replace_all = context.scene.replace_all_keyframes

            # Copy keyframes with remapping
            action = obj.animation_data.action
            if action is None:
                self.report({'ERROR'}, "No animation data found.")
                return {'CANCELLED'}

            for fcurve in action.fcurves:
                # Only process location keyframes
                if not fcurve.data_path.startswith(f'pose.bones["{source_bone.name}"].location'):
                    continue

                # Extract the property and axis index
                property_name = fcurve.data_path.split('.')[-1]
                source_axis_index = fcurve.array_index

                # Ensure the source_axis_index is within bounds
                if source_axis_index < 0 or source_axis_index >= len(source_axes):
                    self.report({'WARNING'}, f"Skipping unexpected axis index {source_axis_index}.")
                    continue

                # Map the source axis to the target axis
                target_axis = source_axes[source_axis_index]
                if target_axis not in axis_mapping:
                    self.report({'WARNING'}, f"Invalid axis mapping: {target_axis}.")
                    continue

                target_axis_index, scale = axis_mapping[target_axis]

                # Debugging: Log the mapping
                self.report({'INFO'}, f"Mapping source axis {source_axis_index} ({target_axis}) to target axis index {target_axis_index} with scale {scale}.")

                # Create or find the corresponding FCurve for the target bone
                target_path = f'pose.bones["{target_bone.name}"].{property_name}'
                target_fcurve = next((fc for fc in action.fcurves if fc.data_path == target_path and fc.array_index == target_axis_index), None)
                if target_fcurve is None:
                    target_fcurve = action.fcurves.new(data_path=target_path, index=target_axis_index)

                # Replace all keyframes if the option is enabled
                if replace_all:
                    target_fcurve.keyframe_points.clear()

                # Copy keyframe points if they exist
                if not fcurve.keyframe_points:
                    self.report({'WARNING'}, f"No keyframe data found for axis index {source_axis_index}. Skipping.")
                    continue

                for keyframe in fcurve.keyframe_points:
                    scaled_value = keyframe.co[1] * scale
                    self.report({'INFO'}, f"Source keyframe at frame {keyframe.co[0]} with value {keyframe.co[1]} scaled to {scaled_value}.")
                    target_fcurve.keyframe_points.insert(keyframe.co[0], scaled_value)
                    self.report({'INFO'}, f"Target keyframe at frame {keyframe.co[0]} set to value {scaled_value} on axis index {target_axis_index}.")
        self.report({'INFO'}, "Remap All completed successfully.")
        return {'FINISHED'}

# Register and Unregister
classes = [
    CopyBoneKeyframesOperator,
    CopyAllAxesKeyframesOperator,
    CopyBoneKeyframesPanel,
    RemapAllBonesOperator,
]

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.source_x_axis = bpy.props.EnumProperty(
        name="Source X+",
        description="Map source X+ axis to target axis",
        items=[
            ('X+', "X+", ""),
            ('X-', "X-", ""),
            ('Y+', "Y+", ""),
            ('Y-', "Y-", ""),
            ('Z+', "Z+", ""),
            ('Z-', "Z-", ""),
        ],
        default='X+',  # Set the default value here
    )
    bpy.types.Scene.source_y_axis = bpy.props.EnumProperty(
        name="Source Y+",
        description="Map source Y+ axis to target axis",
        items=[
            ('X+', "X+", ""),
            ('X-', "X-", ""),
            ('Y+', "Y+", ""),
            ('Y-', "Y-", ""),
            ('Z+', "Z+", ""),
            ('Z-', "Z-", ""),
        ],
        default='Y+',  # Set the default value here
    )
    bpy.types.Scene.source_z_axis = bpy.props.EnumProperty(
        name="Source Z+",
        description="Map source Z+ axis to target axis",
        items=[
            ('X+', "X+", ""),
            ('X-', "X-", ""),
            ('Y+', "Y+", ""),
            ('Y-', "Y-", ""),
            ('Z+', "Z+", ""),
            ('Z-', "Z-", ""),
        ],
        default='Z+',  # Set the default value here
    )
    bpy.types.Scene.replace_all_keyframes = bpy.props.BoolProperty(
        name="Replace All Keyframes",
        description="Replace all keyframes in the target before copying",
        default=False,
    )
    bpy.types.Scene.secondary_x_axis = bpy.props.EnumProperty(
        name="Secondary X+",
        description="Map secondary X+ axis to target axis",
        items=[
            ('X+', "X+", ""),
            ('X-', "X-", ""),
            ('Y+', "Y+", ""),
            ('Y-', "Y-", ""),
            ('Z+', "Z+", ""),
            ('Z-', "Z-", ""),
        ],
        default='X+',  # Set the default value here
    )
    bpy.types.Scene.secondary_y_axis = bpy.props.EnumProperty(
        name="Secondary Y+",
        description="Map secondary Y+ axis to target axis",
        items=[
            ('X+', "X+", ""),
            ('X-', "X-", ""),
            ('Y+', "Y+", ""),
            ('Y-', "Y-", ""),
            ('Z+', "Z+", ""),
            ('Z-', "Z-", ""),
        ],
        default='Y+',  # Set the default value here
    )
    bpy.types.Scene.secondary_z_axis = bpy.props.EnumProperty(
        name="Secondary Z+",
        description="Map secondary Z+ axis to target axis",
        items=[
            ('X+', "X+", ""),
            ('X-', "X-", ""),
            ('Y+', "Y+", ""),
            ('Y-', "Y-", ""),
            ('Z+', "Z+", ""),
            ('Z-', "Z-", ""),
        ],
        default='Z+',  # Set the default value here
    )
    bpy.types.Scene.secondary_replace_all_keyframes = bpy.props.BoolProperty(
        name="Replace All Keyframes",
        description="Replace all keyframes in the target before copying for secondary mapping",
        default=False,
    )
    bpy.types.Scene.primary_mapper = bpy.props.StringProperty(
        name="Primary Mapper",
        description="Primary mapper for axis mapping",
        default="",
    )
    bpy.types.Scene.primary_suffix = bpy.props.StringProperty(
        name="Suffix",
        description="Suffix to add to target bone names",
        default="",
    )
    bpy.types.Scene.secondary_mapper = bpy.props.StringProperty(
        name="Secondary Mapper",
        description="Secondary mapper for axis mapping",
        default="",
    )
    bpy.types.Scene.secondary_suffix = bpy.props.StringProperty(
        name="Suffix",
        description="Suffix to add to target bone names for secondary mapping",
        default="",
    )

def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
    del bpy.types.Scene.source_x_axis
    del bpy.types.Scene.source_y_axis
    del bpy.types.Scene.source_z_axis
    del bpy.types.Scene.replace_all_keyframes
    del bpy.types.Scene.secondary_x_axis
    del bpy.types.Scene.secondary_y_axis
    del bpy.types.Scene.secondary_z_axis
    del bpy.types.Scene.secondary_replace_all_keyframes
    del bpy.types.Scene.primary_mapper
    del bpy.types.Scene.primary_suffix
    del bpy.types.Scene.secondary_mapper
    del bpy.types.Scene.secondary_suffix

if __name__ == "__main__":
    register()