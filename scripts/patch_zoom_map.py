"""Keep thor's auxiliary surface size while retaining the stock zoom-map renderer."""
from pathlib import Path
import shutil
import subprocess


def patch(root: Path):
    zoom = root / 'smali_classes2/ba/h.smali'
    text = zoom.read_text(encoding='utf-8')
    anchor = '# instance fields'
    assert text.count(anchor) == 1
    text = text.replace(anchor, anchor + '\n.field private thorBridge:Lcom/android/camera/thor/ZoomMapBridge;', 1)
    anchor = '    iput-object v0, p0, Lba/h;->e:Landroid/view/Surface;'
    replacement = anchor + '''
    new-instance v0, Lcom/android/camera/thor/ZoomMapBridge;
    iget-object v2, p0, Lba/h;->e:Landroid/view/Surface;
    iget-object v3, p0, Lba/h;->f:Landroid/util/Size;
    iget-object v4, p0, Lba/h;->v:Landroid/os/Handler;
    invoke-direct {v0, v2, v3, v4}, Lcom/android/camera/thor/ZoomMapBridge;-><init>(Landroid/view/Surface;Landroid/util/Size;Landroid/os/Handler;)V
    iput-object v0, p0, Lba/h;->thorBridge:Lcom/android/camera/thor/ZoomMapBridge;
'''
    assert text.count(anchor) == 1
    text = text.replace(anchor, replacement)
    anchor = '    :cond_7d\n    iget-object p0, p0, Lba/h;->e:Landroid/view/Surface;'
    replacement = '''    :cond_7d
    iget-object p0, p0, Lba/h;->thorBridge:Lcom/android/camera/thor/ZoomMapBridge;
    invoke-virtual {p0}, Lcom/android/camera/thor/ZoomMapBridge;->getSurface()Landroid/view/Surface;
    move-result-object p0'''
    assert text.count(anchor) == 1
    text = text.replace(anchor, replacement)
    anchor = '.method public final d()V\n    .registers 4'
    replacement = anchor + '''
    iget-object v0, p0, Lba/h;->thorBridge:Lcom/android/camera/thor/ZoomMapBridge;
    if-eqz v0, :thor_bridge_closed
    invoke-virtual {v0}, Lcom/android/camera/thor/ZoomMapBridge;->close()V
    const/4 v0, 0x0
    iput-object v0, p0, Lba/h;->thorBridge:Lcom/android/camera/thor/ZoomMapBridge;
    :thor_bridge_closed
'''
    assert text.count(anchor) == 1
    zoom.write_text(text.replace(anchor, replacement), encoding='utf-8', newline='\n')
    # classes2.dex is at the field-ID limit. Put the zoom controller family and
    # the bridge together in classes7.dex; class names remain unchanged.
    extra = root / 'smali_classes7/ba'
    extra.mkdir(parents=True, exist_ok=True)
    changes = []
    for item in sorted(zoom.parent.glob('*.smali')):
        target = extra / item.name
        shutil.move(str(item), str(target))
        changes.append(str(target.relative_to(root)))
    return changes


def build_bridge(project: Path, sdk: Path, build_tools: str, work: Path, smali: Path):
    classes = work / 'zoom-bridge-classes'
    dex = work / 'zoom-bridge-dex'
    classes.mkdir()
    dex.mkdir()
    android = sdk / 'platforms/android-37.0/android.jar'
    source = project / 'java/com/android/camera/thor/ZoomMapBridge.java'
    def run(*args):
        subprocess.run([str(arg) for arg in args], check=True)
    run('javac', '--release', '8', '-Xlint:-options', '-classpath', android, '-d', classes, source)
    run(sdk/'build-tools'/build_tools/'d8.bat', '--min-api', '29', '--lib', android,
        '--output', dex, *sorted(classes.rglob('*.class')))
    run('java', '-cp', project/'tools/apktool-cli.jar',
        'com.android.tools.smali.baksmali.Main', 'disassemble', dex/'classes.dex',
        '-o', smali/'smali_classes7')
