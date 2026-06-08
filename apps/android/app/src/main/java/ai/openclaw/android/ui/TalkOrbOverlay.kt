package ai.openclaw.android.ui

import androidx.compose.animation.core.*
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.Path
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import kotlin.math.cos
import kotlin.math.sin

@Composable
fun TalkOrbOverlay(
  seamColor: Color,
  statusText: String,
  isListening: Boolean,
  isSpeaking: Boolean,
  micPowerDb: Float,
  talkVoiceOutputEnabled: Boolean,
  modifier: Modifier = Modifier,
) {
  val trimmed = statusText.trim()
  val showStatus = trimmed.isNotEmpty() && trimmed != "Off"
  
  // Animation state for audio amplitude
  val targetAmplitude = ((micPowerDb + 60f) / 60f).coerceIn(0f, 1f)
  val smoothAmplitude = remember { Animatable(0f) }
  LaunchedEffect(targetAmplitude) {
    val duration = if (targetAmplitude > smoothAmplitude.value) 80 else 200
    smoothAmplitude.animateTo(targetAmplitude, animationSpec = tween(duration))
  }

  val infinite = rememberInfiniteTransition(label = "rocky-horror-pulse")
  val pulse by infinite.animateFloat(
    initialValue = 0f,
    targetValue = 1f,
    animationSpec = infiniteRepeatable(animation = tween(2000), repeatMode = RepeatMode.Reverse),
    label = "pulse"
  )

  Box(
    modifier = modifier.fillMaxSize(),
    contentAlignment = Alignment.Center
  ) {
    val amplitude = smoothAmplitude.value
    
    Canvas(modifier = Modifier.size(400.dp)) {
      val center = this.center
      val w = size.width
      val h = size.height
      
      // 1. Futuristic Background Aura
      drawCircle(
        brush = Brush.radialGradient(
          colors = listOf(
            seamColor.copy(alpha = 0.15f + amplitude * 0.2f),
            Color(0xFF0D0D12).copy(alpha = 0.4f),
            Color.Transparent
          ),
          center = center,
          radius = size.minDimension * 0.8f
        ),
        radius = size.minDimension * 0.8f,
        center = center
      )

      // 2. The "Electric Lips" (Rocky Horror Style)
      // We'll use two symmetric paths for top and bottom lips
      val lipWidth = 220.dp.toPx() * (1f + amplitude * 0.05f)
      val lipHeight = 80.dp.toPx() * (0.8f + amplitude * 1.2f) // Opens wide with volume
      
      val lipColor = Color(0xFFE30613) // Classic Rocky Horror Red
      val electricColor = Color(0xFF66A3FF) // Cyan electricity
      
      // Top Lip
      val topLipPath = Path().apply {
        moveTo(center.x - lipWidth / 2, center.y)
        cubicTo(
          center.x - lipWidth / 4, center.y - lipHeight / 2,
          center.x + lipWidth / 4, center.y - lipHeight / 2,
          center.x + lipWidth / 2, center.y
        )
        // Inner part of top lip (cupid's bow style)
        cubicTo(
          center.x + lipWidth / 4, center.y - lipHeight / 4 * amplitude,
          center.x - lipWidth / 4, center.y - lipHeight / 4 * amplitude,
          center.x - lipWidth / 2, center.y
        )
      }
      
      // Bottom Lip
      val bottomLipPath = Path().apply {
        moveTo(center.x - lipWidth / 2, center.y)
        cubicTo(
          center.x - lipWidth / 4, center.y + lipHeight / 2,
          center.x + lipWidth / 4, center.y + lipHeight / 2,
          center.x + lipWidth / 2, center.y
        )
        // Inner part of bottom lip
        cubicTo(
          center.x + lipWidth / 4, center.y + lipHeight / 4 * amplitude,
          center.x - lipWidth / 4, center.y + lipHeight / 4 * amplitude,
          center.x - lipWidth / 2, center.y
        )
      }

      // Draw the lips with a glow
      drawPath(topLipPath, color = lipColor.copy(alpha = 0.9f))
      drawPath(bottomLipPath, color = lipColor.copy(alpha = 0.9f))
      
      // Electric Arcs around the lips
      if (isSpeaking || isListening) {
        val spikeCount = 30
        for (i in 0 until spikeCount) {
          val angle = (i.toFloat() / spikeCount) * 2f * Math.PI.toFloat()
          val startRadius = lipWidth / 2.2f
          val length = 15.dp.toPx() + (amplitude * 40.dp.toPx() * sin(angle * 5f + pulse * 10f))
          
          val startX = center.x + cos(angle) * startRadius
          val startY = center.y + sin(angle) * startRadius * 0.4f
          val endX = center.x + cos(angle) * (startRadius + length)
          val endY = center.y + sin(angle) * (startRadius + length) * 0.4f
          
          drawLine(
            color = electricColor.copy(alpha = 0.6f * amplitude),
            start = Offset(startX, startY),
            end = Offset(endX, endY),
            strokeWidth = 2.dp.toPx(),
            cap = androidx.compose.ui.graphics.StrokeCap.Round
          )
        }
      }

      // Outer Glow Ring
      drawCircle(
        color = lipColor.copy(alpha = 0.1f + 0.1f * pulse),
        radius = (lipWidth / 1.8f) + (10.dp.toPx() * pulse),
        center = center,
        style = Stroke(width = 2.dp.toPx())
      )
    }

    // Status Pill
    if (!talkVoiceOutputEnabled || showStatus) {
      Box(modifier = Modifier.align(Alignment.BottomCenter).padding(bottom = 80.dp)) {
        Surface(
          color = Color.Black.copy(alpha = 0.75f),
          shape = CircleShape,
          border = androidx.compose.foundation.BorderStroke(1.dp, seamColor.copy(alpha = 0.5f))
        ) {
          Text(
            text = if (!talkVoiceOutputEnabled) "Voice output disabled" else trimmed,
            modifier = Modifier.padding(horizontal = 16.dp, vertical = 8.dp),
            color = Color.White,
            style = MaterialTheme.typography.labelLarge,
            fontWeight = FontWeight.Bold,
          )
        }
      }
    }
  }
}
