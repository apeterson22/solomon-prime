package ai.openclaw.android

enum class ModelRouteMode(val rawValue: String, val label: String, val summary: String) {
  Local(
    rawValue = "local",
    label = "Local",
    summary = "Prefer on-device / low-latency routes.",
  ),
  Hybrid(
    rawValue = "hybrid",
    label = "Hybrid",
    summary = "Balance speed and quality across local + cloud.",
  ),
  Cloud(
    rawValue = "cloud",
    label = "Cloud",
    summary = "Prefer highest-capability remote models.",
  );

  companion object {
    fun fromRawValue(raw: String?): ModelRouteMode {
      val normalized = raw?.trim()?.lowercase().orEmpty()
      return entries.firstOrNull { it.rawValue == normalized } ?: Hybrid
    }
  }
}
