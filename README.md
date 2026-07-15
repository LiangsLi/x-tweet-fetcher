# x-tweet-fetcher

`x-tweet-fetcher` 是一个面向文献阅读器和 AI Agent 的轻量 Python 包：输入一个已经知道的
X/Twitter 帖子或 Article URL，返回稳定、适合机器消费的结构化 JSON。

项目重点不是搜索或自动操作 X，而是尽可能完整地还原单个公开内容，包括：

- 普通帖子与长文本帖子
- X Article 的标题、正文和原帖说明
- 标题、列表、链接、强调、分隔线等富文本结构
- 带语言标记的 Markdown 代码块
- 封面图、正文图片、帖子图片和视频元数据
- 引用帖子、作者、发布时间和互动指标
- 适合程序判断的稳定错误码

当前版本为 `4.0.0.dev0`，要求 Python 3.10 或更高版本。包本身没有第三方运行时依赖，也不需要
X API Key 或登录 Cookie。

## 适用范围

这个项目适合以下场景：

- 阅读器已经拿到一个 X URL，希望导入帖子或 Article
- Coding Agent 需要阅读、总结、翻译或分析某个指定帖子
- Python 程序需要把 X 内容转成稳定的数据模型
- 命令行流程需要获得单个 JSON 对象，并根据退出码处理失败

这个项目不提供以下能力：

- 搜索帖子、用户或话题
- 获取用户时间线、回复列表或完整讨论串
- 监控账号、Follower 或删除事件
- 发布、点赞、转发或管理 X 账号
- 抓取私密、登录后可见或年龄受限内容
- 浏览器自动化、Nitter 后端或媒体文件自动下载

## 支持的 URL

支持 `x.com` 与 `twitter.com` 的公开 `status`、`article` 地址：

```text
https://x.com/{user}/status/{post_id}
https://twitter.com/{user}/status/{post_id}
https://x.com/{user}/article/{post_id}
https://twitter.com/{user}/article/{post_id}
```

例如：

```text
https://x.com/ClaudeDevs/status/2074208949205881033
https://x.com/ClaudeDevs/article/2074208949205881033
```

对于同一个 Post ID，公开的 `status` 与 `article` 地址会得到等价内容。最终的 `kind` 由上游数据
中是否真的包含 Article 决定，而不是只根据 URL 路径判断。

目前不支持内部地址：

```text
https://x.com/i/article/{article_id}
```

## 使用 uv 从 GitHub 安装

目前推荐直接从 GitHub 安装。本仓库地址为：

```text
https://github.com/LiangsLi/x-tweet-fetcher
```

### 作为项目依赖安装

在已有的 uv 项目中执行：

```bash
uv add "x-tweet-fetcher @ git+https://github.com/LiangsLi/x-tweet-fetcher.git@main"
```

uv 会把依赖写入 `pyproject.toml`，并在 `uv.lock` 中记录实际解析到的 Git 提交。

如果生产环境需要完全可复现，建议把 `main` 换成明确的 Commit SHA：

```bash
uv add "x-tweet-fetcher @ git+https://github.com/LiangsLi/x-tweet-fetcher.git@<commit-sha>"
```

### 安装全局命令行工具

如果主要使用 `xtf` 命令，可以通过 uv tool 安装：

```bash
uv tool install "x-tweet-fetcher @ git+https://github.com/LiangsLi/x-tweet-fetcher.git@main"
```

确认安装结果：

```bash
xtf --version
```

### 不安装，直接运行一次

使用 `uvx` 可以临时运行 GitHub 上的版本：

```bash
uvx \
  --from "x-tweet-fetcher @ git+https://github.com/LiangsLi/x-tweet-fetcher.git@main" \
  xtf "https://x.com/ClaudeDevs/status/2074208949205881033" --pretty
```

### 从本地源码安装

```bash
git clone git@github.com:LiangsLi/x-tweet-fetcher.git
cd x-tweet-fetcher
uv tool install .
```

## 命令行用法

最简单的调用方式是把 URL 作为位置参数传给 `xtf`：

```bash
xtf "https://x.com/ClaudeDevs/status/2074208949205881033"
```

格式化 JSON：

```bash
xtf "https://x.com/ClaudeDevs/article/2074208949205881033" --pretty
```

