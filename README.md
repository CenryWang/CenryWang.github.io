# CenryWang 个人主页

线上地址：<https://cenrywang.github.io/>

## 目录结构

- `index.html` — 首页（关于 / 技能 / 作品 / 推荐 / 工具 / 简报 / 现在 / 博客 / 联系）
- `style.css` — 全站样式（含亮/暗双主题变量）
- `script.js` — 全站交互（粒子背景 / 打字机 / 滚动进度条 / 主题切换 / 减少动态效果）
- `merge-quest.html` — **合成大冒险 · Merge Quest** 游戏页，单文件自包含，开箱即玩
- `now.html` — **现在在做什么** 页面（nownownow 风格，记录当前重心，文案自行更新）
- `tools.html` — **工具严选**：按场景分类聚合常用工具与 Agent Skills，带纯前端搜索过滤，零第三方依赖
- `metals.html` — **贵金属与宏观行情**：黄金 / 白银 / 金银比 / 10 年期美债 / 贸易加权美元指数，今日值 + 区间变化 + 30 年月度回溯曲线
- `data/metals.json` — 行情数据（`metals` 工作流每日自动生成，**勿手改**）
- `digest.html` — **每日简报**（RSS 聚合日报，Actions 每日自动生成，**勿手改、勿从本地覆盖**）
- `404.html` — 自定义 404 页（GitHub Pages 会自动使用它；承接已下线的 hot / robotics / 留言墙 旧链接）
- `blog/` — **博客**：`posts/*.md` 是文章源（Markdown + frontmatter），`index.html` 与 `<slug>.html` 由 `scripts/build_blog.py` 构建生成（**勿手改生成的 html**）
- `scripts/` — 页面生成与运维脚本：
  - `nav.py` — **全站导航的唯一配置源**
  - `sync_nav.py` — 把导航同步到所有手写页面
  - `build_digest.py` — 每日简报生成
  - `build_blog.py` — 博客构建
  - `build_metals.py` — 贵金属与宏观行情数据构建（纯标准库）
  - `check_site_health.py` — 线上站点健康自检
  - `trendradar_to_rss.py` / `trr_crawler.py` — 服务器端 TrendRadar 适配器与爬虫
- `.github/workflows/` — 定时任务（`sync-digest` 每日同步简报、`metals` 每日生成行情数据、`site-health` 每日自检、`keepalive` 防止定时任务被自动禁用）
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
- 另合并 **arXiv cs.AI / cs.RO / cs.MA** 三路每日新论文（周六周日 arXiv 不发布更新，届时区块缺席属正常）
- 想调整日报订阅改 garss fork 的 `EditREADME.md`
- 用自带 `GITHUB_TOKEN` 即可跑；**仅当接入 TrendRadar 时**需要额外配置仓库密钥 `TRENDRADAR_RSS_URL`（值为服务器上适配器的带 token 访问地址）。更换服务器后记得同步更新这个密钥
- **源数据过期会让工作流变红**：`build_digest.py` 会解析源 README 的「生成时间」，超过 3 天或非预期格式就直接退出（而不是把旧日报再发一遍）。上游停更时你看 Actions 是红的，而不是页面上看到一份一个月前的日报却毫无察觉

## 定时任务维护

- **60 天无提交会自动禁用 schedule**（GitHub 官方行为，只发一封邮件）。仓库现在靠每日简报的自动提交维持活跃；`keepalive` 工作流每月 1 号检查一次，只有最近提交已超过 45 天才补一个空 commit。正常运行时永远不会触发，不污染历史
- 站点内容由 bot 自动提交，**本地副本经常落后于远端**。从本地同步文件到推送目录时，`digest.html` 这类生成物要以远端为准（否则会把最新内容覆盖成旧版）
- `site-health` 每天北京时间 07:50 检查线上页面（见下节），不产生提交

## 导航统一

所有页面的导航栏都由 `scripts/nav.py` 一处定义，共 10 个入口。改动流程：

```bash
# 1. 改 scripts/nav.py 里的 HOME_LINKS / SUB_LINKS
python scripts/sync_nav.py      # 同步到 index.html / now.html / tools.html / 404.html
python scripts/build_blog.py    # 重新生成 blog/*.html
```

`build_blog.py` 与 `build_digest.py` 会直接 import `nav.py`，所以博客页和每日自动生成的简报页也使用同一套导航，不会被 bot 覆盖回旧版本。404 与简报页使用 `/` 绝对路径（任意 URL 下都正确），且不输出明暗切换按钮（它们有自己的内联脚本，不加载 `script.js`）。

新增/下线栏目时，记得同步更新 `scripts/check_site_health.py` 里的 `NAV_REQUIRED` 与 `FORBIDDEN` 列表。

## 站点健康自检

`scripts/check_site_health.py`（纯标准库）每天由 `site-health` 工作流调用，检查：

- 11 个资源（含行情页、行情数据与 `script.js`）是否全部返回 200
- 简报页头的「同步于 YYYY-MM-DD」是否在 3 天内
- `data/metals.json` 的 `generated_at` 是否在 3 天内、指标数量是否正常
- 页面上是否还残留已下线功能的引用（留言页 / countapi 点赞 / giscus 脚本）
- 首页导航是否包含统一的 5 个独立页入口

**任一项失败都会以非零码退出，让 Actions 变红**，不做静默降级。本地手动跑：

