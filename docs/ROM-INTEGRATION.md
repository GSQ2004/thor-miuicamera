# Thor MIUI Camera：直接集成 ROM

此版本供小米 12S Ultra（thor、arm64）的 ROM 维护者集成。没有 ROM 名称、Android SDK 数值或驱动哈希白名单，也不依赖 Magisk、KernelSU、挂载元模块或模块安装脚本。
不需要在手机上强行刷入 Root 模块来集成。移除这些集成门槛不代表相机二进制已兼容所有 Android ABI；具体 ROM 仍需编译和实拍验证。

## 源码分支

模块和 ROM 集成共用 `main` 主线；不同用途通过目录、导出命令和 Release 附件区分。

```sh
git clone --branch main --single-branch https://github.com/GSQ2004/thor-miuicamera.git
cd thor-miuicamera
```

## 使用

在项目源码目录，用完整模块的解压目录导出（`module/` 空模板不能直接作为输入）：

```sh
python -m zipfile -e thor-miuicamera-android16-17-0.1.7-EXPERIMENTAL.zip work/rom-input
python scripts/export_rom.py --module work/rom-input --output output/thor-rom --app-domain platform_app --tree-path vendor/xiaomi/thor-miuicamera
```

`--app-domain` 应换成目标 ROM 实际提供的应用域，例如 `platform_app_36`；也可使用维护者已定义的相机专属域。
CLI 不读取手机或编译主机的 ROM 版本，也不校验目标 ROM 的驱动哈希。
`--hal-profile` 默认为 `rom`，可显式选择下文说明的已知补丁。导出目录已存在时会退出，防止覆盖之前的成果。

1. 将本目录放到 ROM 源码 `vendor/xiaomi/thor-miuicamera`（如导出时另选路径，以 `integration-report.json` 为准）。
2. 在设备产品 makefile 添加：

```make
$(call inherit-product, vendor/xiaomi/thor-miuicamera/product.mk)
```

3. 在设备 `BoardConfig.mk` 添加：

```make
include vendor/xiaomi/thor-miuicamera/BoardConfig.mk
```

4. 对照设备树合并 `properties.example`。将 `com.android.camera` 追加到原有 `persist.vendor.camera.privapp.list`，保留其他包；已有相同属性定义应合并，不能重复定义。
5. 移除设备树中其他占用 `com.android.camera` 的 APK 定义、以及与本包重复安装的库/配置项。不要同时保留旧模块挂载。

主 APK 通过 Soong 预签名导入到 system 的特权应用目录，权限 XML 同样位于 system。覆盖 APK 通过独立的 product 应用导入，其原有 overlay Manifest 保留。
保持原开发签名，不默认重签平台证书，也不禁用签名验证。`preprocessed` 保留已签名 APK；如果目标构建的预处理检查报对齐/压缩错误，应调整打包并使用维护者自己的密钥签名，而不是关闭整个 ROM 的校验。

## HAL 与策略由目标 ROM 决定

默认 `--hal-profile rom` 不导出 `camera.qcom.so` 或 `libmis_plugin_vidhance.so`，避免覆盖已有 vendor 相机实现。目标 ROM 必须自行提供相互匹配的 HAL、campostproc 服务及其依赖。
也可明确选择 `android16-crdroid1210` 或 `android17-lineage24` 导出已知配套的补丁 HAL/防抖插件；选择只是取出文件，不会证明适用于当前驱动。维护者须先对照目标 ROM 的原库与驱动核对补丁。

导出时 `--app-domain` 指定目标 ROM 已存在、可用于该特权应用的 SELinux 域；不再根据 SDK 强制选择 `platform_app` / `platform_app_36`。
生成规则仍引用目标设备树需提供的 `vendor_hal_camerapostproc_xiaomi*`、`vendor_hal_qspmhal_client` 等类型/属性。
若设备树命名、公共策略可见性或 seapp 规则冲突，维护者应在所属策略目录合并修正，移除重复映射；不要用空类型、全域 allow 或 permissive 掩盖问题。
这里不复制整份 `plat_seapp_contexts`，只新增精确包名映射。

ELF 通过 Soong 预编译库模块安装。`check_elf_files: false` 仅跳过这些闭源预编译库的构建期依赖匹配；不会修复私有 ABI，也不会关闭 ROM 全局检查。
需要在目标系统核对动态链接依赖、libgui/BufferQueue 接口，以及 campostproc 创建会话与回调。

## 当前验证边界

导出器会检查输入文件完整性和 APK ZIP 内容，保留 APK、原生库原字节，并输出报告与校验清单。
本集成目录尚未在目标 ROM 源码中完成 Soong 编译、刷机和实拍验证。`createSession` 卡死仍需目标系统日志定位，去掉安装限制本身不会修复该故障。
测试至少覆盖开机、桌面图标、预览、拍照保存、普通录像/声音、超级防抖/PRO 和高倍率小窗。
发布前先完成实机测试，并获得项目作者发布确认。

原厂 APK/库等权利范围见 `NOTICE.md`；集成配置不会改变原厂材料的许可。
