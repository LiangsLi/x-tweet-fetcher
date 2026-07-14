# X URL Reader 精简分支技术提案

- 状态：Accepted
- 日期：2026-07-14
- 建议分支：`codex/slim-url-reader`
- 基线：当前 `main` HEAD（包含 FxTwitter v2 与 X Article 富文本修复）

## 1. 摘要

在新分支上将 `x-tweet-fetcher` 收敛为一个单一用途的 Python 包：输入一个公开的
X/Twitter `status` 或公开 `article` URL，获取对应帖子，并将普通帖子、Note Tweet、
引用内容、媒体以及内嵌 X Article 统一转换成适合阅读器和 Agent 消费的结构化 JSON。

精简分支保留 FxTwitter v2 主接口、旧接口故障兜底、HTTP 重试、媒体解析和 X Article
富文本到 Markdown 的完整重建；删除搜索、时间线、回复、用户资料、Lists、提及监控、
Nitter、Camofox、Playwright 和通用后端路由。

该分支继续使用标准 `src/` Python 包布局，能够生成 wheel 和 sdist，支持被其他 Python
项目安装，并提供安装后的 `xtf` 命令行入口。

## 2. 背景与问题

当前项目面向通用 X 数据获取，包含三种后端和多个互不相关的功能模式。当前
`src/xtf` 约有 3,800 行 Python，复杂度主要来自：

- Nitter 搜索、时间线和回复解析；
- Camofox 与 Playwright 两套浏览器驱动；
- 浏览器快照解析和分页；
- 后端协议、自动回退路由；
- Lists、用户资料和提及监控；
- 为所有模式服务的 CLI、模型和双语提示。

目标使用场景更窄：文献阅读器或 Agent 已经拥有一个确定的 X URL，只需要可靠地读取
该 URL 指向的帖子或 Article。搜索、发现、时间线和社交关系数据不属于这条链路。

当前 `--url` 实际上已经只调用 FxTwitter；Nitter 与浏览器并未为单帖获取提供回退。
因此删除其他后端不会降低现有 `--url` 路径的实际能力。

## 3. 目标

### 3.1 功能目标

1. 接受以下公开 URL：
   - `https://x.com/{user}/status/{post_id}`
   - `https://twitter.com/{user}/status/{post_id}`
   - `https://x.com/{user}/article/{post_id}`
   - `https://twitter.com/{user}/article/{post_id}`
   - 上述 URL 带查询参数、锚点或末尾斜杠的形式。
2. 获取普通 Post、长 Note Tweet 以及包含 X Article 的 Post。
3. 保留作者、发布时间、互动数据、引用 Post、图片、视频和媒体元数据。
4. 将 X Article 完整转换为 Markdown，至少保留：
   - 标题层级；
   - 段落；
   - 有序和无序列表及缩进；
   - 引用块；
   - 粗体、斜体、删除线；
   - 链接；
   - 行内代码；
   - 围栏代码块及上游提供的语言标识；
   - 分割线；
   - 封面和正文内嵌图片；
   - 内嵌 Post 链接。
5. 同时提供稳定的 Python API 和 JSON-only CLI。
6. 以标准 Python wheel/sdist 形式被其他项目安装。

### 3.2 工程目标

- 保持零运行时第三方依赖，使用 Python 标准库完成 HTTP 与 JSON 处理；
- 将公共 API 收敛为“URL 到文档”，不暴露后端路由概念；
- JSON 输出带显式 `schema_version`，为阅读器提供稳定契约；
- 网络、上游和解析错误具有机器可读的错误码；
- 所有解析测试使用本地 fixture，不在 CI 中依赖真实 X/FxTwitter 网络；
- 目标源代码规模约 700～900 行，不以牺牲富文本完整性换取更少行数。

## 4. 非目标

精简分支不支持：

- 搜索、趋势或内容发现；
- 用户时间线、Lists 和用户资料；
- 回复、评论树和对话线程；
- 提及监控；
- 私密、删除、地区限制、年龄限制或必须登录才能读取的内容；
- 发布、点赞、转发等写操作；
- Nitter、浏览器自动化或 X 登录会话管理；
- 批量爬取和大规模归档；
- 默认下载图片、视频二进制文件到本地。

