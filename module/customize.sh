#!/system/bin/sh
# Sourced by the root manager's installer.
[ "$BOOTMODE" = true ] || abort 'Install from Magisk/KernelSU Manager after booting Android.'
[ "$ARCH" = arm64 ] || abort 'Only arm64 is supported.'
[ "$(getprop ro.product.device)" = thor ] || abort 'This module is only for Xiaomi 12S Ultra (thor).'
case "$API" in
  36|37) ;;
  *) abort 'This experimental build supports Android 16/17 (API 36/37) only.' ;;
esac

ui_print '- Experimental: not all camera modes and image quality have been validated.'
[ -s "$MODPATH/system/priv-app/MiuiCamera/MiuiCamera.apk" ] || abort 'Missing camera APK; source templates are not installable.'
[ -s "$MODPATH/SHA256SUMS" ] || abort 'Missing payload checksums.'
if ! (cd "$MODPATH" && sha256sum -c SHA256SUMS > payload-check.log 2>&1); then
  cat "$MODPATH/payload-check.log"
  abort 'Corrupt or incomplete module payload.'
fi
camera_driver_hash=$(sha256sum /vendor/lib/modules/camera.ko 2>/dev/null)
camera_driver_hash=${camera_driver_hash%% *}
camera_hal_hash=$(sha256sum /vendor/lib64/hw/camera.qcom.so 2>/dev/null)
camera_hal_hash=${camera_hal_hash%% *}
camera_gui_hash=$(sha256sum /system/lib64/libgui.so 2>/dev/null)
camera_gui_hash=${camera_gui_hash%% *}
. "$MODPATH/compatibility.sh"
select_camera_profile "$API" "$camera_driver_hash" "$camera_hal_hash" "$camera_gui_hash" || abort "$camera_profile_error"
ui_print "- Selected compatibility profile: $camera_profile"

existing_camera=$(pm path com.android.camera 2>/dev/null)
case "$existing_camera" in
  '') ;;
  package:/system/priv-app/MiuiCamera/MiuiCamera.apk) ;;
  *) abort 'com.android.camera already exists. Resolve that package conflict first; no apps were removed.' ;;
esac

[ "$camera_hal_payload" = system/vendor/lib64/hw/camera.qcom.so ] || \
  cp -f "$MODPATH/$camera_hal_payload" "$MODPATH/system/vendor/lib64/hw/camera.qcom.so" || abort 'Cannot select vendor camera HAL.'
camera_selected_hash=$(sha256sum "$MODPATH/system/vendor/lib64/hw/camera.qcom.so")
camera_selected_hash=${camera_selected_hash%% *}
[ "$camera_selected_hash" = "$camera_patched_hal_hash" ] || abort 'Selected HAL checksum mismatch.'
printf 'api=%s\nprofile=%s\napp_domain=%s\ndriver_sha256=%s\nhal_sha256=%s\n' \
  "$API" "$camera_profile" "$camera_app_domain" "$camera_driver_hash" "$camera_patched_hal_hash" > "$MODPATH/compatibility-profile.prop"

camera_allowlist=$(getprop persist.vendor.camera.privapp.list)
case ",$camera_allowlist," in
  *,com.android.camera,*) ;;
  *) camera_allowlist="${camera_allowlist:+$camera_allowlist,}com.android.camera" ;;
esac
printf '\npersist.vendor.camera.privapp.list=%s\n' "$camera_allowlist" >> "$MODPATH/system.prop"

set_perm_recursive "$MODPATH" 0 0 0755 0644
chcon u:object_r:vendor_file:s0 "$MODPATH/system/vendor/lib64/hw/camera.qcom.so" || abort 'Cannot label vendor camera HAL.'
chcon u:object_r:vendor_file:s0 "$MODPATH/system/vendor/lib64/libmis_plugin_vidhance.so" || abort 'Cannot label video stabilization plugin.'
for script in post-fs-data.sh service.sh action.sh prepare-contexts.sh; do
  set_perm "$MODPATH/$script" 0 0 0755
done
. "$MODPATH/prepare-contexts.sh"
prepare_camera_contexts "$MODPATH" || abort 'Cannot prepare the camera SELinux app mapping for this ROM.'
if [ "$KSU" = true ]; then
  ui_print '- KernelSU needs working system mounting (a metamodule on current KernelSU).'
fi
ui_print '- Reboot, then grant camera/microphone/media permissions when prompted.'
ui_print '- Keep the module ZIP and recovery/ADB disable instructions available.'

