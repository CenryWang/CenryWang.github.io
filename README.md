# CenryWang 个人主页

线上地址：<https://cenrywang.github.io/>

## 目录结构

- `index.html` — 首页（关于 / 技能 / 作品 / 联系）
- `style.css` — 首页样式
- `script.js` — 首页交互（粒子背景 / 打字机 / 滚动进度条等）
- `merge-quest.html` — **合成大冒险 · Merge Quest** 游戏页，单文件自包含，开箱即玩
- `digest.html` — **每日简报**（RSS 聚合日报，Actions 每日自动生成，勿手改；首次生成前为占位页）
- `scripts/` — 上述页面的生成脚本
- `.github/workflows/` — 定时生成工作流（sync-digest）
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

首页导航的「简报」入口由 Actions 定时生成，页脚标注生成时间：

- 数据来自 garss fork（<https://github.com/CenryWang/garss>，每天北京时间 06:00 抓取 RSS 生成日报并发邮件），本仓库 `sync-digest` 工作流每天 07:30 把它渲染成站点风格的页面
- 想调整日报订阅改 garss fork 的 `EditREADME.md`
- 用自带 `GITHUB_TOKEN`，无需任何额外密钥

## 机器人文献（GitHub Actions 自动生成）

首页导航的「文献」入口由 Actions 每日抓取 arXiv 机器人方向论文，按相关度排序后生成：

- **数据源**：arXiv API 跨分类检索（主 `cs.RO` + 副 `cs.LG` / `cs.CV` / `cs.AI` + 关键词约束），增量 48 小时窗口
- **排序信号**：comment 字段会议名加权（RSS / CoRL / ICRA / IROS / T-RO / RAL / Science Robotics 等命中即加分）
- **领域方向标签**：每篇论文打 6 个具身子方向的 tag（论文可同时属多个）：**VLA**（视觉-语言-动作）/ **WAM**（世界动作模型）/ **HUMANOID**（人形/四足本体）/ **TACTILE**（触觉与灵巧操作）/ **DATA-EVAL**（数据集、benchmark、sim-to-real）/ **AGENTIC**（LLM 规划、层级策略、长程任务）
- **量化标签**：从 abstract / comment 正则提取数据规模，归一显示（`240H` / `60K DEMOS` / `1.2M TRAJ` / `150K SCENES`），零 LLM 纯正则
- **触达**：网页 + RSS feed（`robotics.xml`），零密钥、零外部依赖；用任意 RSS 阅读器订阅即可推送到手机
- **零密钥设计**：纯规则排序，**不依赖任何第三方 key**；GitHub Models 已于 2026-07-30 退役，所以不接 LLM 摘要，Top 5 直接展示 abstract 前 320 字
- **失败兜底**：今日抓不到论文就显示「无新论文」占位（arXiv 周五/六/日 不公布新 announcement 是正常的）；单分类失败容错，主分类失败才报错
- 想调整方向关键词改 `scripts/fetch_robotics.py` 顶部 `DIRECTIONS` 字典；想调整排序或样式改 `scripts/build_robotics.py`
- 历史归档按天落到 `papers/YYYY-MM-DD.md`，页面底部自动列出

工作流每日 **08:17 北京时间**（UTC 00:17）跑一次，与 sync-digest 共用 `concurrency: content-update` 组避免同时 push 冲突。

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
