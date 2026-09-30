package com.arcanaforensics.arcalume.ui

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.heightIn
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Check
import androidx.compose.material3.Button
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.res.pluralStringResource
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.unit.dp
import com.arcanaforensics.arcalume.BuildConfig
import com.arcanaforensics.arcalume.R
import com.arcanaforensics.arcalume.core.Entitlements

class PlanActions(
    val buy: () -> Unit,
    val restore: () -> Unit,
    val activate: (String) -> String?,
    val removeKey: () -> Unit,
    val support: () -> Unit,
)

@Composable
fun PlanScreen(ent: Entitlements, price: String?, sellsInApp: Boolean, acceptsKeys: Boolean, actions: PlanActions, modifier: Modifier = Modifier, trialDaysLeft: Int = 0) {
    var key by rememberSaveable { mutableStateOf("") }
    var keyError by rememberSaveable { mutableStateOf<String?>(null) }
    var showLicenses by rememberSaveable { mutableStateOf(false) }
    val pro = ent.plan == Entitlements.Plan.PRO
    val trial = ent.source == Entitlements.Source.TRIAL
    val owned = pro && !trial
    Column(modifier.fillMaxWidth().verticalScroll(rememberScrollState()).padding(16.dp), verticalArrangement = Arrangement.spacedBy(16.dp)) {
        Section(stringResource(R.string.plan_heading)) {
            Text(
                when {
                    !pro -> stringResource(R.string.plan_free)
                    trial -> pluralStringResource(R.plurals.plan_trial, trialDaysLeft, trialDaysLeft, ent.expires ?: "")
                    ent.source == Entitlements.Source.PLAY -> stringResource(R.string.plan_pro_from_play)
                    ent.licensee.isNotEmpty() -> stringResource(R.string.plan_pro_licensed, ent.licensee)
                    else -> stringResource(R.string.plan_pro)
                },
                style = MaterialTheme.typography.titleLarge,
            )
            if (trial) Text(stringResource(R.string.trial_after), style = MaterialTheme.typography.bodyMedium)
            Text(stringResource(R.string.free_includes), style = MaterialTheme.typography.bodyMedium)
            Heading(stringResource(R.string.pro_adds))
            for (s in listOf(R.string.pro_clean, R.string.pro_seal, R.string.pro_batch, R.string.pro_once)) {
                Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                    Icon(Icons.Filled.Check, contentDescription = null, tint = MaterialTheme.colorScheme.primary)
                    Text(stringResource(s), style = MaterialTheme.typography.bodyMedium)
                }
            }
            if (sellsInApp && !owned) {
                Button(onClick = actions.buy, modifier = Modifier.fillMaxWidth().heightIn(min = 56.dp)) {
                    Text(if (price != null) stringResource(R.string.buy, price) else stringResource(R.string.buy_unpriced))
                }
            }
            if (sellsInApp) {
                TextButton(onClick = actions.restore, modifier = Modifier.heightIn(min = 48.dp)) { Text(stringResource(R.string.restore_purchase)) }
            }
            if (acceptsKeys) {
                if (!owned || ent.source == Entitlements.Source.KEY) {
                    OutlinedTextField(
                        value = key, onValueChange = { key = it; keyError = null }, label = { Text(stringResource(R.string.license_key)) },
                        isError = keyError != null, supportingText = keyError?.let { { Text(it) } }, minLines = 2,
                        modifier = Modifier.fillMaxWidth(),
                    )
                    Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                        Button(onClick = { keyError = actions.activate(key); if (keyError == null) key = "" }, enabled = key.isNotBlank(), modifier = Modifier.heightIn(min = 48.dp)) {
                            Text(stringResource(R.string.activate))
                        }
                        if (ent.source == Entitlements.Source.KEY) OutlinedButton(onClick = actions.removeKey, modifier = Modifier.heightIn(min = 48.dp)) { Text(stringResource(R.string.remove_key)) }
                    }
                }
            }
        }

        Section(stringResource(R.string.limits_heading)) {
            for (s in listOf(R.string.limit_1, R.string.limit_2, R.string.limit_3)) Text(stringResource(s), style = MaterialTheme.typography.bodyMedium)
        }

        Section(stringResource(R.string.about_heading)) {
            Text(stringResource(R.string.about_version, BuildConfig.VERSION_NAME))
            Text(stringResource(R.string.about_privacy), style = MaterialTheme.typography.bodyMedium)
            OutlinedButton(onClick = actions.support, modifier = Modifier.heightIn(min = 48.dp)) { Text(stringResource(R.string.support)) }
            TextButton(onClick = { showLicenses = !showLicenses }, modifier = Modifier.heightIn(min = 48.dp)) { Text(stringResource(R.string.licenses)) }
            if (showLicenses) Text(stringResource(R.string.licenses_body), style = MaterialTheme.typography.bodyMedium)
        }
    }
}
