"""Version-specific thor OS3.0.6.0 camera changes; reject unexpected input."""
from pathlib import Path
import re
from patch_zoom_map import patch as patch_zoom_map


def replace_once(text, old, new):
    if text.count(old) != 1:
        raise ValueError(f'Expected exactly one anchor: {old[:100]!r}')
    return text.replace(old, new, 1)


def patch(root: Path):
    changes = []
    capture = root / 'smali_classes4/com/xiaomi/protocol/ICustomCaptureResult.smali'
    text = capture.read_text(encoding='utf-8')
    signature = '.method public static toTotalCaptureResult(Lcom/xiaomi/protocol/ICustomCaptureResult;IZ)Landroid/hardware/camera2/TotalCaptureResult;'
    start = text.index(signature)
    end = text.index('.end method', start)
    method = text[start:end]
    # Add four local registers. Keep all parameter accesses expressed as pN.
    method = replace_once(method, '    .registers 25', '    .registers 29')
    method = replace_once(method, '    const/16 v0, 0xb', '    const/16 v0, 0xd')
    method = replace_once(method,
        '    aput-object v19, v7, v20',
        '    aput-object v19, v7, v20\n\n'
        '    # Android 14+: hasReadoutTimestamp, readoutTimestamp\n'
        '    const/16 v22, 0xb\n'
        '    const/16 v23, 0xc\n'
        '    sget-object v19, Ljava/lang/Boolean;->TYPE:Ljava/lang/Class;\n'
        '    aput-object v19, v7, v22\n'
        '    sget-object v19, Ljava/lang/Long;->TYPE:Ljava/lang/Class;\n'
        '    aput-object v19, v7, v23')
    # At this point all eleven original constructor arguments have been stored.
    constructor_call = re.search(
        r'    invoke-virtual \{(v\d+), (v\d+)\}, Ljava/lang/reflect/Constructor;->newInstance\(\[Ljava/lang/Object;\)Ljava/lang/Object;', method)
    if not constructor_call or constructor_call.group(2) != 'v0':
        raise ValueError('Unexpected CaptureResultExtras constructor invocation')
    # There is a separate legacy-SDK invocation later in this method.
    # Only the first invocation belongs to the eleven-argument SDK>=30 path.
    method = method[:constructor_call.start()] + (
        '    invoke-static {v2}, Ljava/lang/Boolean;->valueOf(Z)Ljava/lang/Boolean;\n'
        '    move-result-object v19\n'
        '    aput-object v19, v0, v22\n'
        '    const-wide/16 v24, 0x0\n'
        '    invoke-static/range {v24 .. v25}, Ljava/lang/Long;->valueOf(J)Ljava/lang/Long;\n'
        '    move-result-object v19\n'
        '    aput-object v19, v0, v23\n\n') + method[constructor_call.start():]
    capture.write_text(text[:start] + method + text[end:], encoding='utf-8', newline='\n')
    changes.append(str(capture.relative_to(root)))

    # Use the app's global permission path rather than MIUI Security Center.
    region = root / 'smali_classes3/ic/c.smali'
    text = region.read_text(encoding='utf-8')
    pattern = (r'    const-string v0, "ro\.product\.mod_device"\s+'
               r'invoke-static \{v0, v1\}, Lzj/g;->b\(Ljava/lang/String;Ljava/lang/String;\)Ljava/lang/String;\s+'
               r'move-result-object v0\s+const-string v1, "_global"\s+'
               r'invoke-virtual \{v0, v1\}, Ljava/lang/String;->contains\(Ljava/lang/CharSequence;\)Z\s+'
               r'move-result v0')
    text, count = re.subn(pattern, '    const/4 v0, 0x1', text)
    if count != 1:
        raise ValueError('Unexpected thor global permission check')
    region.write_text(text, encoding='utf-8', newline='\n')
    changes.append(str(region.relative_to(root)))

    gallery = root / 'smali/a0/k5.smali'
    text = gallery.read_text(encoding='utf-8')
    if text.count('com.android.camera.action.REVIEW') != 2:
        raise ValueError('Unexpected gallery review implementation')
    text = text.replace('com.android.camera.action.REVIEW', 'android.provider.action.REVIEW')
    text = replace_once(text, 'com.android.camera.action.SPILIT_SCREEN_REVIEW', 'android.provider.action.REVIEW')
    # Keep the constants/register lifetimes intact and remove only package pinning.
    for register in ('p2',):
        for package in ('com.miui.gallery', 'com.google.android.apps.photos'):
            pattern = (r'(    const-string ' + register + r', "' + re.escape(package) + r'"\s+)'
                       r'invoke-virtual \{v1, ' + register + r'\}, Landroid/content/Intent;->setPackage\(Ljava/lang/String;\)Landroid/content/Intent;')
            text, count = re.subn(pattern, r'\1# Use the installed gallery resolver.', text)
            if count != 1:
                raise ValueError(f'Unexpected gallery package binding: {package}')
    gallery.write_text(text, encoding='utf-8', newline='\n')
    changes.append(str(gallery.relative_to(root)))

    changes.extend(patch_zoom_map(root))
    return changes


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('root', type=Path)
    args = parser.parse_args()
    for path in patch(args.root):
        print(path)

