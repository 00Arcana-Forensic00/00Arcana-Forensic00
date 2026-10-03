package com.arcanaforensics.arcalume.core

import java.io.File

object Fixtures {
    val dir = File(System.getProperty("fixtures") ?: "src/test/resources/fixtures")
    fun file(name: String) = File(dir, name)
    val desktop: Json.Obj by lazy { Json.parse(file("desktop.json").readBytes()).obj() }
    val engine: Json.Obj by lazy { Json.parse(file("engine.json").readBytes()).obj() }
    val FAST_KDF = Vault.Kdf(1, 16384, 1)

    /** Optional directory where tests leave artifacts for the Python side to verify. */
    val interopOut: File? = System.getenv("ARCALUME_INTEROP_OUT")?.let { File(it).apply { mkdirs() } }
}
