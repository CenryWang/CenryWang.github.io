# CenryWang 个人主页

线上地址：<https://cenrywang.github.io/>

## 目录结构

- `index.html` — 首页（关于 / 技能 / 作品 / 联系）
- `style.css` — 首页样式
- `script.js` — 首页交互（粒子背景 / 打字机 / 滚动进度条等）
- `merge-quest.html` — **合成大冒险 · Merge Quest** 游戏页，单文件自包含，开箱即玩
- `digest.html` — **每日简报**（RSS 聚合日报，Actions 每日自动生成，**勿手改、勿从本地覆盖**）
- `404.html` — 自定义 404 页（GitHub Pages 会自动使用它；承接已下线的 hot / robotics 旧链接）
- `scripts/` — 上述页面的生成脚本
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

## 每日简报（GitHub Actions 自动生成）

首页导航的「简报」入口由 Actions 定时生成，页头同时标注「源数据生成时间」和「本站同步时间」：

- 数据来自 garss fork（<https://github.com/CenryWang/garss>，每天北京时间 06:00 抓取 RSS 生成日报并发邮件），本仓库 `sync-digest` 工作流每天 07:30 把它渲染成站点风格的页面
- 想调整日报订阅改 garss fork 的 `EditREADME.md`
- 用自带 `GITHUB_TOKEN`，无需任何额外密钥
- **源数据过期会让工作流变红**：`build_digest.py` 会解析源 README 的「生成时间」，超过 3 天或非预期格式就直接退出（而不是把旧日报再发一遍）。上游停更时你看 Actions 是红的，而不是页面上看到一份一个月前的日报却毫无察觉

## 定时任务维护

- **60 天无提交会自动禁用 schedule**（GitHub 官方行为，只发一封邮件）。仓库现在靠每日简报的自动提交维持活跃；`keepalive` 工作流每月 1 号检查一次，只有最近提交已超过 45 天才补一个空 commit。正常运行时永远不会触发，不污染历史
- 站点内容由 bot 自动提交，**本地副本经常落后于远端**。从本地同步文件到推送目录时，`digest.html` 这类生成物要以远端为准（否则会把最新内容覆盖成旧版）

## 访问量统计

首页页脚集成了[不蒜子](https://busuanzi.ibruce.info/)（busuanzi）计数器，显示「本站总访问量 / 访客数」。纯前端接入，无需注册；脚本异步加载，服务不可用时统计行自动隐藏。数据按域名 `cenrywang.github.io` 累计，正式上线后从 0 开始计数。

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
