package com.arcanaforensics.arcalume.ui

import android.app.Application
import androidx.compose.ui.test.assertHasClickAction
import androidx.compose.ui.test.assertIsOff
import androidx.compose.ui.test.junit4.createComposeRule
import androidx.compose.ui.test.assertCountEquals
import androidx.compose.ui.test.onAllNodesWithContentDescription
import androidx.compose.ui.test.onNodeWithContentDescription
import androidx.compose.ui.test.onNodeWithText
import androidx.compose.ui.test.performClick
import androidx.compose.ui.test.performTextInput
import androidx.test.ext.junit.runners.AndroidJUnit4
import com.arcanaforensics.arcalume.core.Entitlements
import com.arcanaforensics.arcalume.core.Finding
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNull
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith
import org.robolectric.annotation.Config

/** Screen behaviour on the JVM (Robolectric). The full flow on a device is in androidTest. */
@RunWith(AndroidJUnit4::class)
@Config(sdk = [35], application = Application::class)
class ScreensTest {
    @get:Rule val rule = createComposeRule()

    private fun actions(log: MutableList<String>) = RecoverActions(
        takePhoto = { log += "camera" }, choosePhotos = { log += "photos" }, chooseFiles = { log += "files" }, sample = { log += "sample" },
        select = {}, reprocess = { _, _ -> }, saveCopy = {}, seal = {}, remove = {},
    )

    @Test fun emptyStateOffersEveryWayIn() {
        val log = mutableListOf<String>()
        rule.setContent { ArcalumeTheme { EmptyState(actions(log)) } }
        for (label in listOf("Take photo", "Choose photos", "Choose files", "Try a sample page")) {
            rule.onNodeWithText(label).assertHasClickAction().performClick()
        }
        assertEquals(listOf("camera", "photos", "files", "sample"), log)
        rule.onNodeWithText("Everything stays on this phone", substring = true).assertExists()
    }

    @Test fun sealDialogExplainsEachProblem() {
        var sealed: String? = null
        rule.setContent { ArcalumeTheme { SealDialog(1, onSeal = { sealed = it }, onDismiss = {}) } }
        rule.onNodeWithText("Passphrase").performTextInput("too short")
        rule.onNodeWithText("Seal").performClick()
        rule.onNodeWithText("Use at least 12 characters.").assertExists()
        rule.onNodeWithText("Tick the box to confirm you understand.").assertExists()
        assertNull(sealed)
        rule.onNodeWithText("Passphrase").performTextInput(" but now long enough")
        rule.onNodeWithText("Repeat passphrase").performTextInput("something else entirely")
        rule.onNodeWithText("I understand", substring = true).performClick()
        rule.onNodeWithText("Seal").performClick()
        rule.onNodeWithText("The passphrases don't match.").assertExists()
        assertNull(sealed)
        rule.onAllNodesWithContentDescription("Show passphrase").assertCountEquals(2)
    }

    @Test fun findingsAreReadAsOneSentenceWithTheirLevel() {
        rule.setContent {
            ArcalumeTheme {
                FindingsCard(listOf(Finding(Finding.Level.WARN, "1 glare spot found."), Finding(Finding.Level.OK, "Lighting evened out.")))
            }
        }
        rule.onNodeWithContentDescription("Caution: 1 glare spot found.").assertExists()
        rule.onNodeWithContentDescription("Done: Lighting evened out.").assertExists()
    }

    @Test fun switchRowTogglesFromItsLabel() {
        var on = false
        rule.setContent { ArcalumeTheme { SwitchRow("Show filled areas", null, on) { on = it } } }
        rule.onNodeWithText("Show filled areas").assertIsOff().performClick()
        assertEquals(true, on)
    }

    @Test fun planShowsPurchaseOnlyWhereItIsSold() {
        rule.setContent {
            ArcalumeTheme {
                PlanScreen(Entitlements.FREE, "US$5.99", sellsInApp = true, acceptsKeys = false,
                    actions = PlanActions({}, {}, { null }, {}, {}))
            }
        }
        rule.onNodeWithText("Unlock Pro, US$5.99").assertHasClickAction()
        rule.onNodeWithText("License key").assertDoesNotExist()
    }

    @Test fun planShowsTheFreeOfferAndStillSellsPro() {
        rule.setContent {
            ArcalumeTheme {
                PlanScreen(Entitlements.pro(Entitlements.Source.TRIAL, expires = "2027-03-29"), "US$5.99", sellsInApp = true, acceptsKeys = false,
                    actions = PlanActions({}, {}, { null }, {}, {}), trialDaysLeft = 180)
            }
        }
        rule.onNodeWithText("Pro, free for 180 more days (until 2027-03-29)").assertExists()
        rule.onNodeWithText("Every new install gets Pro free for 180 days", substring = true).assertExists()
        rule.onNodeWithText("Unlock Pro, US$5.99").assertHasClickAction()
    }

    @Test fun planAcceptsKeysInTheDirectBuild() {
        rule.setContent {
            ArcalumeTheme {
                PlanScreen(Entitlements.pro(Entitlements.Source.KEY, "Ann Examiner"), null, sellsInApp = false, acceptsKeys = true,
                    actions = PlanActions({}, {}, { null }, {}, {}))
            }
        }
        rule.onNodeWithText("Pro, licensed to Ann Examiner").assertExists()
        rule.onNodeWithText("Remove key").assertHasClickAction()
        rule.onNodeWithText("Unlock Pro", substring = true).assertDoesNotExist()
    }
}
