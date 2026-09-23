import Foundation
import PDFKit
import Vision
import CoreGraphics

func fail(_ message: String) -> Never {
    FileHandle.standardError.write((message + "\n").data(using: .utf8)!)
    exit(1)
}

guard CommandLine.arguments.count > 1 else {
    fail("usage: ocr_pdf.swift <pdf> [scale]")
}
let pdfURL = URL(fileURLWithPath: CommandLine.arguments[1])
let scaleValue = CommandLine.arguments.count > 2 ? Double(CommandLine.arguments[2]) : 3.0
guard let scaleValue = scaleValue, scaleValue.isFinite, scaleValue > 0, scaleValue <= 6 else {
    fail("scale must be greater than 0 and at most 6")
}
let scale = CGFloat(scaleValue)
guard let doc = PDFDocument(url: pdfURL), doc.pageCount > 0, !doc.isLocked else {
    fail("cannot open readable, nonempty PDF")
}

// Buffer until every page succeeds: callers never receive a partial extraction.
var output = ["### FILE: \(pdfURL.lastPathComponent) | pages: \(doc.pageCount)"]
for i in 0..<doc.pageCount {
    guard let page = doc.page(at: i) else { fail("page \(i+1): cannot load") }
    let bounds = page.bounds(for: .mediaBox)
    let pixelWidth = bounds.width * scale
    let pixelHeight = bounds.height * scale
    guard pixelWidth.isFinite, pixelHeight.isFinite,
          pixelWidth >= 1, pixelHeight >= 1,
          pixelWidth * pixelHeight <= 60_000_000 else {
        fail("page \(i+1): invalid or oversized dimensions; try a lower scale")
    }
    let cs = CGColorSpaceCreateDeviceRGB()
    guard let ctx = CGContext(data: nil, width: Int(pixelWidth), height: Int(pixelHeight),
                              bitsPerComponent: 8, bytesPerRow: 0, space: cs,
                              bitmapInfo: CGImageAlphaInfo.premultipliedLast.rawValue) else {
        fail("page \(i+1): cannot create image context")
    }
    ctx.setFillColor(CGColor(gray: 1, alpha: 1))
    ctx.fill(CGRect(x: 0, y: 0, width: pixelWidth, height: pixelHeight))
    ctx.scaleBy(x: scale, y: scale)
    ctx.translateBy(x: -bounds.minX, y: -bounds.minY)
    page.draw(with: .mediaBox, to: ctx)
    guard let cgImage = ctx.makeImage() else { fail("page \(i+1): cannot render") }
    let request = VNRecognizeTextRequest()
    request.recognitionLevel = .accurate
    request.usesLanguageCorrection = true
    do {
        try VNImageRequestHandler(cgImage: cgImage, options: [:]).perform([request])
    } catch { fail("page \(i+1) OCR error: \(error)") }
    let observations = (request.results ?? []).sorted { a, b in
        if abs(a.boundingBox.midY - b.boundingBox.midY) > 0.012 {
            return a.boundingBox.midY > b.boundingBox.midY
        }
        return a.boundingBox.minX < b.boundingBox.minX
    }
    let lines = observations.compactMap { $0.topCandidates(1).first?.string }
        .filter { !$0.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty }
    guard !lines.isEmpty else {
        fail("page \(i+1): no recognized text; inspect original (including blank/diagram-only pages)")
    }
    output.append("--- page \(i+1) ---")
    output.append(contentsOf: lines)
}
print(output.joined(separator: "\n"))
