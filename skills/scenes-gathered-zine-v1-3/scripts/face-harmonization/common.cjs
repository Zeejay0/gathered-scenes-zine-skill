'use strict';

const crypto = require('node:crypto');
const fs = require('node:fs');
const path = require('node:path');
const sharp = require('sharp');

function assert(condition, message) { if (!condition) throw new Error(message); }
function digest(bytes) { return crypto.createHash('sha256').update(bytes).digest('hex'); }
function hashFile(file) { return digest(fs.readFileSync(file)); }
function readJson(file) { return JSON.parse(fs.readFileSync(file, 'utf8').replace(/^\uFEFF/, '')); }
function writeJson(file, value) { fs.writeFileSync(file, `${JSON.stringify(value, null, 2)}\n`, { flag: 'wx' }); }
function resolveFrom(file, base) { return path.resolve(base, file); }

function parseArgs() {
  const args = {};
  for (let i = 2; i < process.argv.length; i += 2) {
    assert(process.argv[i]?.startsWith('--') && process.argv[i + 1], 'Expected --option value pairs.');
    args[process.argv[i].slice(2)] = process.argv[i + 1];
  }
  return args;
}

function polygonValid(polygon) {
  return Array.isArray(polygon) && polygon.length >= 3
    && polygon.every(point => Array.isArray(point) && point.length === 2 && point.every(Number.isFinite));
}

function inside(point, polygon) {
  let hit = false;
  const [x, y] = point;
  for (let i = 0, j = polygon.length - 1; i < polygon.length; j = i++) {
    const [xi, yi] = polygon[i];
    const [xj, yj] = polygon[j];
    if (((yi > y) !== (yj > y)) && x < ((xj - xi) * (y - yi)) / (yj - yi) + xi) hit = !hit;
  }
  return hit;
}

function distance(point, polygon) {
  let best = Infinity;
  for (let i = 0; i < polygon.length; i += 1) {
    const start = polygon[i];
    const end = polygon[(i + 1) % polygon.length];
    const dx = end[0] - start[0];
    const dy = end[1] - start[1];
    const t = Math.max(0, Math.min(1, ((point[0] - start[0]) * dx + (point[1] - start[1]) * dy) / (dx * dx + dy * dy || 1)));
    best = Math.min(best, Math.hypot(point[0] - start[0] - t * dx, point[1] - start[1] - t * dy));
  }
  return best;
}

function bounds(polygon) {
  return {
    left: Math.floor(Math.min(...polygon.map(point => point[0]))),
    top: Math.floor(Math.min(...polygon.map(point => point[1]))),
    right: Math.ceil(Math.max(...polygon.map(point => point[0]))),
    bottom: Math.ceil(Math.max(...polygon.map(point => point[1]))),
  };
}

function mapPoint(point, transform) {
  return [
    transform.a * point[0] - transform.b * point[1] + transform.tx,
    transform.b * point[0] + transform.a * point[1] + transform.ty,
  ];
}

function inversePoint(point, transform) {
  const denominator = transform.a * transform.a + transform.b * transform.b;
  const x = point[0] - transform.tx;
  const y = point[1] - transform.ty;
  return [(transform.a * x + transform.b * y) / denominator, (-transform.b * x + transform.a * y) / denominator];
}

function fitSimilarity(source, target) {
  assert(source.length === target.length && source.length >= 3, 'At least three paired landmarks are required.');
  const mean = points => points.reduce(
    (sum, point) => [sum[0] + point[0] / points.length, sum[1] + point[1] / points.length],
    [0, 0],
  );
  const sourceMean = mean(source);
  const targetMean = mean(target);
  let denominator = 0;
  let numeratorA = 0;
  let numeratorB = 0;
  source.forEach((point, index) => {
    const x = point[0] - sourceMean[0];
    const y = point[1] - sourceMean[1];
    const u = target[index][0] - targetMean[0];
    const v = target[index][1] - targetMean[1];
    denominator += x * x + y * y;
    numeratorA += x * u + y * v;
    numeratorB += x * v - y * u;
  });
  assert(denominator > 1e-8, 'Degenerate landmark configuration.');
  const a = numeratorA / denominator;
  const b = numeratorB / denominator;
  const transform = {
    a,
    b,
    tx: targetMean[0] - a * sourceMean[0] + b * sourceMean[1],
    ty: targetMean[1] - b * sourceMean[0] - a * sourceMean[1],
  };
  transform.scale = Math.hypot(a, b);
  transform.rotationDegrees = Math.atan2(b, a) * 180 / Math.PI;
  transform.residual = Math.sqrt(source.reduce((sum, point, index) => {
    const mapped = mapPoint(point, transform);
    return sum + (mapped[0] - target[index][0]) ** 2 + (mapped[1] - target[index][1]) ** 2;
  }, 0) / source.length);
  const eyeDistance = Math.hypot(target[0][0] - target[1][0], target[0][1] - target[1][1]);
  transform.normalizedResidual = transform.residual / eyeDistance;
  assert(transform.scale > 0 && Number.isFinite(transform.normalizedResidual), 'Invalid transform.');
  return transform;
}

