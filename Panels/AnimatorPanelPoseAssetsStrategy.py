import bpy

from ..lipsync_types import BpyObject
from .AnimatorPanelMixin import AnimatorPanelMixin
from ..Core.phoneme_to_viseme import viseme_items_mpeg4_v2 as viseme_items
from ..lipsync_types import BpyContext, BpyUILayout

def pose_icon_id(action) -> int:
    """Thumbnail of a pose asset (the Asset Browser picture), or 0 if it has none."""
    if action is None:
        return 0
    preview = getattr(action, "preview", None)
    if preview is None:
        return 0
    try:
        return preview.icon_id
    except (AttributeError, RuntimeError):
        return 0


# Plain-English sounds for each viseme code, shown next to the code in the panel
VISEME_SOUND_HINTS = {
    "sil": "(rest)",
    "PP": "(m b p)",
    "FF": "(f v)",
    "TH": "(th)",
    "DD": "(d t)",
    "kk": "(k g)",
    "CH": "(ch j sh)",
    "SS": "(s z)",
    "nn": "(n l)",
    "RR": "(r)",
    "aa": "(a)",
    "E": "(e)",
    "ih": "(i)",
    "oh": "(o)",
    "ou": "(oo w)",
    "UNK": "(other)",
}


class AnimatorPanelPoseAssetsStrategy(AnimatorPanelMixin):
    def __init__(self, obj: BpyObject):
        super().__init__(obj)
        if not isinstance(obj.data, bpy.types.Mesh):
            return

    def draw_animator_section(self, context: BpyContext, layout: BpyUILayout):
        panel_header, panel_body = layout.panel(
            "vpg_lipsync_animator_dropdown", default_closed=True
        )

        panel_header.label(text="Rig Settings")

        if panel_body is not None:
            row = panel_body.row()
            row.label(text="Rig Type")

            row = panel_body.row(align=True)
            row.prop(self.props, "lip_sync_2d_rig_type_basic", toggle=True)
            row.prop(self.props, "lip_sync_2d_rig_type_advanced", toggle=True)
            panel_body.separator(factor=1)

    def draw_animation_section(self, context: BpyContext, layout: BpyUILayout):
        panel_header, panel_body = layout.panel(
            "cgp_lipsync_animation_dropdown", default_closed=False
        )
        panel_header.label(text="Animation Settings")
        if panel_body is not None:
            row = panel_body.row()
            row.label(text="Motion:")
            row = panel_body.row()
            row.prop(self.props, "lip_sync_2d_close_motion_duration")

            self.draw_thresholds(self.props, panel_body)

            row = panel_body.row()
            row.prop(self.props, "lip_sync_2d_prioritize_accuracy", toggle=True)

    def draw_visemes_section(self, context: BpyContext, layout: BpyUILayout):
        panel_head, panel_body = layout.panel(
            "cgp_lipsync_viseme_dropdown", default_closed=False
        )
        panel_head.label(text="Mouth Poses")
        if panel_body is not None:
            row = panel_body.row()
            row.scale_y = 1.4
            row.operator("lipsync2d.auto_fill_poses", icon="SHADERFX")

            row = panel_body.row(align=True)
            row.label(text="Sound")
            row.label(text="Mouth Pose")

            visemes = viseme_items(None, None)

            for i, viseme in enumerate(visemes):
                lang_code = list(viseme)[0]
                hint = VISEME_SOUND_HINTS.get(lang_code, "")
                pose = getattr(self.props, f"lip_sync_2d_viseme_pose_{lang_code}", None)

                row = panel_body.row(align=True)
                split = row.split(factor=0.42, align=True)
                split.label(text=f"{lang_code}  {hint}")

                right = split.row(align=True)
                icon_id = pose_icon_id(pose)
                if icon_id:
                    right.label(text="", icon_value=icon_id)
                else:
                    right.label(text="", icon="BLANK1")
                right.prop(self.props, f"lip_sync_2d_viseme_pose_{lang_code}", text="")

                play = right.row(align=True)
                play.enabled = pose is not None
                op = play.operator("lipsync2d.preview_pose", text="", icon="PLAY")
                op.viseme = lang_code  # type: ignore

            row = panel_body.row()
            row.operator("lipsync2d.preview_restore", icon="LOOP_BACK")

    def draw_thresholds(self, props, layout):
        row = layout.row()
        row.label(text="Thresholds:")
        data_list = ["lip_sync_2d_in_between_threshold", "lip_sync_2d_sil_threshold"]
        row = layout.row()
        for data in data_list:
            row.prop(props, data)

    def draw_baking_section(self, context: BpyContext, layout: BpyUILayout):
        if not self.is_model_installed:
            new_row = layout.row()
            new_row.label(
                text="Select a Language Model before Analyzing audio",
                icon="WARNING_LARGE",
            )

        new_row = layout.row()
        new_row.operator(
            "sound.cgp_analyze_audio", text="Bake audio", icon="SCRIPTPLUGINS"
        )
        new_row.enabled = self.is_model_installed

    def draw_edit_section(self, context: BpyContext, layout: BpyUILayout):

        row = layout.row()
        row.label(text="Pose Assets:")
        box = layout.box()
        row = box.row(align=True)
        row.operator("lipsync2d.refresh_pose_assets")

        row = layout.row()
        row.label(text="Clean Up:")

        box = layout.box()
        row = box.row()
        row.label(text="Animation:")
        row = box.row()
        operator = row.operator(
            "object.remove_lip_sync_animations", text="Remove Pose Animation"
        )
        operator.animation_type = "POSEASSETS"  # type: ignore
        row = box.row()
        operator = row.operator(
            "object.remove_lip_sync_animations", text="Remove all Animations"
        )
        operator.animation_type = "ALL"  # type: ignore

        box = layout.box()
        row = box.row()
        row.prop(self.props, "lip_sync_2d_remove_animation_data")
        row = box.row()
        row.alert = True
        row.operator("object.remove_lip_sync_from_selection")
