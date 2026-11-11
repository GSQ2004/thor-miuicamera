#!/system/bin/sh
MODDIR=${0%/*}
# Runs before systemless mounting and zygote. Refresh after same-branch updates.
. "$MODDIR/prepare-contexts.sh"
if ! prepare_camera_contexts "$MODDIR"; then
  printf '%s\n' 'Could not refresh the camera app mapping. Disable this module and reboot.' > "$MODDIR/context-error.log"
fi

