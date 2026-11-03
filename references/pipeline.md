# PDF 构建管线详解（KaTeX 占位符方案）

> 环境：macOS + WorkBuddy 内置 node/python + Google Chrome。换环境先跑 §五的环境自检。

## 一、管线总览

```
教科书 PDF
  │ ① extract_book.py（PUA/全角规范化提取全文）
  ▼
规范化全文 txt ──→ AI 分批精读（每章 ≤6 页一批）
  │ ② AI 撰写 2 份 md（中间产物，放 .workbuddy/tmp-review/）
  ▼
背诵合集.md / 教学文档.md
  │ ③ bare_math_scan.py（裸数学归零）+ numeric 复算（全数值）
  ▼
质检通过的 md
  │ ④ build_pdfs.mjs（md → HTML，KaTeX 占位符方案）
  │ ⑤ Chrome headless 打印（必须 --no-pdf-header-footer）
  ▼
raw PDF
  │ ⑥ watermark_verify.py（加水印 + 四项验证）
  ▼
✅ 背诵合集.pdf + 教学文档.pdf（仅交付这 2 份）
```

## 二、关键机制：KaTeX 占位符方案（E9 的解法）

**问题**：直接把含 `$...$` 的 md 喂给 marked，Markdown 解析器会：
- 吃掉公式内 `\{` 的反斜杠 → KaTeX 报错；
- 把公式内 `_` `*` 解析成斜体/加粗 → 公式碎裂。

**解法**（build_pdfs.mjs 已实现，勿改顺序）：
1. 正则把所有 `$$...$$` 与 `$...$` stash 成 `MATHSLOT{n}ENDSLOT`；
2. marked 解析剩余 Markdown；
3. HTML 字符串里把 slot 替换回公式原文（`\|` → `|`，`&` `<` `>` 转 HTML 实体）；
4. 浏览器端 auto-render 渲染 KaTeX。

## 三、Chrome 打印命令（E11：参数一个都不能少）

```bash
"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" \
  --headless=new --disable-gpu --no-sandbox \
  --virtual-time-budget=40000 \
  --run-all-compositor-stages-before-draw \
  --no-pdf-header-footer \
  --print-to-pdf="<输出.pdf>" "file://<html绝对路径>"
```

- `--virtual-time-budget`：给 KaTeX JS 渲染留时间（40s 富余）；
- `--no-pdf-header-footer`：**必带**，否则页眉页脚（URL/日期）污染版面且被误判为超界；
- 打印后 Chrome 控制台会输出 `KATEX_ERROR:` 行（build_pdfs.mjs 注入的探针），grep 它必须为空。

## 四、验证方法（E12 的教训）

**不要用 DOM 测量公式宽度**（.katex/.katex-display/.katex-html 的 rect 全不可靠，块级元素恒占满行宽）。
**可靠方法 = 打印后的 PDF 上用 pymupdf 检查**：

```python
# 内容超界：文本块右沿 vs 页宽-右边距（A4=595pt，右边距 11mm≈31.2pt，容差 2pt）
limit = 595 - 31.2 + 2
over = [(p+1, round(b[2],1)) for p, page in enumerate(doc)
        for b in page.get_text('blocks') if b[2] > limit]
```

LaTeX 残留：全文检索 `\dfrac` `\frac{` `\bar{` `\hat{` `\overline` `MATHSLOT` 等（watermark_verify.py 的 RESIDUE_PATTERNS）。

## 五、环境自检（换机器先跑）

```bash
# 1. node 路径（E2：先 ls 确认版本号，别猜）
ls /Users/tiantianye/.workbuddy/binaries/node/versions/
NODE=/Users/tiantianye/.workbuddy/binaries/node/versions/22.22.2-6/bin/node

# 2. marked + katex（缺则装到隔离工作区）
/Users/tiantianye/.workbuddy/binaries/node/workspace/node_modules/marked  # 存在？
cd /Users/tiantianye/.workbuddy/binaries/node/workspace && $NODE_BIN_DIR/npm install marked katex

# 3. Chrome
ls "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

# 4. pymupdf（watermark_verify/extract_book 用）
python3 -c "import pymupdf"
```

环境变量覆盖：`MARKED_PATH`、`KATEX_PATH`（见 build_pdfs.mjs 头部）。

## 六、排版规格速查（R9 定稿值）

| 项 | 值 |
|---|---|
| 页面 | A4，margin: 13mm 11mm 15mm 11mm |
| 正文 | 10.5pt / line-height 1.75 |
| h1/h2/h3 | 19pt / 15pt / 12pt（蓝色系条状标题） |
| 公式 | KaTeX 行内 1.16em、display 1.3em |
| 表格 | 9.2pt，蓝头 + 斑马纹 |
| 方法总结框 | blockquote 黄底（#fdf8ec + #d9a520 左边条） |
| 分页 | 背诵合集每章(h2)另起页；教学文档每章(h1)另起页但第一章紧随引言（E10 修复） |
| 水印 | 每页顶部居中 "Designed by TiantianYe"（watermark_verify.py 加） |
