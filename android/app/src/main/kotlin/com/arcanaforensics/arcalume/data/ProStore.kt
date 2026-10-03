package com.arcanaforensics.arcalume.data

import android.app.Activity
import com.arcanaforensics.arcalume.core.Entitlements
import kotlinx.coroutines.flow.StateFlow

/** Where Pro comes from: Play Billing in the play build, a license key in the direct build. */
interface ProStore {
    val entitlements: StateFlow<Entitlements>

    /** Localized price, once known (Play build only). */
    val price: StateFlow<String?>

    /** A message for the user about the last purchase attempt, or null. */
    val notice: StateFlow<String?>

    val sellsInApp: Boolean
    val acceptsKeys: Boolean

    fun purchase(activity: Activity) {}
    fun restore() {}

    /** Returns null on success, or a message fit for the user. */
    fun activateKey(key: String): String? = "License keys are not used in this version."
    fun removeKey() {}
    fun clearNotice() {}
}
