package com.arcanaforensics.arcalume.core

import org.bouncycastle.crypto.generators.Argon2BytesGenerator
import org.bouncycastle.crypto.params.Argon2Parameters
import java.nio.ByteBuffer
import java.security.GeneralSecurityException
import java.security.MessageDigest
import java.security.SecureRandom
import java.text.Normalizer
import javax.crypto.AEADBadTagException
import javax.crypto.Cipher
import javax.crypto.spec.GCMParameterSpec
import javax.crypto.spec.SecretKeySpec

/**
 * ARCR v1 vault, byte-compatible with the desktop app (restore/src/arcana_restore/vault.py):
 *
 *     "ARCR" | version(1) | header_len(4, BE) | header(JSON) | nonce(12) | ciphertext+tag
 *
 * Key = Argon2id(NFC(passphrase), per-file salt). The whole prefix is the AES-256-GCM
 * associated data, so changing any header byte (including KDF parameters) fails
 * authentication. File names and hashes live only in the encrypted manifest entry.
 */
object Vault {
    val MAGIC = byteArrayOf('A'.code.toByte(), 'R'.code.toByte(), 'C'.code.toByte(), 'R'.code.toByte())
    const val VERSION = 1
    const val NONCE_LEN = 12
    const val SALT_LEN = 16
    const val MIN_PASSPHRASE_CHARS = 12
    const val MAX_HEADER_BYTES = 64 * 1024
    const val MAX_PLAINTEXT_BYTES = 512L * 1024 * 1024
    val ROLES = listOf("manifest", "original", "restored", "mask")

    data class Kdf(val t: Int = 3, val mKib: Int = 65536, val p: Int = 4) {
        fun inBounds() = t in 1..10 && mKib in 16384..1048576 && p in 1..16
    }

    val DEFAULT_KDF = Kdf()
    private val random = SecureRandom()

    open class VaultError(msg: String) : Exception(msg)
    class AuthError : VaultError("authentication failed: wrong passphrase or the vault was modified")

    data class Header(val kdf: Kdf, val salt: ByteArray, val entries: List<Pair<String, Long>>, val prefix: ByteArray, val offset: Int)

    fun checkPassphrase(passphrase: String) {
        if (passphrase.codePointCount(0, passphrase.length) < MIN_PASSPHRASE_CHARS) throw VaultError("passphrase must be at least $MIN_PASSPHRASE_CHARS characters")
    }

    fun deriveKey(passphrase: String, salt: ByteArray, kdf: Kdf): ByteArray {
        checkPassphrase(passphrase)
        val pw = Normalizer.normalize(passphrase, Normalizer.Form.NFC).toByteArray(Charsets.UTF_8)
        val params = Argon2Parameters.Builder(Argon2Parameters.ARGON2_id)
            .withVersion(Argon2Parameters.ARGON2_VERSION_13)
            .withIterations(kdf.t).withMemoryAsKB(kdf.mKib).withParallelism(kdf.p)
            .withSalt(salt).build()
        val out = ByteArray(32)
        Argon2BytesGenerator().apply { init(params) }.generateBytes(pw, out)
        pw.fill(0)
        return out
    }

    /** [entries] keeps its order (role -> bytes) and must start with "manifest". */
    fun seal(entries: LinkedHashMap<String, ByteArray>, passphrase: String, kdf: Kdf = DEFAULT_KDF): ByteArray {
        if (entries.keys.firstOrNull() != "manifest") throw VaultError("entries must start with a manifest")
        entries.keys.forEach { if (it !in ROLES) throw VaultError("unknown entry role: $it") }
        val total = entries.values.sumOf { it.size.toLong() }
        if (total > MAX_PLAINTEXT_BYTES) throw VaultError("payload too large")
        val salt = ByteArray(SALT_LEN).also(random::nextBytes)
        val prefix = prefix(kdf, salt, entries.map { it.key to it.value.size.toLong() })
        val nonce = ByteArray(NONCE_LEN).also(random::nextBytes)
        val key = deriveKey(passphrase, salt, kdf)
        val plaintext = ByteArray(total.toInt()).also { buf ->
            var pos = 0
            for (b in entries.values) { System.arraycopy(b, 0, buf, pos, b.size); pos += b.size }
        }
        val ct = aes(Cipher.ENCRYPT_MODE, key, nonce, prefix, plaintext)
        key.fill(0)
        return prefix + nonce + ct
    }

