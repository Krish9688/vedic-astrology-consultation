// Local OCR via macOS Vision. Usage: ocr <image.png> [lang, default en-US]
import Vision
import AppKit
let url = URL(fileURLWithPath: CommandLine.arguments[1])
let lang = CommandLine.arguments.count > 2 ? CommandLine.arguments[2] : "en-US"
guard let img = NSImage(contentsOf: url), let cg = img.cgImage(forProposedRect: nil, context: nil, hints: nil) else { exit(1) }
let req = VNRecognizeTextRequest()
req.recognitionLevel = .accurate
req.recognitionLanguages = [lang]
req.usesLanguageCorrection = false  // keep Sanskrit terms as printed
try VNImageRequestHandler(cgImage: cg).perform([req])
for o in req.results ?? [] { print(o.topCandidates(1).first?.string ?? "") }
