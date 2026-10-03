package com.arcanaforensics.arcalume.core

import org.opencv.core.Core
import org.opencv.core.Mat
import org.opencv.imgcodecs.Imgcodecs
import java.io.File
import java.nio.file.Files
import kotlin.test.Test
import kotlin.test.assertContentEquals
import kotlin.test.assertEquals
import kotlin.test.assertFailsWith
import kotlin.test.assertFalse
import kotlin.test.assertTrue

/**
 * The ported engine against the desktop engine's own outputs (android/tools/make_fixtures.py).
 * Damage detection is exact: same masks, regions, pixel counts and status. The restored
 * pixels may differ by rounding (the desktop truncates floats, OpenCV rounds), so they are
 * compared with a tight tolerance.
 */
class EngineTest {
    companion object { init { nu.pattern.OpenCV.loadLocally() } }

    private fun read(name: String): Mat = Imgcodecs.imread(Fixtures.file(name).path, Imgcodecs.IMREAD_UNCHANGED)
    private fun cfgOf(s: Json.Obj) = RepairConfig(
        flatten = s["flatten"] == Json.Bool(true), fillShadow = s["fill_shadow"] == Json.Bool(true), repair = s["repair"] == Json.Bool(true))

    private fun diff(a: Mat, b: Mat): Pair<Double, Double> {
        val d = Mat().also { Core.absdiff(a, b, it) }
        val mean = Core.mean(d).`val`.take(3).average()
        val max = Core.minMaxLoc(d.reshape(1)).maxVal
        return mean to max
    }

    @Test fun `matches the desktop engine on every fixture`() {
        for (c in Fixtures.engine["cases"]!!.arr().map { it.obj() }) {
            val name = c["name"]!!.str()
            val img = read("$name.input.png")
            val rec = Engine.recover(img, cfgOf(c["settings"]!!.obj()))
            val want = c["report"]!!.obj()
            val got = rec.report.toJson()
            for (k in listOf("width", "height", "white_page_detected", "glare_pixels", "shadow_pixels", "glare_regions",
                "shadow_regions", "masked_fraction", "thresholds", "status", "repair")) {
                assertEquals(want[k]!!.canonical(), got[k]!!.canonical(), "$name: $k")
            }
            val mask = read("$name.mask.png")
            assertEquals(0, Core.countNonZero(Mat().also { Core.absdiff(mask, rec.mask, it) }), "$name: mask")
            val (mean, max) = diff(read("$name.restored.png"), rec.restored)
            assertTrue(mean < 0.75, "$name: mean pixel difference $mean")
            assertTrue(max <= 64, "$name: max pixel difference $max")
            val nodes = Engine.readingOrder(rec.restored)
            val wantNodes = c["reading_order"]!!.arr().size
            assertTrue(kotlin.math.abs(nodes.size - wantNodes) <= maxOf(2, wantNodes / 10), "$name: ${nodes.size} blocks vs $wantNodes")
            rec.release()
        }
    }

    @Test fun `reading order reads the left column before the right`() {
        val c = Fixtures.engine["cases"]!!.arr().map { it.obj() }.first { it["name"]!!.str() == "bars_page" }
        val nodes = Engine.readingOrder(read("bars_page.restored.png"))
        // (Flattening lightens the solid heading bar, which counts as background at that size.)
        val xs = nodes.filter { it.box.y > 100 }.map { it.box.x }
        val firstRight = xs.indexOfFirst { it > 300 }
        assertTrue(firstRight > 0 && xs.drop(firstRight).all { it > 300 }, "whole left column, then the right: $xs")
        val want = c["reading_order"]!!.arr().map { it.obj() }.map { Box(it["x"]!!.long().toInt(), it["y"]!!.long().toInt(), it["w"]!!.long().toInt(), it["h"]!!.long().toInt()) }
        assertEquals(want, nodes.map { it.box })
    }

    @Test fun `xy cut matches the desktop on hand-made boxes`() {
        // Title, then two columns whose rows interleave.
        val boxes = listOf(Box(10, 0, 500, 20), Box(10, 40, 200, 10), Box(300, 45, 200, 10), Box(10, 60, 200, 10), Box(300, 65, 200, 10))
        assertEquals(listOf(0, 1, 3, 2, 4).map { boxes[it] }, ReadingOrder.xyCut(boxes.shuffled(kotlin.random.Random(1)), 9))
        assertEquals(1001, ReadingOrder.xyCut(List(1001) { Box(0, it * 2, 5, 1) }).size)
        assertEquals(9, ReadingOrder.odd(8.5, 3)) // round half to even, then odd
        assertEquals(11, ReadingOrder.odd(9.5, 3))
    }

