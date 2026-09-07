# Terminal-Bench 3 task: repair-freecad-lineage

This repository contains one original Terminal-Bench 3 task about persistent surface lineage in FreeCAD 0.21.2. A candidate must repair a single Python program so that native face references survive a repair, a partial Boolean edit, and a subsequent empty update.

The frozen task checksum is `3502b4fc96379eb53c9da89dc06aa139b0e4377db37455cb659ba012d22ae8e8`. The deterministic 34-file task archive has SHA-256 `8be679e6772af4aecc3c977d238cb293e68a3bf534e225dcf3db30c1ff2ad17f`.

## Why this task is difficult

The final B-rep does not contain enough information to recover temporal provenance. Temporary faces may disappear and later be recreated on identical support without regaining the old lineage. A repeat cut starts as a no-op and becomes partially effective after an edit. Geometry uses a graph-level rigid frame, while every operation names tool surfaces in its own independently permuted `SurfaceFrame`. The candidate must also preserve every native object, property schema, internal ID, placement, link, business value, and immutable B-rep while updating one existing atlas object and its native `App::PropertyLinkSubList` consumers.

The six private scenes execute repair, partial update, and empty update sequentially. The verifier runs the candidate under UID 2001, keeps private inputs and the checker root-only, reopens each output in a separate process, and emits binary reward plus CTRF.

## Repository contents

- `tasks/repair-freecad-lineage/`: complete TB3 task, candidate environment, public contract/checker, reference solution, separate verifier, and six private scenes.
- `evidence/formal-gates/`: frozen machine-readable static, Docker, isolation, Oracle, NOP, mutation, package, and Codex calibration evidence.
- `evidence/evaluations/`: standard and adversarial model-run summaries with invalid infrastructure trials identified separately.
- `docs/project-overview-zh.md`: Chinese end-to-end design and failure analysis.
- `REPRODUCE.md`: exact commands and expected results.
- `REQUIREMENTS.md`: line-by-line audit against the assignment email and Google Doc.

## Verified results

| Gate | Result |
|---|---:|
| Repository static checks | 22/22 pass |
| Implementation rubric | 34 pass, 1 N/A, 0 fail |
| Public repair/update/no-op chain | 3/3 accepted |
| Oracle | 10/10 reward 1, no exceptions |
| NOP | 3/3 reward 0, no exceptions |
| Targeted no-op mutant | reward 0; only the no-op partition invariant failed |
| Prior v4 model success on frozen v5 | reward 0 |
| Candidate tree/rootfs/docker-save scans | 0 findings |
| Codex standard, `gpt-5.6-sol`, `xhigh` | 3/3 valid reward 0, no exceptions |
| Claude standard, `claude-opus-5`, `max`, relay | 3/3 valid reward 0, no exceptions; infrastructure failures excluded |
| Codex adversarial `/cheat` | reward 0; `AgentSafetyRefusalError` disclosed |
| Claude adversarial `/cheat` | reward 0, no exceptions |

The Claude runs use a third-party Anthropic-compatible relay because the author's Anthropic organization is disabled. They verify the observed model string and Claude Code behavior through that route; they are not presented as proof of an official Anthropic endpoint run.

## Standard-run failure analysis

All three valid Codex submissions passed the geometry, temporal lineage, operation-specific `SurfaceFrame`, and consumer checks. They failed only on transformed private scenes because assigning `LineageFaces.Shape` reset the existing non-identity `LineageFaces.Placement`. The verifier reported `unknown_state_preserved`; downstream update/no-op checks then failed through sequential prerequisites.

Two valid Claude submissions independently reached a public-chain pass. Hidden repair passed on the two identity scenes, hidden update failed because the atlas ceased to be a disjoint boundary partition, and the four transformed scenes failed `unknown_state_preserved`. The third valid submission failed all six repair scenes because its atlas was not a disjoint boundary partition and its consumers did not match the pristine oracle. All three are genuine task failures with no agent or verifier exception.

Automated `harbor analyze` produced mixed task-specification judgments for the same documented preservation invariant: some trials passed, while others claimed `unknown_state_preserved` was not stated. The public contract explicitly requires preserving unknown native properties and limits extra-subdivision freedom to `LineageFaces.Shape`; the task remained frozen after evaluation so that results stayed comparable.

## License

Apache-2.0. The assignment states that the author retains the intellectual property and may publish the work.
