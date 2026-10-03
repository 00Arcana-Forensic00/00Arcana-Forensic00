package com.arcanaforensics.arcalume.ui

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.FlowRow
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.heightIn
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.text.selection.SelectionContainer
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Add
import androidx.compose.material.icons.filled.AutoAwesome
import androidx.compose.material.icons.filled.CheckCircle
import androidx.compose.material.icons.filled.Delete
import androidx.compose.material.icons.filled.Info
import androidx.compose.material.icons.filled.Lock
import androidx.compose.material.icons.filled.PhotoCamera
import androidx.compose.material.icons.filled.PhotoLibrary
import androidx.compose.material.icons.filled.Save
import androidx.compose.material.icons.filled.Warning
import androidx.compose.material.icons.filled.ZoomIn
import androidx.compose.material.icons.filled.ZoomOut
import androidx.compose.material.icons.filled.FitScreen
import androidx.compose.material.icons.filled.FolderOpen
import androidx.compose.material3.Button
import androidx.compose.material3.FilledTonalButton
import androidx.compose.material3.FilterChip
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.SegmentedButton
import androidx.compose.material3.SegmentedButtonDefaults
import androidx.compose.material3.SingleChoiceSegmentedButtonRow
import androidx.compose.material3.Slider
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableFloatStateOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.semantics.CustomAccessibilityAction
import androidx.compose.ui.semantics.clearAndSetSemantics
import androidx.compose.ui.semantics.contentDescription
import androidx.compose.ui.semantics.customActions
import androidx.compose.ui.semantics.heading
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.semantics.stateDescription
import androidx.compose.ui.unit.dp
import com.arcanaforensics.arcalume.R
import com.arcanaforensics.arcalume.core.Finding
import com.arcanaforensics.arcalume.core.Findings
import com.arcanaforensics.arcalume.core.Json
import com.arcanaforensics.arcalume.core.Node
import com.arcanaforensics.arcalume.core.RepairConfig
import com.arcanaforensics.arcalume.core.Report
import com.arcanaforensics.arcalume.data.Page
import com.arcanaforensics.arcalume.data.Source
import kotlin.math.roundToInt

class RecoverActions(
    val takePhoto: () -> Unit,
    val choosePhotos: () -> Unit,
    val chooseFiles: () -> Unit,
    val sample: () -> Unit,
    val select: (Page) -> Unit,
    val reprocess: (Page, RepairConfig) -> Unit,
    val saveCopy: (Page) -> Unit,
    val seal: (List<Page>) -> Unit,
    val remove: (Page) -> Unit,
)

@Composable
fun EmptyState(actions: RecoverActions, modifier: Modifier = Modifier) {
    Column(modifier.fillMaxWidth().verticalScroll(rememberScrollState()).padding(24.dp), verticalArrangement = Arrangement.spacedBy(16.dp)) {
        Text(stringResource(R.string.empty_title), style = MaterialTheme.typography.headlineSmall, modifier = Modifier.semantics { heading() })
        Text(stringResource(R.string.empty_body), style = MaterialTheme.typography.bodyLarge)
        BigButton(Icons.Filled.PhotoCamera, stringResource(R.string.take_photo), primary = true, onClick = actions.takePhoto)
        BigButton(Icons.Filled.PhotoLibrary, stringResource(R.string.choose_photos), onClick = actions.choosePhotos)
        BigButton(Icons.Filled.FolderOpen, stringResource(R.string.choose_files), onClick = actions.chooseFiles)
        BigButton(Icons.Filled.AutoAwesome, stringResource(R.string.try_sample), onClick = actions.sample)
        Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
            Icon(Icons.Filled.Lock, contentDescription = null, tint = MaterialTheme.colorScheme.primary)
            Text(stringResource(R.string.privacy_line), style = MaterialTheme.typography.bodyMedium, color = MaterialTheme.colorScheme.onSurfaceVariant)
        }
    }
}

@Composable
private fun BigButton(icon: androidx.compose.ui.graphics.vector.ImageVector, text: String, primary: Boolean = false, onClick: () -> Unit) {
    val m = Modifier.fillMaxWidth().heightIn(min = 56.dp)
    val content: @Composable androidx.compose.foundation.layout.RowScope.() -> Unit = {
        Icon(icon, contentDescription = null)
        Spacer(Modifier.width(12.dp))
        Text(text, style = MaterialTheme.typography.titleMedium)
    }
    if (primary) Button(onClick, m, content = content) else FilledTonalButton(onClick, m, content = content)
}

