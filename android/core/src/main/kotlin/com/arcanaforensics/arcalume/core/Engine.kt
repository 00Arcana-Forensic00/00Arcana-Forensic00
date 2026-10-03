package com.arcanaforensics.arcalume.core

import org.opencv.core.Core
import org.opencv.core.CvType
import org.opencv.core.Mat
import org.opencv.core.MatOfByte
import org.opencv.core.MatOfPoint
import org.opencv.core.Rect
import org.opencv.core.Scalar
import org.opencv.core.Size
import org.opencv.imgcodecs.Imgcodecs
import org.opencv.imgproc.Imgproc
import org.opencv.photo.Photo

/**
 * The document recovery engine, a line-by-line port of the desktop engine
 * (restore/src/arcana_restore/imaging.py) onto OpenCV's Java API:
 *
 * 1. Illumination flattening: divide each channel by a smooth background estimate,
 *    so shadowed or dimmed text that still holds signal comes back.
 * 2. Glare halo stretch: restore ink contrast in the ring around each glare core.
 * 3. Telea inpainting of clipped glare cores only. Those pixels held no data; the fill
 *    does not bring back characters, and every filled pixel is in the mask.
 *
 * Pure-black regions are reported and left alone unless [RepairConfig.fillShadow] is
 * set, because they are often redactions, figures or scanner-lid shadows.
 *
 * Works on 8-bit BGR [Mat]s. The caller loads the native library (OpenCVLoader on
 * Android, the openpnp loader in JVM tests). Every Mat it returns is owned by the caller.
 */
object Engine {
    const val MAX_INPUT_BYTES = 100 * 1024 * 1024
    const val MAX_PIXELS = 100_000_000L
    const val MAX_LISTED_REGIONS = 50
    private const val BACKGROUND_WORK_SIDE = 1200.0

    class ImageError(msg: String) : Exception(msg)

    class Recovery(val restored: Mat, val mask: Mat, val report: Report) {
        fun release() { restored.release(); mask.release() }
    }

    private val MAGICS = listOf(
        byteArrayOf(0x89.toByte(), 'P'.code.toByte(), 'N'.code.toByte(), 'G'.code.toByte(), 0x0d, 0x0a, 0x1a, 0x0a),
        byteArrayOf(0xff.toByte(), 0xd8.toByte(), 0xff.toByte()),
        byteArrayOf('B'.code.toByte(), 'M'.code.toByte()),
        byteArrayOf('I'.code.toByte(), 'I'.code.toByte(), '*'.code.toByte(), 0),
        byteArrayOf('M'.code.toByte(), 'M'.code.toByte(), 0, '*'.code.toByte()),
        // WebP: "RIFF....WEBP" is checked separately
    )

    fun isSupported(data: ByteArray): Boolean =
        MAGICS.any { m -> data.size >= m.size && m.indices.all { data[it] == m[it] } } ||
            (data.size >= 12 && String(data, 0, 4, Charsets.US_ASCII) == "RIFF" && String(data, 8, 4, Charsets.US_ASCII) == "WEBP")

    /**
     * Decode to 8-bit BGR. Unlike the desktop, the camera's EXIF orientation is applied,
     * because phone photos are almost always stored rotated.
     */
    fun decode(data: ByteArray): Mat {
        if (data.size > MAX_INPUT_BYTES) throw ImageError("input exceeds the 100 MiB limit")
        if (!isSupported(data)) throw ImageError("unsupported format (expected PNG, JPEG, TIFF, BMP or WebP)")
        val img = MatOfByte(*data).use { Imgcodecs.imdecode(it, Imgcodecs.IMREAD_COLOR) }
        if (img.empty()) throw ImageError("image could not be decoded (corrupt or truncated)")
        return checkSize(img)
    }

    fun checkSize(img: Mat): Mat {
        if (img.rows() < 8 || img.cols() < 8) { img.release(); throw ImageError("image too small") }
        if (img.rows().toLong() * img.cols() > MAX_PIXELS) { img.release(); throw ImageError("image exceeds the 100 megapixel limit") }
        if (img.type() != CvType.CV_8UC3) { img.release(); throw ImageError("unsupported pixel type") }
        return img
    }

