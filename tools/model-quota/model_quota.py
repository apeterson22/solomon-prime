#!/usr/bin/env python3
"""
Model quota tracker and auto-switcher for Hermes Agent.
Tracks usage, monitors quotas, and switches between free/local models.

Usage:
  python3 model_quota.py status          -- Show current model and quota status
  python3 model_quota.py switch <model>  -- Switch to a specific model
  python3 model_quota.py auto            -- Auto-select best available model
  python3 model_quota.py health          -- Run health check on all models
  python3 model_quota.py reset           -- Reset all health scores
  python3 model_quota.py record <model> <tokens> <success> -- Record usage
"""

import json
import sys
import os
import time
import subprocess
from pathlib import Path
from datetime import datetime, timezone

QUOTA_FILE = Path.home() / ".hermes" / "model-quota.json"
REGISTRY_FILE = Path.home() / ".hermes" / "model-registry.yaml"

DEFAULT_STATE = {
    "current_model": None,
    "models": {},
    "total_tokens_today": 0,
    "total_requests_today": 0,
    "daily_cost": 0.0,
    "last_reset": None,
    "health_checks": {}
}

def load_state() -> dict:
    if QUOTA_FILE.exists():
        with open(QUOTA_FILE) as f:
            return json.load(f)
    return DEFAULT_STATE.copy()

def save_state(state: dict):
    QUOTA_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(QUOTA_FILE, "w") as f:
        json.dump(state, f, indent=2, default=str)

def load_registry() -> dict:
    """Parse the YAML registry file."""
    import yaml
    with open(REGISTRY_FILE) as f:
        return yaml.safe_load(f)

def check_daily_reset(state: dict) -> dict:
    """Reset daily counters if it's a new day."""
    now = datetime.now(timezone.utc)
    last_reset = state.get("last_reset")
    if last_reset:
        last = datetime.fromisoformat(last_reset)
        if last.date() != now.date():
            state["total_tokens_today"] = 0
            state["total_requests_today"] = 0
            state["daily_cost"] = 0.0
            state["last_reset"] = now.isoformat()
            print(f"[quota] Daily counters reset ({now.strftime('%Y-%m-%d')})")
    else:
        state["last_reset"] = now.isoformat()
    return state

def check_ollama_healthy(model_id: str) -> bool:
    """Quick health check for Ollama models."""
    try:
        # Check if Ollama is running
        result = subprocess.run(
            ["ollama", "list"],
            capture_output=True, text=True, timeout=5
        )
        if result.returncode != 0:
            return False
        # Check if the specific model is available
        model_short = model_id.replace("ollama/", "")
        return model_short in result.stdout
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False

