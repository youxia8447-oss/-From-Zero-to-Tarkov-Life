# build/

构建输出目录。`build.bat` 会在此生成：

```text
build/base_v122.exe
build/从零开始的塔科夫生活_V1.2.2.exe
```

该目录中的 EXE、临时基线和校验产物都已写入 `.gitignore`，不要提交到仓库。

发布时建议把 EXE、`settings.json`、`icons/` 和 `README.md` 一起压缩，作为 GitHub Release 附件上传。当前 V1.2.2 发布包的结构：

```text
从零开始的塔科夫生活/
├─ 从零开始的塔科夫生活.exe
├─ settings.json
├─ icons/
│  ├─ first_icon.ico
│  ├─ itachi_mangekyo.ico
│  └─ killer_queen.ico
└─ README.md
```
