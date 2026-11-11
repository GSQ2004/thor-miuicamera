"""Package a prepared module with a freshly generated payload checksum manifest."""
from pathlib import Path
import argparse
import hashlib
import zipfile


def package(module: Path, output: Path):
    files = sorted(p for p in module.rglob('*') if p.is_file() and p.name != 'SHA256SUMS')
    (module/'SHA256SUMS').write_text(''.join(
        hashlib.sha256(p.read_bytes()).hexdigest()+'  '+p.relative_to(module).as_posix()+'\n'
        for p in files), encoding='utf-8', newline='\n')
    temporary = output.with_suffix('.zip.tmp')
    with zipfile.ZipFile(temporary, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
        for path in sorted(module.rglob('*')):
            if path.is_file():
                entry = zipfile.ZipInfo.from_file(path, path.relative_to(module).as_posix())
                entry.external_attr = (0o100755 if path.suffix == '.sh' else 0o100644) << 16
                entry.compress_type = zipfile.ZIP_DEFLATED
                archive.writestr(entry, path.read_bytes())
    with zipfile.ZipFile(temporary) as archive:
        if archive.testzip():
            raise ValueError('Module ZIP CRC failed')
    temporary.replace(output)
    checksum = hashlib.sha256(output.read_bytes()).hexdigest()
    output.with_suffix('.zip.sha256').write_text(checksum+'  '+output.name+'\n', encoding='ascii', newline='\n')
    print(output, output.stat().st_size, checksum)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('module', type=Path)
    parser.add_argument('output', type=Path)
    arguments = parser.parse_args()
    package(arguments.module, arguments.output)
