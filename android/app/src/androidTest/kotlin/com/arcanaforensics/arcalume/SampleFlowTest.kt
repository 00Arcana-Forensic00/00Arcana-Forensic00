package com.arcanaforensics.arcalume

import androidx.compose.ui.semantics.SemanticsProperties
import androidx.compose.ui.semantics.getOrNull
import androidx.compose.ui.test.ComposeTimeoutException
import androidx.compose.ui.test.ExperimentalTestApi
import androidx.compose.ui.test.SemanticsMatcher
import androidx.compose.ui.test.junit4.accessibility.enableAccessibilityChecks
import androidx.compose.ui.test.hasText
import androidx.compose.ui.test.junit4.createAndroidComposeRule
import androidx.compose.ui.test.onNodeWithText
import androidx.compose.ui.test.onRoot
import androidx.compose.ui.test.performClick
import androidx.compose.ui.test.performScrollTo
import androidx.compose.ui.test.tryPerformAccessibilityChecks
import androidx.test.ext.junit.runners.AndroidJUnit4
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith

/**
 * On a real device or emulator: the sample page goes through the real OpenCV engine,
 * and every screen passes the Accessibility Test Framework checks (labels, touch target
 * size, contrast, duplicate descriptions) that Google's Accessibility Scanner uses.
 */
@OptIn(ExperimentalTestApi::class)
@RunWith(AndroidJUnit4::class)
class SampleFlowTest {
    @get:Rule val rule = createAndroidComposeRule<MainActivity>()

    @Test fun sampleRecoversAndEveryScreenPassesAccessibilityChecks() {
        rule.enableAccessibilityChecks()
        rule.onRoot().tryPerformAccessibilityChecks()
        rule.onNodeWithText("Try a sample page").performScrollTo().performClick()
        awaitText("What Arcalume found and did")
        rule.onNodeWithText("glare spot", substring = true, useUnmergedTree = true).assertExists()
        rule.onRoot().tryPerformAccessibilityChecks()
        rule.onNodeWithText("Show filled areas").performScrollTo().performClick()
        rule.onNodeWithText("Show reading order").performScrollTo().performClick()
        rule.onRoot().tryPerformAccessibilityChecks()
        rule.onNodeWithText("Plan").performClick()   // a new install is inside the 180-day free Pro offer
        rule.onNodeWithText("Pro, free for 180 more days", substring = true).assertExists()
        rule.onRoot().tryPerformAccessibilityChecks()
        rule.onNodeWithText("Vault").performClick()
        rule.onNodeWithText("Check the log").performScrollTo().performClick()
        rule.onRoot().tryPerformAccessibilityChecks()
    }

    /**
     * Waits for [text]. On timeout, fails listing every text that appeared while waiting,
     * so a brief error snackbar or a stuck progress label shows up in the report.
     */
    private fun awaitText(text: String, timeoutMs: Long = 180_000) {
        val seen = linkedSetOf<String>()
        try {
            rule.waitUntil(timeoutMs) {
                rule.onAllNodes(SemanticsMatcher("any node") { true }, useUnmergedTree = true).fetchSemanticsNodes()
                    .flatMap { n -> n.config.getOrNull(SemanticsProperties.Text).orEmpty().map { it.text } }
                    .forEach { seen += it }
                rule.onAllNodes(hasText(text)).fetchSemanticsNodes().isNotEmpty()
            }
        } catch (e: ComposeTimeoutException) {
            throw AssertionError("\"$text\" did not appear within ${timeoutMs / 1000} s. Seen while waiting: $seen", e)
        }
    }
}
