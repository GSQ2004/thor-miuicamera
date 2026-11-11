#!/system/bin/sh
# Select only audited framework/driver/HAL combinations, independent of ROM name.
select_camera_profile() {
  camera_profile_error='Unsupported Android/camera-driver combination.'
  case "$1:$2" in
    36:93818c52e0f15f123a339157ee82d30586403056a0bb0532d2b7fe7ab32fe6f9)
      camera_profile=android16-crdroid1210
      camera_app_domain=platform_app
      camera_hal_payload=compat/android16/camera.qcom.so
      camera_stock_hal_hash=4ffa7ed9ddc1a5e48b4ec91d2b4f6ad3233d02d80c1edfb6b4c71d98ae919256
      camera_patched_hal_hash=900dfb00f26dfce1a83e65b6a7839e4a0baa7f841c8d9f36aafdc2d795750b46
      [ "$4" = c230c5ea6b9e5868a1d36d928ccd21cf20e206391af1dc71e96e10fbe4514c3e ] || {
        camera_profile_error='Android 16 libgui differs from the audited crDroid build.'
        return 1
      }
      ;;
    37:6ce5312377c01802a1e271a2e9b499783dfb751e590618ed1609f2f422f55a2f)
      camera_profile=android17-lineage24
      camera_app_domain=platform_app_36
      camera_hal_payload=system/vendor/lib64/hw/camera.qcom.so
      camera_stock_hal_hash=26ad8ccef40638c48cd595f1bc3ed835d0b5e754d8d173ef8b374c566396ba07
      camera_patched_hal_hash=240610b0bcb05d0d8d39d799fa1fc27dde8dbf1ede38fb87baa9f834ae5dbebc
      ;;
    *) return 1 ;;
  esac
  case "$3" in
    "$camera_stock_hal_hash"|"$camera_patched_hal_hash") ;;
    *) camera_profile_error='Camera HAL differs from the selected profile; refuse replacement.'; return 1 ;;
  esac
  camera_profile_error=''
}
