# Lip Sync — Boxels Fork

A fork of [Charley 3D's Lip Sync](https://github.com/Charley3d/lip-sync) (v2.3.2, GPL-3.0-or-later),
updated to run on **Blender 5.1 and 5.2 LTS**. All original credit goes to Charley 3D.
This fork stays under the same GPL-3.0-or-later license.

## 2.4.2 (2026-10-30)
### Added (beginner-friendly)
- **Auto-Fill Mouth Poses** button (Pose Library mode): fills all mouth slots from your pose
  assets by name. Understands mouth-chart names like `Mm`, `F-V`, `A-E`, `O`, `Ooo`, `Sh`,
  `Default`/`Rest`, `MBP`, `AI`, `WQ`; ignores words like "Mouth" and version numbers like
  "-2". Prefers poses in a "Mouth" catalog. Any slot can still be changed by hand.
- Each mouth slot now shows the sounds it covers, e.g. `PP (m b p)`, `ou (oo w)`.
- "Viseme Settings" is now called "Mouth Poses".

## 2.4.1 (2026-10-30)
- Display name back to plain "Lip Sync" (no "(Boxels Fork)" label).

## 2.4.0 (2026-10-30)

### Fixed
- **Pose Library mode crashed on Blender 5.x.** Mouth poses were read with
  `Action.fcurves`, which Blender 5.0 removed. They're now read through the action's
  channelbag (`Core/Animator/action_compat.py`).
- **Sprite Sheet mode** used the same removed API when clearing old keys and setting
  constant interpolation. Fixed the same way.
- **Add-on would not load on Blender 5.1+.** The bundled compiled libraries (cffi, regex,
  rpds-py, charset-normalizer) were built for Python 3.11. Blender 5.1+ uses Python 3.13.
  Replaced with Python 3.13 builds for Windows, macOS (Intel + Apple Silicon) and Linux.
  This also adds the Windows and Apple Silicon builds of charset-normalizer that were missing.
- Switching a fresh object to Pose Library mode printed a `KeyError` from the sprite-sheet
  format update callback. It now skips quietly when that setting was never set.

### Changed
- Extension id is now `boxels_lip_sync`, so it installs
  alongside the original instead of replacing it.
- Minimum Blender version is now 5.1.0 (the Python 3.13 libraries won't load on older
  versions — use the original 2.3.2 for Blender 4.4–5.0).

### Tested
- Installed from the built zip into Blender 5.2.3 LTS (Python 3.13) and baked lip sync
  onto an armature driven by pose-library mouth shapes: real eSpeak phonemes, 48 keyframes,
  every key matches a mouth pose, closes on silence between words.

### Linux note
The bundled Linux eSpeak needs `libpcaudio0` (`sudo apt install libpcaudio0`), which most
desktop distros already have. Windows and macOS builds are self-contained.
