# CenryWang 个人主页

线上地址：<https://cenrywang.github.io/>

## 目录结构

- `index.html` — 首页（关于 / 技能 / 作品 / 联系）
- `style.css` — 首页样式
- `script.js` — 首页交互（粒子背景 / 打字机 / 滚动进度条等）
- `merge-quest.html` — **合成大冒险 · Merge Quest** 游戏页，单文件自包含，开箱即玩

## 作品列表

- **合成大冒险 · Merge Quest** — 物理合成类休闲小游戏（Canvas + Matter.js）
  - 在线游玩：<https://cenrywang.github.io/merge-quest.html>（本仓库 `merge-quest.html`）
- **AIToolsChain · AI 工具链** — Windows AI 工具安装管理器（Tauri v2 / Rust + TypeScript）
  - 源码 / 下载：<https://github.com/CenryWang/AIToolsChain>
- **CherryStudio 工具说明书** — CherryStudio 桌面版使用说明（自整理）
  - 文档：<https://my.feishu.cn/docx/DZvcdVzI0oZQQFxIZ8mc5h9Cnbf?from=from_parent_docx>（飞书，可能需登录）
  - 工具官网：<https://cherry-ai.com>

## 联系方式（首页已配置）

- Email：cenrywang@foxmail.com
- GitHub：<https://github.com/CenryWang>
- 小红书：<https://xhslink.cn/o/GKuYm3zIMN>（二维码图片 `xhs-qrcode.jpg`）

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
