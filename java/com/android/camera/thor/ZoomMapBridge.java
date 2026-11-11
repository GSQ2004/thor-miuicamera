package com.android.camera.thor;

import android.graphics.ImageFormat;
import android.hardware.HardwareBuffer;
import android.media.Image;
import android.media.ImageReader;
import android.media.ImageWriter;
import android.os.Handler;
import android.util.Log;
import android.util.Size;
import android.view.Surface;

/** Transfers camera buffers to the original zoom-map SurfaceTexture without CPU conversion. */
public final class ZoomMapBridge implements ImageReader.OnImageAvailableListener {
    private final ImageReader reader;
    private final ImageWriter writer;
    private boolean closed;
    private int frames;

    public ZoomMapBridge(Surface textureSurface, Size size, Handler handler) {
        writer = ImageWriter.newInstance(textureSurface, 3, ImageFormat.PRIVATE);
        try {
            // Legacy GRALLOC_USAGE_RENDERSCRIPT prevents flexible-consumer size
            // rounding without classifying this GPU stream as a video encoder.
            // Runtime coverage is recorded per audited Android 16/17 profile.
            reader = ImageReader.newInstance(size.getWidth(), size.getHeight(),
                    ImageFormat.PRIVATE, 4,
                    HardwareBuffer.USAGE_GPU_SAMPLED_IMAGE | 0x100000L);
        } catch (RuntimeException error) {
            writer.close();
            throw error;
        }
        reader.setOnImageAvailableListener(this, handler);
        Log.i("ThorZoomMap", "Bridge created: " + size);
    }

    public Surface getSurface() {
        return reader.getSurface();
    }

    @Override
    public synchronized void onImageAvailable(ImageReader source) {
        if (closed) return;
        Image image = null;
        try {
            image = source.acquireLatestImage();
            if (image == null) return;
            writer.queueInputImage(image);
            image = null;
            if (++frames == 1) Log.i("ThorZoomMap", "First buffer forwarded");
        } catch (RuntimeException error) {
            Log.e("ThorZoomMap", "Buffer transfer failed", error);
        } finally {
            if (image != null) image.close();
        }
    }

    public synchronized void close() {
        if (closed) return;
        closed = true;
        reader.setOnImageAvailableListener(null, null);
        reader.close();
        writer.close();
        Log.i("ThorZoomMap", "Bridge closed after " + frames + " buffers");
    }
}
