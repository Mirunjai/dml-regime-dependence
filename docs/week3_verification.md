# Week 3 independent verification and diagnostics

This is Deeptanshu's Week 3 package. It does not run Mirun's DML, choose the
Gate 3 grid, curate Preksha's dataset, or approve a team gate. The supplied Week 3
plan assumes Gate 2/3 are complete; those decisions and the scientific inputs
were not present in the audited repository on 3 November 2026.

## Run the complete software example

From the repository root, using the existing development environment:

```bash
python examples/week3_mock_review.py --output results/raw/week3_software_example
```

Use a new output directory for each execution. The example constructs **mock**
intervals for three scenarios, creates separate reference summaries with the
existing production metric functions, and checks them with the new independent
verifier. It also exercises the calm/turbulent diagnostic on a synthetic panel.
The audit/diagnostic subprocesses run with `python -S`: neither requires NumPy,
the DML code, the experiment runner, nor the production metric implementation.
The example generator's reference calculations use the existing NumPy metrics.

These test scenarios, thresholds, counts and artificial outcomes are not a
locked experimental design or an executed scientific robustness subset.

## Expected-attempt plan

Supply an independently checked plan transcribed from the team's locked memo.
The verifier cannot infer runs omitted by both a producer and its own manifest.
Each scenario has one known effect, an explicit replication-ID list and all four
fixed cells. A replication is an independently generated entire panel; firms
and event windows inside a panel must never be counted as independent runs.

Minimal **mock schema example**:

```json
{
  "schema_version": 1,
  "evidence_kind": "mock",
  "failure_policy": "raise",
  "confidence_level": 0.95,
  "scenarios": [
    {"id": "toy_null", "truth": 0.0,
     "replication_ids": [0, 1, 2], "role": "primary"}
  ]
}
```

For actual saved simulation results use `evidence_kind: simulation`, preserve
memo/version provenance in additional plan metadata, and supply the approved
scenario IDs/truths/replication lists. Roles are `primary`, `robustness` or
`extra_seed`. The plan must include every agreed robustness scenario; a role label
alone is not evidence that it was approved or executed. No parameter defaults or
scientific budgets are chosen by the verifier.

## Raw interval CSV

Required columns:

| Column | Meaning |
| --- | --- |
| `scenario` | Grid/effect condition ID matching the external plan |
| `replication` | Planned independent-panel replication ID |
| `cell` | One of the four canonical IDs below |
| `panel_id` | Same panel ID for all four cells of a replication; different across replications within a scenario |
| `truth` | Known simulation effect, evaluation metadata only |
| `confidence_level` | Explicitly `0.95`, matching the locked coverage question |
| `estimate`, `lower`, `upper` | Finite successful point estimate and closed interval bounds |
| `status` | `ok` or `failed` |

Failed records also need a nonempty `error` reason. Their estimates/bounds are
ignored for arithmetic, while their counts remain in the report. `seconds` is an
optional nonnegative runtime for the saved cell record. It is not automatically
an end-to-end runtime or a replication budget. Extra metadata columns are retained.

Canonical cells:

- `random_xfit__naive_var`
- `random_xfit__robust_var`
- `grouped_xfit__naive_var`
- `grouped_xfit__robust_var`

Missing planned records are counted separately from recorded failures. Duplicates,
unplanned IDs, different truths, reused panel IDs, inconsistent four-cell panel
IDs, malformed intervals and wrong confidence levels are rejected. Distinct IDs
alone cannot prove independent RNG streams; that still needs the producer's
source/seeding audit. Shared innovations across different grid scenarios are not
silently assumed to justify a paired *cross-scenario* analysis.

## Verify saved results and reported figures

```bash
python -m src.evaluation.week3_audit \
  --plan path/to/locked_attempts.json \
  --raw path/to/saved_intervals.csv \
  --claims path/to/claimed_summaries.csv \
  --paired-claims path/to/claimed_central_comparisons.csv \
  --manipulation path/to/manipulation_checks.csv \
  --output results/raw/week3_pilot_audit_01
```

