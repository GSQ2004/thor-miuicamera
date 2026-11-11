#!/system/bin/sh
MODDIR=${0%/*}
counter=0
while [ "$(getprop sys.boot_completed)" != 1 ] && [ "$counter" -lt 120 ]; do
  sleep 2
  counter=$((counter + 1))
done
# Reload only when the provider mapped the original HAL before module mounts.
# Match the file inode, since the visible library path is the same in both cases.
provider_pid=$(getprop init.svc_debug_pid.vendor.camera-provider-2-7)
expected_inode=$(stat -c %i /vendor/lib64/hw/camera.qcom.so 2>/dev/null)
mapped_line=$(grep '/vendor/lib64/hw/camera.qcom.so$' "/proc/$provider_pid/maps" 2>/dev/null | head -n 1)
set -- $mapped_line
if [ -n "$expected_inode" ] && [ -n "$5" ] && [ "$expected_inode" != "$5" ]; then
  setprop ctl.restart vendor.camera-provider-2-7
  setprop ctl.restart cameraserver
fi
{
  date
  printf 'device=%s\nlineage=%s\ncrdroid=%s\napi=%s\n' "$(getprop ro.product.device)" "$(getprop ro.lineage.version)" "$(getprop ro.crdroid.version)" "$(getprop ro.build.version.sdk)"
  cat "$MODDIR/compatibility-profile.prop"
  pm path com.android.camera | cat
  getenforce
  ls -lZ /system/priv-app/MiuiCamera/MiuiCamera.apk /system/lib64/libgui_shim_miuicamera.so
} > "$MODDIR/startup.log" 2>&1

