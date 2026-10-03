package com.arcanaforensics.arcalume.core

import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertFalse
import kotlin.test.assertTrue

class TrialTest {
    private val day = 24L * 60 * 60 * 1000
    private val t0 = 1_790_000_000_000L

    @Test fun `new installs get 180 days of Pro, then fall back to free`() {
        var s = Trial.observe(null, t0)
        assertEquals(180, s.daysLeft())
        assertEquals(Entitlements.Source.TRIAL, Trial.combine(Entitlements.FREE, s).source)
        s = Trial.observe(s, t0 + 179 * day + 1)
        assertEquals(1, s.daysLeft())
        assertTrue(Trial.combine(Entitlements.FREE, s).seal)
        s = Trial.observe(s, t0 + 180 * day)
        assertFalse(s.active())
        assertEquals(Entitlements.FREE, Trial.combine(Entitlements.FREE, s))
    }

    @Test fun `setting the clock back does not extend the offer`() {
        var s = Trial.observe(Trial.observe(null, t0), t0 + 200 * day)
        s = Trial.observe(s, t0 + 10 * day)
        assertFalse(s.active())
    }

    @Test fun `a purchase wins over the trial`() {
        val s = Trial.observe(null, t0)
        assertEquals(Entitlements.Source.PLAY, Trial.combine(Entitlements.pro(Entitlements.Source.PLAY), s).source)
    }
}
