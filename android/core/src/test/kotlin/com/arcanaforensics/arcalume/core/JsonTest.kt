package com.arcanaforensics.arcalume.core

import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertFailsWith

class JsonTest {
    @Test fun `canonical bytes match Python json dumps`() {
        for (c in Fixtures.desktop["canonical"]!!.arr()) {
            val o = c.obj()
            assertEquals(o["bytes"]!!.str(), o["value"]!!.canonical())
        }
    }

    @Test fun `python float repr`() {
        val cases = mapOf(0.25 to "0.25", 1.0 to "1.0", 0.00005 to "5e-05", 0.012345 to "0.012345", 0.0 to "0.0",
            0.30 to "0.3", 1234567.0 to "1234567.0", 0.0001 to "0.0001", 0.00012 to "0.00012", 1.5e-6 to "2e-06", -0.00005 to "-5e-05")
        for ((x, want) in cases) assertEquals(want, Json.pyFloat(x), "for $x")
        assertEquals("0.0123", Json.pyFloat(0.01234567, 4))
    }

    @Test fun `parser keeps number text and rejects bad input`() {
        val line = """{"a":1e-07,"b":[2.50,-0],"c":"\u00e9\ud83d\ude00"}"""
        val v = Json.parse(line).obj()
        assertEquals("1e-07", (v["a"] as Json.Num).raw)
        assertEquals("\u00e9\ud83d\ude00", v["c"]!!.str())
        assertEquals("""{"a":1e-07,"b":[2.50,-0],"c":"\u00e9\ud83d\ude00"}""", v.canonical())
        for (bad in listOf("""{"a":1,"a":2}""", "[1,]", "01", "{", "\"\\x\"", "[1] 2", "nul", "\"\u0001\"")) {
            assertFailsWith<JsonError>(bad) { Json.parse(bad) }
        }
        Json.parse("[".repeat(Json.MAX_DEPTH + 1) + "]".repeat(Json.MAX_DEPTH + 1))
        assertFailsWith<JsonError> { Json.parse("[".repeat(Json.MAX_DEPTH + 2) + "]".repeat(Json.MAX_DEPTH + 2)) }
    }
}
