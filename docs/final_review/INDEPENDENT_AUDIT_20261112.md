# Independent final-week audit - 12 November 2026

**Evidence class: EXPLORATORY. Production: NO-GO.**

## Raw-result accounting (S9 and S13)

The registered 16-scenario grid completed 200 worlds per scenario on CPU Kaggle
kernels, separately for tau=0 and tau=1. The archive contains **3,200 complete
four-cell blocks and 12,800 reference interval records; zero failed or missing
cells**. Completion-file and archive SHA-256 fingerprints, producer source,
registered plan, configuration, seed, truth and cell identities were checked.
Each block stores a shared world fingerprint and all four outcomes. The driver
builds one world, then reuses it across fold/variance cells. Two variance estimates
share each fold scheme's cross-fitted residuals.

The production runner's aggregation previously paired the robust cells even if a
naive cell in that block failed. The review corrects it to require all four cells
for paired contrasts; per-cell valid summaries retain their own successful rows.
The failure-injection regression test checks this distinction. Additional tests
reject altered interval files, recomputed-hash wrong seeds, wrong producer source
and missing attempts. The final independent auditor omits the generic verifier's
two-cell paired comparisons and reports only the complete-four-cell contrasts.

The registered reference is existing overlap-sandwich CR0 plus normal critical
values. The t(G-1) and CR1-regime+t(G-1) outputs are secondary heuristics on the
same residuals, never post hoc primary-method replacements. Production density
sweeps, larger n, 10-fold and second-learner robustness conditions were not run by
this campaign. The precision of R=200 is limited; no equivalence or omnibus
superiority finding is claimed.

## Independent known-truth control (S12)

Fresh reconstruction, tau=1, 200 planned/attempted/valid worlds in every cell:

| Cell | Covered/valid | Coverage | MCSE | Wilson 95% | Failed / missing |
|---|---:|---:|---:|---:|---:|
| Random + naive | 186/200 | .930 | .0180 | [.8859,.9578] | 0 / 0 |
| Random + robust | 174/200 | .870 | .0238 | [.8163,.9097] | 0 / 0 |
| Grouped + naive | 180/200 | .900 | .0212 | [.8506,.9343] | 0 / 0 |
| Grouped + robust | 175/200 | .875 | .0234 | [.8220,.9139] | 0 / 0 |

Fresh null-condition size is .075/.120/.105/.140 in the same cell order. Nonnull
rejection is power, not empirical size. Artificial regime grouping/variance
clusters remain in the independent control; few-cluster and finite-sample
nuisance issues are not excluded as causes. This is not proof that dense common
shocks cause the deficit.

The old ~.87 transcript summary claims 200 valid attempts but lacks its original
replication archive. The fresh run reproduces **120/120 numeric fields at the
printed precision across the five recovered tau=1 control tables**: valid,
failed, coverage, MCSE, SE/SD ratio and estimate SD. This verifies numerical
reconstructability under the recorded source/environment, **not authenticity of
the missing original archive**. No inferred numerator is relabelled as an audited
original covered count.

## Central comparisons and interpretation

At gamma=1 and tau=1, K=4 random/grouped robust coverage is .815/.795;
grouped-minus-random difference -.020, paired MCSE .01579. At K=16 it is
.900/.905; difference +.005, MCSE .01662. Corresponding null-size differences are
-.005 (MCSE .01503) and -.005 (MCSE .01807). All use 200 complete blocks. These
signed differences are not changes in absolute calibration loss. Closeness to
.95 coverage and .05 size matters; larger coverage alone is not an improvement.

Earlier independent structural corroboration reproduced K4: 0/80,000 and K16:
280/80,000 multi-membership events, and calendar-window pair overlap .03481485.
Sparse multi-membership is distinct from regime-sharing pair density. No matched
H4 comparison or approved manipulation threshold is supplied. Source-isolation
and a whole-process randomization diagnostic with a deliberately dependent
positive control support implementation checks, not a mathematical independence
proof or all foundational gate requirements.

## Real-data feasibility and historical results

The exact eight-candidate roster is preserved. Latest saved Yahoo inputs provide
313 prices each for CRM, FAST, MHK, SWKS, ETSY and TER; ADS and CTLT have zero.
The old seven-row CAR output includes ADS and used absent original combined
prices and ^GSPC inputs. Fresh SPY responses cannot certify that different output.
The three counts are not silently reconciled into one analytical sample.

A registered feasibility calculation extends the existing pre-event VIX rule to
each daily return date: strictly prior observations, 20-observation averages,
trailing five calendar years, earlier rolling-average p25/p75, strict below/above
and equality mixed. An independent NumPy convolution/quantile calculation agrees
for all 1,249 label dates (zero mismatches; maximum absolute calculation difference
1.42e-14). This verifies arithmetic, not provider provenance or team label approval.

The six firms provide 1,872 adjacent-session adjusted-close returns, with no
imputation or market residualization. Of 28 candidate pairs, three have any
aligned observations. **No pair has 20 aligned calm observations**; one mixed and
two turbulent pair/label combinations meet that descriptive threshold. All
missing/insufficient pairs remain in the diagnostic CSV. The supported correlations
are descriptive (CRM/FAST turbulent, ETSY/TER mixed and turbulent); no IID p-value,
coverage or general market/regime conclusion is asserted. The planned broad
calm/turbulent comparison remains unsupported by these staggered short histories.
Provider prices and source VIX levels are excluded from the submission package;
source hashes, labels, aggregates and extraction scripts are provided.

Synthetic Control is **NOT EXECUTED**, closed by the final-week v3 plan because
donor data and eligibility were not validated. No more provider search/purchase
was made. Known-weight toy tests remain MOCK, never benchmark evidence.

## Completion boundary

Deeptanshu's independent audit and Mirun's evidence-labelled Methods/Results,
decision memo, one-pager and integration text can be submitted under Plan B after
human review. No full-team approval, validated production experiment, original
missing-input authentication or all-member video recording is invented. The
notebook/figures package receives a separate fresh-kernel execution record.
Course template mapping, intentional blank metadata, team recordings, Drive
viewer permissions and the Google Form remain release controls.
