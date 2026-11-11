"""Build an EXPERIMENTAL module, only from a complete, identified stock APK."""
from pathlib import Path
import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time
import xml.etree.ElementTree as ET
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools/python'))
sys.path.insert(0, str(ROOT / 'scripts'))
from patch_native import patch as patch_native
from patch_smali import patch as patch_smali
from patch_icon import build_icon, patch_resource_names, ICON_FILES
from patch_vendor_camera import patch as patch_vendor_camera, copy_mis_plugin
from patch_zoom_map import build_bridge


def run(*arguments):
    subprocess.run([str(arg) for arg in arguments], check=True, cwd=ROOT)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def is_signature(name):
    upper = name.upper()
    return upper == 'META-INF/MANIFEST.MF' or (upper.startswith('META-INF/') and upper.endswith(('.RSA', '.DSA', '.EC', '.SF')))


def input_apk(explicit, source):
    if explicit or (ROOT / 'inputs/MiuiCamera.apk').is_file():
        apk = explicit.resolve() if explicit else ROOT / 'inputs/MiuiCamera.apk'
    else:
        raise FileNotFoundError('Missing complete inputs/MiuiCamera.apk from thor OS3.0.6.0')
    if not zipfile.is_zipfile(apk):
        raise ValueError('Camera APK is truncated or is not a ZIP/APK')
    if digest(apk) != source['input_apk_sha256']:
        raise ValueError('APK does not match the complete local OS3.0.6.0 stock input')
    with zipfile.ZipFile(apk) as archive:
        bad = archive.testzip()
        if bad:
            raise ValueError(f'APK CRC check failed: {bad}')
        for required in ('AndroidManifest.xml', 'resources.arsc'):
            if required not in archive.namelist():
                raise ValueError(f'Missing APK member: {required}')
        actual = {name: hashlib.sha256(archive.read(name)).hexdigest()
                  for name in archive.namelist() if name.startswith('classes') and name.endswith('.dex')}
        if actual != source['dex_sha256']:
            raise ValueError('This APK does not match the identified thor OS3.0.6.0 code. Re-audit before patching.')
    return apk


