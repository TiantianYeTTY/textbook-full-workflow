# Designed by TiantianYe
#!/usr/bin/env python3
"""
watermark_verify.py —— PDF 加水印 + 交付前强制验证（Skill: textbook-review-pdfs 第 5 步）

职责（两件事一次做完，缺一不可交付）：
    1. 给每页 PDF 上方加 "Designed by TiantianYe" 水印（pymupdf 后处理，位置稳定可验证）；
    2. 强制验证四项，任何一项 FAIL 都不允许交付：
       ① 每页水印存在  ② 内容超界（右边界）  ③ LaTeX 渲染残留  ④ 页数输出。

适配指南（换环境时检查这里）：
    1. WATERMARK 文本、字号、颜色可按需调整；默认置于上边距区（y≈20pt，页边距 13mm≈37pt，不压正文）。
    2. RESIDUE_PATTERNS 是 KaTeX 渲染失败的典型残留，新书如出现新的公式形态可补充。
    3. 边距假设 11mm≈31.2pt：若改了 build_pdfs.mjs 的 @page margin，这里要同步。

用法：
    python3 watermark_verify.py <输入.pdf> <输出.pdf>   # 就地验证 + 写出水印版
示例：
    python3 watermark_verify.py ./背诵合集_raw.pdf ./背诵合集.pdf
退出码：0=全部通过可交付；1=存在 FAIL 禁止交付。
"""
import sys
import re

try:
    import pymupdf
except ImportError:
    sys.exit("缺少 pymupdf：pip install pymupdf")

WATERMARK = "Designed by TiantianYe"
WATERMARK_SIZE = 7.5
WATERMARK_COLOR = (0.45, 0.5, 0.58)   # 中性灰蓝，醒目不抢正文

# KaTeX 渲染失败的典型残留（出现即说明该公式没有渲染成数学排版）
RESIDUE_PATTERNS = [
    '\\dfrac', '\\frac{', '\\bar{', '\\hat{', '\\overline', '\\sum\\limits',
    '\\int\\limits', '\\Longrightarrow', '\\lvert', '\\begin{', '\\chi^2_',
    'MATHSLOT', '_DONE', 'file:///', 'KATEX_ERROR',
]


def add_watermark(doc):
    for page in doc:
        w = page.rect.width
        page.insert_text(
            pymupdf.Point(w / 2 - 52, 20),          # 顶部居中（文本宽约 104pt @7.5pt 字号）
            WATERMARK,
            fontsize=WATERMARK_SIZE,
            color=WATERMARK_COLOR,
        )


def verify(doc, margin_right_pt=31.2, tolerance=2.0):
    fails = []

    # ① 每页水印存在
    missing = [i + 1 for i, page in enumerate(doc) if WATERMARK not in page.get_text()]
    if missing:
        fails.append(f"水印缺失页: {missing}")

    # ② 内容超界（右边界；水印本身在顶部中央，不影响右界检测）
    limit = 595 - margin_right_pt + tolerance   # A4 宽 595pt
    over = [(p + 1, round(b[2], 1))
            for p, page in enumerate(doc) for b in page.get_text('blocks') if b[2] > limit]
    if over:
        fails.append(f"内容超界 {len(over)} 处: {over[:8]}")

    # ③ LaTeX 渲染残留
    resid = []
    for i, page in enumerate(doc):
        t = page.get_text()
        for bad in RESIDUE_PATTERNS:
            if bad in t:
                resid.append((i + 1, bad))
    if resid:
        fails.append(f"LaTeX 残留 {len(resid)} 处: {resid[:8]}")

    return fails


def main():
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    src, dst = sys.argv[1], sys.argv[2]
    doc = pymupdf.open(src)
    add_watermark(doc)
    fails = verify(doc)
    doc.save(dst)
    print(f"页数: {len(doc)} | 输出: {dst}")
    if fails:
        print("✗ 验证未通过，禁止交付：")
        for f in fails:
            print("   -", f)
        sys.exit(1)
    print("✓ 验证全部通过（水印✓ / 超界 0 / 残留 0），可交付")


if __name__ == '__main__':
    main()