    /**
     * Phone photos are scaled down to at most [maxSide] pixels on the long side before
     * recovery, so a 50-megapixel frame does not take minutes. The original is still kept
     * byte-for-byte; the manifest records the scale. Returns the input itself when small enough.
     */
    fun workingCopy(img: Mat, maxSide: Int): Pair<Mat, Double> {
        val s = maxSide.toDouble() / maxOf(img.rows(), img.cols())
        if (s >= 1.0) return img to 1.0
        val out = Mat()
        Imgproc.resize(img, out, Size(maxOf(1.0, Math.rint(img.cols() * s)), maxOf(1.0, Math.rint(img.rows() * s))), 0.0, 0.0, Imgproc.INTER_AREA)
        return out to s
    }

    fun encodePng(img: Mat): ByteArray = MatOfByte().use { buf ->
        if (!Imgcodecs.imencode(".png", img, buf)) throw ImageError("PNG encoding failed")
        buf.toArray()
    }

    // ---- triage ------------------------------------------------------------------

    private fun ellipse(k: Int) = Imgproc.getStructuringElement(Imgproc.MORPH_ELLIPSE, Size(k.toDouble(), k.toDouble()))

    private fun regions(mask: Mat): List<Region> {
        val labels = Mat(); val stats = Mat(); val centroids = Mat()
        val n = Imgproc.connectedComponentsWithStats(mask, labels, stats, centroids, 8, CvType.CV_32S)
        val out = (1 until n).map { i ->
            val s = IntArray(5).also { stats.get(i, 0, it) }
            Region(s[0], s[1], s[2], s[3], s[4])
        }.sortedByDescending { it.area }
        labels.release(); stats.release(); centroids.release()
        return out.take(MAX_LISTED_REGIONS)
    }

    /** numpy's median of an 8-bit image (the mean of the two middle values for an even count). */
    fun median(gray: Mat): Double {
        val hist = LongArray(256)
        val row = ByteArray(gray.cols())
        for (y in 0 until gray.rows()) {
            gray.get(y, 0, row)
            for (b in row) hist[b.toInt() and 0xff]++
        }
        val n = gray.total()
        fun nth(k: Long): Int { var acc = 0L; for (v in 0..255) { acc += hist[v]; if (acc > k) return v }; return 255 }
        return if (n % 2 == 1L) nth(n / 2).toDouble() else (nth(n / 2 - 1) + nth(n / 2)) / 2.0
    }

    class Damage(val glare: Mat, val shadow: Mat, val paperAtClip: Boolean)

    fun damageMasks(img: Mat, cfg: RepairConfig): Damage {
        val gray = Mat().also { Imgproc.cvtColor(img, it, Imgproc.COLOR_BGR2GRAY) }
        val side = minOf(gray.rows(), gray.cols()).toDouble()
        val kg = ReadingOrder.odd(side / 40, 7)
        val ks = ReadingOrder.odd(side / 80, 7)
        val glare = Mat().also { Imgproc.threshold(gray, it, cfg.hi - 1.0, 255.0, Imgproc.THRESH_BINARY) }
        Imgproc.morphologyEx(glare, glare, Imgproc.MORPH_OPEN, ellipse(kg))
        val shadow = Mat().also { Imgproc.threshold(gray, it, cfg.lo.toDouble(), 255.0, Imgproc.THRESH_BINARY_INV) }
        Imgproc.morphologyEx(shadow, shadow, Imgproc.MORPH_OPEN, ellipse(ks))
        val paperAtClip = median(gray) >= cfg.hi
        if (paperAtClip) glare.setTo(Scalar(0.0)) // glare is indistinguishable from clean white paper
        gray.release()
        return Damage(glare, shadow, paperAtClip)
    }

    /** Locate damage. Returns the fill mask (exactly the pixels repair will synthesize) and the report. */
    fun triage(img: Mat, cfg: RepairConfig): Triple<Mat, Report, Mat> {
        val d = damageMasks(img, cfg)
        val fill = d.glare.clone()
        if (cfg.fillShadow) Core.bitwise_or(fill, d.shadow, fill)
        if (Core.countNonZero(fill) > 0) Imgproc.dilate(fill, fill, ellipse(5))
        val report = Report(
            width = img.cols(), height = img.rows(), whitePageDetected = d.paperAtClip,
            glarePixels = Core.countNonZero(d.glare).toLong(), shadowPixels = Core.countNonZero(d.shadow).toLong(),
            glareRegions = regions(d.glare), shadowRegions = regions(d.shadow),
            maskedFraction = Core.countNonZero(fill).toDouble() / d.glare.total(), hi = cfg.hi, lo = cfg.lo,
        )
        d.shadow.release()
        return Triple(fill, report, d.glare)
    }

