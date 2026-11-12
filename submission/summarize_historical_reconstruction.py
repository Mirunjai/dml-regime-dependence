"""Compare a fresh reconstruction with printed summaries without inventing archive authenticity."""
import json,math,statistics
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
old=json.loads((ROOT/'results/tables/mirun_session5_controls.json').read_text())
audit=json.loads((ROOT/'results/raw/final_validation_audit_20261112/audit.json').read_text())
print([s['id'] for s in audit['registered_plan']['scenarios'] if s['config']['tau']==1])
mapping={'C0_default_benchmark':'calendar_K4_g1_tau1','C1_independent_control':'independent_tau1','C2_factor_only':'factor_only_tau1','C3_factor_off_unmatched':'factor_off_tau1','C4_factor_off_variance_matched':'factor_off_variance_matched_tau1'}
checks=[]
for oldcase,case in mapping.items():
 for label,previous in old['conditions'][oldcase]['cells'].items():
  scheme,var=label.split('/');cell=scheme+'_xfit__'+('robust' if var=='multiway' else 'naive')+'_var'
  row=next(x for x in audit['summaries'] if x['scenario']==case and x['cell']==cell)
  records=[json.loads(f.read_text()) for f in (ROOT/'results/raw/final_validation_frozen/validation_tau1'/case).glob('rep_*.json')]
  cells=[next(c for c in r['cells'] if c['cell']==cell) for r in records]
  sd=statistics.stdev(c['estimate'] for c in cells)
  actual={'valid':row['valid'],'failed':row['failed'],'coverage':row['coverage95'],'mcse':round(row['coverage_mcse'],3),'se_over_sd':round(statistics.mean(c['se'] for c in cells)/sd,2),'sd_tau':round(sd,3)}
  for field,value in actual.items():checks.append({'historical_case':oldcase,'scenario':case,'cell':cell,'field':field,'printed':previous[field],'fresh_recomputed':value,'matches_printed_precision':value==previous[field]})
result={'evidence_class':'EXPLORATORY','purpose':'Reproduction of rounded transcript summaries at printed precision; NOT authentication of original raw archive','fields_compared':len(checks),'matching_fields':sum(x['matches_printed_precision'] for x in checks),'discrepancies':[x for x in checks if not x['matches_printed_precision']],'checks':checks,'original_raw_archive_authenticated':False}
out=ROOT/'results/raw/final_historical_reconstruction_20261112';out.mkdir(exist_ok=False);(out/'comparison.json').write_text(json.dumps(result,indent=2)+'\n')
print({k:result[k] for k in ('fields_compared','matching_fields','original_raw_archive_authenticated')});print(result['discrepancies'])
