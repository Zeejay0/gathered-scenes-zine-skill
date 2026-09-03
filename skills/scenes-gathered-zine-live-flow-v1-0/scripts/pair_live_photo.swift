#!/usr/bin/env swift

import Foundation
import AVFoundation
import CoreMedia
import ImageIO
import UniformTypeIdentifiers

struct Options {
    let image: URL
    let video: URL
    let outDir: URL
    let keyTime: Double
    let identifier: String
}

enum PairError: Error, CustomStringConvertible {
    case usage(String)
    case failed(String)

    var description: String {
        switch self {
        case .usage(let message), .failed(let message): return message
        }
    }
}

func parseOptions() throws -> Options {
    var values: [String: String] = [:]
    var index = 1
    while index < CommandLine.arguments.count {
        let key = CommandLine.arguments[index]
        guard key.hasPrefix("--"), index + 1 < CommandLine.arguments.count else {
            throw PairError.usage("Usage: pair_live_photo.swift --image key.jpg --video motion.mov --out-dir output [--key-time 1.5] [--identifier UUID]")
        }
        values[key] = CommandLine.arguments[index + 1]
        index += 2
    }
    guard let image = values["--image"], let video = values["--video"], let outDir = values["--out-dir"] else {
        throw PairError.usage("Missing --image, --video, or --out-dir")
    }
    let keyTime = Double(values["--key-time"] ?? "1.5") ?? 1.5
    let identifier = values["--identifier"] ?? UUID().uuidString.uppercased()
    return Options(
        image: URL(fileURLWithPath: NSString(string: image).expandingTildeInPath),
        video: URL(fileURLWithPath: NSString(string: video).expandingTildeInPath),
        outDir: URL(fileURLWithPath: NSString(string: outDir).expandingTildeInPath, isDirectory: true),
        keyTime: keyTime,
        identifier: identifier
    )
}

func writePairedJPEG(sourceURL: URL, destinationURL: URL, identifier: String) throws {
    guard let source = CGImageSourceCreateWithURL(sourceURL as CFURL, nil),
          let image = CGImageSourceCreateImageAtIndex(source, 0, nil) else {
        throw PairError.failed("Unable to read key image: \(sourceURL.path)")
    }
    var properties = (CGImageSourceCopyPropertiesAtIndex(source, 0, nil) as? [String: Any]) ?? [:]
    var makerApple = properties[kCGImagePropertyMakerAppleDictionary as String] as? [String: Any] ?? [:]
    makerApple["17"] = identifier
    properties[kCGImagePropertyMakerAppleDictionary as String] = makerApple
    properties[kCGImageDestinationLossyCompressionQuality as String] = 0.96

    guard let destination = CGImageDestinationCreateWithURL(
        destinationURL as CFURL,
        UTType.jpeg.identifier as CFString,
        1,
        nil
    ) else {
        throw PairError.failed("Unable to create paired JPEG")
    }
    CGImageDestinationAddImage(destination, image, properties as CFDictionary)
    guard CGImageDestinationFinalize(destination) else {
        throw PairError.failed("Unable to finalize paired JPEG")
    }
}

func contentIdentifierItem(_ identifier: String) -> AVMetadataItem {
    let item = AVMutableMetadataItem()
    item.keySpace = .quickTimeMetadata
    item.key = AVMetadataKey.quickTimeMetadataKeyContentIdentifier as NSString
    item.value = identifier as NSString
    item.dataType = kCMMetadataBaseDataType_UTF8 as String
    return item
}

func makeStillTimeAdaptor(writer: AVAssetWriter) throws -> AVAssetWriterInputMetadataAdaptor {
    let specification: NSDictionary = [
        kCMMetadataFormatDescriptionMetadataSpecificationKey_Identifier as String:
            "mdta/com.apple.quicktime.still-image-time",
        kCMMetadataFormatDescriptionMetadataSpecificationKey_DataType as String:
            kCMMetadataBaseDataType_SInt8 as String,
    ]
    var description: CMMetadataFormatDescription?
    let status = CMMetadataFormatDescriptionCreateWithMetadataSpecifications(
        allocator: kCFAllocatorDefault,
        metadataType: kCMMetadataFormatType_Boxed,
        metadataSpecifications: [specification] as CFArray,
        formatDescriptionOut: &description
    )
    guard status == noErr, let formatDescription = description else {
        throw PairError.failed("Unable to create still-image-time metadata description (\(status))")
    }
    let input = AVAssetWriterInput(mediaType: .metadata, outputSettings: nil, sourceFormatHint: formatDescription)
    input.expectsMediaDataInRealTime = false
    guard writer.canAdd(input) else {
        throw PairError.failed("Asset writer cannot add still-image-time metadata")
    }
    writer.add(input)
    return AVAssetWriterInputMetadataAdaptor(assetWriterInput: input)
}

func copyTrack(_ track: AVAssetTrack, mediaType: AVMediaType, reader: AVAssetReader,
               writer: AVAssetWriter) throws -> (AVAssetReaderTrackOutput, AVAssetWriterInput) {
    let output = AVAssetReaderTrackOutput(track: track, outputSettings: nil)
    output.alwaysCopiesSampleData = false
    guard reader.canAdd(output) else { throw PairError.failed("Reader cannot add \(mediaType.rawValue) track") }
    reader.add(output)
    let hint = track.formatDescriptions.first.map { $0 as! CMFormatDescription }
    let input = AVAssetWriterInput(mediaType: mediaType, outputSettings: nil, sourceFormatHint: hint)
    input.expectsMediaDataInRealTime = false
    guard writer.canAdd(input) else { throw PairError.failed("Writer cannot add \(mediaType.rawValue) track") }
    writer.add(input)
    return (output, input)
}

