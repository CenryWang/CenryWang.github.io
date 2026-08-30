# CenryWang 个人主页

线上地址：<https://cenrywang.github.io/>

## 目录结构

- `index.html` — 首页（关于 / 技能 / 作品 / 联系）
- `style.css` — 首页样式
- `script.js` — 首页交互（粒子背景 / 打字机 / 滚动进度条等）
- `merge-quest.html` — **合成大冒险 · Merge Quest** 游戏页，单文件自包含，开箱即玩
- `digest.html` — **每日简报**（RSS 聚合日报，Actions 每日自动生成，勿手改；首次生成前为占位页）
- `hot.html` — **热榜速览**（全网热榜聚合，Actions 每小时自动生成，勿手改；首次生成前为占位页）
- `scripts/` — 上述两个页面的生成脚本
- `.github/workflows/` — 定时生成工作流（sync-digest / hot-board）
- `.nojekyll` — 禁用 GitHub Pages 的 Jekyll 处理（本站纯静态；防止生成页内容被 Liquid 误解析）

## 作品列表

- **合成大冒险 · Merge Quest** — 物理合成类休闲小游戏（Canvas + Matter.js）
  - 在线游玩：<https://cenrywang.github.io/merge-quest.html>（本仓库 `merge-quest.html`）
- **AIToolsChain · AI 工具链** — Windows AI 工具安装管理器（Tauri v2 / Rust + TypeScript）
  - 源码 / 下载：<https://github.com/CenryWang/AIToolsChain>
- **CherryStudio 工具说明书** — CherryStudio 桌面版使用说明（自整理）
  - 文档：<https://my.feishu.cn/docx/DZvcdVzI0oZQQFxIZ8mc5h9Cnbf?from=from_parent_docx>（飞书，可能需登录）
  - 工具官网：<https://cherry-ai.com>

## 信息简报与热榜（GitHub Actions 自动生成）

首页导航的「简报」「热榜」两个入口由 Actions 定时生成，页脚均标注生成时间：

- **每日简报**（`digest.html`）：数据来自 garss fork（<https://github.com/CenryWang/garss>，每天北京时间 06:00 抓取 RSS 生成日报并发邮件），本仓库 `sync-digest` 工作流每天 07:30 把它渲染成站点风格的页面
- **热榜速览**（`hot.html`）：`hot-board` 工作流每小时起一个 RSSHub 容器，抓微博 / 百度 / 知乎 / B站 / 豆瓣六个榜生成
- 想调整热榜源改 `scripts/build_hot.py` 顶部的 `FEEDS`；想调整日报订阅改 garss fork 的 `EditREADME.md`
- 两个工作流共用 `concurrency: content-update` 组，避免同时 push 冲突；都用自带 `GITHUB_TOKEN`，无需任何额外密钥

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
