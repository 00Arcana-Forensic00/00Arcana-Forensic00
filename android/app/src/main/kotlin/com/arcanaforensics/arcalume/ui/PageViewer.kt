package com.arcanaforensics.arcalume.ui

import androidx.compose.foundation.Canvas
import androidx.compose.foundation.gestures.awaitEachGesture
import androidx.compose.foundation.gestures.awaitFirstDown
import androidx.compose.foundation.gestures.calculatePan
import androidx.compose.foundation.gestures.calculateZoom
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.aspectRatio
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.heightIn
import androidx.compose.runtime.Composable
import androidx.compose.runtime.rememberUpdatedState
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clipToBounds
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.geometry.Size
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.graphics.drawscope.clipRect
import androidx.compose.ui.graphics.graphicsLayer
import androidx.compose.ui.input.pointer.pointerInput
import androidx.compose.ui.input.pointer.positionChanged
import androidx.compose.ui.semantics.CustomAccessibilityAction
import androidx.compose.ui.semantics.contentDescription
import androidx.compose.ui.semantics.customActions
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.text.TextStyle
import androidx.compose.ui.text.drawText
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.rememberTextMeasurer
import androidx.compose.ui.unit.IntSize
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.arcanaforensics.arcalume.data.Page

enum class ViewMode { ORIGINAL, COMPARE, RECOVERED }

private val Ink = Color(0xFF0B1F3A)
private val Marker = Color(0xFFF2B84B)

/**
 * The page, drawn as original, recovered, or both split at [split] (0..1 of the width
 * showing the original). Pinch to zoom and drag to pan once zoomed; one-finger drags at
 * 100% scroll the screen instead. Every gesture has a button or accessibility action.
 */
@Composable
fun PageViewer(
    page: Page, mode: ViewMode, split: Float, showMask: Boolean, showOrder: Boolean,
    zoom: Float, offset: Offset, onTransform: (Float, Offset) -> Unit,
    description: String, actions: List<CustomAccessibilityAction>,
    modifier: Modifier = Modifier,
) {
    val w = page.previewRestored.width
    val h = page.previewRestored.height
    val measurer = rememberTextMeasurer()
    val zoomNow = rememberUpdatedState(zoom)
    val offsetNow = rememberUpdatedState(offset)
    val transform = rememberUpdatedState(onTransform)
    val recovered = if (showMask) page.previewOverlay else page.previewRestored
    val nodeScale = w.toFloat() / page.workWidth
    Box(
        modifier.fillMaxWidth().heightIn(max = 640.dp).aspectRatio(w.toFloat() / h, matchHeightConstraintsFirst = false).clipToBounds()
            .semantics { contentDescription = description; customActions = actions }
            .pointerInput(Unit) {
                awaitEachGesture {
                    awaitFirstDown(requireUnconsumed = false)
                    var z = zoomNow.value
                    var o = offsetNow.value
                    do {
                        val event = awaitPointerEvent()
                        if (event.changes.size > 1 || z > 1f) {
                            z = (z * event.calculateZoom()).coerceIn(1f, 8f)
                            val maxX = (z - 1f) * size.width / 2f
                            val maxY = (z - 1f) * size.height / 2f
                            val p = o + event.calculatePan()
                            o = Offset(p.x.coerceIn(-maxX, maxX), p.y.coerceIn(-maxY, maxY))
                            transform.value(z, o)
                            event.changes.forEach { if (it.positionChanged()) it.consume() }
                        }
                    } while (event.changes.any { it.pressed })
                }
            },
    ) {
        Canvas(Modifier.fillMaxSize().graphicsLayer(scaleX = zoom, scaleY = zoom, translationX = offset.x, translationY = offset.y)) {
            val dst = IntSize(size.width.toInt(), size.height.toInt())
            when (mode) {
                ViewMode.ORIGINAL -> drawImage(page.previewOriginal, dstSize = dst)
                ViewMode.RECOVERED -> drawImage(recovered, dstSize = dst)
                ViewMode.COMPARE -> {
                    drawImage(recovered, dstSize = dst)
                    val x = size.width * split
                    clipRect(right = x) { drawImage(page.previewOriginal, dstSize = dst) }
                    drawLine(Color.White, Offset(x, 0f), Offset(x, size.height), strokeWidth = 6f / zoom)
                    drawLine(Ink, Offset(x, 0f), Offset(x, size.height), strokeWidth = 2f / zoom)
                }
            }
            if (showOrder && mode != ViewMode.ORIGINAL) {
                val k = size.width / w * nodeScale
                for (n in page.nodes) {
                    val tl = Offset(n.box.x * k, n.box.y * k)
                    val sz = Size(n.box.w * k, n.box.h * k)
                    drawRect(Color.White, tl, sz, style = Stroke(4f / zoom))
                    drawRect(Ink, tl, sz, style = Stroke(2f / zoom))
                    val label = measurer.measure("${n.order + 1}", TextStyle(fontSize = (11 / zoom).coerceAtLeast(4f).sp, fontWeight = FontWeight.Bold, color = Ink, background = Marker))
                    drawText(label, topLeft = Offset(tl.x, (tl.y - label.size.height).coerceAtLeast(0f)))
                }
            }
        }
    }
}

