#!/system/bin/sh
MODDIR=${0%/*}
mkdir -p "$MODDIR/diagnostics"
chmod 0700 "$MODDIR/diagnostics"
{
  date
  getprop ro.product.device
  getprop ro.lineage.version
  getprop ro.build.version.sdk
  getenforce
  pm path com.android.camera | cat
  ps -AZ | grep -E 'com.android.camera|camera.provider|cameraserver'
} > "$MODDIR/diagnostics/status.txt" 2>&1
dumpsys package com.android.camera 2>&1 | cat > "$MODDIR/diagnostics/package.txt"
dumpsys media.camera 2>&1 | cat > "$MODDIR/diagnostics/media-camera.txt"
logcat -b crash -d -t 300 > "$MODDIR/diagnostics/crash.txt" 2>&1
logcat -b all -d -t 3000 | grep -iE 'com.android.camera|miuicamera|campostproc|mianode|algoup|avc: denied|linker|CameraService|CameraProvider' > "$MODDIR/diagnostics/camera-log.txt" 2>&1
chmod 0600 "$MODDIR"/diagnostics/*.txt
echo "Diagnostics saved in $MODDIR/diagnostics"

