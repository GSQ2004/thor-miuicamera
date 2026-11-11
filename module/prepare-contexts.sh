#!/system/bin/sh
# Preserve the installed ROM's mappings; add one exact privileged package match.
# This changes the app domain, not Android's package-signature verification.
prepare_camera_contexts() {
  camera_moddir=$1
  camera_contexts=${2:-/system/etc/selinux/plat_seapp_contexts}
  [ -r "$camera_contexts" ] || return 1
  case "$(getprop ro.build.version.sdk)" in
    36) camera_app_domain=platform_app ;;
    37) camera_app_domain=platform_app_36 ;;
    *) return 1 ;;
  esac
  grep -Eq "domain=$camera_app_domain([[:space:]]|$)" "$camera_contexts" || return 1
  [ -s "$camera_moddir/sepolicy.camera.template" ] || return 1
  sed "s/platform_app_36/$camera_app_domain/g" "$camera_moddir/sepolicy.camera.template" > "$camera_moddir/sepolicy.rule.new" || return 1
  chmod 0644 "$camera_moddir/sepolicy.rule.new" || return 1
  mv -f "$camera_moddir/sepolicy.rule.new" "$camera_moddir/sepolicy.rule" || return 1
  mkdir -p "$camera_moddir/system/etc/selinux" || return 1
  camera_new="$camera_moddir/system/etc/selinux/plat_seapp_contexts.new"
  # Also handles reinstalling while an earlier version is already mounted.
  awk '!/name=com[.]android[.]camera([[:space:]]|$)/' "$camera_contexts" > "$camera_new" || return 1
  printf '\nuser=_app seinfo=default isPrivApp=true name=com.android.camera domain=%s type=app_data_file levelFrom=user\n' "$camera_app_domain" >> "$camera_new" || return 1
  chmod 0644 "$camera_new" || return 1
  camera_label=$(ls -Zd "$camera_contexts" | awk '{print $1}')
  case "$camera_label" in u:object_r:*:s0) ;; *) return 1 ;; esac
  chcon "$camera_label" "$camera_new" || return 1
  mv -f "$camera_new" "$camera_moddir/system/etc/selinux/plat_seapp_contexts"
}

