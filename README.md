# Thor MIUI Camera · ROM 集成分支

<img src="assets/camera-icon.svg" alt="Thor Camera 原创相机图标" width="96" />

**`INTEGRATION` 专供 ROM 维护者将相机内置到刷机包。** 普通用户的 Magisk / KernelSU 模块请使用 [main 分支](https://github.com/GSQ2004/thor-miuicamera/tree/main)。

> [!NOTE]
> **作者碎碎念：**开发这个项目的契机是我手上有一部12SU的备用机，想刷类原生却苦于类原生的刷机包自带的相机都有问题（比如录像卡死）。于是用Codex把相机移植了。由于本人并不懂编程，所以该项目的代码全部由Codex编写+一部分反编译。目标嘛~~能用就行。手搓移植的大手子请不要拷打我(ToT)
>
> **关于成果：**基本实现了相机移植，我自己没试出问题；貌似还歪打正着地修复了自带相机的卡死问题(～￣▽￣)～
>
> 总之，欢迎下载试用。如果遇到问题欢迎提交issue

[下载 ROM 集成包](https://github.com/GSQ2004/thor-miuicamera/releases/tag/rom-integration-20261114) · [完整集成说明](docs/ROM-INTEGRATION.md) · [原厂输入与构建](docs/BUILDING.md)

## 获取集成分支

```sh
git clone --branch INTEGRATION --single-branch https://github.com/GSQ2004/thor-miuicamera.git
cd thor-miuicamera
```

集成包包含 `Android.bp`、`product.mk`、SELinux 配置、权限 XML、相机 APK 和配套库。将解压后的目录放到 `vendor/xiaomi/thor-miuicamera`，按完整说明接入产品配置与 BoardConfig。
本分支不限定目标 ROM 名称、Android SDK 数值或目标驱动哈希，不依赖 Root 管理器和元模块。默认保留目标 ROM 的 HAL，已有 HAL 补丁必须由维护者明确选择。
仓库中的 `module/` 等目录是构建和导出的来源；ROM 集成入口为 `scripts/export_rom.py`，不会执行 Root 模块安装脚本。

## 验证状态

**实验性预发布：导出完整性与自动化检查已通过，目标 ROM 编译、刷机和实拍尚未验证。** 适用硬件仍为 `thor / arm64`。解除集成门槛不会自动修复私有 ABI 或 campostproc `createSession` 问题。
ROM 集成 ZIP 用于 ROM 源码，不能作为 Root 模块或 Recovery 刷机包直接刷入。
输入材料和原厂组件的权利范围见 [NOTICE.md](NOTICE.md)。