`https://x.com/i/article/{article_id}` 不在第一阶段支持范围内。该 URL 使用 Article ID，
不保证能直接映射到承载文章的 Post ID；当前实现需要浏览器访问。若实际语料中频繁出现
这种链接，应在后续作为独立、可选的解析扩展处理，而不是把整个浏览器后端带回核心包。

## 5. 产品接口

### 5.1 Python API

唯一主要入口：

```python
from xtf import fetch

document = fetch("https://x.com/ClaudeDevs/status/2074208949205881033")

print(document.title)
print(document.content_markdown)
payload = document.to_dict()
```

建议签名：

```python
def fetch(url: str, *, timeout: float = 30.0) -> XDocument:
    ...
```

同时提供语义更明确的别名：

```python
from xtf import fetch_url
```

`fetch` 和 `fetch_url` 指向同一实现。公共包不再导出 `Router`、`Backend`、`Tweet`、
`Reply`、`Profile` 等通用采集抽象。

### 5.2 CLI

首选形式：

```bash
xtf https://x.com/ClaudeDevs/status/2074208949205881033
```

为现有使用方式保留兼容别名：

```bash
xtf --url https://x.com/ClaudeDevs/status/2074208949205881033
xtf -u https://x.com/ClaudeDevs/status/2074208949205881033
```

辅助参数：

```text
--pretty         缩进输出 JSON
--timeout N      单次上游请求超时秒数
--version        显示包版本
```

CLI 的 stdout 只输出一个 JSON 对象；诊断和重试提示写入 stderr。成功退出码为 `0`，获取
或解析失败为 `1`，参数用法错误为 `2`。调用者应依据 JSON 中的错误码判断具体原因，而
不是依赖错误文案。

## 6. JSON 契约

成功结果建议采用阅读器优先、而不是 FxTwitter 原始结构优先的 schema：

```json
{
  "schema_version": "1.0",
  "source": "x",
  "source_url": "https://x.com/ClaudeDevs/status/2074208949205881033",
  "canonical_url": "https://x.com/ClaudeDevs/status/2074208949205881033",
  "post_id": "2074208949205881033",
  "kind": "article",
  "title": "Article title",
  "author": {
    "name": "Claude Developers",
    "handle": "ClaudeDevs"
  },
  "published_at": "...",
  "post_text": "Text attached to the post",
  "content_text": "Plain readable article text...",
  "content_markdown": "# Heading\n\n```markdown\n...\n```",
  "media": [
    {
      "type": "image",
      "role": "inline",
      "url": "https://pbs.twimg.com/...",
      "width": 1600,
      "height": 900
    }
  ],
  "quote": null,
  "metrics": {
    "likes": 0,
    "reposts": 0,
    "replies": 0,
    "bookmarks": 0,
    "views": 0
  },
  "language": "en"
}
```

字段约定：

- `kind` 只允许 `post` 或 `article`；
- 普通 Post 的 `title` 为 `null`，`content_markdown` 为帖子正文；
- Article 的 `content_markdown` 是阅读器应优先消费的规范正文；
- `content_text` 从原始 block 内容生成，供全文索引和纯文本模型使用；
- `post_text` 始终保留承载 Article 的 Post 文案，避免文章正文覆盖帖子上下文；
- 图片同时出现在正确位置的 Markdown 中和结构化 `media` 数组中；
- `media.role` 可为 `post`、`cover`、`inline` 或 `quote`；
- 视频保留 URL、缩略图、时长和可用 variants，但默认不下载二进制内容；
- 可选字段缺失时使用 `null` 或空数组，schema 中的固定字段不因后端数据为空而消失；
- 不默认返回完整上游原始 JSON，避免不稳定结构泄漏到公共契约。

错误结果：

```json
{
  "schema_version": "1.0",
  "source_url": "...",
  "error": {
    "code": "upstream_unavailable",
    "message": "FxTwitter is temporarily unavailable",
    "retryable": true
  }
}
```

错误码至少包括：

- `invalid_url`
- `not_found`
- `rate_limited`
- `upstream_unavailable`
- `invalid_upstream_response`
- `unsupported_content`

## 7. 上游访问策略

