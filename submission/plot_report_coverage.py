"""Print-sized version of the frozen coverage figure; identical audited values."""
from pathlib import Path
import json,os
os.environ.setdefault('MPLCONFIGDIR','/tmp/ada-report-mpl')
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parents[1]
a=json.loads((ROOT/'results/raw/final_validation_audit_20261112/audit.json').read_text())
by={(r['scenario'],r['cell']):r for r in a['summaries']}
cells=['random_xfit__naive_var','random_xfit__robust_var','grouped_xfit__naive_var','grouped_xfit__robust_var'];names=['Random + naive','Random + robust','Grouped + naive','Grouped + robust'];colors=['#8B969F','#087F8C','#B89769','#B65C39']
plt.rcParams.update({'font.size':8,'axes.spines.top':False,'axes.spines.right':False})
f,ax=plt.subplots(figsize=(3.5,2.8))
for k,case in enumerate(['independent_tau1','calendar_K4_g1_tau1']):
 for i,cell in enumerate(cells):
  r=by[case,cell];x=r['coverage95'];lo,hi=r['coverage_wilson95'];ax.errorbar(x,k+(i-1.5)*.13,xerr=[[x-lo],[hi-x]],fmt='o',markersize=3.5,capsize=2,lw=1,color=colors[i],label=names[i] if k==0 else None)
ax.axvline(.95,color='#475569',ls='--',lw=.8,label='Nominal 95%');ax.set_yticks([0,1],['Independent\ncontrol','Calendar\nK=4, gamma=1']);ax.invert_yaxis();ax.set_xlim(.5,1.015);ax.set_xticks([.5,.6,.7,.8,.9,1]);ax.tick_params(labelsize=7.5);ax.set_xlabel('Coverage (Wilson 95% Monte Carlo interval)',fontsize=7.5);ax.set_title('EXPLORATORY | tau = 1 | R = 200',loc='left',fontsize=9,fontweight='bold');ax.grid(axis='x',alpha=.15)
ax.legend(ncol=2,fontsize=7,frameon=False,loc='upper center',bbox_to_anchor=(.35,-.42),handlelength=1.4,columnspacing=.9)
f.subplots_adjust(left=.24,right=.98,top=.86,bottom=.36)
f.savefig(ROOT.parent/'ADA PROJECT DELIVERABLES/06_IEEE_Report/coverage_report.png',dpi=360,bbox_inches='tight',pad_inches=.04)
