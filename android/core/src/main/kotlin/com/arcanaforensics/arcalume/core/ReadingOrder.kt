package com.arcanaforensics.arcalume.core

/** An axis-aligned block on the page, in pixels. */
data class Box(val x: Int, val y: Int, val w: Int, val h: Int) {
    fun start(axis: Int) = if (axis == 0) x else y
    fun end(axis: Int) = if (axis == 0) x + w else y + h
}

/**
 * XY-cut reading order, identical to the desktop engine (imaging.xy_cut): at each step a
 * vertical gutter at least [minColGap] wide that clears every block splits the set into
 * columns; otherwise the widest horizontal gap splits it into rows. Iterative, so a page
 * with thousands of blocks cannot overflow the stack.
 */
object ReadingOrder {
    const val MAX_NODES = 5000

    fun widestGap(boxes: List<Box>, axis: Int): Pair<Int, Int> {
        val spans = boxes.map { it.start(axis) to it.end(axis) }.sortedWith(compareBy({ it.first }, { it.second }))
        var best = 0 to 0
        var reach = spans[0].second
        for ((start, end) in spans.drop(1)) {
            if (start > reach && start - reach > best.first) best = (start - reach) to start
            reach = maxOf(reach, end)
        }
        return best
    }

    fun xyCut(boxes: List<Box>, minColGap: Int = 1): List<Box> {
        val out = ArrayList<Box>(boxes.size)
        val stack = ArrayDeque<List<Box>>().apply { addLast(boxes) }
        while (stack.isNotEmpty()) {
            val group = stack.removeLast()
            if (group.size <= 1) { out.addAll(group); continue }
            val (xGap, xCut) = widestGap(group, 0)
            val (yGap, yCut) = widestGap(group, 1)
            val (axis, cut) = when {
                xGap >= minColGap -> 0 to xCut
                yGap > 0 -> 1 to yCut
                else -> { out.addAll(group.sortedWith(compareBy({ it.y }, { it.x }))); continue }
            }
            stack.addLast(group.filter { it.start(axis) >= cut })   // taken second
            stack.addLast(group.filter { it.start(axis) < cut })
        }
        return out
    }

    /** Python's `_odd`: round half to even, clamp to [minimum], then make odd. */
    fun odd(n: Double, minimum: Int): Int {
        val r = maxOf(Math.rint(n).toInt(), minimum)
        return if (r % 2 == 1) r else r + 1
    }
}
