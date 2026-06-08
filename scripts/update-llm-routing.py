#!/usr/bin/env python3
"""Dynamic routing update + provider discovery.

- Pulls provider usage/limits via `openclaw status --usage --json`
- Stores limits + available models for providers with keys
- Writes dynamic routing preferences for local-first + Gemini primary
- Enables OpenAI GPT-5.2 *only* as fallback for non-coding tasks when Gemini is capped
"""
import json, os, subprocess, time
from pathlib import Path

DYNAMIC_PATH = Path('/home/aaron/.openclaw/workspace/config/llm-routing-dynamic.json')

# Google limits from user screenshots
GOOGLE_LIMITS = {
    'google/gemini-2.5-pro':   {'rpm': 150,  'tpm': 2_000_000, 'rpd': 1000},
    'google/gemini-2.5-flash': {'rpm': 1000, 'tpm': 1_000_000, 'rpd': 10000},
    'google/gemini-3-pro':     {'rpm': 25,   'tpm': 1_000_000, 'rpd': 250},
    'google/gemini-3-flash':   {'rpm': 1000, 'tpm': 1_000_000, 'rpd': 10000},
}

# OpenAI tiers (user-specified Tier 1; other tiers included)
OPENAI_TIERS = {
    1: {'rpm': 500,   'tpm': 500_000},
    2: {'rpm': 5_000, 'tpm': 1_000_000},
    3: {'rpm': 5_000, 'tpm': 2_000_000},
    4: {'rpm': 10_000,'tpm': 4_000_000},
    5: {'rpm': 15_000,'tpm': 40_000_000},
}
OPENAI_TIER = int(os.getenv('OPENAI_TIER', '1'))
OPENAI_LIMIT = OPENAI_TIERS.get(OPENAI_TIER, OPENAI_TIERS[1])

LIMITS = {
    **GOOGLE_LIMITS,
    'openai/shared': {'rpm': OPENAI_LIMIT['rpm'], 'tpm': OPENAI_LIMIT['tpm'], 'rpd': 1000},
}

THRESH = 0.90  # 90% near-cap


def _extract_usage(snapshot, provider_hint=None):
    usage = {}
    providers = snapshot.get('providers') or []
    for p in providers:
        if provider_hint and provider_hint not in str(p.get('provider','')):
            continue
        windows = p.get('windows') or []
        for w in windows:
            model = w.get('model') or w.get('modelId') or ''
            if model:
                usage[model] = w
    return usage


def _near_cap(model_id, usage):
    limits = LIMITS.get(model_id)
    if not limits:
        return False
    u = usage.get(model_id) or {}
    rpm = u.get('rpm') or u.get('requestsPerMinute') or u.get('requestRate', {}).get('rpm')
    tpm = u.get('tpm') or u.get('tokensPerMinute') or u.get('tokenRate', {}).get('tpm')
    rpd = u.get('rpd') or u.get('requestsPerDay') or u.get('requestRate', {}).get('rpd')
    def hit(val, limit):
        try:
            return float(val)/float(limit) >= THRESH
        except Exception:
            return False
    return hit(rpm, limits['rpm']) or hit(tpm, limits['tpm']) or hit(rpd, limits['rpd'])


def main():
    p = subprocess.run(['openclaw','status','--usage','--json'], text=True, capture_output=True)
    if p.returncode != 0:
        raise SystemExit(p.stderr.strip() or 'openclaw status failed')
    data = json.loads(p.stdout)
    usage_root = data.get('usage') or data.get('providerUsage') or {}

    google_usage = _extract_usage(usage_root, 'google')
    openai_usage = _extract_usage(usage_root, 'openai')

    pro_near = _near_cap('google/gemini-2.5-pro', google_usage)
    flash_near = _near_cap('google/gemini-2.5-flash', google_usage)
    g3pro_near = _near_cap('google/gemini-3-pro', google_usage)
    g3flash_near = _near_cap('google/gemini-3-flash', google_usage)

    # base preferences
    prefs = {
        'general_assistant': 'local.general',
        'quick_qa_or_control': 'local.quick',
        'coding_normal': 'google/gemini-2.5-pro',
        'deep_reasoning_planning_debug': 'google/gemini-2.5-pro',
    }

    if pro_near:
        prefs['coding_normal'] = 'google/gemini-2.5-flash'
        prefs['deep_reasoning_planning_debug'] = 'google/gemini-2.5-flash'
    if flash_near:
        prefs['coding_normal'] = 'local.coding'
        prefs['deep_reasoning_planning_debug'] = 'local.deep_reasoning'
        prefs['general_assistant'] = 'local.general'

    # If both Gemini 2.5 tiers are near cap, allow Gemini 3 tiers for non-coding
    if pro_near and flash_near:
        if not g3pro_near:
            prefs['general_assistant'] = 'google/gemini-3-pro'
        elif not g3flash_near:
            prefs['general_assistant'] = 'google/gemini-3-flash'
        else:
            # final fallback for non-coding only
            prefs['general_assistant'] = 'openai/gpt-5.2'

    dynamic = {
        'updatedAt': int(time.time()),
        'limits': LIMITS,
        'openaiTier': OPENAI_TIER,
        'nearCap': {
            'gemini_pro': pro_near,
            'gemini_flash': flash_near,
            'gemini3_pro': g3pro_near,
            'gemini3_flash': g3flash_near,
        },
        'taskPreferred': prefs,
        'availableModels': {
            'google': sorted(list(google_usage.keys())),
            'openai': sorted(list(openai_usage.keys())),
        },
    }
    DYNAMIC_PATH.write_text(json.dumps(dynamic, indent=2, sort_keys=True))
    print(str(DYNAMIC_PATH))


if __name__ == '__main__':
    main()
