package com.arcanaforensics.arcalume.ui

import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.darkColorScheme
import androidx.compose.material3.lightColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.ui.graphics.Color

// Fixed palettes (no wallpaper colours) so every pair below keeps at least 4.5:1 contrast
// for text and 3:1 for control outlines, in both themes.
private val Light = lightColorScheme(
    primary = Color(0xFF1D4E89), onPrimary = Color.White,
    primaryContainer = Color(0xFFD5E3FF), onPrimaryContainer = Color(0xFF001C3B),
    secondary = Color(0xFF7A4B00), onSecondary = Color.White,
    secondaryContainer = Color(0xFFFFDDB3), onSecondaryContainer = Color(0xFF281800),
    tertiary = Color(0xFF8E1F7A), onTertiary = Color.White,
    error = Color(0xFFB3261E), onError = Color.White,
    errorContainer = Color(0xFFF9DEDC), onErrorContainer = Color(0xFF410E0B),
    background = Color(0xFFFBF8F3), onBackground = Color(0xFF1B1C1E),
    surface = Color(0xFFFBF8F3), onSurface = Color(0xFF1B1C1E),
    surfaceVariant = Color(0xFFE3E2EC), onSurfaceVariant = Color(0xFF44464F),
    surfaceContainer = Color(0xFFF1EDE6), surfaceContainerHigh = Color(0xFFEAE6DF),
    outline = Color(0xFF74777F), outlineVariant = Color(0xFFC4C6D0),
)

private val Dark = darkColorScheme(
    primary = Color(0xFFA7C8FF), onPrimary = Color(0xFF00315F),
    primaryContainer = Color(0xFF1D4E89), onPrimaryContainer = Color(0xFFD5E3FF),
    secondary = Color(0xFFFFB951), onSecondary = Color(0xFF412D00),
    secondaryContainer = Color(0xFF5C3900), onSecondaryContainer = Color(0xFFFFDDB3),
    tertiary = Color(0xFFFFAEE4), onTertiary = Color(0xFF5B0049),
    error = Color(0xFFF2B8B5), onError = Color(0xFF601410),
    errorContainer = Color(0xFF8C1D18), onErrorContainer = Color(0xFFF9DEDC),
    background = Color(0xFF12161C), onBackground = Color(0xFFE3E2E6),
    surface = Color(0xFF12161C), onSurface = Color(0xFFE3E2E6),
    surfaceVariant = Color(0xFF44464F), onSurfaceVariant = Color(0xFFC6C6D0),
    surfaceContainer = Color(0xFF1C2027), surfaceContainerHigh = Color(0xFF262A31),
    outline = Color(0xFF90909A), outlineVariant = Color(0xFF44464F),
)

@Composable
fun ArcalumeTheme(dark: Boolean = isSystemInDarkTheme(), content: @Composable () -> Unit) {
    MaterialTheme(colorScheme = if (dark) Dark else Light, content = content)
}