兼容旧版的 `--url` / `-u` 写法：

```bash
xtf --url "https://x.com/ClaudeDevs/status/2074208949205881033" --pretty
```

可用参数：

| 参数 | 说明 |
| --- | --- |
| `URL` | 位置参数形式的 X/Twitter URL |
| `--url URL`, `-u URL` | 与位置参数等价的兼容写法；不要同时使用两种写法 |
| `--pretty`, `-p` | 对 JSON 进行缩进格式化 |
| `--timeout N` | 上游请求超时秒数，默认 `30`，必须大于 `0` |
| `--version` | 输出已安装版本 |

在正常支持的调用形式中，stdout 只包含一个 UTF-8 JSON 对象，便于直接交给程序或 Agent 处理。

退出码约定：

| 退出码 | 含义 |
| --- | --- |
| `0` | 成功获取文档 |
| `1` | URL 已成功解析，但抓取或上游处理失败 |
| `2` | URL 缺失、参数冲突、超时值非法或其他命令行使用错误 |

## Python API

同步获取一个文档：

```python
from xtf import fetch

document = fetch(
    "https://x.com/ClaudeDevs/status/2074208949205881033",
    timeout=30,
)

print(document.kind)              # "post" 或 "article"
print(document.title)             # 普通帖子通常为 None
print(document.content_text)      # 适合搜索和索引的纯文本
print(document.content_markdown)  # 保留结构、图片和代码块的 Markdown

payload = document.to_dict()
```

`fetch_url` 是 `fetch` 的别名：

```python
from xtf import fetch_url

document = fetch_url("https://x.com/user/status/123")
```

捕获稳定异常：

```python
from xtf import RateLimited, XtfError, fetch

try:
    document = fetch("https://x.com/user/status/123")
except RateLimited as error:
    # error.retryable 为 True，可以稍后重试
    print(error.code, error)
except XtfError as error:
    print(error.code, error.retryable, error)
```

## JSON 输出结构

成功结果固定包含 `schema_version: "1.0"`，示例结构如下：

```json
{
  "schema_version": "1.0",
  "source": "x",
  "source_url": "https://x.com/user/article/123",
  "canonical_url": "https://x.com/user/status/123",
  "post_id": "123",
  "kind": "article",
  "title": "Article 标题",
  "author": {
    "name": "作者显示名",
    "handle": "user"
  },
  "published_at": "...",
  "post_text": "发布 Article 时附带的帖子文本",
  "content_text": "去除 Markdown 标记后的可搜索正文",
  "content_markdown": "# 保留富文本结构、图片和代码块的正文",
  "media": [],
  "quote": null,
  "metrics": {
    "likes": 0,
    "reposts": 0,
    "replies": 0,
    "bookmarks": 0,
    "views": 0
  },
  "language": "zh"
}
```

关键字段：

| 字段 | 说明 |
| --- | --- |
| `source_url` | 调用者传入的原始 URL，用于保留来源信息 |
| `canonical_url` | 规范化后的 `https://x.com/{handle}/status/{post_id}` 地址 |
| `kind` | `post` 或 `article` |
| `post_text` | X 帖子本身的文本；对于 Article，它不是 Article 正文 |
| `content_text` | 适合搜索、索引和纯文本处理；保留代码文本但去掉 Markdown 围栏 |
| `content_markdown` | 阅读器和 Agent 应优先使用的完整正文表示 |
| `media` | 图片或视频 URL、尺寸、缩略图、时长及视频变体 |
| `quote` | 引用帖子的作者、文本、媒体和指标；没有引用时为 `null` |
| `metrics` | 点赞、转发、回复、书签和浏览量快照 |

### Article 内容保真

Article 的 `content_markdown` 会尽量保留：

- 标题和层级结构
- 有序列表与无序列表
- 粗体、斜体和链接
- 分隔线
- 封面图与正文图片
- 嵌入帖子的链接
- 带 `python`、`markdown` 等语言标签的 fenced code block

`media` 保存的是远程 URL 和元数据，项目不会主动下载二进制图片或视频文件。

### 错误输出

CLI 失败时使用同一版本化错误信封：

