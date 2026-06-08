package ai.openclaw.android.ui

import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.dynamicDarkColorScheme
import androidx.compose.material3.dynamicLightColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext

@Composable
fun OpenClawTheme(content: @Composable () -> Unit) {
  val context = LocalContext.current
  val isDark = isSystemInDarkTheme()
  val colorScheme = if (isDark) dynamicDarkColorScheme(context) else dynamicLightColorScheme(context)

  MaterialTheme(colorScheme = colorScheme, content = content)
}

@Composable
fun overlayContainerColor(): Color {
  val isDark = isSystemInDarkTheme()
  return if (isDark) {
    // Dashboard-inspired dark mode: black glass with red tint.
    Color(0xCC12060A)
  } else {
    // Keep light mode usable but avoid bright glare over canvas.
    Color(0xE62A141A)
  }
}

@Composable
fun overlayIconColor(): Color {
  return if (isSystemInDarkTheme()) Color(0xFFFF5A66) else MaterialTheme.colorScheme.onSurfaceVariant
}
