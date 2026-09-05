"""Locate facial landmarks locally; do not identify, synthesize, or retouch people."""
import argparse
import hashlib
import io
import json
import os
from pathlib import Path

OVAL = [10,338,297,332,284,251,389,356,454,323,361,288,397,365,379,378,400,377,152,148,176,149,150,136,172,58,132,93,234,127,162,21,54,103,67,109]


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--max-faces', type=int, default=4)
    parser.add_argument('--expected-faces', type=int)
    parser.add_argument('--max-edge', type=int, default=2800)
    parser.add_argument('--roi', help='Optional x,y,width,height in oriented source pixels for distant faces.')
    args = parser.parse_args()
    if args.out.exists():
        parser.error('Output already exists; use a new detection filename.')
    if not 1 <= args.max_faces <= 10 or args.max_edge < 640:
        parser.error('max-faces must be 1..10 and max-edge >= 640.')
    args.out.parent.mkdir(parents=True, exist_ok=True)
    os.environ.setdefault('MPLCONFIGDIR', str(args.out.parent.resolve() / '.matplotlib'))
    import mediapipe as mp
    import numpy as np
    from PIL import Image, ImageCms, ImageDraw, ImageOps
    from mediapipe.tasks import python
    from mediapipe.tasks.python import vision
    manifest_path = Path(__file__).resolve().parents[2] / 'assets' / 'face-harmonization-model.json'
    manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
    model = manifest_path.parent / manifest['file']
    if sha256(model) != manifest['sha256']:
        raise ValueError('Model checksum mismatch.')
    with Image.open(args.input) as opened:
        source = ImageOps.exif_transpose(opened).convert('RGB')
        icc = opened.info.get('icc_profile')
        if icc:
            source = ImageCms.profileToProfile(source, ImageCms.ImageCmsProfile(io.BytesIO(icc)), ImageCms.createProfile('sRGB'), outputMode='RGB')
    width, height = source.size
    roi = [0, 0, width, height]
    if args.roi:
        roi = [int(v) for v in args.roi.split(',')]
        if len(roi) != 4 or min(roi) < 0 or min(roi[2:]) < 32 or roi[0]+roi[2] > width or roi[1]+roi[3] > height:
            parser.error('ROI must be x,y,width,height inside the oriented original image.')
    reduced = source.crop((roi[0], roi[1], roi[0]+roi[2], roi[1]+roi[3]))
    reduced.thumbnail((args.max_edge, args.max_edge), Image.Resampling.LANCZOS)
    options = vision.FaceLandmarkerOptions(
        base_options=python.BaseOptions(model_asset_path=str(model)),
        running_mode=vision.RunningMode.IMAGE,
        num_faces=args.max_faces,
        min_face_detection_confidence=0.5,
        min_face_presence_confidence=0.5,
        output_face_blendshapes=False,
        output_facial_transformation_matrixes=False,
    )
    with vision.FaceLandmarker.create_from_options(options) as detector:
        result = detector.detect(mp.Image(image_format=mp.ImageFormat.SRGB, data=np.asarray(reduced)))
    faces = []
    for landmarks in result.face_landmarks:
        points = [[round(roi[0] + p.x * roi[2], 4), round(roi[1] + p.y * roi[3], 4)] for p in landmarks]
        oval = [points[i] for i in OVAL]
        xs, ys = zip(*oval)
        face_width, face_height = max(xs)-min(xs), max(ys)-min(ys)
        crop = {
            'x': max(0, int(min(xs) - face_width * .28)),
            'y': max(0, int(min(ys) - face_height * .45)),
            'right': min(width, int(max(xs) + face_width * .28) + 1),
            'bottom': min(height, int(max(ys) + face_height * .25) + 1),
        }
        faces.append({'landmarks': points, 'corePolygon': oval, 'cropSuggestion': crop,
                      'anchors': [points[33], points[263], points[1]],
                      'center': [sum(xs)/len(xs), sum(ys)/len(ys)]})
    # Position order is only a label for visual review, never an identity match.
    faces.sort(key=lambda f: f['center'][0])
    for i, face in enumerate(faces):
        face['id'] = 'face-' + str(i+1)
    payload = {'schemaVersion': 1, 'input': str(args.input.resolve()), 'inputSha256': sha256(args.input),
               'image': {'width': width, 'height': height, 'coordinates': 'exif-oriented-source-pixels'},
               'detector': {'name': 'MediaPipe Face Landmarker', 'version': mp.__version__, 'modelSha256': manifest['sha256']},
               'detectionRoi': roi, 'faces': faces, 'identityMappingReviewed': False}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding='utf-8')
    preview = source.copy()
    preview.thumbnail((1600, 2400), Image.Resampling.LANCZOS)
    draw = ImageDraw.Draw(preview)
    sx, sy = preview.width/width, preview.height/height
    for face in faces:
        poly = [(x*sx,y*sy) for x,y in face['corePolygon']]
        draw.line(poly + poly[:1], fill='#00ffff', width=3)
        box = face['cropSuggestion']
        draw.rectangle((box['x']*sx,box['y']*sy,box['right']*sx,box['bottom']*sy), outline='#ffcc00', width=2)
        draw.text((box['x']*sx, max(0,box['y']*sy-16)), face['id'], fill='#ffcc00')
    preview.save(args.out.with_suffix('.preview.jpg'), quality=92)
    print(json.dumps({'faces': len(faces), 'output': str(args.out)}, ensure_ascii=False))
    if not faces or (args.expected_faces is not None and len(faces) != args.expected_faces):
        raise SystemExit('Face count mismatch. Inspect the preview; do not assume detection succeeded.')


if __name__ == '__main__':
    main()
