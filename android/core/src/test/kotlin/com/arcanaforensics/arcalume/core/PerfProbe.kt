package com.arcanaforensics.arcalume.core

import org.opencv.core.Mat
import org.opencv.core.Size
import org.opencv.imgcodecs.Imgcodecs
import org.opencv.imgproc.Imgproc
import kotlin.test.Test

class PerfProbe {
    init { nu.pattern.OpenCV.loadLocally() }
    @Test fun probe() {
        if (System.getenv("PERF") == null) return
        val src = Imgcodecs.imread(Fixtures.file("synth_page.input.png").path)
        for (side in listOf(1300, 2400, 4000)) {
            val s = side / 1300.0
            val img = Mat().also { Imgproc.resize(src, it, Size(1000 * s, 1300 * s)) }
            val t = System.nanoTime()
            val r = Engine.recover(img)
            val t2 = System.nanoTime()
            Engine.readingOrder(r.restored)
            println("side=$side recover=${(t2 - t) / 1e6}ms order=${(System.nanoTime() - t2) / 1e6}ms status=${r.report.status}")
        }
    }
}
