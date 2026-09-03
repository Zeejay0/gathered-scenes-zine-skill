# Apple Live Photo Pairing

An Apple Live Photo is one Photos asset backed by two resources: a JPEG still image and a QuickTime MOV paired video.

## Required pairing

- Both resources must have identical pixel dimensions.
- Write the same asset identifier into the JPEG Maker Apple metadata and the MOV QuickTime content identifier.
- Add a timed `com.apple.quicktime.still-image-time` metadata sample to the MOV.
- For the v0.1 reveal, mark `2.7` seconds: the first exact frame of the final-poster hold.
- Encode the default MOV as H.264, `yuv420p`, 30 fps, with no audio.
- Derive the JPEG from that exact final frame; do not generate or redesign it separately.

Use `scripts/pair_live_photo.swift`. It emits a paired `.JPG`, `.MOV`, and an internal JSON receipt sharing one UUID.

## Delivery

Place only the paired JPG and MOV in the delivery ZIP. Keep the JSON receipt outside the ZIP. Transfers that recompress either resource may destroy the relationship.

Do not silently import into the user's Photos library. A reliable authorized import uses one `PHAssetCreationRequest` with the still added as `.photo` and the MOV as `.pairedVideo`. Validation and Photos import are separate explicit actions.
