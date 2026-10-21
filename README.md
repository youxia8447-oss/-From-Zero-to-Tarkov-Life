<div align="center">

# 从零开始的塔科夫生活

**From Zero to Tarkov Life**

面向《逃离塔科夫》本地 PvE 的 Windows 10/11 视觉辅助工具

![version](https://img.shields.io/badge/version-1.0-A78BFA)
![platform](https://img.shields.io/badge/platform-Windows%2010%2F11-0078D6)
![python](https://img.shields.io/badge/Python-3.11-3776AB)
![license](https://img.shields.io/badge/license-MIT-4ADE80)

</div>

> **仅建议用于本地 PvE / 离线模式。** 在线模式使用可能违反游戏规则，风险由使用者自行承担。本项目是非官方同人工具，与 Battlestate Games 没有任何关联。

## 简介

「从零开始的塔科夫生活」是一款面向《逃离塔科夫》本地 PvE 的 Windows 视觉辅助工具。它只截取屏幕顶部的 HUD，不读取游戏内存、不注入游戏进程、不修改游戏文件。

程序确认战斗 HUD 后开始监控；当 HUD 持续缺失达到设定延时，发送一次 **Alt+F4** 并自动停止监控。它还支持 HUD 就绪后定时自动按键、自定义分辨率、测试模式、快捷键切换与多套主题音效。

**V1 新增完整的简体中文 / English 双语界面**：点击窗口右上角的 `EN` / `中` 即可即时切换，无需重启；语言选择会写入 `settings.json`，下次启动自动沿用。默认语言为中文。

## 界面

### 中文

<p align="center">
  <img src="docs/images/main.png" width="31%" alt="战前准备" />
  <img src="docs/images/advanced.png" width="31%" alt="进阶设置" />
  <img src="docs/images/diagnostics.png" width="31%" alt="日志诊断" />
</p>

### English

<p align="center">
  <img src="docs/images/main_en.png" width="31%" alt="Prep" />
  <img src="docs/images/advanced_en.png" width="31%" alt="Advanced" />
  <img src="docs/images/diagnostics_en.png" width="31%" alt="Diagnostics" />
</p>

固定 **464 × 540** 的 16:10 紧凑窗口，三个标签页：

| 标签页 | 内容 |
| :--- | :--- |
| **战前准备** / Prep | 音效选择/试听/导入、快捷键、当前状态、测试模式、开始/停止监控 |
| **进阶设置** / Advanced | 音效开关、延时、采样率、自定义分辨率、自动按键、诊断采集、保存设置 |
| **日志诊断** / Diagnostics | 运行状态、实时事件、打开日志、刷新、关于信息 |

页面内容超出时可用鼠标滚轮滚动，滚动条只在需要时出现。

## 中英双语

- 窗口右上角 `EN` / `中` 按钮：运行中即时切换，所有标签页、按钮、提示、状态与日志同步翻译。
- 窗口标题同步切换：`从零开始的塔科夫生活 · 正式版` ↔ `From Zero to Tarkov Life · Official Release`。
- 月读主题：`月読 · 正式版` ↔ `Tsukuyomi · Official Release`。
- 动态监控状态与日志事件名也会翻译，例如「本轮停止 · 游戏已退出」↔ `Round ended · game exited`。
- 音效下拉框显示当前语言的名称，但内部仍使用原始音效键；切换语言不会改变已选音效或主题。
- 语言保存在 `settings.json` 的 `language` 字段（`zh` / `en`）。删除该字段后回到中文。

## 功能

| 功能 | 说明 |
| :--- | :--- |
| **纯屏幕识别** | 只处理屏幕顶部 HUD 像素，不读取角色内存、不注入游戏进程 |
| **中英双语** | 运行中即时切换中文 / English，语言选择自动保存 |
| **单次退出** | HUD 持续缺失达到延时后发送一次 Alt+F4，按键保持 40 ms，不自动重试 |
| **自动按键** | HUD 就绪后立即按一次，之后按设定间隔重复；游戏失焦或 HUD 消失时暂停 |
| **自定义分辨率** | 支持 `auto` 或 `2560x1600` 这样的实际分辨率，写入 `settings.json` |
| **测试模式** | 只记录候选与日志，不发送 Alt+F4，适合先验证识别效果 |
| **主题音效** | 内置多套退出音效，窗口标题、配色与图标随主题切换 |
| **日志诊断** | 实时事件、详细分数日志、诊断截图与日志文件入口 |
| **管理员提示** | 首次普通权限启动时提示提权，避免 Windows UIPI 拦截模拟按键 |

## 快速开始

1. 从 [Releases](../../releases/latest) 下载 `从零开始的塔科夫生活_V1.zip`。
2. 解压后保持 `从零开始的塔科夫生活.exe`、`settings.json`、`icons` 在同一个目录。
3. 双击 EXE。首次启动需要解包，可能等待数秒；如果出现「管理员权限」提示，建议选择「是」。
4. 先保持「测试模式」勾选，进入本地 PvE 战局，确认 HUD、血量人形和快捷栏可见后按 **F9** 开始监控。
5. 观察右上角模式徽标与状态卡「就绪」是否正常。测试模式只记录，不发送按键。
6. 确认识别稳定后，取消测试模式，再按 F9 开始正常监控；再次按 F9 停止。
7. 需要英文界面时点击右上角 `EN`，切回中文点击 `中`。

快捷键、模式或分辨率修改后，到「进阶设置」点「保存设置」。

## 自动按键

- 在「进阶设置」中勾选「启用」，设置间隔（1–3600 秒）和按键（支持字母、数字、F1–F12、Space、Tab、Enter、Backspace）。
- 只有游戏处于前台，并且识别到战斗 HUD / 血量人形 / 快捷栏后才会触发。
- 就绪后立即按一次，之后按间隔重复；按住 Ctrl / Alt / Shift / Win 时自动跳过。
- 打开背包、菜单或 HUD 消失时会自动暂停，回到战局后重新立即按一次。
- 默认关闭；开关和配置会写入 `settings.json`。

## 自定义分辨率

在「进阶设置 → 检测参数 → 分辨率」中填写：

- `auto` 或留空：自动模式，沿用 16:10 检测配置。
- `宽x高`：例如 `2560x1600`、`1920x1080`、`3440x1440`，支持字母 `x` 或乘号 `×`。

填写后点「保存设置」才会写入配置文件。**限制**：采集逻辑仍要求游戏窗口客户区等于主显示器全屏区域；自定义分辨率只在独占全屏且显示分辨率与填写值一致时生效。无边框/窗口化模式请填写与桌面一致的分辨率，或使用 `auto`。

## 从源码构建

本仓库包含重写后的 UI 源码与重封包 / 校验工具。完整程序需要上游 `ID486-Tarkov-Assistant` 的 PyInstaller 基底 EXE；仓库不包含该二进制，也不包含第三方音频和图标。

```text
.
├─ ui_compact.py           重写后的主界面与中英双语
├─ scripts/                编译、补丁、重封包与校验脚本
├─ docs/                   构建说明、发布说明、截图
├─ requirements-build.txt  构建依赖
├─ base/                   放置上游基底 EXE（不提交）
├─ assets/                 放置图标/音频（不提交）
└─ build/                  构建输出（不提交）
```

构建步骤、依赖与常见问题见 [docs/BUILD.md](docs/BUILD.md)。变更概览见 [docs/UPSTREAM.md](docs/UPSTREAM.md)。

## 版本

| 版本 | 日期 | 主要变化 |
| :--- | :--- | :--- |
| **v1.0** | 2026-10-22 | 中英双语即时切换；标题后缀改为「正式版」/ `Official Release`；日志与动态状态本地化；PE 版本 1.0.0.0 |
| v0.7.1 | 2026-10-22 | 月读主题标题去掉「紧凑版」；PE 版本 0.7.1.0 |
| v0.7 | 2026-10-22 | 徽标位置纠正、自定义分辨率、首次运行管理员提示、PYZ 重封包 |
| v0.6 | 2026-10-22 | HUD 准入阈值修复、自动按键改为就绪触发、设置完整保存 |

完整更新记录见 [CHANGELOG.md](CHANGELOG.md)，v1.0 发布说明见 [docs/releases/v1.md](docs/releases/v1.md)。

## 已知限制

- 基础 HUD 识别基于 2560×1600、16:10、全屏实测；其他分辨率请使用自定义分辨率，并确认与游戏实际画面一致。
- 自定义分辨率不改采集区域，仍需独占全屏且客户区等于主屏；无边框/窗口化只支持与桌面同分辨率。
- 游戏以管理员权限运行时，本工具若不是管理员权限，Windows UIPI 会阻止模拟按键和 Alt+F4。
- 自动按键与 Alt+F4 都是模拟输入，可能被反作弊或权限策略拦截。
- 托盘图标固定为第一版图标；窗口标题、主题和窗口图标会随退出音效切换，但 EXE 文件图标不会动态变化。
- 程序未签名，首次运行可能出现 SmartScreen 提示；请确认文件来源。
- 无 UI 不等于死亡。菜单、加载、转场或未收录界面仍可能导致误判，建议先用测试模式验证。

## 致谢与版权

- 上游项目：[liudoge66/ID486-Tarkov-Assistant](https://github.com/liudoge66/ID486-Tarkov-Assistant)，作者 Liudoge（Bilibili）。
- 本项目是在上游项目基础上进行界面重写与构建工具开发的非官方衍生作品；上游代码、二进制与素材的权利归原作者所有。
- 本仓库原创代码与文档以 MIT 许可证发布；上游衍生代码、第三方音频、图标与角色素材不在 MIT 范围内，详见 [NOTICE.md](NOTICE.md)。
- Escape from Tarkov 及相关商标归 Battlestate Games 所有。其他作品、角色与素材归各自权利人所有。

## English

**From Zero to Tarkov Life** is a Windows 10/11 visual assistant for Escape from Tarkov local PvE. It captures only the top HUD, no memory reading or game injection, and sends Alt+F4 once when the combat HUD stays missing. Features HUD-ready auto-keys, custom resolution, test mode, hotkeys and themed sounds.

**V1** adds a complete Simplified Chinese / English interface. Use the `EN` / `中` button in the top-right corner to switch instantly without restarting; the choice is saved in `settings.json` and restored on the next launch. The default language is Chinese. Window titles use `正式版` in Chinese and `Official Release` in English.

This is an unofficial fan project, not affiliated with Battlestate Games. Original code is MIT-licensed; upstream code and third-party assets are covered in [NOTICE.md](NOTICE.md). Offline PvE only; online use at your own risk.
