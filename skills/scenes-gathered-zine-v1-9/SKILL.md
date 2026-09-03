---
name: scenes-gathered-zine-v1-9
description: "Transform a supplied photo into an orientation-matched Gathered Scenes Zine paper poster. Keep retained photographic regions visually unchanged, translate paper-covered regions into simplified spatially registered illustration whose source colors fade gradually from rich near the photo to quiet near the paper, add one source-derived high-saturation guide color, and fuse media through pigment dissolution without torn edges. Use for tactile photo-and-illustration collage posters; do not use when the user wants the whole photo restyled or enhanced."
---

# 拾景纸刊 · Gathered Scenes Zine v1.9

Create a calm, flat-scanned paper poster whose three layers remain clearly different:

1. **Photographic anchor:** the supplied image, unchanged inside the retained area.
2. **Registered illustration:** a sparse print interpretation of the exact scene hidden beneath paper.
3. **Guide color:** one high-saturation, source-derived line or compact field that directs the eye.

The signature is **真景不改、同位简译、源色渐隐、艳色引路、颗粒消融**.

Return the generated image and one brief Chinese rationale. Return prompts or detailed notes only when requested.

## Decision Order

1. Preserve scene identity and input orientation.
2. Keep the photographic anchor unchanged.
3. Preserve spatial continuity between photo and illustration.
4. Simplify illustrated content before adding texture or decoration.
5. Use source color twice in distinct roles: a rich-to-quiet spatial fade inside the illustration, and one high-saturation family for eye guidance.
6. Fuse through pigment dissolution; never create a torn or cut edge.
7. Keep text short, readable, and subordinate.

When priorities conflict, protect the photograph and remove illustration detail.

## Read the Source

Build a compact internal scene card:

- **Core subjects:** one or two elements that identify the scene.
- **Spatial invariants:** horizon, scale, relative position, overlap, facing direction, perspective, and contact points.
- **Dominant gesture:** the strongest horizon, diagonal, gaze, path, shoreline, roofline, wire, branch, or movement.
- **Visual-weight map:** large dark areas, faces, bright windows, saturated regions, isolation, and edge tension.
- **Native palette:** dominant temperature plus two to four broad local hue families.
- **Color-fade direction:** the distance or path from photographic boundary through illustrated scene to quiet paper.
- **Guide-color candidate:** one meaningful source hue and one source path it can follow.
- **Quiet field:** sky, water, wall, ground, haze, or other low-information area.
- **Semantic minimum:** the few forms and relationships needed to recognize this exact scene.

Treat the source photo as fact. Illustration may change medium and information density, not scene content.

## 1. Photographic Anchor: Zero Restyling

Retained photographic regions are an immutable plate. Cropping, placement, and a boundary dissolve are allowed; interior alteration is not.

Preserve the source's existing:

- color, white balance, saturation, exposure, contrast, shadows, and highlights;
- softness, focus, resolution, grain, noise, atmospheric haze, lens character, and motion blur;
- geometry, silhouettes, already-resolved texture, and object detail;
- identity, expression, gaze, posture, proportions, skin tone, and facial softness.

Do not apply:

- color grading, desaturation, recoloring, relighting, HDR, dehaze, local contrast, clarity, sharpening, or texture enhancement;
- denoising followed by reconstruction, synthetic upscaling detail, AI smoothing, beautification, skin retouching, or face enhancement;
- invented eyes, teeth, hair, pores, fabric weave, water ripples, foliage, highlights, reflections, signage, architecture, or other absent detail;
- paper texture, halftone, illustration marks, or vintage filters over the photo-anchor interior.

Faces are protected even when small. A soft or indistinct face must remain soft or indistinct. If the image-generation tool cannot preserve a photographic area literally, request the strongest possible source fidelity and keep the retained anchor broad, simple, and free of stylistic overlay.

## 2. Spatially Registered Illustration

Every paper-covered location depicts the real source content hidden beneath it.

- **Same content:** sky remains sky; water remains water; a building, person, flag, tree, fence, pole, or road remains that object.
- **Same coordinates:** preserve approximate position, scale, crop, and overlap order.
- **Same geometry:** preserve horizon height, slopes, wire and rail angles, perspective convergence, rhythm, facing direction, and contact base.
- **Same continuation:** a contour crossing from photography into paper begins at the same point and continues in the same direction.
- **Lower information density:** omit roughly 65–85% of small detail. Spatial registration is not tracing.

Choose one primary grammar and at most one support:

