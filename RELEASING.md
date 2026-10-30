# Releasing a new version

**Releases are optional.** Anyone can install the latest code with the green
Code → Download ZIP button (it installs directly in Blender 5.1+). Just push to `master`.

Make a release when you want a fixed version that won't change, e.g. one you link from a
tutorial. Releases build and publish themselves; you never upload zips by hand.

1. Make your changes.
2. Bump `version` in `blender_manifest.toml` (e.g. `2.4.1` → `2.4.2`) and add a line to `FORK_CHANGES.md`.
3. Commit and push to `master`.
4. Push a matching tag:

   ```
   git tag v2.4.2
   git push origin v2.4.2
   ```

GitHub Actions then builds the Windows, macOS (Apple Silicon + Intel) and Linux zips and
publishes a Release with them attached. Watch it under the repo's **Actions** tab (~1 minute).
The README's "latest release" link updates on its own.

If the tag and the manifest version don't match, the build stops with an error telling you so.
Nothing gets published in that case.

You can also do the tag from GitHub's website: **Releases → Draft a new release → Choose a tag →
type `v2.4.2` → Create new tag**. But then publishing the release there yourself creates it
without the zips. The tag push from git (or asking Claude to do it) is the hands-off way.
