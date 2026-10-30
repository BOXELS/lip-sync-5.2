"""
Auto-Fill Mouth Poses: match pose assets to viseme slots by name.

Works with common mouth-chart naming, e.g. "Mm_Mouth", "F-V_Mouth", "A-E-2-Mouth",
"Default_Mouth", "MBP", "FV", "AI", "WQ", "Rest", "Ooo". Words like "mouth" or "pose"
and version numbers ("-2", ".001") are ignored when matching.
"""

import re

import bpy

from ..Core.phoneme_to_viseme import viseme_items_mpeg4_v2

# Ignored words when reading a pose name
FILLER_WORDS = {"mouth", "mouths", "mth", "pose", "poses", "viseme", "phoneme", "lips", "lip", "shape"}

# For each viseme slot, pose-name keys to look for, best match first.
# A key is the cleaned pose name, e.g. "F-V_Mouth" -> "f-v".
VISEME_CANDIDATES: dict[str, list[str]] = {
    "sil": ["rest", "default", "neutral", "closed", "sil", "silence", "idle", "blank"],
    "PP": ["mbp", "m-b-p", "bmp", "pp", "mm", "m", "p", "b"],
    "FF": ["f-v", "fv", "ff", "f", "v"],
    "TH": ["th", "l-th", "th-l", "l"],
    "DD": ["d-t", "dt", "dd", "d", "t"],
    "kk": ["k-g", "kg", "kk", "k", "g", "c"],
    "CH": ["ch-j", "ch", "sh-ch", "sh", "j"],
    "SS": ["s-z", "s-x", "ss", "s", "z"],
    "nn": ["n-l", "nn", "n"],
    "RR": ["r-ar", "rr", "r", "ar", "er"],
    "aa": ["a-i", "ai", "a-e", "aa", "a", "ah"],
    "E": ["ee", "e", "eh", "e-i"],
    "ih": ["ih", "i", "ee-i", "ee"],
    "oh": ["oh", "o"],
    "ou": ["w-q", "wq", "ooo", "oo", "ou", "w", "u-w", "q", "u"],
    "UNK": ["uh", "u", "etc", "a-e", "a", "ai", "default", "rest"],
}


def clean_pose_name(name: str) -> str:
    """'A-E-2-Mouth' -> 'a-e', 'Ooo-2_Mouth.001' -> 'ooo', 'Rest Pose' -> 'rest'."""
    name = re.sub(r"\.\d{3}$", "", name.lower())
    tokens = [t for t in re.split(r"[\s\-_.]+", name) if t]
    tokens = [t for t in tokens if not t.isdigit() and t not in FILLER_WORDS]
    return "-".join(tokens)


def is_mouth_pose(action: "bpy.types.Action") -> bool:
    catalog = action.asset_data.catalog_simple_name.lower() if action.asset_data else ""
    return "mouth" in action.name.lower() or "mouth" in catalog or "lip" in catalog


def find_pose_assets() -> dict[str, "bpy.types.Action"]:
    """Cleaned name -> pose asset action. Mouth poses win over others with the same name."""
    found: dict[str, bpy.types.Action] = {}
    for action in sorted(bpy.data.actions, key=lambda a: not is_mouth_pose(a)):
        if action.asset_data is None:
            continue
        key = clean_pose_name(action.name)
        if key and key not in found:
            found[key] = action
    return found


def auto_fill(props, overwrite: bool = False) -> tuple[list[str], list[str]]:
    """Fill viseme pose slots. Returns (filled, still_empty) viseme ids."""
    poses = find_pose_assets()
    filled, empty = [], []

    for enum_id, _, _ in viseme_items_mpeg4_v2(None, None):
        prop = f"lip_sync_2d_viseme_pose_{enum_id}"
        if not overwrite and getattr(props, prop) is not None:
            continue
        match = next((poses[k] for k in VISEME_CANDIDATES.get(enum_id, []) if k in poses), None)
        if match is None:
            empty.append(enum_id)
            continue
        setattr(props, prop, match)
        filled.append(enum_id)

    return filled, empty


class LIPSYNC2D_OT_AutoFillPoses(bpy.types.Operator):
    bl_idname = "lipsync2d.auto_fill_poses"
    bl_label = "Auto-Fill Mouth Poses"
    bl_description = (
        "Fill the mouth slots from your pose assets by name.\n"
        "Works with names like Mm, F-V, A-E, O, Ooo, Default/Rest.\n"
        "You can change any slot afterwards"
    )
    bl_options = {"REGISTER", "UNDO"}

    overwrite: bpy.props.BoolProperty(  # type: ignore
        name="Replace filled slots",
        description="Also replace slots you already set",
        default=True,
    )

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return obj is not None and obj.type == "ARMATURE" and hasattr(obj, "lipsync2d_props")

    def execute(self, context):
        props = context.active_object.lipsync2d_props  # type: ignore

        if not find_pose_assets():
            self.report(
                {"WARNING"},
                "No pose assets in this file. Try 'Refresh Pose Assets' under Edit, or mark your mouth poses as assets.",
            )
            return {"CANCELLED"}

        filled, empty = auto_fill(props, overwrite=self.overwrite)

        if empty:
            self.report(
                {"WARNING"},
                f"Filled {len(filled)} mouth slots. Pick these by hand: {', '.join(empty)}",
            )
        else:
            self.report({"INFO"}, f"Filled {len(filled)} mouth slots")
        return {"FINISHED"}
