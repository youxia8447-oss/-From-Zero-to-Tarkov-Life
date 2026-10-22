# 构建说明

本项目使用“重封包”方式构建：从上游的 PyInstaller 单文件 EXE 出发，替换 PYZ 中的 `primary_ui`、`sound_library`、`detector` 三个模块，再重建外壳归档。它不是从零开始的 PyInstaller 源码构建。

## 环境要求

- Windows 10/11 x64
- Python 3.11.9 x64
- Python 包：`zopfli`（用于更小的压缩体积；没有时会回退到 zlib）
- 上游 `ID486-Tarkov-Assistant` 的 PyInstaller 单文件 EXE，作为 `base/base_branded.exe`

```bat
py -3.11 -m pip install -r requirements-build.txt
```

## 准备基底 EXE

1. 从上游 [ID486-Tarkov-Assistant](https://github.com/liudoge66/ID486-Tarkov-Assistant) 的 Release 下载 Windows 便携版。
2. 解压，找到上游的 `ID486模拟助手.exe`。
3. 复制到本仓库的 `base\` 目录，并重命名为 `base_branded.exe`。

基底必须包含以下内容，否则脚本会报错：

- PyInstaller 外壳 cookie 和 `PYZ.pyz` 条目；
- PYZ 模块 `primary_ui`、`sound_library`、`detector`；
- 外壳资源 `assets\subaru_clean.ico` 与 `assets\duckov_extract.wav`（仅在替换素材时需要）。

> 仓库不提供基底 EXE。它体积约 107 MB，且包含上游代码和第三方素材，不适合直接提交到 Git。

## 准备界面识别模板

`scripts/patch_detector.py` 会把界面模板嵌入 `detector.marshal`。请把以下灰度 PNG 放到 `assets\interface\`：

```text
assets\interface\
├─ hotbar_A.png      无武装快捷栏 A
├─ tabs_B.png        装备 / 背包页签 B
├─ tabs_C.png        总览页签 C
├─ tabs_D.png        健康页签 D
├─ tabs_E.png        技能页签 E
├─ tabs_F.png        地图页签 F
├─ tabs_G.png        任务页签 G
├─ tabs_O.png        成就页签 O
├─ console_P.png     控制台 P
├─ pause_Q.png       游戏主页 Q（固定区域）
└─ home_Q.png        游戏主页 Q（ESCAPE 标志模板）
```

模板坐标以检测端的 1920×240 顶部条为基准，具体裁剪框在 `scripts/patch_detector.py` 的 `IFACE_TEMPLATES` 中维护。`home_Q.png` 不绑定固定坐标，匹配时会按多种比例搜索。模板来自游戏画面，仓库不提供，请自行截取并确认使用权限。

## 一键构建

```bat
build.bat
```

脚本依次执行：

1. 从基底重新生成 `sound_library.marshal`；
2. 复制基底为 `build\base_v122.exe`，并写入 PE 版本 `1.2.2.0`；
3. 编译 `ui_compact.py`，生成 `ui_compact.marshal`；
4. 运行检测补丁，生成 `detector.marshal`；
5. 用 `repack_pyz.py` 重排 PYZ，输出 `build\从零开始的塔科夫生活_V1.2.2.exe`；
6. 用 `validate_final.py` 校验三个模块和嵌入资源。

## 手动构建

```bat
py -3.11 scripts\patch_sound_library.py
copy /Y "base\base_branded.exe" "build\base_v122.exe"
py -3.11 scripts\patch_version_info.py "build\base_v122.exe"
py -3.11 scripts\compile_ui.py
py -3.11 scripts\patch_detector.py
py -3.11 scripts\repack_pyz.py "build\base_v122.exe" "build\从零开始的塔科夫生活_V1.2.2.exe"
py -3.11 scripts\validate_final.py "build\从零开始的塔科夫生活_V1.2.2.exe"
```

生成的中间文件：

- `ui_compact.marshal`
- `sound_library.marshal`
- `detector.marshal`

这些文件已写入 `.gitignore`，不应提交。

## 可选：替换图标与音效

仓库不包含第三方图标和音频。准备你自己的文件：

```text
assets\icons\first_icon.ico
assets\audio\itachi_exit_v2_35.wav
```

然后：

```bat
py -3.11 scripts\patch_assets.py "base\base_branded.exe" "build\base_custom.exe"
py -3.11 scripts\repack_pyz.py "build\base_custom.exe" "build\从零开始的塔科夫生活_V1.2.2.exe"
```

`patch_assets.py` 会替换外壳资源槽中的图标和退出音效。新资源必须能压进原槽位，否则会报 `does not fit slot`。

## PE 版本信息

`build.bat` 会先复制基底，再对副本写入版本，不会修改 `base\base_branded.exe`。手动构建时也可以单独执行：

```bat
py -3.11 scripts\patch_version_info.py "build\base_v122.exe"
```

该脚本会就地修改目标 EXE 的版本资源，不会移动 overlay。修改前请先备份。V1.2.2 的版本号为 `1.2.2.0`，在 `scripts/patch_version_info.py` 顶部的 `VERSION` 中维护。

## 校验

`validate_final.py` 会检查：

- `primary_ui`、`sound_library`、`detector` 三个模块是否与生成的 marshal 一致；
- 如果存在 `build\icons\first_icon.ico` 和 `assets\audio\itachi_exit_v2_35.wav`，检查嵌入资源是否一致；
- 输出文件大小与 SHA256。

最后建议实际启动 EXE，用测试模式确认界面和检测逻辑正常。

## 常见问题

| 错误 | 原因 |
| :--- | :--- |
| `cookie not found` | 目标不是 PyInstaller 单文件 EXE，或文件被修改过 |
| `PYZ header mismatch` | 基底不是预期的 PyInstaller 格式 |
| `module not in PYZ` | 基底缺少 `primary_ui` / `sound_library` / `detector` |
| `patched detector does not fit its PYZ slot` | 基底检测模块槽位太小，或补丁后模块过大 |
| `does not fit slot` | 新图标/音频压缩后仍大于原资源槽 |
| `FileNotFoundError: assets/interface/...` | 界面模板未准备，见上文模板清单 |
| `'py' is not recognized` | 安装 Python 3.11，或先设置 `PYTHON` 环境变量为实际解释器路径，例如 `set PYTHON=C:\Python311\python.exe` |

## 说明

- 构建只写 `build\` 和生成的 marshal 文件，不会修改 `base\base_branded.exe`。
- `patch_version_info.py` 例外，它会就地修改传入的 EXE。
- `sound_library.marshal` 是从基底重新生成的，因此重新构建的 EXE 可能与 Release 附件相差几个字节；以 `validate_final.py` 的输出和 Release 中公布的 SHA256 为准。
- 本项目没有包含上游源码或二进制；如需完整源码构建，请先与上游作者确认授权与构建方式。
