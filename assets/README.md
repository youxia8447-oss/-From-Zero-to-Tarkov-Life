# assets/

仓库不包含第三方音频、图标、字体或游戏素材。构建时可按需放入以下文件：

```text
assets/icons/first_icon.ico
assets/audio/itachi_exit_v2_35.wav
```

`scripts/patch_assets.py` 会读取这两个文件并替换基底 EXE 中的图标和退出音效槽位。替换前请确认你拥有相应素材的再分发权限。

默认主题还期望部署目录中存在：

```text
icons/first_icon.ico
icons/killer_queen.ico
icons/itachi_mangekyo.ico
```

这些图标需要与最终 EXE 放在同一目录。缺少 `icons` 文件夹时，程序会回退到内嵌默认图标。
