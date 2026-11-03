---
name: textbook-review-pdfs
description: 教科书PDF电子书→两份复习PDF（背诵合集+教学文档）。当用户给一份教材/电子书PDF要求"整理知识点、做复习资料、背诵合集、教学文档、备考资料、公式合集、自学文档"，或提到"做成PDF复习"，或要求"开源的复习资料生成"时使用。全部内容溯源原书、LaTeX排版、逐页水印、强制校对，仅交付2份PDF。
---

# textbook-review-pdfs —— 教科书 PDF → 两份复习 PDF

## 目标与产出

用户提供一份教科书 PDF 电子书，本 Skill 产出**且仅产出 2 份 PDF**：

1. **《书名 · 全书知识点与公式背诵合集.pdf》**——纯知识点列表：全部定义/定理/公式 + 分布/区间/检验汇总速查表 + 易混淆速记。看着它就能背诵复习，**不允许掺杂无关信息**。
2. **《书名 · 自学教学文档.pdf》**——原书例题（**完整原题**）+ **分步带做解析**（第 1 步/第 2 步……每步做什么+为什么）+ 方法总结。看了它就能自学解题。

硬性要求（用户原话级约束，违反必返工）：
- 每页 PDF 上方有 **"Designed by TiantianYe"** 水印；
- 全部知识点/例题**只来源于用户提供的电子书**，严禁编造、严禁网摘；
- 每一个数学公式、字母都必须是**标准 LaTeX**（渲染由 KaTeX 完成），严禁 Unicode 直排；
- 输出前**必须严格校对**（数值复算 + 溯源核对 + 渲染验证），严禁不经校对输出；
- 只交付 2 份 PDF；md 是中间产物，不交付。

## 输入

| 输入 | 必需 | 说明 |
|---|---|---|
| 教科书 PDF 路径 | ✓ | 需带文本层（扫描无文本层时先告知用户无法保证准确性） |
| 学科名/书名 | ✓ | 用于标题与文件名 |
| 中间目录 | 默认 `<PDF所在目录>/.workbuddy/tmp-review/` | 存放提取 txt、md、raw PDF |

## 流程（6 步，前 3 步质量决定一切）

### 第 1 步 · 提取原书全文
```bash
python3 scripts/extract_book.py "<教科书.pdf>" "<中间目录>/book_full.txt"
```
- 产出带 `[PDF第N页]` 页标的规范化全文（全角→半角、PUA→小数点）；
- **看脚本末尾的非常规字符扫描报告**，新书有漏网字符就加进 CHAR_MAP 重跑；
- 之后**分批精读**（每批 ≤6 页），全书读完再动笔——禁止只读部分就开始写。

### 第 2 步 · 撰写两份 md（中间产物）
按 [references/doc-templates.md](references/doc-templates.md) 的定稿骨架写：
- 背诵合集：`## 第N章`（h2 分章）；教学文档：`# 第N章`（h1 分章）+ `### 例题 N（教材例 M）`；
- 例题题目 = 书上完整原题（数据列表一字不落）；解析分步带做；每题方法总结 blockquote；
- 每道例题必须在 book_full.txt 中检索到原题（容错正则），检索不到 = 换书中原题。

### 第 3 步 · 强制校对（两道关卡，全过才准进第 4 步）
1. **数值复算**：按 [references/proofread.md](references/proofread.md) §二，对文档中每一个计算结果精确复算/数值积分/蒙特卡洛旁证（模板：`scripts/numeric_check_template.py`，逐项替换成新书内容）。分段函数做边界自检。原书数值错误 → 采信计算正确值并加注。
2. **裸数学扫描**：
```bash
python3 scripts/bare_math_scan.py 背诵合集.md 教学文档.md   # 退出码必须为 0
```

### 第 4 步 · 构建 HTML + 打印 PDF
```bash
node scripts/build_pdfs.mjs 背诵合集.md /tmp/背诵合集.html "<书名> · 背诵合集" h2
node scripts/build_pdfs.mjs 教学文档.md /tmp/教学文档.html "<书名> · 自学教学文档" h1
"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" --headless=new --disable-gpu \
  --no-sandbox --virtual-time-budget=40000 --run-all-compositor-stages-before-draw \
  --no-pdf-header-footer --print-to-pdf="<中间目录>/背诵合集_raw.pdf" "file:///tmp/背诵合集.html"
# 教学文档同理；打印输出里 grep KATEX_ERROR 必须为空
```
管线原理与坑：[references/pipeline.md](references/pipeline.md)。

### 第 5 步 · 加水印 + 终验
```bash
python3 scripts/watermark_verify.py <中间目录>/背诵合集_raw.pdf "<PDF目录>/背诵合集.pdf"
python3 scripts/watermark_verify.py <中间目录>/教学文档_raw.pdf  "<PDF目录>/教学文档.pdf"
```
四项验证（每页水印/超界/LaTeX 残留/页数）退出码 0 才算通过；非 0 修复后重跑第 4-5 步。

### 第 6 步 · 交付与收尾
- `present_files` 只放 2 份 PDF；
- 工作日志写入 `<PDF目录>/.workbuddy/memory/`（新书特殊字符、学科新坑）；
- 中间目录保留（用户后续可能要改 md），但不列入交付。

## 红线速查（详见 references/format-rules-and-errors.md 错误档案 17+8 条）

1. **严禁 Unicode 直排**——用户要 LaTeX 就是为了 PDF 渲染清晰；"md 里 LaTeX 乱"的正解是交付 PDF，不是改写公式（档案 F5，最严重的一次方向性错误）。
2. **数学零裸露**——每个数学元素都进 `$...$`，`bare_math_scan.py` 归零为准（F6）。
3. **内容全溯源**——例题标注（教材例 M）且能在原书检索到；非书中题一律换掉（E8）。
4. **校对=程序复算**——5 处真实数值错误全是复算抓的，人工通读抓不到（E3-E7）；带分数 1¾ 提取后变 13/4，警惕（E3）。
5. **Chrome 打印必带 `--no-pdf-header-footer`**（E11）；溢出检测用 pymupdf 查文本块右沿，别用 DOM 测量（E12）。
6. **node 路径先 ls 确认**（E2：22.22.2-5 不存在，-6 才对）。
7. 已验收的产物只读；返工只动用户点名的文件（F7）。

## 协作约定

- 用户明确要求"背诵合集不允许再动"这类锁定时，该文件只读；
- 章节分批精读时保持节奏汇报（"第 X 章读完"），让用户知道进度；
- 数值修正、替换例题等**内容级改动**要在交付说明里逐条列出（改了什么、为什么）；
- 新学科首跑：extract_book.py 的字符扫描报告 + numeric 模板全量替换是两个必做适配点。