func writePairedMovie(sourceURL: URL, destinationURL: URL, identifier: String, keyTime: Double) throws {
    let asset = AVURLAsset(url: sourceURL)
    let reader = try AVAssetReader(asset: asset)
    let writer = try AVAssetWriter(outputURL: destinationURL, fileType: .mov)
    writer.metadata = [contentIdentifierItem(identifier)]

    guard let videoTrack = asset.tracks(withMediaType: .video).first else {
        throw PairError.failed("Input MOV has no video track")
    }
    let videoPair = try copyTrack(videoTrack, mediaType: .video, reader: reader, writer: writer)
    var audioPair: (AVAssetReaderTrackOutput, AVAssetWriterInput)?
    if let audioTrack = asset.tracks(withMediaType: .audio).first {
        audioPair = try copyTrack(audioTrack, mediaType: .audio, reader: reader, writer: writer)
    }
    let metadataAdaptor = try makeStillTimeAdaptor(writer: writer)

    guard writer.startWriting() else {
        throw PairError.failed("Unable to start movie writer: \(writer.error?.localizedDescription ?? "unknown error")")
    }
    guard reader.startReading() else {
        throw PairError.failed("Unable to start movie reader: \(reader.error?.localizedDescription ?? "unknown error")")
    }
    writer.startSession(atSourceTime: .zero)

    let stillItem = AVMutableMetadataItem()
    stillItem.keySpace = .quickTimeMetadata
    stillItem.key = "com.apple.quicktime.still-image-time" as NSString
    stillItem.value = NSNumber(value: Int8(0))
    stillItem.dataType = kCMMetadataBaseDataType_SInt8 as String
    let frameDuration = CMTime(value: 1, timescale: 30)
    let start = CMTime(seconds: keyTime, preferredTimescale: 600)
    let group = AVTimedMetadataGroup(items: [stillItem], timeRange: CMTimeRange(start: start, duration: frameDuration))
    guard metadataAdaptor.append(group) else {
        throw PairError.failed("Unable to append still-image-time metadata")
    }
    metadataAdaptor.assetWriterInput.markAsFinished()

    let completion = DispatchGroup()
    let queue = DispatchQueue(label: "live-photo-pairing")

    func pump(_ output: AVAssetReaderTrackOutput, _ input: AVAssetWriterInput) {
        completion.enter()
        input.requestMediaDataWhenReady(on: queue) {
            while input.isReadyForMoreMediaData {
                if let sample = output.copyNextSampleBuffer() {
                    if !input.append(sample) {
                        input.markAsFinished()
                        completion.leave()
                        return
                    }
                } else {
                    input.markAsFinished()
                    completion.leave()
                    return
                }
            }
        }
    }

    pump(videoPair.0, videoPair.1)
    if let pair = audioPair { pump(pair.0, pair.1) }
    completion.wait()

    guard reader.status == .completed else {
        writer.cancelWriting()
        throw PairError.failed("Movie reader failed: \(reader.error?.localizedDescription ?? "unknown error")")
    }
    let finish = DispatchSemaphore(value: 0)
    writer.finishWriting { finish.signal() }
    finish.wait()
    guard writer.status == .completed else {
        throw PairError.failed("Movie writer failed: \(writer.error?.localizedDescription ?? "unknown error")")
    }
}

do {
    let options = try parseOptions()
    let fileManager = FileManager.default
    guard fileManager.fileExists(atPath: options.image.path) else { throw PairError.failed("Image does not exist") }
    guard fileManager.fileExists(atPath: options.video.path) else { throw PairError.failed("Video does not exist") }
    try fileManager.createDirectory(at: options.outDir, withIntermediateDirectories: true)
    let stem = "LIVE_" + options.identifier.replacingOccurrences(of: "-", with: "").prefix(12)
    let imageOutput = options.outDir.appendingPathComponent("\(stem).JPG")
    let videoOutput = options.outDir.appendingPathComponent("\(stem).MOV")
    try? fileManager.removeItem(at: imageOutput)
    try? fileManager.removeItem(at: videoOutput)
    try writePairedJPEG(sourceURL: options.image, destinationURL: imageOutput, identifier: options.identifier)
    try writePairedMovie(sourceURL: options.video, destinationURL: videoOutput, identifier: options.identifier, keyTime: options.keyTime)
    let receipt: [String: Any] = [
        "asset_identifier": options.identifier,
        "key_time": options.keyTime,
        "photo": imageOutput.path,
        "paired_video": videoOutput.path,
    ]
    let receiptURL = options.outDir.appendingPathComponent("\(stem).json")
    let data = try JSONSerialization.data(withJSONObject: receipt, options: [.prettyPrinted, .sortedKeys])
    try data.write(to: receiptURL)
    print(String(data: data, encoding: .utf8)!)
} catch {
    fputs("error: \(error)\n", stderr)
    exit(1)
}
