"""Exploratory, source-pinned DML size/coverage campaign.

Runs the proposal's full 2x3x2 DGP grid at tau=0 and tau=1. This is a
pre-production calibration, not an approved production run. Same replication
seed is reused across paired conditions and all four estimator cells.
"""
from __future__ import annotations
import argparse, json, hashlib, platform, time
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import numpy as np
from scipy.stats import t as student_t
from src.infra import dml_engine as E

OUT = ROOT / "results" / "calibration" / "mirun_dml_size_coverage_2026-11-12.json"
REPS = 100
ROOT_SEED = 60000
Z = 1.959963984540054

def wilson(x, n):
    if n == 0: return [None, None]
    p=x/n; den=1+Z*Z/n
    center=(p+Z*Z/(2*n))/den
    half=Z*np.sqrt(p*(1-p)/n+Z*Z/(4*n*n))/den
    return [float(max(0,center-half)),float(min(1,center+half))]

def summarize(records, truth, k):
    good=[r for r in records if r["status"]=="ok"]
    fail=len(records)-len(good)
    covered=[r["lower"] <= truth <= r["upper"] for r in good]
    rejected=[not (r["lower"] <= 0.0 <= r["upper"]) for r in good]
    n=len(good); hits=sum(covered); rej=sum(rejected)
    variance_sensitivity={}
    if records and records[0]["cell"].endswith("robust_var"):
      valid=[r for r in good if r.get("se") is not None and r.get("estimate") is not None]
      df=max(int(k)-1,1)
      crit=float(student_t.ppf(0.975,df))
      lo=[r["estimate"]-crit*r["se"] for r in valid]
      hi=[r["estimate"]+crit*r["se"] for r in valid]
      nh=sum(a <= truth <= b for a,b in zip(lo,hi))
      nr=sum(not (a <= 0.0 <= b) for a,b in zip(lo,hi))
      nv=len(valid)
      variance_sensitivity={"cr0_t_df_K_minus_1":{
        "valid":nv,"degrees_freedom":df,"critical_value":crit,
        "coverage_conditional":nh/nv if nv else None,
        "coverage_wilson95":wilson(nh,nv),
        "rejection_rate":nr/nv if nv else None,
        "rejection_wilson95":wilson(nr,nv)}}
    return {
      "planned":len(records),"valid":n,"failed":fail,
      "variance_sensitivity":variance_sensitivity,
      "coverage_conditional":hits/n if n else None,
      "coverage_mcse":float(np.sqrt((hits/n)*(1-hits/n)/n)) if n else None,
      "coverage_wilson95":wilson(hits,n),
      "rejection_rate":rej/n if n else None,
      "rejection_wilson95":wilson(rej,n),
      "mean_ci_width":float(np.mean([r["upper"]-r["lower"] for r in good])) if n else None,
      "mean_estimate":float(np.mean([r["estimate"] for r in good])) if n else None,
      "all_attempted_coverage_bounds":[hits/len(records),(hits+fail)/len(records)] if records else [None,None],
    }