@Composable
fun ReviewScreen(pages: List<Page>, page: Page, isPro: Boolean, actions: RecoverActions, modifier: Modifier = Modifier) {
    var mode by rememberSaveable { mutableStateOf(ViewMode.COMPARE) }
    var split by rememberSaveable { mutableFloatStateOf(0.5f) }
    var showMask by rememberSaveable { mutableStateOf(false) }
    var showOrder by rememberSaveable { mutableStateOf(false) }
    var zoom by remember(page.id) { mutableFloatStateOf(1f) }
    var offset by remember(page.id) { mutableStateOf(Offset.Zero) }

    val sOriginal = stringResource(R.string.action_show_original)
    val sRecovered = stringResource(R.string.action_show_recovered)
    val sCompare = stringResource(R.string.action_compare)
    val sFilled = stringResource(R.string.show_filled)
    val sZoomIn = stringResource(R.string.zoom_in)
    val sZoomOut = stringResource(R.string.zoom_out)
    val pctOriginal = (split * 100).roundToInt()
    val modeText = when (mode) {
        ViewMode.ORIGINAL -> stringResource(R.string.view_original)
        ViewMode.RECOVERED -> stringResource(R.string.view_recovered)
        ViewMode.COMPARE -> stringResource(R.string.split_state, pctOriginal, 100 - pctOriginal)
    }
    val viewerActions = listOf(
        CustomAccessibilityAction(sOriginal) { mode = ViewMode.ORIGINAL; true },
        CustomAccessibilityAction(sRecovered) { mode = ViewMode.RECOVERED; true },
        CustomAccessibilityAction(sCompare) { mode = ViewMode.COMPARE; true },
        CustomAccessibilityAction(sFilled) { showMask = !showMask; true },
        CustomAccessibilityAction(sZoomIn) { zoom = (zoom * 1.5f).coerceAtMost(8f); true },
        CustomAccessibilityAction(sZoomOut) { zoom = (zoom / 1.5f).coerceAtLeast(1f); if (zoom == 1f) offset = Offset.Zero; true },
    )

    Column(modifier.fillMaxWidth().verticalScroll(rememberScrollState()).padding(16.dp), verticalArrangement = Arrangement.spacedBy(12.dp)) {
        PageStrip(pages, page, actions)

        SingleChoiceSegmentedButtonRow(Modifier.fillMaxWidth()) {
            val options = listOf(ViewMode.ORIGINAL to R.string.view_original, ViewMode.COMPARE to R.string.view_compare, ViewMode.RECOVERED to R.string.view_recovered)
            options.forEachIndexed { i, (m, label) ->
                SegmentedButton(selected = mode == m, onClick = { mode = m }, shape = SegmentedButtonDefaults.itemShape(i, options.size), modifier = Modifier.heightIn(min = 48.dp)) {
                    Text(stringResource(label))
                }
            }
        }

        PageViewer(
            page, mode, split, showMask, showOrder, zoom, offset, onTransform = { z, o -> zoom = z; offset = o },
            description = stringResource(R.string.viewer_desc, modeText), actions = viewerActions,
        )

        if (mode == ViewMode.COMPARE) {
            val label = stringResource(R.string.split_label)
            val state = stringResource(R.string.split_state, pctOriginal, 100 - pctOriginal)
            Slider(
                value = split, onValueChange = { split = it }, valueRange = 0f..1f, steps = 19,
                modifier = Modifier.fillMaxWidth().semantics { contentDescription = label; stateDescription = state },
            )
        }
        Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween, verticalAlignment = Alignment.CenterVertically) {
            Text(stringResource(R.string.zoom_state, (zoom * 100).roundToInt()), style = MaterialTheme.typography.bodyMedium)
            Row {
                IconButton(onClick = { zoom = (zoom / 1.5f).coerceAtLeast(1f); if (zoom == 1f) offset = Offset.Zero }, enabled = zoom > 1f) { Icon(Icons.Filled.ZoomOut, sZoomOut) }
                IconButton(onClick = { zoom = 1f; offset = Offset.Zero }, enabled = zoom > 1f) { Icon(Icons.Filled.FitScreen, stringResource(R.string.zoom_fit)) }
                IconButton(onClick = { zoom = (zoom * 1.5f).coerceAtMost(8f) }, enabled = zoom < 8f) { Icon(Icons.Filled.ZoomIn, sZoomIn) }
            }
        }

        SwitchRow(sFilled, if (showMask) stringResource(R.string.show_filled_legend) else null, showMask) { showMask = it }
        SwitchRow(stringResource(R.string.show_order), if (showOrder) stringResource(R.string.show_order_legend) else null, showOrder) { showOrder = it }

        FindingsCard(page.findings)

        // primary actions
        Button(onClick = { actions.saveCopy(page) }, modifier = Modifier.fillMaxWidth().heightIn(min = 56.dp)) {
            Icon(Icons.Filled.Save, contentDescription = null); Spacer(Modifier.width(12.dp)); Text(stringResource(R.string.save_copy))
        }
        if (!isPro) Text(stringResource(R.string.save_copy_free_note), style = MaterialTheme.typography.bodyMedium, color = MaterialTheme.colorScheme.onSurfaceVariant)
        FilledTonalButton(onClick = { actions.seal(listOf(page)) }, modifier = Modifier.fillMaxWidth().heightIn(min = 56.dp)) {
            Icon(Icons.Filled.Lock, contentDescription = null); Spacer(Modifier.width(12.dp)); Text(stringResource(R.string.seal))
        }
        if (pages.size > 1) {
            OutlinedButton(onClick = { actions.seal(pages) }, modifier = Modifier.fillMaxWidth().heightIn(min = 56.dp)) {
                Text(stringResource(R.string.seal_all, pages.size))
            }
        }

        ReadingOrderList(page)
        SettingsCard(page, actions)
        DetailsCard(page)

        TextButton(onClick = { actions.remove(page) }, modifier = Modifier.heightIn(min = 48.dp)) {
            Icon(Icons.Filled.Delete, contentDescription = null); Spacer(Modifier.width(8.dp)); Text(stringResource(R.string.remove_page))
        }
    }
}

