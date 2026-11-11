# 0.1.5 验证记录

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