def build(args):
    source = json.loads((ROOT / 'sources.json').read_text(encoding='utf-8'))
    # Fail before creating an installable artifact if any input is incomplete.
    apk = input_apk(args.apk, source)
    for name, expected in source['native_sha256'].items():
        if digest(ROOT / 'inputs' / name) != expected:
            raise ValueError(f'Unexpected native input: {name}')
    sdk_tools = args.sdk / 'build-tools' / args.build_tools
    llvm = args.ndk / 'toolchains/llvm/prebuilt/windows-x86_64/bin'
    required = [ROOT / 'tools/apktool-cli.jar', sdk_tools / 'zipalign.exe',
                sdk_tools / 'apksigner.bat', llvm / 'clang.exe']
    for tool in required:
        if not tool.is_file():
            raise ValueError(f'Missing build tool: {tool}')
    stamp = time.strftime('%Y%m%d-%H%M%S', time.gmtime())
    work = ROOT / 'work' / ('build-' + stamp)
    work.mkdir(parents=True, exist_ok=False)
    dex = work / 'dex'
    dex.mkdir()
    smali = work / 'smali'
    jar = ROOT / 'tools/apktool-cli.jar'

    # Inspect the real binary manifest without rebuilding resources.
    # Feed only the original binary manifest/resource table to avoid copying
    # thousands of unrelated assets merely to inspect declarations.
    manifest_input = work/'manifest-input.apk'
    with zipfile.ZipFile(apk) as original, zipfile.ZipFile(manifest_input, 'w') as inspection:
        for name in ('AndroidManifest.xml', 'resources.arsc'):
            inspection.writestr(name, original.read(name))
    run('java', '-jar', jar, 'd', '--only-manifest', '--no-src', '-p', work/'framework', '-o', work/'manifest', manifest_input)
    manifest = ET.parse(work/'manifest/AndroidManifest.xml').getroot()
    android = '{http://schemas.android.com/apk/res/android}'
    if manifest.get('package') != 'com.android.camera':
        raise ValueError('Unexpected camera package name')
    shared_uid = manifest.get(android+'sharedUserId', '')
    if shared_uid.startswith('android.'):
        raise ValueError('Stock shared system UID requires its signing key; this module does not bypass signature checks.')
    app = manifest.find('application')
    if app is None:
        raise ValueError('Missing application declaration')
    for library in app.findall('uses-library'):
        if library.get(android+'required', 'true') == 'true' and 'miui' in library.get(android+'name', '').lower():
            raise ValueError('This manifest requires an external MIUI framework library. Add and audit that dependency first.')

    replacements = {}
    for name, folder in (('classes.dex', 'smali'), ('classes2.dex', 'smali_classes2'), ('classes3.dex', 'smali_classes3'), ('classes4.dex', 'smali_classes4')):
        with zipfile.ZipFile(apk) as archive:
            (dex/name).write_bytes(archive.read(name))
        run('java', '-cp', jar, 'com.android.tools.smali.baksmali.Main', 'disassemble', dex/name,
            '-o', smali/folder, '--jobs', '4')
    modified = patch_smali(smali)
    build_bridge(ROOT, args.sdk, args.build_tools, work, smali)
    for name, folder in (('classes.dex', 'smali'), ('classes2.dex', 'smali_classes2'), ('classes3.dex', 'smali_classes3'), ('classes4.dex', 'smali_classes4'), ('classes7.dex', 'smali_classes7')):
        target = dex / ('patched-' + name)
        run('java', '-cp', jar, 'com.android.tools.smali.smali.Main', 'assemble', smali/folder,
            '-o', target, '--jobs', '4')
        replacements[name] = target
    unsigned = work / 'camera-unsigned.apk'
    icon_xml = build_icon(ROOT, args.sdk, work)
    # Preserve every stock asset and binary manifest. Old APK signatures are replaced below.
    with zipfile.ZipFile(apk) as original, zipfile.ZipFile(unsigned, 'w') as rebuilt:
        for entry in original.infolist():
            if is_signature(entry.filename):
                continue
            data = replacements[entry.filename].read_bytes() if entry.filename in replacements else original.read(entry)
            if entry.filename == 'resources.arsc':
                data = patch_resource_names(data)
            elif entry.filename in ICON_FILES:
                entry.filename = entry.filename.replace('.png', '.xml')
                data = icon_xml
            rebuilt.writestr(entry, data)
        rebuilt.write(replacements['classes7.dex'], 'classes7.dex')
    aligned = work / 'camera-aligned.apk'
    run(sdk_tools/'zipalign.exe', '-P', '16', '-f', '4', unsigned, aligned)
    key = ROOT / 'tools/thor-camera-dev.jks'
    if not key.exists():
        run('keytool', '-genkeypair', '-keystore', key, '-storepass', 'android', '-keypass', 'android',
            '-alias', 'thor-camera', '-keyalg', 'RSA', '-keysize', '2048', '-validity', '10000',
            '-dname', 'CN=Thor Camera Development', '-noprompt')
    module = work / 'module'
    shutil.copytree(ROOT/'module', module)
    shutil.copy2(ROOT/'README.md', module/'README.md')
    shutil.copytree(ROOT/'assets', module/'assets')
    destination = module / 'system/priv-app/MiuiCamera/MiuiCamera.apk'
    destination.parent.mkdir(parents=True)
    run(sdk_tools/'apksigner.bat', 'sign', '--ks', key, '--ks-key-alias', 'thor-camera',
        '--ks-pass', 'pass:android', '--key-pass', 'pass:android', '--min-sdk-version', '26',
        '--v1-signing-enabled', 'true', '--v2-signing-enabled', 'true', '--v4-signing-enabled', 'false', '--out', destination, aligned)
    run(sdk_tools/'apksigner.bat', 'verify', '--verbose', destination)
    run(sdk_tools/'zipalign.exe', '-c', '-P', '16', '4', destination)
    overlay = ROOT/'inputs/MiuiCameraOverlayLeicaed.apk'
    if digest(overlay) != source['leica_overlay_sha256']:
        raise ValueError('Unexpected Leica resource overlay')
    overlay_aligned = work/'leica-aligned.apk'
    run(sdk_tools/'zipalign.exe', '-f', '4', overlay, overlay_aligned)
    overlay_output = module/'system/product/overlay/MiuiCameraOverlayLeicaed/MiuiCameraOverlayLeicaed.apk'
    overlay_output.parent.mkdir(parents=True)
    run(sdk_tools/'apksigner.bat', 'sign', '--ks', key, '--ks-key-alias', 'thor-camera',
        '--ks-pass', 'pass:android', '--key-pass', 'pass:android', '--v4-signing-enabled', 'false', '--out', overlay_output, overlay_aligned)
    run(sdk_tools/'apksigner.bat', 'verify', overlay_output)
    native_dir = module/'system/lib64'
    native_report = patch_native(ROOT/'inputs', native_dir)
    vendor_camera_report = patch_vendor_camera(ROOT/'inputs/camera.qcom.so',
        module/'system/vendor/lib64/hw/camera.qcom.so')
    vendor_camera_android16 = patch_vendor_camera(ROOT/'inputs/crdroid-16-20260530/camera.qcom.so',
        module/'compat/android16/camera.qcom.so', profile='android16')
    copy_mis_plugin(ROOT/'inputs/libmis_plugin_vidhance.so',
        module/'system/vendor/lib64/libmis_plugin_vidhance.so')
    run(llvm/'clang.exe', '--target=aarch64-linux-android35', '-shared', '-nostdlib',
        '-Wl,-soname,libgui_shim_miuicamera.so', '-Wl,-z,max-page-size=16384',
        ROOT/'native/libgui_shim_miuicamera.c', '-o', native_dir/'libgui_shim_miuicamera.so')
    report = {'status': 'EXPERIMENTAL_UNTESTED_ON_DEVICE', 'sources': source,
              'input_apk_sha256': digest(apk), 'output_apk_sha256': digest(destination),
              'modified_smali': modified, 'native': native_report,
              'vendor_camera': vendor_camera_report,
              'vendor_camera_android16': vendor_camera_android16,
              'icon_source': source['launcher_icon'],
              'validation': ['APK CRC and exact stock DEX identities', 'smali assembled',
                             'APK signature verified', '16 KiB native alignment checked'],
              'not_validated': ['Android installation and app launch', 'SELinux runtime policy',
                                'all camera hardware and image quality', 'Magisk/KernelSU boot mounting']}
    (module/'build-report.json').write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
    for xml in module.rglob('*.xml'):
        ET.parse(xml)
    checksum_lines = []
    for path in sorted(module.rglob('*')):
        if path.is_file():
            checksum_lines.append(f'{digest(path)}  {path.relative_to(module).as_posix()}')
    (module/'SHA256SUMS').write_text('\n'.join(checksum_lines)+'\n', encoding='utf-8', newline='\n')
    output = ROOT/'dist'/f'thor-miuicamera-android16-17-0.1.6-EXPERIMENTAL-{stamp}.zip'
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_suffix('.zip.tmp')
    with zipfile.ZipFile(temporary, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
        for path in sorted(module.rglob('*')):
            if path.is_file():
                info = zipfile.ZipInfo.from_file(path, path.relative_to(module).as_posix())
                info.external_attr = (0o100755 if path.suffix == '.sh' else 0o100644) << 16
                info.compress_type = zipfile.ZIP_DEFLATED
                archive.writestr(info, path.read_bytes())
    with zipfile.ZipFile(temporary) as archive:
        if archive.testzip():
            raise ValueError('Module ZIP CRC failed')
    temporary.replace(output)
    print(f'EXPERIMENTAL / NOT HARDWARE TESTED: {output}')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    sdk = Path(os.environ.get('ANDROID_HOME', Path.home()/'AppData/Local/Android/Sdk'))
    parser.add_argument('--apk', type=Path, help='Complete original thor OS3.0.6.0 camera APK')
    parser.add_argument('--sdk', type=Path, default=sdk)
    parser.add_argument('--build-tools', default='36.0.0')
    parser.add_argument('--ndk', type=Path, default=sdk/'ndk/28.2.13676358')
    try:
        build(parser.parse_args())
    except (ValueError, FileNotFoundError, zipfile.BadZipFile, subprocess.CalledProcessError) as error:
        print(f'BUILD STOPPED: {error}', file=sys.stderr)
        sys.exit(1)