def paired_coverage(records, truth):
    """Use only complete, identified four-cell worlds, including for two-cell contrasts."""
    diffs = []
    for record in records:
        cells = record["cells"]
        if (record.get("paired_block_status") != "complete" or len(cells) != 4
                or {c["cell"] for c in cells} != set(E.CELL_MAP)
                or any(c["status"] != "ok" for c in cells)):
            continue
        identity = (record.get("paired_block_id"), record.get("world_sha256"))
        if not all(identity) or any((c.get("paired_block_id"), c.get("world_sha256")) != identity for c in cells):
            continue
        by = {c["cell"]: c for c in cells}
        a, b = by["random_xfit__robust_var"], by["grouped_xfit__robust_var"]
        diffs.append(float(b["lower"] <= truth <= b["upper"]) - float(a["lower"] <= truth <= a["upper"]))
    return {"valid_pairs": len(diffs), "excluded_blocks": len(records)-len(diffs),
            "difference": float(np.mean(diffs)) if diffs else None,
            "mcse": float(np.std(diffs, ddof=1)/np.sqrt(len(diffs))) if len(diffs)>1 else None}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reps", type=int, default=REPS)
    parser.add_argument("--out", type=Path, default=OUT)
    args = parser.parse_args(argv)
    if args.reps < 2:
        parser.error("Require at least two replications for Monte Carlo uncertainty")
    out = args.out
    raw_dir = out.with_suffix("")
    if raw_dir == out:
        parser.error("--out must be a file with an extension, such as screening.json")
    if out.exists() or raw_dir.exists():
        parser.error("Output already exists; choose a fresh path to preserve prior evidence")
    raw_dir.mkdir(parents=True)
    cfg=E.load_proposal(ROOT/"configs/mirun_gate3.yaml")
    values=E.resolve_parameters(cfg,smoke=True)
    conditions=[]
    for d in (0.25,0.50,0.75):
      for k in (4,16):
       for gamma in (0.0,1.0):
        for kind,tau in (("zero_effect",0.0),("coverage",1.0)):
         conditions.append({"name":f"d{d:g}_K{k}_g{gamma:g}_{kind}",
            "density":d,"K":k,"gamma":gamma,"tau":tau,"kind":kind})
    E.save_json_atomic(raw_dir/"manifest.json", {
        "evidence_class": "EXPLORATORY", "conditions": conditions,
        "replications_per_condition": args.reps, "root_seed": ROOT_SEED,
        "source_sha256": {name: hashlib.sha256((ROOT/name).read_bytes()).hexdigest()
                          for name in ("src/infra/dml_engine.py", "research/week2_completion/dgp.py",
                                       "research/week2_completion/dml.py", "scripts/mirun_dml_size_coverage_calibration.py")},
        "software": E.software_versions(), "proposal_values": values,
        "failure_policy": "retain every attempted world; paired comparisons require four successful identified cells"})
    allrows=[]; started=time.time()
    for ci,c in enumerate(conditions,1):
      print(f"[{ci}/{len(conditions)}] {c['name']}",flush=True)
      reps=[]
      condition_dir = raw_dir/c["name"]
      condition_dir.mkdir()
      for rep in range(args.reps):
        record=E.run_replication(cfg,values,c,rep,ROOT_SEED,label="exploratory_calibration")
        record["cells"]=[{**cell,"replication_id":rep} for cell in record["cells"]]
        reps.append(record)
        E.save_json_atomic(condition_dir/f"rep_{rep:06d}.json", record)
        if (rep+1)%10==0: print(f"  {rep+1}/{args.reps}",flush=True)
      summaries={}
      for cell in E.CELL_MAP:
        cellrows=[]
        for record in reps:
          x=next(v for v in record["cells"] if v["cell"]==cell)
          cellrows.append(x)
        summaries[cell]=summarize(cellrows,c["tau"],c["K"])
      summaries["paired_grouped_robust_minus_random_robust"] = paired_coverage(reps, c["tau"])
      allrows.append({"condition":c,"cells":summaries,
        "paired_worlds":sum(r["paired_block_status"]=="complete" for r in reps),
        "incomplete_worlds":sum(r["paired_block_status"]!="complete" for r in reps),
        "mean_seconds_per_replication":float(np.mean([r["total_seconds"] for r in reps]))})
      partial={"schema":"project_a_dml_size_coverage_calibration_v1",
        "status":"RUNNING_EXPLORATORY_NOT_GATE_APPROVAL",
        "grid":"density={0.25,0.50,0.75} x K={4,16} x gamma={0,1} x tau={0,1}",
        "conditions_planned":len(conditions),"conditions_completed":len(allrows),
        "raw_records_directory":str(raw_dir),
        "replications_per_condition":args.reps,"root_seed":ROOT_SEED,"conditions":allrows}
      out.parent.mkdir(parents=True,exist_ok=True)
      E.save_json_atomic(out, partial)
    result={
      "schema":"project_a_dml_size_coverage_calibration_v1",
      "status":"EXPLORATORY_NOT_GATE_APPROVAL_NOT_PRODUCTION",
      "grid":"density={0.25,0.50,0.75} x K={4,16} x gamma={0,1} x tau={0,1}",
      "replications_per_condition":args.reps,"root_seed":ROOT_SEED,
      "raw_records_directory":str(raw_dir),
      "same_seed_pairing":"Same seed IDs across tau=0/tau=1 and grid conditions; each DGP stream remains internally named.",
      "estimator":"Unmodified research.week2_completion.dml.run_dml; naive and overlap-sandwich CR0-normal",
      "dgp_file_sha1":hashlib.sha1((ROOT/"research/week2_completion/dgp.py").read_bytes()).hexdigest(),
      "dml_sha256":hashlib.sha256((ROOT/"research/week2_completion/dml.py").read_bytes()).hexdigest(),
      "engine_sha256":hashlib.sha256((ROOT/"src/infra/dml_engine.py").read_bytes()).hexdigest(),
      "python":platform.python_version(),"numpy":np.__version__,
      "elapsed_seconds":time.time()-started,"conditions":allrows,
      "limitations":[
        f"{args.reps} replications per cell are screening/calibration, not final precision for a 95% coverage claim.",
        "Coverage and size are conditional on successful intervals; all-attempted bounds and failure counts are also reported.",
        "tau=0 rejection rate is empirical size; tau=1 rejection rate is power; tau=1 coverage is reported separately.",
        "CR0-normal is evaluated as implemented; CR0-t with df=K-1 is a same-world sensitivity. CR1-regime-t is not computed because the current estimator does not expose a separately validated regime-only meat component.",
        "No production approval or Gate 2/3 sign-off is implied."
      ]
    }
    out.parent.mkdir(parents=True,exist_ok=True)
    E.save_json_atomic(out, result)
    print(f"Saved {out}; elapsed={result['elapsed_seconds']:.1f}s",flush=True)

if __name__=="__main__": main()