The calculation module imports only the standard library and is independent of
`src/evaluation/metrics.py`. The JSON includes all four cells at every planned
scenario, valid/failed/missing counts, coverage, null size or nonnull power, MCSEs,
Wilson intervals, CI widths, bias and RMSE. All six within-scenario cell pairs
have signed coverage and size/power differences with paired MCSEs. The central
random+robust minus grouped+robust pair is explicitly marked.

Claimed summary CSV needs `scenario,cell,planned,attempted,valid,failed,missing`,
`coverage95,coverage_mcse,mean_ci_width,width_mcse`, and either
`empirical_size,size_mcse` under the null or `power,power_mcse` otherwise.
If bias/RMSE fields are also supplied, they are checked too. JSON `summaries` and
the existing single-run mock reporter's JSON `cells` format are supported.
A missing claimed row/required field is a discrepancy, not an agreement.

Paired-claim CSV columns are `scenario,a,b,outcome,direction,difference,mcse`,
`valid_pairs,planned_pairs,excluded_pairs`. The two central comparisons per
scenario must be present; extra supplied within-scenario comparisons are checked.
`direction` must be `a_minus_b`. `outcome` is `coverage`, `empirical_size` or `power`
as applicable. Do not compare successful subsets without explicitly aligned IDs.

Use full-precision saved summaries. Default comparison tolerances (`atol=1e-12`,
`rtol=1e-10`) concern floating-point agreement, not scientific materiality. A
coarser `--atol` must be explicitly chosen for rounded producer output and is
recorded in the audit. Counts always compare exactly. Gate 3 benefit/materiality
criteria remain untouched; this tool does not turn a signed difference or a
nonsignificant result into a benefit/equivalence claim.

Closed endpoints count as covered. Size is defined only for truth zero; nonzero
truth gives power. With failed/missing attempts, rates are explicitly conditional
on available successes and the report gives coverage bounds over *all planned*
attempts. All-failed/all-missing metrics are undefined, never zero. A single valid
pair cannot estimate a paired MCSE. Boundary binomial MCSEs can be zero; the
Wilson interval retains finite-sample uncertainty. RMSE MCSE uses the delta method
on squared errors and is approximate; it is undefined at zero RMSE. Relevant
moment assumptions need review for the actual estimator before interpreting that
approximation. Bias and coverage are reported separately.

The saved report contains input hashes, UTC time, Python version, Git head/dirty
status and verifier source hashes. Exact uncommitted sources are retained in
`verifier_sources.zip`. Inputs changing during a read are rejected; use frozen
or atomically published raw chunks for a final audit.

Exit code 2 records invalid inputs, discrepancies, unreported strict-mode failures,
missing planned records or numerical/manipulation review flags. Exit 0 means the
requested arithmetic/snapshot completed; it is **not a pilot launch or gate
approval**. For simulation plans, missing summary/central-comparison claims or
unevaluated manipulation definitions also return 2. Input failures produce
`input_error.json` and no verified metric table. Numerical counts/examples already
computed from a well-formed CSV are retained even when a bad value blocks metrics. Existing output directories are
protected from replacement.

## Manipulation checks and numerical monitoring

Manipulation CSV: `scenario,cell,diagnostic,value`. Definitions come exclusively
from `plan.manipulation_checks`, for example `{name, operator, threshold,
scenarios}` with operator `>=`, `>`, `<=` or `<`. Each planned diagnostic is
required separately for all four cells of each target scenario. Missing values,
failed criteria and absent definitions remain visible. Statistical independence
of treatment/volatility and successful induction of cross-sectional dependence
are different checks; a fabricated scalar or placeholder cannot establish either.
Definitions/thresholds must be transcribed from the actual lock memo.

