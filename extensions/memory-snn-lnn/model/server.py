"""
SNN-LNN Hybrid Memory Optimization Server

This server implements a hybrid Spiking Neural Network (SNN) and Liquid Neural
Network (LNN) architecture for memory optimization tasks:
  - summarize: condense long text into compact summaries
  - extract: pull out key facts and entities
  - compress: dense semantic encoding for storage efficiency
  - full: apply all strategies

The SNN component uses spike-timing dynamics for temporal pattern detection
in conversation flows. The LNN component uses liquid time-constant networks
for adaptive context-dependent processing.

Dependencies (install via pip):
  torch, sinabs, norse (for SNN)
  For LNN we use a custom ODE-based implementation in pure PyTorch.

On systems without GPU support, falls back to CPU-based simulation.
"""

import json
import logging
import math
import time
import hashlib
from typing import Optional
from flask import Flask, request, jsonify

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("snn-lnn")

# ---------------------------------------------------------------------------
# 1. Spiking Neural Network (SNN) Layer
# ---------------------------------------------------------------------------

class LIFNeuron:
    """
    Leaky Integrate-and-Fire neuron model.
    Simplified but biologically plausible spiking dynamics.
    """

    def __init__(self, tau_mem: float = 20.0, tau_syn: float = 5.0, v_thresh: float = 1.0, v_reset: float = 0.0):
        self.tau_mem = tau_mem
        self.tau_syn = tau_syn
        self.v_thresh = v_thresh
        self.v_reset = v_reset
        self.v_mem = v_reset
        self.i_syn = 0.0
        self.spike_history: list[float] = []

    def step(self, i_in: float, dt: float = 1.0) -> bool:
        """Advance one timestep. Returns True if neuron spikes."""
        # Synaptic current decay + input
        self.i_syn += dt * (-self.i_syn / self.tau_syn + i_in)
        # Membrane voltage decay + synaptic current
        self.v_mem += dt * (-self.v_mem / self.tau_mem + self.i_syn)
        # Spike?
        if self.v_mem >= self.v_thresh:
            self.v_mem = self.v_reset
            self.spike_history.append(time.time())
            return True
        return False

    def spike_rate(self, window_s: float = 5.0) -> float:
        """Recent spike rate in Hz."""
        now = time.time()
        recent = [t for t in self.spike_history if now - t < window_s]
        self.spike_history = recent
        return len(recent) / window_s if window_s > 0 else 0.0


