#!/system/bin/sh
set -eu
. "$1"
driver16=93818c52e0f15f123a339157ee82d30586403056a0bb0532d2b7fe7ab32fe6f9
driver17=6ce5312377c01802a1e271a2e9b499783dfb751e590618ed1609f2f422f55a2f
stock16=4ffa7ed9ddc1a5e48b4ec91d2b4f6ad3233d02d80c1edfb6b4c71d98ae919256
patched16=900dfb00f26dfce1a83e65b6a7839e4a0baa7f841c8d9f36aafdc2d795750b46
stock17=26ad8ccef40638c48cd595f1bc3ed835d0b5e754d8d173ef8b374c566396ba07
patched17=240610b0bcb05d0d8d39d799fa1fc27dde8dbf1ede38fb87baa9f834ae5dbebc
gui16=c230c5ea6b9e5868a1d36d928ccd21cf20e206391af1dc71e96e10fbe4514c3e
accept() {
  expected=$1
  shift
  select_camera_profile "$@" || { echo "FAIL expected acceptance: $*"; exit 1; }
  [ "$camera_profile" = "$expected" ] || exit 1
  echo "PASS accepted $expected ($3)"
}
reject() {
  if select_camera_profile "$@"; then echo "FAIL expected rejection: $*"; exit 1; fi
  [ -n "$camera_profile_error" ] || exit 1
  echo "PASS rejected $1/$2: $camera_profile_error"
}
accept android16-crdroid1210 36 "$driver16" "$stock16" "$gui16"
accept android16-crdroid1210 36 "$driver16" "$patched16" "$gui16"
accept android17-lineage24 37 "$driver17" "$stock17" ''
accept android17-lineage24 37 "$driver17" "$patched17" ''
reject 35 "$driver16" "$stock16" "$gui16"
reject 36 "$driver17" "$stock16" "$gui16"
reject 36 "$driver16" "$stock17" "$gui16"
reject 36 "$driver16" "$stock16" bad-libgui
reject 37 unknown-driver "$stock17" ''
