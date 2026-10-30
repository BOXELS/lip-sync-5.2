"""
Mouth pose preview (Pose Library mode).

Click ▶ next to a mouth slot: the rig eases from the rest (sil) pose into that
slot's pose and holds it. "Back to Rest" puts every touched channel back exactly
as it was before the first preview. Nothing is keyframed.
"""

import time

import bpy

from ..Core.Animator.action_compat import iter_fcurves

PREVIEW_SECONDS = 0.25

# rig name -> {(data_path, index): original value}, captured before the first preview
_saved_pose: dict[str, dict[tuple[str, int], float]] = {}


# --- reading pose assets and the rig -----------------------------------------------------

def pose_values(action) -> dict[tuple[str, int], float]:
    """The pose an asset stores: first key of each F-Curve (same rule the baker uses)."""
    values = {}
    if action is None:
        return values
    for fc in iter_fcurves(action):
        if len(fc.keyframe_points):
            values[(fc.data_path, fc.array_index)] = fc.keyframe_points[0].co.y
    return values


def _split_path(data_path: str) -> tuple[str, str, bool]:
    """'pose.bones["jaw"].location' -> ('pose.bones["jaw"]', 'location', False)
    'pose.bones["jaw"]["prop"]'     -> ('pose.bones["jaw"]', 'prop', True)"""
    if data_path.endswith('"]'):
        owner, key = data_path.rsplit('["', 1)
        return owner, key[:-2], True
    owner, attr = data_path.rsplit(".", 1)
    return owner, attr, False


def get_channel(rig, data_path: str, index: int):
    try:
        owner_path, name, is_item = _split_path(data_path)
        owner = rig.path_resolve(owner_path)
        value = owner[name] if is_item else getattr(owner, name)
    except (ValueError, KeyError, AttributeError, TypeError):
        return None
    if isinstance(value, (int, float, bool)):
        return float(value)
    try:
        return float(value[index])
    except (TypeError, IndexError, KeyError):
        return None


def set_channel(rig, data_path: str, index: int, value: float) -> bool:
    try:
        owner_path, name, is_item = _split_path(data_path)
        owner = rig.path_resolve(owner_path)
        current = owner[name] if is_item else getattr(owner, name)
    except (ValueError, KeyError, AttributeError, TypeError):
        return False
    try:
        if isinstance(current, (int, float, bool)):
            cast = type(current)
            new = cast(round(value)) if cast in (int, bool) else value
            if is_item:
                owner[name] = new
            else:
                setattr(owner, name, new)
        else:
            current[index] = value  # mathutils / RNA arrays write through
        return True
    except (TypeError, IndexError, ValueError, AttributeError):
        return False


def blend_targets(rig, rest_action, target_action):
    """(path, index) -> (start, end): from the rest pose to the target pose."""
    rest = pose_values(rest_action)
    target = pose_values(target_action)
    channels = {}
    for key in set(rest) | set(target):
        current = get_channel(rig, *key)
        if current is None:
            continue  # channel doesn't exist on this rig
        start = rest.get(key, current)
        end = target.get(key, rest.get(key, current))
        channels[key] = (start, end)
    return channels


def apply_blend(rig, channels, t: float):
    t = max(0.0, min(1.0, t))
    t = t * t * (3 - 2 * t)  # ease in/out
    for (path, index), (start, end) in channels.items():
        set_channel(rig, path, index, start + (end - start) * t)


def remember_original(rig, channels):
    """Keep the pose from before the FIRST preview, so Back to Rest is exact."""
    saved = _saved_pose.setdefault(rig.name, {})
    for key in channels:
        if key not in saved:
            value = get_channel(rig, *key)
            if value is not None:
                saved[key] = value


def has_saved_pose(rig) -> bool:
    return rig is not None and bool(_saved_pose.get(rig.name))


def restore_original(rig) -> int:
    saved = _saved_pose.pop(rig.name, {})
    for (path, index), value in saved.items():
        set_channel(rig, path, index, value)
    return len(saved)


def _redraw(context):
    if context.view_layer:
        context.view_layer.update()
    for window in context.window_manager.windows:
        for area in window.screen.areas:
            if area.type == "VIEW_3D":
                area.tag_redraw()


# --- operators ------------------------------------------------------------------------------

class LIPSYNC2D_OT_PreviewPose(bpy.types.Operator):
    bl_idname = "lipsync2d.preview_pose"
    bl_label = "Preview Mouth Pose"
    bl_description = "Show this mouth shape on the character, moving from rest into it.\nNothing is keyframed. Use Back to Rest to undo"

    viseme: bpy.props.StringProperty()  # type: ignore

    _timer = None
    _start = 0.0
    _channels = None

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return obj is not None and obj.type == "ARMATURE" and hasattr(obj, "lipsync2d_props")

    def _setup(self, context):
        rig = context.active_object
        props = rig.lipsync2d_props
        target = getattr(props, f"lip_sync_2d_viseme_pose_{self.viseme}", None)
        if target is None:
            self.report({"WARNING"}, f"No mouth pose set for '{self.viseme}' yet")
            return None
        rest = props.lip_sync_2d_viseme_pose_sil
        channels = blend_targets(rig, rest, target)
        if not channels:
            self.report({"WARNING"}, f"'{target.name}' doesn't move any bones on this rig")
            return None
        remember_original(rig, channels)
        return channels

    def execute(self, context):
        # Non-interactive (scripts, redo): jump straight to the pose
        channels = self._setup(context)
        if channels is None:
            return {"CANCELLED"}
        apply_blend(context.active_object, channels, 1.0)
        _redraw(context)
        return {"FINISHED"}

    def invoke(self, context, event):
        self._channels = self._setup(context)
        if self._channels is None:
            return {"CANCELLED"}
        self._start = time.monotonic()
        apply_blend(context.active_object, self._channels, 0.0)
        self._timer = context.window_manager.event_timer_add(1 / 60, window=context.window)
        context.window_manager.modal_handler_add(self)
        return {"RUNNING_MODAL"}

    def modal(self, context, event):
        if event.type != "TIMER":
            return {"PASS_THROUGH"}
        rig = context.active_object
        t = (time.monotonic() - self._start) / PREVIEW_SECONDS
        if rig is not None:
            apply_blend(rig, self._channels, t)
            _redraw(context)
        if t >= 1.0 or rig is None:
            context.window_manager.event_timer_remove(self._timer)
            return {"FINISHED"}
        return {"RUNNING_MODAL"}


class LIPSYNC2D_OT_PreviewRestore(bpy.types.Operator):
    bl_idname = "lipsync2d.preview_restore"
    bl_label = "Back to Rest"
    bl_description = "Put the mouth back exactly how it was before previewing"

    @classmethod
    def poll(cls, context):
        return has_saved_pose(context.active_object)

    def execute(self, context):
        count = restore_original(context.active_object)
        _redraw(context)
        self.report({"INFO"}, f"Restored {count} channels")
        return {"FINISHED"}
