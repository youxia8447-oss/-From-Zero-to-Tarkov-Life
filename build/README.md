# build/

构建输出目录。`build.bat` 会在此生成：

```text
build/从零开始的塔科夫生活_V1.exe
```

该目录中的 EXE、临时基线和校验产物都已写入 `.gitignore`，不要提交到仓库。

发布时建议把 EXE、`settings.json`、`icons/` 和 `README.md` 一起压缩，作为 GitHub Release 附件上传。
