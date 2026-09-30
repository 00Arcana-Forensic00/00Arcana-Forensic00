package com.arcanaforensics.arcalume.core

import java.time.Instant
import java.time.ZoneOffset

/**
 * The introductory offer: every new install gets Pro free for [DAYS] days, then Pro is a
 * one-time purchase. Google Play has no free trial for one-time products, so the clock
 * runs on the device from first launch. Time only moves forward: if the phone's clock is
 * set back, the latest time already seen is used instead.
 */
object Trial {
    const val DAYS = 180
    private const val DAY_MS = 24L * 60 * 60 * 1000

    data class State(val startedMillis: Long, val lastSeenMillis: Long) {
        val endsMillis get() = startedMillis + DAYS * DAY_MS
        fun active() = lastSeenMillis < endsMillis
        /** Whole days left, rounded up, so the last day reads "1 day left". */
        fun daysLeft(): Int = if (!active()) 0 else ((endsMillis - lastSeenMillis + DAY_MS - 1) / DAY_MS).toInt()
        fun endsDate(): String = Instant.ofEpochMilli(endsMillis).atZone(ZoneOffset.UTC).toLocalDate().toString()
    }

    /** Starts the clock on first use and advances it; never lets it go backwards. */
    fun observe(previous: State?, nowMillis: Long): State =
        if (previous == null) State(nowMillis, nowMillis)
        else previous.copy(lastSeenMillis = maxOf(previous.lastSeenMillis, nowMillis))

    /** A purchase or license always wins; otherwise Pro while the offer runs. */
    fun combine(owned: Entitlements, state: State): Entitlements = when {
        owned.plan == Entitlements.Plan.PRO -> owned
        state.active() -> Entitlements.pro(Entitlements.Source.TRIAL, expires = state.endsDate())
        else -> owned
    }
}
