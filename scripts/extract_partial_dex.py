"""Inspect complete DEX members in a partially downloaded stock APK (never package it)."""
from pathlib import Path
import struct
import zlib

data = Path('inputs/MiuiCamera.partial.apk').read_bytes()
out = Path('work/dex')
out.mkdir(parents=True, exist_ok=True)
offset = 0
while data[offset:offset + 4] == b'PK\x03\x04':
    _, flags, method, _, _, crc, packed, size, name_len, extra_len = struct.unpack_from('<HHHHHIIIHH', data, offset + 4)
    if flags & 8:
        raise RuntimeError('Unexpected data descriptor')
    name = data[offset + 30:offset + 30 + name_len].decode()
    start = offset + 30 + name_len + extra_len
    end = start + packed
    if end > len(data):
        break
    if name.startswith('classes') and name.endswith('.dex'):
        value = data[start:end]
        if method == 8:
            value = zlib.decompress(value, -15)
        elif method != 0:
            raise RuntimeError(f'Unexpected compression {method}')
        assert len(value) == size and zlib.crc32(value) == crc, name
        (out / name).write_bytes(value)
        print(name, size)
    offset = end
