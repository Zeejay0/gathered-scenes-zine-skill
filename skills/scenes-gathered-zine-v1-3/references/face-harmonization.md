# Optional source-face harmonization

Use this extension only when the user explicitly asks before generation to preserve the original facial features, or asks after generation to repair a distorted face. It is a post-processing step for the existing Gathered Scenes result, not a separate composition mode.

## Boundaries

- Preserve the original skill's prompt, composition, photographic anchor, illustration, chromatic structure, torn edge, text, output, credit, and correction rules.
- Do not run face detection or local compositing unless the user explicitly requests face preservation or repair.
- Restore only facial features. Do not paste back a whole head, body, garment, animal, or photographic background region.
- Keep the generated image dimensions unchanged.
- This process retains source facial detail while intentionally adapting low-frequency light and color. Never claim that source pixels remain identical.
- Do not infer identity from face order. View both detection previews and record the source-to-target correspondence explicitly.

## Compatibility

The source and generated faces must show compatible pose, expression, visibility, and head geometry. Do not restore a hidden face, invent an occluded feature, or force a frontal face into a strong profile. If the generated pose differs too much, use the skill's single targeted regeneration first. If it remains incompatible, return the unmodified generated result and explain the limitation.

## Procedure

1. Finish the normal Gathered Scenes generation and its ordinary targeted correction, if needed.
2. Detect faces in the source and generated result with `scripts/face-harmonization/detect_faces.py`. Set `--expected-faces` from visual inspection. For a distant face, `--roi x,y,width,height` may focus detection; coordinates remain in the full oriented image.
3. Inspect both preview images. Match each person using visible position, hair, clothing, pose, and surrounding context. Positional IDs such as `face-1` are labels, not identity evidence.
4. Create a job JSON using [face-harmonization-job.md](face-harmonization-job.md). Use the default strength first.
5. Run `scripts/face-harmonization/harmonize.cjs`. It uses an eye-and-nose similarity transform, so it may rotate, uniformly scale, and translate the source facial region without stretching facial geometry.
6. Compare `final.png`, `preview.jpg`, and `selection-check.png` with the source and generated result. Check eye shape and spacing, nose, mouth, expression, face contour, skin-to-neck color, hairline, temples, ears, jaw, and transitions at 100% scale.
7. Deliver `final.png` only after the visual review succeeds. Keep the unmodified generated image as the fallback.

The tone operation is equivalent to:

```text
result = source detail + strength × (target low frequency − source low frequency)
```

The default `strength` is `0.32`, with an allowed range of `0..0.6`. Raise it slightly only when the face still appears pasted on; lower it when identity detail or natural skin color weakens. The default low-frequency radius is about 3.5% of the source face width. An adaptive transition ring blends the facial core toward the generated skin and surrounding material.

Read [face-harmonization-setup.md](face-harmonization-setup.md) only when this extension is requested. Runtime packages and intermediate files are unnecessary for the default Gathered Scenes workflow.
