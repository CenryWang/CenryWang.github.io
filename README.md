# CenryWang 个人主页

线上地址：<https://cenrywang.github.io/>

## 目录结构

- `index.html` — **首页**主板块（关于 / 技能 / 作品 / 推荐 / 联系）
- `info.html` — **信息**主板块落地页，下设简报 / 工具 / 行情三个子板块
- `whimsy.html` — **奇思**主板块落地页（人生一万天 / 合成大冒险）
- `sitemap.html` — **站点导航页**，展示全站分支结构（由 `scripts/build_sitemap.py` 生成，**勿手改**）
- `style.css` — 全站样式（含亮/暗双主题变量、左侧板块目录、导航页分支树）
- `script.js` — 全站交互（粒子背景 / 打字机 / 滚动进度条 / 主题切换 / 人生一万天 / 减少动态效果）
- `merge-quest.html` — **合成大冒险 · Merge Quest** 游戏页，Vite 单文件自包含，开箱即玩；文件末尾追加了「← 奇思」返回入口与明暗主题接入段（**重新构建游戏时须保留该段**）
- `tools.html` — **工具严选**：7 个分类（AI大模型 / Coding工具 / 常用框架 / 常用工具软件 / 学习科研 / 设计绘图 / Agent Skills），带纯前端搜索过滤，零第三方依赖
- `metals.html` — **贵金属与宏观行情**：黄金 / 白银 / 金银比 / 10 年期美债 / 联邦基金有效利率 / 贸易加权美元指数六个指标，今日值 + 区间变化 + 30 年月度回溯曲线
- `data/metals.json` — 行情数据（`metals` 工作流每日自动生成，**勿手改**）
- `digest.html` — **每日简报**（RSS 聚合日报，Actions 每日自动生成，**勿手改、勿从本地覆盖**）
- `404.html` — 自定义 404 页（GitHub Pages 会自动使用它；承接已下线的 hot / robotics / 留言墙 / 现在 旧链接）
- `blog/` — **博客**：`posts/*.md` 是文章源（Markdown + frontmatter），`index.html` 与 `<slug>.html` 由 `scripts/build_blog.py` 构建生成（**勿手改生成的 html**）
- `scripts/` — 页面生成与运维脚本：
  - `nav.py` — **全站站点树的唯一配置源**（4 主板块 + 板块内目录 + 工具 7 分类）
  - `sync_nav.py` — 把顶部导航与左侧板块目录同步到所有页面（含 bot 生成的 digest.html）
  - `build_sitemap.py` — 从 nav.py 生成站点导航页
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

## 导航结构（4 主板块 + 左侧板块目录）

顶部主导航只有 **首页 / 信息 / 博客 / 奇思** 四个主板块，另有一个「导航」工具入口指向 `sitemap.html`。
每个主板块的页面左侧显示「板块内目录」（`render_sidebar()`），层级关系全部定义在 `scripts/nav.py` 的 `SITE_TREE`：

- 首页 → 关于我 / 技能 / 作品 / 推荐 / 联系
- 信息 → 板块概览 / 简报 / 工具 / 行情；**工具**展开后是 7 个分类锚点
- 博客 → 全部文章 + 每篇文章（`build_blog.py` 从 posts 动态注入）
- 奇思 → 人生一万天 / 合成大冒险

原先 9 个平铺入口把首页锚点和独立页面混在一行，层级不清、窄屏还容易折行；现在二级目录统一收进左侧，≤1000px 时侧栏自动变成导航下方的横向胶囊条（sticky 常驻）。

改动流程（**只改 `nav.py` 一处**）：

```bash
python scripts/sync_nav.py        # 同步全站导航 + 侧栏；--only <文件> 可只同步一个
python scripts/build_blog.py      # 重新生成 blog/*.html（侧栏要列出全部文章）
python scripts/build_sitemap.py   # 重新生成 sitemap.html（分支结构不能与站点脱节）
```

`build_blog.py` 与 `build_digest.py` 直接 import `nav.py`，所以博客页和每日自动生成的简报页也使用同一套导航；`sync-digest.yml` 生成简报后再跑一次 `sync_nav.py --only digest.html` 作为双保险。404 / 简报页用 `/` 绝对路径（任意 URL 下都正确）。`sync_nav.py` 的替换单元是「nav + 紧随其后的可选侧栏」，重复运行幂等，同时按有无侧栏维护 `<body class="has-board">`。

新增/下线栏目时，记得同步更新 `scripts/check_site_health.py` 的 `NAV_REQUIRED` / `NAV_CHECK_PAGES` / `SIDEBAR_PAGES` / `SITEMAP_REQUIRED` 与 `FORBIDDEN` 列表。

## 工具严选与奇思板块

- `tools.html` 的 7 个二级分类与 `nav.py` 的 `TOOL_CATEGORIES` 一一对应，标题带 `id="cat-*"` 锚点，左侧目录可直接跳转；搜索过滤会把无匹配的分类整块隐藏。
- 2026-11-15 移除 Perplexity / Docker / PowerToys / Figma / remove.bg；原「我做的」分类并入「常用工具软件」；补充 Vue 3 / Vite / React 三张框架卡，让「常用框架」这一分类成立。
- Magpie 条目按 `Blinue/Magpie` 官方 README 校正：名称、官方仓库链接、分类标签改为「窗口超分」，描述补充 Win+Shift+A 快捷键、WinUI 3 / 40+ 着色器效果与 Win10 1903+ / Win11 系统要求。
- 「人生一万天」计算器从首页迁入 `whimsy.html`（奇思板块），逻辑仍复用 `script.js`；首页只保留关于 / 技能 / 作品 / 推荐 / 联系。