1. 从 URL 提取 Post ID 和作者 handle；
2. 首先请求 FxTwitter v2：`/2/status/{post_id}`；
3. 对网络错误、5xx、无效 JSON 或缺失 v2 payload，尝试旧接口：
   `/{user}/status/{post_id}`；
4. 明确的 404 不回退，直接返回 `not_found`；
5. 对 429 和暂时性错误采用有上限的指数退避；
6. 对响应体设置大小上限，避免异常上游消耗无限内存；
7. 校验 envelope 和关键字段类型，再进入内容规范化；
8. 上游响应不得直接原样成为公共 JSON schema。

旧接口兜底只提高 FxTwitter 自身版本兼容性，不被描述为独立后端或可用性 SLA。

## 8. 内部架构

建议目录：

```text
src/xtf/
├── __init__.py       # 仅导出 fetch/fetch_url、XDocument 和公共异常
├── cli.py            # JSON-only 命令行入口
├── client.py         # URL -> FxTwitter -> XDocument 主流程
├── models.py         # XDocument、Author、Media、Metrics、Quote
├── http.py           # 有界响应、超时、重试和 JSON 解码
├── errors.py         # 稳定错误码与异常类型
├── urls.py           # status/article URL 解析与 canonical URL
├── normalize.py      # Post、Quote、媒体与指标规范化
└── article.py        # Draft.js Article -> plain text + Markdown
```

不再保留：

```text
backends/base.py
backends/nitter.py
backends/browser.py
backends/_camofox_driver.py
backends/_playwright_driver.py
parsers/nitter_html.py
parsers/snapshot.py
router.py
monitor.py
```

此结构保留职责边界，但避免为了一个 FxTwitter 数据源引入 Strategy/Router 抽象。若未来
新增真正的官方 API 或 Direct-X fallback，应先证明需求，再引入小型 client adapter，
而不是提前恢复通用后端框架。

## 9. Python 包管理

### 9.1 包身份

- distribution name：`x-tweet-fetcher`
- import package：`xtf`
- CLI：`xtf`
- Python：`>=3.10`
- license：MIT
- 精简分支开发版本建议：`4.0.0.dev0`

这是一次破坏性范围收缩，因此若最终合并或发布，应提升主版本。仅从 Git 分支安装时，
开发版本足以区分当前 v3 通用版本。

### 9.2 构建配置

继续使用 `pyproject.toml` 和 `src/` layout。构建后必须同时得到：

```text
dist/x_tweet_fetcher-*.whl
dist/x_tweet_fetcher-*.tar.gz
```

保留：

```toml
[project.scripts]
xtf = "xtf.cli:main"
```

运行时保持零依赖；开发依赖至少包括 `pytest` 和 `ruff`。版本只保留一个真源，运行时
通过 `importlib.metadata.version("x-tweet-fetcher")` 获取，避免 `VERSION`、
`pyproject.toml` 和 `__init__.py` 三处漂移。

### 9.3 安装场景

本地开发：

```bash
uv sync --extra dev
uv run xtf https://x.com/user/status/123
```

从 Git 分支安装：

```bash
pip install "x-tweet-fetcher @ git+https://github.com/ythx-101/x-tweet-fetcher.git@codex/slim-url-reader"
```

其他项目通过 `uv add` 或 PEP 508 Git dependency 固定到明确 commit；生产环境不建议只
固定可移动的分支名。

## 10. 测试策略

### 10.1 单元测试

- URL：两种域名、两种路由、查询参数、锚点、非法域名和非法 ID；
- HTTP：超时、404、429、5xx、无效 JSON、响应体上限和重试次数；
- v2 envelope 与旧接口 envelope；
- 普通 Post、Note Tweet、引用 Post、图片和视频；
- Article 标题、列表、缩进、链接、行内样式、分割线；
- 围栏代码块及语言标识；
- 封面和正文图片在 Markdown 与 `media` 中的一致性；
- 纯文本和 Markdown 内容顺序一致；
- 固定字段与 `schema_version`。

### 10.2 Fixture 与回归测试

保留当前真实 FxTwitter Article fixture，并补充：

- 普通 Post fixture；
- Note Tweet fixture；
- 引用 + 媒体 fixture；
- 包含多种 Draft.js block/entity 的 Article fixture；
- v2 异常 envelope 与旧接口成功 envelope。

