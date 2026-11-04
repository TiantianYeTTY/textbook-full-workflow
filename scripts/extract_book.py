# Designed by TiantianYe
#!/usr/bin/env python3
"""
extract_book.py —— 教科书 PDF 文本提取与规范化（Skill: textbook-full-workflow 第 1 步）

用途：
    把用户提供的教科书 PDF 提取为带页码标记的规范化全文文本，供 AI 分批精读。

适配指南（换书/换环境时检查这里）：
    1. CHAR_MAP 是本类扫描版教材常见的 PUA/异体编码映射，遇到新书先扫描一遍
       非常规字符（main 里的 odd-scan 逻辑），把新字符加进 CHAR_MAP 再重跑。
    2. 全角→半角 + "数字间 PUA→小数点" 是通用清洗，无需改。
    3. PYTHON 路径按本机环境修改（默认适配 WorkBuddy 内置 Python）。

用法：
    python3 extract_book.py <输入PDF> <输出txt>
示例：
    python3 extract_book.py "概率论与数理统计.pdf" /tmp/book_full.txt
"""
import sys
import re

try:
    import pymupdf
except ImportError:
    sys.exit("缺少 pymupdf：pip install pymupdf")

# 已知异体/私用区字符映射（源自《概率论与数理统计》同济版实测；换书先扫描再补充）
# ⚠ 注意：\U 转义必须正好 8 位十六进制。'\U0001001b0' 是错误写法（Python 只取
#   0001001b 共 8 位 + 字面 '0'），导致映射永不匹配——本项目曾因此潜伏（靠下游
#   容错正则掩盖），写映射时对照扫描报告逐个确认 code point。
CHAR_MAP = {
    '\ua3ac': '，',      # 全角逗号异体
    '\ua3bb': '；',      # 全角分号异体
    '\U001001b0': '。',  # 全角句号（U+1001B0）
    '\U001001ba': '…',   # 省略号（U+1001BA）
    '\U00100170': '.',   # 小数点（U+100170）
    '\U00100a85': '⇒',  # 推导符号（U+100A85）
    '\uf0a8': '≈',
}

# 全角 → 半角
FW_MAP = {}
for i in range(10):
    FW_MAP[chr(0xFF10 + i)] = str(i)
for i in range(26):
    FW_MAP[chr(0xFF21 + i)] = chr(65 + i)
    FW_MAP[chr(0xFF41 + i)] = chr(97 + i)
for a, b in [('．', '.'), ('（', '('), ('）', ')'), ('，', ','), ('：', ':'),
             ('～', '~'), ('－', '-'), ('＋', '+'), ('／', '/'), ('＝', '='),
             ('％', '%'), ('＿', '_'), ('　', ' ')]:
    FW_MAP[a] = b

# ⚠ \U 转义必须正好 8 位十六进制：'\U00010000-\U0010FFFF'。此前误写为
#   '\U000100000-\U0010FFFF'（多一个 0），剩余字面 '0' 与 '-' 组成范围
#   U+0030-U+10FFFF，导致所有数字间的数字被替换成小数点（1024→1..4）。
PUA_RANGE = r'\uE000-\uF8FF\U00010000-\U0010FFFF'


def clean(text: str) -> str:
    for k, v in CHAR_MAP.items():
        text = text.replace(k, v)
    text = text.translate(str.maketrans(FW_MAP))
    # 数字之间的 PUA 字符 → 小数点（扫描版教材常见）
    text = re.sub(rf'(?<=\d)[{PUA_RANGE}](?=\d)', '.', text)
    return text


def main():
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    src, dst = sys.argv[1], sys.argv[2]
    doc = pymupdf.open(src)
    out = []
    for i, page in enumerate(doc):
        out.append(f"\n===== [PDF第{i+1}页] =====\n")
        out.append(clean(page.get_text()))
    text = ''.join(out)
    with open(dst, 'w', encoding='utf-8') as f:
        f.write(text)
    print(f"页数: {len(doc)} | 字符数: {len(text)} | 输出: {dst}")
    # 附：私用区字符扫描报告（只报 PUA 平面——标准数学符号 ∞∑≤∫ 是正常 Unicode 无需映射；
    # 换新书时重点看这里有没有漏网编码字符）
    import collections
    odd = collections.Counter()
    for ch in text:
        o = ord(ch)
        if 0xE000 <= o <= 0xF8FF or 0x100000 <= o <= 0x10FFFF:
            odd[ch] += 1
    if odd:
        print("⚠ 私用区/Plane1 编码字符（需人工确认是否加入 CHAR_MAP）：")
        for ch, n in odd.most_common(20):
            print(f"   U+{ord(ch):05X} {ch!r} × {n}")
    else:
        print("✓ 无残留私用区编码字符")


if __name__ == '__main__':
    main()