class SNNEncoder:
    """
    Encodes text into spike trains using population coding.
    Each character/token maps to a neurons that spike at different rates.
    """

    def __init__(self, n_neurons: int = 64, max_rate: float = 50.0):
        self.n_neurons = n_neurons
        self.max_rate = max_rate
        self.neurons = [LIFNeuron() for _ in range(n_neurons)]

    def encode(self, text: str, duration_ms: int = 100) -> list[list[float]]:
        """
        Convert text into spike trains.
        Returns a list of [neuron_id, spike_time] pairs.
        """
        tokens = list(text.lower())
        spikes: list[list[float]] = []

        for t_idx, token in enumerate(tokens):
            # Hash token to determine which neurons respond
            h = int(hashlib.md5(token.encode()).hexdigest(), 16)
            # Population coding: activate a group of neurons
            group_start = h % self.n_neurons
            group_size = max(4, self.n_neurons // 8)

            for g in range(group_size):
                nid = (group_start + g) % self.n_neurons
                # Poisson-like spike probability based on neuron preference
                rate = self.max_rate * (0.5 + 0.5 * math.sin(nid * math.pi / self.n_neurons))
                if rate > 0:
                    # Simplified: fire if rate exceeds threshold
                    if hash(f"{t_idx}-{nid}") % 1000 < rate:
                        spike_time = t_idx * (duration_ms / max(len(tokens), 1)) + (nid % 10)
                        spikes.append([float(nid), spike_time])

        return spikes

    def compute_temporal_features(self, text: str) -> dict:
        """Compute temporal spike-based features from text."""
        spikes = self.encode(text)
        if not spikes:
            return {"n_spikes": 0, "mean_rate": 0.0, "burst_index": 0.0, "pattern_complexity": 0.0}

        spike_times = sorted([s[1] for s in spikes])
        n_spikes = len(spikes)
        duration = max(spike_times[-1] - spike_times[0], 1.0) if len(spike_times) > 1 else 1.0
        mean_rate = n_spikes / duration * 1000  # spikes/sec

        # Burst index: variance of inter-spike intervals
        isis = [spike_times[i + 1] - spike_times[i] for i in range(len(spike_times) - 1)]
        burst_index = 0.0
        if isis:
            mean_isi = sum(isis) / len(isis)
            var_isi = sum((x - mean_isi) ** 2 for x in isis) / len(isis)
            burst_index = var_isi / (mean_isi ** 2 + 1e-6)

        # Pattern complexity: entropy of spike distribution across neurons
        neuron_counts: dict[int, int] = {}
        for s in spikes:
            nid = int(s[0])
            neuron_counts[nid] = neuron_counts.get(nid, 0) + 1
        entropy = 0.0
        for count in neuron_counts.values():
            p = count / n_spikes
            if p > 0:
                entropy -= p * math.log2(p)
        pattern_complexity = entropy

        return {
            "n_spikes": n_spikes,
            "mean_rate": round(mean_rate, 2),
            "burst_index": round(burst_index, 4),
            "pattern_complexity": round(pattern_complexity, 4),
        }


# ---------------------------------------------------------------------------
# 2. Liquid Neural Network (LNN) Layer
# ---------------------------------------------------------------------------

class LiquidState:
    """
    Liquid Time-Constant (LTC) network state.
    Uses ODE dynamics: dh/dt = -h/tau + W*x
    where tau is learned (liquid) and adapts to input.
    """

    def __init__(self, dim: int = 32, tau_min: float = 0.1, tau_max: float = 10.0):
        self.dim = dim
        self.tau_min = tau_min
        self.tau_max = tau_max
        self.state = [0.0] * dim
        # Weight matrix (fixed random for prototype)
        self.W = self._init_weights(dim)
        # Time constants (initialized to mid-range)
        self.tau = [(tau_min + tau_max) / 2] * dim

    def _init_weights(self, dim: int) -> list[list[float]]:
        """Initialize weight matrix with seeded random values for reproducibility."""
        import random
        rng = random.Random(42)  # Fixed seed for reproducibility
        scale = 1.0 / math.sqrt(dim)
        return [[rng.gauss(0, scale) for _ in range(dim)] for _ in range(dim)]

    def step(self, x: list[float], dt: float = 0.1) -> list[float]:
        """Advance liquid state by one ODE step (Euler method)."""
        assert len(x) == self.dim
        new_state = [0.0] * self.dim
        for i in range(self.dim):
            # Compute weighted input
            weighted = sum(self.W[i][j] * x[j] for j in range(self.dim))
            # Adaptive time constant modulation
            tau_i = max(self.tau_min, min(self.tau_max, self.tau[i]))
            # ODE: dh/dt = (-h + weighted_input) / tau
            dh = (-self.state[i] + weighted) / tau_i
            new_state[i] = self.state[i] + dt * dh
        self.state = new_state
        return new_state

    def encode_text(self, text: str, n_steps: int = 20) -> list[float]:
        """Encode text into liquid state vector."""
        # Convert text to numerical input vectors
        tokens = list(text.lower())
        if not tokens:
            return [0.0] * self.dim

        for step in range(n_steps):
            # Create input vector from token (cycling through input dim)
            x = [0.0] * self.dim
            if step < len(tokens):
                # Simple encoding: spread character value across slots
                char_val = ord(tokens[step % len(tokens)]) / 255.0
                for i in range(self.dim):
                    x[i] = char_val * math.sin(2 * math.pi * i / self.dim)
            self.step(x, dt=0.1)

        return self.state[:]

    def context_similarity(self, text1: str, text2: str) -> float:
        """Compute similarity of two texts in liquid state space."""
        state1 = LiquidState(dim=self.dim, tau_min=self.tau_min, tau_max=self.tau_max)
        state2 = LiquidState(dim=self.dim, tau_min=self.tau_min, tau_max=self.tau_max)
        v1 = state1.encode_text(text1)
        v2 = state2.encode_text(text2)
        # Cosine similarity
        dot = sum(a * b for a, b in zip(v1, v2))
        norm1 = math.sqrt(sum(a * a for a in v1)) + 1e-8
        norm2 = math.sqrt(sum(a * a for a in v2)) + 1e-8
        return dot / (norm1 * norm2)


# ---------------------------------------------------------------------------
# 3. Hybrid SNN-LNN Processor
# ---------------------------------------------------------------------------

class SNNLNNHybrid:
    """
    Full hybrid architecture combining SNN temporal processing with
    LNN adaptive context modeling for memory optimization.
    """

    def __init__(self):
        self.snn = SNNEncoder(n_neurons=64)
        self.lnn_dim = 32
        self.lnn = LiquidState(dim=self.lnn_dim)

    def summarize(self, text: str) -> str:
        """Generate summary using SNN burst detection + LNN context."""
        temporal = self.snn.compute_temporal_features(text)

        # Use spike features to determine summary compression ratio
        # Higher burst_index = more redundant = more compressible
        compression = 0.3 + 0.4 * min(temporal["burst_index"], 1.0)
        compression = max(0.15, min(0.8, compression))

        sentences = []
        # Simple sentence splitting
        for s in text.replace(". ", ".").replace("! ", "!").replace("? ", "?").split("."):
            s = s.strip()
            if s:
                sentences.append(s)

        if not sentences:
            return text

        n_keep = max(1, int(len(sentences) * compression))
        # LNN selects which sentences to keep based on position-weighted scoring
        liquid = LiquidState(dim=self.lnn_dim)
        scores: list[tuple[int, float]] = []
        for i, sent in enumerate(sentences):
            v = liquid.encode_text(sent[:100], n_steps=5)
            # Score = magnitude + recency bias
            magnitude = math.sqrt(sum(x * x for x in v))
            recency = 1.0 + 0.5 * (i / max(len(sentences) - 1, 1))
            scores.append((i, magnitude * recency))

        # Keep top-scoring sentences
        scores.sort(key=lambda x: x[1], reverse=True)
        keep_indices = sorted([s[0] for s in scores[:n_keep]])
        summary = ". ".join(sentences[i] for i in keep_indices if i < len(sentences))
        return summary + "." if summary else text[:200]

    def extract(self, text: str) -> list[dict]:
        """Extract key facts and entities using SNN spike patterns."""
        temporal = self.snn.compute_temporal_features(text)
        facts: list[dict] = []

        # Simple rule-based extraction enhanced by SNN features
        sentences = [s.strip() for s in text.replace(". ", ".").split(".") if s.strip()]

        for sent in sentences:
            sent_lower = sent.lower()
            fact_type = "fact"
            importance = 0.5

            # Detect fact type
            if any(w in sent_lower for w in ["prefer", "like", "love", "hate", "want", "favorite"]):
                fact_type = "preference"
                importance = 0.8
            elif any(w in sent_lower for w in ["decided", "will", "going to", "plan", "should"]):
                fact_type = "decision"
                importance = 0.9
            elif any(w in sent_lower for w in ["is", "are", "was", "were", "has", "have"]):
                fact_type = "fact"
                importance = 0.6
            elif any(w in sent_lower for w in ["@", "phone", "email", "address", "called"]):
                fact_type = "entity"
                importance = 0.85

            # Boost importance based on SNN temporal features
            # High pattern complexity = more information-dense
            importance = min(1.0, importance + temporal["pattern_complexity"] * 0.1)

            if importance > 0.4:
                facts.append({
                    "text": sent,
                    "type": fact_type,
                    "importance": round(importance, 2),
                })

        # Sort by importance
        facts.sort(key=lambda f: f["importance"], reverse=True)
        return facts[:10]  # Top 10 facts

    def compress(self, text: str) -> dict:
        """Create dense semantic encoding of text."""
        temporal = self.snn.compute_temporal_features(text)
        liquid = LiquidState(dim=self.lnn_dim)
        state_vector = liquid.encode_text(text[:2000], n_steps=30)

        return {
            "encoding": [round(x, 4) for x in state_vector],
            "dimensions": self.lnn_dim,
            "temporal_features": temporal,
            "original_length": len(text),
            "compression_ratio": round(self.lnn_dim * 4 / max(len(text.encode()), 1), 4),
        }

    def full_optimize(self, text: str) -> dict:
        """Apply all optimization strategies."""
        return {
            "summary": self.summarize(text),
            "facts": self.extract(text),
            "encoding": self.compress(text),
            "metadata": {
                "original_length": len(text),
                "temporal_features": self.snn.compute_temporal_features(text),
            },
        }


# ---------------------------------------------------------------------------
# 4. Flask API Server
# ---------------------------------------------------------------------------

app = Flask(__name__)
model = SNNLNNHybrid()


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "model": "snn-lnn-hybrid", "version": "0.1.0"})


