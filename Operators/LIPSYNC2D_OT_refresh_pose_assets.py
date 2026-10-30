import re
from pathlib import Path
from typing import Literal

import bpy


def base_name(name: str) -> str:
    """'Mm_Mouth.002' -> 'mm_mouth' so copies of the same pose count as one."""
    return re.sub(r"\.\d{3}$", "", name).lower()


def is_mouth_pose_name(name: str) -> bool:
    lowered = name.lower()
    return "mouth" in lowered or "lip" in lowered or "viseme" in lowered


class LIPSYNC2D_OT_refresh_pose_assets(bpy.types.Operator):
    bl_idname = "lipsync2d.refresh_pose_assets"
    bl_label = "Refresh Pose Assets"
    bl_description = (
        "Only use this if your mouth poses are not in the list.\n"
        "Links mouth pose assets (names containing 'Mouth' or 'Lip') from your asset libraries.\n"
        "Poses already in this file are skipped, and nothing is copied into the file"
    )
    bl_options = {"REGISTER", "UNDO"}

    def invoke(self, context, event):
        return context.window_manager.invoke_confirm(
            self,
            event,
            title="Refresh Pose Assets",
            message="Link mouth poses from your asset libraries that this file doesn't have yet?",
            confirm_text="Link Poses",
        )

    def execute(
        self, context
    ) -> set[
        Literal["RUNNING_MODAL", "CANCELLED", "FINISHED", "PASS_THROUGH", "INTERFACE"]
    ]:
        added = self.load_pose_assets_from_libraries()

        if added:
            self.report({"INFO"}, f"Linked {len(added)} new mouth poses: {', '.join(added[:6])}{'…' if len(added) > 6 else ''}")
        else:
            self.report({"INFO"}, "No new mouth poses found. Everything is already here")

        return {"FINISHED"}

    def load_pose_assets_from_libraries(self) -> list[str]:
        """
        Link (never append) mouth pose assets from the configured asset libraries.

        Skips any pose whose name is already in this file, including numbered
        copies ('Mm_Mouth' and 'Mm_Mouth.001' are the same pose), so pressing the
        button again never adds anything twice.
        """
        prefs = bpy.context.preferences
        if prefs is None:
            return []

        current_file = Path(bpy.data.filepath).resolve() if bpy.data.filepath else None
        have = {base_name(a.name) for a in bpy.data.actions}
        added: list[str] = []

        for asset_library in prefs.filepaths.asset_libraries:
            library_path = Path(asset_library.path)
            if not library_path.exists():
                continue

            for blend_file in sorted(library_path.rglob("*.blend")):
                if not blend_file.is_file() or (current_file and blend_file.resolve() == current_file):
                    continue
                try:
                    with bpy.data.libraries.load(str(blend_file), link=True, assets_only=True) as (data_from, data_to):
                        wanted = []
                        for name in data_from.actions:
                            key = base_name(name)
                            if is_mouth_pose_name(name) and key not in have:
                                wanted.append(name)
                                have.add(key)
                        data_to.actions = wanted
                    added.extend(a.name for a in data_to.actions if a is not None)
                except Exception:
                    continue

        return added
