---
name: textbook-full-workflow
description: 教材/教科书"全流程学习"技能，覆盖电子书获取→文本提取→复习 PDF 产出全链路。三种输入自动路由：①用户只给书名→从正规公开渠道（高校公开教学资源、出版社官方等）检索下载电子书；②用户给的 PDF 是扫描版（无文本层）→用 macOS Vision 框架 OCR 脚本识别全文；③PDF 带文本层→直接提取。产出《背诵合集》与《教学文档》PDF（用户只要一份时按需交付）。当用户要求"下载教材电子书、做复习资料、整理知识点、背诵合集、教学文档、备考资料"，或提供教材 PDF 要求输出复习 PDF，或提到扫描版教材需要 OCR 时使用。全部内容溯源原书、LaTeX 排版、逐页水印、强制程序化校对。
agent_created: true
---

# textbook-full-workflow —— 电子书获取 → OCR → 复习 PDF 全流程

## 目标与产出

按用户输入自动路由，最终产出**背诵复习 PDF**（默认含《自学教学文档》，用户明确不需要时只交一份）：

1. **《书名 · 全书知识点与公式背诵合集.pdf》**——纯知识点列表：全部定义/定理/公式 + 汇总速查表 + 易混淆速记。看着它就能背诵复习，**不允许掺杂无关信息**。
2. **《书名 · 自学教学文档.pdf》**——原书例题（**完整原题**）+ **分步带做解析**（第 1 步/第 2 步……每步做什么+为什么）+ 方法总结。看了它就能自学解题。

硬性要求（用户原话级约束，违反必返工）：
- 每页 PDF 上方有 **"Designed by TiantianYe"** 水印；
- 全部知识点/例题**只来源于电子书**，严禁编造、严禁网摘；
- 每一个数学公式、字母都必须是**标准 LaTeX**（渲染由 KaTeX 完成），严禁 Unicode 直排；
- 输出前**必须严格校对**（数值复算/溯源核对 + 渲染验证），严禁不经校对输出；
- 默认交付 2 份 PDF；**用户明确只要其中一份时按用户要求交付**（如实记录于交付说明）；md 是中间产物，不交付。

## 流程总览（8 步）

| 步 | 名称 | 触发条件 | 关键产物/脚本 |
|---|---|---|---|
| 0 | 输入分诊 | 每次必做 | 三态路由判定 |
| 1 | 电子书获取 | 只给书名 | [references/download-guide.md](references/download-guide.md) |
| 2 | 原书全文获取 | 有 PDF 后 | extract_book.py（文本层）/ ocr_book.py（扫描版） |
| 3 | 精读与撰写 | 有全文后 | 两份 md（模板见 doc-templates.md） |
| 4 | 强制校对 | md 完成后 | 溯源核对/数值复算 + bare_math_scan.py |
| 5 | 构建 HTML + 打印 | 校对全过 | build_pdfs.mjs + Chrome headless |
| 6 | 水印 + 终验 | raw PDF 后 | watermark_verify.py |
| 7 | 交付与收尾 | 终验通过 | present_files + 工作日志 |

## 第 0 步 · 输入分诊（每次必做）

三态判定，据此路由：

```bash
# 文本层判定：抽样检查是否为扫描版
python3 - << 'EOF'
import pymupdf, sys
doc = pymupdf.open(sys.argv[1] if len(sys.argv)>1 else '书.pdf')
empty = sum(1 for i in range(0, len(doc), 20) if len(doc[i].get_text().strip()) < 10)
print(f"页数 {len(doc)}, 空文本页 {empty}")
EOF
```

- **态 A · 只有书名** → 先走第 1 步下载，再按态 B/C 继续；
- **态 B · PDF 带文本层**（空文本页 ≈ 0）→ 第 2 步走 extract_book.py；
- **态 C · 扫描版无文本层**（抽样页几乎全空）→ 第 2 步走 ocr_book.py，并向用户简要说明"该书为扫描版，将先 OCR 识别"。

