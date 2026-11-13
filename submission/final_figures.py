"""Publication figures from audited final evidence; no estimator execution."""
from pathlib import Path
import json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'results/raw/final_research_20261112'
OUT=BASE/'final_assets';OUT.mkdir(parents=True,exist_ok=True)
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.spines.top':False,'axes.spines.right':False,
                     'savefig.dpi':220,'figure.dpi':130,'axes.titleweight':'bold','pdf.fonttype':42})
BLUE='#245B87';ORANGE='#BE5A36'


def save(fig,name):
    fig.savefig(OUT/(name+'.png'),bbox_inches='tight',facecolor='white')
    fig.savefig(OUT/(name+'.pdf'),bbox_inches='tight',facecolor='white');plt.close(fig)


def real_figures():
    audit=json.loads((BASE/'real_analysis_v3/audit.json').read_text())
    f=pd.read_csv(BASE/'real_analysis_v3/aligned_returns.csv'); firms=audit['firms']
    fig,axes=plt.subplots(1,2,figsize=(9.4,4),layout='constrained')
    for ax,lab in zip(axes,['calm','turbulent']):
        c=f.loc[f.regime_label==lab,firms].corr().to_numpy()
        im=ax.imshow(c,vmin=0,vmax=1,cmap='Blues')
        ax.set_xticks(range(6),firms,rotation=45,ha='right');ax.set_yticks(range(6),firms)
        ax.set_title(f'{lab.capitalize()} ({audit["label_counts"][lab]} dates)')
        for i in range(6):
            for j in range(6):ax.text(j,i,f'{c[i,j]:.2f}',ha='center',va='center',fontsize=9,color='white' if c[i,j]>.58 else '#102D43')
    fig.colorbar(im,ax=list(axes),shrink=.8,label='Pearson correlation');save(fig,'aligned_regime_correlations')
    fig,ax=plt.subplots(figsize=(7.2,3.6),layout='constrained')
    for k,(kind,label) in enumerate([('raw_returns','Adjusted-close returns'),('prior_market_residuals','Prior market-model residuals')]):
        for j,length in enumerate([10,20,40]):
            r=next(v for v in audit['block_bootstrap'][kind] if v['block_length']==length)
            y=k+(j-1)*.18;d=r['observed']['difference'];lo,hi=r['percentile95']
            ax.errorbar(d,y,xerr=[[d-lo],[hi-d]],fmt='o',capsize=3,color=BLUE if j==1 else '#869DAF',label=f'{length}-session blocks' if k==0 else None)
    ax.axvline(0,color='#777777',linestyle='--',linewidth=1)
    ax.set_yticks([0,1],['Raw returns','Market residuals']);ax.invert_yaxis()
    ax.set_xlabel('Turbulent minus calm mean pairwise correlation')
    ax.set_title('Joint calendar-block bootstrap, percentile 95% intervals')
    ax.legend(loc='upper right',fontsize=8);save(fig,'real_correlation_contrast')
    labels=pd.read_csv(BASE/'real_analysis_v3/daily_labels_and_thresholds.csv',parse_dates=['date'])
    fig,ax=plt.subplots(figsize=(9.4,3),layout='constrained')
    ax.plot(labels.date,labels.pre_event_vix20,color=BLUE,lw=.9,label='Strictly prior 20-observation VIX mean')
    ax.plot(labels.date,labels.vix_p25,color='#83A1B5',lw=.8,label='Earlier five-year p25')
    ax.plot(labels.date,labels.vix_p75,color=ORANGE,lw=.8,label='Earlier five-year p75')
    ax.set_ylabel('VIX index points');ax.set_title('Regime classification uses only earlier observations');ax.legend(fontsize=8,ncol=3,loc='upper left')
    save(fig,'daily_regime_timeline')
    f=pd.read_csv(BASE/'real_analysis_v3/fresh_classical_event_study.csv')
    fig,ax=plt.subplots(figsize=(7.2,3.6),layout='constrained');x=np.arange(len(f))
    ax.bar(x,100*f.car_primary,color=[BLUE if v>=0 else ORANGE for v in f.car_primary])
    ax.axhline(0,color='#555555',lw=.8);ax.set_xticks(x,f.ticker);ax.set_ylabel('CAR, percentage points')
    ax.set_title('Fresh market-model event study, event window [−1, +1]')
    ax.text(.01,-.25,'Descriptive seven-event sample. ADS uses the verified BFH issuer crosswalk.',transform=ax.transAxes,fontsize=8)
    save(fig,'fresh_classical_cars')


