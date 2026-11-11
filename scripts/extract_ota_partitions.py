"""Extract selected full-OTA partitions and verify manifest hashes (no flashing)."""
from pathlib import Path
import argparse
import bz2
import hashlib
import json
import lzma
import struct
import zipfile


def varint(data, pos):
    value = shift = 0
    while pos < len(data) and shift < 70:
        byte = data[pos]
        pos += 1
        value |= (byte & 127) << shift
        if byte < 128:
            return value, pos
        shift += 7
    raise ValueError('Invalid protobuf varint')


def fields(data):
    result = {}
    pos = 0
    while pos < len(data):
        tag, pos = varint(data, pos)
        number, wire = tag >> 3, tag & 7
        if wire == 0:
            value, pos = varint(data, pos)
        elif wire == 2:
            length, pos = varint(data, pos)
            value = data[pos:pos+length]
            if len(value) != length:
                raise ValueError('Truncated protobuf field')
            pos += length
        elif wire in (1, 5):
            length = 8 if wire == 1 else 4
            value = data[pos:pos+length]
            pos += length
        else:
            raise ValueError(f'Unsupported protobuf wire type {wire}')
        result.setdefault(number, []).append(value)
    return result


def digest(path):
    with path.open('rb') as source:
        return hashlib.file_digest(source, 'sha256').hexdigest()


def extract(archive, output, names):
    # Schema: LineageOS/android_system_update_engine, update_metadata.proto.
    with zipfile.ZipFile(archive) as ota:
        entry = ota.getinfo('payload.bin')
        if entry.compress_type != zipfile.ZIP_STORED:
            raise ValueError('Seekable ZIP_STORED payload required')
        with archive.open('rb') as source:
            source.seek(entry.header_offset)
            header = source.read(30)
            name_len, extra_len = struct.unpack_from('<HH', header, 26)
            payload = entry.header_offset + 30 + name_len + extra_len
            source.seek(payload)
            magic, major, manifest_size, signature_size = struct.unpack('>4sQQI', source.read(24))
            if magic != b'CrAU' or major != 2:
                raise ValueError('Only OTA payload version 2 is supported')
            manifest = fields(source.read(manifest_size))
            if manifest.get(12, [0])[0] != 0:
                raise ValueError('Incremental OTA is not supported')
            block = manifest.get(3, [4096])[0]
            blobs = payload + 24 + manifest_size + signature_size
            output.mkdir(parents=True, exist_ok=True)
            results = {}
            for raw in manifest[13]:
                part = fields(raw)
                name = part[1][0].decode('ascii')
                if name not in names:
                    continue
                info = fields(part[7][0])
                size, expected = info[1][0], info[2][0].hex()
                destination = output / (name + '.img')
                if destination.is_file() and destination.stat().st_size == size and digest(destination) == expected:
                    results[name] = {'size': size, 'sha256': expected, 'verified': True, 'reused': True}
                    print(name, 'existing image verified', flush=True)
                    continue
                temporary = destination.with_suffix('.img.partial')
                with temporary.open('wb') as target:
                    target.truncate(size)
                    for raw_op in part[8]:
                        op = fields(raw_op)
                        kind = op[1][0]
                        if kind in (6, 7):
                            continue  # A fresh sparse file already contains zeros.
                        if kind not in (0, 1, 8):
                            raise ValueError(f'{name}: unsupported operation {kind}')
                        source.seek(blobs + op.get(2, [0])[0])
                        data = source.read(op[3][0])
                        if 8 in op and hashlib.sha256(data).digest() != op[8][0]:
                            raise ValueError(f'{name}: operation hash mismatch')
                        if kind == 1:
                            data = bz2.decompress(data)
                        elif kind == 8:
                            data = lzma.decompress(data)
                        used = 0
                        for raw_extent in op[6]:
                            extent = fields(raw_extent)
                            count = extent[2][0] * block
                            target.seek(extent[1][0] * block)
                            target.write(data[used:used+count])
                            used += count
                        if used != len(data):
                            raise ValueError(f'{name}: extent/data length mismatch')
                actual = digest(temporary)
                if actual != expected:
                    raise ValueError(f'{name}: partition hash mismatch {actual}')
                temporary.replace(destination)
                results[name] = {'size': size, 'sha256': actual, 'verified': True, 'reused': False}
                print(name, 'extracted and verified', flush=True)
            if set(results) != set(names):
                raise ValueError('Some requested partitions were absent')
            (output/'partition-verification.json').write_text(json.dumps(results, indent=2)+'\n', encoding='utf-8')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('archive', type=Path)
    parser.add_argument('output', type=Path)
    parser.add_argument('partitions', nargs='+')
    args = parser.parse_args()
    extract(args.archive, args.output, args.partitions)
