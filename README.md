# Thor MIUI Camera

为小米 12S Ultra（`thor`）适配的 MIUI 相机模块，支持已核对的 Android 16 / 17 驱动组合。
保留徕卡风格、红色 Leica 桌面图标、录像防抖和高倍率辅助取景小窗。

> [!NOTE]
> **作者碎碎念：**开发这个项目的契机是我手上有一部12SU的备用机，想刷类原生却苦于类原生的刷机包自带的相机都有问题（比如录像卡死）。于是用Codex把相机移植了。由于本人并不懂编程，所以该项目的代码全部由Codex编写+一部分反编译。目标嘛~~能用就行。手搓移植的大手子请不要拷打我(ToT)
>
> **关于成果：**基本实现了相机移植，我自己没试出问题；貌似还歪打正着地修复了自带相机的卡死问题(～￣▽￣)～
>
> 总之，欢迎下载试用。如果遇到问题欢迎提交issue

**开发测试版：仅适用于下表中的驱动与系统库组合。安装器按哈希选择配置，不只检查 Android 版本。**

[下载 0.1.5](https://github.com/GSQ2004/thor-miuicamera/releases/tag/v0.1.5) ·
[兼容配置与哈希](sources.json) · [构建说明](docs/BUILDING.md) · [验证记录](docs/VALIDATION.md)

## 兼容范围

| Android | 已核对 ROM | 状态 |
| --- | --- | --- |
| 16 / API 36 | `crDroidAndroid-16.0-20260530-thor-v12.10` | 0.1.5 已安装、重启及实拍验证 |
| 17 / API 37 | `24.0-20261107-NIGHTLY-thor` | 保留 0.1.4 已验证的配置，0.1.5 本轮未刷回重测 |

Android 16 实测环境为 KernelSU-Next + Magic Mount-RS，SELinux 保持 Enforcing。
拍照保存、普通录像、防抖录像、视频播放及声音、高倍率取景小窗已由实机用户确认正常。
尚未穷尽全部镜头、拍摄模式、分辨率、帧率和画质。其他 ROM 需要另行核对相机驱动、HAL 和系统库。

## 安装

1. 确认设备为 `thor`，系统原有相机正常，并已安装 root 管理器。
2. 从 Release 下载完整模块 ZIP。**不要把 GitHub 的 Source code ZIP 当作模块安装。**
3. 在管理器中安装模块。KernelSU 系列需要可用的系统挂载元模块；本项目实测使用 Magic Mount-RS。
4. 重启，打开相机，按需授予相机、麦克风和照片/视频权限。相机应用本身不需要 root。
5. 测试照片保存、录像、声音、不同镜头和防抖。

模块 ID 沿用 `thor_miuicamera_los24`，便于旧版本升级。
若有其他占用 `com.android.camera` 的安装，安装器会中止，不会自动卸载它。
升级 ROM、切换 Android 大版本或更换相机驱动前先禁用模块，再在新系统上重新安装，重新匹配配置。

## 已完成的修复

- 补齐新版 `CaptureResultExtras` 接口，适配首次权限流程和图库跳转。
- 修补应用端 JNI 的 libgui ABI 差异，并补入兼容 shim。
- 为 Android 16 / 17 分别选用已核对的 HAL，修正三个 ISPv3 电源控制命令，恢复录像切换。
- 补齐 Vidhance MIS 插件，恢复超级防抖和 PRO。
- 用 PRIVATE ImageReader / ImageWriter 桥接保留原尺寸辅助流，恢复长焦取景小窗和定位白框。
- 按系统版本生成相机 seapp 映射及相应规则，SELinux 保持强制模式。

模块挂载 APK、应用库、HAL 和配置；不刷写内核或整个 vendor 分区。
SELinux 规则使用 ROM 中已有的应用域，会作用于同域应用，并非独立新建的相机域。

## 排查与卸载

- 如果图标存在但应用立即退出，检查 root 管理器是否对相机开启了“卸载模块 / 隐藏模块挂载”。相机进程需要能读取自己的 APK 和依赖。
- 如果启动器显示通用图标，检查启动器是否能读取模块 APK；不必给启动器或相机授予 root。
- 管理器的模块“操作 / Action”按钮将日志写入 `/data/adb/modules/thor_miuicamera_los24/diagnostics/`。
- 也可运行 `scripts/collect-device.ps1` 收集 ADB 日志。提交问题前检查日志中的设备及应用信息，不必上传照片或视频。
- 正常退出：在管理器禁用或卸载模块后重启。

已有可用的 ADB 和 shell root 时，可单独禁用本模块：

```text
adb shell su -c "touch /data/adb/modules/thor_miuicamera_los24/disable"
adb reboot
```

## 源码与材料

仓库提供构建脚本、补丁逻辑、Java 缓冲桥接、原生 shim 和模块模板。
原厂 APK、原生库、ROM 镜像、构建工具、签名私钥和个人调试数据不纳入 Git。
构建所需原厂材料及 SHA-256 见 [构建说明](docs/BUILDING.md) 和 [sources.json](sources.json)。

Release 是经测试的成品，包含必要的原厂应用及依赖；这些组件和 Leica 标志的权利仍归各自权利人。
本项目与 Xiaomi、Leica、LineageOS、crDroid 无官方关联。代码来源与许可范围见 [NOTICE.md](NOTICE.md)。

## 参考

- [LineageOS thor Wiki](https://wiki.lineageos.org/devices/thor/)
- [LineageOS thor 设备树](https://github.com/LineageOS/android_device_xiaomi_thor)
- [cupid-development 相机移植与补丁](https://github.com/cupid-development/android_device_xiaomi_miuicamera-cupid)
- [Magisk 模块指南](https://topjohnwu.github.io/Magisk/guides.html)
- [KernelSU 模块指南](https://kernelsu.org/guide/module.html)