- **Contour-led:** broken lines for architecture, paths, rails, coastlines, wires, and gestures.
- **Field-led:** sparse halftone or translucent ink for sky, water, fog, shadow, and ground.
- **Silhouette-led:** one or two broad masses for people, trees, roofs, boats, and compact subjects.
- **Rhythm-led:** a few repeated marks for windows, posts, waves, or steps.

Keep the illustration visibly quieter than photography. Merge repeated forms, leave contours incomplete, and preserve generous blank paper. Do not render pores, facial features beyond the semantic minimum, hair strands, fabric weave, individual leaves, gravel, water micro-ripples, or full photographic shading.

For dense foliage or organic texture, omit 85–95% of individual parts and retain only one dominant mass, one to three directional gestures, and at most two secondary clusters.

## 3. Source-Color Gradient

Illustration should retain the covered scene's color and lose it gradually across space, not become pale the moment photography ends.

- Keep two to four broad source hue families in their correct locations. Preserve hue direction and temperature more than exact samples.
- Define one continuous fade path beginning at the photographic boundary and ending in quiet paper. Follow scene depth, atmosphere, or the dominant compositional gesture rather than a mechanical straight band.
- **Near zone:** retain roughly 70–85% of the source's perceived saturation and value contrast. The medium is illustrated, but its color connection to the photograph is unmistakable.
- **Middle zone:** reduce to roughly 45–60%, merging variation into broad washes, broken risograph layers, dry ink, pencil, or halftone.
- **Far zone:** reduce to roughly 20–35%, thin the printed density, and dissolve into the paper tone.
- Vary saturation, value contrast, and mark density together so the transition reads as layered atmospheric loss rather than three visible stripes.
- Keep the illustration simpler and flatter than photography at every stage. High local saturation never restores photographic texture or tonal modeling.
- Never make the entire illustration uniformly faint, beige, gray, monochrome, or washed out. Never move color to an unrelated object for decoration.

Examples of correct registration: cyan water stays with water, cobalt ice shadow with ice, vegetation green with vegetation, warm window light with windows, garment color with the same figure, and deck or building color with that structure.

The fade describes distance from photographic fact to paper memory. It changes color intensity and print density, not hidden content or geometry.

## 4. High-Saturation Eye Guide

Add one clearly visible high-saturation family derived from a meaningful source color. This accent must guide attention rather than decorate empty space.

### Choose the hue

Select by one source-aware relationship:

- intensify a meaningful minor source color;
- use an analogous saturated hue to extend the native atmosphere;
- use a near-complementary hue to connect separated focal areas;
- bridge warm and cool areas already present in the photo.

Use one exact family—for example coral-magenta derived from sunset pink, cobalt derived from deep water, tomato red derived from a garment, or vivid green derived from vegetation. Do not introduce a second competing bright family.

### Build the path

Derive the accent geometry from the source's dominant gesture. It may:

- follow and transform along a horizon, shoreline, roofline, path, gaze, rail, wire, branch, or shadow;
- begin near one focal point, disappear through a quiet interval, and reappear near the next;
- use one broken line plus two or three compact flat passages in the same hue family;
- pass behind or beside subjects without recoloring, covering, outlining, or altering them.

Keep it roughly 4–10% of poster area. Use matte risograph, dry ink, broken coverage, or slight misregistration. At thumbnail size, removing it must weaken the eye path, balance, or photo–illustration continuity.

Never use a detached corner block, generic circle, arbitrary bright dot, isolated swatch, confetti, uniform border, or unrelated geometric sticker.

## Composition

- Portrait source → portrait **3:5**.
- Landscape source → landscape **5:3**.
- Square source → portrait 3:5 unless its dominant gesture clearly needs width.

Choose a source-driven layout:

- **Transformative seam:** photo 30–50%; continue a real contour or plane into illustration.
- **Photo anchor + expansive field:** photo 25–45%; let registered illustration and quiet paper carry the wider composition.
- **Underprint overlay:** photo 35–60%; keep the photo interior untouched while illustration and guide color move around or behind it.
- **Directional split:** start near 55/45 to 65/35 and align the split to a real source gesture.

Balance visual weight rather than equal area. Preserve breathing room in front of a gaze, path, wave, or diagonal. Make the illustrated field larger by extent, not by added detail.

## Natural Fusion

Use one asymmetric **pigment-dissolution zone** around the photographic anchor.