@Composable
private fun PageStrip(pages: List<Page>, current: Page, actions: RecoverActions) {
    Column(verticalArrangement = Arrangement.spacedBy(4.dp)) {
        Heading(stringResource(R.string.pages_heading))
        FlowRow(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
            for (p in pages) {
                FilterChip(
                    selected = p.id == current.id, onClick = { actions.select(p) },
                    label = { Text(stringResource(R.string.page_chip, p.name, statusText(p.report.status))) },
                    modifier = Modifier.heightIn(min = 48.dp),
                )
            }
            FilterChip(
                selected = false, onClick = actions.takePhoto,
                label = { Text(stringResource(R.string.take_photo)) },
                leadingIcon = { Icon(Icons.Filled.PhotoCamera, contentDescription = null, modifier = Modifier.size(18.dp)) },
                modifier = Modifier.heightIn(min = 48.dp),
            )
            FilterChip(
                selected = false, onClick = actions.choosePhotos,
                label = { Text(stringResource(R.string.choose_photos)) },
                leadingIcon = { Icon(Icons.Filled.Add, contentDescription = null, modifier = Modifier.size(18.dp)) },
                modifier = Modifier.heightIn(min = 48.dp),
            )
        }
    }
}

@Composable
fun statusText(s: Report.Status): String = stringResource(when (s) {
    Report.Status.STABLE -> R.string.status_stable
    Report.Status.ENHANCED -> R.string.status_enhanced
    Report.Status.REPAIRED -> R.string.status_repaired
    Report.Status.DETECTED_NOT_REPAIRED -> R.string.status_detected
    Report.Status.SKIPPED_DAMAGE_TOO_EXTENSIVE -> R.string.status_skipped
})

