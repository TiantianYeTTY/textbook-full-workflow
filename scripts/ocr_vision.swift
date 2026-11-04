// Designed by TiantianYe
// ocr_vision.swift —— macOS Vision 框架中文 OCR（Skill: textbook-full-workflow 第 2 步扫描版入口）
//
// 原理：CoreGraphics 把 PDF 每页渲染为位图（默认 4 倍 ≈ 288DPI），
//       Vision VNRecognizeTextRequest(.accurate + zh-Hans + 语言纠错) 逐页识别，
//       输出带 `===== [PDF第N页] =====` 页标的全文，供后续 AI 分批精读。
//
// 实测：386 页中文扫描书（约 23 万字）≈150 秒，目录/正文识别质量高；
//       tesseract 无 chi_sim 语言包时，这是 macOS 上中文 OCR 的最优路线。
//
// 依赖：Xcode Command Line Tools（swiftc 编译）。一般由 ocr_book.py 包装调用，
//       手动使用方法：
//         swiftc -O ocr_vision.swift -o ocr_vision
//         ./ocr_vision <输入.pdf> <输出.txt> [起始页] [结束页] [渲染倍率]
//       页码为 1 起始的 PDF 物理页号；不传起止页则跑全书。
// 适配：若原书为繁体/中英混排，recognitionLanguages 已同时声明 zh-Hans、zh-Hant；
//       英文书可改为 ["en-US"]。

import Foundation
import CoreGraphics
import Vision

let args = CommandLine.arguments
guard args.count >= 3 else {
    print("用法: ocr_vision <pdf路径> <输出txt路径> [起始页] [结束页] [渲染倍率]")
    exit(1)
}
let pdfPath = args[1]
let outPath = args[2]
let startPage = args.count > 3 ? Int(args[3]) ?? 1 : 1
let endPage = args.count > 4 ? Int(args[4]) ?? 0 : 0
let scale = args.count > 5 ? Double(args[5])! : 4.0

let url = URL(fileURLWithPath: pdfPath) as CFURL
guard let doc = CGPDFDocument(url) else {
    print("无法打开 PDF: \(pdfPath)")
    exit(1)
}
let n = doc.numberOfPages
let last = (endPage > 0 && endPage <= n) ? endPage : n
let first = max(1, startPage)
print("总页数: \(n), 本次识别: \(first)-\(last) 页, 渲染倍率: \(scale)")

func ocrPage(_ cg: CGImage) -> String {
    let req = VNRecognizeTextRequest()
    req.recognitionLevel = .accurate
    req.recognitionLanguages = ["zh-Hans", "zh-Hant"]
    req.usesLanguageCorrection = true
    let handler = VNImageRequestHandler(cgImage: cg, options: [:])
    do {
        try handler.perform([req])
    } catch {
        return "<<OCR错误: \(error.localizedDescription)>>"
    }
    return (req.results ?? []).compactMap { $0.topCandidates(1).first?.string }.joined(separator: "\n")
}

var full = ""
full.reserveCapacity(1 << 23)
let start = Date()

for i in first...last {
    guard let page = doc.page(at: i) else { continue }
    let box = page.getBoxRect(.mediaBox)
    let w = Int(box.width * scale)
    let h = Int(box.height * scale)
    let cs = CGColorSpaceCreateDeviceRGB()
    guard let ctx = CGContext(data: nil, width: w, height: h, bitsPerComponent: 8, bytesPerRow: 0,
                              space: cs, bitmapInfo: CGImageAlphaInfo.premultipliedLast.rawValue) else { continue }
    ctx.setFillColor(CGColor(red: 1, green: 1, blue: 1, alpha: 1))
    ctx.fill(CGRect(x: 0, y: 0, width: CGFloat(w), height: CGFloat(h)))
    ctx.scaleBy(x: CGFloat(scale), y: CGFloat(scale))
    ctx.translateBy(x: -box.minX, y: -box.minY)
    ctx.drawPDFPage(page)
    guard let img = ctx.makeImage() else { continue }
    let text = ocrPage(img)
    full += "===== [PDF第\(i)页] =====\n\(text)\n\n"
    if (i - first + 1) % 10 == 0 || i == last {
        let done = Double(i - first + 1)
        let elapsed = Date().timeIntervalSince(start)
        let eta = elapsed / done * Double(last - i)
        print("进度 \(i - first + 1)/\(last - first + 1) 已用\(Int(elapsed))s 预计剩余\(Int(eta))s")
        fflush(stdout)
    }
}

try! full.write(toFile: outPath, atomically: true, encoding: .utf8)
print("DONE 共识别\(last - first + 1)页, 输出\(full.count)字符")
