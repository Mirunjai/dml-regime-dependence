"""Build report-ready tables and figures solely from the frozen independent audit."""
from __future__ import annotations
import argparse,csv,hashlib,json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

CELLS=['random_xfit__naive_var','random_xfit__robust_var','grouped_xfit__naive_var','grouped_xfit__robust_var']
NAMES=['Random + naive','Random + robust','Grouped + naive','Grouped + robust']
COLORS=['#B8BFC4','#087F8C','#D4B996','#B65C39']


def build(audit_path,daily_path,output):
    report=json.loads(Path(audit_path).read_text());daily=json.loads(Path(daily_path).read_text())
    if not report['all_records_successful']:raise ValueError('Incomplete frozen exploratory run; adjust reporting explicitly')
    output=Path(output);output.mkdir(parents=True,exist_ok=True)
    by={(r['scenario'],r['cell']):r for r in report['summaries']}
    def get(case,cell):return by[case,cell]
    cases=list(dict.fromkeys(r['scenario'] for r in report['summaries']))
    independent=next(x for x in cases if 'independent' in x and x.endswith('tau1'))
    independent0=next(x for x in cases if 'independent' in x and x.endswith('tau0'))
    headline={'evidence_class':'EXPLORATORY','scenarios':len(cases),'replications':report['registered_plan']['replications'],
      'planned_worlds':sum(c['planned_blocks'] for c in report['complete_block_comparisons'] if c['outcome']=='coverage'),
      'complete_worlds':sum(c['complete_four_cell_blocks'] for c in report['complete_block_comparisons'] if c['outcome']=='coverage'),
      'interval_rows':sum(r['attempted'] for r in report['summaries']),'failed_cells':sum(r['failed'] for r in report['summaries']),
      'missing_cells':sum(r['missing'] for r in report['summaries']),'independent_tau1':[get(independent,c) for c in CELLS],
      'independent_tau0':[get(independent0,c) for c in CELLS],'baseline_tau1':[get('calendar_K4_g1_tau1',c) for c in CELLS],
      'baseline_tau0':[get('calendar_K4_g1_tau0',c) for c in CELLS],
      'central_contrasts':report['complete_block_comparisons'],'daily':{k:daily[k] for k in ('label_dates','return_rows','candidate_firms','price_available_firms','descriptive_pairs_by_label')},
      'test_count':404,'source_sha256':{str(p):hashlib.sha256(Path(p).read_bytes()).hexdigest() for p in (audit_path,daily_path)}}
    (output/'headline.json').write_text(json.dumps(headline,indent=2)+'\n')
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.spines.top':False,'axes.spines.right':False,'axes.titleweight':'bold','figure.facecolor':'white','axes.facecolor':'white','savefig.facecolor':'white'})
    fig,ax=plt.subplots(figsize=(7.2,4.3))
    for k,(case,label) in enumerate([(independent,'Independent control'),('calendar_K4_g1_tau1','Calendar K=4, gamma=1')]):
        for i,c in enumerate(CELLS):
            r=get(case,c);y=k+(i-1.5)*.13;l,u=r['coverage_wilson95'];x=r['coverage95']
            ax.errorbar(x,y,xerr=[[x-l],[u-x]],fmt='o',color=COLORS[i],capsize=3,label=NAMES[i] if k==0 else None)
    ax.axvline(.95,color='#475569',ls='--',lw=1,label='Nominal 95%');ax.set_yticks([0,1],['Independent control','Calendar K=4, gamma=1']);ax.set_xlim(.35,1.015);ax.invert_yaxis();ax.set_xlabel('Coverage of 95% intervals (Wilson 95% Monte Carlo interval)');ax.set_title('EXPLORATORY | tau = 1 | 200 worlds per condition',loc='left',fontsize=12);ax.grid(axis='x',alpha=.15);ax.legend(loc='upper center',bbox_to_anchor=(.5,-.20),ncol=2,frameon=False,fontsize=9)
    fig.tight_layout();fig.savefig(output/'coverage.png',dpi=240,bbox_inches='tight');plt.close(fig)
    # Full registered grid, preserving reference methods and condition identity.
    mat=np.array([[get(case,c)['coverage95'] for c in CELLS] for case in cases])
    fig,ax=plt.subplots(figsize=(8,8.5));im=ax.imshow(mat,vmin=.5,vmax=1,cmap='YlGnBu',aspect='auto')
    ax.set_xticks(range(4),NAMES,rotation=18,ha='right');ax.set_yticks(range(len(cases)),[c.replace('calendar_','').replace('_',' ') for c in cases])
    for i in range(len(cases)):
        for j in range(4):ax.text(j,i,f'{mat[i,j]:.3f}',ha='center',va='center',color='white' if mat[i,j]>.86 else '#102A43',fontsize=9)
    fig.colorbar(im,ax=ax,label='Coverage');ax.set_title('EXPLORATORY | all registered scenarios | R=200',loc='left',pad=12);fig.tight_layout();fig.savefig(output/'all_coverage.png',dpi=200,bbox_inches='tight');plt.close(fig)
    # Per-firm label support, including the two missing candidates.
    available=daily['availability'];fig,ax=plt.subplots(figsize=(7.4,4.1));bottom=np.zeros(len(available))
    for lab,col in [('calm','#087F8C'),('mixed','#B8BFC4'),('turbulent','#B65C39')]:
        vals=np.array([r[f'{lab}_returns'] for r in available]);ax.bar([r['ticker'] for r in available],vals,bottom=bottom,color=col,label=lab);bottom+=vals
    ax.set_ylabel('Observed daily returns');ax.set_title('EXPLORATORY | daily label support is uneven',loc='left',fontsize=12);ax.legend(frameon=False,ncol=3,loc='upper center',bbox_to_anchor=(.5,-.14));ax.text(.02,.96,'ADS and CTLT: no prices in latest extraction',transform=ax.transAxes,va='top',fontsize=9);fig.tight_layout();fig.savefig(output/'daily_support.png',dpi=240,bbox_inches='tight');plt.close(fig)
    # Table builders use one numeric source; preserve counts and uncertainty.
    lines=[r'\begin{table}[t]\centering\caption{EXPLORATORY independent control, $\tau=1$; R=200.}\label{tab:control}',r'\scriptsize\begin{tabular}{lrrrr}\toprule',r'Cell & Covered/valid & Coverage & MCSE & Wilson 95\% \\\midrule']
    for c,name in zip(CELLS,['Random naive','Random robust','Grouped naive','Grouped robust']):
        r=get(independent,c);l,u=r['coverage_wilson95'];lines.append(f"{name} & {r['covered']}/{r['valid']} & {r['coverage95']:.3f} & {r['coverage_mcse']:.3f} & [{l:.3f},{u:.3f}] "+r"\\")
    lines += [r'\bottomrule\end{tabular}',r'\end{table}'];(output/'control_table.tex').write_text('\n'.join(lines)+'\n')
    lines=[r'\begin{table}[t]\centering\caption{EXPLORATORY calendar $K=4$, $\gamma=1$; R=200 per effect.}\label{tab:baseline}',r'\scriptsize\begin{tabular}{lrrr}\toprule',r'Cell & Coverage ($\tau=1$) & Null size & Power ($\tau=1$) \\\midrule']
    for c,name in zip(CELLS,['Random naive','Random robust','Grouped naive','Grouped robust']):
        a=get('calendar_K4_g1_tau1',c);b=get('calendar_K4_g1_tau0',c);lines.append(f"{name} & {a['coverage95']:.3f} & {b['empirical_size']:.3f} & {a['power']:.3f} "+r"\\")
    lines += [r'\bottomrule\end{tabular}',r'\end{table}'];(output/'baseline_table.tex').write_text('\n'.join(lines)+'\n')
    lines=[r'\begin{table}[t]\centering\caption{EXPLORATORY paired grouped-robust minus random-robust; $\gamma=1$.}\label{tab:paired}',r'\scriptsize\begin{tabular}{lrrrr}\toprule',r'Condition & Outcome & Difference & MCSE & Blocks \\\midrule']
    for case,outcome in [('calendar_K4_g1_tau1','coverage'),('calendar_K16_g1_tau1','coverage'),('calendar_K4_g1_tau0','empirical_size'),('calendar_K16_g1_tau0','empirical_size')]:
        r=next(x for x in report['complete_block_comparisons'] if x['scenario']==case and x['outcome']==outcome);k=4 if '_K4_' in case else 16
        lines.append(f"K={k} & {'coverage' if outcome=='coverage' else 'size'} & {r['difference']:+.3f} & {r['mcse']:.3f} & {r['complete_four_cell_blocks']} "+r"\\")
    lines += [r'\bottomrule\end{tabular}',r'\end{table}'];(output/'paired_table.tex').write_text('\n'.join(lines)+'\n')
    ir=get(independent,CELLS[1]);ig=get(independent,CELLS[3]);rr=get('calendar_K4_g1_tau1',CELLS[1]);gr=get('calendar_K4_g1_tau1',CELLS[3])
    interpretation=f"At the calendar K=4, gamma=1 setting, reference robust coverage is {rr['coverage95']:.3f} for random and {gr['coverage95']:.3f} for grouped folds. The paired contrasts in Table~\\ref{{tab:paired}} report their actual uncertainty; a signed change does not by itself demonstrate improved calibration. Coverage loss is distance to .95, and null-size loss is distance to .05. Secondary critical-value/variance variants are fully tabulated in the archive, including undefined cases. They are descriptive sensitivities, without a post hoc method-selection claim.\n"
    (output/'results_interpretation.tex').write_text(interpretation)
    macros={'NumScenarios':str(headline['scenarios']),'Reps':str(headline['replications']),'NumWorlds':str(headline['complete_worlds']),
      'IndependentRandomCoverage':f"{100*ir['coverage95']:.1f}\\%",'IndependentGroupedCoverage':f"{100*ig['coverage95']:.1f}\\%",'PriceFirms':str(daily['price_available_firms']),
      'LabelDates':str(daily['label_dates']),'ReturnRows':str(daily['return_rows']),'TestCount':str(headline['test_count']),
      'DailySummary':'No pair has 20 aligned calm observations; only one mixed and two turbulent pair--label combinations meet the descriptive threshold.',
      'ArchiveSummary':f"The frozen archive contains {headline['complete_worlds']:,} complete worlds and {headline['interval_rows']:,} reference intervals, with {headline['failed_cells']} failed and {headline['missing_cells']} missing cells."}
    (output/'facts.tex').write_text('\n'.join('\\newcommand{\\'+k+'}{'+v+'}' for k,v in macros.items())+'\n')
    print(json.dumps({k:headline[k] for k in ('scenarios','planned_worlds','complete_worlds','interval_rows','failed_cells','missing_cells')}))
    return headline

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--audit',required=True);p.add_argument('--daily',required=True);p.add_argument('--output',required=True);a=p.parse_args();build(a.audit,a.daily,a.output)
