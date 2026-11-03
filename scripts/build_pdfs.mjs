// Designed by TiantianYe
/**
 * build_pdfs.mjs —— Markdown → HTML(KaTeX) 构建器（Skill: textbook-review-pdfs 第 3 步）
 *
 * 核心机制（详见 references/pipeline.md）：
 *   占位符方案 —— 数学式先 stash 成 MATHSLOTnENDSLOT，等 marked 解析完 Markdown
 *   再以 HTML 实体放回。若跳过此步，marked 会吃掉 \{ 的反斜杠、把 _ * 当斜体，
 *   导致 KaTeX 渲染失败（本项目踩过的真实事故，见 references/format-rules-and-errors.md #14）。
 *
 * 适配指南（换环境时检查这里）：
 *   1. MARKED / KATEX 路径：默认适配 WorkBuddy 内置 node 工作区
 *      （/Users/tiantianye/.workbuddy/binaries/node/workspace/node_modules）。
 *      换机器先 npm install marked katex，再用环境变量 MARKED_PATH / KATEX_PATH 覆盖。
 *   2. split 模式：'h1' = 教学文档（每章另起页，第一章紧随引言防首页空白）；
 *      'h2' = 背诵合集（每章另起页）。
 *
 * 用法：
 *   node build_pdfs.mjs <输入.md> <输出.html> <标题> <split: h1|h2>
 * 示例：
 *   node build_pdfs.mjs ./背诵合集.md /tmp/背诵合集.html "高等数学 · 背诵合集" h2
 */
import { readFileSync, writeFileSync } from 'fs';

const MARKED = process.env.MARKED_PATH ||
  '/Users/tiantianye/.workbuddy/binaries/node/workspace/node_modules/marked/lib/marked.esm.js';
const KATEX = process.env.KATEX_PATH ||
  '/Users/tiantianye/.workbuddy/binaries/node/workspace/node_modules/katex/dist';
const { marked } = await import(MARKED);

const [mdPath, htmlPath, title, split] = process.argv.slice(2);
if (!mdPath || !htmlPath || !title || !['h1', 'h2'].includes(split)) {
  console.error('用法: node build_pdfs.mjs <输入.md> <输出.html> <标题> <h1|h2>');
  process.exit(1);
}

function buildHtml(md) {
  const slots = [];
  const stash = (s) => { slots.push(s); return `MATHSLOT${slots.length - 1}ENDSLOT`; };
  let t = md.replace(/\$\$[\s\S]+?\$\$|\$[^\$\n]+?\$/g, stash);
  let html = marked.parse(t, { gfm: true, breaks: false });
  html = html.replace(/MATHSLOT(\d+)ENDSLOT/g, (_, i) => {
    let m = slots[+i];
    m = m.replace(/\\\|/g, '|');   // 表格内 \|Z\| 在这里还原
    m = m.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
    return m;
  });
  return html;
}

// 排版规格（用户验收定稿，勿擅自改动；字号依据见 format-rules #13）
const CSS = `
@page { size: A4; margin: 13mm 11mm 15mm 11mm; }
* { box-sizing: border-box; }
html { -webkit-print-color-adjust: exact; print-color-adjust: exact; }
body { font-family: "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", sans-serif; font-size: 10.5pt; line-height: 1.75; color: #1f2933; margin: 0; }
h1, h2, h3, h4 { font-weight: 700; break-after: avoid-page; line-height: 1.4; }
h1 { font-size: 19pt; color: #0b3a66; margin: 0 0 14px; padding: 10px 14px 10px; background: linear-gradient(90deg, #e8f1fa 0%, #f6fafd 70%, transparent); border-left: 6px solid #1a5fa8; border-radius: 3px; }
body.split-h1 h1:not(:first-of-type) { break-before: page; margin-top: 4px; }
body.split-h1 h1:nth-of-type(2) { break-before: auto; }
body.split-h2 h2:not(:first-of-type) { break-before: page; }
h2 { font-size: 15pt; color: #0b3a66; margin: 20px 0 10px; padding: 5px 12px; background: #eef4fa; border-left: 5px solid #2e6fb7; border-radius: 3px; }
h3 { font-size: 12pt; color: #1a5fa8; margin: 15px 0 6px; padding-left: 8px; border-left: 3px solid #9dbfe0; }
p { margin: 6px 0; text-align: justify; }
strong { color: #083358; }
blockquote { margin: 9px 0; padding: 8px 13px; background: #fdf8ec; border-left: 4px solid #d9a520; border-radius: 3px; break-inside: avoid-page; }
blockquote p { margin: 3px 0; }
table { border-collapse: collapse; width: 100%; margin: 9px 0; font-size: 9.2pt; line-height: 1.6; }
th { background: #2e6fb7; color: #fff; font-weight: 600; padding: 5px 8px; border: 1px solid #b9cfe6; text-align: center; }
td { padding: 5px 8px; border: 1px solid #c4d6e8; vertical-align: middle; }
tbody tr:nth-child(even) { background: #f4f8fc; }
tr { break-inside: avoid; }
ul, ol { margin: 6px 0; padding-left: 22px; }
li { margin: 3px 0; }
hr { border: none; border-top: 1.5px dashed #b9cfe6; margin: 13px 0; }
.katex-display { margin: 10px 0; break-inside: avoid; }
.katex { font-size: 1.16em; }
.katex-display > .katex { font-size: 1.3em; }
.katex-error { color: #c0392b !important; }
code { background: #f0f3f6; padding: 1px 4px; border-radius: 3px; font-size: 0.92em; }
`;

const shell = (title, body, split) => `<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="UTF-8"><title>${title}</title>
<link rel="stylesheet" href="file://${KATEX}/katex.min.css">
<script src="file://${KATEX}/katex.min.js"></script>
<script src="file://${KATEX}/contrib/auto-render.min.js"></script>
<style>${CSS}</style></head>
<body class="split-${split}">
${body}
<script>
document.addEventListener("DOMContentLoaded", function() {
  renderMathInElement(document.body, { delimiters: [{left:"$$",right:"$$",display:true},{left:"$",right:"$",display:false}], throwOnError: false, strict: false, trust: true });
  document.querySelectorAll('.katex-error').forEach(el => console.log("KATEX_ERROR:" + el.textContent.slice(0,60)));
  document.title += "_DONE";
});
</script></body></html>`;

writeFileSync(htmlPath, shell(title, buildHtml(readFileSync(mdPath, 'utf-8')), split), 'utf-8');
console.log('HTML 已生成:', htmlPath);