    // ---- recovery ----------------------------------------------------------------

    private fun background(channel: Mat): Mat {
        val h = channel.rows(); val w = channel.cols()
        val scale = minOf(1.0, BACKGROUND_WORK_SIDE / maxOf(h, w))
        val small = if (scale < 1) Mat().also {
            Imgproc.resize(channel, it, Size(maxOf(1.0, Math.rint(w * scale)), maxOf(1.0, Math.rint(h * scale))), 0.0, 0.0, Imgproc.INTER_AREA)
        } else channel
        val k = ReadingOrder.odd(minOf(small.rows(), small.cols()) / 25.0, 15)
        val bg = Mat()
        Imgproc.morphologyEx(small, bg, Imgproc.MORPH_CLOSE, ellipse(k))
        Imgproc.medianBlur(bg, bg, ReadingOrder.odd(k / 2.0, 5))
        if (scale < 1) {
            small.release()
            Imgproc.resize(bg, bg, Size(w.toDouble(), h.toDouble()), 0.0, 0.0, Imgproc.INTER_LINEAR)
        }
        return bg
    }

    /** Divide each channel by its background so paper becomes uniform and dimmed ink returns. */
    fun flattenIllumination(img: Mat): Mat {
        val chans = ArrayList<Mat>().also { Core.split(img, it) }
        for (i in chans.indices) {
            val ch = chans[i]
            val bg = background(ch)
            Core.max(bg, Scalar(1.0), bg)
            val out = Mat()
            Core.divide(ch, bg, out, 255.0, CvType.CV_8U)
            ch.release(); bg.release()
            chans[i] = out
        }
        return Mat().also { Core.merge(chans, it); chans.forEach(Mat::release) }
    }

    /** Restore contrast in the ring around each glare core; flat (inkless) windows are left alone. */
    fun stretchGlareHalo(img: Mat, glare: Mat, minContrast: Int = 25): Mat {
        if (Core.countNonZero(glare) == 0) return img.clone()
        val side = minOf(img.rows(), img.cols()).toDouble()
        // The ring is every pixel within side/14 of a glare core, found with a Euclidean
        // distance transform in linear time (a dilation that large dominated run time).
        val radius = ReadingOrder.odd(side / 7, 31) / 2
        val notGlare = Mat().also { Core.bitwise_not(glare, it) }
        val dist = Mat().also { Imgproc.distanceTransform(notGlare, it, Imgproc.DIST_L2, Imgproc.DIST_MASK_PRECISE) }
        val halo = Mat().also { Core.compare(dist, Scalar(radius.toDouble()), it, Core.CMP_LE) }
        Core.bitwise_and(halo, notGlare, halo)
        notGlare.release(); dist.release()
        val win = ReadingOrder.odd(side / 16, 15).toDouble()
        val blur = ReadingOrder.odd(side / 32, 9).toDouble()
        val rect = Imgproc.getStructuringElement(Imgproc.MORPH_RECT, Size(win, win))
        val chans = ArrayList<Mat>().also { Core.split(img, it) }
        for (ch in chans) {
            val low = Mat()
            Imgproc.erode(ch, low, rect)
            Imgproc.blur(low, low, Size(blur, blur))
            // (ch - low) * 255 / (255 - low), only where the window holds at least minContrast of range
            val ok = Mat().also { Core.compare(low, Scalar(255.0 - minContrast), it, Core.CMP_LE) }
            Core.bitwise_and(ok, halo, ok)
            val ch32 = Mat().also { ch.convertTo(it, CvType.CV_32F) }
            val low32 = Mat().also { low.convertTo(it, CvType.CV_32F) }
            val num = Mat().also { Core.subtract(ch32, low32, it) }
            val span = Mat().also { Core.subtract(Mat(low32.size(), CvType.CV_32F, Scalar(255.0)), low32, it) }
            Core.max(span, Scalar(1.0), span)
            val st = Mat().also { Core.divide(num, span, it, 255.0) }
            val st8 = Mat().also { st.convertTo(it, CvType.CV_8U) } // saturates to 0..255
            st8.copyTo(ch, ok)
            listOf(low, ok, ch32, low32, num, span, st, st8).forEach(Mat::release)
        }
        halo.release()
        return Mat().also { Core.merge(chans, it); chans.forEach(Mat::release) }
    }

