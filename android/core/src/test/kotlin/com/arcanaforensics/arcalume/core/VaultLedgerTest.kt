package com.arcanaforensics.arcalume.core

import java.io.File
import java.nio.file.Files
import kotlin.test.Test
import kotlin.test.assertContentEquals
import kotlin.test.assertEquals
import kotlin.test.assertFailsWith
import kotlin.test.assertFalse
import kotlin.test.assertTrue

class VaultLedgerTest {
    private val pw get() = Fixtures.desktop["passphrase"]!!.str()
    private fun tmp(): File = Files.createTempDirectory("arcalume").toFile()

    @Test fun `opens a vault the desktop app sealed`() {
        val out = Vault.unseal(Fixtures.file("desktop.arcr").readBytes(), pw)
        assertEquals(listOf("manifest", "original", "restored", "mask"), out.keys.toList())
        assertEquals("Übersicht.png", Json.parse(out.getValue("manifest")).obj()["source_name"]!!.str())
        assertContentEquals("\u0089PNG fake original".toByteArray(Charsets.ISO_8859_1), out.getValue("original"))
        assertEquals(0, out.getValue("mask").size)
    }

    @Test fun `wrong passphrase and any changed byte fail authentication`() {
        val blob = Fixtures.file("desktop.arcr").readBytes()
        assertFailsWith<Vault.AuthError> { Vault.unseal(blob, "definitely the wrong one") }
        for (i in listOf(9, 20, blob.size - 1, blob.size - 20)) {
            val bad = blob.copyOf().also { it[i] = (it[i].toInt() xor 1).toByte() }
            assertFailsWith<Vault.VaultError>("byte $i") { Vault.unseal(bad, pw) }
        }
    }

    @Test fun `rejects hostile headers before deriving a key`() {
        val salt = ByteArray(16)
        val huge = Vault.prefix(Vault.Kdf(3, 4_000_000, 4), salt, listOf("manifest" to 1L)) + ByteArray(40)
        assertFailsWith<Vault.VaultError> { Vault.parseHeader(huge) }
        val noManifest = Vault.prefix(Vault.Kdf(1, 16384, 1), salt, listOf("original" to 1L)) + ByteArray(40)
        assertFailsWith<Vault.VaultError> { Vault.parseHeader(noManifest) }
        assertFailsWith<Vault.VaultError> { Vault.parseHeader("ARCX".toByteArray() + ByteArray(40)) }
        assertFailsWith<Vault.VaultError> { Vault.seal(linkedMapOf("manifest" to ByteArray(1)), "short") }
    }

    @Test fun `round trip and prefix bytes match the desktop format`() {
        val entries = linkedMapOf("manifest" to "{}".toByteArray(), "original" to ByteArray(1000) { it.toByte() })
        val blob = Vault.seal(entries, pw, Fixtures.FAST_KDF)
        val h = Vault.parseHeader(blob)
        val header = String(h.prefix, 9, h.prefix.size - 9, Charsets.US_ASCII)
        assertEquals("""{"entries":[{"role":"manifest","size":2},{"role":"original","size":1000}],"kdf":{"m_kib":16384,"name":"argon2id","p":1,"salt":"${hex(h.salt)}","t":1}}""", header)
        val back = Vault.unseal(blob, pw)
        assertContentEquals(entries.getValue("original"), back.getValue("original"))
        // NFC: a decomposed passphrase opens a vault sealed with the composed form
        val v2 = Vault.seal(entries, "caf\u00e9 correct horse", Fixtures.FAST_KDF)
        Vault.unseal(v2, "cafe\u0301 correct horse")
    }

    @Test fun `verifies and extends a ledger the desktop app wrote`() {
        val d = Fixtures.desktop
        val dir = tmp()
        val f = File(dir, "ledger.jsonl").also { Fixtures.file("desktop_ledger.jsonl").copyTo(it) }
        val r = Ledger(f).verify(d["ledger_head"]!!.str())
        assertTrue(r.ok, r.message)
        assertEquals(d["ledger_entries"]!!.long().toInt(), r.entries)
        val e = Ledger(f).append("opened", Json.obj("by" to "phone", "fraction" to Json.Num(Json.pyFloat(0.00005))))
        assertEquals(4L, e["seq"]!!.long())
        assertTrue(Ledger(f).verify(e["hash"]!!.str()).ok)
        assertFalse(Ledger(f).verify(d["ledger_head"]!!.str()).ok, "old head must not match after an append")
    }

    @Test fun `detects edits, reordering and truncation`() {
        val dir = tmp()
        val lg = Ledger(File(dir, "l.jsonl"))
        repeat(4) { lg.append("e$it", Json.obj("i" to it)) }
        val head = lg.verify().head
        val lines = lg.file.readLines()
        lg.file.writeText(lines.mapIndexed { i, l -> if (i == 1) l.replace("\"i\":1", "\"i\":9") else l }.joinToString("\n", postfix = "\n"))
        assertEquals("chain broken at line 2", lg.verify().message)
        lg.file.writeText(listOf(lines[0], lines[2], lines[1], lines[3]).joinToString("\n", postfix = "\n"))
        assertFalse(lg.verify().ok)
        lg.file.writeText(lines.dropLast(1).joinToString("\n", postfix = "\n"))
        assertTrue(lg.verify().ok)
        assertFalse(lg.verify(head).ok, "a removed final line is caught with the saved head")
        assertFalse(Ledger(File(dir, "missing")).verify(head).ok)
    }
}
