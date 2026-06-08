# Skill: Forge (Code Refactoring Agent)

## Description

Delegate heavy code refactoring, optimization, and architectural restructuring tasks to the "Forge" sub-agent. This agent specializes in maintaining code integrity while improving performance and readability.

## Context

- **Target Host:** `jarvis3` (10.0.0.204)
- **User:** `jarvis`
- **Primary Model:** `deepseek-r1:8b` (Logic/Planning)
- **Secondary Model:** `qwen2.5-coder:7b` (Syntax/Generation)

## Usage

When you ask to "refactor", "optimize", or "restructure" a codebase, I will invoke Forge.

## Command Pattern (Example)

```bash
# This is an internal command I will construct and run.
ssh jarvis@10.0.0.204 "python3 ~/forge/refactor.py --target '/path/to/code' --goal 'Extract interfaces and reduce complexity' --model 'deepseek-r1:8b'"
```
