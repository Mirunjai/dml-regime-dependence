# Session 5 reconstruction status and provenance

## Source material recovered
- Session 5 Claude execution transcript: 791 lines, recovered from the user's Library.
- Session 4 checkpoint `files (9).zip`: exact additions-only patch, handoff, Deeptanshu audit package, undercoverage diagnosis and Session 2–4 raw-output archive.
- Session 3 and earlier checkpoint archives were retained in the previous reconstruction bundle and are not duplicated in the repository patch.
- GitHub default branch was independently checked: `main` remains at `b5581562d818534a802f060920465df5fddf8a67`.

## What was reconstructed
- The Session 5 diagnostic script was extracted verbatim from the transcript's complete heredoc and syntax-compiled.
- Session 5 config/report renames and path-reference updates were reproduced.
- Gate 3 YAML proposals, recursive approval guard and its regression test were reconstructed from the transcript's recorded commands.
- The Session 5 hypothesis ledger, Gate 2 evidence extension, Methods-only draft and empty Results template were recreated from transcript heredocs.
- The GARCH, overlap and five-condition control summaries were restored as far as the console output supports. Their JSON files include provenance notes when the original full JSON was not recovered.

## Verification actually performed in this reconstruction
- `python -m py_compile` passed for `scripts/mirun_session5_checks.py`, `src/infra/dml_engine.py`, `src/real_data/panel_contract.py`, `tests/test_dml_engine.py` and `tests/test_real_data_contract.py`.
- `configs/mirun_gate3.yaml` parsed successfully with PyYAML.
- Session 5 transcript records 19 targeted tests before the final guard change and 11 DML-engine tests after it.
- The project-wide suite was not rerun after Session 5. The 354-pass claim belongs to Session 4 only.

## Missing / not reconstructed byte-for-byte
1. The old Claude runtime's `results/raw/mirun_session5/controls/` directory (five conditions x 200 per-replication files plus `calibration.json`) is not in the Session 4 raw tarball. `results/raw/mirun_session5/RECOVERY_NOTE.md` documents this. No per-replication JSON is fabricated.
2. The original full `results/tables/mirun_garch_canonical_vs_calendar.json` and `results/tables/mirun_session5_controls.json` were not attached. The restored summaries preserve the printed values and label their provenance; the script can regenerate fresh outputs.
3. The old Claude session ended due to quota immediately after writing the Results template. The transcript therefore does not show a final Session 5 patch, raw-output packaging, full-suite run, production run, or GitHub delivery.

## Scientific / governance status
- Session 5 controls used `tau=1`; a separate `tau=0` empirical-size study remains outstanding.
- Existing multiway/CR0-normal variance undercovers in the independent control. The evidence flags a few-cluster calibration issue, not proof that dependence-robust inference generally fails.
- The calendar-factor ablation does not support the factor as the cause in this DGP; the intended dense common-shock mechanism remains a design question.
- Gate 2 and Gate 3 remain unapproved. All new YAML proposal fields remain `AWAITING_TEAM_APPROVAL`.
- No commit, push, branch update or pull request was created.
