package com.arcanaforensics.arcalume.core

/** Recovery settings; the defaults match the desktop engine (imaging.RepairConfig). */
data class RepairConfig(
    val hi: Int = 250,              // pixels >= hi are candidate glare
    val lo: Int = 5,                // pixels <= lo are candidate shadow
    val inpaintRadius: Int = 5,
    val maxMaskedFraction: Double = 0.30,
    val repair: Boolean = true,     // false: triage and report only, pixels untouched
    val flatten: Boolean = true,    // divide out uneven lighting (recovers dimmed text)
    val fillShadow: Boolean = false, // also fill clipped-black regions (may be redactions)
)

data class Region(val x: Int, val y: Int, val w: Int, val h: Int, val area: Int)

data class RepairSteps(
    var illuminationFlattened: Boolean = false,
    var glareHaloStretched: Boolean = false,
    var inpaintedPixels: Long = 0,
    var inpaintMethod: String? = null,
    var shadowFilled: Boolean = false,
)

data class Node(val order: Int, val box: Box, val density: Double)

/** What the engine found and did to one page. [toJson] matches the desktop report keys. */
data class Report(
    val width: Int,
    val height: Int,
    val whitePageDetected: Boolean,
    val glarePixels: Long,
    val shadowPixels: Long,
    val glareRegions: List<Region>,
    val shadowRegions: List<Region>,
    val maskedFraction: Double,
    val hi: Int,
    val lo: Int,
    var status: Status = Status.STABLE,
    val steps: RepairSteps = RepairSteps(),
    var readingOrderNodes: Int? = null,
) {
    enum class Status(val wire: String) {
        STABLE("stable"), ENHANCED("enhanced"), REPAIRED("repaired"),
        DETECTED_NOT_REPAIRED("detected_not_repaired"), SKIPPED_DAMAGE_TOO_EXTENSIVE("skipped_damage_too_extensive");
        companion object { fun of(s: String) = entries.first { it.wire == s } }
    }

    fun toJson(): Json.Obj {
        val m = linkedMapOf<String, Any?>(
            "width" to width, "height" to height, "white_page_detected" to whitePageDetected,
            "glare_pixels" to glarePixels, "shadow_pixels" to shadowPixels,
            "glare_regions" to glareRegions.map(::regionJson), "shadow_regions" to shadowRegions.map(::regionJson),
            "masked_fraction" to Json.Num(Json.pyFloat(maskedFraction, 6)),
            "thresholds" to Json.obj("hi" to hi, "lo" to lo),
            "status" to status.wire,
            "repair" to Json.obj(
                "illumination_flattened" to steps.illuminationFlattened, "glare_halo_stretched" to steps.glareHaloStretched,
                "inpainted_pixels" to steps.inpaintedPixels, "inpaint_method" to steps.inpaintMethod, "shadow_filled" to steps.shadowFilled,
            ),
        )
        readingOrderNodes?.let { m["reading_order_nodes"] = it }
        return Json.of(m).obj()
    }

    companion object {
        private fun regionJson(r: Region) = Json.obj("x" to r.x, "y" to r.y, "w" to r.w, "h" to r.h, "area" to r.area)
    }
}

fun Node.toJson(): Json.Obj = Json.obj("order" to order, "x" to box.x, "y" to box.y, "w" to box.w, "h" to box.h, "density" to Json.Num(Json.pyFloat(density, 4)))