## 第 1 步 · 电子书获取（态 A）

按 [references/download-guide.md](references/download-guide.md) 执行：正规渠道搜索 → 页面附件解析 →（博达 CMS 验证码流程）→ 下载 → **三步验真**（格式/页数/封面目检）。验真不通过则换渠道重找，严禁将错书带入后续流程。

## 第 2 步 · 原书全文获取

**态 B（文本层）**：

```bash
python3 scripts/extract_book.py "<教科书.pdf>" "<中间目录>/book_full.txt"
```

- **看脚本末尾的非常规字符扫描报告**，新书有漏网字符就加进 CHAR_MAP 重跑；
- 之后**分批精读**，全书读完再动笔——禁止只读部分就开始写。

**态 C（扫描版）**：

```bash
# 先抽 10-15 页试跑，人工抽检 OCR 质量；确认后再跑全书
python3 scripts/ocr_book.py "<教科书.pdf>" "<中间目录>/sample.txt" 6 20
python3 scripts/ocr_book.py "<教科书.pdf>" "<中间目录>/book_full.txt"
```

- 原理：`ocr_vision.swift` 用 CoreGraphics 逐页渲染（默认 4 倍 ≈288DPI）+ macOS Vision 框架 `.accurate` 中文识别（zh-Hans/zh-Hant + 语言纠错）；`ocr_book.py` 负责编译缓存、调用与规范化，产物格式与 extract_book.py **完全一致**（`===== [PDF第N页] =====` 页标 + 全角→半角清洗 + 漏网字符报告）；
- 依赖 Xcode CLT（`swiftc`）；实测 386 页中文书约 150 秒、23 万字，页数多时用 run_in_background；
- **OCR 后必做抽检**：`pdftoppm` 渲染 3-5 页，与 OCR 文本（含封面/目录/正文中各抽）逐句比对；发现系统性识别问题（如断行丢字、标点错乱）先评估影响面再决定是否调倍率重跑；
- OCR 文本常有**跨行断词/页眉页脚噪声**（页码被误识别为 `《`、`4` 等单字符）：精读时按上下文脑补断行，关键数字一律以溯源核对兜底。

## 第 3 步 · 撰写 md（中间产物）

按 [references/doc-templates.md](references/doc-templates.md) 的定稿骨架写：
- 背诵合集：`## 第N章`（h2 分章）；教学文档：`# 第N章`（h1 分章）+ `### 例题 N（教材例 M）`；
- 例题题目 = 书上完整原题（数据列表一字不落）；解析分步带做；每题方法总结 blockquote；
- 每道例题必须在 book_full.txt 中检索到原题（容错正则），检索不到 = 换书中原题；
- 历史/政治/文科类教材：知识点条目 = "术语 + 年份/内容 + 一句话意义"；汇总表替换为"大事年表/会议汇总表"；数字使用半角，括号用全角（避免触发裸数学误报，见第 4 步）。

## 第 4 步 · 强制校对（两道关卡，全过才准进第 5 步）

1. **数值/事实校验**（按学科二选一）：
   - **数学类**：按 [references/proofread.md](references/proofread.md) §二，对文档中每一个计算结果精确复算/数值积分/蒙特卡洛旁证（模板：`scripts/numeric_check_template.py`，逐项替换成新书内容）。分段函数做边界自检。原书数值错误 → 采信计算正确值并加注。
   - **非数学类（历史/政治/文科）**：数值复算改为**溯源核对**——把文档中全部年份、数字、会议名、文件名批量提取成正则清单，grep 核对到 book_full.txt（逐项命中 = 通过；未命中先查是否 OCR 断行误报，再查真实笔误）。人工通读抓不出数字错误，**必须程序化批量核对**。
2. **裸数学扫描**：

