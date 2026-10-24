# CenryWang 个人主页

线上地址：<https://cenrywang.github.io/>

## 目录结构

- `index.html` — 首页（关于 / 技能 / 作品 / 推荐 / 工具 / 简报 / 现在 / 博客 / 留言 / 联系）
- `style.css` — 首页样式（含亮/暗双主题变量）
- `script.js` — 首页交互（粒子背景 / 打字机 / 滚动进度条 / 主题切换）
- `merge-quest.html` — **合成大冒险 · Merge Quest** 游戏页，单文件自包含，开箱即玩
- `now.html` — **现在在做什么** 页面（nownownow 风格，记录当前重心，文案自行更新）
- `guestbook.html` — **访客留言墙**（基于 giscus / GitHub Discussions，需先完成下方配置）
- `tools.html` — **工具严选**：分类展示精选工具（AI 助手 / 开发 / Windows 效率 / 学习科研 / 设计素材 / 我做的），每张卡片带 👍 点赞（countapi.xyz 计数，localStorage 防重复）
- `digest.html` — **每日简报**（RSS 聚合日报，Actions 每日自动生成，**勿手改、勿从本地覆盖**）
- `404.html` — 自定义 404 页（GitHub Pages 会自动使用它；承接已下线的 hot / robotics 旧链接）
- `blog/` — **博客**：`posts/*.md` 是文章源（Markdown + frontmatter），`index.html` 与 `<slug>.html` 由 `scripts/build_blog.py` 构建生成（**勿手改生成的 html**）
- `scripts/` — 页面生成脚本（`build_digest.py` 简报、`build_blog.py` 博客）
- `.github/workflows/` — 定时任务（`sync-digest` 每日同步简报、`keepalive` 防止定时任务被自动禁用）
- `.nojekyll` — 禁用 GitHub Pages 的 Jekyll 处理（本站纯静态；防止生成页内容被 Liquid 误解析）

## 作品列表

- **合成大冒险 · Merge Quest** — 物理合成类休闲小游戏（Canvas + Matter.js）
  - 在线游玩：<https://cenrywang.github.io/merge-quest.html>（本仓库 `merge-quest.html`）
- **AIToolsChain · AI 工具链** — Windows AI 工具安装管理器（Tauri v2 / Rust + TypeScript）
  - 源码 / 下载：<https://github.com/CenryWang/AIToolsChain>
- **CherryStudio 工具说明书** — CherryStudio 桌面版使用说明（自整理）
  - 文档：<https://my.feishu.cn/docx/DZvcdVzI0oZQQFxIZ8mc5h9Cnbf?from=from_parent_docx>（飞书，可能需登录）
  - 工具官网：<https://cherry-ai.com>

## 推荐 / 友链

首页导航「推荐」区块放外部优质信源卡片（非本人作品，纯友链性质）：

- **数字生命卡兹克 · AIHOT** — AI 资讯聚合站（每天抓取 168 个精选信源，用 AI 筛掉噪声）：<https://aihot.news/>
  - RSS：<https://aihot.news/feed.xml>（已换到新域名，旧 `aihot.virxact.com` 2026-10-31 停用）

## 每日简报（GitHub Actions 自动生成）

首页导航的「简报」入口由 Actions 定时生成，页头同时标注「源数据生成时间」和「本站同步时间」：

- 数据来自 garss fork（<https://github.com/CenryWang/garss>，每天北京时间 06:00 抓取 RSS 生成日报并发邮件），本仓库 `sync-digest` 工作流每天 07:30 把它渲染成站点风格的页面
- 简报同时合并 **AIHOT**（数字生命卡兹克的 AI 资讯聚合站）作为附加源：工作流额外抓取 `https://aihot.news/feed.xml`，取近 3 天精选（上限 20 条）渲染为「AIHOT 精选 · 数字生命卡兹克」区块，标注来源与版权。AIHOT 抓取失败或最新条目超过 7 天（疑似停更）时自动跳过该区块，不影响 garss 主源
- 简报还合并 **热搜雷达 · TrendRadar**：TrendRadar 跑在你的轻量服务器上（聚合微博/知乎/抖音等热榜，存进 SQLite），由 `scripts/trendradar_to_rss.py` 适配器把最新 SQLite 转成 RSS，GA 再当作第二个附加源抓进来，渲染为「热搜雷达 · TrendRadar」区块。服务器不可达或抓取失败时该区块自动跳过，不影响主源
- 想调整日报订阅改 garss fork 的 `EditREADME.md`
- 用自带 `GITHUB_TOKEN` 即可跑；**仅当接入 TrendRadar 时**需要额外配置仓库密钥 `TRENDRADAR_RSS_URL`（值为你服务器上适配器的带 token 访问地址，如 `https://你的域名:8088/rss.xml?token=xxx`）。不接 TrendRadar 时忽略此密钥，工作流照常运行
- **源数据过期会让工作流变红**：`build_digest.py` 会解析源 README 的「生成时间」，超过 3 天或非预期格式就直接退出（而不是把旧日报再发一遍）。上游停更时你看 Actions 是红的，而不是页面上看到一份一个月前的日报却毫无察觉