    /** Recover the page and set the report's status and repair steps. */
    fun repair(img: Mat, mask: Mat, glare: Mat, cfg: RepairConfig, report: Report): Mat {
        val steps = report.steps
        val hasMask = Core.countNonZero(mask) > 0
        if (!cfg.repair) {
            report.status = if (hasMask || report.shadowPixels > 0) Report.Status.DETECTED_NOT_REPAIRED else Report.Status.STABLE
            return img.clone()
        }
        if (report.maskedFraction > cfg.maxMaskedFraction) {
            report.status = Report.Status.SKIPPED_DAMAGE_TOO_EXTENSIVE
            return img.clone()
        }
        var out = img.clone()
        fun replace(next: Mat) { out.release(); out = next }
        if (cfg.flatten) { replace(flattenIllumination(out)); steps.illuminationFlattened = true }
        if (Core.countNonZero(glare) > 0) { replace(stretchGlareHalo(out, glare)); steps.glareHaloStretched = true }
        if (hasMask) {
            replace(Mat().also { Photo.inpaint(out, mask, it, cfg.inpaintRadius.toDouble(), Photo.INPAINT_TELEA) })
            steps.inpaintedPixels = Core.countNonZero(mask).toLong()
            steps.inpaintMethod = "telea"
            steps.shadowFilled = cfg.fillShadow && report.shadowPixels > 0
        }
        report.status = when {
            steps.inpaintedPixels > 0 -> Report.Status.REPAIRED
            differs(out, img) -> Report.Status.ENHANCED
            else -> Report.Status.STABLE
        }
        return out
    }

    private fun differs(a: Mat, b: Mat): Boolean {
        val d = Mat().also { Core.absdiff(a, b, it) }
        val s = Core.sumElems(d).`val`.sum()
        d.release()
        return s > 0
    }

    /** Triage and repair in one call. */
    fun recover(img: Mat, cfg: RepairConfig = RepairConfig()): Recovery {
        val (mask, report, glare) = triage(img, cfg)
        val restored = repair(img, mask, glare, cfg, report)
        glare.release()
        return Recovery(restored, mask, report)
    }

    // ---- reading order -------------------------------------------------------------

    fun binarize(gray: Mat): Mat {
        val bin = Mat()
        Imgproc.threshold(gray, bin, 0.0, 255.0, Imgproc.THRESH_BINARY_INV + Imgproc.THRESH_OTSU)
        if (Core.countNonZero(bin) > bin.total() / 2) Core.bitwise_not(bin, bin)
        return bin
    }

    /** Detect text and figure blocks and order them with XY-cut (geometry, not understanding). */
    fun readingOrder(img: Mat): List<Node> {
        val gray = Mat().also { Imgproc.cvtColor(img, it, Imgproc.COLOR_BGR2GRAY) }
        val binary = binarize(gray)
        gray.release()
        val h = binary.rows(); val w = binary.cols()
        val kern = Imgproc.getStructuringElement(Imgproc.MORPH_RECT,
            Size(ReadingOrder.odd(w / 100.0, 9).toDouble(), ReadingOrder.odd(h / 400.0, 3).toDouble()))
        val dil = Mat().also { Imgproc.dilate(binary, it, kern) }
        val contours = ArrayList<MatOfPoint>()
        val hier = Mat()
        Imgproc.findContours(dil, contours, hier, Imgproc.RETR_EXTERNAL, Imgproc.CHAIN_APPROX_SIMPLE)
        dil.release(); hier.release()
        val minArea = maxOf(16L, h.toLong() * w / 200_000)
        val boxes = contours.map { c -> Imgproc.boundingRect(c).also { c.release() } }
            .map { Box(it.x, it.y, it.width, it.height) }
            .filter { it.w.toLong() * it.h >= minArea }
            .sortedByDescending { it.w.toLong() * it.h }
            .take(ReadingOrder.MAX_NODES)
        val nodes = ReadingOrder.xyCut(boxes, ReadingOrder.odd(w / 100.0, 9)).mapIndexed { i, b ->
            val roi = binary.submat(Rect(b.x, b.y, b.w, b.h))
            val density = Core.countNonZero(roi).toDouble() / (b.w * b.h)
            roi.release()
            Node(i, b, density)
        }
        binary.release()
        return nodes
    }

