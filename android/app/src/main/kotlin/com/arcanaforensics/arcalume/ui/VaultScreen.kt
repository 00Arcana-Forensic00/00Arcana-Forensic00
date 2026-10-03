package com.arcanaforensics.arcalume.ui

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.FlowRow
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.heightIn
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.text.selection.SelectionContainer
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.CheckCircle
import androidx.compose.material.icons.filled.Error
import androidx.compose.material3.Button
import androidx.compose.material3.HorizontalDivider
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
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.semantics.LiveRegionMode
import androidx.compose.ui.semantics.liveRegion
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.unit.dp
import com.arcanaforensics.arcalume.R
import com.arcanaforensics.arcalume.data.EvidenceRepo
import java.text.DateFormat
import java.util.Date

class VaultActions(
    val open: (EvidenceRepo.VaultFile) -> Unit,
    val export: (EvidenceRepo.VaultFile) -> Unit,
    val delete: (EvidenceRepo.VaultFile) -> Unit,
    val verify: (String?) -> Unit,
    val exportLog: () -> Unit,
    val openFile: () -> Unit,
)

@Composable
fun VaultScreen(state: UiState, actions: VaultActions, modifier: Modifier = Modifier) {
    var expected by rememberSaveable { mutableStateOf("") }
    Column(modifier.fillMaxWidth().verticalScroll(rememberScrollState()).padding(16.dp), verticalArrangement = Arrangement.spacedBy(16.dp)) {
        Section(stringResource(R.string.vault_heading)) {
            if (state.vaults.isEmpty()) Text(stringResource(R.string.vault_empty))
            val fmt = DateFormat.getDateTimeInstance(DateFormat.MEDIUM, DateFormat.SHORT)
            state.vaults.forEachIndexed { i, v ->
                if (i > 0) HorizontalDivider()
                Column(Modifier.fillMaxWidth(), verticalArrangement = Arrangement.spacedBy(4.dp)) {
                    Text(stringResource(R.string.vault_item, v.file.name, fmt.format(Date(v.sealedMillis)), humanBytes(v.bytes)), style = MaterialTheme.typography.bodyMedium)
                    FlowRow(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                        OutlinedButton(onClick = { actions.open(v) }, modifier = Modifier.heightIn(min = 48.dp)) { Text(stringResource(R.string.open)) }
                        OutlinedButton(onClick = { actions.export(v) }, modifier = Modifier.heightIn(min = 48.dp)) { Text(stringResource(R.string.export)) }
                        TextButton(onClick = { actions.delete(v) }, modifier = Modifier.heightIn(min = 48.dp)) { Text(stringResource(R.string.delete)) }
                    }
                }
            }
        }

        Section(stringResource(R.string.log_heading)) {
            Text(stringResource(R.string.log_body), style = MaterialTheme.typography.bodyMedium)
            state.head?.let {
                Text(stringResource(R.string.log_head), style = MaterialTheme.typography.labelLarge)
                SelectionContainer { Mono(it) }
            }
            OutlinedTextField(
                value = expected, onValueChange = { expected = it.take(64) }, singleLine = true,
                label = { Text(stringResource(R.string.log_expected)) }, modifier = Modifier.fillMaxWidth(),
            )
            Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                Button(onClick = { actions.verify(expected) }, modifier = Modifier.heightIn(min = 48.dp)) { Text(stringResource(R.string.log_verify)) }
                OutlinedButton(onClick = actions.exportLog, enabled = state.log.isNotEmpty(), modifier = Modifier.heightIn(min = 48.dp)) { Text(stringResource(R.string.log_export)) }
            }
            state.check?.let { c -> CheckResult(c) }
            if (state.log.isEmpty()) Text(stringResource(R.string.log_empty))
            for (e in state.log.take(100)) {
                val event = when (e.event) {
                    "evidence_sealed" -> stringResource(R.string.event_evidence_sealed)
                    "rejected" -> stringResource(R.string.event_rejected)
                    "vault_deleted" -> stringResource(R.string.event_vault_deleted)
                    else -> e.event.replace('_', ' ')
                }
                HorizontalDivider()
                Text(
                    stringResource(R.string.log_entry, e.seq.toInt(), event, e.ts, e.sourceName?.let { "$it." } ?: "", e.hash.takeLast(8)),
                    style = MaterialTheme.typography.bodyMedium,
                    modifier = Modifier.fillMaxWidth().semantics(mergeDescendants = true) {},
                )
            }
        }

        Section(stringResource(R.string.open_file_heading)) {
            Text(stringResource(R.string.open_file_body), style = MaterialTheme.typography.bodyMedium)
            OutlinedButton(onClick = actions.openFile, modifier = Modifier.heightIn(min = 48.dp)) { Text(stringResource(R.string.open_file)) }
        }
    }
}

@Composable
private fun CheckResult(c: EvidenceRepo.Check) {
    val ok = c.result.ok
    val text = when {
        !ok -> stringResource(R.string.log_bad, c.result.message)
        c.matchedExpected -> stringResource(R.string.log_ok_expected, c.result.entries)
        c.matchedKnown -> stringResource(R.string.log_ok_known, c.result.entries)
        else -> stringResource(R.string.log_ok, c.result.entries)
    }
    Row(
        Modifier.fillMaxWidth().semantics(mergeDescendants = true) { liveRegion = if (ok) LiveRegionMode.Polite else LiveRegionMode.Assertive },
        horizontalArrangement = Arrangement.spacedBy(8.dp),
    ) {
        Icon(if (ok) Icons.Filled.CheckCircle else Icons.Filled.Error, contentDescription = null,
            tint = if (ok) MaterialTheme.colorScheme.primary else MaterialTheme.colorScheme.error)
        Text(text, style = MaterialTheme.typography.bodyLarge, color = if (ok) MaterialTheme.colorScheme.onSurface else MaterialTheme.colorScheme.error)
    }
}