@Composable
fun FindingsCard(findings: List<Finding>) {
    Section(stringResource(R.string.findings_heading)) {
        for (f in findings) {
            val (icon, word, tint) = when (f.level) {
                Finding.Level.OK -> Triple(Icons.Filled.CheckCircle, stringResource(R.string.level_ok), MaterialTheme.colorScheme.primary)
                Finding.Level.INFO -> Triple(Icons.Filled.Info, stringResource(R.string.level_info), MaterialTheme.colorScheme.onSurfaceVariant)
                Finding.Level.WARN -> Triple(Icons.Filled.Warning, stringResource(R.string.level_warn), MaterialTheme.colorScheme.secondary)
            }
            val spoken = stringResource(R.string.finding_item, word, f.text)
            Row(Modifier.fillMaxWidth().clearAndSetSemantics { contentDescription = spoken }, horizontalArrangement = Arrangement.spacedBy(12.dp)) {
                Icon(icon, contentDescription = null, tint = tint, modifier = Modifier.padding(top = 2.dp))
                Column {
                    Text(word, style = MaterialTheme.typography.labelLarge, color = tint)
                    Text(f.text, style = MaterialTheme.typography.bodyMedium)
                }
            }
        }
    }
}

@Composable
private fun ReadingOrderList(page: Page) {
    val n = page.nodes.size
    if (n == 0) return
    Collapsible(stringResource(R.string.order_heading, n)) {
        for (node in page.nodes.take(200)) {
            Text(stringResource(R.string.order_item, node.order + 1, n, where(node, page.workWidth, page.workHeight), node.box.w, node.box.h),
                style = MaterialTheme.typography.bodyMedium)
        }
    }
}

@Composable
private fun where(n: Node, w: Int, h: Int): String {
    val cx = (n.box.x + n.box.w / 2.0) / w
    val cy = (n.box.y + n.box.h / 2.0) / h
    val wide = n.box.w > w * 0.6
    val vertical = if (cy < 0.34) 0 else if (cy < 0.67) 1 else 2
    return stringResource(when {
        wide -> listOf(R.string.where_top, R.string.where_middle, R.string.where_bottom)[vertical]
        cx < 0.5 && cy < 0.5 -> R.string.where_top_left
        cx >= 0.5 && cy < 0.5 -> R.string.where_top_right
        cx < 0.5 -> R.string.where_bottom_left
        else -> R.string.where_bottom_right
    })
}

@Composable
private fun SettingsCard(page: Page, actions: RecoverActions) {
    Collapsible(stringResource(R.string.settings_heading)) {
        val cfg = page.cfg
        SwitchRow(stringResource(R.string.set_flatten), stringResource(R.string.set_flatten_help), cfg.flatten, enabled = cfg.repair) {
            actions.reprocess(page, cfg.copy(flatten = it))
        }
        SwitchRow(stringResource(R.string.set_fill_shadow), stringResource(R.string.set_fill_shadow_help), cfg.fillShadow, enabled = cfg.repair) {
            actions.reprocess(page, cfg.copy(fillShadow = it))
        }
        SwitchRow(stringResource(R.string.set_repair), stringResource(R.string.set_repair_help), cfg.repair) {
            actions.reprocess(page, cfg.copy(repair = it))
        }
    }
}

@Composable
private fun DetailsCard(page: Page) {
    Collapsible(stringResource(R.string.details_heading)) {
        Detail(stringResource(R.string.detail_source), stringResource(when (page.source) {
            Source.CAMERA -> R.string.source_camera
            Source.IMPORT -> R.string.source_import
            Source.SAMPLE -> R.string.source_sample
        }))
        Detail(stringResource(R.string.detail_status), statusText(page.report.status))
        Detail(stringResource(R.string.detail_filled), Findings.pct(page.report.maskedFraction))
        Detail(stringResource(R.string.detail_size), humanBytes(page.original.size.toLong()))
        Detail(stringResource(R.string.detail_processed), "${page.workWidth} × ${page.workHeight}")
        Text(stringResource(R.string.detail_original_hash), style = MaterialTheme.typography.labelLarge)
        SelectionContainer { Mono(page.originalSha256) }
        SelectionContainer { Mono(Json.obj("report" to page.report.toJson(), "capture" to page.captureJson()).canonical()) }
    }
}

@Composable
private fun Detail(label: String, value: String) {
    Row(Modifier.fillMaxWidth().semantics(mergeDescendants = true) {}, horizontalArrangement = Arrangement.spacedBy(12.dp)) {
        Text(label, style = MaterialTheme.typography.labelLarge, modifier = Modifier.weight(0.4f))
        Text(value, style = MaterialTheme.typography.bodyMedium, modifier = Modifier.weight(0.6f))
    }
}
