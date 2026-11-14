"""Export a completed camera payload for direct ROM builds, without installer gates."""
from pathlib import Path, PurePosixPath
import argparse
import hashlib
import json
import re
import zipfile

ROOT = Path(__file__).resolve().parents[1]
HALS = {'rom': None, 'android16-crdroid1210': 'compat/android16/camera.qcom.so',
        'android17-lineage24': 'system/vendor/lib64/hw/camera.qcom.so'}
COMMON = [
    'system/priv-app/MiuiCamera/MiuiCamera.apk',
    'system/product/overlay/MiuiCameraOverlayLeicaed/MiuiCameraOverlayLeicaed.apk',
    'system/etc/public.libraries-xiaomi.txt',
    'system/etc/permissions/privapp-permissions-thor-miuicamera.xml',
    'system/etc/sysconfig/thor-miuicamera-hiddenapi.xml',
    'system/product/etc/device_features/thor.xml',
] + ['system/lib64/'+name for name in (
    'libcamera_algoup_jni.xiaomi.so', 'libcamera_mianode_jni.xiaomi.so',
    'libgui_shim_miuicamera.so', 'libmicampostproc_client.so',
    'vendor.xiaomi.hardware.campostproc@1.0.so')]


def sha(data):
    return hashlib.sha256(data).hexdigest()