回归测试必须显式断言截图中曾丢失的代码块内容，避免只检查标题、字数或图片数量。

### 10.3 包验收

CI 或本地发布检查应执行：

```bash
uv run ruff check src tests
uv run pytest
uv build
```

随后在临时虚拟环境安装生成的 wheel，并验证：

```bash
xtf --help
xtf --version
python -c "from xtf import fetch"
```

CLI 网络调用使用 mock/fixture，不把真实 FxTwitter 可用性作为 CI 成功条件。

## 11. 分支与迁移策略

1. 从当前 HEAD 创建 `codex/slim-url-reader`，确保富文本和 FxTwitter v2 修复成为基线；
2. 先增加新的 `XDocument` schema、`fetch(url)` API 和对应测试；
3. 将现有 `--url` 实现迁移到新 client，并验证 JSON 完整性；
4. 删除不再需要的后端、解析器、模型和 CLI 模式；
5. 更新 README、SKILL.md、包描述和示例，只宣称精简分支实际支持的能力；
6. 构建并在干净环境安装 wheel；
7. 使用至少一个普通 Post 和当前 ClaudeDevs Article 做人工端到端验证；
8. 精简分支不改变当前通用 `main`，直到明确决定是否用精简版本替代主线。

旧的 `Router` Python API 和 `--search/--user/...` CLI 不提供兼容层，因为保留兼容层会
重新引入本提案要消除的复杂度。若有现有消费者，应继续固定 v3 或当前 `main`。

## 12. 风险与缓解

### FxTwitter 是单一外部依赖

风险：公共服务无 SLA，可能限流、停机或随 X 变化。

缓解：保留 v2/旧接口回退、有限重试、明确错误码、短期调用方缓存，以及本地 fixture
回归测试。精简分支不声称离线或永久可用。

### 上游 Article schema 漂移

风险：Draft.js block/entity 类型或媒体字段可能变化。

缓解：未知 block 尽可能保留原始文本；未知 entity 不应导致整篇失败；以真实 fixture
锁定代码块、链接和图片；解析失败返回明确错误而不是静默空正文。

### 图片 URL 不是本地归档

风险：阅读器稍后打开时，远程图片可能失效或受到网络限制。

缓解：第一阶段返回原图 URL 和尺寸，并在 Markdown 中保留位置。二进制下载与 URL
重写可作为阅读器侧职责或后续 `download_media()` 扩展，不进入核心 fetch 流程。

### 功能范围被再次扩大

风险：逐步加入搜索、时间线和浏览器后重新回到当前复杂度。

缓解：任何新增能力必须仍然服务“给定 URL 到可阅读文档”；发现和社交图谱功能应位于
独立包或当前通用主线。

## 13. 验收标准

精简分支完成需同时满足：

1. wheel 能被一个全新 Python 3.10+ 环境安装；
2. 安装后 `xtf URL` 输出合法、单一的 JSON 对象；
3. Python 调用方可通过 `from xtf import fetch` 获取 `XDocument`；
4. `status` 与公开 `article` 路由得到同一 Post ID 时输出等价内容；
5. 普通 Post、Note Tweet、引用、图片和视频被结构化保留；
6. ClaudeDevs 示例 Article 的正文、代码块、链接、标题和图片全部存在；
7. Article 图片同时出现在 Markdown 正确位置和 `media` 数组；
8. v2 上游暂时失败时会尝试旧接口；
9. 404、限流、上游故障和无效响应返回稳定错误码；
10. 测试、lint、wheel/sdist 构建和干净环境安装检查全部通过；
11. 核心包不导入 Nitter、Camofox、Playwright 或浏览器相关模块；
12. README 明确列出支持与不支持的 URL/内容范围。

## 14. 建议结论

该需求合理，且适合用独立分支验证。推荐实施本提案中的“硬精简”方案，而不是仅在现有
通用包外再包一层 façade：当前非目标模块不会为核心 `--url` 路径提供可用性回退，却会
持续增加安装认知、测试范围和维护成本。

富文本 Article 渲染、媒体规范化、HTTP 边界和 fixture 测试属于核心能力，应完整保留；
后端抽象、浏览器、Nitter 和发现类功能应从精简分支移除。
