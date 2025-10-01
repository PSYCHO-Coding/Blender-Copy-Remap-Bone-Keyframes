# Blender Plugin: Copy Bone Keyframes with Axis Mapping
# This plugin allows users to copy keyframes from one bone to another with axis remapping.

bl_info = {
    "name": "Psycho's Helpers",
    "author": "Nesha aka TwitchingPsycho",
    "version": (1, 0),
    "blender": (3, 0, 0),
    "location": "3D View > Tool Shelf",
    "description": "Located in the 'N' menus, flip keyframe fcurve values or copy keyframes from one bone to another with axis remapping. For now only location axis remapping is supported!",
    "category": "Animation, Simple Helpers",
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
    bl_category = 'Psycho''s Helpers'

    def draw(self, context):
        layout = self.layout

        # Primary Mapping Section
        layout.label(text="Primary Mapping:")
        row = layout.row()
        row.label(text="Source Mapper:")
        row.prop(context.scene, "primary_mapper", text="")
        #row.prop(context.scene, "primary_suffix", text="Suffix")

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
        row.label(text="Source Mapper:")
        row.prop(context.scene, "secondary_mapper", text="")
        #row.prop(context.scene, "secondary_suffix", text="Suffix")

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

        # Duplicate/Target suffix
        row = layout.row()
        layout.prop(context.scene, "primary_suffix", text="Target Suffix")

        # Remap All Button
        row = layout.row()
        row = layout.row()
        layout.operator("object.remap_all_bones", text="Remap All")

class SwapAndFlipKeyframesPanel(bpy.types.Panel):
    """Creates a Panel in the 3D Viewport for axis mapping."""
    bl_label = "Swap And Flip Keyframes"
    bl_idname = "VIEW3D_PT_swap_and_flip_keyframes"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    #bl_category = 'Psycho''s Helpers'
    bl_category = 'Item'

    """
    def draw(self, context):
        layout = self.layout
        row = layout.row()
        row.operator("object.XXX", text="Flip X Loc")
        row.operator("object.XXX", text="Flip X Rot")
        row = layout.row()
        row.operator("object.XXX", text="Flip Y Loc")
        row.operator("object.XXX", text="Flip Y Rot")
        row = layout.row()
        row.operator("object.XXX", text="Flip Z Loc")
        row.operator("object.XXX", text="Flip Z Rot")
    """
    def draw(self, context):
        layout = self.layout
        row = layout.row()
        for axis, label in enumerate("XYZ"):
            row = layout.row()
            op = row.operator("object.flip_keyframe_axis", text=f"Flip {label} Loc")
            op.property = 'location'
            op.axis = axis

            op = row.operator("object.flip_keyframe_axis", text=f"Flip {label} Rot")
            op.property = 'rotation_euler'
            op.axis = axis

            op = row.operator("object.flip_keyframe_axis", text=f"Flip {label} Scale")
            op.property = 'scale'
            op.axis = axis

        row = layout.row()
        row = layout.row()
        layout.operator("object.swap_keyframes", text="Swap Keyframes")

class FlipKeyframeAxisOperator(bpy.types.Operator):
    """Flip Keyframe Curve Values for a Specific Axis and Property"""
    bl_idname = "object.flip_keyframe_axis"
    bl_label = "Flip Keyframe Axis"
    
    property: bpy.props.StringProperty()  # 'location' or 'rotation_euler'
    axis: bpy.props.IntProperty()         # 0=X, 1=Y, 2=Z

    def execute(self, context):
        obj = context.object
        if not obj or obj.type != 'ARMATURE':
            self.report({'ERROR'}, "Active object is not an armature.")
            return {'CANCELLED'}

        pose_bone = context.active_pose_bone
        if not pose_bone:
            self.report({'ERROR'}, "No active pose bone.")
            return {'CANCELLED'}

        action = obj.animation_data.action if obj.animation_data else None
        if not action:
            self.report({'ERROR'}, "No action found on this object.")
            return {'CANCELLED'}

        data_path = f'pose.bones["{pose_bone.name}"].{self.property}'
        
        fcurve = next((fc for fc in action.fcurves 
                       if fc.data_path == data_path and fc.array_index == self.axis), None)

        if not fcurve:
            self.report({'WARNING'}, f"No keyframes found for {self.property} axis {self.axis}.")
            return {'CANCELLED'}

        for kp in fcurve.keyframe_points:
            kp.co[1] *= -1  # Flip the value
            kp.handle_left[1] *= -1
            kp.handle_right[1] *= -1

        fcurve.update()
        self.report({'INFO'}, f"Flipped {self.property} axis {self.axis} keyframes for {pose_bone.name}")
        return {'FINISHED'}

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
        #secondary_suffix = context.scene.secondary_suffix
        secondary_suffix = primary_suffix

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

# Add to right-click context menu in Pose Mode
def pose_context_menu(self, context):
    if context.mode == 'POSE' and len(context.selected_pose_bones) == 2:
        self.layout.separator()
        self.layout.operator("object.swap_keyframes", icon='ARROW_LEFTRIGHT')

def copy_keyframe_data(kp):
    return {
        'co': kp.co[:],
        'handle_left': kp.handle_left[:],
        'handle_right': kp.handle_right[:],
        'interpolation': kp.interpolation,
        'easing': kp.easing,
        'handle_left_type': kp.handle_left_type,
        'handle_right_type': kp.handle_right_type,
    }

def apply_keyframe_data(kp, data):
    kp.handle_left = data['handle_left']
    kp.handle_right = data['handle_right']
    kp.interpolation = data['interpolation']
    kp.easing = data['easing']
    kp.handle_left_type = data['handle_left_type']
    kp.handle_right_type = data['handle_right_type']

class SwapKeyframesOperator(bpy.types.Operator):
    """Swap keyframes between two selected pose bones"""
    bl_idname = "object.swap_keyframes"
    bl_label = "Swap Keyframes Between Two Bones"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        obj = context.object
        if not obj or obj.type != 'ARMATURE':
            self.report({'ERROR'}, "Active object is not an armature.")
            return {'CANCELLED'}

        bones = context.selected_pose_bones
        if not bones or len(bones) != 2:
            self.report({'ERROR'}, "Select exactly two bones.")
            return {'CANCELLED'}

        active_bone = context.active_pose_bone
        if active_bone not in bones:
            self.report({'ERROR'}, "Active bone must be one of the selected bones.")
            return {'CANCELLED'}

        # Define bones
        source_bone = bones[0] if bones[1] == active_bone else bones[1]
        target_bone = active_bone

        # Animation check
        if not obj.animation_data or not obj.animation_data.action:
            self.report({'ERROR'}, "No animation data found.")
            return {'CANCELLED'}

        action = obj.animation_data.action

        # Store fcurves to process
        transform_properties = ['location', 'rotation_euler', 'rotation_quaternion', 'scale']

        for prop in transform_properties:
            for axis_index in range(3 if prop != 'rotation_quaternion' else 4):
                source_path = f'pose.bones["{source_bone.name}"].{prop}'
                target_path = f'pose.bones["{target_bone.name}"].{prop}'

                source_fcurve = next((fc for fc in action.fcurves
                                      if fc.data_path == source_path and fc.array_index == axis_index), None)
                target_fcurve = next((fc for fc in action.fcurves
                                      if fc.data_path == target_path and fc.array_index == axis_index), None)

                # Store keyframes
                source_data = [copy_keyframe_data(kp) for kp in source_fcurve.keyframe_points] if source_fcurve else []
                target_data = [copy_keyframe_data(kp) for kp in target_fcurve.keyframe_points] if target_fcurve else []

                # Ensure fcurves exist
                """
                if not source_fcurve:
                    source_fcurve = action.fcurves.new(data_path=source_path, index=axis_index)
                else:
                    source_fcurve.keyframe_points.clear()

                if not target_fcurve:
                    target_fcurve = action.fcurves.new(data_path=target_path, index=axis_index)
                else:
                    target_fcurve.keyframe_points.clear()

                # Apply swapped keyframes
                for data in source_data:
                    kp = target_fcurve.keyframe_points.insert(data['co'][0], data['co'][1])
                    apply_keyframe_data(kp, data)

                for data in target_data:
                    kp = source_fcurve.keyframe_points.insert(data['co'][0], data['co'][1])
                    apply_keyframe_data(kp, data)
                """

                if not source_fcurve or not target_fcurve:
                    # Skip this axis/property entirely if either FCurve is missing
                    continue

                # Copy keyframes before clearing
                source_data = [copy_keyframe_data(kp) for kp in source_fcurve.keyframe_points]
                target_data = [copy_keyframe_data(kp) for kp in target_fcurve.keyframe_points]

                # Clear and swap
                source_fcurve.keyframe_points.clear()
                target_fcurve.keyframe_points.clear()

                for data in source_data:
                    kp = target_fcurve.keyframe_points.insert(data['co'][0], data['co'][1])
                    apply_keyframe_data(kp, data)

                for data in target_data:
                    kp = source_fcurve.keyframe_points.insert(data['co'][0], data['co'][1])
                    apply_keyframe_data(kp, data)

        self.report({'INFO'}, f"Swapped keyframes between '{source_bone.name}' and '{target_bone.name}'.")
        return {'FINISHED'}

# Register and Unregister
classes = [
    CopyBoneKeyframesOperator,
    CopyAllAxesKeyframesOperator,
    CopyBoneKeyframesPanel,
    SwapAndFlipKeyframesPanel,
    FlipKeyframeAxisOperator,
    RemapAllBonesOperator,
    SwapKeyframesOperator,
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
        default=True,
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
        default=True,
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
    bpy.types.VIEW3D_MT_pose_context_menu.append(pose_context_menu)

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
    bpy.types.VIEW3D_MT_pose_context_menu.remove(pose_context_menu)

if __name__ == "__main__":
    register()