'use strict';

const {
  assert, bounds, distance, fitSimilarity, fs, harmonizePatch, hashFile, inside, inversePoint, mapPoint,
  parseArgs, path, polygonValid, readJson, resolveFrom, sampleRgb, sharp, writeJson,
} = require('./common.cjs');

function prepareFace(mapping, sourceFace, targetFace) {
  assert(/^[a-z0-9-]+$/.test(mapping.id), 'Use a stable lowercase face ID.');
  assert(typeof mapping.identityReview === 'string' && mapping.identityReview.length >= 8,
    'Describe the visually checked source and target correspondence.');
  const transform = fitSimilarity(sourceFace.anchors, targetFace.anchors);
  assert(transform.normalizedResidual <= 0.12, 'Head geometry differs too much for local restoration.');
  assert(Math.abs(transform.rotationDegrees) <= 30, 'Head rotation differs too much for local restoration.');
  const coreBox = bounds(sourceFace.corePolygon);
  const center = [(coreBox.left + coreBox.right) / 2, (coreBox.top + coreBox.bottom) / 2];
  const outerPolygon = mapping.outerPolygon ?? sourceFace.corePolygon.map(point => [
    center[0] + (point[0] - center[0]) * 1.24,
    center[1] + (point[1] - center[1]) * 1.18,
  ]);
  assert(polygonValid(outerPolygon), 'Invalid outer polygon.');
  const minimumClearance = mapping.minimumClearancePx ?? Math.max(3, (coreBox.right - coreBox.left) * 0.025);
  assert(sourceFace.corePolygon.every(point => inside(point, outerPolygon) && distance(point, outerPolygon) >= minimumClearance),
    'Outer polygon does not contain the facial core and transition ring.');
  const strength = mapping.strength ?? 0.32;
  const radiusPx = mapping.radiusPx ?? Math.max(4, (coreBox.right - coreBox.left) * 0.035);
  assert(Number.isFinite(strength) && strength >= 0 && strength <= 0.6, 'strength must be between 0 and 0.6.');
  assert(Number.isFinite(radiusPx) && radiusPx >= 2 && radiusPx <= 200, 'radiusPx must be between 2 and 200 source pixels.');
  return { ...mapping, corePolygon: sourceFace.corePolygon, outerPolygon, minimumClearance, radiusPx, strength, transform };
}

function renderPatch(source, face, canvas) {
  const box = bounds(face.outerPolygon.map(point => mapPoint(point, face.transform)));
  assert(box.left >= 0 && box.top >= 0 && box.right < canvas.width && box.bottom < canvas.height,
    'Face transition extends beyond the generated image.');
  const width = box.right - box.left + 1;
  const height = box.bottom - box.top + 1;
  const rgba = Buffer.alloc(width * height * 4);
  const reference = Buffer.alloc(width * height * 3);
  let activePixels = 0;
  for (let y = 0; y < height; y += 1) for (let x = 0; x < width; x += 1) {
    const sourcePoint = inversePoint([box.left + x, box.top + y], face.transform);
    const inCore = inside(sourcePoint, face.corePolygon);
    const inOuter = inside(sourcePoint, face.outerPolygon);
    if (!inCore && !inOuter) continue;
    const rgb = sampleRgb(source, sourcePoint[0], sourcePoint[1]);
    const index = y * width + x;
    const outerDistance = distance(sourcePoint, face.outerPolygon);
    const coreDistance = distance(sourcePoint, face.corePolygon);
    let opacity = inCore ? 1 : outerDistance / (outerDistance + coreDistance);
    opacity = opacity * opacity * (3 - 2 * opacity);
    for (let channel = 0; channel < 3; channel += 1) {
      rgba[index * 4 + channel] = rgb[channel];
      reference[index * 3 + channel] = rgb[channel];
    }
    rgba[index * 4 + 3] = Math.round(opacity * 255);
    activePixels += 1;
  }
  assert(activePixels >= 64, 'Face region is too small to harmonize.');
  return { ...box, width, height, rgba, reference };
}

