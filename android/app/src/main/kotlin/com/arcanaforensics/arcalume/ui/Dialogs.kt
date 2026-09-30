package com.arcanaforensics.arcalume.ui

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.heightIn
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.selection.toggleable
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.foundation.text.selection.SelectionContainer
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.CheckCircle
import androidx.compose.material.icons.filled.Visibility
import androidx.compose.material.icons.filled.VisibilityOff
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.Checkbox
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.autofill.ContentType
import androidx.compose.ui.platform.LocalClipboardManager
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.semantics.Role
import androidx.compose.ui.semantics.contentType
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.text.AnnotatedString
import androidx.compose.ui.text.input.ImeAction
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.text.input.PasswordVisualTransformation
import androidx.compose.ui.text.input.VisualTransformation
import androidx.compose.ui.unit.dp
import androidx.compose.ui.window.DialogProperties
import androidx.compose.ui.window.SecureFlagPolicy
import com.arcanaforensics.arcalume.R
import com.arcanaforensics.arcalume.core.Vault

/** Dialogs that handle passphrases are kept out of screenshots and the recent-apps preview. */
private val secure = DialogProperties(securePolicy = SecureFlagPolicy.SecureOn)

@Composable
fun PassphraseField(value: String, onChange: (String) -> Unit, label: String, error: String?, help: String?, newPassword: Boolean, last: Boolean, onDone: () -> Unit = {}) {
    var shown by remember { mutableStateOf(false) }
    OutlinedTextField(
        value = value, onValueChange = onChange, label = { Text(label) }, singleLine = true,
        isError = error != null,
        supportingText = (error ?: help)?.let { { Text(it) } },
        visualTransformation = if (shown) VisualTransformation.None else PasswordVisualTransformation(),
        keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Password, imeAction = if (last) ImeAction.Done else ImeAction.Next, autoCorrectEnabled = false),
        keyboardActions = androidx.compose.foundation.text.KeyboardActions(onDone = { onDone() }),
        trailingIcon = {
            IconButton(onClick = { shown = !shown }) {
                Icon(if (shown) Icons.Filled.VisibilityOff else Icons.Filled.Visibility,
                    contentDescription = stringResource(if (shown) R.string.hide_passphrase else R.string.show_passphrase))
            }
        },
        modifier = Modifier.fillMaxWidth().semantics { contentType = if (newPassword) ContentType.NewPassword else ContentType.Password },
    )
}

@Composable
fun SealDialog(count: Int, onSeal: (String) -> Unit, onDismiss: () -> Unit) {
    var p1 by remember { mutableStateOf("") }
    var p2 by remember { mutableStateOf("") }
    var ack by remember { mutableStateOf(false) }
    var tried by remember { mutableStateOf(false) }
    val min = Vault.MIN_PASSPHRASE_CHARS
    val shortErr = stringResource(R.string.passphrase_short, min)
    val mismatch = stringResource(R.string.passphrase_mismatch)
    val ackErr = stringResource(R.string.seal_ack_needed)
    val e1 = if (tried && p1.codePointCount(0, p1.length) < min) shortErr else null
    val e2 = if (tried && e1 == null && p1 != p2) mismatch else null
    val e3 = if (tried && !ack) ackErr else null
    fun go() {
        tried = true
        if (p1.codePointCount(0, p1.length) >= min && p1 == p2 && ack) { onSeal(p1); p1 = ""; p2 = "" }
    }
    AlertDialog(
        onDismissRequest = onDismiss, properties = secure,
        title = { Text(if (count > 1) stringResource(R.string.seal_all, count) else stringResource(R.string.seal_title)) },
        text = {
            Column(Modifier.verticalScroll(rememberScrollState()), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                Text(stringResource(R.string.seal_body))
                PassphraseField(p1, { p1 = it }, stringResource(R.string.passphrase), e1, stringResource(R.string.passphrase_help, min), newPassword = true, last = false)
                PassphraseField(p2, { p2 = it }, stringResource(R.string.passphrase_confirm), e2, null, newPassword = true, last = true, onDone = ::go)
                Row(
                    Modifier.fillMaxWidth().heightIn(min = 48.dp).toggleable(ack, role = Role.Checkbox) { ack = it },
                    verticalAlignment = Alignment.CenterVertically,
                ) {
                    Checkbox(checked = ack, onCheckedChange = null)
                    Text(stringResource(R.string.seal_ack), style = MaterialTheme.typography.bodyMedium, modifier = Modifier.weight(1f))
                }
                if (e3 != null) Text(e3, color = MaterialTheme.colorScheme.error, style = MaterialTheme.typography.bodyMedium)
            }
        },
        confirmButton = { TextButton(onClick = ::go, modifier = Modifier.heightIn(min = 48.dp)) { Text(stringResource(R.string.seal_go)) } },
        dismissButton = { TextButton(onClick = onDismiss, modifier = Modifier.heightIn(min = 48.dp)) { Text(stringResource(R.string.cancel)) } },
    )
}

