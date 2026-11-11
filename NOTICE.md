# 来源、权利与许可范围

本仓库未为全部内容统一授予开源许可证。没有单独许可声明的项目代码，默认保留权利；
公开可见不等于已授予无限制再分发许可。

## 上游代码

`native/libgui_shim_miuicamera.c` 基于 The LineageOS Project / cupid-development 的 shim，
保留其 2023 年版权与 Apache-2.0 标识。`scripts/patch_native.py` 的应用端修补方式参考同一上游。
原生 shim 对应的 Apache License 2.0 全文见 `LICENSES/Apache-2.0.txt`。

参考仓库：
https://github.com/cupid-development/android_device_xiaomi_miuicamera-cupid

核对提交：`f3ed20d16a65cc3dcd1fac0c06b224190f3ba150`。
本项目另外实现了 thor 的驱动配置、HAL 电源命令修补、辅助流桥接和模块打包。

## 原厂材料与标志

MIUI Camera APK、原厂 ELF 库、徕卡资源覆盖包和设备配置来自 Xiaomi 原厂固件；
Android 16 HAL 来自用户提供的 crDroid ROM，保留其版本原有内容。
这些组件仍受各自原有许可或权利限制，不因本仓库公开而成为 Apache-2.0 代码。

`module/system/product/etc/device_features/thor.xml` 为原厂设备配置。
原厂二进制没有纳入 Git；Release 成品包含运行所必需的应用、原生库和资源。
0.1.6 起桌面图标使用本项目原创的几何相机矢量图，源文件为 `assets/camera-icon.xml`，不含品牌文字或标志。
相机应用内原有的品牌资源仍归各自权利人所有；桌面图标更新没有移除这些应用内资源。

本项目不代表 Xiaomi、Leica、LineageOS 或 crDroid 官方。
