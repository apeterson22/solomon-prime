#!/usr/bin/env python3
"""
Hermes Model Switcher
Switches the active model in the Hermes configuration and optionally in Ollama.

Usage:
  python3 switch_model.py free          -- Switch to best available free cloud model
  python3 switch_model.py local         -- Switch to best available local model
  python3 switch_model.py <model_id>    -- Switch to a specific model
  python3 switch_model.py status         -- Show current model and available options
"""

import sys
import os
import json
import subprocess
import shutil
from pathlib import Path
from datetime import datetime

CONFIG_FILE = Path.home() / ".hermes" / "config.yaml"
REGISTRY_FILE = Path.home() / ".hermes" / "model-registry.yaml"
QUOTA_FILE = Path.home() / ".hermes" / "model-quota.json"
HARMONY_CLI = "hermes"

def load_yaml(path: Path) -> dict:
    """Load a YAML file."""
    import yaml
    with open(path) as f:
        return yaml.safe_load(f)

def save_yaml(path: Path, data: dict):
    """Save a YAML file."""
    import yaml
    with open(path, "w") as f:
        yaml.dump(data, f, default_flow_style=False, sort_keys=False, allow_unicode=True)

def get_current_model(config: dict) -> str:
    """Get the current model from config."""
    return config.get("model", {}).get("default", "unknown")

def get_current_provider(config: dict) -> str:
    """Get the current provider from config."""
    return config.get("model", {}).get("provider", "unknown")

def switch_model(model_id: str, registry: dict):
    """Switch Hermes to use a specified model."""
    
    # Determine provider from model ID
    if model_id.startswith("ollama/"):
        provider = "ollama-launch"
        actual_model = model_id.replace("ollama/", "")
        base_url = "http://127.0.0.1:11434/v1"
        api_key = "ollama"
    elif model_id.startswith("openrouter/"):
        provider = "openrouter"
        actual_model = model_id.replace("openrouter/", "")
        base_url = "https://openrouter.ai/api/v1"
        api_key = None  # Uses env var
    else:
        # Could be a direct model name like kimi-k2.6:cloud
        # Try to determine from registry
        for model in registry.get("models", []):
            if model["id"] == model_id:
                if model.get("type") == "local":
                    provider = "ollama-launch"
                    actual_model = model_id
                    base_url = "http://127.0.0.1:11434/v1"
                    api_key = "ollama"
                else:
                    provider = "openrouter"
                    actual_model = model_id
                    base_url = "https://openrouter.ai/api/v1"
                    api_key = None
                break
        else:
            print(f"[switch] Cannot determine provider for model: {model_id}")
            # Default to ollama
            provider = "ollama-launch"
            actual_model = model_id
            base_url = "http://127.0.0.1:11434/v1"
            api_key = "ollama"
    
    # Load existing config
    config = load_yaml(CONFIG_FILE)
    
    # Update model settings
    old_model = get_current_model(config)
    config["model"]["default"] = model_id
    config["model"]["provider"] = provider
    
    if base_url:
        config["model"]["base_url"] = base_url
    if api_key:
        config["model"]["api_key"] = api_key
    
    # Save config
    save_yaml(CONFIG_FILE, config)
    
    # Update quota state
    if QUOTA_FILE.exists():
        with open(QUOTA_FILE) as f:
            quota = json.load(f)
    else:
        quota = {"models": {}, "health_checks": {}}
    
    quota["current_model"] = model_id
    quota["last_switch"] = datetime.now().isoformat()
    quota["previous_model"] = old_model
    quota["previous_provider"] = get_current_provider(config)
    
    with open(QUOTA_FILE, "w") as f:
        json.dump(quota, f, indent=2)
    
    # Get model info from registry
    model_info = None
    for model in registry.get("models", []):
        if model["id"] == model_id:
            model_info = model
            break
    
    print(f"\n[switch] Model switched successfully!")
    print(f"  From : {old_model}")
    print(f"  To   : {model_id}")
    print(f"  Provider : {provider}")
    if model_info:
        print(f"  Tier  : {model_info.get('tier', '?')}")
        print(f"  Cost  : ${model_info.get('cost_per_1m_tokens', 0)}/1M tokens")
        print(f"  Strengths: {', '.join(model_info.get('strengths', []))}")
    print(f"\n  Config saved: {CONFIG_FILE}")
    print(f"  Restart Hermes for changes to take effect: hermes restart\n")