def structure_figures():
    s=json.loads((BASE/'structure/structure.json').read_text());fig,axes=plt.subplots(1,2,figsize=(8.6,3.3),layout='constrained')
    for K,color in [(4,BLUE),(16,ORANGE)]:
        a=sorted([r for r in s['scaling'] if r['K']==K],key=lambda r:r['n'])
        axes[0].loglog([r['n'] for r in a],[r['shared_pairs']['mean'] for r in a],marker='o',color=color,label=f'K={K}')
        a=sorted([r for r in s['grid'] if r['K']==K and r['density'] in [.25,.5,.75]],key=lambda r:r['density'])
        axes[1].plot([r['density'] for r in a],[r['average_common_shock_correlation']['mean'] for r in a],marker='o',color=color,label=f'K={K}')
    axes[0].set_xlabel('Number of events n');axes[0].set_ylabel('Mean shared-regime event pairs');axes[0].set_title('Pair counts grow approximately as n²')
    axes[1].set_xlabel('Configured calendar fraction');axes[1].set_ylabel('Analytical mean common-shock correlation');axes[1].set_title('Dependence increases across density settings')
    for ax in axes:ax.legend(fontsize=8)
    save(fig,'structural_manipulation')


def simulation_figures():
    p=BASE/'final_interpretation/interpretation.json'
    if not p.exists():return
    facts=json.loads(p.read_text());rows=facts['summaries'];fig,axes=plt.subplots(1,2,figsize=(9.4,3.5),layout='constrained')
    cells=['random_xfit__naive_var','random_xfit__robust_var','grouped_xfit__naive_var','grouped_xfit__robust_var']
    for ax,K in zip(axes,[4,16]):
        for j,cell in enumerate(cells):
            r=next(r for r in rows if r['scenario']==f'main_K{K}_d0.5_g1_tau1' and r['cell']==cell)
            lo,hi=r['coverage_wilson95'];v=r['coverage95'];ax.errorbar(j,v,yerr=[[v-lo],[hi-v]],fmt='o',capsize=3,color=BLUE if 'random' in cell else ORANGE)
        ax.axhline(.95,color='#777777',ls='--',lw=1,label='Nominal .95')
        ax.set_xticks(range(4),['Random\nnaive','Random\nCR2','Grouped\nnaive','Grouped\nCR2']);ax.set_title(f'K={K}, density=.5, γ=1, τ=1');ax.set_ylim(.5,1.01)
    axes[0].set_ylabel('Known-truth coverage with Wilson 95% interval');save(fig,'focal_coverage')
    fig,axes=plt.subplots(2,2,figsize=(9.4,6.5),layout='constrained')
    for i,K in enumerate([4,16]):
        for j,gamma in enumerate([0,1]):
            ax=axes[i,j]
            for cell,color,style in [('random_xfit__robust_var',BLUE,'-'),('grouped_xfit__robust_var',ORANGE,'--')]:
                rr=[next(r for r in rows if r['scenario']==f'main_K{K}_d{d}_g{gamma}_tau1' and r['cell']==cell) for d in [.25,.5,.75]]
                ax.errorbar([.25,.5,.75],[r['coverage95'] for r in rr],yerr=[[r['coverage95']-r['coverage_wilson95'][0] for r in rr],[r['coverage_wilson95'][1]-r['coverage95'] for r in rr]],fmt='o'+style,color=color,capsize=2,label='Grouped CR2' if 'grouped' in cell else 'Random CR2')
            ax.axhline(.95,color='#777777',ls=':',lw=1);ax.set_title(f'K={K}, γ={gamma}, τ=1');ax.set_xlabel('Configured density');ax.set_ylabel('Coverage');ax.set_ylim(.65,1.01);ax.legend(fontsize=8)
    save(fig,'full_primary_coverage')


if __name__=='__main__':
    real_figures();structure_figures();simulation_figures();print(OUT)
