# io_scene_dts

A modern Blender plugin for working with DTS/DSQ assets. Includes an importer and an exporter.

### Goals

* Implement import and export of all detail levels, nodes, objects, meshes, materials and sequences from/to DTS/DSQ files.
* Support all versions of the DTS file format from the one used in TGE 1.0 to the one used in the current version of T3D.
* Support the newest version of Blender (at the time of writing, 2.77), unlike the original DTS plugin (2.49b).

### Blender 5.x support

This fork updates the add-on for **Blender 4.2 – 5.1**. It installs either as a
modern extension (via the bundled `blender_manifest.toml`) or as a legacy add-on
(via `bl_info`). The port builds on the partial 2.80 work and additionally
handles the API breakages introduced since then:

* Slotted Actions (Blender 4.4): F-Curves are read/written through the
  slot/layer/strip channelbag API instead of `Action.fcurves`.
* Principled BSDF socket rename (4.0): `Emission` → `Emission Color`.
* EEVEE Next material API (4.2): `Material.shadow_method` removed; transparency
  is set via `blend_method` / `surface_render_method` / `use_transparent_shadow`.
* Removed `Material.diffuse_intensity` and 4-component `diffuse_color`.
* Removed `Scene.objects.link` and object groups (`users_group`).

Install: download the repository as a `.zip` and use *Edit → Preferences →
Add-ons → Install from Disk* (or *Get Extensions* in 5.x).
