package com.arcanaforensics.arcalume.data

import android.graphics.Bitmap
import android.graphics.BitmapFactory
import android.graphics.ImageDecoder
import android.os.Build
import androidx.compose.ui.graphics.asImageBitmap
import com.arcanaforensics.arcalume.Brand
import com.arcanaforensics.arcalume.core.Engine
import com.arcanaforensics.arcalume.core.Findings
import com.arcanaforensics.arcalume.core.Ledger
import com.arcanaforensics.arcalume.core.RepairConfig
import com.arcanaforensics.arcalume.core.sha256Hex
import org.opencv.android.Utils
import org.opencv.core.Mat
import org.opencv.imgproc.Imgproc
import java.nio.ByteBuffer
import java.util.concurrent.atomic.AtomicLong

/** Turns acquired bytes into a [Page]. Call off the main thread. */
object Processor {
    private val ids = AtomicLong()

    fun process(name: String, source: Source, original: ByteArray, cfg: RepairConfig, acquiredUtc: String = Ledger.now(), id: Long = ids.incrementAndGet()): Page {
        if (original.size > Brand.MAX_INPUT_BYTES) throw Engine.ImageError("input exceeds the 100 MB limit")
        val full = decode(original)
        val (work, scale) = Engine.workingCopy(full, Brand.WORK_MAX_SIDE)
        val rec = Engine.recover(work, cfg)
        try {
            val nodes = Engine.readingOrder(rec.restored)
            rec.report.readingOrderNodes = nodes.size
            val overlay = Engine.maskOverlay(rec.restored, rec.mask)
            return Page(
                id = id, name = name, source = source, original = original, originalSha256 = sha256Hex(original),
                acquiredUtc = acquiredUtc, cfg = cfg, report = rec.report, nodes = nodes,
                findings = Findings.of(rec.report, nodes.size), scale = scale, workWidth = work.cols(), workHeight = work.rows(),
                restoredPng = Engine.encodePng(rec.restored), maskPng = Engine.encodePng(rec.mask),
                previewOriginal = preview(work), previewRestored = preview(rec.restored), previewOverlay = preview(overlay).also { overlay.release() },
            )
        } finally {
            rec.release()
            if (work !== full) work.release()
            full.release()
        }
    }

    /** Re-run recovery with new settings, keeping the page's identity and acquisition time. */
    fun reprocess(page: Page, cfg: RepairConfig): Page = process(page.name, page.source, page.original, cfg, page.acquiredUtc, page.id)

    /**
     * PNG, JPEG, TIFF, BMP and WebP go through OpenCV (which applies the camera's EXIF
     * rotation). Anything else Android can read, such as HEIC from newer cameras, is
     * decoded by the platform. Either way [original] itself is never altered.
     */
    fun decode(original: ByteArray): Mat {
        if (Engine.isSupported(original)) return Engine.decode(original)
        val bmp = platformDecode(original) ?: throw Engine.ImageError("unsupported or damaged image")
        val rgba = Mat()
        Utils.bitmapToMat(bmp, rgba)
        bmp.recycle()
        val bgr = Mat()
        Imgproc.cvtColor(rgba, bgr, Imgproc.COLOR_RGBA2BGR)
        rgba.release()
        return Engine.checkSize(bgr)
    }

    private fun platformDecode(bytes: ByteArray): Bitmap? = try {
        if (Build.VERSION.SDK_INT >= 28) {
            ImageDecoder.decodeBitmap(ImageDecoder.createSource(ByteBuffer.wrap(bytes))) { d, info, _ ->
                d.allocator = ImageDecoder.ALLOCATOR_SOFTWARE
                val px = info.size.width.toLong() * info.size.height
                if (px > Engine.MAX_PIXELS) {
                    val s = Math.sqrt(Engine.MAX_PIXELS.toDouble() / px)
                    d.setTargetSize((info.size.width * s).toInt(), (info.size.height * s).toInt())
                }
            }.let { if (it.config == Bitmap.Config.ARGB_8888) it else it.copy(Bitmap.Config.ARGB_8888, false) }
        } else {
            BitmapFactory.decodeByteArray(bytes, 0, bytes.size, BitmapFactory.Options().apply { inPreferredConfig = Bitmap.Config.ARGB_8888 })
        }
    } catch (e: Exception) {
        null
    }

    private fun preview(bgr: Mat) = toBitmap(Engine.fit(bgr, Brand.PREVIEW_MAX_SIDE, Brand.PREVIEW_MAX_SIDE), release = true).asImageBitmap()

    fun toBitmap(bgr: Mat, release: Boolean = false): Bitmap {
        val rgba = Mat()
        Imgproc.cvtColor(bgr, rgba, Imgproc.COLOR_BGR2RGBA)
        if (release) bgr.release()
        val bmp = Bitmap.createBitmap(rgba.cols(), rgba.rows(), Bitmap.Config.ARGB_8888)
        Utils.matToBitmap(rgba, bmp)
        rgba.release()
        return bmp
    }

    /** The PNG to save for "Save recovered copy": watermarked on the free plan. */
    fun exportPng(page: Page, watermark: Boolean): ByteArray {
        if (!watermark) return page.restoredPng
        val img = Engine.decode(page.restoredPng)
        val wm = Engine.watermark(img, "Arcalume Free")
        img.release()
        return Engine.encodePng(wm).also { wm.release() }
    }
}
