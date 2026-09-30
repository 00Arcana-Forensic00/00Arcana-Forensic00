package com.arcanaforensics.arcalume.core

import java.io.File
import java.io.FileOutputStream
import java.nio.file.FileAlreadyExistsException
import java.nio.file.Files

/**
 * Acquire -> triage -> repair -> seal -> record for one page, producing the same vault
 * and ledger entries as the desktop app (pipeline.process_bytes), so a vault sealed on
 * the phone opens in the desktop app and the other way round.
 */
object Evidence {
    const val LEDGER_NAME = "ledger.jsonl"
    const val NOTICE = "restored is a derivative: lighting is corrected across the whole page and the " +
        "pixels marked in mask were synthesized by inpainting (they carry no original data). " +
        "original is byte-identical to the acquired source."
    private val UNSAFE = Regex("[^A-Za-z0-9._-]+")
    private val rng = java.security.SecureRandom()

    data class Sealed(val vault: File, val vaultSha256: String, val ledgerEntry: Json.Obj, val report: Report)

    fun safeName(name: String): String {
        val base = UNSAFE.replace(name.substringAfterLast('/').substringAfterLast('\\'), "_").trim('.', '_').ifEmpty { "evidence" }
        return base.take(80)
    }

    fun manifest(
        tool: String, createdUtc: String, sourceName: String, original: ByteArray, restoredPng: ByteArray, maskPng: ByteArray,
        report: Report, nodes: List<Node>, cfg: RepairConfig, capture: Json.Obj? = null,
    ): Json.Obj {
        val m = linkedMapOf<String, Json>(
            "tool" to Json.Str(tool),
            "created_utc" to Json.Str(createdUtc),
            "source_name" to Json.Str(sourceName),
            "entries" to Json.obj(
                "original" to Json.obj("sha256" to sha256Hex(original), "size" to original.size),
                "restored" to Json.obj("sha256" to sha256Hex(restoredPng), "size" to restoredPng.size),
                "mask" to Json.obj("sha256" to sha256Hex(maskPng), "size" to maskPng.size),
            ),
            "report" to report.toJson(),
            "reading_order" to Json.Arr(nodes.map { it.toJson() }),
            "settings" to Json.obj("flatten" to cfg.flatten, "fill_shadow" to cfg.fillShadow, "repair" to cfg.repair),
            "notice" to Json.Str(NOTICE),
        )
        if (capture != null) m["capture"] = capture
        return Json.Obj(m)
    }

    /**
     * Seal already-recovered page data into `<vaultDir>/evidence-<hash16>-<random>.arcr` and
     * append `evidence_sealed` to the ledger. Never overwrites an existing file.
     */
    fun seal(
        vaultDir: File, sourceName: String, original: ByteArray, restoredPng: ByteArray, maskPng: ByteArray,
        manifest: Json.Obj, report: Report, passphrase: String, kdf: Vault.Kdf = Vault.DEFAULT_KDF,
    ): Sealed {
        val blob = Vault.seal(linkedMapOf(
            "manifest" to manifest.canonicalBytes(), "original" to original, "restored" to restoredPng, "mask" to maskPng,
        ), passphrase, kdf)
        vaultDir.mkdirs()
        val srcHash = sha256Hex(original)
        // No source name on disk or in the log (it stays in the encrypted manifest); the random
        // suffix keeps two copies of the same file as separate exhibits. Same rule as the desktop.
        val out = File(vaultDir, "evidence-${srcHash.take(16)}-${hex(ByteArray(3).also(rng::nextBytes))}.arcr")
        writeNew(out, blob)
        val blobHash = sha256Hex(blob)
        val entry = Ledger(File(vaultDir, LEDGER_NAME)).append("evidence_sealed", Json.obj(
            "source_sha256" to srcHash, "vault" to out.name, "vault_sha256" to blobHash,
            "status" to report.status.wire, "masked_fraction" to Json.Num(Json.pyFloat(report.maskedFraction, 6)),
        ))
        return Sealed(out, blobHash, entry, report)
    }

    fun recordRejected(vaultDir: File, original: ByteArray?, reason: String): Json.Obj {
        vaultDir.mkdirs()
        return Ledger(File(vaultDir, LEDGER_NAME)).append("rejected", Json.obj(
            "source_sha256" to original?.let(::sha256Hex), "reason" to reason,
        ))
    }

    /** Open a vault and check every entry against the hashes in its manifest. */
    fun open(blob: ByteArray, passphrase: String): Pair<Json.Obj, LinkedHashMap<String, ByteArray>> {
        val entries = Vault.unseal(blob, passphrase)
        val manifest = Json.parse(entries.getValue("manifest")).obj()
        for ((role, meta) in manifest["entries"]!!.obj().fields) {
            val data = entries[role] ?: continue
            if (sha256Hex(data) != meta.obj()["sha256"]!!.str()) throw Vault.VaultError("integrity check failed for $role")
        }
        return manifest to entries
    }

    /** Durably write a new file; fails if the destination exists. */
    fun writeNew(dest: File, data: ByteArray) {
        if (dest.exists()) throw FileAlreadyExistsException(dest.path, null, "a vault for this exact file already exists (refusing to overwrite)")
        val tmp = File.createTempFile(dest.name, ".tmp", dest.parentFile)
        try {
            FileOutputStream(tmp).use { it.write(data); it.fd.sync() }
            Files.move(tmp.toPath(), dest.toPath()) // no REPLACE_EXISTING: throws if dest appeared meanwhile
        } finally {
            tmp.delete()
        }
    }
}
