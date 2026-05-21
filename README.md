# 📝 Sengins Blog

个人博客，使用 Markdown 写作，自动发布为静态 HTML 网站。

🌐 **访问地址**: https://sengins.github.io/blog/

## 目录结构

```
blog/
├── articles/          # Markdown 文章源文件
│   └── *.md
├── assets/images/     # 图片资源
├── scripts/           # 构建脚本
├── templates/         # HTML 模板 (Jinja2)
├── src/               # Python 核心库
├── _site/             # 生成的静态网站 (gitignore)
├── config.json        # 博客配置
└── .github/workflows/ # GitHub Actions 自动部署
```

## 如何写一篇新文章

在 `articles/` 目录下创建 Markdown 文件，格式如下：

```markdown
---
title: 文章标题
date: 2025-06-01
tags: [标签1, 标签2]
slug: my-article-slug
---

这里是文章正文，支持标准 Markdown 语法。

### 表格示例

| 列1 | 列2 | 列3 |
|-----|-----|-----|
| A   | B   | C   |

### 图片示例

![图片描述](assets/images/2025-06-01/image-1.jpg)

### 代码示例

```python
print("Hello World")
```
```

> **注意**: 如果 `slug` 未指定，会自动从标题生成。中文标题会使用 MD5 哈希作为 slug。

## 本地预览

```bash
# 安装依赖
pip install jinja2 mistune Pillow pyyaml python-dateutil

# 生成 HTML
python scripts/publish.py --blog-dir . --template-dir templates --output-dir ./_site

# 打开 _site/index.html 即可预览
```

## 发布到线上

```bash
# 提交并推送
git add .
git commit -m "新文章: 文章标题"
git push
```

推送后，GitHub Actions 会自动：
1. 运行 `publish.py` 将 Markdown 转换为 HTML
2. 部署到 `gh-pages` 分支
3. GitHub Pages 自动更新

## 配置

编辑 `config.json` 修改博客标题、描述、作者信息等。

```json
{
  "title": "我的博客",
  "description": "个人博客描述",
  "author": "Your Name",
  "site_url": "https://sengins.github.io/blog/",
  ...
}
```

## 技术栈

- **内容格式**: Markdown + YAML front matter
- **模板引擎**: Jinja2
- **Markdown 渲染**: mistune
- **自动部署**: GitHub Actions → GitHub Pages
- **图片处理**: Pillow (自动压缩/缩放)