    @Test fun `decode refuses what it cannot safely read`() {
        assertFailsWith<Engine.ImageError> { Engine.decode("GIF89a....".toByteArray()) }
        assertFailsWith<Engine.ImageError> { Engine.decode(byteArrayOf(0xff.toByte(), 0xd8.toByte(), 0xff.toByte(), 0, 1, 2)) }
        val tiny = Engine.encodePng(Mat(4, 4, org.opencv.core.CvType.CV_8UC3))
        assertFailsWith<Engine.ImageError> { Engine.decode(tiny) }
        val img = Engine.decode(Fixtures.file("bars_page.input.png").readBytes())
        assertEquals(800 to 600, img.cols() to img.rows())
    }

    @Test fun `seals a page the desktop can open, and opens it again`() {
        val original = Fixtures.file("bars_page.input.png").readBytes()
        val img = Engine.decode(original)
        val cfg = RepairConfig()
        val rec = Engine.recover(img, cfg)
        val nodes = Engine.readingOrder(rec.restored)
        rec.report.readingOrderNodes = nodes.size
        val restored = Engine.encodePng(rec.restored)
        val mask = Engine.encodePng(rec.mask)
        val man = Evidence.manifest("Arcalume for Android 0.1.0", "2026-09-30T12:00:00+00:00", "Receipt – März.png",
            original, restored, mask, rec.report, nodes, cfg)
        val dir = Fixtures.interopOut ?: Files.createTempDirectory("arcalume-seal").toFile()
        dir.listFiles()?.forEach { it.delete() }
        val pw = Fixtures.desktop["passphrase"]!!.str()
        val sealed = Evidence.seal(dir, "Receipt – März.png", original, restored, mask, man, rec.report, pw, Fixtures.FAST_KDF)
        assertTrue(Regex("evidence-${sha256Hex(original).take(16)}-[0-9a-f]{6}\\.arcr").matches(sealed.vault.name), sealed.vault.name)
        assertFalse("rz" in File(dir, Evidence.LEDGER_NAME).readText(), "no source name in the log")
        val (m2, entries) = Evidence.open(sealed.vault.readBytes(), pw)
        assertContentEquals(original, entries.getValue("original"))
        assertEquals("repaired", m2["report"]!!.obj()["status"]!!.str())
        val led = Ledger(File(dir, Evidence.LEDGER_NAME)).verify(sealed.ledgerEntry["hash"]!!.str())
        assertTrue(led.ok && led.entries == 1, led.message)
        File(dir, "expect.json").writeText(Json.obj("passphrase" to pw, "head" to led.head, "vault" to sealed.vault.name,
            "original_sha256" to sha256Hex(original)).canonical())
        // tampering with a sealed entry is caught by the manifest hashes even with the right passphrase
        val swapped = Vault.seal(linkedMapOf("manifest" to man.canonicalBytes(), "original" to original + 0, "restored" to restored, "mask" to mask), pw, Fixtures.FAST_KDF)
        assertFailsWith<Vault.VaultError> { Evidence.open(swapped, pw) }
        rec.release()
    }

    @Test fun `findings use the desktop wording`() {
        val c = Fixtures.engine["cases"]!!.arr().map { it.obj() }.first { it["name"]!!.str() == "bars_page" }
        val rec = Engine.recover(read("bars_page.input.png"))
        val f = Findings.of(rec.report, 25)
        assertEquals(listOf(Finding.Level.OK, Finding.Level.WARN, Finding.Level.INFO, Finding.Level.INFO), f.map { it.level })
        assertTrue(f[1].text.startsWith("1 glare spot found. Faded text around it was restored. The blown-out centre (${Findings.pct(c["report"]!!.obj()["masked_fraction"]!!.let { (it as Json.Num).double })} of the page)"))
        assertEquals("under 0.1%", Findings.pct(0.0004))
        val wm = Engine.watermark(rec.restored, "Arcalume Free")
        assertTrue(diff(wm, rec.restored).first > 0.5)
        val ov = Engine.maskOverlay(rec.restored, rec.mask)
        assertTrue(diff(ov, rec.restored).second > 100)
    }
}
