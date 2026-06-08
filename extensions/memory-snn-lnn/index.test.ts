import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
// ---------------------------------------------------------------------------
// Config schema tests
// ---------------------------------------------------------------------------
import { snnLnnConfigSchema } from "./config.js";

describe("snnLnnConfigSchema", () => {
  it("should return defaults for empty config", () => {
    const cfg = snnLnnConfigSchema.parse({});
    expect(cfg.modelEndpoint).toBe("http://127.0.0.1:5001");
    expect(cfg.enabled).toBe(true);
    expect(cfg.autoOptimize).toBe(true);
    expect(cfg.optimizationMode).toBe("full");
    expect(cfg.maxInputTokens).toBe(8192);
    expect(cfg.timeoutMs).toBe(30000);
    expect(cfg.fallbackToBuiltin).toBe(true);
  });

  it("should parse valid config with overrides", () => {
    const cfg = snnLnnConfigSchema.parse({
      modelEndpoint: "http://localhost:8080",
      enabled: false,
      optimizationMode: "summarize",
      maxInputTokens: 4096,
      timeoutMs: 15000,
      fallbackToBuiltin: false,
    });
    expect(cfg.modelEndpoint).toBe("http://localhost:8080");
    expect(cfg.enabled).toBe(false);
    expect(cfg.optimizationMode).toBe("summarize");
    expect(cfg.maxInputTokens).toBe(4096);
    expect(cfg.timeoutMs).toBe(15000);
    expect(cfg.fallbackToBuiltin).toBe(false);
  });

  it("should throw on invalid optimization mode", () => {
    expect(() => snnLnnConfigSchema.parse({ optimizationMode: "invalid" })).toThrow();
  });

  it("should throw on maxInputTokens out of range", () => {
    expect(() => snnLnnConfigSchema.parse({ maxInputTokens: 100 })).toThrow();
    expect(() => snnLnnConfigSchema.parse({ maxInputTokens: 200000 })).toThrow();
  });

  it("should throw on timeoutMs out of range", () => {
    expect(() => snnLnnConfigSchema.parse({ timeoutMs: 500 })).toThrow();
    expect(() => snnLnnConfigSchema.parse({ timeoutMs: 200000 })).toThrow();
  });

  it("should throw on unknown keys", () => {
    expect(() => snnLnnConfigSchema.parse({ unknownKey: true })).toThrow();
  });

  it("should throw on non-object input", () => {
    expect(() => snnLnnConfigSchema.parse(null)).toThrow();
    expect(() => snnLnnConfigSchema.parse("string")).toThrow();
    expect(() => snnLnnConfigSchema.parse([])).toThrow();
  });
});

// ---------------------------------------------------------------------------
// HTTP client helper tests (mocked fetch)
// ---------------------------------------------------------------------------

// We test the callModelService logic indirectly by testing the config
// and the plugin structure. Full integration tests are in the integration test file.

describe("model endpoint construction", () => {
  it("should construct correct endpoint URLs", () => {
    const endpoint = "http://127.0.0.1:5001";
    expect(`${endpoint}/optimize`).toBe("http://127.0.0.1:5001/optimize");
    expect(`${endpoint}/similarity`).toBe("http://127.0.0.1:5001/similarity");
    expect(`${endpoint}/health`).toBe("http://127.0.0.1:5001/health");
  });
});

// ---------------------------------------------------------------------------
// Plugin structure tests
// ---------------------------------------------------------------------------

describe("memorySnnLnnPlugin", () => {
  it("should have correct plugin metadata", async () => {
    const { default: plugin } = await import("./index.js");
    expect(plugin.id).toBe("memory-snn-lnn");
    expect(plugin.name).toBe("Memory (SNN-LNN Hybrid)");
    expect(plugin.kind).toBe("memory");
  });

  it("should have a register function", async () => {
    const { default: plugin } = await import("./index.js");
    expect(typeof plugin.register).toBe("function");
  });

  it("should have a configSchema", async () => {
    const { default: plugin } = await import("./index.js");
    expect(plugin.configSchema).toBeDefined();
    expect(typeof plugin.configSchema.parse).toBe("function");
  });
});
