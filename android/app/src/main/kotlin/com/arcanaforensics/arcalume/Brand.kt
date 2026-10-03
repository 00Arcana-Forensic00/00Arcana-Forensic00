package com.arcanaforensics.arcalume

object Brand {
    const val NAME = "Arcalume"
    const val SUPPORT_URL = "https://arcana-forensics.com/arcalume/support"
    const val PRIVACY_URL = "https://arcana-forensics.com/arcalume/privacy"
    const val TERMS_URL = "https://arcana-forensics.com/arcalume/terms"

    /** Google Play one-time product that unlocks Pro (create it in Play Console with this id). */
    const val PRO_PRODUCT_ID = "arcalume_pro"

    /**
     * Play Console > Monetization setup > Licensing: the app's base64 RSA public key. When
     * set, purchase signatures are checked on the device. Empty until the app exists in
     * Play Console (see android/store/SUBMISSION.md).
     */
    const val PLAY_LICENSE_KEY = ""

    /** Ed25519 public keys for offline license keys (direct build). Same list as the desktop app. */
    val LICENSE_PUBLIC_KEYS: List<String> = emptyList()

    /** Long side, in pixels, that photos are recovered at. The original is always kept as-is. */
    const val WORK_MAX_SIDE = 3200

    /** Long side of the on-screen previews. */
    const val PREVIEW_MAX_SIDE = 2048

    const val MAX_INPUT_BYTES = 100 * 1024 * 1024

    const val TOOL = "Arcalume for Android " + BuildConfig.VERSION_NAME
}
