'use strict';

const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const { strict } = require('node:assert');
const { test } = require('node:test');
const sharp = require('sharp');
const { fitSimilarity, harmonizePatch, hashFile } = require('../scripts/face-harmonization/common.cjs');
const { harmonize } = require('../scripts/face-harmonization/harmonize.cjs');

test('similarity alignment preserves facial geometry', () => {
  const source = [[12, 8], [64, 10], [35, 47]];
  const angle = Math.PI / 9;
  const scale = 1.7;
  const target = source.map(([x, y]) => [
    scale * Math.cos(angle) * x - scale * Math.sin(angle) * y + 35,
    scale * Math.sin(angle) * x + scale * Math.cos(angle) * y - 9,
  ]);
  const transform = fitSimilarity(source, target);
  strict.ok(Math.abs(transform.scale - scale) < 1e-10);
  strict.ok(Math.abs(transform.rotationDegrees - 20) < 1e-10);
  strict.ok(transform.normalizedResidual < 1e-10);
});

test('harmonization shifts low-frequency tone while retaining source contrast', () => {
  const width = 21;
  const height = 21;
  const reference = Buffer.alloc(width * height * 3);
  const rgba = Buffer.alloc(width * height * 4);
  const target = Buffer.alloc(width * height * 3, 220);
  for (let y = 0; y < height; y += 1) for (let x = 0; x < width; x += 1) {
    for (let channel = 0; channel < 3; channel += 1) {
      const index = y * width + x;
      const value = 100 + (x % 2 ? 10 : -10);
      reference[index * 3 + channel] = value;
      rgba[index * 4 + channel] = value;
      rgba[index * 4 + 3] = 255;
    }
  }
  const output = harmonizePatch({ width, height, reference, rgba }, target, 0.35, 5);
  const channel = x => output[(10 * width + x) * 4];
  strict.ok(channel(10) > 90 && channel(10) < 220);
  strict.ok(Math.abs((channel(11) - channel(10)) - 20) <= 2);
});

test('one mapped face is harmonized without changing target dimensions', async () => {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'gathered-face-test-'));
  try {
    const width = 512;
    const height = 512;
    const source = path.join(root, 'source.png');
    const target = path.join(root, 'target.png');
    await sharp({ create: { width, height, channels: 3, background: { r: 100, g: 100, b: 100 } } }).png().toFile(source);
    await sharp({ create: { width, height, channels: 3, background: { r: 200, g: 200, b: 200 } } }).png().toFile(target);
    const face = { id: 'face-1', anchors: [[90, 105], [150, 105], [120, 135]], corePolygon: [[80, 75], [160, 75], [160, 175], [80, 175]] };
    const sourceFaces = path.join(root, 'source-faces.json');
    const targetFaces = path.join(root, 'target-faces.json');
    fs.writeFileSync(sourceFaces, JSON.stringify({ inputSha256: hashFile(source), image: { width, height }, faces: [face] }));
    fs.writeFileSync(targetFaces, JSON.stringify({ inputSha256: hashFile(target), image: { width, height }, faces: [face] }));
    const job = path.join(root, 'job.json');
    fs.writeFileSync(job, JSON.stringify({
      source,
      target,
      sourceDetections: sourceFaces,
      targetDetections: targetFaces,
      outputDir: path.join(root, 'output'),
      faces: [{ id: 'person-1', sourceId: 'face-1', targetId: 'face-1', identityReview: 'Synthetic fixture mapping checked by position.', strength: 0.35 }],
    }));
    const result = await harmonize(job);
    const metadata = await sharp(result.image).metadata();
    strict.equal(metadata.width, width);
    strict.equal(metadata.height, height);
    const report = JSON.parse(fs.readFileSync(result.report, 'utf8'));
    strict.equal(report.operation, 'source-face-harmonized');
    strict.equal(report.pixelVerification, 'not-applicable');
    strict.equal(report.visualReview, 'required');
  } finally {
    strict.ok(path.resolve(root).startsWith(`${path.resolve(os.tmpdir())}${path.sep}gathered-face-test-`));
    fs.rmSync(root, { recursive: true, force: true });
  }
});
