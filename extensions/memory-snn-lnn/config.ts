export type SNNLNNConfig = {
  modelEndpoint: string;
  enabled: boolean;
  autoOptimize: boolean;
  optimizationMode: "summarize" | "extract" | "compress" | "full";
  maxInputTokens: number;
  timeoutMs: number;
  fallbackToBuiltin: boolean;
};

const DEFAULT_ENDPOINT = "http://127.0.0.1:5001";

export const snnLnnConfigSchema = {
  parse(value: unknown): SNNLNNConfig {
    if (!value || typeof value !== "object" || Array.isArray(value)) {
      throw new Error("memory-snn-lnn config required");
    }
    const cfg = value as Record<string, unknown>;

    const allowed = [
      "modelEndpoint",
      "enabled",
      "autoOptimize",
      "optimizationMode",
      "maxInputTokens",
      "timeoutMs",
      "fallbackToBuiltin",
    ];
    const unknown = Object.keys(cfg).filter((k) => !allowed.includes(k));
    if (unknown.length > 0) {
      throw new Error(`memory-snn-lnn config has unknown keys: ${unknown.join(", ")}`);
    }

    const optimizationMode = cfg.optimizationMode as string | undefined;
    if (
      optimizationMode &&
      !["summarize", "extract", "compress", "full"].includes(optimizationMode)
    ) {
      throw new Error(
        `memory-snn-lnn: optimizationMode must be one of: summarize, extract, compress, full`,
      );
    }

    const maxInputTokens =
      typeof cfg.maxInputTokens === "number" ? Math.floor(cfg.maxInputTokens) : 8192;
    if (maxInputTokens < 256 || maxInputTokens > 131072) {
      throw new Error("memory-snn-lnn: maxInputTokens must be between 256 and 131072");
    }

    const timeoutMs = typeof cfg.timeoutMs === "number" ? Math.floor(cfg.timeoutMs) : 30000;
    if (timeoutMs < 1000 || timeoutMs > 120000) {
      throw new Error("memory-snn-lnn: timeoutMs must be between 1000 and 120000");
    }

    return {
      modelEndpoint: typeof cfg.modelEndpoint === "string" ? cfg.modelEndpoint : DEFAULT_ENDPOINT,
      enabled: cfg.enabled !== false,
      autoOptimize: cfg.autoOptimize !== false,
      optimizationMode: (optimizationMode as SNNLNNConfig["optimizationMode"]) ?? "full",
      maxInputTokens,
      timeoutMs,
      fallbackToBuiltin: cfg.fallbackToBuiltin !== false,
    };
  },
  uiHints: {
    modelEndpoint: {
      label: "Model Service Endpoint",
      placeholder: DEFAULT_ENDPOINT,
      help: "HTTP endpoint for the Python SNN-LNN model server",
    },
    enabled: {
      label: "Enabled",
      help: "Enable SNN-LNN memory optimization",
    },
    autoOptimize: {
      label: "Auto-Optimize",
      help: "Automatically optimize memory content via lifecycle hooks",
    },
    optimizationMode: {
      label: "Optimization Mode",
      help: "summarize=condense, extract=key facts, compress=dense encoding, full=all strategies",
    },
    maxInputTokens: {
      label: "Max Input Tokens",
      help: "Maximum tokens to send to the model service per request",
      advanced: true,
    },
    timeoutMs: {
      label: "Timeout (ms)",
      help: "Request timeout for the model service",
      advanced: true,
    },
    fallbackToBuiltin: {
      label: "Fallback to Built-in",
      help: "Fall back to built-in memory if SNN-LNN service is unavailable",
    },
  },
};