    /** The exact prefix bytes the desktop app writes for these parameters. */
    fun prefix(kdf: Kdf, salt: ByteArray, entries: List<Pair<String, Long>>): ByteArray {
        val header = Json.obj(
            "kdf" to Json.obj("name" to "argon2id", "t" to kdf.t, "m_kib" to kdf.mKib, "p" to kdf.p, "salt" to hex(salt)),
            "entries" to entries.map { (r, s) -> Json.obj("role" to r, "size" to s) },
        ).canonicalBytes()
        return MAGIC + byteArrayOf(VERSION.toByte()) + ByteBuffer.allocate(4).putInt(header.size).array() + header
    }

    fun parseHeader(blob: ByteArray): Header {
        if (blob.size < 9 || !blob.copyOfRange(0, 4).contentEquals(MAGIC)) throw VaultError("not an Arcana vault (bad magic)")
        if (blob[4].toInt() != VERSION) throw VaultError("unsupported vault version ${blob[4]}")
        val hlen = ByteBuffer.wrap(blob, 5, 4).int.toLong() and 0xffffffffL
        if (hlen == 0L || hlen > MAX_HEADER_BYTES || blob.size < 9 + hlen + NONCE_LEN + 16) throw VaultError("vault header is truncated or oversized")
        val end = 9 + hlen.toInt()
        try {
            val h = Json.parse(blob.copyOfRange(9, end)).obj()
            val k = h["kdf"]!!.obj()
            if (k["name"]?.str() != "argon2id") throw JsonError("kdf")
            val salt = unhex(k["salt"]!!.str())
            if (salt.size != SALT_LEN) throw JsonError("salt")
            val kdf = Kdf(k["t"]!!.long().toInt(), k["m_kib"]!!.long().toInt(), k["p"]!!.long().toInt())
            if (!kdf.inBounds()) throw JsonError("kdf bounds")
            val entries = h["entries"]!!.arr().map { it.obj()["role"]!!.str() to it.obj()["size"]!!.long() }
            if (entries.isEmpty() || entries[0].first != "manifest") throw JsonError("entries")
            if (entries.map { it.first }.toSet().size != entries.size || entries.any { it.first !in ROLES || it.second < 0 }) throw JsonError("entries")
            if (entries.sumOf { it.second } > MAX_PLAINTEXT_BYTES) throw JsonError("size")
            return Header(kdf, salt, entries, blob.copyOfRange(0, end), end)
        } catch (e: VaultError) {
            throw e
        } catch (e: Exception) {
            throw VaultError("invalid vault header (${e.message ?: e::class.simpleName})")
        }
    }

    fun unseal(blob: ByteArray, passphrase: String): LinkedHashMap<String, ByteArray> {
        val h = parseHeader(blob)
        val nonce = blob.copyOfRange(h.offset, h.offset + NONCE_LEN)
        val ct = blob.copyOfRange(h.offset + NONCE_LEN, blob.size)
        val key = deriveKey(passphrase, h.salt, h.kdf)
        val plain = try {
            aes(Cipher.DECRYPT_MODE, key, nonce, h.prefix, ct)
        } catch (e: AEADBadTagException) {
            throw AuthError()
        } catch (e: GeneralSecurityException) {
            throw AuthError()
        } finally {
            key.fill(0)
        }
        if (plain.size.toLong() != h.entries.sumOf { it.second }) throw VaultError("entry sizes do not match payload")
        val out = LinkedHashMap<String, ByteArray>()
        var pos = 0
        for ((role, size) in h.entries) { out[role] = plain.copyOfRange(pos, pos + size.toInt()); pos += size.toInt() }
        return out
    }

    private fun aes(mode: Int, key: ByteArray, nonce: ByteArray, aad: ByteArray, data: ByteArray): ByteArray =
        Cipher.getInstance("AES/GCM/NoPadding").run {
            init(mode, SecretKeySpec(key, "AES"), GCMParameterSpec(128, nonce))
            updateAAD(aad)
            doFinal(data)
        }
}

fun sha256Hex(data: ByteArray): String = hex(MessageDigest.getInstance("SHA-256").digest(data))
fun hex(b: ByteArray): String = b.joinToString("") { String.format(java.util.Locale.ROOT, "%02x", it.toInt() and 0xff) }
fun unhex(s: String): ByteArray {
    if (s.length % 2 != 0 || !s.all { it in '0'..'9' || it in 'a'..'f' }) throw JsonError("bad hex")
    return ByteArray(s.length / 2) { s.substring(it * 2, it * 2 + 2).toInt(16).toByte() }
}
