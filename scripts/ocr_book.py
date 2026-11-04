#!/usr/bin/env python3
# Designed by TiantianYe
"""
ocr_book.py —— 扫描版教科书 OCR 一键入口（Skill: textbook-full-workflow 第 2 步扫描版分支）

职责：
    1. 编译并缓存 scripts/ocr_vision.swift（macOS Vision 框架中文 OCR，依赖 Xcode CLT）；
    2. 调用二进制识别 PDF（支持页码范围，默认全书）；
    3. 复用 extract_book.py 的 clean() 做"全角→半角 / 私用区编码"规范化（与文本层
       提取产物格式完全一致，下游精读/校对流程无需感知来源差异）；
    4. 输出与 extract_book.py 相同的"漏网字符扫描报告"。

用法：
    python3 ocr_book.py <输入PDF> <输出txt> [起始页] [结束页] [渲染倍率]
    页码为 1 起始的 PDF 物理页号；起止页缺省时识别全书。
示例：
    python3 ocr_book.py "改革开放简史.pdf" book_full.txt          # 全书
    python3 ocr_book.py "改革开放简史.pdf" sample.txt 6 20        # 先抽 15 页试跑质检
依赖：
    Xcode Command Line Tools（swiftc）。检查：swiftc --version
    无 swiftc 环境的降级方案见 SKILL.md 第 2 步（tesseract + chi_sim）。
环境要求说明：
    渲染倍率默认 4.0（≈288DPI，实测中文识别质量与速度的最佳平衡点）。
    386 页中文扫描书约 150 秒；页数多时建议用 run_in_background 并轮询进度。
"""
import os
import re
import sys
import stat
import tempfile
import collections
import subprocess

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)
from extract_book import clean, PUA_RANGE  # 复用规范化逻辑，保证两种提取入口产物一致


def _swift_binary_path() -> str:
    """按 swift 源文件 mtime+size 哈希缓存编译产物，源码更新后自动重编译。"""
    src = os.path.join(SCRIPT_DIR, 'ocr_vision.swift')
    st = os.stat(src)
    key = f"{int(st.st_mtime)}-{st.st_size}"
    cache_dir = os.path.join(tempfile.gettempdir(), 'ocr_vision_build')
    os.makedirs(cache_dir, exist_ok=True)
    return os.path.join(cache_dir, f'ocr_vision_{key}')


def build_binary() -> str:
    bin_path = _swift_binary_path()
    if os.path.exists(bin_path) and os.access(bin_path, os.X_OK):
        return bin_path
    try:
        subprocess.run(['swiftc', '--version'], capture_output=True, check=True)
    except (FileNotFoundError, subprocess.CalledProcessError):
        sys.exit("✗ 未找到 swiftc（需 Xcode Command Line Tools：xcode-select --install）。\n"
                 "  降级方案见 SKILL.md 第 2 步：tesseract + chi_sim 语言包。")
    src = os.path.join(SCRIPT_DIR, 'ocr_vision.swift')
    print("编译 ocr_vision.swift ...")
    subprocess.run(['swiftc', '-O', src, '-o', bin_path], check=True)
    os.chmod(bin_path, os.stat(bin_path).st_mode | stat.S_IXUSR)
    print("编译完成:", bin_path)
    return bin_path


def main():
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    src, dst = sys.argv[1], sys.argv[2]
    extra = sys.argv[3:]
    bin_path = build_binary()
    raw_txt = os.path.join(tempfile.gettempdir(), 'ocr_vision_raw.txt')
    cmd = [bin_path, src, raw_txt] + extra
    subprocess.run(cmd, check=True)

    text = open(raw_txt, encoding='utf-8').read()
    text = clean(text)
    # 页标记统一为 extract_book.py 的格式；正则幂等（兼容 Swift 已带 ===== 包裹与裸页标两种形态）
    text = re.sub(r'(?:===== )?\[PDF第(\d+)页\](?: =====)?', r'===== [PDF第\1页] =====', text)
    with open(dst, 'w', encoding='utf-8') as f:
        f.write(text)
    pages = len(re.findall(r'===== \[PDF第\d+页\] =====', text))
    print(f"OCR 完成 | 识别页数: {pages} | 字符数: {len(text)} | 输出: {dst}")

    # 漏网字符扫描报告（与 extract_book.py 一致）
    odd = collections.Counter()
    for ch in text:
        o = ord(ch)
        if 0xE000 <= o <= 0xF8FF or 0x100000 <= o <= 0x10FFFF:
            odd[ch] += 1
    if odd:
        print("⚠ 私用区/Plane1 编码字符（需人工确认是否加入 extract_book.py 的 CHAR_MAP）：")
        for ch, n in odd.most_common(20):
            print(f"   U+{ord(ch):05X} {ch!r} × {n}")
    else:
        print("✓ 无残留私用区编码字符")


if __name__ == '__main__':
    main()