@Composable
fun SealedDialog(outcome: SealOutcome, onCopied: () -> Unit, onExport: (java.io.File) -> Unit, onDismiss: () -> Unit) {
    val clipboard = LocalClipboardManager.current
    AlertDialog(
        onDismissRequest = onDismiss,
        icon = { Icon(Icons.Filled.CheckCircle, contentDescription = null) },
        title = { Text(stringResource(R.string.sealed_title)) },
        text = {
            Column(Modifier.verticalScroll(rememberScrollState()), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                Text(stringResource(R.string.sealed_body, outcome.names.joinToString(", ")))
                SelectionContainer { Mono(outcome.head) }
                Text(stringResource(R.string.sealed_keep), style = MaterialTheme.typography.bodyMedium)
                OutlinedButton(onClick = { clipboard.setText(AnnotatedString(outcome.head)); onCopied() }, modifier = Modifier.fillMaxWidth().heightIn(min = 48.dp)) {
                    Text(stringResource(R.string.copy_fingerprint))
                }
                if (outcome.vaults.size == 1) {
                    OutlinedButton(onClick = { onExport(outcome.vaults.single()) }, modifier = Modifier.fillMaxWidth().heightIn(min = 48.dp)) {
                        Text(stringResource(R.string.export_vault))
                    }
                }
            }
        },
        confirmButton = { TextButton(onClick = onDismiss, modifier = Modifier.heightIn(min = 48.dp)) { Text(stringResource(R.string.done)) } },
    )
}

@Composable
fun UpgradeDialog(onPlans: () -> Unit, onDismiss: () -> Unit) {
    AlertDialog(
        onDismissRequest = onDismiss,
        title = { Text(stringResource(R.string.upgrade_title)) },
        text = { Text(stringResource(R.string.upgrade_body)) },
        confirmButton = { TextButton(onClick = onPlans, modifier = Modifier.heightIn(min = 48.dp)) { Text(stringResource(R.string.see_plans)) } },
        dismissButton = { TextButton(onClick = onDismiss, modifier = Modifier.heightIn(min = 48.dp)) { Text(stringResource(R.string.not_now)) } },
    )
}

@Composable
fun OpenVaultDialog(fileName: String, wrong: Boolean, onOpen: (String) -> Unit, onDismiss: () -> Unit) {
    var p by remember { mutableStateOf("") }
    val err = if (wrong) stringResource(R.string.open_wrong) else null
    AlertDialog(
        onDismissRequest = onDismiss, properties = secure,
        title = { Text(stringResource(R.string.open_title)) },
        text = {
            Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                Text(fileName, style = MaterialTheme.typography.bodyMedium)
                PassphraseField(p, { p = it }, stringResource(R.string.passphrase), err, null, newPassword = false, last = true, onDone = { onOpen(p) })
            }
        },
        confirmButton = { TextButton(onClick = { onOpen(p) }, enabled = p.isNotEmpty(), modifier = Modifier.heightIn(min = 48.dp)) { Text(stringResource(R.string.open_go)) } },
        dismissButton = { TextButton(onClick = onDismiss, modifier = Modifier.heightIn(min = 48.dp)) { Text(stringResource(R.string.cancel)) } },
    )
}

@Composable
fun OpenedDialog(v: OpenedVault, onSave: (role: String) -> Unit, onDismiss: () -> Unit) {
    AlertDialog(
        onDismissRequest = onDismiss, properties = secure,
        icon = { Icon(Icons.Filled.CheckCircle, contentDescription = null) },
        title = { Text(stringResource(R.string.opened_title)) },
        text = {
            Column(Modifier.verticalScroll(rememberScrollState()), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                Text(stringResource(R.string.opened_intact, v.entries.size))
                Text(stringResource(R.string.opened_source, v.sourceName))
                Text(stringResource(R.string.opened_created, v.created, v.tool))
                if (v.status.isNotEmpty()) Text(stringResource(R.string.opened_status, v.status.replace('_', ' ')))
                for ((role, label) in listOf("original" to R.string.save_original, "restored" to R.string.save_recovered, "mask" to R.string.save_mask, "manifest" to R.string.save_manifest)) {
                    if (role in v.entries) {
                        OutlinedButton(onClick = { onSave(role) }, modifier = Modifier.fillMaxWidth().heightIn(min = 48.dp)) { Text(stringResource(label)) }
                    }
                }
            }
        },
        confirmButton = { TextButton(onClick = onDismiss, modifier = Modifier.heightIn(min = 48.dp)) { Text(stringResource(R.string.done)) } },
    )
}

@Composable
fun ConfirmDialog(title: String, body: String, confirm: String, onConfirm: () -> Unit, onDismiss: () -> Unit) {
    AlertDialog(
        onDismissRequest = onDismiss,
        title = { Text(title) }, text = { Text(body) },
        confirmButton = { TextButton(onClick = onConfirm, modifier = Modifier.heightIn(min = 48.dp)) { Text(confirm) } },
        dismissButton = { TextButton(onClick = onDismiss, modifier = Modifier.heightIn(min = 48.dp)) { Text(stringResource(R.string.cancel)) } },
    )
}