    // ---- presentation --------------------------------------------------------------

    /** Scale down (never up) to fit inside max width and height. */
    fun fit(img: Mat, maxW: Int, maxH: Int): Mat {
        val s = minOf(maxW.toDouble() / img.cols(), maxH.toDouble() / img.rows(), 1.0)
        if (s >= 1.0) return img.clone()
        return Mat().also { Imgproc.resize(img, it, Size(maxOf(1, (img.cols() * s).toInt()).toDouble(), maxOf(1, (img.rows() * s).toInt()).toDouble()), 0.0, 0.0, Imgproc.INTER_AREA) }
    }

    /** Diagonal repeated text across the image, for free-tier exports (same look as the desktop). */
    fun watermark(img: Mat, text: String): Mat {
        val h = img.rows(); val w = img.cols()
        val layer = Mat.zeros(h, w, CvType.CV_8U)
        val scale = maxOf(0.6, minOf(h, w) / 700.0)
        val thick = maxOf(1, (scale * 2).toInt())
        val base = IntArray(1)
        val ts = Imgproc.getTextSize(text, Imgproc.FONT_HERSHEY_SIMPLEX, scale, thick, base)
        val tw = ts.width.toInt(); val th = ts.height.toInt()
        val stepX = tw + (80 * scale).toInt(); val stepY = th + (140 * scale).toInt()
        var row = 0
        var y = th
        while (y < h + stepY) {
            var x = -tw + (row % 2) * stepX / 2
            while (x < w) {
                Imgproc.putText(layer, text, org.opencv.core.Point(x.toDouble(), y.toDouble()), Imgproc.FONT_HERSHEY_SIMPLEX, scale, Scalar(255.0), thick, Imgproc.LINE_AA)
                x += stepX
            }
            y += stepY; row++
        }
        val alpha = Mat().also { layer.convertTo(it, CvType.CV_32F, 0.35 / 255.0) }
        layer.release()
        val chans = ArrayList<Mat>().also { Core.split(img, it) }
        val color = doubleArrayOf(60.0, 60.0, 200.0)
        for (i in chans.indices) {
            val c32 = Mat().also { chans[i].convertTo(it, CvType.CV_32F) }
            val inv = Mat().also { Core.subtract(Mat(alpha.size(), CvType.CV_32F, Scalar(1.0)), alpha, it) }
            Core.multiply(c32, inv, c32)
            Core.scaleAdd(alpha, color[i], c32, c32)
            chans[i].release()
            chans[i] = Mat().also { c32.convertTo(it, CvType.CV_8U) }
            c32.release(); inv.release()
        }
        alpha.release()
        return Mat().also { Core.merge(chans, it); chans.forEach(Mat::release) }
    }

    /** Hatch synthesized pixels in magenta (a pattern, not colour alone). */
    fun maskOverlay(img: Mat, mask: Mat): Mat {
        val out = img.clone()
        val stripe = Mat(mask.size(), CvType.CV_8U)
        val row = ByteArray(mask.cols())
        for (y in 0 until mask.rows()) {
            for (x in row.indices) row[x] = if (((x + y) / 4) % 2 == 0) 0xff.toByte() else 0
            stripe.put(y, 0, row)
        }
        val magenta = Mat(img.size(), img.type(), Scalar(255.0, 0.0, 255.0))
        for ((sel, a) in listOf(Pair(true, 0.85), Pair(false, 0.35))) {
            val m = Mat()
            if (sel) Core.bitwise_and(mask, stripe, m) else { Core.bitwise_not(stripe, m); Core.bitwise_and(mask, m, m) }
            val blend = Mat().also { Core.addWeighted(out, 1 - a, magenta, a, 0.0, it) }
            blend.copyTo(out, m)
            m.release(); blend.release()
        }
        stripe.release(); magenta.release()
        return out
    }
}

private inline fun <T> MatOfByte.use(block: (MatOfByte) -> T): T = try { block(this) } finally { release() }
