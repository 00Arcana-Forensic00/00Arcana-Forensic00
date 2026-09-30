package com.arcanaforensics.arcalume.data

import androidx.compose.ui.graphics.ImageBitmap
import com.arcanaforensics.arcalume.core.Finding
import com.arcanaforensics.arcalume.core.Json
import com.arcanaforensics.arcalume.core.Node
import com.arcanaforensics.arcalume.core.RepairConfig
import com.arcanaforensics.arcalume.core.Report

enum class Source(val wire: String) { CAMERA("camera"), IMPORT("import"), SAMPLE("sample") }

/** One page in the current session: the untouched original plus what recovery made of it. */
class Page(
    val id: Long,
    val name: String,
    val source: Source,
    val original: ByteArray,
    val originalSha256: String,
    val acquiredUtc: String,
    val cfg: RepairConfig,
    val report: Report,
    val nodes: List<Node>,
    val findings: List<Finding>,
    val scale: Double,
    val workWidth: Int,
    val workHeight: Int,
    val restoredPng: ByteArray,
    val maskPng: ByteArray,
    val previewOriginal: ImageBitmap,
    val previewRestored: ImageBitmap,
    val previewOverlay: ImageBitmap,
) {
    /** How the page reached the app, recorded in the sealed manifest. */
    fun captureJson(): Json.Obj = Json.obj(
        "source" to source.wire,
        "acquired_utc" to acquiredUtc,
        "provenance" to when (source) {
            Source.CAMERA -> "captured in-app; original bytes are the camera's file, unmodified"
            Source.IMPORT -> "imported; history before import is unknown"
            Source.SAMPLE -> "synthetic sample page"
        },
        "processing" to Json.obj(
            "scale" to Json.Num(Json.pyFloat(scale, 6)), "width" to workWidth, "height" to workHeight,
        ),
    )
}