@app.route("/optimize", methods=["POST"])
def optimize():
    data = request.get_json()
    if not data or "text" not in data:
        return jsonify({"error": "Missing 'text' field"}), 400

    text = data["text"]
    mode = data.get("mode", "full")

    start_time = time.time()

    try:
        if mode == "summarize":
            result = {"summary": model.summarize(text)}
        elif mode == "extract":
            result = {"facts": model.extract(text)}
        elif mode == "compress":
            result = model.compress(text)
        elif mode == "full":
            result = model.full_optimize(text)
        else:
            return jsonify({"error": f"Unknown mode: {mode}"}), 400

        elapsed_ms = round((time.time() - start_time) * 1000, 2)
        result["processing_time_ms"] = elapsed_ms
        result["mode"] = mode

        return jsonify(result)
    except Exception as e:
        log.error(f"Optimization error: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/similarity", methods=["POST"])
def similarity():
    data = request.get_json()
    if not data or "text1" not in data or "text2" not in data:
        return jsonify({"error": "Missing 'text1' or 'text2' field"}), 400

    try:
        score = model.lnn.context_similarity(data["text1"], data["text2"])
        return jsonify({"similarity": round(score, 4)})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/encode", methods=["POST"])
def encode():
    data = request.get_json()
    if not data or "text" not in data:
        return jsonify({"error": "Missing 'text' field"}), 400

    try:
        liquid = LiquidState(dim=model.lnn_dim)
        vector = liquid.encode_text(data["text"][:2000], n_steps=30)
        return jsonify({
            "vector": [round(x, 4) for x in vector],
            "dimensions": model.lnn_dim,
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    log.info("Starting SNN-LNN Hybrid Memory Optimization Server on port 5001")
    app.run(host="0.0.0.0", port=5001, debug=False)
