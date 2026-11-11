"""Apply the current cupid-development application-side native fixups to thor."""
from pathlib import Path
import hashlib
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools/python'))
import lief


LIBRARIES = (
    'libcamera_algoup_jni.xiaomi.so',
    'libcamera_mianode_jni.xiaomi.so',
    'libmicampostproc_client.so',
    'vendor.xiaomi.hardware.campostproc@1.0.so',
)


def patch(source: Path, destination: Path):
    destination.mkdir(parents=True, exist_ok=True)
    report = []
    for name in LIBRARIES:
        raw = (source / name).read_bytes()
        if not raw.startswith(b'\x7fELF\x02\x01'):
            raise ValueError(f'Not an ELF64 little-endian library: {name}')
        if name == 'libcamera_algoup_jni.xiaomi.so':
            old, new = bytes.fromhex('08 ad 40 f9'), bytes.fromhex('08 a9 40 f9')
            if raw.count(old) != 1:
                raise ValueError('Unexpected JNI vtable instruction; refuse unbounded replacement')
            raw = raw.replace(old, new, 1)
        elf = lief.ELF.parse(list(raw))
        if elf.header.machine_type != lief.ELF.ARCH.AARCH64:
            raise ValueError(f'Not AArch64: {name}')
        if name.startswith(('libcamera_algoup_', 'libcamera_mianode_')):
            elf.add_library('libgui_shim_miuicamera.so')
        if name == 'libmicampostproc_client.so':
            if not elf.has_library('libhidltransport.so'):
                raise ValueError('Unexpected post-processing client input')
            elf.remove_library('libhidltransport.so')
        target = destination / name
        elf.write(str(target))
        check = lief.ELF.parse(str(target))
        if name.startswith(('libcamera_algoup_', 'libcamera_mianode_')):
            assert check.has_library('libgui_shim_miuicamera.so')
        if name == 'libmicampostproc_client.so':
            assert not check.has_library('libhidltransport.so')
        report.append({'file': name, 'input_sha256': hashlib.sha256((source/name).read_bytes()).hexdigest(),
                       'output_sha256': hashlib.sha256(target.read_bytes()).hexdigest(), 'needed': check.libraries})
    return report


if __name__ == '__main__':
    import argparse, json
    parser = argparse.ArgumentParser()
    parser.add_argument('source', type=Path)
    parser.add_argument('destination', type=Path)
    args = parser.parse_args()
    print(json.dumps(patch(args.source, args.destination), indent=2))

