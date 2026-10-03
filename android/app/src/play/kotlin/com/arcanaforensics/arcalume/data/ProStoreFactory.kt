package com.arcanaforensics.arcalume.data

import android.app.Activity
import android.content.Context
import android.util.Base64
import com.android.billingclient.api.AcknowledgePurchaseParams
import com.android.billingclient.api.BillingClient
import com.android.billingclient.api.BillingClientStateListener
import com.android.billingclient.api.BillingFlowParams
import com.android.billingclient.api.BillingResult
import com.android.billingclient.api.PendingPurchasesParams
import com.android.billingclient.api.ProductDetails
import com.android.billingclient.api.Purchase
import com.android.billingclient.api.QueryProductDetailsParams
import com.android.billingclient.api.QueryPurchasesParams
import com.arcanaforensics.arcalume.Brand
import com.arcanaforensics.arcalume.core.Entitlements
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import java.security.KeyFactory
import java.security.Signature
import java.security.spec.X509EncodedKeySpec

fun createProStore(context: Context): ProStore = PlayProStore(context.applicationContext)

/**
 * Play build: Pro is a one-time in-app product bought through Google Play Billing.
 * Billing talks to the Play Store app over IPC; Arcalume itself still has no network
 * permission. Ownership is re-read from Play on every launch, and is cached so Pro keeps
 * working offline.
 */
class PlayProStore(private val context: Context) : ProStore {
    private val prefs = context.getSharedPreferences("plan", Context.MODE_PRIVATE)
    private val state = MutableStateFlow(if (prefs.getBoolean("pro", false)) Entitlements.pro(Entitlements.Source.PLAY) else Entitlements.FREE)
    private val priceState = MutableStateFlow<String?>(null)
    private val noticeState = MutableStateFlow<String?>(null)
    override val entitlements: StateFlow<Entitlements> = state
    override val price: StateFlow<String?> = priceState
    override val notice: StateFlow<String?> = noticeState
    override val sellsInApp = true
    override val acceptsKeys = false

    private var details: ProductDetails? = null

    private val client: BillingClient = BillingClient.newBuilder(context)
        .setListener { result, purchases -> if (result.responseCode == BillingClient.BillingResponseCode.OK) handle(purchases.orEmpty()) else report(result) }
        .enablePendingPurchases(PendingPurchasesParams.newBuilder().enableOneTimeProducts().build())
        .build()

    // The launch-time connection is silent: a phone without Google Play (or offline) should not
    // greet the user with a store error. Failures are reported when they tap buy or restore.
    init { connect(quiet = true) }

    private fun connect(quiet: Boolean = false, then: (() -> Unit)? = null) {
        if (client.isReady) { then?.invoke(); return }
        client.startConnection(object : BillingClientStateListener {
            override fun onBillingSetupFinished(result: BillingResult) {
                if (result.responseCode != BillingClient.BillingResponseCode.OK) { if (!quiet) report(result); return }
                queryDetails()
                restore()
                then?.invoke()
            }
            override fun onBillingServiceDisconnected() {}
        })
    }

    private fun queryDetails() {
        val params = QueryProductDetailsParams.newBuilder().setProductList(listOf(
            QueryProductDetailsParams.Product.newBuilder().setProductId(Brand.PRO_PRODUCT_ID).setProductType(BillingClient.ProductType.INAPP).build(),
        )).build()
        client.queryProductDetailsAsync(params) { result, res ->
            if (result.responseCode == BillingClient.BillingResponseCode.OK) {
                details = res.productDetailsList.firstOrNull()
                @Suppress("DEPRECATION")
                priceState.value = details?.oneTimePurchaseOfferDetails?.formattedPrice
            }
        }
    }

    override fun restore() {
        if (!client.isReady) { connect(); return }
        client.queryPurchasesAsync(QueryPurchasesParams.newBuilder().setProductType(BillingClient.ProductType.INAPP).build()) { result, purchases ->
            if (result.responseCode == BillingClient.BillingResponseCode.OK) {
                val owned = purchases.any { owns(it) }
                setPro(owned)
                handle(purchases)
            }
        }
    }

    override fun purchase(activity: Activity) {
        val pd = details
        if (pd == null) { connect { queryDetails() }; noticeState.value = "The store isn't ready yet. Try again in a moment."; return }
        val flow = BillingFlowParams.newBuilder().setProductDetailsParamsList(listOf(
            BillingFlowParams.ProductDetailsParams.newBuilder().setProductDetails(pd).build(),
        )).build()
        val result = client.launchBillingFlow(activity, flow)
        if (result.responseCode != BillingClient.BillingResponseCode.OK) report(result)
    }

    override fun clearNotice() { noticeState.value = null }

    private fun owns(p: Purchase) = Brand.PRO_PRODUCT_ID in p.products && p.purchaseState == Purchase.PurchaseState.PURCHASED && signatureOk(p)

    private fun handle(purchases: List<Purchase>) {
        for (p in purchases) {
            if (Brand.PRO_PRODUCT_ID !in p.products) continue
            when (p.purchaseState) {
                Purchase.PurchaseState.PURCHASED -> if (signatureOk(p)) {
                    setPro(true)
                    if (!p.isAcknowledged) {
                        client.acknowledgePurchase(AcknowledgePurchaseParams.newBuilder().setPurchaseToken(p.purchaseToken).build()) { }
                    }
                }
                Purchase.PurchaseState.PENDING -> noticeState.value = "Your payment is pending. Pro unlocks when Google Play confirms it."
                else -> {}
            }
        }
    }

    private fun setPro(pro: Boolean) {
        prefs.edit().putBoolean("pro", pro).apply()
        state.value = if (pro) Entitlements.pro(Entitlements.Source.PLAY) else Entitlements.FREE
    }

    private fun report(result: BillingResult) {
        when (result.responseCode) {
            BillingClient.BillingResponseCode.USER_CANCELED -> {}
            BillingClient.BillingResponseCode.ITEM_ALREADY_OWNED -> restore()
            else -> noticeState.value = "Google Play purchases aren't available right now: ${result.debugMessage.ifEmpty { "code ${result.responseCode}" }}"
        }
    }

    /** RSA-SHA1 check of the purchase data against the app's Play licensing key, when configured. */
    private fun signatureOk(p: Purchase): Boolean {
        if (Brand.PLAY_LICENSE_KEY.isEmpty()) return true
        return try {
            val key = KeyFactory.getInstance("RSA").generatePublic(X509EncodedKeySpec(Base64.decode(Brand.PLAY_LICENSE_KEY, Base64.DEFAULT)))
            Signature.getInstance("SHA1withRSA").run {
                initVerify(key)
                update(p.originalJson.toByteArray(Charsets.UTF_8))
                verify(Base64.decode(p.signature, Base64.DEFAULT))
            }
        } catch (e: Exception) {
            false
        }
    }
}
