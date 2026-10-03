package com.arcanaforensics.arcalume.data

import android.content.Context
import com.arcanaforensics.arcalume.Brand
import com.arcanaforensics.arcalume.core.Entitlements
import com.arcanaforensics.arcalume.core.Licensing
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import java.io.File

fun createProStore(context: Context): ProStore = KeyProStore(File(context.filesDir, "license.key"), Brand.LICENSE_PUBLIC_KEYS)

/** Direct build: Pro comes from an offline Ed25519 license key, the same keys as the desktop app. */
class KeyProStore(private val file: File, private val publicKeys: List<String>) : ProStore {
    private val state = MutableStateFlow(load())
    override val entitlements: StateFlow<Entitlements> = state
    override val price: StateFlow<String?> = MutableStateFlow(null)
    override val notice: StateFlow<String?> = MutableStateFlow(null)
    override val sellsInApp = false
    override val acceptsKeys = true

    private fun load(): Entitlements = try {
        Licensing.entitlementsFor(Licensing.verifyKey(file.readText(Charsets.US_ASCII).take(Licensing.MAX_KEY_CHARS + 2), publicKeys))
    } catch (e: Exception) {
        Entitlements.FREE
    }

    override fun activateKey(key: String): String? = try {
        val ent = Licensing.entitlementsFor(Licensing.verifyKey(key, publicKeys))
        val tmp = File(file.parentFile, file.name + ".tmp")
        tmp.writeText(key.filterNot { it.isWhitespace() } + "\n", Charsets.US_ASCII)
        tmp.renameTo(file)
        state.value = ent
        null
    } catch (e: Licensing.LicenseError) {
        e.message
    }

    override fun removeKey() {
        file.delete()
        state.value = Entitlements.FREE
    }
}
