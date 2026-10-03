package com.arcanaforensics.arcalume.ui

import android.Manifest
import android.content.Intent
import android.content.pm.PackageManager
import android.net.Uri
import android.provider.Settings
import android.view.KeyEvent
import androidx.activity.compose.BackHandler
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.camera.core.CameraSelector
import androidx.camera.core.ImageCapture
import androidx.camera.core.ImageCaptureException
import androidx.camera.core.Preview
import androidx.camera.lifecycle.ProcessCameraProvider
import androidx.camera.view.PreviewView
import androidx.compose.foundation.background
import androidx.compose.foundation.focusable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.heightIn
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.safeDrawingPadding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Close
import androidx.compose.material.icons.filled.PhotoCamera
import androidx.compose.material3.Button
import androidx.compose.material3.FilledIconButton
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.IconButtonDefaults
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.DisposableEffect
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.focus.FocusRequester
import androidx.compose.ui.focus.focusRequester
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.input.key.onPreviewKeyEvent
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.semantics.heading
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.unit.dp
import androidx.compose.ui.viewinterop.AndroidView
import androidx.core.content.ContextCompat
import androidx.lifecycle.compose.LocalLifecycleOwner
import com.arcanaforensics.arcalume.R
import java.io.File

/**
 * Full-screen camera. The photo is written to a private cache file exactly as the camera
 * produced it (EXIF included); those bytes become the sealed original. Either volume
 * key also takes the photo, which helps when holding the phone steady over a page.
 */
@Composable
fun CameraScreen(onCaptured: (File) -> Unit, onChoosePhotos: () -> Unit, onClose: () -> Unit, onError: (String) -> Unit) {
    val context = LocalContext.current
    val lifecycle = LocalLifecycleOwner.current
    var granted by remember { mutableStateOf(ContextCompat.checkSelfPermission(context, Manifest.permission.CAMERA) == PackageManager.PERMISSION_GRANTED) }
    var asked by remember { mutableStateOf(false) }
    val permission = rememberLauncherForActivityResult(ActivityResultContracts.RequestPermission()) { granted = it; asked = true }
    LaunchedEffect(Unit) { if (!granted) permission.launch(Manifest.permission.CAMERA) }
    BackHandler(onBack = onClose)

    Box(Modifier.fillMaxSize().background(Color.Black)) {
        if (!granted) {
            Column(Modifier.fillMaxSize().safeDrawingPadding().padding(24.dp), verticalArrangement = Arrangement.spacedBy(16.dp, Alignment.CenterVertically)) {
                if (asked) {
                    Text(stringResource(R.string.camera_denied), color = Color.White, style = MaterialTheme.typography.bodyLarge)
                    Button(onClick = {
                        context.startActivity(Intent(Settings.ACTION_APPLICATION_DETAILS_SETTINGS, Uri.fromParts("package", context.packageName, null)))
                    }, modifier = Modifier.fillMaxWidth().heightIn(min = 56.dp)) { Text(stringResource(R.string.open_settings)) }
                    OutlinedButton(onClick = onChoosePhotos, modifier = Modifier.fillMaxWidth().heightIn(min = 56.dp)) { Text(stringResource(R.string.choose_photos), color = Color.White) }
                }
                OutlinedButton(onClick = onClose, modifier = Modifier.fillMaxWidth().heightIn(min = 56.dp)) { Text(stringResource(R.string.close_camera), color = Color.White) }
            }
            return@Box
        }

        val capture = remember {
            ImageCapture.Builder()
                .setCaptureMode(ImageCapture.CAPTURE_MODE_MAXIMIZE_QUALITY)
                .setJpegQuality(95)
                .build()
        }
        var busy by remember { mutableStateOf(false) }
        val previewView = remember { PreviewView(context).apply { scaleType = PreviewView.ScaleType.FIT_CENTER; importantForAccessibility = android.view.View.IMPORTANT_FOR_ACCESSIBILITY_NO } }
        val failed = stringResource(R.string.camera_failed, "%s")
        val unavailable = stringResource(R.string.camera_unavailable)

        DisposableEffect(lifecycle) {
            val future = ProcessCameraProvider.getInstance(context)
            future.addListener({
                val provider = future.get()
                try {
                    provider.unbindAll()
                    val preview = Preview.Builder().build().also { it.setSurfaceProvider(previewView.surfaceProvider) }
                    provider.bindToLifecycle(lifecycle, CameraSelector.DEFAULT_BACK_CAMERA, preview, capture)
                } catch (e: Exception) {
                    onError(unavailable)
                    onClose()
                }
            }, ContextCompat.getMainExecutor(context))
            onDispose { runCatching { future.get().unbindAll() } }
        }

        fun shoot() {
            if (busy) return
            busy = true
            val out = File(context.cacheDir, "capture-${System.currentTimeMillis()}.jpg")
            capture.takePicture(ImageCapture.OutputFileOptions.Builder(out).build(), ContextCompat.getMainExecutor(context),
                object : ImageCapture.OnImageSavedCallback {
                    override fun onImageSaved(output: ImageCapture.OutputFileResults) { busy = false; onCaptured(out) }
                    override fun onError(exception: ImageCaptureException) { busy = false; out.delete(); onError(failed.format(exception.message ?: "")) }
                })
        }

        val focus = remember { FocusRequester() }
        LaunchedEffect(Unit) { runCatching { focus.requestFocus() } }
        AndroidView({ previewView }, Modifier.fillMaxSize())
        Column(
            Modifier.fillMaxSize().safeDrawingPadding().focusRequester(focus).focusable()
                .onPreviewKeyEvent {
                    val k = it.nativeKeyEvent
                    if ((k.keyCode == KeyEvent.KEYCODE_VOLUME_UP || k.keyCode == KeyEvent.KEYCODE_VOLUME_DOWN)) {
                        if (k.action == KeyEvent.ACTION_UP) shoot()
                        true
                    } else false
                },
            verticalArrangement = Arrangement.SpaceBetween,
        ) {
            Row(Modifier.fillMaxWidth().background(Color(0xAA000000)).padding(8.dp)) {
                Column(Modifier.weight(1f)) {
                    Text(stringResource(R.string.camera_title), color = Color.White, style = MaterialTheme.typography.titleMedium, modifier = Modifier.semantics { heading() })
                    Text(stringResource(R.string.camera_hint), color = Color.White, style = MaterialTheme.typography.bodyMedium)
                }
                IconButton(onClick = onClose) { Icon(Icons.Filled.Close, stringResource(R.string.close_camera), tint = Color.White) }
            }
            Box(Modifier.fillMaxWidth().padding(24.dp), contentAlignment = Alignment.Center) {
                FilledIconButton(
                    onClick = ::shoot, enabled = !busy, shape = CircleShape,
                    colors = IconButtonDefaults.filledIconButtonColors(containerColor = Color.White, contentColor = Color.Black),
                    modifier = Modifier.size(80.dp),
                ) { Icon(Icons.Filled.PhotoCamera, stringResource(R.string.shutter), modifier = Modifier.size(36.dp)) }
            }
        }
    }
}
