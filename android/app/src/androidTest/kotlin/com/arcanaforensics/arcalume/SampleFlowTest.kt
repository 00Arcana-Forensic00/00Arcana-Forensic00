package com.arcanaforensics.arcalume

import androidx.compose.ui.test.ExperimentalTestApi
import androidx.compose.ui.test.enableAccessibilityChecks
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
        rule.waitUntil(120_000) { rule.onAllNodes(hasText("What Arcalume found and did")).fetchSemanticsNodes().isNotEmpty() }
        rule.onNodeWithText("glare spot", substring = true).assertExists()
        rule.onRoot().tryPerformAccessibilityChecks()
        rule.onNodeWithText("Show filled areas").performScrollTo().performClick()
        rule.onNodeWithText("Show reading order").performScrollTo().performClick()
        rule.onRoot().tryPerformAccessibilityChecks()
        rule.onNodeWithText("Seal as evidence").performScrollTo().performClick()   // free: the upgrade dialog
        rule.onNodeWithText("This is a Pro feature").assertExists()
        rule.onNodeWithText("See plans").performClick()
        rule.onRoot().tryPerformAccessibilityChecks()
        rule.onNodeWithText("Vault").performClick()
        rule.onNodeWithText("Check the log").performScrollTo().performClick()
        rule.onRoot().tryPerformAccessibilityChecks()
    }
}
