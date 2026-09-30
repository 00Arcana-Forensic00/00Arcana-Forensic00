package com.arcanaforensics.arcalume.core

import org.bouncycastle.crypto.params.Ed25519PublicKeyParameters
import org.bouncycastle.crypto.signers.Ed25519Signer
import java.time.LocalDate
import java.time.ZoneOffset
import java.time.format.DateTimeParseException
import java.util.Base64

/**
 * Offline license keys, the same format the desktop app and the license worker use:
 * `ARC1.<base64url payload>.<base64url signature>`, Ed25519 over the raw payload bytes.
 * The app holds only public keys, so it can check a key but never mint one.
 *
 * On Google Play, Pro is bought with Play Billing ([Entitlements.Source.PLAY]); keys
 * are for the direct (sideloaded) build and for customers who already own a key.
 */
object Licensing {
    const val PREFIX = "ARC1"
    const val PRODUCT = "arcalume"
    const val MAX_KEY_CHARS = 4096

    class LicenseError(msg: String) : Exception(msg)

    /** Returns the payload of a valid key, or throws [LicenseError] with a message fit for the user. */
    fun verifyKey(key: String?, publicKeys: List<String>, today: LocalDate = LocalDate.now(ZoneOffset.UTC)): Json.Obj {
        val k = (key ?: "").filterNot { it.isWhitespace() }
        if (k.isEmpty() || k.length > MAX_KEY_CHARS) throw LicenseError("That doesn't look like a license key.")
        val parts = k.split(".")
        if (parts.size != 3 || parts[0] != PREFIX) throw LicenseError("That doesn't look like a license key.")
        val raw: ByteArray
        val sig: ByteArray
        val payload: Json
        try {
            raw = b64d(parts[1])
            sig = b64d(parts[2])
            payload = Json.parse(raw)
        } catch (e: IllegalArgumentException) {
            throw LicenseError("The license key is damaged. Copy it again from your receipt.")
        }
        if (publicKeys.isEmpty()) throw LicenseError("This build cannot validate license keys yet.")
        val good = publicKeys.any { pk ->
            try {
                val pub = Base64.getDecoder().decode(pk)
                sig.size == 64 && pub.size == 32 && Ed25519Signer().run {
                    init(false, Ed25519PublicKeyParameters(pub, 0))
                    update(raw, 0, raw.size)
                    verifySignature(sig)
                }
            } catch (e: IllegalArgumentException) {
                false
            }
        }
        if (!good) throw LicenseError("This license key is not valid.")
        val obj = payload as? Json.Obj
        if (obj == null || (obj["v"] as? Json.Num)?.raw != "1" || (obj["product"] as? Json.Str)?.value != PRODUCT) {
            throw LicenseError("This license key is for a different product.")
        }
        val exp = obj["expires"]
        if (exp != null && exp != Json.Null && !(exp is Json.Str && exp.value.isEmpty())) {
            val expires = try {
                LocalDate.parse(exp.str())
            } catch (e: Exception) {
                when (e) { is DateTimeParseException, is JsonError -> throw LicenseError("The license key has an invalid expiry date."); else -> throw e }
            }
            if (expires < today) throw LicenseError("This license expired on ${exp.str()}.")
        }
        return obj
    }

    fun entitlementsFor(payload: Json.Obj): Entitlements {
        val name = (payload["name"] as? Json.Str)?.value?.takeIf { it.isNotEmpty() } ?: (payload["email"] as? Json.Str)?.value ?: ""
        return Entitlements.pro(Entitlements.Source.KEY, name, (payload["expires"] as? Json.Str)?.value)
    }

    private fun b64d(s: String): ByteArray = Base64.getUrlDecoder().decode(s.trimEnd('='))
}

data class Entitlements(val plan: Plan, val source: Source, val licensee: String = "", val expires: String? = null) {
    enum class Plan { FREE, PRO }
    enum class Source { NONE, KEY, PLAY }

    val cleanExport get() = plan == Plan.PRO
    val seal get() = plan == Plan.PRO
    val batch get() = plan == Plan.PRO

    companion object {
        val FREE = Entitlements(Plan.FREE, Source.NONE)
        fun pro(source: Source, licensee: String = "", expires: String? = null) = Entitlements(Plan.PRO, source, licensee, expires)
    }
}
