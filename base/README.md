# base/

构建时把上游的 PyInstaller 单文件 EXE 放在这里，命名为：

```text
base/base_branded.exe
```

该文件不包含在仓库中：

- 体积约 107 MB，超过 GitHub 普通的单文件提交建议；
- 包含上游代码、二进制与第三方素材；
- 需要由使用者自行获取并确认分发/使用权限。

准备方法见 [../docs/BUILD.md](../docs/BUILD.md)。
