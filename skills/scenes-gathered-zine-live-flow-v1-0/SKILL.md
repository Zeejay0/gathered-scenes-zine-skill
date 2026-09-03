---
name: scenes-gathered-zine-live-flow-v1-0
description: "Run the complete Gathered Scenes workflow from a supplied photograph to a static poster, a scene-authored adaptive v0.2 flat paper-tear Apple Live Photo ZIP, and optional handoff of that ZIP to the local Live Photo Importer. Use when the user wants the full source-to-Live-Photo flow with a custom narrative tear path and broad rounded low-frequency contours; do not use for static-only posters, 3D paper curls, or motion inside the photographed scene."
---

# 拾景纸刊实况全流程 v1.0

Turn one supplied photograph into one importer-ready Live Photo ZIP through two strictly separated modules:

1. Create the finished poster with the frozen sibling skill `../scenes-gathered-zine-v1-9/SKILL.md`.
2. Animate only a flat covering sheet tearing away from that finished poster.
3. Pair the exact final frame as an Apple Live Photo JPG/MOV pair.
4. Package only that pair in one ZIP.
5. When import is requested, hand the ZIP to “实况照片导入器” through macOS file-open and stop.

Do not modify `scenes-gathered-zine-v1-9`. It remains the single source of truth for all static visual decisions.

## Trigger Modes

- **Full flow / import:** source photo → v1.9 poster → Live ZIP → importer handoff.
- **ZIP only:** source photo or finished v1.9 poster → Live ZIP with `--no-import`.
- **Static only:** use `scenes-gathered-zine-v1-9` directly and stop; this orchestration skill is unnecessary.

For the established full-flow workflow, skip preview movies, contact sheets, visual review gates, metadata reports, and approval pauses. Continue automatically unless a step returns an explicit error. The user performs the final visual check.

## Phase 1: Freeze the Poster

If the input is a raw photograph:

1. Read and follow the complete sibling `../scenes-gathered-zine-v1-9/SKILL.md`.
2. Generate the orientation-matched poster using its required image-generation path.
3. Save the flattened result inside the current project output directory.

If the input is already a finished v1.9 poster, begin from it directly.

After this phase, treat the finished poster as an immutable bottom plate. Do not recolor, sharpen, clarify, regenerate, crop, resize non-proportionally, retouch faces, add detail, or otherwise redesign it during animation. Every fully revealed frame region must come directly from this frozen poster.

## Phase 2: Choose the Tear

Compose the tear path only after seeing the finished poster. Read:

- `references/adaptive-path-selection.md`
- `references/adaptive-tear-boundary.md`

Always compose one custom source-derived path with 3–7 normalized points. Do not choose from preset directions. Start in quiet paper, establish the environment or a clue, reveal the structural relationship next, bring the primary subject into view during the middle third, and end at a clear visual resting point.

Follow a real ridge, shoreline, roofline, road, gaze, spatial-depth transition, or relationship between subjects. Complement the poster's guide color without tracing it. Avoid top-to-bottom and bottom-to-top reveals, one rigid straight diagonal, faces, bodies, text, and defining objects.

The visible opening follows one scene-aware global path. Its boundary uses broad, high-amplitude, low-frequency rises and falls, small unequal notches, changing opening width, and a narrow warm fiber fringe. Reject clean digital wipes, uniform saw teeth, regular zigzags, curled sheets, and 3D depth simulation.

## Phase 3: Build the Live ZIP

Use `scripts/build_live_zip_and_import.py` with the frozen poster, chosen direction, and optional custom path. The accepted motion profile is fixed:

- 3.0 seconds at 30 fps;
- brief fully covered hold;
- crack propagation;
- asymmetric two-sided expansion with broad rounded low-frequency boundary variation;
- exact unchanged poster from 2.7 seconds through the final hold;
- no camera motion, subject motion, relighting, parallax, or internal animation.

Example ZIP-only build:

```bash
python3 scripts/build_live_zip_and_import.py \
  --input /absolute/path/to/final-poster.png \
  --output-zip /absolute/path/to/GatheredScenesLivePhoto.zip \
  --direction custom \
  --path-points "0.04,0.72;0.26,0.60;0.52,0.44;0.76,0.34;0.98,0.24" \
  --no-import
```

Read `references/apple-live-photo.md` for pairing invariants. The ZIP contract is strict:

- exactly one top-level folder;
- exactly one paired `.JPG` and one paired `.MOV` inside it;
- no poster, receipt, contact sheet, preview, source file, or sidecar inside the ZIP;
- the ZIP is the only durable delivery artifact required from this workflow.

All render frames, unpaired media, and receipts remain temporary.

## Phase 4: Importer Handoff

When the user asks for the complete automated flow or asks to place the result in Photos, omit `--no-import`. Read `references/importer-handoff.md` and let the build script open the completed ZIP with bundle id `com.zeejay.live-photo-importer`.

Do not simulate drag-and-drop and do not operate the Photos app. Successful submission of the ZIP to “实况照片导入器” is the stopping point. The importer owns pairing validation, permissions, Photos-library insertion, and later iCloud synchronization.

If the importer cannot be found, keep the finished ZIP and report the handoff error. Do not regenerate the poster or animation. Use `--importer-app /absolute/path/实况照片导入器.app` only when its exact path is known.

## Response Contract

For ZIP-only mode, return the absolute ZIP path. For full-flow mode, return the absolute ZIP path, state whether macOS accepted the importer handoff, and briefly describe the composed narrative path. Do not present intermediate files unless the user explicitly asks for them.
