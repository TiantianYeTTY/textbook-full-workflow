# Designed by TiantianYe
#!/usr/bin/env python3
"""
bare_math_scan.py —— Markdown 裸数学扫描器（Skill: textbook-full-workflow md 质检步）

职责：
    扫描 md 中所有"没包进 $...$/$$...$$ 的数学写法"，输出行号与命中详情。
    硬规则：交付前必须跑一遍且命中归零（数学零裸露），否则退回重写。
    依据：用户反馈 #2「还是有很多字母不是LaTeX数学格式的，我都需要LaTeX数学格式」。

适配指南：
    1. 白名单：标题分隔符 · 与流程箭头 → 属纯排版符号，已在最后过滤；
       换学科若正文合法使用其他单字符（如逻辑学 ∴），加入 WHITELIST。
    2. 检测器为启发式（希腊字母/上下标/运算符/P()/E()/N() 型函数记号/X_下标），
       命中后需人工逐条确认是否真为裸数学。

用法：
    python3 bare_math_scan.py <文档.md> [更多.md ...]
退出码：0=零裸数学；1=存在命中（禁止进入构建）。
"""
import re
import sys

GREEK = set('αβγδεζηθικλμνξπρστυφχψωΑΒΓΔΘΛΞΠΣΦΨΩ')
SUPSUB = set('⁰¹²³⁴⁵⁶⁷⁸⁹ⁿᵏᵢᵀ₀₁₂₃₄₅₆₇₈₉ₙⱼᵤᵥᵣₖₗₘₚₛₜᵅᵝᵞᶿᵡ')
OPS = set('±×÷≤≥≠≈∪∩∈∉⊂⊆∅∞√∫∏·∼⇒⇔−̄̂')
# 纯排版符号白名单：标题分隔符 · 与流程箭头 →（非数学内容）
WHITELIST = {'·', '→'}
# 已知基线：本项目定稿教学文档存在 2 处中文散文用法（"÷ 列和"比喻、
# "二阶矩 − 一阶矩平方"文字描述）属历史遗留且被用户验收；新产内容按归零标准，
# 此类写法应写作"减"或包进 $...$。


def scan(path):
    lines = open(path, encoding='utf-8').read().split('\n')
    hits, in_block = [], False
    for i, ln in enumerate(lines, 1):
        work = ln
        if in_block:
            if '$$' in ln:
                in_block = False
                work = ln.split('$$', 1)[1]
            else:
                continue
        else:
            if ln.count('$$') >= 2:
                work = re.sub(r'\$\$.*?\$\$', '', ln)
            elif ln.count('$$') == 1:
                in_block = True
                work = ln.split('$$', 1)[0]
        work = re.sub(r'\$[^$\n]+?\$', '', work)
        found = ''.join(sorted(set(ch for ch in work
                                   if (ch in GREEK or ch in SUPSUB or ch in OPS)
                                   and ch not in WHITELIST)))
        m1 = re.findall(r'[A-Za-z]\([^()$]{0,40}\)', work)            # P(A)、N(μ,σ²) 型
        m2 = re.findall(r'[A-Za-z]_\{?[^\s,，。；:：)）|]{1,20}', work)  # X_n 型下标
        m3 = re.findall(r'[~^]', work)                                  # 裸上下标符
        if found or m1 or m2 or m3:
            hits.append((i, found, m1, m2, m3, ln))
    return hits


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    total = 0
    for path in sys.argv[1:]:
        hits = scan(path)
        total += len(hits)
        print(f'=== {path}: {len(hits)} 行含裸数学 ===')
        for i, found, m1, m2, m3, ln in hits:
            flags = f'[{found[:24]}]' if found else ''
            if m1: flags += f' fn:{m1[:3]}'
            if m2: flags += f' _:{m2[:3]}'
            if m3: flags += f' ~^:{m3[:3]}'
            print(f'L{i} {flags}')
            print(f'   {ln[:120]}')
    print(f'\n总计 {total} 行。' + ('✓ 数学零裸露，可进入构建' if total == 0 else '✗ 存在裸数学，退回重写'))
    sys.exit(0 if total == 0 else 1)


if __name__ == '__main__':
    main()
