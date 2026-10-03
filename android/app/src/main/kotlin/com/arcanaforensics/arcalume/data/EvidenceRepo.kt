package com.arcanaforensics.arcalume.data

import android.content.Context
import com.arcanaforensics.arcalume.Brand
import com.arcanaforensics.arcalume.core.Evidence
import com.arcanaforensics.arcalume.core.Json
import com.arcanaforensics.arcalume.core.Ledger
import com.arcanaforensics.arcalume.core.Vault
import java.io.File

/**
 * The vault folder in app-private storage: sealed `.arcr` files plus `ledger.jsonl`.
 * The last ledger head this phone wrote is remembered, so a log that loses its final
 * entries is caught even when the user never saved the fingerprint elsewhere.
 */
class EvidenceRepo(context: Context) {
    val dir = File(context.filesDir, "vault")
    private val prefs = context.getSharedPreferences("custody", Context.MODE_PRIVATE)
    private val ledger get() = Ledger(File(dir, Evidence.LEDGER_NAME))
    val ledgerFile: File get() = File(dir, Evidence.LEDGER_NAME)

    data class VaultFile(val file: File, val sealedMillis: Long, val bytes: Long)
    data class LogEntry(val seq: Long, val ts: String, val event: String, val sourceName: String?, val hash: String)
    data class Check(val result: Ledger.Result, val matchedKnown: Boolean, val matchedExpected: Boolean)

    val knownHead: String? get() = prefs.getString("head", null)

    private fun remember(entry: Json.Obj) {
        prefs.edit().putString("head", entry["hash"]!!.str()).apply()
    }

    fun vaults(): List<VaultFile> = (dir.listFiles { f -> f.isFile && f.name.endsWith(".arcr") } ?: emptyArray())
        .map { VaultFile(it, it.lastModified(), it.length()) }
        .sortedByDescending { it.sealedMillis }

    @Synchronized
    fun seal(page: Page, passphrase: String, kdf: Vault.Kdf = Vault.DEFAULT_KDF): Evidence.Sealed {
        val manifest = Evidence.manifest(
            Brand.TOOL, Ledger.now(), page.name, page.original, page.restoredPng, page.maskPng,
            page.report, page.nodes, page.cfg, page.captureJson(),
        )
        return Evidence.seal(dir, page.name, page.original, page.restoredPng, page.maskPng, manifest, page.report, passphrase, kdf)
            .also { remember(it.ledgerEntry) }
    }

    @Synchronized
    fun delete(v: VaultFile) {
        val sha = com.arcanaforensics.arcalume.core.sha256Hex(v.file.readBytes())
        val entry = ledger.append("vault_deleted", Json.obj("vault" to v.file.name, "vault_sha256" to sha))
        remember(entry)
        v.file.delete()
    }

    fun verify(expected: String?): Check {
        val exp = expected?.trim()?.lowercase()?.takeIf { it.isNotEmpty() }
        val r = ledger.verify(exp)
        val known = knownHead
        if (r.ok && exp == null && known != null && known != r.head) {
            return Check(Ledger.Result(false, r.entries, r.head, "the log no longer ends where this phone last recorded (entries were removed or replaced)"), false, false)
        }
        return Check(r, r.ok && known != null && known == r.head, r.ok && exp != null)
    }

    fun entries(limit: Int = 500): List<LogEntry> {
        val f = ledgerFile
        if (!f.exists()) return emptyList()
        return f.readLines().takeLast(limit).mapNotNull { line ->
            runCatching {
                val e = Json.parse(line).obj()
                val data = e["data"]?.obj()
                LogEntry(e["seq"]!!.long(), e["ts"]!!.str(), e["event"]!!.str(), (data?.get("source_name") ?: data?.get("vault"))?.let { (it as? Json.Str)?.value }, e["hash"]!!.str())
            }.getOrNull()
        }.reversed()
    }
}
