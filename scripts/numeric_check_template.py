# Designed by TiantianYe
#!/usr/bin/env python3
"""
numeric_check_template.py —— 数值复算模板（Skill: textbook-review-pdfs 校对步）

职责：
    交付前的强制校对底座。硬规则：**文档中每一个计算结果都必须程序化复算**，
    本模板提供三类验证手段与自检框架，AI 需按文档实际内容填充 CHECKS 列表：
      ① exact    —— 精确复算（组合数/概率/期望/统计量，误差容忍 tol）
      ② numeric  —— 数值积分（定积分/分段积分，梯形法足够 1e-6 精度）
      ③ montecarlo —— 蒙特卡洛（期望/概率的独立旁证，容忍 1e-2）

    依据：用户多次强调「务必确保准确性」；本项目实测发现过 5 处计算/提取错误
    （例37 带分数 1¾→13/4 误读、例38 1331/33→460/33、例27 x³/12→x⁴/48、
    例73 原书印 0.98 实为 1.01、生日问题原书 0.9922 实为 0.9941），
    全部是靠程序复算抓出来的，人工通读抓不到。

适配指南：
    1. CHECKS 里每项 = (名称, 复算函数, 期望值, 容差)。换学科时按文档内容重写全部条目。
    2. 查表值（如 Φ(1.22)=0.8888、t 分位数）视为已知常量，直接写进 want 即可。
    3. 原书数值与复算不符时：优先采信计算正确值并在文档加注，禁止照抄原书错误。

用法：
    python3 numeric_check_template.py   # 跑内置示例（本项目概率论题）验证模板可用
"""
import math
import sys
from math import comb, exp, factorial, sqrt, pi

Phi = lambda v: 0.5 * (1 + math.erf(v / sqrt(2)))
pois = lambda k, lam: exp(-lam) * lam ** k / factorial(k)

# ---- 三类验证手段 ----
def trapezoid(f, a, b, n=20000):
    """数值积分（梯形法）"""
    h = (b - a) / n
    return h / 2 * (f(a) + f(b) + 2 * sum(f(a + i * h) for i in range(1, n)))


def montecarlo(g, N=400000, seed=7):
    """蒙特卡洛期望（g: 采样函数，内部自行抽样）"""
    import random
    random.seed(seed)
    return sum(g() for _ in range(N)) / N


# ---- 复算清单：（名称, 复算函数, 期望值, 容差）----
# 以下为概率论项目真实条目示例，换学科时整体替换。
CHECKS = [
    # ① 精确复算（第一章～第八章抽样）
    ("生日问题 n=23",          lambda: 1 - math.prod((365 - i) / 365 for i in range(23)), 0.507, 5e-4),
    ("生日问题 n=60 精确值",    lambda: 1 - math.prod((365 - i) / 365 for i in range(60)), 0.9941, 5e-5),
    ("碰面问题 11/36",         lambda: (60**2 - 50**2) / 60**2, 11/36, 1e-12),
    ("全概率 P(B)=0.07",       lambda: 0.6*0.05 + 0.4*0.1, 0.07, 1e-12),
    ("二项 P(X=3) 0.2048",     lambda: comb(5,3)*0.8**3*0.2**2, 0.2048, 1e-12),
    ("泊松 P(X<=8) 0.847237",  lambda: sum(pois(k, 6) for k in range(9)), 0.847237, 1e-5),
    ("例13 P(B)=53/120",       lambda: (1/3)*(1/5 + 1/2 + 5/8), 53/120, 1e-12),
    ("例37 E(X^2)=7/4",        lambda: 1*0.25 + 1*0.5 + 4*0.25, 7/4, 1e-12),
    ("例37 E(X^3)=9/4",        lambda: -1*0.25 + 1*0.5 + 8*0.25, 9/4, 1e-12),
    ("例38 460/33",            lambda: 8*(0.5-1/2.2) + 24*(1/2.2-1/3) + 32/3, 460/33, 1e-10),
    ("例48 n上限 78.09",       lambda: 12*25/1.96**2, 78.0924, 1e-3),
    ("例65 区间下限",           lambda: 0.2 - 1.96*sqrt(0.4)/sqrt(5), -0.354, 1e-3),
    ("例66 mu下限 1485.69",    lambda: 1500 - 2.262*20/sqrt(10), 1485.69, 1e-2),
    ("例78 锭子 chi2=36.57",
     lambda: sum((o-e)**2/e for o, e in zip(
         [264, 112, 38, 19, 7],
         [440*p for p in [pois(k, 0.65) for k in range(4)] + [1 - sum(pois(k, 0.65) for k in range(4))]])),
     36.57, 0.05),
    # ② 数值积分（例33 分段 CDF）
    ("例33 F_Z(0.5)=z^3/4",
     lambda: trapezoid(lambda x: 6*x*(0.5-2*x), 0, 0.25), 0.5**3/4, 1e-8),
    # ③ 蒙特卡洛旁证（例42 E(sin²Z)=0.5）
    ("例42 E(sin^2 Z)=0.5",
     lambda: montecarlo(lambda: math.sin(__import__('random').uniform(0, 2*pi))**2), 0.5, 1e-2),
]


def main():
    fails = []
    for name, fn, want, tol in CHECKS:
        got = fn()
        ok = abs(got - want) <= tol
        print(f"{'✓' if ok else '✗ MISMATCH'} {name}: got={got:.6f} want={want}")
        if not ok:
            fails.append(name)
    print('\n' + ('✓ 全部复算通过' if not fails else f'✗ {len(fails)} 项不符: {fails}'))
    sys.exit(0 if not fails else 1)


if __name__ == '__main__':
    main()
