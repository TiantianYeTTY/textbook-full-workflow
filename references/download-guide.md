# Designed by TiantianYe
# 电子书获取指南（Skill: textbook-full-workflow 第 1 步）

> 仅当用户**只提供书名**（未附 PDF）时进入本步。目标：从**正规公开渠道**取得该书的
> 电子版 PDF，并完成验真。全文遵守本文件末尾的合规红线。

## 一、搜索策略（WebSearch，一般 2-4 次查询收敛）

| 轮次 | 查询模板 | 目的 |
|---|---|---|
| 1 | `《书名》电子书 全文 下载 出版社` | 摸底有哪些官方/公开渠道 |
| 2 | `《书名》电子版 马克思主义学院 教学资料`（思政/党史类书最有效） | 定位高校公开教学资源页 |
| 3 | `《书名》 在线阅读 免费正版` | 兜底找正规平台的免费阅读入口 |

搜索结果甄别要点：
- **高校域名**（`.edu.cn` 的马克思主义学院/教务处页面）挂出的课程必读附件是高置信来源；
- 出版社官方、学习强国、人民网理论频道等官方渠道优先；
- **Z-Library 等影子图书馆/盗版站点一律不使用**，即使搜索结果靠前也跳过。

## 二、页面解析与附件提取

高校 CMS 页面的附件通常是 `<a href="...">文件名.pdf</a>` 形态，且文件名往往就是完整书目信息（含作者/出版社/年份，可用于验真）。提取方法：

```bash
curl -sL "页面URL" -o /tmp/page.html
python3 - << 'EOF'
import re
html = open('/tmp/page.html', encoding='utf-8').read()
anchors = re.findall(r'<a[^>]+href=["\']([^"\']+)["\'][^>]*>([^<]*\.pdf)</a>', html)
for url, name in anchors:
    print(name, '->', url)
EOF
```

- 相对链接需拼上站点域名；注意 URL 中的 `&` 可能是 `&amp;`，需还原；
- 常见附件系统路径模式：`/system/_content/download.jsp?...`（博达 CMS）、
  `/wp-content/uploads/...`、`/sites/default/files/...` 等。

## 三、博达 CMS 验证码下载流程（实测有效）

大量高校官网使用博达 CMS，附件下载需验证码。完整流程（requests/curl 均可，关键是**全程携带同一会话 cookie**）：

```bash
# 1. 请求 download.jsp 拿到验证码页 + 会话 cookie（-c 落盘 cookie）
curl -sL -c /tmp/ck.txt -A "Mozilla/5.0" "https://站点/system/_content/download.jsp?urltype=news.DownloadAttachUrl&owner=...&wbfileid=..." -o /tmp/captcha_page.html

# 2. 从验证码页解析出图片地址，一般形如
#    /system/resource/js/filedownload/createimage.jsp?randnum=<时间戳>
#    带着 -b /tmp/ck.txt 下载验证码图
curl -sL -b /tmp/ck.txt -c /tmp/ck.txt "https://站点/system/resource/js/filedownload/createimage.jsp?randnum=$(date +%s)" -o /tmp/captcha.png

# 3. 用 ViewImage 工具识别验证码字符（通常 4 位数字/字母）

# 4. 带 codeValue 参数重新请求 download.jsp（-b 携带同一 cookie，-e 带 Referer）
curl -sL -b /tmp/ck.txt -A "Mozilla/5.0" -e "https://站点/..." \
  "https://站点/system/_content/download.jsp?...&codeValue=<验证码>" -o 书名.pdf
```

判断是否成功的标志：下载体积（几十 KB 以内多半是验证码页/错误页，用 `file` 命令确认
是 HTML 还是 PDF）；识别错验证码会再次返回 HTML，重取一张新验证码图重试即可（次数
控制在 3 次内，仍失败则换渠道）。

## 四、通用下载要点

- **请求头**：带浏览器 `User-Agent`；下载类请求尽量带 `Referer`（指向来源页面）；
- **超时**：大文件用 `--max-time 300~600`；教育网较慢属正常，几十 MB 以上耐心等待；
- **验证码图的识别**一律用 ViewImage 工具视觉识别，不要猜。

## 五、下载后验真（必做，三步）

1. **格式校验**：`file 书.pdf` 应为 `PDF document`；`%PDF` 头与 `%%EOF` 尾齐全；
2. **规模合理性**：pymupdf/pypdf 读页数，与实体书篇幅（一般可在出版社/豆瓣页查到）对照；
3. **内容目检**：`pdftoppm -png -f 1 -l 5 -r 60` 渲染前几页，用 ViewImage 核对
   封面书名/出版社/目录是否与目标书一致。**书不对 = 弃用重找**，严禁将错书带入后续流程。

## 六、拿不到 PDF 时的降级路径

1. 指引用户到**正规电子书平台**（微信读书、京东读书、Kindle 商店、出版社官方 App），
   部分教材可免费在线阅读或低价购买；
2. 用户能自行提供纸质书拍照/扫描件时，接收后从第 2 步 OCR 分支进入；
3. 明确告知"未能找到合法电子版"，**不得**转向盗版站点。

## 七、合规红线（不可越过）

- 只使用**合法公开渠道**：出版社官方、政府/党委宣传部门公开资源、高校公开教学资料页、
  官方媒体全文转载、正规电子书平台；
- 不破解任何付费/登录墙；不在需要盗版下载器/注册盗版站账号的站点下载；
- 下载所得仅供用户个人学习使用；在最终交付说明中**注明来源**，方便用户自行复查。
