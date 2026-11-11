# 验证记录

## 0.1.7：白底自适应图标（实机确认）

图标设计已由用户审核同意，实机测试获用户确认，随后用户同意发布并明确注明缓存限制。

- 文件：`thor-miuicamera-android16-17-0.1.7-EXPERIMENTAL.zip`，132281923 字节。
- ZIP SHA-256：`a2fe19b7ee34690937a1266192d6bac29e42fa3f356c7fe9796d7e00b645c016`。
- APK versionCode：610006107；模块 versionCode：8。
- 三个图标资源为 adaptive-icon，背景为白色，前景为审核通过的蓝色相机线框与青绿色镜头。
- 与 0.1.6 比较，APK 仅改变三个图标资源及 Manifest 内一个 versionCode 整数值；DEX、资源表、权限与其他 APK 内容相同。
- 原生库、HAL 及相机配置与 0.1.6 相同。
- 已通过签名、16 KiB 对齐、CRC、校验清单和 aapt2 检查。
- 用户已确认白底图标外观、照片拍摄保存、录像保存/播放/声音、防抖和 20 倍以上小窗正常。
- 本轮在 thor / crDroid 12.10 / API 36 / KernelSU-Next + Magic Mount-RS 上测试，SELinux 保持 Enforcing。
- 预览出帧：拍照 71；约 52.5 倍时主预览 721、辅助流 86；普通录像 77；超级防抖 79；PRO 83。用户实拍后 crash buffer 为空。
- 升级限制：首次重启后，系统复用旧解析缓存、桌面复用旧图标；备份并仅清理相机解析缓存后再次重启，系统识别 610006107；随后单独重建相机主入口的图标缓存才正确显示。
- 未清空桌面数据或相机数据；缓存处理是本轮手动测试操作，安装包不包含自动刷新机制。
- 本轮未重新刷回 Android 17。

## 0.1.6：原创桌面图标

日期：2026-11-11。仅更新桌面图标及相应版本、说明和构建元数据。

- 文件：`thor-miuicamera-android16-17-0.1.6-EXPERIMENTAL.zip`，132281694 字节。
- ZIP SHA-256：`9d962c888835229f6e68b8965e6bc8410b600411a5fed3a0a6034c55b39ae238`。
- 原创矢量源：`assets/camera-icon.xml`，SHA-256 为 `d4ad64826a84da5c2ac131cdd767004e25dacb0b70484ff46deb84d1d3bd8e15`。
- 与 0.1.5 对比，排除签名后 APK 文件集合不变，只有 `res/HAL.xml`、`res/O9k.xml`、`res/fB5.xml` 内容变化。
- 所有 DEX、Manifest、资源表、其他 APK 内容、原生库和驱动补丁均保持不变。
- 同一开发证书签名验证、16 KiB ZIP 对齐、成品 CRC 与校验清单通过。
- 新图标矢量已渲染检查；本轮未重新安装到实机，不能将下述 0.1.5 实测写成 0.1.6 实测。

## 0.1.5 验证记录

日期：2026-11-11。成品文件为 `thor-miuicamera-android16-17-0.1.5-EXPERIMENTAL.zip`。

- 大小：132271565 字节。
- ZIP SHA-256：`c15e6d514c5d38f236c20dad3e9192ca8ce80be0fd5291417598f825e6163be6`。
- APK SHA-256：`9b9cc5fefeeab868cde645ea7c771694f292d66afcd1b2ade75dce230c691893`。

## Android 16 实机

设备为 thor，ROM 为 `crDroidAndroid-16.0-20260530-thor-v12.10`，API 36，
构建时间戳 1780172458，内核 `5.10.256-PhoenyxCore.LTO.v1`。
安装环境为 KernelSU-Next + Magic Mount-RS，已重启，SELinux 为 Enforcing。
安装器选中 `android16-crdroid1210`，挂载 HAL 和 APK 的哈希与成品匹配。

| 项目 | 设备观察 |
| --- | --- |
| 后置拍照预览 | 主预览 871 帧，预览回传 870 帧 |
| 高倍率取景窗 | 约 96.2 倍，主预览 1243 帧，408×306 辅助流 46 帧；桥接首次转发及 ROI 更新成功 |
| 普通录像预览 | 模式 0x8004，172 帧 |
| 超级防抖预览 | 模式 0x800d，108 帧 |
| 防抖 PRO 预览 | 模式 0x800f，111 帧 |
| 崩溃检查 | 测试后 crash buffer 为空，本轮未观察到相机崩溃 |

用户确认照片拍摄与保存、录像保存与播放及声音、防抖录像、20 倍以上取景小窗实时变化正常。
原始日志和截图保存在本地，不公开上传。

## 静态检查

- ZIP CRC 和全部 26 个清单条目通过，清单使用 LF 换行。
- 9 项兼容配置接受 / 拒绝场景通过。
- Android 16 seapp 映射、生成的 SELinux 规则和 KernelSU 策略解析通过。
- 已核对实际 `camera.ko` 的 ISPv3 11/12 电源命令分支，再修改对应 HAL 的三个立即数。
- 已核对 Android 16 libgui、CaptureResultExtras 接口和 Vidhance 导入符号。

## Android 17 与边界

0.1.4 已在 `24.0-20261107-NIGHTLY-thor` 验证拍照、录像、防抖、长焦辅助小窗及定位白框，用户确认正常。
0.1.5 中 Android 17 HAL、防抖插件和应用端 system/lib64 库与 0.1.4 逐字节相同，
但本轮没有刷回 Android 17 重新测试 0.1.5。

未穷尽所有镜头、模式、分辨率、帧率和画质；本轮未另测 Magisk。
目前不对所有 Android 16 ROM 作兼容承诺，安装器会拒绝未核对的组合。
