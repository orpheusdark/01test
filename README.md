# DriftGuard: Offline RL Environment for Schema Drift Migrations

DriftGuard is a hackathon-ready offline RL environment that simulates schema drift in a Python service repository.
The agent must migrate code through tool use only, while passing tests, schema validation, and policy checks.

## Problem Statement

Episode ticket: **"Upstream JSON response schema changed."**

The agent gets a repository snapshot and must repair it so that:
1. tests pass,
2. payloads validate against active JSON Schema,
3. policy scan passes.

A schema drift event occurs mid-episode (v1 → v2), causing previously passing code to fail unless migrated.

## Environment Loop (reset/step)

- `reset(seed=...)`:
  - creates a deterministic working copy of `driftguard/repo_snapshot/`
  - initializes scenario/ticket metadata
  - sets active schema to v1 and payload sample to v1
- `step(action)`:
  - applies drift at configured step
  - executes one tool action (`read_file`, `search`, `apply_patch`, `run_tests`, etc.)
  - returns observation, reward, done, info

Step limit is enforced (`step_limit`, default 15).

## Tools / Actions

- `read_file(path)`
- `search(pattern)`
- `apply_patch(path, old, new)`
- `run_tests()` (pytest in snapshot)
- `validate_schema()` (jsonschema)
- `policy_scan()`
- `ask_requester(question)`
- `ask_security(question)`
- `submit_for_review(summary)` (oversight shaping)

Agent cannot write files directly; only `apply_patch` can modify code.

## Schema Drift

Drift is applied by `driftguard.drift.apply_schema_drift()` at `drift_step`.

- active schema switch: `user_v1.schema.json` → `user_v2.schema.json`
- sample payload shape changes (e.g., `name` → `full_name`, `email` nested in `contact.email`)

## Reward Model and Metrics

Per-step reward:
- `-0.01` per tool call
- `+1` for passing `run_tests`
- `+1` for passing `validate_schema`
- `+1` for passing `policy_scan`
- repeated failed checks incur extra penalty (`-0.05`)
- oversight shaping on review:
  - `+0.2 * explanation_score`
  - `-0.1 * risk_flags`

Episode success requires all three checks passing.

Metrics (`driftguard.eval`):
- success rate
- average reward
- average steps
- pass rates for tests/schema/policy

## Run

Install:

```bash
pip install -r requirements.txt
```

Single rollout:

```bash
python scripts/run_rollout.py --agent smart --seed 7
```

Benchmark:

```bash
python scripts/benchmark.py --episodes 20 --seed 7
```

This writes `benchmark_metrics.json` in the current directory.

## Minimal Training (Colab / local)

Use the minimal training stub:

```bash
python training/train_trl.py --episodes 30 --seed 7
```

Colab quick steps:
1. Upload repo or clone your fork.
2. `pip install -r requirements.txt`
3. (Optional TRL path) `pip install trl transformers accelerate datasets`
4. Run `python training/train_trl.py --episodes 50`

If TRL is unavailable, the script runs an offline placeholder loop and still logs rewards/success.
