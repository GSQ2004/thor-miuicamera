"""Map the audited thor HALs to their Android 16/17 ISPv3 driver ABI."""
from pathlib import Path
import hashlib

STOCK_SHA256 = '26ad8ccef40638c48cd595f1bc3ed835d0b5e754d8d173ef8b374c566396ba07'
DRIVER_SHA256 = '6ce5312377c01802a1e271a2e9b499783dfb751e590618ed1609f2f422f55a2f'
MIS_PLUGIN_SHA256 = 'ecaaa236be8608a53b3939fbe4dc8a9569774bd7c308ffc4439531ef3aa8a454'
PROFILES = {
    'android17': {'input_sha256': STOCK_SHA256, 'driver_sha256': DRIVER_SHA256},
    'android16': {
        'input_sha256': '4ffa7ed9ddc1a5e48b4ec91d2b4f6ad3233d02d80c1edfb6b4c71d98ae919256',
        'driver_sha256': '93818c52e0f15f123a339157ee82d30586403056a0bb0532d2b7fe7ab32fe6f9',
    },
}
PATCHES = (
    (0xe1abf0, 0x52800123, 0x52800163),  # mov w3, 9 -> 11
    (0xe1ad48, 0x52800143, 0x52800183),  # mov w3, 10 -> 12
    (0xe1b078, 0x52800123, 0x52800163),  # mov w3, 9 -> 11
)


def patch(source: Path, destination: Path, profile='android17'):
    identity = PROFILES[profile]
    raw = source.read_bytes()
    if hashlib.sha256(raw).hexdigest() != identity['input_sha256']:
        raise ValueError('Unexpected vendor camera HAL; refuse opcode patch')
    data = bytearray(raw)
    for offset, old, new in PATCHES:
        if int.from_bytes(data[offset:offset+4], 'little') != old:
            raise ValueError(f'Unexpected ISPv3 power instruction at {offset:#x}')
        data[offset:offset+4] = new.to_bytes(4, 'little')
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(data)
    return {'profile': profile, 'input_sha256': identity['input_sha256'], 'output_sha256': hashlib.sha256(data).hexdigest(),
            'required_camera_driver_sha256': identity['driver_sha256'],
            'patched_offsets': [hex(p[0]) for p in PATCHES]}


def copy_mis_plugin(source: Path, destination: Path):
    data = source.read_bytes()
    if hashlib.sha256(data).hexdigest() != MIS_PLUGIN_SHA256:
        raise ValueError('Unexpected thor Vidhance stabilization plugin')
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(data)
