package com.arcanaforensics.arcalume.core

import java.util.Locale

/** A plain-language line about what happened to a page, as the desktop app words it. */
data class Finding(val level: Level, val text: String) {
    enum class Level { OK, INFO, WARN }
}

object Findings {
    fun pct(x: Double): String {
        val v = x * 100
        return if (v >= 0.1 || v == 0.0) String.format(Locale.ROOT, "%.1f%%", v) else "under 0.1%"
    }

    fun of(report: Report, nodes: Int): List<Finding> {
        val out = ArrayList<Finding>()
        val steps = report.steps
        when (report.status) {
            Report.Status.SKIPPED_DAMAGE_TOO_EXTENSIVE -> out += Finding(Finding.Level.WARN,
                "Over ${pct(0.30)} of the page is blown out, so nothing was changed. Retake the photo at an angle to the light.")
            Report.Status.DETECTED_NOT_REPAIRED -> out += Finding(Finding.Level.INFO, "Repair is off: damage is reported, pixels are untouched.")
            else -> {}
        }
        if (steps.illuminationFlattened) out += Finding(Finding.Level.OK, "Shadows and uneven lighting were evened out across the page.")
        val g = report.glareRegions.size
        if (g > 0) {
            out += Finding(Finding.Level.WARN,
                "$g glare spot${if (g != 1) "s" else ""} found. Faded text around ${if (g != 1) "them" else "it"} was restored. " +
                    "The blown-out centre (${pct(report.maskedFraction)} of the page) held no data and was filled smoothly. " +
                    "Text that was there cannot be recovered from this photo; turn on “Show filled areas” to see where.")
        }
        val s = report.shadowRegions.size
        if (s > 0 && !steps.shadowFilled) {
            out += Finding(Finding.Level.INFO,
                "$s solid black area${if (s != 1) "s" else ""} left untouched. These are often redactions, photos or scanner edges. " +
                    "You can fill them if they are shadows.")
        } else if (s > 0) {
            out += Finding(Finding.Level.WARN, "$s solid black area${if (s != 1) "s were" else " was"} filled, as you asked.")
        }
        if (g == 0 && s == 0 && report.status in setOf(Report.Status.STABLE, Report.Status.ENHANCED)) {
            out += Finding(Finding.Level.OK, "No blown-out or blacked-out areas: nothing was invented.")
        }
        if (nodes > 0) out += Finding(Finding.Level.INFO, "Reading order mapped: $nodes text blocks.")
        return out
    }
}