```bash
python3 scripts/bare_math_scan.py 背诵合集.md 教学文档.md   # 退出码必须为 0
```

- 历史类文档注意：半角括号紧跟拉丁字母（如 `GDP(...)`）会触发函数记号误报——全文使用全角括号；箭头 → 与间隔点 · 已在白名单，可正常使用。

## 第 5 步 · 构建 HTML + 打印 PDF

```bash
node scripts/build_pdfs.mjs 背诵合集.md /tmp/背诵合集.html "<书名> · 背诵合集" h2
node scripts/build_pdfs.mjs 教学文档.md /tmp/教学文档.html "<书名> · 自学教学文档" h1
"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" --headless=new --disable-gpu \
  --no-sandbox --virtual-time-budget=40000 --run-all-compositor-stages-before-draw \
  --no-pdf-header-footer --print-to-pdf="<中间目录>/背诵合集_raw.pdf" "file:///tmp/背诵合集.html"
# 教学文档同理；打印输出里 grep KATEX_ERROR 必须为空
```

管线原理与坑：[references/pipeline.md](references/pipeline.md)。node 路径先 `ls` 确认（E2 教训）。

## 第 6 步 · 加水印 + 终验

```bash
python3 scripts/watermark_verify.py <中间目录>/背诵合集_raw.pdf  "<交付目录>/背诵合集.pdf"
python3 scripts/watermark_verify.py <中间目录>/教学文档_raw.pdf  "<交付目录>/教学文档.pdf"
```

四项验证（每页水印/超界/LaTeX 残留/页数）退出码 0 才算通过；非 0 修复后重跑第 5-6 步。

## 第 7 步 · 交付与收尾

- `present_files` 只放**按用户要求确定的份数**（默认 2 份，用户只要一份时交一份并在说明里注明）；
- 工作日志写入 `<交付目录>/.workbuddy/memory/`（新书特殊字符、学科新坑、来源渠道）；
- 中间目录保留（用户后续可能要改 md），但不列入交付；
- 态 A 下载的书在交付说明中**注明来源渠道**（供用户复查）。

## 红线速查（详见 references/format-rules-and-errors.md 错误档案）

1. **严禁 Unicode 直排**——用户要 LaTeX 就是为了 PDF 渲染清晰；"md 里 LaTeX 乱"的正解是交付 PDF，不是改写公式（档案 F5）。
2. **数学零裸露**——每个数学元素都进 `$...$`，`bare_math_scan.py` 归零为准（F6）；文科文档用全角括号规避函数记号误报。
3. **内容全溯源**——例题标注（教材例 M）且能在原书检索到；非书中题一律换掉（E8）。
4. **校对=程序复算/批量溯源**——数值错误人工通读抓不到（E3-E7）；带分数 1¾ 提取后变 13/4，警惕（E3）。
5. **Chrome 打印必带 `--no-pdf-header-footer`**（E11）；溢出检测用 pymupdf 查文本块右沿，别用 DOM 测量（E12）。
6. **node 路径先 ls 确认**（E2）。
7. 已验收的产物只读；返工只动用户点名的文件（F7）。
8. **下载只走正规公开渠道**——Z-Library 等盗版站点一律不碰；来源须写入交付说明（download-guide.md §七）。
9. **扫描版必须先 OCR 并抽检**——严禁对无文本层 PDF 直接凭渲染图片凭空总结；OCR 抽检不通过不得进入撰写。
10. **错书 = 全部重来**——下载验真发现书名/版本不符，弃用重找，严禁带错书进入精读。

## 协作约定

- 用户明确要求"背诵合集不允许再动"这类锁定时，该文件只读；
- 章节分批精读时保持节奏汇报（"第 X 章读完"），让用户知道进度；
- OCR 大书识别（>200 页）建议 run_in_background 并汇报进度；
- 数值修正、替换例题、来源渠道等**内容级信息**要在交付说明里逐条列出（改了什么、为什么、来自哪里）。
