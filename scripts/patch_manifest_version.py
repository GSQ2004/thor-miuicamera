"""Update only the typed Android versionCode integer in a binary manifest."""
import struct


def patch_version_code(raw: bytes, expected: int, version: int) -> bytes:
    if not 0 < version < 0x80000000 or version <= expected:
        raise ValueError('Output APK versionCode must increase')
    if len(raw) < 8 or struct.unpack_from('<H', raw)[0] != 0x0003:
        raise ValueError('Expected binary Android XML')
    result = bytearray(raw)
    offset = struct.unpack_from('<H', raw, 2)[0]
    resources = []
    matches = []
    while offset < len(raw):
        kind, header_size, size = struct.unpack_from('<HHI', raw, offset)
        if size < header_size or header_size < 8 or offset + size > len(raw):
            raise ValueError('Invalid binary XML chunk')
        if kind == 0x0180:
            count = (size - header_size) // 4
            resources = list(struct.unpack_from('<'+'I'*count, raw, offset+header_size))
        elif kind == 0x0102:
            if header_size != 16 or size < 36:
                raise ValueError('Unexpected binary XML element')
            ext = offset + header_size
            attribute_start, attribute_size, count = struct.unpack_from('<HHH', raw, ext+8)
            if attribute_size < 20:
                raise ValueError('Unexpected attribute format')
            for index in range(count):
                attr = ext + attribute_start + index * attribute_size
                if attr + 20 > offset + size:
                    raise ValueError('Truncated attribute')
                name = struct.unpack_from('<I', raw, attr+4)[0]
                if name < len(resources) and resources[name] == 0x0101021b:
                    raw_value = struct.unpack_from('<I', raw, attr+8)[0]
                    value_size, reserved, value_type, value = struct.unpack_from('<HBBI', raw, attr+12)
                    if raw_value != 0xffffffff or value_size != 8 or reserved or value_type != 0x10 or value != expected:
                        raise ValueError('Unexpected versionCode attribute; refuse patch')
                    matches.append(attr+16)
        offset += size
    if offset != len(raw) or len(matches) != 1:
        raise ValueError('Expected exactly one versionCode attribute')
    struct.pack_into('<I', result, matches[0], version)
    return bytes(result)