def export(module: Path, output: Path, app_domain: str, tree_path: str, hal_profile='rom'):
    if not re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]*', app_domain):
        raise ValueError('Invalid SELinux domain')
    if not re.fullmatch(r'(?:device|vendor)/[A-Za-z0-9_./-]+', tree_path) or '..' in PurePosixPath(tree_path).parts:
        raise ValueError('Use a ROM-relative device/... or vendor/... tree path')
    if hal_profile not in HALS:
        raise ValueError('Unknown explicit HAL profile')
    if output.exists():
        raise FileExistsError('Output already exists; use a new directory to preserve previous exports')
    payload = COMMON.copy()
    if HALS[hal_profile]:
        payload += [HALS[hal_profile], 'system/vendor/lib64/libmis_plugin_vidhance.so']
    # Check integrity, not the host's Android/ROM/driver identity. Nothing here accesses ADB.
    manifest = {}
    for line in (module/'SHA256SUMS').read_text(encoding='utf-8').splitlines():
        digest, name = line.split('  ', 1)
        if not re.fullmatch('[0-9a-f]{64}', digest) or name in manifest:
            raise ValueError('Invalid checksum manifest')
        manifest[name] = digest
    data = {}
    for name in payload + ['sepolicy.camera.template', 'system.prop']:
        blob = (module/name).read_bytes()
        if manifest.get(name) != sha(blob):
            raise ValueError('Payload checksum mismatch: '+name)
        if name.endswith('.apk'):
            import io
            with zipfile.ZipFile(io.BytesIO(blob)) as apk:
                if apk.testzip() or 'AndroidManifest.xml' not in apk.namelist():
                    raise ValueError('Incomplete APK: '+name)
        data[name] = blob
    output.mkdir(parents=True)
    mapping = {}
    for name in payload:
        destination = 'system/vendor/lib64/hw/camera.qcom.so' if name == HALS[hal_profile] else name
        relative = 'proprietary/'+destination
        path = output/relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data[name])
        mapping[destination] = relative

    def write(name, content):
        path = output/name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding='utf-8', newline='\n')

    # Soong imports keep certificates intact; system permissions stay with the system app.
    modules = ['ThorMiuiCamera', 'ThorMiuiCameraLeicaOverlay']
    bp = '''// Generated ROM integration. No ROM-name, SDK or root-manager gates.
android_app_import {
    name: "ThorMiuiCamera",
    apk: "proprietary/system/priv-app/MiuiCamera/MiuiCamera.apk",
    filename: "MiuiCamera.apk",
    privileged: true,
    preprocessed: true,
    dex_preopt: { enabled: false },
}
android_app_import {
    name: "ThorMiuiCameraLeicaOverlay",
    apk: "proprietary/system/product/overlay/MiuiCameraOverlayLeicaed/MiuiCameraOverlayLeicaed.apk",
    product_specific: true,
    preprocessed: true,
    dex_preopt: { enabled: false },
}
'''
    copies = []
    for destination, source in sorted(mapping.items()):
        if destination.endswith('.apk'):
            continue
        if destination.endswith('.so'):
            stem = PurePosixPath(destination).name[:-3]
            name = 'ThorCamera_'+re.sub(r'[^A-Za-z0-9_]', '_', stem)
            modules.append(name)
            vendor = destination.startswith('system/vendor/')
            extra = '    vendor: true,\n' if vendor else ''
            if destination.endswith('/hw/camera.qcom.so'):
                extra += '    relative_install_path: "hw",\n'
            # Blobs retain private ABI dependencies; ROM maintainers audit these on target.
            bp += ('cc_prebuilt_library_shared {\n'+f'    name: "{name}",\n    stem: "{stem}",\n'
                   +f'    srcs: ["{source}"],\n'+extra+
                   '    compile_multilib: "64",\n    strip: { none: true },\n'
                   '    check_elf_files: false,\n    stl: "none",\n    system_shared_libs: [],\n}\n')
        else:
            if destination.startswith('system/product/'):
                target = '$(TARGET_COPY_OUT_PRODUCT)/'+destination.removeprefix('system/product/')
            else:
                target = '$(TARGET_COPY_OUT_SYSTEM)/'+destination.removeprefix('system/')
            copies.append(f'    {tree_path}/{source}:{target}')
    write('Android.bp', bp)
    write('product.mk', '# Include with inherit-product from your device product.\nPRODUCT_PACKAGES += \\\n    '
          +' \\\n    '.join(modules)+'\n\nPRODUCT_COPY_FILES += \\\n'+' \\\n'.join(copies)+'\n\n'
          '# Merge these properties with existing device properties; avoid duplicate definitions.\n'
          '# See README.md for persist.vendor.camera.privapp.list (preserve existing entries).\n')
    write('BoardConfig.mk', '# Include from the device BoardConfig after reviewing target policy types.\n'
          f'BOARD_VENDOR_SEPOLICY_DIRS += {tree_path}/sepolicy\n')
    policy = data['sepolicy.camera.template'].decode('utf-8').replace('platform_app_36', app_domain)
    write('sepolicy/thor_camera.te', policy)
    write('sepolicy/seapp_contexts', 'user=_app seinfo=default isPrivApp=true name=com.android.camera '
          f'domain={app_domain} type=app_data_file levelFrom=user\n')
    write('properties.example', data['system.prop'].decode('utf-8')+
          '\n# Append com.android.camera to the target ROM existing value; do not remove other packages.\n'
          '# persist.vendor.camera.privapp.list=<existing>,com.android.camera\n')
    for name in ['NOTICE.md', 'LICENSES/Apache-2.0.txt']:
        source = ROOT/name
        if not source.is_file():
            source = ROOT/'publish/thor-miuicamera'/name
        if source.is_file():
            write(name, source.read_text(encoding='utf-8'))
    write('README.md', (ROOT/'rom-integration/README.md').read_text(encoding='utf-8'))
    report = {'format': 1, 'rom_allowlist': None, 'android_api_allowlist': None,
              'root_required': False, 'target_hardware': 'thor / arm64',
              'tree_path': tree_path, 'app_domain': app_domain, 'hal_profile': hal_profile,
              'preserves_target_hal': hal_profile == 'rom',
              'validation': 'export integrity checked; target ROM build and hardware test pending',
              'payload_sha256': {name: sha((output/path).read_bytes()) for name, path in mapping.items()}}
    write('integration-report.json', json.dumps(report, indent=2)+'\n')
    write('SHA256SUMS', ''.join(sha(path.read_bytes())+'  '+path.relative_to(output).as_posix()+'\n'
                              for path in sorted(output.rglob('*')) if path.is_file()))
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--module', required=True, type=Path, help='Completed, uninstalled module staging directory')
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--app-domain', required=True, help='Existing target ROM app domain, e.g. platform_app')
    parser.add_argument('--tree-path', default='vendor/xiaomi/thor-miuicamera')
    parser.add_argument('--hal-profile', choices=list(HALS), default='rom')
    args = parser.parse_args()
    try:
        result = export(args.module, args.output, args.app_domain, args.tree_path, args.hal_profile)
        print(json.dumps(result, indent=2))
    except (OSError, ValueError, zipfile.BadZipFile) as error:
        parser.exit(1, f'ROM export failed: {error}\n')
