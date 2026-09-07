# Assignment compliance audit

Sources checked live on 2026-09-07:

- Email subject `大模型数据工程师 - 笔试`, sent by Xiangkai Zeng on 2026-09-04, asks for completion within seven days and links the Google Doc.
- Google Doc ID `1DAAGNM4BZnSLX-FuGmsB4qarO__nm1i4FcKwu9dsKrM` defines the requirements below.
- Current Terminal-Bench 3 CI and contribution documents are treated as the operational source of truth.

| Requirement | Status | Evidence |
|---|---|---|
| One original TB3 task | Complete | `tasks/repair-freecad-lineage` |
| Follow contribution, CI, and review rules | Complete | 22/22 static checks; 34 pass + 1 N/A implementation rubric |
| Docker environment builds | Complete | `evidence/formal-gates/image-baseline.json` |
| Oracle passes | Complete | 10/10 reward 1, zero exceptions |
| NOP fails | Complete | 3/3 reward 0, zero exceptions |
| Codex standard: `gpt-5.6-sol`, `xhigh`, 3 genuine failures | Complete | 3/3 reward 0, zero exceptions; `codex-calibration.json` |
| Claude Code standard: Opus 5, max, 3 genuine failures | Complete | 3/3 valid reward 0, zero exceptions; infrastructure failures excluded |
| Codex `/cheat` once, reward 0 | Score complete with limitation | reward 0; platform returned `AgentSafetyRefusalError` during concrete bypass testing |
| Claude `/cheat` once, reward 0 | Complete | exact CI-derived prompt; reward 0, zero exceptions |
| Analyze completed standard and adversarial runs | Complete | `evidence/evaluations/analysis-summary.json`; infrastructure-only analysis failures excluded |
| Repository contains task, commands/config/results, failure analysis | Complete | this repository tree |
| Send GitHub repository within 7 days | Ready | deadline window opened 2026-09-04; private GitHub remote is the delivery artifact |
| Be ready to discuss design, verifier, iteration, failures | Complete | root README and `docs/project-overview-zh.md` |
| No TB3 pull request required | Acknowledged | GitHub repository submission only |
| Author retains IP; open source optional | Acknowledged | Apache-2.0 selected |

Invalid infrastructure and policy-stop trials are disclosed rather than counted as genuine model failures.
