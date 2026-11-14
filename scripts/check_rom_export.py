"""Verify ROM export isolation, target HAL preservation, and opt-in HAL selection."""
from pathlib import Path
import io
import tempfile
import zipfile
from export_rom import COMMON, HALS, export, sha


def main():
    with tempfile.TemporaryDirectory(prefix='thor-rom-export-') as temporary:
        base = Path(temporary)
        module = base/'module'
        module.mkdir()
        names = COMMON + list(filter(None, HALS.values())) + ['system/vendor/lib64/libmis_plugin_vidhance.so',
                'sepolicy.camera.template', 'system.prop']
        for name in names:
            path = module/name
            path.parent.mkdir(parents=True, exist_ok=True)
            if name.endswith('.apk'):
                with zipfile.ZipFile(path, 'w') as apk:
                    apk.writestr('AndroidManifest.xml', b'fixture-manifest')
            else:
                path.write_text('platform_app_36 fixture '+name, newline='\n')
        (module/'SHA256SUMS').write_text(''.join(sha((module/n).read_bytes())+'  '+n+'\n'
                                               for n in names), newline='\n')
        rom = base/'rom'
        report = export(module, rom, 'custom_camera_app', 'vendor/test/camera')
        assert report['rom_allowlist'] is None and report['android_api_allowlist'] is None
        assert not report['root_required'] and report['preserves_target_hal']
        assert not (rom/'proprietary/system/vendor').exists()
        assert not any(p.name in ('customize.sh', 'post-fs-data.sh', 'module.prop', 'ksu-mount-guard') for p in rom.rglob('*'))
        assert 'domain=custom_camera_app' in (rom/'sepolicy/seapp_contexts').read_text()
        assert 'platform_app_36' not in (rom/'sepolicy/thor_camera.te').read_text()
        assert 'TARGET_COPY_OUT_SYSTEM' in (rom/'product.mk').read_text()
        assert not any('.apk:' in line or '.so:' in line for line in (rom/'product.mk').read_text().splitlines())
        for name in COMMON:
            assert (rom/'proprietary'/name).read_bytes() == (module/name).read_bytes()
        print('PASS: no ROM/API/root gates; target HAL preserved; target domain; payload unchanged')
        for profile, source in HALS.items():
            if source is None:
                continue
            out = base/profile
            export(module, out, 'platform_app', 'vendor/test/camera', profile)
            assert (out/'proprietary/system/vendor/lib64/hw/camera.qcom.so').read_bytes() == (module/source).read_bytes()
            assert (out/'proprietary/system/vendor/lib64/libmis_plugin_vidhance.so').is_file()
        print('PASS: Android 16/17 HAL and stabilization plugin exported only by explicit choice')
        for args in [(module, rom, 'platform_app', 'vendor/test/camera'),
                     (module, base/'bad', 'x;allow all', 'vendor/test/camera'),
                     (module, base/'escape', 'platform_app', 'vendor/../escape')]:
            try:
                export(*args)
                raise AssertionError('invalid export accepted')
            except (ValueError, FileExistsError):
                pass
        (module/COMMON[0]).write_bytes(b'corrupt')
        try:
            export(module, base/'corrupt', 'platform_app', 'vendor/test/camera')
            raise AssertionError('corrupt payload accepted')
        except ValueError:
            assert not (base/'corrupt').exists()
        print('PASS: existing outputs, invalid parameters and corruption rejected before output')


if __name__ == '__main__':
    main()
