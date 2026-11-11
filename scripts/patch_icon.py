"""Compile the unmodified official Leica logo paths as an Android vector icon."""
from pathlib import Path
import hashlib
import subprocess
import xml.etree.ElementTree as ET
import zipfile

ICON_FILES = ('res/O9k.png', 'res/fB5.png', 'res/HAL.png')
SVG_SHA256 = '5edc10c74a9acbf97c18e7de2d9d332fd0d2ffb0936eea32baf20b7c653815b4'


def build_icon(root: Path, sdk: Path, work: Path) -> bytes:
    source = root/'inputs/leica-logo-official.svg'
    if hashlib.sha256(source.read_bytes()).hexdigest() != SVG_SHA256:
        raise ValueError('Unexpected official Leica logo input')
    svg = ET.parse(source).getroot()
    if svg.get('viewBox') != '0 0 200 200':
        raise ValueError('Unexpected Leica logo view box')
    paths = svg.findall('./{http://www.w3.org/2000/svg}g/{http://www.w3.org/2000/svg}path')
    if len(paths) != 2 or paths[0].get('fill') != '#E20612' or paths[1].get('fill') != 'white':
        raise ValueError('Unexpected Leica logo paths')
    android = 'http://schemas.android.com/apk/res/android'
    ET.register_namespace('android', android)
    vector = ET.Element('vector', {
        '{'+android+'}width': '108dp', '{'+android+'}height': '108dp',
        '{'+android+'}viewportWidth': '200', '{'+android+'}viewportHeight': '200'})
    for path in paths:
        ET.SubElement(vector, 'path', {'{'+android+'}fillColor':
            '#FFFFFF' if path.get('fill') == 'white' else path.get('fill'),
            '{'+android+'}pathData': path.get('d')})
    stage = work/'leica-icon'
    (stage/'res/drawable').mkdir(parents=True, exist_ok=True)
    ET.ElementTree(vector).write(stage/'res/drawable/leica_icon.xml', encoding='utf-8', xml_declaration=True)
    (stage/'AndroidManifest.xml').write_text(
        '<manifest xmlns:android="http://schemas.android.com/apk/res/android" package="local.thor.icon">'
        '<uses-sdk android:minSdkVersion="26"/><application android:hasCode="false"/></manifest>', encoding='utf8')
    aapt = sdk/'build-tools/36.0.0/aapt2.exe'
    subprocess.run([str(aapt), 'compile', '--dir', str(stage/'res'), '-o', str(stage/'compiled.zip')], check=True)
    subprocess.run([str(aapt), 'link', '-I', str(sdk/'platforms/android-37.0/android.jar'),
        '--manifest', str(stage/'AndroidManifest.xml'), '-o', str(stage/'icon.apk'), str(stage/'compiled.zip')], check=True)
    with zipfile.ZipFile(stage/'icon.apk') as archive:
        return archive.read('res/drawable/leica_icon.xml')


def patch_resource_names(table: bytes) -> bytes:
    for name in ICON_FILES:
        old = name.encode('ascii')
        if table.count(old) != 1:
            raise ValueError(f'Unexpected launcher resource path: {name}')
        # Equal byte length preserves the compiled resource string pool offsets.
        table = table.replace(old, name.replace('.png', '.xml').encode('ascii'), 1)
    return table
