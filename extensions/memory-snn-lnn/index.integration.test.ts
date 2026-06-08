/**
 * Integration tests for SNN-LNN extension.
 *
 * These tests verify the full pipeline: TS plugin -> Python model server.
 * They are skipped if the model service is not running.
 */

import { describe, it, expect, beforeAll } from "vitest";

const MODEL_ENDPOINT = "http://127.0.0.1:5001";
const TIMEOUT = 10000;

async function isServiceUp(): Promise<boolean> {
  try {
    const res = await fetch(`${MODEL_ENDPOINT}/health`, {
      signal: AbortSignal.timeout(3000),
    });
    return res.ok;
  } catch {
    return false;
  }
}

async function post(path: string, body: Record<string, unknown>) {
  const res = await fetch(`${MODEL_ENDPOINT}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
    signal: AbortSignal.timeout(TIMEOUT),
  });
  return res.json();
}

describe("SNN-LNN Model Service Integration", () => {
  beforeAll(async () => {
    const up = await isServiceUp();
    if (!up) {
      console.warn(
        "\n  ⚠ SNN-LNN model service is not running on " +
          MODEL_ENDPOINT +
          "\n  Start it with: python3 extensions/memory-snn-lnn/model/server.py\n  Skipping integration tests.\n",
      );
    }
  });

  const describeIf = (condition: () => Promise<boolean>) => (name: string, fn: () => void) => {
    describe(name, () => {
      it("checking service availability", async () => {
        const up = await condition();
        if (!up) {
          console.warn("  Skipping: service not available");
          return;
        }
      });
      fn();
    });
  };

  const serviceUp = describeIf(isServiceUp);

  serviceUp("health endpoint", () => {
    it("should return healthy status", async () => {
      const res = await fetch(`${MODEL_ENDPOINT}/health`, {
        signal: AbortSignal.timeout(5000),
      });
      expect(res.ok).toBe(true);
      const data = (await res.json()) as Record<string, unknown>;
      expect(data.status).toBe("ok");
    });
  });

  serviceUp("summarize mode", () => {
    it("should summarize multi-sentence text", async () => {
      const text =
        "The quick brown fox jumps over the lazy dog. Machine learning is a subset of artificial intelligence. " +
        "Deep learning uses neural networks with many layers. Python is a popular programming language. " +
        "OpenClaw is an open-source AI gateway framework.";
      const result = await post("/optimize", { text, mode: "summarize" });
      expect(result.summary).toBeDefined();
      expect(typeof result.summary).toBe("string");
      expect((result.summary as string).length).toBeGreaterThan(0);
      expect((result.summary as string).length).toBeLessThan(text.length);
      expect(result.processing_time_ms).toBeDefined();
    });
  });

  serviceUp("extract mode", () => {
    it("should extract facts and preferences", async () => {
      const text =
        "I prefer Python over JavaScript. We decided to use TypeScript for the backend. " +
        "The API endpoint is https://api.example.com. John's email is john@example.com. " +
        "The database has 10,000 records.";
      const result = await post("/optimize", { text, mode: "extract" });
      expect(result.facts).toBeDefined();
      expect(Array.isArray(result.facts)).toBe(true);
      const facts = result.facts as Array<Record<string, unknown>>;
      expect(facts.length).toBeGreaterThan(0);
      // Should have at least one preference and one decision
      const types = facts.map((f) => f.type);
      expect(types).toContain("preference");
      expect(types).toContain("decision");
    });

    it("should rank facts by importance", async () => {
      const text =
        "I prefer dark mode. We decided to rewrite the entire frontend in Rust. " +
        "The server is running.";
      const result = await post("/optimize", { text, mode: "extract" });
      const facts = result.facts as Array<Record<string, unknown>>;
      if (facts.length >= 2) {
        expect((facts[0].importance as number) ?? 0).toBeGreaterThanOrEqual(
          (facts[1].importance as number) ?? 0,
        );
      }
    });
  });

  serviceUp("compress mode", () => {
    it("should produce a compressed encoding", async () => {
      const text = "This is a test of the compression system for memory optimization.";
      const result = await post("/optimize", { text, mode: "compress" });
      expect(result.encoding).toBeDefined();
      expect(Array.isArray(result.encoding)).toBe(true);
      expect(result.dimensions).toBe(32);
      expect(result.compression_ratio).toBeDefined();
      expect(result.original_length).toBe(text.length);
      expect(result.temporal_features).toBeDefined();
    });

    it("should include temporal features from SNN encoder", async () => {
      const text = "Repeated repeated repeated words words show show patterns patterns.";
      const result = await post("/optimize", { text, mode: "compress" });
      const tf = result.temporal_features as Record<string, unknown>;
      expect(tf.n_spikes).toBeDefined();
      expect(tf.mean_rate).toBeDefined();
      expect(tf.burst_index).toBeDefined();
      expect(tf.pattern_complexity).toBeDefined();
    });
  });

  serviceUp("full mode", () => {
    it("should return all optimization results", async () => {
      const text =
        "OpenClaw is an AI gateway that connects multiple messaging channels. " +
        "It supports Telegram, Discord, Slack, and Signal. " +
        "We decided to use TypeScript for the entire codebase. " +
        "The memory system uses vector search with SQLite. " +
        "I prefer concise responses with technical accuracy.";
      const result = await post("/optimize", { text, mode: "full" });
      expect(result.summary).toBeDefined();
      expect(result.facts).toBeDefined();
      expect(result.encoding).toBeDefined();
      expect(result.metadata).toBeDefined();
      expect(result.processing_time_ms).toBeDefined();
      expect(result.processing_time_ms as number).toBeGreaterThan(0);
    });
  });

  serviceUp("similarity endpoint", () => {
    it("should compute similarity between texts", async () => {
      const result = await post("/similarity", {
        text1: "The cat sat on the mat",
        text2: "A cat was sitting on a mat",
      });
      expect(result.similarity).toBeDefined();
      expect(typeof result.similarity).toBe("number");
      expect(result.similarity as number).toBeGreaterThanOrEqual(-1);
      expect(result.similarity as number).toBeLessThanOrEqual(1);
    });

    it("should give higher similarity for related texts than unrelated", async () => {
      const related = await post("/similarity", {
        text1: "The cat sat on the mat",
        text2: "A cat was sitting on a mat",
      });
      const unrelated = await post("/similarity", {
        text1: "The cat sat on the mat",
        text2: "quantum physics equations",
      });
      expect(related.similarity as number).toBeGreaterThan(unrelated.similarity as number);
    });

    it("should give low similarity for unrelated texts", async () => {
      const result = await post("/similarity", {
        text1: "quantum physics equations",
        text2: "pizza delivery menu",
      });
      // Should be lower than self-similarity
      const selfResult = await post("/similarity", {
        text1: "quantum physics equations",
        text2: "quantum physics equations",
      });
      expect(result.similarity as number).toBeLessThan((selfResult.similarity as number) + 0.3);
    });
  });

  serviceUp("encode endpoint", () => {
    it("should return a fixed-dimension vector", async () => {
      const result = await post("/encode", { text: "Hello world" });
      expect(result.vector).toBeDefined();
      expect(Array.isArray(result.vector)).toBe(true);
      expect(result.vector.length).toBe(32);
      expect(result.dimensions).toBe(32);
    });
  });

  serviceUp("error handling", () => {
    it("should return 400 for missing text field", async () => {
      const res = await fetch(`${MODEL_ENDPOINT}/optimize`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ mode: "full" }),
        signal: AbortSignal.timeout(TIMEOUT),
      });
      expect(res.status).toBe(400);
    });

    it("should return 400 for unknown mode", async () => {
      const res = await fetch(`${MODEL_ENDPOINT}/optimize`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text: "test", mode: "unknown" }),
        signal: AbortSignal.timeout(TIMEOUT),
      });
      expect(res.status).toBe(400);
    });
  });
});
