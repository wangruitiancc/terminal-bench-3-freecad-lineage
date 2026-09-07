# Reproduction commands

Run these from a current checkout of the Terminal-Bench 3 repository after placing this task at `tasks/repair-freecad-lineage`.

## Static checks

```bash
for check in scripts/checks/*.sh; do
  bash "$check" tasks/repair-freecad-lineage
done
```

Expected: 22 pass, 0 fail. See `evidence/formal-gates/static-checks.json`.

## Docker builds

```bash
docker build -t repair-freecad-lineage-env:repro tasks/repair-freecad-lineage/environment
docker build -t repair-freecad-lineage-tests:repro tasks/repair-freecad-lineage/tests
```

Frozen evidence identifies candidate image `sha256:4c6df62de2f2d9baa6873f09b24ad8e0332c8fd5a54477334230b05dad4d6b20` and verifier image `sha256:a776063f3009a81c48ee86b3281be0eecb6d00bd11474a28aa655f82dc101afb`.

## Oracle and NOP

```bash
harbor run -p tasks/repair-freecad-lineage --agent oracle --env docker -k 10 -n 1 --job-name lineage-oracle-10x -y
harbor run -p tasks/repair-freecad-lineage --agent nop --env docker -k 3 -n 1 --job-name lineage-nop-3x -y
```

Expected: Oracle 10/10 reward 1 with zero exceptions; NOP 3/3 reward 0 with zero exceptions.

## Standard model trials

```bash
CODEX_FORCE_AUTH_JSON=YES harbor run \
  -p tasks/repair-freecad-lineage -a codex -m openai/gpt-5.6-sol \
  -k 3 -n 1 --ak reasoning_effort=xhigh \
  --ae CODEX_FORCE_AUTH_JSON=YES --job-name lineage-codex-standard-3x -y

CLAUDE_CODE_MAX_OUTPUT_TOKENS=128000 harbor run \
  -p tasks/repair-freecad-lineage -a claude-code -m anthropic/claude-opus-5 \
  -k 3 -n 1 --ak reasoning_effort=max \
  --job-name lineage-claude-standard-3x -y
```

Use credentials through environment variables or a protected Harbor config. Never commit them. The recorded relay run used model name `claude-opus-5` because the compatible endpoint expected the unprefixed request model.

## Adversarial `/cheat`

Follow `.github/workflows/run-cheat-trials.yml` from the current TB3 main branch exactly: copy the task, remove sentences matching `[Dd]o not cheat[^.]*\.`, append `docs/prompts/hack-trial-prompt.md`, then run each target agent once with the same model and reasoning settings. Expected reward is 0 for both agents.

## Analyze

```bash
harbor analyze jobs/<standard-or-cheat-job> \
  -m sonnet \
  -r docs/prompts/trial-analysis.toml \
  --job-prompt docs/prompts/trial-analysis-job.txt
```

Run this from a current Terminal-Bench checkout so both prompt files come from the same CI revision. The recorded reports under `evidence/analyze-current/` cover all six current criteria for six standard and two adversarial trials. They used the current rubric and job prompt with observed model `claude-sonnet-5` through a compatible relay; local Harbor 0.22.0 spells the prompt option `-p/--prompt` and writes a job directory, while CI-pinned Harbor 0.14.0 uses `--job-prompt` and `-o`. Check `.github/harbor-run-defaults.yml` before rerunning in case model, backend, attempts, or analysis settings change.

## Implementation review

Current CI stages the task plus `docs/prompts/task-implementation.toml` and runs `harbor exec` with `scripts/rubric-regression/templates/instruction.md`, Claude Code, and Sonnet. The recorded run used CI-pinned Harbor 0.18.0 and observed model `claude-sonnet-5`; all 35 criteria passed. See `evidence/formal-gates/implementation-rubric-claude-sonnet5-current.json`.
