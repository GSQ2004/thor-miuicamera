# 在 Windows 上构建

当前脚本按 Windows 工具链编写。已使用 Python 3.12、JDK（包含 `javac` 和 `keytool`）、
Android SDK Build Tools 36.0.0、Android SDK Platform 37.0、NDK 28.2.13676358。
运行命令前进入仓库根目录。

## 准备工具

1. 配置 Python 和 Java 的 PATH。
2. 用 Android SDK Manager 安装上述 Build Tools、Platform 和 NDK；可通过 `--sdk`、`--ndk` 指定目录。
3. 把官方 Apktool 3.0.3 fat JAR 放到 `tools/apktool-cli.jar`。构建需要它提供 `com.android.tools.smali` 的 smali / baksmali 类；本地使用的 JAR SHA-256 为 `29fc610eed9dd349e75d40fd5af02538e0118b08d56a61ef6f53f8256adadc9a`。
4. 安装 Python 依赖：

```powershell
python -m pip install --target tools/python -r requirements.txt
```

构建参数 `--build-tools` 不会覆盖图标脚本中固定的 36.0.0；请按此版本安装。
Java 桥接和图标资源当前都使用 `platforms/android-37.0/android.jar` 编译。
编译使用 SDK 37 不代表 APK 最低运行版本为 Android 17。

## 准备输入

自行准备 `thor_images_OS3.0.6.0.VLACNXM_15.0` 原厂完整包，提取以下完整文件到 `inputs/`：

```text
inputs/
  MiuiCamera.apk
  MiuiCameraOverlayLeicaed.apk
  libcamera_algoup_jni.xiaomi.so
  libcamera_mianode_jni.xiaomi.so
  libmicampostproc_client.so
  vendor.xiaomi.hardware.campostproc@1.0.so
  camera.qcom.so
  libmis_plugin_vidhance.so
  crdroid-16-20260530/
    camera.qcom.so
```

最后一个 HAL 来自 `crDroidAndroid-16.0-20260530-thor-v12.10.zip`，其余二进制来自上述原厂包。
桌面图标直接使用仓库中的原创 `assets/camera-icon.xml`，不需要下载品牌标志。
0.1.7 使用内嵌白色背景与透明前景矢量的 adaptive-icon，不依赖新增的应用资源 ID。
构建同时仅修改二进制 Manifest 中 versionCode 的整数值；其余 Manifest 保留。
文件哈希必须匹配 `sources.json`。不要混入不完整 APK、旧 MIUI 版本或其他设备的库。
`module/system/product/etc/device_features/thor.xml` 是同一原厂包的设备配置。

仓库提供 `scripts/extract_ota_partitions.py`，用于从完整 OTA payload 提取分区并校验数据：

```powershell
python scripts/extract_ota_partitions.py --help
```

它不负责自动解析分区文件系统；提取所需 APK / ELF 仍需相应文件系统工具。

## 构建与签名

```powershell
python scripts/build.py
```

成功时在 `dist/` 生成带时间戳的模块 ZIP，包内含 `build-report.json` 和 `SHA256SUMS`。
脚本核对原始 DEX、APK 和库的身份，编译补丁、对齐并签名，分别构建两个 HAL payload。
输入不匹配会中止。

首次构建会在 `tools/thor-camera-dev.jks` 生成本地开发签名密钥。
密钥是本机构建材料，不上传仓库；密码参数 `android` 仅对应这个开发密钥，不是账号凭据。
后续更新应保留自己的签名密钥。自行构建使用的证书与本仓库 Release 的证书不同，
不要假设能直接覆盖安装另一证书签名的相机。

`module/` 是模板，缺少 APK / ELF 和校验清单，不能直接压缩安装。
`package_module.py` 只用于重新打包已经完整构建的模块目录，不代替构建过程。

## 验证

```powershell
python -m compileall -q scripts
```

兼容配置测试可在 POSIX shell 或 Android shell 中执行：

```sh
sh scripts/check_compatibility_profiles.sh module/compatibility.sh
```

静态检查不能证明实机功能正常；每个新 ROM / 驱动组合仍需检查接口并完成启动、预览和实拍验证。
