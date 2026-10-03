package com.arcanaforensics.arcalume.data

import android.content.SharedPreferences
import com.arcanaforensics.arcalume.core.Entitlements
import com.arcanaforensics.arcalume.core.Trial
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.SharingStarted
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.combine
import kotlinx.coroutines.flow.stateIn

/**
 * Wraps the real store (Play Billing or license keys) with the 180-day introductory Pro
 * offer. The offer's clock is kept in app-private preferences, which are excluded from
 * backups, so it starts at the first launch on each device.
 */
class TrialProStore(private val inner: ProStore, private val prefs: SharedPreferences, now: () -> Long = System::currentTimeMillis) : ProStore by inner {
    private val clock = now
    private val trialState = MutableStateFlow(load())
    val trial: StateFlow<Trial.State> = trialState
    private val scope = CoroutineScope(SupervisorJob() + Dispatchers.Main.immediate)

    override val entitlements: StateFlow<Entitlements> = combine(inner.entitlements, trialState) { owned, t -> Trial.combine(owned, t) }
        .stateIn(scope, SharingStarted.Eagerly, Trial.combine(inner.entitlements.value, trialState.value))

    /** Advance the clock; called on every launch and return to the app. */
    fun tick() { trialState.value = load() }

    private fun load(): Trial.State {
        val prev = if (prefs.contains("trial_start")) Trial.State(prefs.getLong("trial_start", 0), prefs.getLong("trial_seen", 0)) else null
        val next = Trial.observe(prev, clock())
        prefs.edit().putLong("trial_start", next.startedMillis).putLong("trial_seen", next.lastSeenMillis).apply()
        return next
    }
}
