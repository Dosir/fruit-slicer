// 把单个 emoji 渲染成带透明背景的 PNG（用于游戏里的真实水果贴图）。
// 用法: swift tools/render_emoji.swift <emoji> <输出路径>
import AppKit

let args = CommandLine.arguments
guard args.count == 3 else {
    FileHandle.standardError.write("用法: render_emoji.swift <emoji> <out.png>\n".data(using: .utf8)!)
    exit(1)
}
let emoji = args[1]
let outPath = args[2]

let size = 512
let fontSize: CGFloat = 400

guard let rep = NSBitmapImageRep(
    bitmapDataPlanes: nil, pixelsWide: size, pixelsHigh: size,
    bitsPerSample: 8, samplesPerPixel: 4, hasAlpha: true, isPlanar: false,
    colorSpaceName: .deviceRGB, bytesPerRow: 0, bitsPerPixel: 0
) else {
    FileHandle.standardError.write("无法创建位图\n".data(using: .utf8)!)
    exit(1)
}

NSGraphicsContext.saveGraphicsState()
NSGraphicsContext.current = NSGraphicsContext(bitmapImageRep: rep)

let font = NSFont.systemFont(ofSize: fontSize)
let attrs: [NSAttributedString.Key: Any] = [.font: font]
let str = NSAttributedString(string: emoji, attributes: attrs)
let s = str.size()
let x = (CGFloat(size) - s.width) / 2
let y = (CGFloat(size) - s.height) / 2
str.draw(at: NSPoint(x: x, y: y))

NSGraphicsContext.restoreGraphicsState()

guard let png = rep.representation(using: .png, properties: [:]) else {
    FileHandle.standardError.write("PNG 编码失败\n".data(using: .utf8)!)
    exit(1)
}
try! png.write(to: URL(fileURLWithPath: outPath))
print("已生成 \(outPath)")