def check_openrouter_healthy(model_id: str) -> bool:
    """Quick health check for OpenRouter models (just check API reachability)."""
    try:
        import urllib.request
        req = urllib.request.Request(
            "https://openrouter.ai/api/v1/models",
            headers={"HTTP-Referer": "https://hermes-agent.local"},
            method="GET"
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.status == 200
    except Exception:
        return False

def get_model_health(state: dict, model_id: str) -> dict:
    """Get health info for a model."""
    health = state.get("health_checks", {}).get(model_id, {
        "errors": 0,
        "last_used": None,
        "last_error": None,
        "avg_response_time": 0,
        "total_calls": 0
    })
    return health

def is_model_available(state: dict, model_id: str, registry: dict) -> bool:
    """Check if a model is available and healthy."""
    health = get_model_health(state, model_id)
    
    # Check error threshold
    error_threshold = registry.get("policy", {}).get("error_threshold", 3)
    if health["errors"] >= error_threshold:
        return False
    
    # Provider-specific health checks
    if model_id.startswith("ollama/"):
        return check_ollama_healthy(model_id)
    elif model_id.startswith("openrouter/"):
        return check_openrouter_healthy(model_id)
    
    return True

def select_best_model(state: dict, registry: dict, task_type: str = "general") -> str:
    """Select the best available model for the given task type."""
    routing = registry.get("routing", {})
    policy = registry.get("policy", {})
    
    # Get preferred models for the task type
    task_routing = routing.get(task_type, routing.get("general", {}))
    preferred = task_routing.get("preferred", [])
    fallback = task_routing.get("fallback", [])
    
    all_models = preferred + fallback
    
    for model_id in all_models:
        if is_model_available(state, model_id, registry):
            return model_id
    
    # Ultimate fallback: any model from the registry
    for model in registry.get("models", []):
        if is_model_available(state, model["id"], registry):
            return model["id"]
    
    return None

def cmd_status(state: dict, registry: dict):
    """Show current status."""
    state = check_daily_reset(state)
    
    print(f"\n{'='*60}")
    print("  Hermes Model Quota & Health Status")
    print(f"{'='*60}")
    print(f"  Current model  : {state.get('current_model', 'NONE')}")
    print(f"  Tokens today   : {state.get('total_tokens_today', 0):,}")
    print(f"  Requests today : {state.get('total_requests_today', 0):,}")
    print(f"  Daily cost     : ${state.get('daily_cost', 0):.6f}")
    print(f"{'='*60}\n")
    
    print("  Model Health:")
    print(f"  {'Model':<55} {'Err':>4} {'Calls':>6} {'Avg ms':>8} {'Available':>10}")
    print(f"  {'-'*55} {'-'*4} {'-'*6} {'-'*8} {'-'*10}")
    
    for model in registry.get("models", []):
        mid = model["id"]
        h = get_model_health(state, mid)
        health_str = "YES" if is_model_available(state, mid, registry) else "NO"
        tier = model.get("tier", "?").upper()
        print(f"  {mid:<55} {h['errors']:>4} {h['total_calls']:>6} "
              f"{h['avg_response_time']:>7.0f} {health_str:>9} [{tier}]")
    
    print()

def cmd_switch(state: dict, registry: dict, model_id: str):
    """Switch to a specific model."""
    # Validate model exists in registry
    valid_ids = [m["id"] for m in registry.get("models", [])]
    if model_id not in valid_ids:
        print(f"[quota] ERROR: Unknown model '{model_id}'")
        print(f"  Valid models: {', '.join(valid_ids)}")
        sys.exit(1)
    
    state["current_model"] = model_id
    save_state(state)
    print(f"[quota] Switched to model: {model_id}")
    print(f"  Tier: {[m for m in registry['models'] if m['id']==model_id][0].get('tier', '?')}")
    print(f"  Provider: {[m for m in registry['models'] if m['id']==model_id][0].get('provider', '?')}")

def cmd_auto(state: dict, registry: dict, task_type: str = "general"):
    """Auto-select and switch to the best available model."""
    state = check_daily_reset(state)
    model_id = select_best_model(state, registry, task_type)
    
    if model_id:
        cmd_switch(state, registry, model_id)
        print(f"[quota] Auto-selected for task type: {task_type}")
    else:
        print("[quota] ERROR: No available models found!")
        sys.exit(1)

def cmd_health(state: dict, registry: dict):
    """Run health checks on all models and show status."""
    print("[quota] Running health checks...\n")
    
    for model in registry.get("models", []):
        mid = model["id"]
        start = time.time()
        healthy = is_model_available(state, mid, registry)
        elapsed = (time.time() - start) * 1000
        
        status = "HEALTHY" if healthy else "DOWN"
        print(f"  {mid:<55} {status:>8} ({elapsed:.0f}ms)")
    
    print()
    cmd_status(state, registry)

def cmd_reset(state: dict, registry: dict):
    """Reset all health scores."""
    state["health_checks"] = {}
    save_state(state)
    print("[quota] All health scores reset.")

def cmd_record(state: dict, registry: dict, model_id: str, tokens: int, success: bool):
    """Record usage for a model."""
    state = check_daily_reset(state)
    
    if "health_checks" not in state:
        state["health_checks"] = {}
    
    h = state["health_checks"].get(model_id, {
        "errors": 0,
        "last_used": None,
        "last_error": None,
        "avg_response_time": 0,
        "total_calls": 0
    })
    
    h["total_calls"] += 1
    h["last_used"] = datetime.now(timezone.utc).isoformat()
    
    if success:
        h["errors"] = 0  # Reset error count on success
    else:
        h["errors"] += 1
        h["last_error"] = datetime.now(timezone.utc).isoformat()
    
    state["health_checks"][model_id] = h
    state["total_tokens_today"] += tokens
    state["total_requests_today"] += 1
    
    # Update cost
    for model in registry.get("models", []):
        if model["id"] == model_id:
            cost = model.get("cost_per_1m_tokens", 0) * tokens / 1_000_000
            state["daily_cost"] += cost
            break
    
    save_state(state)
    status = "OK" if success else "FAIL"
    print(f"[quota] Recorded: {model_id} | {tokens} tokens | {status}")

def cmd_ollama_status():
    """Check if Ollama is running and list available models."""
    print(f"\n{'='*60}")
    print("  Ollama Local Model Status")
    print(f"{'='*60}\n")
    
    try:
        result = subprocess.run(
            ["ollama", "list", "--no-trunc"],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode == 0:
            print(result.stdout)
            print("  Ollama is RUNNING and models are available.")
        else:
            print("  Ollama returned an error.")
            print(f"  stderr: {result.stderr}")
    except FileNotFoundError:
        print("  Ollama is NOT installed.")
    except subprocess.TimeoutExpired:
        print("  Ollama is UNRESPONSIVE (timeout after 10s).")
    
    print()

def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    
    state = load_state()
    
    try:
        registry = load_registry()
    except Exception as e:
        print(f"[quota] WARNING: Could not load registry: {e}")
        registry = {"models": [], "policy": {}, "routing": {}}
    
    cmd = sys.argv[1]
    
    if cmd == "status":
        if len(sys.argv) > 2 and sys.argv[2] == "ollama":
            cmd_ollama_status()
        else:
            cmd_status(state, registry)
    elif cmd == "switch":
        if len(sys.argv) < 3:
            print("Usage: model_quota.py switch <model_id>")
            sys.exit(1)
        cmd_switch(state, registry, sys.argv[2])
    elif cmd == "auto":
        task = sys.argv[2] if len(sys.argv) > 2 else "general"
        cmd_auto(state, registry, task)
    elif cmd == "health":
        cmd_health(state, registry)
    elif cmd == "reset":
        cmd_reset(state, registry)
    elif cmd == "record":
        if len(sys.argv) < 5:
            print("Usage: model_quota.py record <model_id> <tokens> <success:true|false>")
            sys.exit(1)
        success = sys.argv[4].lower() in ("true", "1", "yes")
        cmd_record(state, registry, sys.argv[2], int(sys.argv[3]), success)
    else:
        print(f"Unknown command: {cmd}")
        print(__doc__)
        sys.exit(1)

if __name__ == "__main__":
    main()
