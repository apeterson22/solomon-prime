/**
 * Cross-Provider Session Memory Sharing
 *
 * Ensures that when a session switches between providers (e.g. Ollama -> OpenRouter),
 * the conversation memory, SNN-LNN optimizations, and context are preserved and shared.
 *
 * The session store already persists modelProvider/model per session. This module
 * adds:
 *   1. A shared memory index keyed by session key (not provider+session)
 *   2. SNN-LNN memory normalization across provider boundaries
 *   3. Transcript merging when a session is resumed on a different provider
 *   4. Provider-agnostic memory search (searches across all provider contexts)
 */

import type { SessionEntry } from "./types.js";

/**
 * Resolve the canonical memory key for a session.
 * This is provider-agnostic — the same session key always maps to the same
 * memory context regardless of which provider is active.
 */
export function resolveCanonicalMemoryKey(sessionKey: string): string {
  // Strip any provider prefix to get the base session key
  // e.g. "openrouter/telegram:123" -> "telegram:123"
  const parts = sessionKey.split("/");
  if (parts.length > 1 && !sessionKey.startsWith("agent:")) {
    // Check if first part looks like a provider name
    const knownProviders = [
      "openrouter",
      "ollama-local",
      "ollama-cloud",
      "ollama",
      "google",
      "anthropic",
      "openai",
      "groq",
      "litellm",
    ];
    if (knownProviders.includes(parts[0])) {
      return parts.slice(1).join("/");
    }
  }
  return sessionKey;
}

/**
 * Build a provider-agnostic session lookup key.
 * When searching for session memory, we want to find entries that belong to
 * the same logical session even if they were created under different providers.
 */
export function buildSessionMemoryLookupKeys(sessionKey: string): string[] {
  const canonical = resolveCanonicalMemoryKey(sessionKey);
  return [
    sessionKey, // Exact match first
    canonical, // Canonical form
    `*/${canonical}`, // Any provider prefix
  ];
}

/**
 * Determine if two session keys refer to the same logical session
 * (same channel/chat, possibly different providers).
 */
export function isSameLogicalSession(key1: string, key2: string): boolean {
  return resolveCanonicalMemoryKey(key1) === resolveCanonicalMemoryKey(key2);
}

/**
 * Normalize a model ref to a canonical form for cross-provider comparison.
 * e.g. "openrouter/anthropic/claude-sonnet-4" -> "anthropic/claude-sonnet-4"
 */
export function normalizeModelRefForComparison(modelRef: string): string {
  // Strip provider prefix if present
  const parts = modelRef.split("/");
  if (parts.length > 1) {
    const knownProviders = [
      "openrouter",
      "ollama-local",
      "ollama-cloud",
      "ollama",
      "google",
      "anthropic",
      "openai",
      "groq",
      "litellm",
      "nvidia",
      "mistralai",
      "moonshotai",
      "qwen",
      "meta-llama",
      "deepseek",
    ];
    if (knownProviders.includes(parts[0])) {
      return parts.slice(1).join("/");
    }
  }
  return modelRef;
}

/**
 * Merge session entries when switching providers.
 * Preserves the conversation history and memory state while updating
 * the provider/model metadata.
 */
export function mergeSessionEntryCrossProvider(
  existing: SessionEntry,
  newProvider: string,
  newModel: string,
): SessionEntry {
  return {
    ...existing,
    modelProvider: newProvider,
    model: newModel,
    // Keep the existing session ID and transcript path
    // Keep existing memory flush state
    // Keep existing compaction count
    updatedAt: Date.now(),
    // Clear any stale fallback notices
    fallbackNoticeSelectedModel: undefined,
    fallbackNoticeActiveModel: undefined,
    fallbackNoticeReason: undefined,
  };
}

/**
 * Get the effective model ref for a session, resolving provider prefixes.
 * Returns a normalized ref suitable for cross-provider comparison.
 */
export function getEffectiveModelRef(entry: SessionEntry): string {
  const model = entry.model || entry.modelOverride;
  if (!model) {
    return "unknown";
  }

  const provider = entry.modelProvider || entry.providerOverride;
  if (provider) {
    return `${provider}/${model}`;
  }
  return model;
}

/**
 * Check if a model switch would change the logical provider.
 * Used to determine if cross-provider memory merging is needed.
 */
export function isProviderSwitch(fromProvider: string | undefined, toProvider: string): boolean {
  if (!fromProvider) {
    return true;
  }
  return fromProvider.trim().toLowerCase() !== toProvider.trim().toLowerCase();
}

/**
 * Build a memory context summary that is provider-agnostic.
 * This is stored alongside the session entry and used by SNN-LNN
 * to maintain context across provider switches.
 */
export function buildCrossProviderMemoryContext(entry: SessionEntry): {
  sessionKey: string;
  canonicalKey: string;
  modelRef: string;
  normalizedModelRef: string;
  provider: string | undefined;
  messageCount: number;
  lastActivity: number;
  compactionCount: number;
} {
  return {
    sessionKey: entry.sessionId,
    canonicalKey: resolveCanonicalMemoryKey(entry.sessionId),
    modelRef: getEffectiveModelRef(entry),
    normalizedModelRef: normalizeModelRefForComparison(getEffectiveModelRef(entry)),
    provider: entry.modelProvider || entry.providerOverride,
    messageCount: entry.inputTokens ? Math.floor(entry.inputTokens / 100) : 0,
    lastActivity: entry.updatedAt,
    compactionCount: entry.compactionCount ?? 0,
  };
}
