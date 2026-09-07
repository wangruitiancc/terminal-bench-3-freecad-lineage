# Assignment compliance audit

Sources checked live on 2026-09-07:

- Email subject `大模型数据工程师 - 笔试`, sent by Xiangkai Zeng on 2026-09-04, asks for completion within seven days and links the Google Doc.
- Google Doc ID `1DAAGNM4BZnSLX-FuGmsB4qarO__nm1i4FcKwu9dsKrM` defines the requirements below.
- Current Terminal-Bench 3 CI and contribution documents are treated as the operational source of truth.

| Requirement | Status | Evidence |
|---|---|---|
| One original TB3 task | Complete | `tasks/repair-freecad-lineage` |
| Follow contribution, CI, and review rules | Complete with transport disclosure | current 22/22 static checks pass; CI-pinned Harbor 0.18.0 + Claude Code Sonnet review passes 35/35 |
| Docker environment builds | Complete | `evidence/formal-gates/image-baseline.json` |
| Oracle passes | Complete | 10/10 reward 1, zero exceptions |
| NOP fails | Complete | 3/3 reward 0, zero exceptions |
| Codex standard: `gpt-5.6-sol`, `xhigh`, 3 genuine failures | Complete | 3/3 reward 0, zero exceptions; `codex-calibration.json` |
| Claude Code standard: Opus 5, max, 3 genuine failures | Complete | 3/3 valid reward 0, zero exceptions; infrastructure failures excluded |
| Codex `/cheat` once, reward 0 | Score complete with limitation | reward 0; platform returned `AgentSafetyRefusalError` during concrete bypass testing |
| Claude `/cheat` once, reward 0 | Complete | exact CI-derived prompt; reward 0, zero exceptions |
| Analyze completed standard and adversarial runs | Complete with version/transport disclosure | all 8 formal trials have current six-criterion reports under `evidence/analyze-current`; 0 analysis errors |
| Repository contains task, commands/config/results, failure analysis | Complete | this repository tree |
| Send GitHub repository within 7 days | Ready but not sent | Gmail shows receipt at 2026-09-05 01:04 Asia/Shanghai; private GitHub remote exists, but reviewer access and the submission email remain external actions |
| Be ready to discuss design, verifier, iteration, failures | Complete | root README and `docs/project-overview-zh.md` |
| No TB3 pull request required | Acknowledged | GitHub repository submission only |
| Author retains IP; open source optional | Acknowledged | Apache-2.0 selected |

Invalid infrastructure and policy-stop trials are disclosed rather than counted as genuine model failures.

Current-source recheck on 2026-09-07 used Terminal-Bench main commit `83c7a6172d629c6575b785ab12c8db787bb2e323`. Its 22 static checks pass the current task. The four required task README sections were rewritten by the contributor and meet the structural length guidance. This reviewer-facing README rewrite changed the Harbor directory checksum from the evaluated snapshot to `140191cdc208c8ce99d1a168b306c71d74dd5cd2052a796c29d6f977054ae760`; the instruction, task configuration, environment, solution, and tests remain byte-identical to the model-trial snapshot. The current submission also passed all 35 implementation-review criteria using CI-pinned Harbor 0.18.0, Claude Code, and observed model `claude-sonnet-5`. All six standard and both adversarial trials have current six-criterion analyses with zero analysis errors. Those analyses used the current prompt/rubric with local Harbor 0.22.0 rather than CI-pinned 0.14.0. Model-backed checks used a compatible relay, so they are not official Anthropic endpoint evidence.