1. Begin the transition before the photo would otherwise stop.
2. Only inside this boundary zone, taper contrast, saturation, micro-detail, and edge certainty.
3. Break the remaining image into soft halftone dust, dry-brush residue, translucent pigment loss, and paper-fiber absorption.
4. Let the registered illustration emerge from the same geometry.
5. Keep horizons, paths, rails, wires, shorelines, figures, and other crossing points aligned.
6. Let residue thin asymmetrically into clean paper; do not form a closed outline.

Use a broader dissolve for sky, fog, water, and ground; a narrower one around faces, hands, thin limbs, recognizable objects, and decisive structural edges. Never increase or reconstruct detail before dissolving it.

Hard prohibition: torn edge, deckled rim, exposed fiber strip, ripped notch, scallop, paper frame, cutout outline, white halo, glow, uniform blur rim, sticker edge, rectangular clipping, drop shadow, curled corner, lifted paper, or 3D depth.

## Text Material

Read [references/text-material.md](references/text-material.md) before generating.

- Reproduce supplied wording exactly.
- Otherwise author one English-only scene phrase: one word, a two-to-four-word keyword sequence, or a phrase of five words or fewer.
- Use Chinese-only or bilingual text only when supplied or requested; Chinese stays at eight Han characters or fewer.
- Use one text behavior: semantic break, directional alignment, drifting baseline, modest offset, two-scale contrast, or limited occlusion.
- Use at most two type voices and two size levels; keep one clear reading order.
- Derive placement and direction from the source gesture. Use charcoal, graphite, faded brown-black, or a restrained echo of the guide hue.
- Never conceal a face or compete with the core subject.

## Prompt Compiler

Write four compact paragraphs:

1. **Canvas and attention:** ratio, chosen layout, photo share, illustration field, focal area, quiet area, eye path, and text area.
2. **Immutable photograph:** exact retained content and explicit prohibition of any interior color, tone, clarity, texture, identity, or detail change.
3. **Registered illustration and color:** coverage map, continuation points, grammar, omitted detail, near/middle/far source-color levels and fade direction, high-saturation guide hue, guide path, material, area, and natural fusion.
4. **Paper, text, mood, and avoids:** exact text, typography, paper/scan texture, emotional temperature, and prohibited aesthetics.

State visible decisions, not design theory or file metadata.

## Workflow

1. Detect orientation and build the scene card.
2. Choose the immutable photo anchor and quiet field.
3. Build a coverage map for every paper region.
4. Choose one illustration grammar and simplify 65–85% of detail.
5. Register two to four source hue families to their hidden objects or planes, then resolve a continuous near 70–85% → middle 45–60% → far 20–35% fade into paper.
6. Choose one high-saturation source hue and a source-derived guide path.
7. Define the pigment-dissolution boundary without touching the photo interior.
8. Resolve one short text unit using the reference guide.
9. Compile the prompt and generate with the source image as the edit target.
10. If one correction is needed, change only the failed system: photo fidelity, registration, simplification, guide path, fusion, or text.

## Targeted Corrections

- **Photo changed:** restore original color, tone, softness, grain, focus, texture, silhouettes, and faces; remove every overlay or enhancement from the photo interior.
- **Illustration too literal:** omit at least half the remaining detail, merge shapes, flatten color, and enlarge quiet paper.
- **Wrong hidden content:** restore the real source object, coordinates, perspective, overlap, and crossing direction.
- **Illustration too pale:** restore rich source color near the photographic boundary, then taper it progressively through middle and far zones without restoring detail.
- **Color fade banded:** replace visible saturation stripes with an irregular atmospheric gradient that changes chroma, contrast, and print density together.
- **Color fade too flat:** strengthen the difference between near, middle, and far zones while keeping their transitions continuous.
- **Guide color decorative:** attach it to a real horizon, path, gaze, roofline, shoreline, rail, wire, or other dominant gesture.
- **Guide color weak:** increase chroma, continuity, or one compact passage while keeping a single hue family and protecting subjects.
- **Guide color dominant:** reduce area or frequency, not chroma; keep the path legible.
- **Fusion abrupt:** widen only the boundary dissolve and restore the sequence photo → pigment → aligned illustration → paper.
- **Fusion muddy:** narrow residue around defining subjects and restore clean paper.
- **Text illegible or dominant:** restore exact wording, one behavior, clear order, and subordinate scale.

## Output

Return:

```markdown
![Gathered Scenes Zine v1.9 poster](absolute-image-path-or-rendered-image)

**创作思路**

[One short Chinese paragraph explaining the immutable photo anchor, registered illustration, and guide-color path.]
```

Do not include the full prompt unless requested.