async function harmonize(jobPath) {
  const job = readJson(jobPath);
  const base = path.dirname(path.resolve(jobPath));
  const sourcePath = resolveFrom(job.source, base);
  const targetPath = resolveFrom(job.target, base);
  const sourceDetectionsPath = resolveFrom(job.sourceDetections, base);
  const targetDetectionsPath = resolveFrom(job.targetDetections, base);
  const outputDir = resolveFrom(job.outputDir, base);
  assert(!fs.existsSync(outputDir) || fs.readdirSync(outputDir).length === 0,
    'Output directory is not empty; choose a new directory.');
  const sourceDetections = readJson(sourceDetectionsPath);
  const targetDetections = readJson(targetDetectionsPath);
  assert(sourceDetections.inputSha256 === hashFile(sourcePath), 'Source detections do not match the source image.');
  assert(targetDetections.inputSha256 === hashFile(targetPath), 'Target detections do not match the generated image.');
  assert(Array.isArray(job.faces) && job.faces.length > 0, 'At least one explicitly mapped face is required.');
  assert(new Set(job.faces.map(face => face.sourceId)).size === job.faces.length, 'Duplicate source face mapping.');
  assert(new Set(job.faces.map(face => face.targetId)).size === job.faces.length, 'Duplicate target face mapping.');
  const source = await sharp(sourcePath).autoOrient().toColourspace('srgb').removeAlpha().raw().toBuffer({ resolveWithObject: true });
  const target = await sharp(targetPath).autoOrient().toColourspace('srgb').removeAlpha().raw().toBuffer({ resolveWithObject: true });
  assert(source.info.width === sourceDetections.image.width && source.info.height === sourceDetections.image.height,
    'Source coordinate system differs from its detections.');
  assert(target.info.width === targetDetections.image.width && target.info.height === targetDetections.image.height,
    'Generated image coordinate system differs from its detections.');
  const faces = job.faces.map(mapping => {
    const sourceFace = sourceDetections.faces.find(face => face.id === mapping.sourceId);
    const targetFace = targetDetections.faces.find(face => face.id === mapping.targetId);
    assert(sourceFace && targetFace, 'Mapped face ID was not found in the detections.');
    return prepareFace(mapping, sourceFace, targetFace);
  });
  const final = Buffer.from(target.data);
  const selection = Buffer.from(target.data);
  const occupied = Buffer.alloc(target.info.width * target.info.height);
  const records = [];
  for (const face of faces) {
    const patch = renderPatch(source, face, target.info);
    const targetPatch = Buffer.alloc(patch.width * patch.height * 3);
    for (let y = 0; y < patch.height; y += 1) for (let x = 0; x < patch.width; x += 1) {
      const local = y * patch.width + x;
      const global = (patch.top + y) * target.info.width + patch.left + x;
      for (let channel = 0; channel < 3; channel += 1) targetPatch[local * 3 + channel] = target.data[global * 3 + channel];
    }
    const harmonized = harmonizePatch(patch, targetPatch, face.strength, face.radiusPx * face.transform.scale);
    for (let y = 0; y < patch.height; y += 1) for (let x = 0; x < patch.width; x += 1) {
      const local = y * patch.width + x;
      const global = (patch.top + y) * target.info.width + patch.left + x;
      const alpha = harmonized[local * 4 + 3];
      if (!alpha) continue;
      assert(!occupied[global], 'Mapped face regions overlap; revise the selections.');
      occupied[global] = 1;
      for (let channel = 0; channel < 3; channel += 1) {
        final[global * 3 + channel] = Math.round((harmonized[local * 4 + channel] * alpha
          + target.data[global * 3 + channel] * (255 - alpha)) / 255);
        selection[global * 3 + channel] = Math.round(final[global * 3 + channel] * 0.55
          + [0, 220, 255][channel] * 0.45);
      }
    }
    records.push({
      id: face.id,
      sourceId: face.sourceId,
      targetId: face.targetId,
      strength: face.strength,
      radiusPx: face.radiusPx,
      scale: face.transform.scale,
      rotationDegrees: face.transform.rotationDegrees,
      normalizedResidual: face.transform.normalizedResidual,
      bounds: { left: patch.left, top: patch.top, width: patch.width, height: patch.height },
    });
  }
  fs.mkdirSync(outputDir, { recursive: true });
  const finalPath = path.join(outputDir, 'final.png');
  await sharp(final, { raw: { width: target.info.width, height: target.info.height, channels: 3 } }).png().toFile(finalPath);
  await sharp(final, { raw: { width: target.info.width, height: target.info.height, channels: 3 } })
    .resize({ width: 1200, height: 2000, fit: 'inside', withoutEnlargement: true })
    .jpeg({ quality: 93, chromaSubsampling: '4:4:4' }).toFile(path.join(outputDir, 'preview.jpg'));
  await sharp(selection, { raw: { width: target.info.width, height: target.info.height, channels: 3 } })
    .resize({ width: 1500, height: 2500, fit: 'inside', withoutEnlargement: true })
    .png().toFile(path.join(outputDir, 'selection-check.png'));
  const report = {
    schemaVersion: 1,
    operation: 'source-face-harmonized',
    sourceSha256: hashFile(sourcePath),
    targetSha256: hashFile(targetPath),
    finalSha256: hashFile(finalPath),
    dimensions: { width: target.info.width, height: target.info.height },
    faces: records,
    pixelVerification: 'not-applicable',
    visualReview: 'required',
  };
  const reportPath = path.join(outputDir, 'face-harmonization.json');
  writeJson(reportPath, report);
  return { image: finalPath, report: reportPath, faces: records.length };
}

if (require.main === module) {
  const args = parseArgs();
  harmonize(args.job).then(result => console.log(JSON.stringify(result))).catch(error => {
    console.error(error.message);
    process.exitCode = 1;
  });
}

module.exports = { harmonize, prepareFace, renderPatch };
