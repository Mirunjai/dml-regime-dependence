"""Narrated, executable stages for the final exploratory research notebook."""

def make_cells(bundle_sha256):
    cells = []
    def md(text):
        cells.append({'cell_type':'markdown','id':f'm{len(cells):03d}','metadata':{},'source':text.strip().splitlines(keepends=True)})
    def step(title, why, source):
        md(f'## {sum(c["cell_type"]=="code" for c in cells)+1}. {title}\n\n{why}')
        cells.append({'cell_type':'code','id':f'c{len(cells):03d}','metadata':{},'source':source.strip().splitlines(keepends=True),'outputs':[],'execution_count':None})
    md('''# Auditing DML confidence intervals under regime-level dependence
**Advanced Data Analytics · Project A · EXPLORATORY / Plan B**

Deeptanshu Kumar (PES1UG24AM357), Mirunjai Suresh Kumar (PES1UG24AM161), Preksha K (PES1UG24AM907), Sudarshan G (PES1UG24AM450).

Team name: __________ · Sections: __________

Run all cells in order from a fresh Python kernel. Keep `02_Code` beside `03_Dataset`, or attach the private Kaggle bundle dataset. Python 3.11+, NumPy, SciPy, scikit-learn, pandas and Matplotlib are required; internet and a GPU are unnecessary. The notebook regenerates the audit, tables and figures from 3,200 archived worlds and demonstrates the actual DGP and estimator on one world. It does not rerun the full Monte Carlo campaign.

**Research question:** does robust variance suffice, or does regime-aware cross-fitting add inferential benefit? The four cells are random/grouped folds × naive/robust variance. Coverage is primary; null size is the key diagnostic.

**Evidence boundary:** all campaign results are exploratory. The primary production question remains unresolved because foundational calibration/manipulation checks are not satisfied. Real data supply descriptive evidence, never known-truth coverage. Synthetic Control is NOT EXECUTED. Missing historical inputs are not reconstructed as observations. MOCK arithmetic is labelled separately.''')
    step('Locate and verify the frozen input bundle',
         'A SHA-256 checksum ties this notebook to one exact source-and-results package. Verifying it before extraction prevents accidental mixing of experiments.',
         '''from pathlib import Path
import hashlib,io,json,os,sys,tempfile,zipfile
BUNDLE_SHA256 = '''+repr(bundle_sha256)+'''
candidates=[Path.cwd()/"notebook_bundle.zip",Path.cwd()/"03_Dataset/source/notebook_bundle.zip",Path.cwd().parent/"03_Dataset/source/notebook_bundle.zip",Path("/kaggle/input/ada-dml-final-exploratory-bundle/notebook_bundle.bin")]
bundle_path=next((p for p in candidates if p.is_file()),None)
if bundle_path is None:
    raise FileNotFoundError("Keep 02_Code beside 03_Dataset, or attach the private Kaggle bundle dataset.")
blob=bundle_path.read_bytes()
assert hashlib.sha256(blob).hexdigest()==BUNDLE_SHA256
print("Verified bundle:",BUNDLE_SHA256)''')
    step('Create an isolated reproduction directory',
         'Extract into a new temporary directory so the run cannot pick up host-repository outputs. Every archive path is checked before extraction.',
         '''RUN=Path(tempfile.mkdtemp(prefix="ada-final-reproduction-"))
with zipfile.ZipFile(io.BytesIO(blob)) as archive:
    assert all((RUN/name).resolve().is_relative_to(RUN) for name in archive.namelist())
    archive.extractall(RUN)
os.chdir(RUN)
os.environ["MPLCONFIGDIR"]=str(RUN/"mpl-cache")
sys.path.insert(0,str(RUN))
OUTPUT=RUN/"generated";OUTPUT.mkdir()
print("Fresh workspace:",RUN)''')
    step('Record the software environment',
         'Library versions can change fitted forests even with identical seeds. We record versions and distinguish exact world reproduction from estimator agreement across versions.',
         '''from importlib.metadata import version
import platform
import numpy as np
import pandas as pd
from IPython.display import display,Image
environment={"python":sys.version,"platform":platform.platform(),"packages":{name:version(name) for name in ("numpy","scipy","scikit-learn","matplotlib","pandas")},"bundle_sha256":BUNDLE_SHA256}
print(json.dumps(environment,indent=2))''')
    step('Load the registered exploratory design',
         'The dated plan predates execution and fixes the conditions being reported. A simulated world is the replication unit; firms, days and folds are not extra replications.',
         '''plan_path=RUN/"configs/experiments/final-review/exploratory_validation_20261112.json"
plan=json.loads(plan_path.read_text())
assert plan["evidence_class"]=="EXPLORATORY" and plan["replications"]==200 and len(plan["scenarios"])==16
print("Registered UTC:",plan["registered_utc"])
print("Planned worlds:",len(plan["scenarios"])*plan["replications"])''')
    step('Inspect the scenario grid and effect conditions',
         'Zero-effect scenarios measure empirical size; nonzero-effect scenarios measure coverage and power. Reused seeds pair conditions, so scenarios must not be pooled as independent samples.',
         '''grid=pd.DataFrame([{"scenario":s["id"],"seed0":s["seed0"],"folds":s["folds"],**s["config"]} for s in plan["scenarios"]])
display(grid[["scenario","tau","n","T","H","density","n_regimes","gamma","seed0"]])
assert set(grid.tau)=={0.,1.}''')
    step('Inspect named random-number streams',
         'Separate SeedSequence child streams isolate volatility, timing, treatment and shared shocks. Stream addresses establish construction; a small empirical correlation would not prove independence.',
         '''from research.week2_completion.dgp import Config,build_world,STREAMS,spawn_rngs
case=next(s for s in plan["scenarios"] if s["id"]=="independent_tau1")
seed=case["seed0"]
streams=spawn_rngs(seed)
display(pd.DataFrame([{"component":name,"entropy":seed,"spawn_key":str([i])} for i,name in enumerate(STREAMS)]))
assert tuple(streams)==STREAMS''')
    step('Generate one actual demonstration world',
         'This runs the source-pinned calendar DGP used in the archive. The independent control switches off common shocks, factors and regime-driven treatment effects while retaining artificial grouping labels.',
         '''world=build_world(Config(**{**case["config"],"seed":seed}))
memberships=world["cluster_memberships"]
print("Known effect:",world["cfg"].tau,"; treated share:",float(world["D"].mean()))
assert world["cfg"].sd_shock==world["cfg"].sd_factor==world["cfg"].gamma==0''')
    step('Check dimensions, units and finite values',
         'Each firm contributes one event outcome; volatility and standardized innovations have firm × time shape. Sigma is a conditional standard deviation, so the idiosyncratic return is sigma × innovation.',
         '''shape_table=[]
for name in ("X","D","Y","sig","z","t0","idx"):
    value=np.asarray(world[name]);assert np.isfinite(value).all()
    shape_table.append({"field":name,"shape":str(value.shape),"dtype":str(value.dtype)})
assert world["sig"].shape==world["z"].shape and np.all(world["sig"]>0)
display(pd.DataFrame(shape_table))
print("Mean squared idiosyncratic return:",float(np.mean((world["sig"]*world["z"])**2)))''')
    step('Distinguish the two GARCH parameterizations',
         'The historical generator fixes alpha=.10, whereas the standalone component sets alpha=.10×persistence. Equal unconditional variance and persistence do not make these models identical.',
         '''from src.dgp.volatility import garch_parameters
parameter_rows=[]
for rho in (.9,.99):
    for family,share in (("historical fixed alpha",.1/rho),("canonical arch share",.1)):
        p=garch_parameters(rho,arch_share=share)
        parameter_rows.append({"family":family,"rho":rho,"alpha":p.alpha,"beta":p.beta,"omega":p.omega,"variance_target":p.unconditional_variance,"finite_fourth_moment":p.has_finite_fourth_moment})
display(pd.DataFrame(parameter_rows))''')
    step('Measure realized exposure and dependence structure',
         'Configured calendar density, exposed-event share and shared-regime pair density measure different things. These structural diagnostics must be checked before interpreting a dense-dependence claim.',
         '''from scripts.mirun_gate2_validation import event_metrics
structure=event_metrics(world)
print(json.dumps(structure,indent=2))
assert 0<=structure["shared_pair_density"]<=1''')
    step('Construct random and grouped folds',
         'Grouped splitting keeps connected regime-membership components together. It does not automatically remove shared calendar-factor dependence, which is audited separately.',
         '''from research.week2_completion.dml import make_folds,crossfit,estimate,audit_folds
folds={scheme:make_folds(scheme,memberships,case["folds"],np.random.default_rng(seed+(scheme=="grouped"))) for scheme in ("random","grouped")}
fold_audits={scheme:audit_folds(world,fold) for scheme,fold in folds.items()}
display(pd.DataFrame(fold_audits).T)
assert fold_audits["grouped"]["regime_cross_fold_pairs"]==0
print("Fold sizes:",{scheme:np.bincount(fold).tolist() for scheme,fold in folds.items()})''')
    step('Cross-fit nuisance predictions with random folds',
         'Each observation is predicted by forests fitted outside its held-out fold. Residualizing both outcome and treatment removes the fitted nuisance components before estimating the effect.',
         '''residuals={}
residuals["random"]=crossfit(world["Y"],world["D"],world["X"],folds["random"],case["folds"],seed)
print("Random residual shapes:",[x.shape for x in residuals["random"]])''')
    step('Cross-fit the same world with grouped folds',
         'The data and learner settings are held fixed while fold construction changes. Comparing these residuals separates fold design from the later variance choice.',
         '''residuals["grouped"]=crossfit(world["Y"],world["D"],world["X"],folds["grouped"],case["folds"],seed)
assert all(np.isfinite(a).all() for pair in residuals.values() for a in pair)
print("Grouped residual shapes:",[x.shape for x in residuals["grouped"]])''')
    step('Inspect the orthogonal-score calculation',
         'For the partial-linear score, the effect is sum(D-residual × Y-residual)/sum(D-residual²). The known simulation truth is used for evaluation, not for fitting nuisance functions.',
         '''score_checks=[]
for scheme,(yt,dt) in residuals.items():
    J=float(np.sum(dt**2));assert J>np.finfo(float).eps
    theta=float(np.sum(dt*yt)/J)
    psi=dt*(yt-theta*dt)
    score_checks.append({"scheme":scheme,"theta":theta,"residual_treatment_sum_squares":J,"mean_score":float(psi.mean())})
    np.testing.assert_allclose(psi.sum(),0.,atol=1e-10)
display(pd.DataFrame(score_checks))''')
    step('Evaluate both variance choices on each set of residuals',
         'Naive and overlap-sandwich intervals share a point estimate within a fold scheme. The reference uses normal critical values; a nonpositive sandwich variance remains an explicit failure, never clipped.',
         '''fits={scheme:estimate(yt,dt,memberships,allow_invalid_multiway=True) for scheme,(yt,dt) in residuals.items()}
demo_intervals=[]
for scheme,fit in fits.items():
    for variance,key in (("naive","se_naive"),("robust","se_multiway")):
        se=fit[key];error=fit["multiway_error"] if variance=="robust" else None
        demo_intervals.append({"scheme":scheme,"variance":variance,"estimate":fit["tau"],"se":se,"lower":fit["tau"]-fit["critical_value"]*se if se is not None else None,"upper":fit["tau"]+fit["critical_value"]*se if se is not None else None,"error":error})
display(pd.DataFrame(demo_intervals))''')
    step('Replay one archived world through the campaign driver',
         'The driver generates one world for all four cells and saves its fingerprint. Exact interval agreement is checked when producer package versions match; cross-version agreement is not assumed.',
         '''import importlib.util
spec=importlib.util.spec_from_file_location("frozen_validation_driver",RUN/"compute-tools/final-validation/validation_driver.py")
driver=importlib.util.module_from_spec(spec);spec.loader.exec_module(driver)
replay=driver.run_one((case,0))
expected=json.loads((RUN/"raw/validation_tau1/independent_tau1/rep_000000.json").read_text())
assert replay["world_sha256"]==expected["world_sha256"]==driver.digest_world(world)
producer=json.loads((RUN/"raw/validation_tau1/manifest.json").read_text())["packages"]
matching_versions=all(environment["packages"][k]==v for k,v in producer.items())
if matching_versions:
    for actual,saved in zip(replay["cells"],expected["cells"]):
        assert actual["status"]==saved["status"]=="ok"
        np.testing.assert_allclose([actual["estimate"],actual["lower"],actual["upper"]],[saved["estimate"],saved["lower"],saved["upper"]],rtol=1e-10,atol=1e-10)
print("World fingerprint matches; producer versions match:",matching_versions)''')
    step('Independently audit all frozen replication records',
         'The verifier checks planned identities, source hashes, seeds, truth, confidence levels and archive integrity. It recomputes statistics from raw intervals rather than trusting saved summary tables.',
         '''from scripts.audit_final_validation import audit
report,rows,canonical_plan=audit(plan_path,[RUN/"raw/validation_tau0",RUN/"raw/validation_tau1"],source_root=RUN)
frozen=json.loads((RUN/"frozen/audit.json").read_text())
assert report["all_planned_records_present"] and report["all_records_successful"]
assert len(rows)==12800
print("Raw interval rows:",len(rows))''')
    step('Reconcile denominators and archived summary arithmetic',
         'Coverage must show planned, attempted, valid, failed and missing counts. Complete-block pairing additionally requires all four successful cells on the same world.',
         '''assert sum(r["valid"] for r in report["summaries"])==12800
assert sum(r["complete_four_cell_blocks"] for r in report["complete_block_comparisons"] if r["outcome"]=="coverage")==3200
assert len(report["summaries"])==len(frozen["summaries"])
for actual,saved in zip(report["summaries"],frozen["summaries"]):
    assert (actual["scenario"],actual["cell"])==(saved["scenario"],saved["cell"])
    for field in ("planned","attempted","valid","failed","missing","covered","rejected_zero"):
        assert actual[field]==saved[field]
    for field in ("coverage95","coverage_mcse","mean_ci_width","bias","rmse"):
        np.testing.assert_allclose(actual[field],saved[field],rtol=1e-12,atol=1e-12)
print("3,200 complete worlds; 12,800 valid intervals; zero failed or missing cells.")''')
    step('Create analysis tables from audited records',
         'Full-precision CSVs preserve every registered scenario. The same audited tables feed the report and figures, reducing discrepancies between artifacts.',
         '''summaries=pd.DataFrame(report["summaries"])
intervals=pd.DataFrame(rows)
paired=pd.DataFrame(report["complete_block_comparisons"])
sensitivity=pd.DataFrame(report["sensitivity"])
(OUTPUT/"audit.json").write_text(json.dumps(report,indent=2,allow_nan=False))
for name,data in (("summaries.csv",summaries),("paired_complete_blocks.csv",paired),("sensitivity.csv",sensitivity),("intervals.csv",intervals)):
    data.to_csv(OUTPUT/name,index=False)
print("Saved audit and four complete tables.")''')
    step('Inspect known-effect independent-control coverage',
         'A control without common shocks checks baseline calibration before attributing deficits to dependence. These are fresh reconstructed outcomes, not authentication of the missing historical archive.',
         '''control=summaries.loc[summaries.scenario=="independent_tau1"]
display(control[["cell","planned","attempted","valid","covered","failed","missing","coverage95","coverage_mcse","coverage_wilson95"]])
assert control.loc[control.cell=="random_xfit__robust_var","covered"].item()==174
assert control.loc[control.cell=="grouped_xfit__robust_var","covered"].item()==175''')
    step('Inspect null size separately from nonnull power',
         'Rejecting zero when the true effect is zero is empirical size; doing so when the effect is nonzero is power. They answer different questions and must not share one label.',
         '''display(summaries.loc[summaries.scenario.str.startswith("independent_"),["scenario","cell","rejected_zero","valid","empirical_size","power"]])''')
    step('Recompute one Monte Carlo standard error transparently',
         'For R independent worlds, the plug-in coverage MCSE is sqrt(p(1-p)/R). Wilson intervals remain useful near boundary rates where plug-in MCSE can be zero.',
         '''from scripts.mirun_gate2_validation import wilson_interval
control_row=control.loc[control.cell=="random_xfit__robust_var"].iloc[0]
p_hat=control_row.covered/control_row.valid
manual_mcse=float(np.sqrt(p_hat*(1-p_hat)/control_row.valid))
np.testing.assert_allclose(manual_mcse,control_row.coverage_mcse,rtol=1e-12)
np.testing.assert_allclose(wilson_interval(int(control_row.covered),int(control_row.valid)),control_row.coverage_wilson95,rtol=1e-12)
print({"covered":int(control_row.covered),"valid":int(control_row.valid),"coverage":p_hat,"mcse":manual_mcse})''')
    step('Inspect the central paired coverage contrast',
         'Grouped robust minus random robust directly tests the incremental fold effect. The uncertainty uses aligned world-level differences, and non-significance does not establish equivalence.',
         '''central_mask=paired.scenario.str.contains("calendar_K")&paired.scenario.str.contains("_g1_")
display(paired.loc[central_mask&(paired.outcome=="coverage"),["scenario","difference","mcse","planned_blocks","complete_four_cell_blocks","excluded_blocks"]])''')
    step('Independently recompute a complete-block paired MCSE',
         'This reconstructs binary coverage indicators from the raw interval table and requires all four successful outcomes per world. It never substitutes two independent-binomial standard errors.',
         '''selected=intervals.loc[intervals.scenario=="calendar_K4_g1_tau1"].copy()
valid_blocks=selected.groupby("replication").filter(lambda g:len(g)==4 and g.cell.nunique()==4 and g.status.eq("ok").all() and g.panel_id.nunique()==1)
valid_blocks["hit"]=(valid_blocks.lower<=valid_blocks.truth)&(valid_blocks.upper>=valid_blocks.truth)
wide=valid_blocks.pivot(index="replication",columns="cell",values="hit").astype(float)
differences=wide["grouped_xfit__robust_var"]-wide["random_xfit__robust_var"]
manual_pair={"difference":float(differences.mean()),"mcse":float(differences.std(ddof=1)/np.sqrt(len(differences)))}
saved_pair=paired.loc[(paired.scenario=="calendar_K4_g1_tau1")&(paired.outcome=="coverage")].iloc[0]
np.testing.assert_allclose([manual_pair["difference"],manual_pair["mcse"]],[saved_pair.difference,saved_pair.mcse],rtol=1e-12)
print(manual_pair,"; complete blocks:",len(wide))''')
    step('Compare paired empirical-size outcomes',
         'Better calibration means approaching .95 coverage and .05 null size, not simply increasing coverage. Null size provides a separate check of false-positive behavior.',
         '''display(paired.loc[central_mask&(paired.outcome=="empirical_size"),["scenario","difference","mcse","complete_four_cell_blocks","excluded_blocks"]])''')
    step('Retain the full four-cell results grid',
         'Inspect every condition so favorable rows cannot replace the registered analysis. The K comparison is descriptive here; no approved matched-density H4 design is claimed.',
         '''display(summaries[["scenario","cell","valid","coverage95","empirical_size","power"]].reset_index(drop=True))''')
    step('Inspect bias, RMSE and interval widths',
         'Point-estimate error and interval calibration are distinct outcomes. Narrower intervals are not automatically better when they undercover.',
         '''display(summaries.loc[summaries.scenario.isin(["independent_tau1","calendar_K4_g1_tau1","calendar_K16_g1_tau1"]),["scenario","cell","bias","rmse","mean_ci_width","coverage95"]])''')
    step('Inspect labelled secondary variance sensitivities',
         't(G−1) and CR1-regime variants are heuristic sensitivity analyses on the same residuals. They never replace the reference CR0-normal method after results are seen.',
         '''display(sensitivity.loc[sensitivity.scenario.isin(["independent_tau1","calendar_K4_g1_tau1"]),["scenario","scheme","variant","planned","valid","undefined_or_missing","coverage","coverage_mcse","rejection_kind","rejection_rate"]])''')
    step('Check numerical and dependence diagnostics',
         'Nonfinite or nonpositive volatility states are failures; extreme finite returns are retained. Realized exposure and memberships describe the mechanism actually exercised by the campaign.',
         '''diagnostics=pd.DataFrame(report["diagnostics"])
assert diagnostics.nonfinite_sigma.sum()==0 and diagnostics.nonpositive_sigma.sum()==0
print("Nonfinite sigma:",int(diagnostics.nonfinite_sigma.sum()),"; nonpositive sigma:",int(diagnostics.nonpositive_sigma.sum()))
display(diagnostics.head(16))''')
    step('Load and check frozen daily regime labels',
         'The exploratory daily rule uses strictly prior VIX observations, 20-observation averages and trailing-five-year quartiles. Mixed labels remain mixed; labels alone do not authenticate the source prices or VIX series.',
         '''daily=json.loads((RUN/"frozen/daily.json").read_text())
labels=pd.read_csv(RUN/"frozen/daily_labels.csv")
assert len(labels)==daily["label_dates"]==1249
assert labels.regime_label.value_counts().to_dict()==daily["label_counts_dates"]
display(labels.regime_label.value_counts().rename("dates").to_frame())''')
    step('Reconcile candidates, available histories and returns',
         'The roster, latest available price histories and historical CAR output refer to different samples. Six available firms are usable for a scoped descriptive check; the count alone is not a validity criterion.',
         '''assert sum(x["valid_return_rows"] for x in daily["availability"])==daily["return_rows"]==1872
display(pd.DataFrame(daily["availability"]))
print("Eight candidates; six saved histories; seven legacy CAR rows. No silent substitution.")''')
    step('Check aligned daily-pair diagnostics',
         'Correlation needs aligned observations within the same regime label. These aggregates support descriptive arithmetic, while the planned broad calm-versus-turbulent comparison needs more common support.',
         '''for pair in daily["pairs"]:
    if pair["status"]=="descriptive":
        np.testing.assert_allclose(pair["correlation"],pair["sample_covariance"]/np.sqrt(pair["variance_a"]*pair["variance_b"]),rtol=1e-12)
assert daily["descriptive_pairs_by_label"]["calm"]==0
display(pd.DataFrame(daily["pairs"]).query("aligned_sessions > 0"))
print("SCM: NOT EXECUTED. Historical CARs need their original combined prices and market inputs.")''')
    step('Regenerate the shared figure assets',
         'One builder generates the figures consumed by the notebook, report and slides. It uses the recomputed audit and frozen daily aggregates, not hand-entered plotted values.',
         '''from scripts.build_final_results_assets import build
assets=OUTPUT/"assets"
headline=build(OUTPUT/"audit.json",RUN/"frozen/daily.json",assets)
assert headline["complete_worlds"]==3200 and headline["interval_rows"]==12800
print("Figure directory:",assets)''')
    step('Plot the independent-control coverage comparison',
         'The nominal .95 reference makes calibration shortfalls visible. These are exploratory control findings rather than proof of a dense-dependence mechanism.',
         '''display(Image(filename=str(assets/"coverage.png")))''')
    step('Plot coverage across all registered scenarios',
         'The complete-grid view preserves unfavorable and favorable outcomes together. Scenario differences share seeds and are not independent pooled experiments.',
         '''display(Image(filename=str(assets/"all_coverage.png")))''')
    step('Plot daily-data support by regime label',
         'Available aligned observations determine which descriptive comparisons are supported. This feasibility figure is separate from simulated known-truth coverage.',
         '''display(Image(filename=str(assets/"daily_support.png")))''')
    step('Run a clearly labelled MOCK arithmetic check',
         'A hand-built fixture contains exactly 95 covered intervals and five null rejections. This checks metric arithmetic only and provides no evidence of estimator calibration.',
         '''from src.evaluation.metrics import summarize_intervals
lower=np.r_[np.full(95,-1.),np.full(5,.1)];upper=np.ones(100)
mock=summarize_intervals(lower,upper,truth=0.,expected_replications=100)
assert int(((lower<=0)&(upper>=0)).sum())==95
assert int(((upper<0)|(lower>0)).sum())==5
print("MOCK fixture:",mock)''')
    step('Save the reproduction record',
         'The final record binds regenerated outputs to the bundle, environment and one-world replay. It explicitly records the exploratory status and data-redistribution boundary.',
         '''record={"evidence_class":"EXPLORATORY","environment":environment,"complete_worlds":headline["complete_worlds"],"interval_rows":headline["interval_rows"],"failed":headline["failed_cells"],"missing":headline["missing_cells"],"actual_component_replay":{"world_sha256":replay["world_sha256"],"same_producer_package_versions":matching_versions},"provider_prices_redistributed":False,"production_approved":False}
(OUTPUT/"reproduction.json").write_text(json.dumps(record,indent=2,allow_nan=False))
print(json.dumps(record,indent=2))
print("Regenerated files:",OUTPUT)''')
    md('''## Interpretation and next steps

The software and exploratory archive are reproducible, including actual DGP/estimator execution, independent raw-result verification and figure regeneration. Independent-control miscalibration and the dependence-manipulation boundary prevent a validated production answer to the primary question. H4 remains unresolved. Missing original historical inputs and Synthetic Control have no fabricated results.

Before submission, fill team/section blanks, review the claims as a team, apply the course PPT template, record the members, and complete Drive sharing and form submission. Provider prices and source VIX levels are excluded; daily arithmetic is checked from frozen derived aggregates.

References: [DML (2018)](https://doi.org/10.1111/ectj.12097); [multiway DML](https://doi.org/10.1080/07350015.2021.1895815) and [correction](https://doi.org/10.1080/07350015.2021.1970572); [Balkus, Laith, Hejazi preprint v3](https://arxiv.org/abs/2601.10899v3); [ADEMP](https://doi.org/10.1002/sim.8086). Full references appear in the report.''')
    return cells
