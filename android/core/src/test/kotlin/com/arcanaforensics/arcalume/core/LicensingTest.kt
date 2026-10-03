package com.arcanaforensics.arcalume.core

import java.time.LocalDate
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertFailsWith

class LicensingTest {
    private val d = Fixtures.desktop
    private val pub = listOf(d["public_key"]!!.str())
    private fun key(name: String) = d["keys"]!!.obj()[name]!!.str()
    private val today = LocalDate.of(2026, 9, 30)

    private fun fails(k: String?, msg: String, keys: List<String> = pub) {
        val e = assertFailsWith<Licensing.LicenseError> { Licensing.verifyKey(k, keys, today) }
        assertEquals(msg, e.message)
    }

    @Test fun `accepts keys the desktop tool issued`() {
        val p = Licensing.verifyKey(key("valid"), pub, today)
        val ent = Licensing.entitlementsFor(p)
        assertEquals(Entitlements.Plan.PRO, ent.plan)
        assertEquals("Ann Examiner", ent.licensee)
        // line breaks from email clients are tolerated
        Licensing.verifyKey(key("valid_until_2030").chunked(40).joinToString("\n"), pub, today)
    }

    @Test fun `rejects bad keys with the desktop wording`() {
        fails(key("expired"), "This license expired on 2020-01-01.")
        fails(key("bad_expiry"), "The license key has an invalid expiry date.")
        fails(key("other_product"), "This license key is for a different product.")
        fails(key("forged"), "This license key is not valid.")
        fails(key("valid"), "This build cannot validate license keys yet.", emptyList())
        fails("hello", "That doesn't look like a license key.")
        fails(null, "That doesn't look like a license key.")
        fails("ARC1.@@@.###", "The license key is damaged. Copy it again from your receipt.")
        val parts = key("valid").split(".")
        fails("${parts[0]}.${parts[1]}.${parts[2].reversed()}", "This license key is not valid.")
    }
}