function sampleRgb(source, x, y) {
  const { data, info } = source;
  assert(x >= 0 && y >= 0 && x <= info.width - 1 && y <= info.height - 1, 'Face patch extends beyond source.');
  const x0 = Math.floor(x);
  const y0 = Math.floor(y);
  const x1 = Math.min(x0 + 1, info.width - 1);
  const y1 = Math.min(y0 + 1, info.height - 1);
  const fx = x - x0;
  const fy = y - y0;
  return [0, 1, 2].map(channel => Math.round(
    data[(y0 * info.width + x0) * 3 + channel] * (1 - fx) * (1 - fy)
      + data[(y0 * info.width + x1) * 3 + channel] * fx * (1 - fy)
      + data[(y1 * info.width + x0) * 3 + channel] * (1 - fx) * fy
      + data[(y1 * info.width + x1) * 3 + channel] * fx * fy,
  ));
}

function boxBlurRgb(data, width, height, radius, valid) {
  const roundedRadius = Math.max(1, Math.round(radius));
  const stride = width + 1;
  const size = (width + 1) * (height + 1);
  const sums = [new Float64Array(size), new Float64Array(size), new Float64Array(size)];
  const counts = new Uint32Array(size);
  for (let y = 0; y < height; y += 1) for (let x = 0; x < width; x += 1) {
    const sourceIndex = y * width + x;
    const targetIndex = (y + 1) * stride + x + 1;
    const enabled = !valid || valid[sourceIndex];
    counts[targetIndex] = counts[targetIndex - 1] + counts[targetIndex - stride] - counts[targetIndex - stride - 1] + (enabled ? 1 : 0);
    for (let channel = 0; channel < 3; channel += 1) {
      sums[channel][targetIndex] = sums[channel][targetIndex - 1] + sums[channel][targetIndex - stride]
        - sums[channel][targetIndex - stride - 1] + (enabled ? data[sourceIndex * 3 + channel] : 0);
    }
  }
  const output = new Float32Array(width * height * 3);
  for (let y = 0; y < height; y += 1) for (let x = 0; x < width; x += 1) {
    const x0 = Math.max(0, x - roundedRadius);
    const y0 = Math.max(0, y - roundedRadius);
    const x1 = Math.min(width - 1, x + roundedRadius);
    const y1 = Math.min(height - 1, y + roundedRadius);
    const a = y0 * stride + x0;
    const b = y0 * stride + x1 + 1;
    const d = (y1 + 1) * stride + x0;
    const e = (y1 + 1) * stride + x1 + 1;
    const count = counts[e] - counts[b] - counts[d] + counts[a];
    if (!count) continue;
    for (let channel = 0; channel < 3; channel += 1) {
      output[(y * width + x) * 3 + channel] = (sums[channel][e] - sums[channel][b] - sums[channel][d] + sums[channel][a]) / count;
    }
  }
  return output;
}

function harmonizePatch(patch, target, strength, radius) {
  const valid = Buffer.alloc(patch.width * patch.height);
  for (let index = 0; index < valid.length; index += 1) valid[index] = patch.rgba[index * 4 + 3] > 0 ? 1 : 0;
  const sourceLow = boxBlurRgb(patch.reference, patch.width, patch.height, radius, valid);
  const targetLow = boxBlurRgb(target, patch.width, patch.height, radius);
  const output = Buffer.from(patch.rgba);
  for (let index = 0; index < valid.length; index += 1) {
    if (!valid[index]) continue;
    for (let channel = 0; channel < 3; channel += 1) {
      const shifted = patch.reference[index * 3 + channel]
        + strength * (targetLow[index * 3 + channel] - sourceLow[index * 3 + channel]);
      output[index * 4 + channel] = Math.max(0, Math.min(255, Math.round(shifted)));
    }
  }
  return output;
}

module.exports = {
  assert, bounds, distance, fitSimilarity, fs, harmonizePatch, hashFile, inside, inversePoint, mapPoint,
  parseArgs, path, polygonValid, readJson, resolveFrom, sampleRgb, sharp, writeJson,
};