```json
{
  "schema_version": "1.0",
  "source_url": "https://x.com/user/status/123",
  "error": {
    "code": "upstream_unavailable",
    "message": "上游错误说明",
    "retryable": true
  }
}
```

稳定错误码：

| 错误码 | 可重试 | 含义 |
| --- | --- | --- |
| `invalid_url` | 否 | URL 或调用方式无效 |
| `not_found` | 否 | 帖子不存在，或者公开上游无法访问 |
| `rate_limited` | 是 | 上游限流或拒绝访问 |
| `upstream_unavailable` | 是 | 上游服务或网络暂时不可用 |
| `invalid_upstream_response` | 是 | 上游返回了不完整或无法解析的数据 |
| `unsupported_content` | 否 | 返回数据中没有可读取的受支持内容 |

完整字段含义、媒体结构以及 Article/Post/错误样例见
[`skills/fetch-x-post/references/output-schema.md`](skills/fetch-x-post/references/output-schema.md)。

## 安装 Agent Skill

仓库内提供了可分发的 [`$fetch-x-post`](skills/fetch-x-post) Skill。它会指导 Codex 或兼容的
Coding Agent：

- 识别受支持的 X/Twitter URL
- 调用 `xtf` 并解析退出码与 JSON
- 优先使用 `content_markdown` 阅读 Article
- 保留代码块、图片信息和引用帖子上下文
- 根据 `error.retryable` 决定是否适合重试
- 避免把抓取失败误报为成功

### 让 Codex 安装

可以直接把下面的请求交给支持 GitHub Skill 安装的 Codex：

```text
请从 https://github.com/LiangsLi/x-tweet-fetcher/tree/main/skills/fetch-x-post 安装这个 Skill。
```

### 手动安装

先确保 `xtf` 已经作为工具安装：

```bash
uv tool install "x-tweet-fetcher @ git+https://github.com/LiangsLi/x-tweet-fetcher.git@main"
```

然后从仓库检出 Skill 并复制到个人 Skill 目录：

```bash
git clone --depth 1 https://github.com/LiangsLi/x-tweet-fetcher.git
mkdir -p "${CODEX_HOME:-$HOME/.codex}/skills"
cp -R x-tweet-fetcher/skills/fetch-x-post "${CODEX_HOME:-$HOME/.codex}/skills/"
```

重新加载 Agent 客户端后，可以显式调用：

```text
使用 $fetch-x-post 阅读并总结这个 Article：
https://x.com/ClaudeDevs/status/2074208949205881033
```

Skill 的核心说明位于 [`skills/fetch-x-post/SKILL.md`](skills/fetch-x-post/SKILL.md)。

## 工作原理

```text
X/Twitter status 或 article URL
              ↓
      解析用户名与 Post ID
              ↓
   请求 FxTwitter 公共 API v2
              ↓
瞬时故障或异常响应时回退旧接口
              ↓
    规范化为 XDocument / JSON 1.0
```

默认优先请求：

```text
https://api.fxtwitter.com/2/status/{post_id}
```

只有 v2 出现临时不可用或响应异常时，才会尝试旧接口。明确的 `404` 不会回退，避免把真正的
“不存在”误判为临时故障。

FxTwitter 是独立第三方服务，不属于 X，也没有可用性 SLA。请求时，目标 Post ID 和相关 URL
信息会发送给 FxTwitter；如果你的场景不允许使用第三方上游，请不要使用本项目。

## 开发与验证

克隆仓库并安装开发依赖：

```bash
git clone git@github.com:LiangsLi/x-tweet-fetcher.git
cd x-tweet-fetcher
uv sync --extra dev
```

运行测试、代码检查和构建：

```bash
uv run pytest
uv run ruff check src tests
uv build
```

测试使用本地 fixtures 和模拟 HTTP 请求，CI 不依赖真实 X 或 FxTwitter 网络访问。

## 相关文档

- [Skill 使用说明](skills/fetch-x-post/SKILL.md)
- [完整输出结构与样例](skills/fetch-x-post/references/output-schema.md)
- [v4 精简版技术提案](docs/proposals/slim-url-reader-package.md)
- [版本变更记录](CHANGELOG.md)
- [迁移说明](MIGRATION.md)

## 许可证

本项目使用 [MIT License](LICENSE)。