```bash
python scripts/check_site_health.py
```

## 贵金属与宏观行情看板

`metals.html` 读取同仓库的 `data/metals.json`，每天北京时间 07:40 由 `metals` 工作流重新生成。页面纯静态、零前端库、零 API 密钥、运行时不请求任何第三方接口。

**指标**：黄金、白银、金银比、10 年期美债收益率、美元指数（美联储广义贸易加权口径，**不是 ICE 的 DXY**）。
**时间维度**：今日值 + 1月 / 3月 / 1年 / 3年 / 10年 / 30年 的区间变化，另有可切换指标与窗口的 30 年月度回溯曲线。

数据源全部免费、无需注册或 API key：

| 来源 | 用途 | 许可 |
|---|---|---|
| `gold-api.com` | XAU / XAG 现货「今日值」 | 公开免费接口 |
| World Bank Commodity Markets "Pink Sheet" | 金银月度均价（1960 起）长周期序列 | CC BY 4.0，页面已署名 |
| FRED `DGS10` | 10 年期美债收益率 | 美国政府公开数据 |
| FRED `DTWEXBGS` | 广义贸易加权美元指数（2006 起） | 美国政府公开数据 |

几点口径约定，避免数字被误读：

- 所有指标统一降采样为月度序列（保留最近 30 年），**涨跌幅与曲线基于同一条序列**；卡片上的「今日值」是现货 / 最新观测，不与历史月均价混算。
- 10 年期美债是利率，变化以**基点 (bp)** 表示，不套用百分比涨跌幅。
- 美元指数用贸易加权口径，且 2006 年才有数据，30 年窗口如实留「—」，不拼接不同基期的旧序列。
- 世界银行 xlsx 的下载链接**每月轮换文档 ID**，`build_metals.py` 从官方页面动态解析当前链接；短周期（1月 / 3月）是月度均价参考值，不是日频收盘涨跌幅。

**失败即变红**：任一源不可达、数据为空、或时间戳超过阈值（现货 3 天 / FRED 14 天 / 世界银行 60 天），脚本直接 `exit 1`，Actions 变红，绝不静默发布空页或反复重发旧数据。

## 风险提示与合规边界

页面在**首屏**放置了不依赖 JavaScript 的静态风险提示，底部「数据来源与口径」区块还列出来源、许可、口径注意事项与免责声明；`data/metals.json` 里的 `sources` / `caveats` / `disclaimer` 由 `build_metals.py` 统一生成，页面渲染时读取，避免页面文案与数据文件脱节。

明确写出的风险包括：贵金属价格、利率与汇率波动剧烈，投资可能造成本金损失；公开来源数据可能延迟或存在误差，不保证实时、准确、完整，也不是交易报价；历史涨跌幅不代表未来表现；据此操作的风险与后果由读者自行承担。

页面定位是**纯数据展示**：不含投资建议、分析预测、买卖信号、收益承诺，不接交易平台 / 开户 / 返佣链接，不收费，也不放广告。不要往这个页面加「买入信号」「目标价」「拐点预警」之类的措辞——向公众提供行情的分析、预测或建议涉及证券投资咨询资质，性质完全不同。数据来源均标注名称、用途、链接与许可（World Bank Pink Sheet 为 CC BY 4.0，页面已署名）。

本地生成与预览：

```bash
python scripts/build_metals.py      # 生成 data/metals.json
python -m http.server 8000          # fetch 在 file:// 下会被浏览器拦截，必须走 HTTP
# 然后打开 http://localhost:8000/metals.html
```

调试时若本机网络受限，可用 `--cache-dir <目录>` 复用 curl 下载的响应副本（生产 workflow 不传此参数，始终实时抓取）；时间戳校验依然生效，旧缓存会直接报错。

## 访问量统计

首页页脚集成了[不蒜子](https://busuanzi.ibruce.info/)（busuanzi）计数器，显示「本站总访问量 / 访客数」。纯前端接入，无需注册；脚本异步加载，服务不可用时统计行自动隐藏。数据按域名 `cenrywang.github.io` 累计，正式上线后从 0 开始计数。

## 主题切换（亮 / 暗）

各页面右上角有明暗切换按钮，选择写入 `localStorage`，刷新保持；首屏在 `<head>` 内联脚本提前应用，避免闪烁。亮色主题通过 `style.css` 的 `[data-theme="light"]` 变量覆盖实现，不影响默认暗色科技风。

`script.js` 同时尊重系统的 `prefers-reduced-motion`：开启后关闭 CSS 动画之外的粒子循环、打字机与光标光晕，标签页不可见时也会跳过粒子绘制。

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

3. 生成的 `blog/*.html` 复用首页 `style.css` 与 `script.js`（粒子背景、明暗主题、滚动揭示自动带上）。

> 构建产物是生成文件，提交前重新跑一遍脚本即可；不要手工改 `blog/index.html` 与 `<slug>.html`，改 `posts/*.md` 源文件。

## 已下线的功能

- 热榜（hot board）、机器人文献（robotics）：旧链接统一由 `404.html` 承接
- 访客留言墙（`guestbook.html` / giscus）：2026-11-07 整块移除，包括导航入口、`script.js` 里的 giscus 消息同步与文章页评论位
- 工具页点赞（countapi.xyz）：第三方计数服务已不可用，改为纯严选清单 + 本地搜索过滤，不再依赖任何外部计数 API

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