## 站点健康自检

`scripts/check_site_health.py`（纯标准库）每天由 `site-health` 工作流调用，检查：

- 13 个资源（含信息 / 奇思 / 导航页、行情数据与 `script.js`）是否全部返回 200
- 简报页头的「同步于 YYYY-MM-DD」是否在 3 天内
- `data/metals.json` 的 `generated_at` 是否在 3 天内、指标数量是否正常
- 页面上是否还残留已下线功能的引用（留言页 / countapi 点赞 / giscus 脚本）
- 首页导航是否包含 4 个主板块与导航页入口，且 10 个页面的 4 项导航标签序列完全一致（防止简报页回退）
- 8 个板块页面是否都带左侧「板块内目录」；导航页是否列全部分支节点
- 11 个 HTML 页面是否都有 `localStorage` 主题预加载与可切换按钮；Vite 游戏页是否保留 `mqThemeToggle` 与 `html[data-theme="dark"]` 覆盖（防止重建游戏时把主题接入冲掉）

**任一项失败都会以非零码退出，让 Actions 变红**，不做静默降级。本地手动跑：

```bash
python scripts/check_site_health.py
```

## 贵金属与宏观行情看板

`metals.html` 读取同仓库的 `data/metals.json`，每天北京时间 07:40 由 `metals` 工作流重新生成。页面纯静态、零前端库、零 API 密钥、运行时不请求任何第三方接口。

**指标（6 个）**：黄金、白银、金银比、10 年期美债收益率、联邦基金有效利率（FRED DFF，政策利率的市场执行值，非 FOMC 目标区间）、美元指数（美联储广义贸易加权口径，**不是 ICE 的 DXY**）。
**时间维度**：今日值 + 1月 / 3月 / 1年 / 3年 / 10年 / 30年 的区间变化，另有可切换指标与窗口的 30 年月度回溯曲线。

数据源全部免费、无需注册或 API key：

| 来源 | 用途 | 许可 |
|---|---|---|
| `gold-api.com` | XAU / XAG 现货「今日值」 | 公开免费接口 |
| World Bank Commodity Markets "Pink Sheet" | 金银月度均价（1960 起）长周期序列 | CC BY 4.0，页面已署名 |
| FRED `DGS10` | 10 年期美债收益率 | 美国政府公开数据 |
| FRED `DFF` | 联邦基金有效利率（政策利率） | 美国政府公开数据 |
| FRED `DTWEXBGS` | 广义贸易加权美元指数（2006 起） | 美国政府公开数据 |

几点口径约定，避免数字被误读：

- 所有指标统一降采样为月度序列（保留最近 30 年），**涨跌幅与曲线基于同一条序列**；卡片上的「今日值」是现货 / 最新观测，不与历史月均价混算。
- 10 年期美债与联邦基金有效利率都是利率，变化以**基点 (bp)** 表示，不套用百分比涨跌幅。
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

**全站所有页面**（含 404 与每日简报）右上角都有明暗切换按钮，选择写入 `localStorage`，刷新保持；首屏在 `<head>` 内联脚本提前应用，避免闪烁。亮色主题通过 `style.css` 的 `[data-theme="light"]` 变量覆盖实现，不影响默认暗色科技风。404 与简报页改为加载 `script.js`（原先各自的内联脚本已移除），因此主题、滚动进度、揭示动画与页脚年份行为与其余页面完全一致；侧栏在亮色下使用接近不透明的白底，避免极光光晕透过面板影响小字可读性。

`merge-quest.html` 是 Vite 单文件产物，不加载 `style.css` / `script.js`，因此在文件内追加了一段自包含的接入代码：`<head>` 里读同一个 `localStorage.theme` 并覆盖游戏自身的 `:root` 变量与硬编码浅色面板，右下角常驻「← 奇思」返回链接与主题按钮（按钮层级高于游戏弹层，首次进入的引导卡不会挡住它）。**重新构建游戏时请保留这段**，健康自检会检查它是否还在。

窄屏（≤640px）顶部导航做了专门压缩：默认 18px 间距会让第四个主板块「奇思」溢出到「导航」按钮上被裁掉；末尾的高优先级 `@media` 把间距、logo、按钮尺寸一并收紧，390 / 375 / 360 / 320px 均已实测四项无横向溢出。

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

3. 生成的 `blog/*.html` 复用首页 `style.css` 与 `script.js`（粒子背景、明暗主题、滚动揭示自动带上）。博客索引页与文章页使用 `hero--compact` + `.section--tight`，让「全部文章」标题和文章卡片落在首屏——沿用首页全屏 hero 时，点进博客后首屏只有大字和粒子背景，看起来像没离开首页。改版式请改 `scripts/build_blog.py` 模板，不要手改生成页。

> 构建产物是生成文件，提交前重新跑一遍脚本即可；不要手工改 `blog/index.html` 与 `<slug>.html`，改 `posts/*.md` 源文件。

## 本地 / 面板预览

**直接打开 `blog/index.html` 只会看到裸文字**：预览服务按「被打开文件的所在目录」单独映射，此时 `blog/` 成了映射根，页面里的 `../style.css` / `../script.js` 会解析到映射之外 → 404。站点本身没问题（正常部署与从首页点进去都正常）。

需要看效果时生成自包含快照（CSS / JS 内联、站内链接全部改写到同一目录，任何映射方式都能完整显示）：

```bash
python scripts/build_preview.py                    # 输出到系统临时目录
python scripts/build_preview.py <输出目录>          # 指定目录
```

`build_preview.py` 会生成 11 个页面 + `data/metals.json` 的副本；快照**只用于预览，不要提交进站点**。

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