def cmd_free(registry: dict):
    """Switch to the best available free cloud model."""
    print("[switch] Selecting best free cloud model...")
    free_models = [
        m for m in registry.get("models", [])
        if m.get("tier") == "free" and m.get("type") == "cloud"
    ]
    
    if not free_models:
        print("[switch] No free cloud models found in registry!")
        sys.exit(1)
    
    # Check health and pick best
    if QUOTA_FILE.exists():
        with open(QUOTA_FILE) as f:
            quota = json.load(f)
    else:
        quota = {"health_checks": {}}
    
    health_checks = quota.get("health_checks", {})
    
    # Sort healthy free models by priority
    best = None
    for model in sorted(free_models, key=lambda m: m.get("priority", 99)):
        mid = model["id"]
        health = health_checks.get(mid, {"errors": 0})
        threshold = registry.get("policy", {}).get("error_threshold", 3)
        if health["errors"] < threshold:
            best = model
            break
    
    if not best:
        best = free_models[0]  # Fall back to first free model
        print(f"[switch] WARNING: All free models have errors, using {best['id']}")
    
    switch_model(best["id"], registry)

def cmd_local(registry: dict):
    """Switch to the best available local model."""
    print("[switch] Selecting best local model...")
    local_models = [
        m for m in registry.get("models", [])
        if m.get("tier") == "local" and m.get("type") == "local"
    ]
    
    if not local_models:
        print("[switch] No local models found in registry!")
        sys.exit(1)
    
    # Check if Ollama is running
    try:
        result = subprocess.run(
            ["ollama", "list"],
            capture_output=True, text=True, timeout=5
        )
        if result.returncode != 0:
            print("[switch] WARNING: Ollama is not responding!")
            sys.exit(1)
    except (FileNotFoundError, subprocess.TimeoutExpired):
        print("[switch] ERROR: Ollama is not available!")
        sys.exit(1)
    
    # Check health and pick best
    if QUOTA_FILE.exists():
        with open(QUOTA_FILE) as f:
            quota = json.load(f)
    else:
        quota = {"health_checks": {}}
    
    health_checks = quota.get("health_checks", {})
    
    best = None
    for model in sorted(local_models, key=lambda m: m.get("priority", 99)):
        mid = model["id"]
        health = health_checks.get(mid, {"errors": 0})
        threshold = registry.get("policy", {}).get("error_threshold", 3)
        if health["errors"] < threshold:
            best = model
            break
    
    if not best:
        best = local_models[0]
        print(f"[switch] WARNING: All local models have errors, using {best['id']}")
    
    switch_model(best["id"], registry)

def cmd_status(registry: dict):
    """Show current model and available options."""
    config = load_yaml(CONFIG_FILE)
    
    current = get_current_model(config)
    provider = get_current_provider(config)
    
    print(f"\n{'='*60}")
    print("  Hermes Model Status")
    print(f"{'='*60}")
    print(f"  Current model  : {current}")
    print(f"  Current provider: {provider}")
    
    if QUOTA_FILE.exists():
        with open(QUOTA_FILE) as f:
            quota = json.load(f)
        print(f"  Tokens today   : {quota.get('total_tokens_today', 0):,}")
        print(f"  Requests today : {quota.get('total_requests_today', 0):,}")
        print(f"  Daily cost     : ${quota.get('daily_cost', 0):.6f}")
    
    print(f"{'='*60}\n")
    
    # Group models by tier
    free_models = [m for m in registry.get("models", []) if m.get("tier") == "free"]
    local_models = [m for m in registry.get("models", []) if m.get("tier") == "local"]
    
    print("  Free Cloud Models (zero cost):")
    print(f"  {'ID':<50} {'Priority':>8} {'Context':>8}")
    print(f"  {'-'*50} {'-'*8} {'-'*8}")
    for m in sorted(free_models, key=lambda x: x.get("priority", 99)):
        print(f"  {m['id']:<50} {m.get('priority', 99):>8} {m.get('context_length', 0):>7,}")
    
    print(f"\n  Local Models (Ollama):")
    print(f"  {'ID':<50} {'Priority':>8} {'Context':>8}")
    print(f"  {'-'*50} {'-'*8} {'-'*8}")
    for m in sorted(local_models, key=lambda x: x.get("priority", 99)):
        print(f"  {m['id']:<50} {m.get('priority', 99):>8} {m.get('context_length', 0):>7,}")
    
    print()

def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    
    try:
        registry = load_yaml(REGISTRY_FILE)
    except Exception as e:
        print(f"[switch] ERROR: Could not load registry: {e}")
        sys.exit(1)
    
    cmd = sys.argv[1]
    
    if cmd == "status":
        cmd_status(registry)
    elif cmd == "free":
        cmd_free(registry)
    elif cmd == "local":
        cmd_local(registry)
    else:
        # Treat as a model ID
        switch_model(cmd, registry)

if __name__ == "__main__":
    main()
