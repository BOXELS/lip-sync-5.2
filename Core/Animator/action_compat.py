"""
Helpers for reading F-Curves from Actions on Blender 5.x.

Blender 5.0 removed the legacy ``Action.fcurves`` / ``Action.groups`` API.
All Actions are now "layered": F-Curves live in a channelbag that belongs to
a keyframe strip and an action slot. These helpers hide that so the
animators can stay simple.
"""

from typing import Iterator

import bpy


def iter_channelbags(action: "bpy.types.Action", slot=None) -> Iterator["bpy.types.ActionChannelbag"]:
    """Yield the channelbags of an action, optionally restricted to one slot."""
    if action is None:
        return

    for layer in action.layers:
        for strip in layer.strips:
            if not isinstance(strip, bpy.types.ActionKeyframeStrip):
                continue
            if slot is not None:
                channelbag = strip.channelbag(slot)
                if channelbag is not None:
                    yield channelbag
                continue
            for channelbag in strip.channelbags:
                yield channelbag


def iter_fcurves(action: "bpy.types.Action", slot=None) -> Iterator["bpy.types.FCurve"]:
    """Yield every F-Curve of an action (optionally only for one slot)."""
    for channelbag in iter_channelbags(action, slot):
        yield from channelbag.fcurves


def find_fcurve(action: "bpy.types.Action", data_path: str, index: int = 0, slot=None):
    """Find an F-Curve by data path and array index, like the old ``Action.fcurves.find``."""
    for channelbag in iter_channelbags(action, slot):
        fcurve = channelbag.fcurves.find(data_path, index=index)
        if fcurve is not None:
            return fcurve
    return None
