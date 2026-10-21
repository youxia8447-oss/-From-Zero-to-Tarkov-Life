# 与上游项目的关系

- 上游项目：<https://github.com/liudoge66/ID486-Tarkov-Assistant>
- 上游作者：Liudoge（Bilibili）
- 对比基线：上游 `main` / tag `v0.2`

本仓库是在上游项目基础上进行界面重写与构建工具开发的非官方衍生项目。

## 主要改动

| 区域 | 改动 |
| :--- | :--- |
| 界面 | 用 `ui_compact.py` 重写为 464×540 三标签紧凑窗口 |
| 检测 | 调整战斗 HUD 准入阈值，支持 16:10 与自定义分辨率 |
| 自动按键 | HUD 就绪后立即按一次，之后按间隔重复；失焦或 HUD 消失时暂停 |
| 品牌 | 应用名改为「从零开始的塔科夫生活」，支持三套主题名称与配色 |
| 双语 | 新增中文 / English 运行时切换，覆盖界面、状态、日志与音效显示名 |
| 打包 | 用 `repack_pyz.py` 重排 PYZ，不再受固定槽位限制 |
| 设置 | 完整保存音效、快捷键、测试模式、分辨率与自动按键配置 |
| 管理员提示 | 首次普通权限启动时提示通过 UAC 提权重启 |

## 上游衍生内容

- `scripts/patch_detector.py` 中的 `normalize_top` 替换源码来自上游 `detector.py`，并按本项目需要修改。
- 基底 EXE、`sound_library` 与 `detector` 的原始实现来自上游项目。

这些内容不在本仓库 MIT 许可证的覆盖范围内，详见 [NOTICE.md](../NOTICE.md)。

## 未包含的内容

本仓库不包含：

- 上游或本项目的 EXE；
- 上游 PYZ / marshal 编译产物；
- 第三方音频、图标、字体或游戏素材。

构建时需要自行准备上游基底 EXE，见 [BUILD.md](BUILD.md)。
