<div align="center">

# 从零开始的塔科夫生活

**From Zero to Tarkov Life**

面向《逃离塔科夫》本地 PvE 的 Windows 10/11 视觉辅助工具

![version](https://img.shields.io/badge/version-1.2.7-A78BFA)
![platform](https://img.shields.io/badge/platform-Windows%2010%2F11-0078D6)
![python](https://img.shields.io/badge/Python-3.11-3776AB)
![license](https://img.shields.io/badge/license-MIT-4ADE80)

</div>

> **仅建议用于本地 PvE / 离线模式。** 在线模式使用可能违反游戏规则，风险由使用者自行承担。本项目是非官方同人工具，与 Battlestate Games 没有任何关联。

## 简介

「从零开始的塔科夫生活」是一款面向《逃离塔科夫》本地 PvE 的 Windows 视觉辅助工具。它只截取屏幕顶部的 HUD，不读取游戏内存、不注入游戏进程、不修改游戏文件。

程序确认战斗 HUD 后开始监控。普通情况下，当 HUD 持续缺失达到设定延时，程序发送一次 **Alt+F4** 并自动停止监控。识别到顶部绿色「停留在撤离点内」横幅后，程序会**立即释放自动按键、停止监控并进入待机，不发送 Alt+F4**；窗口保持打开，下一局需要重新按 F1 开始。

已收录的背包、总览、健康、技能、地图、任务、成就、控制台、游戏主页、设置、确认和战局结算等界面都有白名单或后备保护，不会触发 Alt+F4。`TKF-7314-Y` 只作为撤离后的结算后备保护：最近 60 秒内识别过有效撤离横幅时才会命中。

## V1.2.7 更新（2026-10-22）

**这是一个界面修复版本，检测、撤离待机、自动按键、音效和自定义音频行为与 V1.2.6 一致。**

- **修复英文界面下语言切换按钮消失**：在 464 px 宽度下，英文标题 `From Zero to Tarkov Life`、状态文字 `Not started` 与右上角编号徽标合计超出可用宽度，`中` 按钮被挤出布局。现在标题在左侧可伸缩，语言按钮、状态与编号放入固定的右侧控件组，`中` 按钮始终可见。
- **英文头部状态缩短**：`Not started` / `Monitoring` / `Round ended` 在顶部只显示 `Idle` / `Active` / `Ended`，状态卡内仍显示完整文字，避免再次挤占按钮空间。
- **窗口仍为 V0.7 的 464 × 540**，不可缩放；中文界面布局不变。
- **版本号更新**：PE 文件版本为 `1.2.7.0`，关于区域显示 `V1.2.7`，发布包内附 `更新说明_V1.2.7.txt`。
- **功能与资源不变**：仍保留 5 个音效预置、24 个运行必需资源与 1218 个归档条目；自定义音频、启用/静音状态和旧配置迁移逻辑未改动。
- **体积为 85,863,682 字节**，比 V1.2.6 增加 274 字节。
- **历史成品不受影响**：V1.2.6、V1.2.5、V1.2.4 的 EXE、ZIP 与桌面副本，以及 V1.2.3 的 EXE、ZIP 均未删除或覆盖，可随时回滚。

### 自 V1.2.2 以来的变化

| 版本 | 主要变化 |
| :--- | :--- |
| **V1.2.3** | 识别绿色撤离横幅后自动停止监控并待机，解决撤离后仍发送 Alt+F4 的问题。 |
| **V1.2.4** | 清理 51 个未使用归档条目，EXE 从 112,328,610 字节降到 86,242,453 字节。 |
| **V1.2.5** | 退役 `电子回溯` 与 `塔科夫任务完成电音` 两个预置，归档条目降到 1218；音效库改为源码维护。 |
| **V1.2.6** | 窗口宽度从 600 回退到 464，恢复 V0.7 的固定 464 × 540。 |
| **V1.2.7** | 修复 464 px 英文界面 `中` 按钮消失；英文顶部状态改为 Idle / Active / Ended。 |

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

> 截图为 V1.2.7 的实际界面，窗口固定为 **464 × 540**。英文界面右上角始终保留 `中` 按钮。

固定 **464 × 540** 的窗口，三个标签页：

| 标签页 | 内容 |
| :--- | :--- |
| **战前准备** / Prep | 音效选择 / 试听 / 导入、快捷键、当前状态、测试模式、开始 / 停止监控 |
| **进阶设置** / Advanced | 音效开关、延时、采样率、自定义分辨率、自动按键、诊断采集、保存设置 |
| **日志诊断** / Diagnostics | 运行状态、实时事件、当前界面、打开日志、刷新、关于信息 |

页面内容超出时可用鼠标滚轮滚动，滚动条只在需要时出现。

## 功能

| 功能 | 说明 |
| :--- | :--- |
| **纯屏幕识别** | 只处理屏幕顶部 HUD 像素，不读取角色内存、不注入游戏进程、不修改游戏文件 |
| **战斗 HUD 监控** | 综合人体轮廓、血量颜色、快捷栏横竖框、标签边缘与颜色占比判断战局 |
| **单次退出** | HUD 持续缺失达到延时后发送一次 Alt+F4，按键保持 40 ms，不自动重试 |
| **撤离自动待机** | 识别绿色撤离横幅 `TKF-7314-N` 后，约 300 ms 确认即释放自动按键、停止监控并待机，不发送 Alt+F4 |
| **结算后备保护** | `TKF-7314-Y` 命中「战局结束」标题且最近 60 秒识别过有效撤离横幅时，不触发 Alt+F4 |
| **界面识别与白名单** | 识别背包、总览、健康、技能、地图、任务、成就、控制台、设置、确认、游戏主页与结算页；安全界面不会触发 Alt+F4 |
| **中英双语** | 运行中即时切换中文 / English，语言选择自动保存；464 px 下 `中` / `EN` 按钮始终可见 |
| **自动按键** | HUD 就绪后立即按一次，之后按设定间隔重复；游戏失焦、暂停或 HUD 消失时暂停并强制松开 |
| **自定义分辨率** | 支持 `auto` 或 `2560x1600` 这样的实际分辨率，写入 `settings.json` |
| **测试模式** | 只记录候选与日志，不发送 Alt+F4，适合先验证识别效果 |
| **主题音效** | 内置 5 个音效预置，窗口标题、配色与图标随主题切换 |
| **自定义音频** | 可导入 WAV / MP3 / FLAC / OGG，试听、启用或静音，设置持久化 |
| **日志诊断** | 实时事件、当前界面编号、详细分数日志、诊断截图与日志文件入口 |
| **管理员提示** | 首次普通权限启动时提示提权，避免 Windows UIPI 拦截模拟按键 |

## 界面识别与保护

检测端把界面编号显示在窗口右上角，编号格式为 `TKF-7314-<字母>`：

| 编号 | 界面 | 颜色与行为 |
| :--- | :--- | :--- |
| `TKF-7314-A` | 无武装战局 | 绿色；战斗分较低时作为安全界面兜底 |
| `TKF-7314-B` | 装备 / 背包 | 绿色；不触发 Alt+F4 |
| `TKF-7314-C` | 总览 | 绿色；不触发 Alt+F4 |
| `TKF-7314-D` | 健康 | 绿色；不触发 Alt+F4 |
| `TKF-7314-E` | 技能 | 绿色；不触发 Alt+F4 |
| `TKF-7314-F` | 地图 | 绿色；不触发 Alt+F4 |
| `TKF-7314-G` | 任务 | 绿色；不触发 Alt+F4 |
| `TKF-7314-O` | 成就 | 绿色；不触发 Alt+F4 |
| `TKF-7314-P` | 控制台 | 绿色；不触发 Alt+F4 |
| `TKF-7314-Q` | 游戏主页 | 绿色；不触发 Alt+F4 |
| `TKF-7314-S` | 设置 | 绿色；不触发 Alt+F4 |
| `TKF-7314-K` | 确认 | 绿色；不触发 Alt+F4 |
| `TKF-7314-H` | 转生 / 未识别页签 | 绿色；不触发 Alt+F4 |
| `TKF-7314-Y` | 战局结束 / 结算 | 绿色；仅在最近 60 秒识别过有效撤离横幅时作为后备保护 |
| `TKF-7314-N` | 撤离点 | 红色；绿色横幅显示期间受保护，确认后停止监控并待机 |
| `TKF-7314-X` | 战斗 HUD | 琥珀色；正常战局监控目标 |
| `TKF-7314-0` | 未识别 | 灰色；按普通缺失逻辑处理 |

游戏主页使用 `assets/interface/home_Q.png` 中的 `ESCAPE` 字样做灰度模板匹配：顶部条缩放后按多种位置、纵横比与水平比例搜索，最高得分达到 0.66 判定为 `Q`。

撤离保护分三层：绿色横幅 `N` 连续约 300 ms 确认后立即停止监控；如果横幅被遮挡而未触发待机，红色读秒 `00` 与画面淡出确认仍会作为第二层保护；撤离后的结算页 `Y` 在最近 60 秒识别过有效横幅时作为第三层后备保护。死亡 / 失踪结算不会命中 `Y`。

## 快速开始

1. 从 [Releases](../../releases/latest) 下载 `从零开始的塔科夫生活_V1.2.7.zip`。
2. 解压后保持 `从零开始的塔科夫生活.exe`、`settings.json`、`icons` 在同一个目录，不要只复制 EXE。
3. 双击 EXE。首次启动需要解包，可能等待数秒；如果出现「管理员权限」提示，建议选择「是」。
4. 建议先勾选「测试模式」，进入本地 PvE 战局，确认 HUD、血量人形和快捷栏可见后按 **F1** 开始监控。
5. 观察右上角界面编号与状态卡「就绪」是否正常。测试模式只记录，不发送按键。
6. 依次测试背包、ESC、设置、撤离等场景，确认不会误触发。
7. 确认识别稳定后，取消测试模式，再按 F1 开始正常监控；再次按 F1 手动停止。
8. 撤离时看到绿色「停留在撤离点内」横幅后，程序会自动停止监控并待机。这是正常行为，不是崩溃，也不会关闭游戏；下一局重新按 F1。
9. 需要英文界面时点击右上角 `EN`；切回中文点击 `中`。V1.2.7 已确保英文界面下 `中` 按钮始终可见。

快捷键、模式或分辨率修改后，到「进阶设置」点「保存设置」。

## 自动按键

- 在「进阶设置」中勾选「启用」，设置间隔（1–3600 秒）和按键（支持字母、数字、F1–F12、Space、Tab、Enter、Backspace）。
- 只有游戏处于前台，并且识别到战斗 HUD / 血量人形 / 快捷栏后才会触发。
- HUD 就绪后立即按一次，之后按间隔重复；按住 Ctrl / Alt / Shift / Win 时自动跳过。
- 打开背包、菜单或 HUD 消失时自动暂停，回到战局后重新立即按一次。
- V1.2.2 起，自动按键准入线调整为 `bar_frames ≥ 0.12`，并增加按下状态跟踪；暂停或失去前台时强制松开，避免按键卡住。
- 默认关闭；开关和配置会写入 `settings.json`。

## 自定义分辨率

在「进阶设置 → 检测参数 → 分辨率」中填写：

- `auto` 或留空：自动模式，沿用 16:10 检测配置。
- `宽x高`：例如 `2560x1600`、`1920x1080`、`3440x1440`，支持字母 `x` 或乘号 `×`。

填写后点「保存设置」才会写入配置文件。**限制**：采集逻辑仍要求游戏窗口客户区等于主显示器全屏区域；自定义分辨率只在独占全屏且显示分辨率与填写值一致时生效。无边框 / 窗口化模式请填写与桌面一致的分辨率，或使用 `auto`。

## 音效与自定义音频

当前保留 5 个音效预置：

| 预置 | 文件 | 用途 |
| :--- | :--- | :--- |
| 486回归音效 | `return_by_death.wav` | 默认退出音效 |
| 轻提示 · 开启 | `enabled.wav` | 开启监控提示 |
| 轻提示 · 关闭 | `disabled.wav` | 停止监控提示 |
| 杀手皇后第三炸弹败者食尘 | `killer_queen.wav` | 可选退出音效 |
| 宇智波鼬 · 幻术 | `duckov_extract.wav` | 可选退出音效 |

退出音效下拉框显示 3 个可选预置（486、杀手皇后、宇智波鼬）以及导入的自定义音频。支持 WAV / MP3 / FLAC / OGG，单个文件不超过 50 MB、时长不超过 60 秒。导入的副本保存在 `user_audio\`，选择与启用 / 静音状态保存在 `sound_settings.json`。

## 从源码构建

本仓库包含重写后的 UI 源码、音效库源码、检测补丁与重封包 / 校验工具。完整程序需要上游 `ID486-Tarkov-Assistant` 的 PyInstaller 基底 EXE；仓库不包含该二进制，也不包含第三方音频、图标和界面模板。

```text
.
├─ ui_compact.py                 重写后的主界面与中英双语
├─ sound_library.py              音效预置与自定义音频库
├─ scripts/                      编译、检测补丁、重封包与校验脚本
├─ assets/interface/             界面识别模板（自行准备，不提交）
├─ docs/                         构建说明、发布说明、截图
├─ requirements-build.txt        构建依赖
├─ base/                         放置上游基底 EXE（不提交）
├─ assets/                       放置图标 / 音频（不提交）
└─ build/                        构建输出（不提交）
```

构建步骤、模板清单与常见问题见 [docs/BUILD.md](docs/BUILD.md)。与上游的差异见 [docs/UPSTREAM.md](docs/UPSTREAM.md)。

## 版本

| 版本 | 日期 | 主要变化 |
| :--- | :--- | :--- |
| **v1.2.7** | 2026-10-22 | 修复 464 px 英文界面 `中` 按钮消失、标题可伸缩、英文顶部状态缩短为 Idle/Active/Ended、PE 1.2.7.0 |
| v1.2.6 | 2026-10-22 | 窗口宽度 600 → 464，恢复 V0.7 的 464×540、PE 1.2.6.0 |
| v1.2.5 | 2026-10-22 | 退役 2 个音效预置，归档条目 1220 → 1218，体积减少 379,054 字节、PE 1.2.5.0 |
| v1.2.4 | 2026-10-22 | 清理 51 个未使用归档条目，EXE 从 112,328,610 字节降到 86,242,453 字节、PE 1.2.4.0 |
| v1.2.3 | 2026-10-22 | 撤离绿色横幅自动待机，不再发送 Alt+F4、PE 1.2.3.0 |
| v1.2.2 | 2026-10-22 | 窗口 600×540、自动按键准入线 0.12 与按键状态跟踪、`TKF-7314-Y` 结算后备保护、PE 1.2.2.0 |
| v1.2.1 | 2026-10-22 | 游戏主页多位置 / 多比例识别、`Q` 更名为「游戏主页」、窗口加高至 464×621、PE 1.2.1.0 |
| v1.2 | 2026-10-22 | 红色撤离读秒识别、`N` 横幅保护、`00` + 淡出确认、多分辨率标题匹配、TKF 编号、PE 1.2.0.0 |
| v1.0 | 2026-10-22 | 中英双语即时切换、正式版命名、日志本地化、PE 1.0.0.0 |
| v0.7.1 | 2026-10-22 | 月读主题标题简化、PE 0.7.1.0 |
| v0.7 | 2026-10-22 | 徽标位置纠正、自定义分辨率、首次运行管理员提示、PYZ 重封包 |
| v0.6 | 2026-10-22 | HUD 准入阈值修复、自动按键改为就绪触发、设置完整保存 |

完整更新记录见 [CHANGELOG.md](CHANGELOG.md)，V1.2.7 发布说明见 [docs/releases/v1.2.7.md](docs/releases/v1.2.7.md)。

- 版本号：`1.2.7.0`
- 构建日期：2026-10-22
- EXE 大小：85,863,682 字节
- EXE SHA256：`8F431552D751CF231BD911104C49E61AF68DBF2442051CD01A949B0CAB297159`
- 发布包大小：85,278,508 字节
- 发布包 SHA256：`15B84EDE2731C79EC1C6AFBE430CC58EF9DACB0EB896BC2FC25B65B6FC47E314`

## 文件结构

```text
从零开始的塔科夫生活\
├─ 从零开始的塔科夫生活.exe   主程序（85,863,682 字节）
├─ settings.json              默认配置
├─ icons\
│  ├─ first_icon.ico          486 回归音效
│  ├─ killer_queen.ico        杀手皇后第三炸弹
│  └─ itachi_mangekyo.ico     宇智波鼬 · 幻术
├─ README.md                  完整说明
└─ 更新说明_V1.2.7.txt        本版本更新清单
```

运行后还会生成：

- `monitor_events.jsonl`：监控事件日志
- `sound_settings.json`：音效导入 / 选择记录
- `user_audio\`：导入的音频副本

## 已知限制

- 基础 HUD 识别基于 2560×1600、16:10、全屏实测；其他分辨率请使用自定义分辨率，并确认与游戏实际画面一致。
- 自定义分辨率不改采集区域，仍需独占全屏且客户区等于主屏；无边框 / 窗口化只支持与桌面同分辨率。
- 游戏以管理员权限运行时，本工具若不是管理员权限，Windows UIPI 会阻止模拟按键和 Alt+F4；首次提示可选择提权重启。
- 托盘图标固定为第一版图标；窗口标题、主题和窗口图标会随退出音效切换，但 EXE 文件图标不会动态变化。
- 自动按键与 Alt+F4 都是模拟输入，可能被反作弊或权限策略拦截。
- 程序未签名，首次运行可能出现 SmartScreen 提示；请确认文件来源。
- 不要同时运行多个实例；程序使用单实例锁。如果提示「工具已经运行」，请先关闭旧的程序窗口。
- 无 UI 不等于死亡。已收录的 `A/B/C/D/E/F/G/O/P/Q/S/K/H/Y` 界面有白名单或后备保护；未收录的菜单、加载或转场仍可能被当作 HUD 缺失，建议先用测试模式验证。
- 撤离画面 `N` 在绿色横幅显示期间受保护；正常识别后约 300 ms 内停止监控并待机。如果横幅被遮挡、分辨率差异过大或界面刷新异常而没有触发待机，撤离读秒与淡出确认仍会作为第二层保护。
- 撤离后的结算画面 `Y` 是后备保护：只有最近 60 秒内识别过有效撤离横幅时才会命中，不会触发 Alt+F4；死亡 / 失踪结算不会命中 `Y`，仍可能按普通 HUD 缺失逻辑处理。
- 如果横幅、读秒和结算页都没有被识别，且中途经过长时间完全未识别的黑屏 / 加载画面，仍可能由普通缺失门控触发。
- 撤离读秒只读取横幅右侧最末两位数字；剩余时间大于 10 分钟、数字被遮挡或画面比例差异过大时可能返回未知状态。
- 游戏主页识别依赖顶部条内的 Tarkov 标志；如果标志被其他界面完全遮挡，可能回退为「未识别」，建议先用测试模式确认。

## 致谢与版权

- 上游项目：[liudoge66/ID486-Tarkov-Assistant](https://github.com/liudoge66/ID486-Tarkov-Assistant)，作者 Liudoge（Bilibili）。
- 本项目是在上游项目基础上进行界面重写与构建工具开发的非官方衍生作品；上游代码、二进制与素材的权利归原作者所有。
- 本仓库原创代码与文档以 MIT 许可证发布；上游衍生代码、第三方音频、图标与角色素材不在 MIT 范围内，详见 [NOTICE.md](NOTICE.md)。
- Escape from Tarkov 及相关商标归 Battlestate Games 所有。其他作品、角色与素材归各自权利人所有。

## English

**From Zero to Tarkov Life** is a Windows 10/11 visual assistant for Escape from Tarkov local PvE. It captures only the top HUD, does not read game memory or inject into the game, and sends **Alt+F4** once when the combat HUD stays missing past the configured delay. Known menus (inventory, overview, health, skills, map, quests, achievements, console, settings, confirmation, game home and settlement) are recognized and excluded from the trigger. When the green extraction banner is recognized, the tool stops monitoring and returns to standby **without sending Alt+F4**; the game is left running. The `TKF-7314-Y` settlement page is a fallback protection that only applies when a valid extraction banner was seen in the last 60 seconds.

**V1.2.7** fixes the language button disappearing in the 464 px English layout. The header title now yields space to a fixed right-hand control group containing the `中` / `EN` button, status and interface badge, so the language switch is always reachable. English header statuses are shortened to Idle / Active / Ended while the status card keeps the full text. The window remains the V0.7 fixed **464 × 540**. Detection, extraction standby, auto-key, sound presets and custom-audio behavior are unchanged from V1.2.6. The five remaining presets are 486 Return Sound, Soft cue On, Soft cue Off, Killer Queen, and Itachi Illusion; the exit dropdown offers the 486, Killer Queen and Itachi presets plus imported custom audio. The PE version is `1.2.7.0`; the About area shows `V1.2.7`. The archive still contains 24 required assets and 1218 entries, and the EXE is 85,863,682 bytes.

Features include HUD-ready auto-keys, custom resolution, test mode, hotkeys, themed sounds, custom audio import and a first-run administrator prompt. The top-right badge shows the detected interface as a TKF-style code (`TKF-7314-A` … `TKF-7314-Y`); the documented interfaces A/B/C/D/E/F/G/O/P/Q/S/K/H/Y are excluded from the Alt+F4 trigger. Offline PvE only; online use is at your own risk. This is an unofficial fan project and is not affiliated with Battlestate Games.

- Version: `1.2.7.0`
- EXE SHA256: `8F431552D751CF231BD911104C49E61AF68DBF2442051CD01A949B0CAB297159`
- ZIP SHA256: `15B84EDE2731C79EC1C6AFBE430CC58EF9DACB0EB896BC2FC25B65B6FC47E314`