## 定时任务维护

- **60 天无提交会自动禁用 schedule**（GitHub 官方行为，只发一封邮件）。仓库现在靠每日简报的自动提交维持活跃；`keepalive` 工作流每月 1 号检查一次，只有最近提交已超过 45 天才补一个空 commit。正常运行时永远不会触发，不污染历史
- 站点内容由 bot 自动提交，**本地副本经常落后于远端**。从本地同步文件到推送目录时，`digest.html` 这类生成物要以远端为准（否则会把最新内容覆盖成旧版）

## 访问量统计

首页页脚集成了[不蒜子](https://busuanzi.ibruce.info/)（busuanzi）计数器，显示「本站总访问量 / 访客数」。纯前端接入，无需注册；脚本异步加载，服务不可用时统计行自动隐藏。数据按域名 `cenrywang.github.io` 累计，正式上线后从 0 开始计数。

## 主题切换（亮 / 暗）

首页、`now.html`、`guestbook.html` 右上角有明暗切换按钮，选择写入 `localStorage`，刷新保持；首屏在 `<head>` 内联脚本提前应用，避免闪烁。亮色主题通过 `style.css` 的 `[data-theme="light"]` 变量覆盖实现，不影响默认暗色科技风。

## 访客留言（giscus）

`guestbook.html` 用 [giscus](https://giscus.app)（基于 GitHub Discussions，免费、无需额外注册）承载留言。首次使用前需在 GitHub 侧完成一次性配置，然后把 `guestbook.html` 里的两处占位替换掉：

1. 仓库 `CenryWang/CenryWang.github.io` 必须是 **Public**，并在仓库 `Settings → General → Features` 开启 **Discussions**
2. 安装 giscus App：<https://github.com/apps/giscus>（授权该仓库）
3. 打开 <https://giscus.app>，填入仓库、选好分类（如「留言」），复制生成的 `data-repo-id` 与 `data-category-id`
4. 把 `guestbook.html` 中 `data-repo-id="REPO_ID"` 与 `data-category-id="CATEGORY_ID"` 两处占位替换成真实值即可

主题切换会自动通过 `postMessage` 同步给 giscus 评论区（暗色↔亮色）。

## 博客（内容管线）

零依赖纯静态博客，文章用 Markdown 写、Python 标准库构建，**无需任何第三方包**：

1. 在 `blog/posts/` 新建一个 `.md` 文件，头部写 frontmatter：

   ```markdown
   ---
   title: 文章标题
   date: 2026-10-24
   description: 一句话简介
   tags: 标签1, 标签2
   slug: my-post
   ---

   正文用普通 Markdown（标题 / 列表 / 引用 / 行内代码 / 代码块 / 链接 / 加粗 / 斜体）。
   ```

2. 运行构建，自动生成 `blog/index.html` 与 `blog/<slug>.html`：

   ```bash
   python scripts/build_blog.py
   ```

3. 生成的 `blog/*.html` 复用首页 `style.css` 与 `script.js`（粒子背景、明暗主题、滚动揭示自动带上）。文章页已预留 giscus 评论位，可后续接入。

> 构建产物是生成文件，提交前重新跑一遍脚本即可；不要手工改 `blog/index.html` 与 `<slug>.html`，改 `posts/*.md` 源文件。

## 联系方式（首页已配置）

- Email：cenrywang@foxmail.com
- GitHub：<https://github.com/CenryWang>
- 小红书：<https://xhslink.cn/o/GKuYm3zIMN>

## 关于游戏

`merge-quest.html` 由 [Merge Quest](../../ZcodeWorkspace/Pro01) 项目用 Vite 单文件构建生成
（`vite-plugin-singlefile`，JS/CSS 全部内联）。更新游戏时，重新构建后覆盖该文件即可：

```bash
cd G:/MyWorkspace/ZcodeWorkspace/Pro01 && npm run build
cp dist/index.html  G:/MyWorkspace/Myproject/personal-site/merge-quest.html
```

## 本地预览

直接用浏览器打开 `index.html`，或在仓库根目录起一个静态服务：

```bash
npx serve .
```
