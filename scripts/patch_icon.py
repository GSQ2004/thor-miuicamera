"""Compile the project's user-approved white adaptive camera launcher icon."""
from pathlib import Path
import hashlib
import json
import subprocess
import xml.etree.ElementTree as ET
import zipfile

ICON_FILES = ('res/O9k.png', 'res/fB5.png', 'res/HAL.png')


def build_icon(root: Path, sdk: Path, work: Path) -> bytes:
    source = root/'assets/camera-icon.xml'
    identity = json.loads((root/'sources.json').read_text(encoding='utf-8'))
    if hashlib.sha256(source.read_bytes()).hexdigest() != identity['launcher_icon']['sha256']:
        raise ValueError('Unexpected project camera icon input')
    icon = ET.parse(source).getroot()
    if icon.tag != 'adaptive-icon' or {c.tag for c in icon} != {'background', 'foreground'}:
        raise ValueError('Expected an adaptive icon with background and foreground')
    stage = work/'camera-icon'
    (stage/'res/drawable').mkdir(parents=True, exist_ok=True)
    (stage/'res/drawable/camera_icon.xml').write_bytes(source.read_bytes())
    (stage/'AndroidManifest.xml').write_text(
        '<manifest xmlns:android="http://schemas.android.com/apk/res/android" package="local.thor.icon">'
        '<uses-sdk android:minSdkVersion="26"/><application android:hasCode="false"/></manifest>', encoding='utf8')
    aapt = sdk/'build-tools/36.0.0/aapt2.exe'
    subprocess.run([str(aapt), 'compile', '--dir', str(stage/'res'), '-o', str(stage/'compiled.zip')], check=True)
    subprocess.run([str(aapt), 'link', '-I', str(sdk/'platforms/android-37.0/android.jar'),
        '--manifest', str(stage/'AndroidManifest.xml'), '-o', str(stage/'icon.apk'), str(stage/'compiled.zip')], check=True)
    with zipfile.ZipFile(stage/'icon.apk') as archive:
        return archive.read('res/drawable/camera_icon.xml')


def patch_resource_names(table: bytes) -> bytes:
    for name in ICON_FILES:
        old = name.encode('ascii')
        if table.count(old) != 1:
            raise ValueError(f'Unexpected launcher resource path: {name}')
        # Equal byte length preserves the compiled resource string pool offsets.
        table = table.replace(old, name.replace('.png', '.xml').encode('ascii'), 1)
    return table