An optional long-form `--trace path/to/numeric_trace.csv` screens values with
columns `scenario,replication,cell,component,quantity,value` and optional unique
`coordinate`. NaN/inf/malformed values, nonpositive `variance`,
`conditional_variance`, `conditional_std` or `sigma`, and explicitly supplied
absolute limits in `plan.trace_absolute_limits` are counted. Every flagged value
is counted; only the first 100 examples are embedded, with a truncation indicator.
There is no clipping or deletion. Traces must reference planned attempts; optional
coordinates cannot repeat. Trace presence is reported per planned cell attempt.
Only supplied values are screened: one saved trace value is not proof that every
state or nuisance-fitting value was examined.

Saved estimates/intervals/status/runtime are screened even without a trace.
`--estimate-limit` is an optional recorded review flag, not a scientific cutoff.
No return/pathology threshold is silently chosen for the real experiment.

For a producer running independently, monitor new snapshots:

```bash
python -m src.evaluation.monitor --interval 60 --iterations 0 \
  --output-root results/raw/week3_monitor_01 -- \
  --plan path/to/locked_attempts.json --raw path/to/growing_raw.csv \
  --allow-incomplete
```

`--iterations 0` explicitly requests continuous operation; Ctrl-C stops it.
Otherwise the default is one snapshot. A changing/truncated CSV is logged as an
input error and retried at the next snapshot. The monitor never writes the
producer's files or launches its next job. `--allow-incomplete` permits a partial
snapshot; it does not hide discrepancies, numerical flags, failed strict-mode
attempts, or make `all_planned_records_present` true. Snapshot cost grows with
input size; choose the monitoring interval accordingly. The offline reader uses
memory proportional to the saved records; per-scenario exports can bound its cost.

## Existing mock-runner adapter

`--runner-dir` replaces `--raw` for the currently merged mock-only runner. Supply
a single-scenario **mock** plan. The adapter independently checks config hashes,
truth, seed addresses, replication filenames, root seed and cell identities. It
rejects a producer-invalidated run. It does not import the runner's validators or
assume a future scientific runner has the same schema. No teammate module needs
to change to use the CSV interface.

## Positive-control recheck

```bash
python scripts/check_week3_positive_control.py --seed 20261103 \
  --output results/raw/week3_positive_control_recheck_01
```

This reruns the existing Week 2 **component** diagnostic on a fresh recorded seed
using the merged, pinned regime generator and unchanged GARCH component. Its
configuration is saved before execution. It retains 100 independent-panel
records, complete-process randomization evidence, stream invariance, deliberate
broken-independence controls, Wilson intervals and independent rate recomputation.
Settings remain the prior provisional engineering settings. It is neither the
integrated DGP's manipulation check nor a locked DML robustness run.

## Calm/turbulent real-data diagnostics

Input long-form panel: `date,firm_id,value,regime`. Dates use `YYYY-MM-DD`; regime
labels must be the externally defined `calm` or `turbulent`, consistent for one
market date. Duplicate date/firm rows, nonfinite values and conflicting labels
are rejected. A blank value is explicit missingness; absent firm/date rows are
counted using the observed date and firm unions. An event-list-only file is not
sufficient: actual daily return/abnormal-return/residual observations are needed.

```bash
python -m src.real_data.dependence \
  --panel path/to/frozen_labelled_panel.csv --evidence-kind real \
  --value-kind residual --min-overlap TEAM_CHOSEN_MINIMUM \
  --label-source 'Path/version of the approved external label rationale' \
  --output results/raw/week3_real_data_diagnostics_01
```

Choose `return`, `abnormal_return` or `residual` to describe the supplied values;
the tool does not fit factors/residuals or choose regime labels. Minimum overlap
must be explicitly supplied and at least three; this engineering minimum does
not make a short-window correlation reliable. Toy data must use
`--evidence-kind mock`.

