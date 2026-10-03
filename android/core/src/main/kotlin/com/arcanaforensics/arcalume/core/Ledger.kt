package com.arcanaforensics.arcalume.core

import java.io.File
import java.io.RandomAccessFile
import java.time.Instant
import java.time.ZoneOffset
import java.time.format.DateTimeFormatter
import java.time.temporal.ChronoUnit

/**
 * Append-only, SHA-256 hash-chained custody ledger (JSON Lines), the same format as the
 * desktop app's ledger.py: each line is
 * `{"data":..,"event":..,"hash":..,"prev":..,"seq":..,"ts":..}` where hash =
 * SHA-256(canonical({data, event, prev, seq, ts})). Editing, reordering or deleting a
 * line breaks the chain; keep the head elsewhere to also detect removed final lines.
 */
class Ledger(val file: File) {
    data class Result(val ok: Boolean, val entries: Int, val head: String, val message: String)

    companion object {
        const val GENESIS = "0000000000000000000000000000000000000000000000000000000000000000"
        private val TS = DateTimeFormatter.ofPattern("yyyy-MM-dd'T'HH:mm:ssxxx").withZone(ZoneOffset.UTC)

        fun entryHash(e: Json.Obj): String {
            val body = Json.Obj(listOf("seq", "ts", "event", "data", "prev").associateWith { e[it] ?: throw JsonError("missing $it") })
            return sha256Hex(body.canonicalBytes())
        }

        fun now(): String = TS.format(Instant.now().truncatedTo(ChronoUnit.SECONDS))
    }

    @Synchronized
    fun append(event: String, data: Json.Obj, ts: String = now()): Json.Obj {
        file.parentFile?.mkdirs()
        RandomAccessFile(file, "rw").use { raf ->
            raf.channel.lock().use {
                val last = lastEntry(raf)
                val fields = linkedMapOf<String, Json>(
                    "seq" to Json.of(if (last != null) last["seq"]!!.long() + 1 else 1L),
                    "ts" to Json.Str(ts),
                    "event" to Json.Str(event),
                    "data" to data,
                    "prev" to Json.Str(last?.get("hash")?.str() ?: GENESIS),
                )
                fields["hash"] = Json.Str(entryHash(Json.Obj(fields)))
                val entry = Json.Obj(fields)
                raf.seek(raf.length())
                raf.write(entry.canonicalBytes() + '\n'.code.toByte())
                raf.fd.sync()
                return entry
            }
        }
    }

    private fun lastEntry(raf: RandomAccessFile): Json.Obj? {
        val size = raf.length()
        if (size == 0L) return null
        val chunk = minOf(size, 1L shl 20).toInt()
        raf.seek(size - chunk)
        val buf = ByteArray(chunk).also { raf.readFully(it) }
        val lines = String(buf, Charsets.UTF_8).split('\n').filter { it.isNotBlank() }
        return lines.lastOrNull()?.let { Json.parse(it).obj() }
    }

    fun verify(expectHead: String? = null): Result {
        if (!file.exists()) return Result(expectHead == null, 0, GENESIS, if (expectHead == null) "no ledger" else "ledger missing")
        var prev = GENESIS
        var n = 0
        file.bufferedReader(Charsets.UTF_8).useLines { lines ->
            for ((idx, line) in lines.withIndex()) {
                val hash = try {
                    val e = Json.parse(line).obj()
                    val h = e["hash"]!!.str()
                    if (e["prev"]!!.str() == prev && e["seq"]!!.long() == n + 1L && h == entryHash(e)) h else null
                } catch (e: Exception) {
                    null
                }
                if (hash == null) return Result(false, n, prev, "chain broken at line ${idx + 1}")
                prev = hash
                n++
            }
        }
        if (expectHead != null && expectHead != prev) return Result(false, n, prev, "head does not match expected value (entries removed or replaced)")
        return Result(true, n, prev, "ok")
    }
}
