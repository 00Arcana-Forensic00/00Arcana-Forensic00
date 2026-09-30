package com.arcanaforensics.arcalume.ui

import android.app.Activity
import android.content.Intent
import android.net.Uri
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.PickVisualMediaRequest
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.AutoFixHigh
import androidx.compose.material.icons.filled.Lock
import androidx.compose.material.icons.filled.WorkspacePremium
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.NavigationBar
import androidx.compose.material3.NavigationBarItem
import androidx.compose.material3.Scaffold
import androidx.compose.material3.SnackbarHost
import androidx.compose.material3.SnackbarHostState
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.material3.TopAppBar
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.semantics.LiveRegionMode
import androidx.compose.ui.semantics.liveRegion
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.unit.dp
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import com.arcanaforensics.arcalume.Brand
import com.arcanaforensics.arcalume.R
import com.arcanaforensics.arcalume.core.Evidence
import com.arcanaforensics.arcalume.data.EvidenceRepo
import com.arcanaforensics.arcalume.data.Page
import java.io.File

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun ArcalumeRoot(vm: AppViewModel) {
    val ui by vm.ui.collectAsStateWithLifecycle()
    val ent by vm.pro.entitlements.collectAsStateWithLifecycle()
    val price by vm.pro.price.collectAsStateWithLifecycle()
    val proNotice by vm.pro.notice.collectAsStateWithLifecycle()
    val message by vm.message.collectAsStateWithLifecycle()
    val context = LocalContext.current
    val snackbar = remember { SnackbarHostState() }

    var camera by rememberSaveable { mutableStateOf(false) }
    var sealing by remember { mutableStateOf<List<Page>?>(null) }
    var upgrade by rememberSaveable { mutableStateOf(false) }
    var opening by remember { mutableStateOf<Pair<String, ByteArray>?>(null) }
    var wrongPass by remember { mutableStateOf(false) }
    var deleting by remember { mutableStateOf<EvidenceRepo.VaultFile?>(null) }
    // What the next "create document" result should be written from.
    var pendingSave by remember { mutableStateOf<((Uri) -> Unit)?>(null) }

    LaunchedEffect(ui.opened) { if (ui.opened != null) opening = null }
    LaunchedEffect(message) { message?.let { snackbar.showSnackbar(it); vm.said() } }
    LaunchedEffect(proNotice) { proNotice?.let { snackbar.showSnackbar(it); vm.pro.clearNotice() } }

    val pickPhotos = rememberLauncherForActivityResult(ActivityResultContracts.PickMultipleVisualMedia(20)) { if (it.isNotEmpty()) vm.importUris(it) }
    val pickFiles = rememberLauncherForActivityResult(ActivityResultContracts.OpenMultipleDocuments()) { if (it.isNotEmpty()) vm.importUris(it) }
    val pickVault = rememberLauncherForActivityResult(ActivityResultContracts.OpenDocument()) { uri ->
        if (uri != null) {
            val bytes = vm.readUri(uri)
            if (bytes == null) vm.say(context.getString(R.string.read_failed, uri.lastPathSegment ?: "file", "unreadable")) else { wrongPass = false; opening = (uri.lastPathSegment?.substringAfterLast('/') ?: "vault") to bytes }
        }
    }
    val createPng = rememberLauncherForActivityResult(ActivityResultContracts.CreateDocument("image/png")) { uri -> uri?.let { pendingSave?.invoke(it) }; pendingSave = null }
    val createBin = rememberLauncherForActivityResult(ActivityResultContracts.CreateDocument("application/octet-stream")) { uri -> uri?.let { pendingSave?.invoke(it) }; pendingSave = null }
    val createJson = rememberLauncherForActivityResult(ActivityResultContracts.CreateDocument("application/json")) { uri -> uri?.let { pendingSave?.invoke(it) }; pendingSave = null }
    val createText = rememberLauncherForActivityResult(ActivityResultContracts.CreateDocument("text/plain")) { uri -> uri?.let { pendingSave?.invoke(it) }; pendingSave = null }

    fun exportVault(f: File) { pendingSave = { vm.exportFile(f, it) }; createBin.launch(f.name) }
    val choosePhotos = { pickPhotos.launch(PickVisualMediaRequest(ActivityResultContracts.PickVisualMedia.ImageOnly)) }

    if (camera) {
        CameraScreen(
            onCaptured = { camera = false; vm.captured(it) },
            onChoosePhotos = { camera = false; choosePhotos() },
            onClose = { camera = false },
            onError = { vm.say(it) },
        )
        return
    }

    val recoverActions = RecoverActions(
        takePhoto = { camera = true },
        choosePhotos = choosePhotos,
        chooseFiles = { pickFiles.launch(arrayOf("image/*")) },
        sample = vm::loadSample,
        select = vm::show,
        reprocess = vm::reprocess,
        saveCopy = { page -> pendingSave = { vm.saveCopy(page, it) }; createPng.launch(Evidence.safeName(page.name).substringBeforeLast('.') + "-recovered.png") },
        seal = { pages -> if (ent.seal) sealing = pages else upgrade = true },
        remove = vm::remove,
    )
    val vaultActions = VaultActions(
        open = { v -> wrongPass = false; opening = v.file.name to v.file.readBytes() },
        export = { v -> exportVault(v.file) },
        delete = { v -> deleting = v },
        verify = vm::verify,
        exportLog = { pendingSave = { vm.exportFile(vm.repo.ledgerFile, it) }; createText.launch("arcalume-custody-log.jsonl") },
        openFile = { pickVault.launch(arrayOf("*/*")) },
    )
    val planActions = PlanActions(
        buy = { (context as? Activity)?.let { vm.pro.purchase(it) } },
        restore = vm.pro::restore,
        activate = vm.pro::activateKey,
        removeKey = vm.pro::removeKey,
        support = { runCatching { context.startActivity(Intent(Intent.ACTION_VIEW, Uri.parse(Brand.SUPPORT_URL))) } },
    )

    Scaffold(
        topBar = {
            TopAppBar(title = {
                Column {
                    Text(stringResource(R.string.app_name))
                    Text(stringResource(R.string.app_subtitle), style = MaterialTheme.typography.labelMedium, color = MaterialTheme.colorScheme.onSurfaceVariant)
                }
            })
        },
        bottomBar = {
            NavigationBar {
                for ((tab, label, icon) in listOf(
                    Triple(Tab.RECOVER, R.string.tab_recover, Icons.Filled.AutoFixHigh),
                    Triple(Tab.VAULT, R.string.tab_vault, Icons.Filled.Lock),
                    Triple(Tab.PLAN, R.string.tab_plan, Icons.Filled.WorkspacePremium),
                )) {
                    NavigationBarItem(selected = ui.tab == tab, onClick = { vm.select(tab) }, icon = { Icon(icon, contentDescription = null) }, label = { Text(stringResource(label)) })
                }
            }
        },
        snackbarHost = { SnackbarHost(snackbar) },
    ) { inner ->
        Box(Modifier.fillMaxSize().padding(inner)) {
            when (ui.tab) {
                Tab.RECOVER -> {
                    val page = ui.current
                    if (page == null) EmptyState(recoverActions) else ReviewScreen(ui.pages, page, ent.cleanExport, recoverActions)
                }
                Tab.VAULT -> VaultScreen(ui, vaultActions)
                Tab.PLAN -> PlanScreen(ent, price, vm.pro.sellsInApp, vm.pro.acceptsKeys, planActions)
            }
            ui.busy?.let { BusyOverlay(it) }
        }
    }

    sealing?.let { pages -> SealDialog(pages.size, onSeal = { pass -> sealing = null; vm.seal(pages, pass) }, onDismiss = { sealing = null }) }
    ui.sealed?.let { SealedDialog(it, onCopied = { vm.say(context.getString(R.string.copied)) }, onExport = ::exportVault, onDismiss = vm::dismissSealed) }
    if (upgrade) UpgradeDialog(onPlans = { upgrade = false; vm.select(Tab.PLAN) }, onDismiss = { upgrade = false })
    opening?.let { (name, bytes) ->
        OpenVaultDialog(name, wrongPass, onOpen = { pass -> wrongPass = false; vm.openVault(bytes, pass) { wrongPass = true } }, onDismiss = { opening = null })
    }
    ui.opened?.let { v ->
        OpenedDialog(v, onSave = { role ->
            val base = Evidence.safeName(v.sourceName).substringBeforeLast('.')
            val bytes = v.entries.getValue(role)
            pendingSave = { vm.exportBytes(bytes, it) }
            when (role) {
                "manifest" -> createJson.launch("$base.manifest.json")
                "original" -> createBin.launch("$base.original." + Evidence.safeName(v.sourceName).substringAfterLast('.', "bin"))
                else -> createPng.launch("$base.$role.png")
            }
        }, onDismiss = vm::closeOpened)
    }
    deleting?.let { v ->
        ConfirmDialog(stringResource(R.string.delete_title), stringResource(R.string.delete_body, v.file.name), stringResource(R.string.delete),
            onConfirm = { deleting = null; vm.deleteVault(v) }, onDismiss = { deleting = null })
    }
}

@Composable
private fun BusyOverlay(text: String) {
    Surface(Modifier.fillMaxSize(), color = MaterialTheme.colorScheme.background.copy(alpha = 0.85f)) {
        Row(
            Modifier.fillMaxWidth().padding(24.dp).semantics(mergeDescendants = true) { liveRegion = LiveRegionMode.Polite },
            horizontalArrangement = Arrangement.spacedBy(16.dp, Alignment.CenterHorizontally),
            verticalAlignment = Alignment.CenterVertically,
        ) {
            CircularProgressIndicator()
            Text(text, style = MaterialTheme.typography.bodyLarge)
        }
    }
}
