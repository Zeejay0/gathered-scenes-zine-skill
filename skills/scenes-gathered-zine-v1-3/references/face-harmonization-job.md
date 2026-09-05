# Face harmonization job

Use absolute paths or paths relative to the job file. Create a new empty output directory for each run.

```text
<python> scripts/face-harmonization/detect_faces.py --input <source.jpg> --out <run>/source-faces.json --expected-faces 2
<python> scripts/face-harmonization/detect_faces.py --input <generated.png> --out <run>/target-faces.json --expected-faces 2
<node> scripts/face-harmonization/harmonize.cjs --job <run>/job.json
```

Example job:

```json
{
  "source": "source.jpg",
  "target": "generated.png",
  "sourceDetections": "source-faces.json",
  "targetDetections": "target-faces.json",
  "outputDir": "harmonized-v1",
  "faces": [{
    "id": "person-left",
    "sourceId": "face-1",
    "targetId": "face-1",
    "identityReview": "Compared both previews: same left subject, hair, clothing, pose, and context.",
    "strength": 0.32
  }]
}
```

Add one mapping for every face that the user asked to repair. `sourceId` and `targetId` come from the two detection files. Optional per-face fields are:

- `strength`: low-frequency light and color adaptation, default `0.32`, range `0..0.6`.
- `radiusPx`: source-image blur radius, default about 3.5% of face width, range `2..200`.
- `outerPolygon`: source-image points for a manually reviewed transition boundary.
- `minimumClearancePx`: minimum distance between the facial core and outer transition boundary.

The output directory contains the master `final.png`, a display-sized `preview.jpg`, a `selection-check.png`, and `face-harmonization.json`. The report records provenance and parameters and marks pixel verification as not applicable because light and color are intentionally changed.