The diagnostic computes each firm pair's Pearson correlation on shared dates
within each label and exports every pair, including undefined results and overlap
counts. Constant series and insufficient overlap produce N/A, not zero. It reports
mean/median/mean-absolute correlations by label and a comparison restricted to
firm pairs usable under both labels. Pairs are equally weighted; sample sizes,
firm composition and dates can still differ. Pair correlations share firms and
dates and are not independent: no iid pair-based MCSE, significance test, or causal
interpretation is supplied. Common market factors, volatility and selection can
explain a contrast. Real-data true effects are unknown, so no coverage or empirical
size is estimated. Results are qualitative.

## Methods references

- [Morris, White and Crowther (2019), Table 6](https://pmc.ncbi.nlm.nih.gov/articles/PMC6492164/):
  definitions and Monte Carlo errors for simulation performance measures. The
  independent verifier uses sample-mean uncertainty and paired indicator
  differences; it does not call the production implementation.
- [NIST, product-moment correlation](https://www.itl.nist.gov/div898/software/dataplot/refman2/auxillar/correlat.htm):
  descriptive Pearson correlation formula. The iid significance calculations
  shown there are deliberately not applied to overlapping financial observations.
- The team's Week 3 plan and `docs/DECISIONS.md` govern ownership, failure reporting
  and unresolved design choices. The earlier P5 materiality proposal is not an
  approved protocol simply because implementation utilities now exist.
# Actual calendar-runner and archived pilot review (4 November)

The reviewed `research.week2_completion.run_week2` producer now saves atomic
attempts. Its manifest is the plan; a missing scenario or replication remains
missing even when an aggregate summary omits it. Run the independent adapter:

```bash
python -S -m src.evaluation.mirun_audit \
  --run-dir results/raw/<producer-run> \
  --output results/raw/<new-audit-directory>

python -m src.evaluation.monitor --producer calendar --interval 60 \
  --iterations 0 --output-root results/raw/<new-monitor-directory> -- \
  --run-dir results/raw/<producer-run>
```

The adapter checks recorded configs, seed addresses, estimator settings, four-cell
identity, fold assignments and producer source hashes. Atomic attempt files are
authoritative; inline copies never replace missing files. It outputs canonical
CSV, an explicit plan, independent summaries/paired MCSEs, stability screens,
claim discrepancies and source/input hashes. Source checks establish content
consistency, not authenticity. Producer numeric/fold screens remain labelled as
producer claims until separately replayed. No diagnostic threshold is inferred.

Exit 0 requires complete successful raw cells, matching required headline claims,
consistent inline attempts and verifiable source bytes. Exit 2 preserves a report
with failures, missing work, discrepancies or unavailable source. A producer's
`source_changed.json` invalidates the run. Invalid inputs raise; monitoring saves
them as input errors and can continue without modifying the producer.

To reconstruct the already-published historical pilots from immutable Git source
(requires the original `26e65f1` object and research dependencies):

```bash
python scripts/replay_mirun_pilots.py --output results/raw/<new-replay>
python -S scripts/audit_mirun_replays.py \
  --calendar-dir results/raw/<new-replay>/calendar \
  --legacy-dir results/raw/<new-replay>/legacy \
  --output results/raw/<new-historical-audit>

python scripts/check_calendar_independence.py \
  --output results/raw/<new-calendar-diagnostic>
```

Reconstruction preserves the two estimator variants and their existing grids and
seed rules. It does not create an approved robustness campaign. The replay driver
uses two processes with explicit single-threaded BLAS and one learner thread;
runtime depends on the machine. Reused legacy worlds across tables do not count
as additional independent panels. The original raw archive/environment was not
provided, so small continuous differences remain unresolved and the historical
audit returns 2. The separate single-toy timing example is excluded from MC counts.

The delivered tables report 320 active-pilot and 5,040 legacy interval rows,
76 matching coverage rates, and 120 differences among 520 checked fields
(maximum absolute difference 6.2211e-6). Original missing power/width/paired MCSEs
are not retroactively presented as verified claims. Supplementary MCSEs come from
reviewer raw reconstructions. See the [Week 3 report](../reports/deeptanshu_week3.md)
for exact environments, sensitivity/control findings and pending team inputs.
