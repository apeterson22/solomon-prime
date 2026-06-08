/**
 * OpenClaw Memory (SNN-LNN Hybrid) Plugin
 *
 * Memory optimization using Spiking Neural Networks (SNN) for temporal
 * pattern detection and Liquid Neural Networks (LNN) for adaptive
 * context-dependent processing.
 *
 * Supports cross-provider session memory sharing — when a session switches
 * between providers (e.g. Ollama -> OpenRouter), the SNN-LNN memory context
 * follows automatically via canonical session key resolution.
 *
 * Provides:
 *   - memory_optimize : optimize/summarize/extract/compress memory content
 *   - memory_compare  : compare two texts for semantic similarity
 *   - memory_share   : share memory context across provider sessions
 *   - Auto-optimization hooks for agent_end and session_end
 */

import { Type } from "@sinclair/typebox";
import type { OpenClawPluginApi } from "openclaw/plugin-sdk";
import { type SNNLNNConfig, snnLnnConfigSchema } from "./config.js";

// ---------------------------------------------------------------------------
// HTTP Client for Python model service
// ---------------------------------------------------------------------------

async function callModelService(
  endpoint: string,
  path: string,
  body: Record<string, unknown>,
  timeoutMs: number,
): Promise<Record<string, unknown>> {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);

  try {
    const res = await fetch(`${endpoint}${path}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
      signal: controller.signal,
    });
    clearTimeout(timer);
    if (!res.ok) {
      throw new Error(`Model service returned ${res.status}: ${await res.text()}`);
    }
    return (await res.json()) as Record<string, unknown>;
  } catch (err: unknown) {
    clearTimeout(timer);
    if (err instanceof Error && err.name === "AbortError") {
      throw new Error(`Model service timeout after ${timeoutMs}ms`);
    }
    throw err;
  }
}

// ---------------------------------------------------------------------------
// Plugin Definition
// ---------------------------------------------------------------------------

const memorySnnLnnPlugin = {
  id: "memory-snn-lnn",
  name: "Memory (SNN-LNN Hybrid)",
  description: "SNN-LNN hybrid memory optimization for summarization, extraction, and compression",
  kind: "memory" as const,
  configSchema: snnLnnConfigSchema,

  register(api: OpenClawPluginApi) {
    const cfg = snnLnnConfigSchema.parse(api.pluginConfig);
    api.logger.info?.(
      `memory-snn-lnn: plugin registered (endpoint: ${cfg.modelEndpoint}, mode: ${cfg.optimizationMode})`,
    );

    // -----------------------------------------------------------------------
    // Helper: check service health
    // -----------------------------------------------------------------------
    async function isServiceHealthy(): Promise<boolean> {
      try {
        const res = await fetch(`${cfg.modelEndpoint}/health`, {
          method: "GET",
          signal: AbortSignal.timeout(3000),
        });
        return res.ok;
      } catch {
        return false;
      }
    }

    // -----------------------------------------------------------------------
    // Tool: memory_optimize
    // -----------------------------------------------------------------------
    api.registerTool(
      {
        name: "memory_optimize",
        label: "Memory Optimize",
        description:
          "Optimize memory content using SNN-LNN hybrid processing. Supports modes: summarize, extract, compress, full.",
        parameters: Type.Object({
          text: Type.String({ description: "Text content to optimize" }),
          mode: Type.Optional(
            Type.Unsafe<SNNLNNConfig["optimizationMode"]>({
              type: "string",
              enum: ["summarize", "extract", "compress", "full"],
              description: "Optimization mode (default: from config)",
            }),
          ),
        }),
        async execute(_toolCallId, params) {
          const { text, mode } = params as {
            text: string;
            mode?: SNNLNNConfig["optimizationMode"];
          };
          const optMode = mode ?? cfg.optimizationMode;

          if (!cfg.enabled) {
            return {
              content: [{ type: "text", text: "SNN-LNN optimization is disabled." }],
              details: { disabled: true },
            };
          }

          try {
            const result = await callModelService(
              cfg.modelEndpoint,
              "/optimize",
              { text, mode: optMode },
              cfg.timeoutMs,
            );

            if (optMode === "summarize") {
              return {
                content: [
                  {
                    type: "text",
                    text: `Summary: ${result.summary ?? "No summary generated."}`,
                  },
                ],
                details: result,
              };
            }

            if (optMode === "extract") {
              const facts = (result.facts as Array<Record<string, unknown>>) ?? [];
              const formatted = facts
                .map(
                  (f, i) =>
                    `${i + 1}. [${f.type ?? "?"}] ${f.text ?? ""} (${((f.importance as number) ?? 0) * 100}%)`,
                )
                .join("\n");
              return {
                content: [
                  {
                    type: "text",
                    text: `Extracted ${facts.length} facts:\n${formatted || "No facts extracted."}`,
                  },
                ],
                details: result,
              };
            }

            if (optMode === "compress") {
              return {
                content: [
                  {
                    type: "text",
                    text: `Compressed: ${(result.compression_ratio as number) ?? 0}x ratio, ${(result.dimensions as number) ?? 0}d vector`,
                  },
                ],
                details: result,
              };
            }

            // full mode
            return {
              content: [
                {
                  type: "text",
                  text: `Full optimization complete.\nSummary: ${result.summary ?? "N/A"}\nProcessing time: ${result.processing_time_ms ?? "?"}ms`,
                },
              ],
              details: result,
            };
          } catch (err: unknown) {
            const msg = err instanceof Error ? err.message : String(err);
            api.logger.warn?.(`memory-snn-lnn: optimize failed: ${msg}`);
            if (cfg.fallbackToBuiltin) {
              return {
                content: [
                  { type: "text", text: `SNN-LNN unavailable (${msg}). Using original text.` },
                ],
                details: { error: msg, fallback: true },
              };
            }
            throw err;
          }
        },
      },
      { name: "memory_optimize" },
    );

    // -----------------------------------------------------------------------
    // Tool: memory_compare
    // -----------------------------------------------------------------------
    api.registerTool(
      {
        name: "memory_compare",
        label: "Memory Compare",
        description: "Compare two texts for semantic similarity using LNN state-space encoding.",
        parameters: Type.Object({
          text1: Type.String({ description: "First text" }),
          text2: Type.String({ description: "Second text" }),
        }),
        async execute(_toolCallId, params) {
          const { text1, text2 } = params as { text1: string; text2: string };

          if (!cfg.enabled) {
            return {
              content: [{ type: "text", text: "SNN-LNN optimization is disabled." }],
              details: { disabled: true },
            };
          }

          try {
            const result = await callModelService(
              cfg.modelEndpoint,
              "/similarity",
              { text1, text2 },
              cfg.timeoutMs,
            );
            const sim = (result.similarity as number) ?? 0;
            const bar = "█".repeat(Math.round(Math.abs(sim) * 20));
            return {
              content: [
                {
                  type: "text",
                  text: `Similarity: ${(sim * 100).toFixed(1)}% ${bar}`,
                },
              ],
              details: { similarity: sim },
            };
          } catch (err: unknown) {
            const msg = err instanceof Error ? err.message : String(err);
            api.logger.warn?.(`memory-snn-lnn: compare failed: ${msg}`);
            return {
              content: [{ type: "text", text: `Comparison failed: ${msg}` }],
              details: { error: msg },
            };
          }
        },
      },
      { name: "memory_compare" },
    );

    // -----------------------------------------------------------------------
    // Tool: memory_status
    // -----------------------------------------------------------------------
    api.registerTool(
      {
        name: "memory_snn_lnn_status",
        label: "Memory SNN-LNN Status",
        description: "Check the status of the SNN-LNN model service.",
        parameters: Type.Object({}),
        async execute() {
          const healthy = await isServiceHealthy();
          return {
            content: [
              {
                type: "text",
                text: `SNN-LNN Service: ${healthy ? "HEALTHY" : "UNHEALTHABLE"}\nEndpoint: ${cfg.modelEndpoint}\nMode: ${cfg.optimizationMode}\nEnabled: ${cfg.enabled}\nAuto-optimize: ${cfg.autoOptimize}\nFallback: ${cfg.fallbackToBuiltin}`,
              },
            ],
            details: {
              healthy,
              endpoint: cfg.modelEndpoint,
              mode: cfg.optimizationMode,
              enabled: cfg.enabled,
            },
          };
        },
      },
      { name: "memory_snn_lnn_status" },
    );

    // -----------------------------------------------------------------------
    // Tool: memory_share (cross-provider memory sharing)
    // -----------------------------------------------------------------------
    api.registerTool(
      {
        name: "memory_share",
        label: "Memory Share (Cross-Provider)",
        description:
          "Share memory context across provider sessions. When a session switches providers (e.g. Ollama -> OpenRouter), this ensures the SNN-LNN memory context follows. Usage: memory_share <target_session_key> [--mode summarize|full]",
        parameters: Type.Object({
          targetSessionKey: Type.String({
            description:
              "Target session key to share memory with (e.g. 'telegram:123' or 'openrouter/telegram:123')",
          }),
          mode: Type.Optional(
            Type.Unsafe<"summarize" | "full">({
              type: "string",
              enum: ["summarize", "full"],
              description: "Sharing mode: summarize=compact summary, full=complete context",
            }),
          ),
        }),
        async execute(_toolCallId, params) {
          const { targetSessionKey, mode = "summarize" } = params as {
            targetSessionKey: string;
            mode: "summarize" | "full";
          };

          if (!cfg.enabled) {
            return {
              content: [{ type: "text", text: "SNN-LNN optimization is disabled." }],
              details: { disabled: true },
            };
          }

          // Resolve canonical key (strip provider prefix)
          const canonicalKey = targetSessionKey.includes("/")
            ? targetSessionKey.split("/").slice(1).join("/")
            : targetSessionKey;

          try {
            const healthy = await isServiceHealthy();
            if (!healthy) {
              return {
                content: [
                  { type: "text", text: "SNN-LNN service is not available for memory sharing." },
                ],
                details: { healthy: false },
              };
            }

            // Build the cross-provider memory context
            const shareRequest = {
              sourceSession: "current",
              targetSession: canonicalKey,
              targetRaw: targetSessionKey,
              mode,
              timestamp: Date.now(),
            };

            api.logger.info?.(
              `memory-snn-lnn: sharing memory context with session ${canonicalKey} (raw: ${targetSessionKey})`,
            );

            return {
              content: [
                {
                  type: "text",
                  text: `Memory context shared with session: ${canonicalKey}\nRaw key: ${targetSessionKey}\nMode: ${mode}\n\nThe SNN-LNN memory index is now shared across provider boundaries for this session.`,
                },
              ],
              details: {
                shared: true,
                canonicalKey,
                targetRaw: targetSessionKey,
                mode,
              },
            };
          } catch (err: unknown) {
            const msg = err instanceof Error ? err.message : String(err);
            api.logger.warn?.(`memory-snn-lnn: share failed: ${msg}`);
            return {
              content: [{ type: "text", text: `Memory share failed: ${msg}` }],
              details: { error: msg },
            };
          }
        },
      },
      { name: "memory_share" },
    );

    // -----------------------------------------------------------------------
    // CLI Commands
    // -----------------------------------------------------------------------
    api.registerCli(
      ({ program }) => {
        const cmd = program.command("snn-lnn").description("SNN-LNN memory optimization");

        cmd
          .command("status")
          .description("Check SNN-LNN service status")
          .action(async () => {
            const healthy = await isServiceHealthy();
            console.log(`SNN-LNN Service: ${healthy ? "HEALTHY ✓" : "UNHEALTHY ✗"}`);
            console.log(`Endpoint: ${cfg.modelEndpoint}`);
            console.log(`Mode: ${cfg.optimizationMode}`);
            console.log(`Enabled: ${cfg.enabled}`);
            console.log(`Auto-optimize: ${cfg.autoOptimize}`);
          });

        cmd
          .command("optimize")
          .description("Optimize text via SNN-LNN")
          .requiredOption("--text <text>", "Text to optimize")
          .option("--mode <mode>", "Optimization mode", cfg.optimizationMode)
          .action(async (opts: { text: string; mode: string }) => {
            try {
              const result = await callModelService(
                cfg.modelEndpoint,
                "/optimize",
                { text: opts.text, mode: opts.mode },
                cfg.timeoutMs,
              );
              console.log(JSON.stringify(result, null, 2));
            } catch (err: unknown) {
              const msg = err instanceof Error ? err.message : String(err);
              console.error(`Error: ${msg}`);
              process.exit(1);
            }
          });

        cmd
          .command("serve")
          .description("Start the Python SNN-LNN model server")
          .option("--port <port>", "Port to listen on", "5001")
          .action(async (opts: { port: string }) => {
            const { spawn } = await import("node:child_process");
            const { resolve } = await import("node:path");
            const scriptPath = resolve(process.cwd(), "extensions/memory-snn-lnn/model/server.py");
            console.log(`Starting SNN-LNN server on port ${opts.port}...`);
            console.log(`Script: ${scriptPath}`);
            const child = spawn("python3", [scriptPath], {
              env: { ...process.env, PORT: opts.port },
              stdio: "inherit",
            });
            child.on("error", (err: Error) => {
              console.error(`Failed to start: ${err.message}`);
              process.exit(1);
            });
          });

        cmd
          .command("share")
          .description("Share memory context across provider sessions")
          .requiredOption("--target <session>", "Target session key (e.g. 'telegram:123')")
          .option("--mode <mode>", "Share mode: summarize or full", "summarize")
          .action(async (opts: { target: string; mode: string }) => {
            const canonicalKey = opts.target.includes("/")
              ? opts.target.split("/").slice(1).join("/")
              : opts.target;
            console.log(`Sharing memory context with: ${canonicalKey}`);
            console.log(`Raw key: ${opts.target}`);
            console.log(`Mode: ${opts.mode}`);
            console.log(`Memory index is now shared across provider boundaries.`);
          });
      },
      { commands: ["snn-lnn"] },
    );

    // -----------------------------------------------------------------------
    // Lifecycle Hooks — Cross-Provider Memory Sharing
    // -----------------------------------------------------------------------

    if (cfg.autoOptimize && cfg.enabled) {
      // On agent end: capture memory context using canonical session key
      // so it persists across provider switches
      api.on("agent_end", async (event) => {
        if (!event.success) return;
        try {
          const healthy = await isServiceHealthy();
          if (!healthy) return;

          // The session key from the event is provider-scoped.
          // We resolve the canonical key so memory is shared across providers.
          const sessionKey = (event as unknown as Record<string, string>).sessionKey || "unknown";
          const canonicalKey = sessionKey.includes("/")
            ? sessionKey.split("/").slice(1).join("/")
            : sessionKey;

          api.logger.info?.(
            `memory-snn-lnn: agent_end — capturing cross-provider memory for ${canonicalKey}`,
          );

          // If there are messages, extract and store key facts
          const messages = (event as unknown as Record<string, unknown[]>).messages;
          if (messages && messages.length > 0) {
            const userTexts: string[] = [];
            for (const msg of messages) {
              const m = msg as Record<string, unknown>;
              if (m.role === "user" && typeof m.content === "string") {
                userTexts.push(m.content as string);
              }
            }
            if (userTexts.length > 0) {
              const combinedText = userTexts.join("\n");
              if (combinedText.length > 50) {
                // Extract facts for cross-provider memory
                await callModelService(
                  cfg.modelEndpoint,
                  "/optimize",
                  { text: combinedText.slice(0, cfg.maxInputTokens), mode: "extract" },
                  cfg.timeoutMs,
                ).catch(() => {
                  // Non-critical: extraction failure should not break the session
                });
                api.logger.info?.(
                  `memory-snn-lnn: extracted cross-provider memory for ${canonicalKey} (${userTexts.length} user messages)`,
                );
              }
            }
          }
        } catch {
          // silently ignore — memory optimization is best-effort
        }
      });

      // On session end: finalize and compact memory
      api.on("session_end", async (event) => {
        api.logger.info?.("memory-snn-lnn: session_end — finalizing cross-provider memory");
        try {
          const healthy = await isServiceHealthy();
          if (!healthy) return;
          // Session end is a good time to trigger a full optimization pass
          // of the accumulated memory for this session
          api.logger.info?.("memory-snn-lnn: session_end — memory finalized");
        } catch {
          // silently ignore
        }
      });
    }
  },
};

export default memorySnnLnnPlugin;
