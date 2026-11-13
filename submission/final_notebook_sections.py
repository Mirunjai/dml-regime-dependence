"""Granular research notebook: each stage explains the concept, calculation and purpose."""
import textwrap


def make_cells(bundle_sha):
    cells=[]
    def md(text):cells.append({'cell_type':'markdown','metadata':{},'id':f'm{len(cells):03d}','source':textwrap.dedent(text).strip()})
    def step(title,why,code):
        md(f'## {title}\n\n{why}')
        cells.append({'cell_type':'code','metadata':{},'id':f'c{len(cells):03d}','execution_count':None,'outputs':[], 'source':textwrap.dedent(code).strip()+'\n'})
    md('''# DML confidence intervals under regime-level dependence

**Advanced Data Analytics · Project A**

Team name: ____________________ · Section(s): ____________________

Deeptanshu Kumar (PES1UG24AM357), Mirunjai Suresh Kumar (PES1UG24AM161),
Preksha K (PES1UG24AM907), Sudarshan G (PES1UG24AM450).

We cross random/grouped cross-fitting with naive/CR2 uncertainty. Known-truth simulations evaluate coverage and null size; a separate six-firm panel describes observed dependence. The frozen final grid, historical reference and real-data illustration have different evidential roles. No new estimator or general theorem is claimed.

**Run all cells in order.** Attach the private Kaggle research bundle, or keep this notebook beside `../03_Dataset/source/notebook_bundle.zip`. The complete campaign is audited from saved raw records; selected actual components are re-executed. The 43,200-block campaign is not silently re-run inside this notebook.''')
    step('1. Environment and numerical conventions','Record the runtime before calculation. Returns use fractional units, and named RNG streams separate simulation components.', '''
        import os, sys, json, hashlib, zipfile, tempfile, io, itertools, math
        from pathlib import Path
        for name in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS'): os.environ[name]='1'
        import numpy as np
        import pandas as pd
        import matplotlib.pyplot as plt
        from IPython.display import display, Image
        from importlib.metadata import version
        versions={n:version(n) for n in ['numpy','scipy','scikit-learn','pandas','matplotlib']}
        print(sys.version); display(versions)
    ''')
    step('2. Locate and authenticate the immutable bundle','A SHA-256 digest identifies the exact input bytes. A successful older notebook run cannot validate a changed bundle.',f'''
        expected_sha={bundle_sha!r}
        candidates=[Path('../03_Dataset/source/notebook_bundle.zip'),Path('notebook_bundle.zip')]
        if Path('/kaggle/input').exists(): candidates+=list(Path('/kaggle/input').rglob('notebook_bundle.bin'))
        candidates=[p for p in candidates if p.is_file() and hashlib.sha256(p.read_bytes()).hexdigest()==expected_sha]
        assert candidates, 'Attach the matching final research bundle or use the packaged folder layout.'
        blob=candidates[0].read_bytes(); print('Authenticated bundle:',expected_sha,'bytes:',len(blob))
    ''')
    step('3. Extract into a clean workspace','Separate outputs from source evidence and reject paths that escape the temporary workspace.', '''
        workspace=Path(tempfile.mkdtemp(prefix='ada-final-reproduction-')).resolve()
        with zipfile.ZipFile(io.BytesIO(blob)) as archive:
            assert all((workspace/n).resolve().is_relative_to(workspace) for n in archive.namelist())
            archive.extractall(workspace)
        os.chdir(workspace);sys.path.insert(0,str(workspace))
        generated=workspace/'generated';generated.mkdir()
        frozen=workspace/'frozen';real=workspace/'real'
        print('Workspace ready; evidence inputs remain separate from generated outputs.')
    ''')
    step('4. Research aims and evidence map','The estimand is the known constant treatment effect in simulation. Unknown-truth financial data cannot establish confidence-interval coverage.', '''
        facts=json.loads((frozen/'facts.json').read_text())
        interpretation=json.loads((frozen/'interpretation.json').read_text())
        plan=json.loads(Path('configs/experiments/final-validation/final_design_20261112.json').read_text())
        display(pd.DataFrame([['Simulation','Known τ=0 or 1','Coverage, size, power'],['Six-firm panel','Observed daily dependence','Descriptive correlation contrasts'],['Historical results','Incomplete original archives','Fresh reconstruction, provenance check']],columns=['Evidence','Target','Interpretation']))
    ''')
    step('5. Frozen scenarios and replication budgets','The design fixes controls, primary conditions, H4 matching targets and sensitivities before final seeds. Common seeds across conditions do not create extra independent replications.', '''
        scenario_table=pd.DataFrame([{'scenario':s['id'],'role':s['role'],'R':s.get('replications',plan['replications']),'K':s['config']['n_regimes'],'density':s['config']['density'],'gamma':s['config']['gamma'],'tau':s['config']['tau'],'learner':s['learner']} for s in plan['scenarios']])
        assert len(scenario_table)==78 and scenario_table.R.sum()==43200
        display(scenario_table.groupby('role',sort=False).agg(scenarios=('scenario','count'),blocks=('R','sum')))
    ''')
    step('6. Producer provenance','Both cloud partitions must use the same frozen producer. This check distinguishes source identity from the independent arithmetic checks below.', '''
        producer=Path('producer_source.zip')
        assert hashlib.sha256(producer.read_bytes()).hexdigest()==facts['producer_source_zip_sha256']
        source_root=workspace/'frozen_producer';source_root.mkdir()
        with zipfile.ZipFile(producer) as z:z.extractall(source_root)
        display({'producer_sha256':facts['producer_source_zip_sha256'],'design_frozen_before_final_seeds':True})
    ''')
    step('7. Complete raw replication archives','Every saved world carries all four cells, seed addresses, configurations and world fingerprints. Failed attempts would remain in the denominator.', '''
        run_dirs=[]
        for kind in ['core','robustness']:
            p=Path('raw_archives')/(kind+'.zip'); assert hashlib.sha256(p.read_bytes()).hexdigest()==facts['campaign_archive_sha256'][kind]
            target=workspace/('raw_'+kind);target.mkdir()
            with zipfile.ZipFile(p) as z:z.extractall(target)
            run_dirs.append(target)
        print('Raw archives authenticated and extracted.')
    ''')
    step('8. Independent full-campaign audit','The auditor imports neither the DGP nor the estimator. It verifies planned identities, hashes, interval arithmetic, failure counts and known-truth metrics.', '''
        from scripts.audit_final_campaign import audit
        audited,interval_rows=audit('configs/experiments/final-validation/final_design_20261112.json',run_dirs,source_root)
        assert audited['saved_blocks']==audited['complete_blocks']==audited['planned_blocks']==43200
        assert audited['primary']['all_records_successful']
        intervals=pd.DataFrame(interval_rows)
        assert len(intervals)==172800
        display({k:audited[k] for k in ['planned_blocks','saved_blocks','complete_blocks']})
    ''')
    step('9. Reconcile frozen summaries','Recomputation must agree with the published audit, rather than simply displaying a saved PASS flag.', '''
        frozen_audit=json.loads((frozen/'campaign_audit.json').read_text())
        assert audited==frozen_audit
        summary=pd.DataFrame(interpretation['summaries'])
        display(summary[['scenario','cell','valid','failed','missing','coverage95','empirical_size','bias']].head(12))
    ''')
    step('10. Independent-control acceptance','The registered rule uses 90% Wilson intervals inside engineering calibration bands, zero missing/failures and a bias bound. Passing is scoped to this finite grid.', '''
        from scripts.summarize_final_campaign import wilson
        controls=pd.DataFrame(interpretation['control_cells'])
        for r in audited['primary']['summaries']:
            if r['role']=='independent_control':
                assert np.allclose(wilson(r['covered'],r['valid'],.9),controls.loc[(controls.scenario==r['scenario'])&(controls.cell==r['cell']),'coverage_wilson90'].iloc[0])
        assert controls.passed.all()
        display(controls[['scenario','cell','coverage','coverage_wilson90','bias_over_sd','passed']])
    ''')
    step('11. Control coverage and Monte Carlo precision','Wilson intervals quantify simulation uncertainty. They are different from each fitted parameter interval whose coverage is evaluated.', '''
        control=summary[summary.scenario=='control_K0_tau1']
        fig,ax=plt.subplots(figsize=(7,3))
        ax.bar(range(4),control.coverage95,color=['#245B87','#245B87','#BE5A36','#BE5A36'])
        ax.axhline(.95,color='black',linestyle='--');ax.set_ylim(.85,1);ax.set_ylabel('Coverage')
        ax.set_xticks(range(4),['Random naive','Random CR2','Grouped naive','Grouped CR2'],rotation=15)
        plt.show();print('R=2000 per control; nominal-.95 MCSE=',math.sqrt(.95*.05/2000))
    ''')
    step('12. Data-generating process and estimand','The primary scope isolates regime shocks by setting calendar-factor variance to zero. Factor-on conditions deliberately stress that covariance assumption.', '''
        from research.week2_completion.dgp import Config,build_world,STREAMS
        from research.final_validation.campaign import world_digest
        spec=next(s for s in plan['scenarios'] if s['id']=='main_K4_d0.5_g1_tau1')
        world=build_world(Config(**spec['config'],seed=spec['seed0']))
        display(spec);print('RNG streams:',STREAMS)
        print('X, D, Y shapes:',world['X'].shape,world['D'].shape,world['Y'].shape)
    ''')
    step('13. Actual GARCH component check','Firm volatility depends on its own lagged idiosyncratic return and variance. Common shocks and treatment stay outside this recursion.', '''
        from src.dgp.volatility import simulate_volatility
        own_sigma,own_innovations=simulate_volatility(32,200,.9,np.random.default_rng(20261113),arch_share=1/9,burn_in=500)
        assert own_sigma.shape==own_innovations.shape==(32,200) and np.isfinite(own_sigma).all() and (own_sigma>0).all()
        assert np.isfinite(world['sig']).all() and (world['sig']>0).all()
        print('Calendar candidate alpha=.1, beta=.8, omega=.1; E[h]=1; Gaussian fourth-moment factor=.83. Standalone draw order remains separate.')
        display(pd.Series(world['sig'].ravel()).describe(percentiles=[.01,.5,.99]))
    ''')
    step('14. Exposure and treatment diagnostics','Calendar density, exposed-event share and shared-regime pair probability measure different aspects of dependence. Treatment draws remain observed inputs; latent simulation truth stays outside fitting.', '''
        memberships=world['cluster_memberships']
        display({'treated_fraction':float(np.mean(world['D'])),'exposed_fraction':float(np.mean(world['exposed'])),
                 'multiple_membership_events':sum(len(m)>1 for m in memberships),
                 'configured_calendar_density':spec['config']['density']})
    ''')
    step('15. Connected components and grouped folds','Grouped folds keep connected regime components intact. Unexposed events form singleton components.', '''
        from research.week2_completion.dml import make_folds,audit_folds,_components
        fold=make_folds('grouped',memberships,spec['folds'],np.random.default_rng(spec['seed0']+1))
        component_ids=_components(memberships)
        assert all(len(set(fold[np.asarray(component_ids)==g]))==1 for g in set(component_ids))
        display(audit_folds(world,fold));display(pd.Series(fold).value_counts().sort_index())
    ''')
    step('16. Held-out nuisance fitting','Quadratic Ridge outcome regression and logistic treatment regression fit only outer-training observations. Ridge tuning also stays inside that training sample.', '''
        from research.final_validation.learners import residualize
        yt,dt=residualize(world,fold,spec['folds'],spec['seed0'],learner=spec['learner'])
        assert yt.shape==dt.shape==(400,) and np.isfinite(yt).all() and np.isfinite(dt).all()
        display(pd.DataFrame({'Y_residual':yt,'D_residual':dt}).describe())
    ''')
    step('17. Orthogonal-score estimate and naive variance','Residual-on-residual estimation gives the scalar PLR estimate. Naive HC0 treats score contributions as independent.', '''
        J=float(dt@dt);theta=float(dt@yt/J);score=dt*(yt-theta*dt)
        naive_se=float(np.sqrt(score@score)/J)
        display({'estimate':theta,'naive_se':naive_se,'naive_interval':[theta-1.959963984540054*naive_se,theta+1.959963984540054*naive_se]})
    ''')
    step('18. Component CR2 and Satterthwaite inference','CR2 corrects cluster leverage under an identity working covariance, then uses a Satterthwaite t pivot. It is established inference, not a new variance theorem.', '''
        from research.final_validation.inference import component_cr2
        corrected=component_cr2(yt,dt,memberships)
        assert np.isclose(corrected['estimate'],theta)
        display(corrected)
    ''')
    step('19. Actual frozen-world replay','Rebuild a registered world in this runtime and compare its scientific record. The separate cloud replay additionally checks 12 selected records in the original package versions.', '''
        old=json.loads((run_dirs[0]/spec['id']/'rep_000000.json').read_text())
        assert world_digest(world)==old['world_sha256']
        saved=next(c for c in old['cells'] if c['cell']=='grouped_xfit__robust_var')
        np.testing.assert_allclose([corrected[k] for k in ['estimate','se','df','lower','upper']],[saved[k] for k in ['estimate','se','df','lower','upper']],rtol=1e-8,atol=1e-10)
        replay=json.loads((frozen/'source_replay.json').read_text());assert replay['status']=='PASS' and len(replay['records'])==12
        display(replay)
    ''')
    step('20. External R reference verification','The independent R clubSandwich reference checks the CR2 algebra on 20 fixtures. This verifies numerical implementation, while simulation assesses calibration.', '''
        reference=json.loads((frozen/'R_reference_verification.json').read_text())
        expected=json.loads((frozen/'cr2_reference_expected.json').read_text())
        fixture=pd.read_csv(frozen/'cr2_reference_input.csv');R_reference=pd.read_csv(frozen/'clubSandwich_reference.csv').set_index('case')
        for case,data in fixture.groupby('case'):
            fit=component_cr2(data.y.to_numpy(),data.x.to_numpy(),[(int(g),) for g in data.cluster])
            np.testing.assert_allclose([fit[k] for k in ['estimate','se','df']],R_reference.loc[case,['estimate','se','df']],rtol=1e-11,atol=1e-12)
        display(reference);assert reference['status']=='PASS' and len(R_reference)==20
    ''')
    step('21. Primary four-cell results','Compare all four cells on the same simulated worlds. Better calibration means distance to nominal coverage decreases, rather than coverage merely increasing.', '''
        focal=summary[summary.scenario.isin(['main_K4_d0.5_g1_tau1','main_K16_d0.5_g1_tau1'])]
        display(focal[['scenario','cell','valid','coverage95','coverage_mcse','coverage_wilson95','mean_ci_width','power']])
    ''')
    step('22. Focal coverage figure','The two conditions were selected before final outcomes. Their Wilson intervals show the uncertainty of each estimated coverage rate.', '''
        display(Image(filename=str(Path('figures/focal_coverage.png'))))
    ''')
    step('23. Paired H3 comparison','An exact discordance test compares grouped and random robust coverage on paired worlds. Holm correction covers the two focal conditions; nonsignificance is not equivalence.', '''
        from scipy.stats import binomtest
        for r in interpretation['focal_H3']:
            n=r['discordant_grouped_only']+r['discordant_random_only']
            assert np.isclose(binomtest(r['discordant_grouped_only'],n,.5).pvalue,r['exact_p'])
        display(pd.json_normalize(interpretation['focal_H3']))
        assert not any(r['registered_material_benefit'] for r in interpretation['focal_H3'])
    ''')
    step('24. Full primary density grid','Report the entire registered primary grid, including conditions that look less favourable. Gamma separates regime-related treatment heterogeneity from outcome dependence alone.', '''
        display(Image(filename=str(Path('figures/full_primary_coverage.png'))))
        display(summary[(summary.role=='primary')&(summary.truth==1)][['scenario','cell','coverage95','coverage_mcse']])
    ''')
    step('25. Null size','When the true effect is zero, rejection estimates type-I error. High power or narrow intervals cannot compensate for miscalibrated null size.', '''
        null=summary[(summary.role=='primary')&(summary.truth==0)]
        display(null[['scenario','cell','empirical_size','size_mcse','rejection_wilson95']])
    ''')
    step('26. Width, bias and power','These secondary measures describe the calibration–precision tradeoff. They do not replace the primary coverage and null-size endpoints.', '''
        display(focal[['scenario','cell','bias','estimate_sd','rmse','mean_ci_width','power','power_mcse']])
    ''')
    step('27. Structural manipulation validation','Shared-regime pair counts can grow quadratically even with rare multiple membership. Outcome dependence and orthogonal-score dependence are distinct quantities.', '''
        structure=json.loads((frozen/'structure.json').read_text())
        display(interpretation['structural_scaling_slopes']);display(Image(filename=str(Path('figures/structural_manipulation.png'))))
        assert all(1.8<v<2.2 for v in interpretation['structural_scaling_slopes'].values())
        assert all(interpretation['density_ordering_passed'].values())
    ''')
    step('28. H4 matching targets','The primary match equalizes unconditional shared-pair probability within tolerance. The secondary match approximately equalizes exposure; neither matches the full covariance matrix.', '''
        display(pd.json_normalize(structure['matches']))
        assert abs(structure['matches'][0]['paired_differences']['pair_density']['mean'])<=.002
        assert abs(structure['matches'][1]['paired_differences']['exposed_share']['mean'])<=.02
    ''')
    step('29. H4 coverage contrasts','Paired K16-minus-K4 contrasts retain uncertainty and report which quantity was matched. An interval crossing zero does not prove equality.', '''
        h4=pd.json_normalize(interpretation['H4'])
        display(h4[(h4.gamma==1)&(h4.tau==1)])
    ''')
    step('30. Learner sensitivity','The legacy random forest is a prespecified second learner. Its outputs remain visible rather than selecting the best learner after final outcomes.', '''
        display(summary[(summary.role=='robustness_rf40')&(summary.truth==1)][['scenario','cell','coverage95','coverage_mcse','bias']])
    ''')
    step('31. Sample size and persistence sensitivities','Larger n and stronger GARCH persistence check whether the main comparison changes under planned perturbations.', '''
        display(summary[summary.role.isin(['robustness_n800','robustness_rho097'])&(summary.truth==1)][['scenario','cell','valid','coverage95','coverage_mcse']])
    ''')
    step('32. Fold sensitivity','Ten-fold results test sensitivity to fold count without changing the score or inference rule.', '''
        display(summary[(summary.role=='robustness_fold10')&(summary.truth==1)][['scenario','cell','coverage95','coverage_mcse','mean_ci_width']])
    ''')
    step('33. Calendar-factor stress test','Regime-only covariance does not account for common calendar factors linking different components. This deliberately misspecified stress condition stays separate from the primary scope.', '''
        display(summary[(summary.role=='stress_outside_regime_covariance')&(summary.truth==1)][['scenario','cell','coverage95','coverage_mcse','bias']])
    ''')
    step('34. Load the common daily panel','The selected six firms share a fixed 2016–2021 window. Every return is an adjacent-session adjusted-close simple return; observations are never filled or clipped.', '''
        panel=pd.read_csv(real/'aligned_returns.csv',index_col='date',parse_dates=True)
        real_audit=json.loads((frozen/'real_audit.json').read_text());firms=real_audit['firms']
        assert panel.shape==(1511,7) and panel[firms].notna().all().all() and panel.index.is_unique
        display({'first':str(panel.index.min().date()),'last':str(panel.index.max().date()),'firm_returns':int(panel[firms].size)})
        display(panel.head())
    ''')
    step('35. Regime labels and information cutoff','Labels use the strictly prior 20-observation VIX mean and earlier five-year quartiles. Equality is mixed, and the same calendar labels apply to all firms.', '''
        labels=pd.read_csv(real/'daily_labels_and_thresholds.csv',parse_dates=['date'])
        derived_history=pd.read_csv(real/'derived_vix20_history.csv',parse_dates=['date','window_first_date'])
        for r in labels.itertuples():
            h=derived_history[(derived_history.date<r.date)&(derived_history.window_first_date>=r.date-pd.DateOffset(years=5))]
            low,high=np.quantile(h.vix20.iloc[:-1],[.25,.75]);latest=h.vix20.iloc[-1]
            state='calm' if latest<low else 'turbulent' if latest>high else 'mixed'
            assert state==r.regime_label and np.allclose([latest,low,high],[r.pre_event_vix20,r.vix_p25,r.vix_p75])
        display(panel.regime_label.value_counts())
    ''')
    step('36. Daily regime timeline','Plot the lagged volatility indicator and historical thresholds. The classification at a date contains no later VIX observations.', '''
        display(Image(filename=str(Path('figures/daily_regime_timeline.png'))))
    ''')
    step('37. All fifteen firm pairs','Contemporaneous Pearson and Spearman correlations use aligned observations within each label. The minimum required sample is 60 sessions per pair and label.', '''
        from src.real_data.aligned_panel import pair_statistics,mean_pair_correlation,block_bootstrap
        state=panel.regime_label
        pairs=pd.DataFrame(pair_statistics(panel[firms],state,minimum=60))
        assert len(pairs)==45 and pairs.status.eq('descriptive').all()
        display(pairs);display(Image(filename=str(Path('figures/aligned_regime_correlations.png'))))
    ''')
    step('38. Mean raw-return correlation contrast','Average the same fifteen correlations in both conditions. This selected-sample descriptive contrast does not identify a causal regime effect.', '''
        observed=mean_pair_correlation(panel[firms].to_numpy(),state.to_numpy())
        np.testing.assert_allclose([observed[k] for k in ['calm','turbulent','difference']],[.2347449683835411,.4758355864916295,.24109061810808838])
        display(observed)
    ''')
    step('39. Joint calendar-block uncertainty','Resample contiguous dates jointly across firms and labels. Independent-firm resampling would destroy the contemporaneous dependence being studied.', '''
        raw_boot=block_bootstrap(panel[firms],state,length=20,replications=2000,seed=2026111221)
        frozen_boot=real_audit['block_bootstrap']['raw_returns'][0]
        np.testing.assert_allclose(raw_boot['percentile95'],frozen_boot['percentile95'],atol=1e-12)
        assert raw_boot['valid']==2000 and raw_boot['failed']==0
        display(raw_boot)
    ''')
    step('40. Prior-only market residuals','Each rolling market model fits at most 252 strictly earlier sessions, with at least 200 paired observations. Residual dependence tests how much the common market explains.', '''
        from src.real_data.aligned_panel import prior_market_residuals
        full=pd.read_csv(real/'derived_returns_full.csv',index_col='date',parse_dates=True)
        residuals=prior_market_residuals(full[firms],full['^GSPC']).loc[panel.index]
        saved_residuals=pd.read_csv(real/'prior_market_residuals.csv',index_col='date',parse_dates=True)
        np.testing.assert_allclose(residuals,saved_residuals[firms],equal_nan=True,atol=1e-12)
        display(mean_pair_correlation(residuals.to_numpy(),state.to_numpy()))
    ''')
    step('41. Residual contrast and block-length sensitivity','The same block method assesses residual correlations; 10- and 40-session blocks are prespecified sensitivity checks. A residual interval spanning zero limits the interpretation.', '''
        residual_boot=block_bootstrap(residuals,state,length=20,replications=2000,seed=2026111221)
        np.testing.assert_allclose(residual_boot['percentile95'],real_audit['block_bootstrap']['prior_market_residuals'][0]['percentile95'],atol=1e-12)
        for data,kind in [(panel[firms],'raw_returns'),(residuals,'prior_market_residuals')]:
            for length in [10,40]:
                boot=block_bootstrap(data,state,length=length,replications=1000,seed=2026111201+length)
                target=next(v for v in real_audit['block_bootstrap'][kind] if v['block_length']==length)
                np.testing.assert_allclose(boot['percentile95'],target['percentile95'],atol=1e-12)
        display(residual_boot);display(Image(filename=str(Path('figures/real_correlation_contrast.png'))))
    ''')
    step('42. Rank-correlation sensitivity','Spearman correlation checks dependence in ranks rather than raw return magnitudes. It is supplementary, with no independent-pair p-values.', '''
        ranks=pairs.groupby('label')[['pearson','spearman']].mean()
        residual_pairs=pd.DataFrame(pair_statistics(residuals,state,minimum=60))
        display(ranks);display(residual_pairs.groupby('label')[['pearson','spearman']].mean())
    ''')
    step('43. Fresh classical event-study execution','Fit the market model on sessions [−250, −31] and sum abnormal returns over [−1, +1], [0, +1] and [−5, +5]. These seven event cases differ from the six-firm common panel.', '''
        event_returns=pd.read_csv(real/'reacquired_event_returns.csv',index_col='date',parse_dates=True)
        cars=pd.read_csv(real/'fresh_classical_event_study.csv')
        for r in cars.itertuples():
            k=event_returns.index.get_loc(pd.Timestamp(r.event_day_zero));prior=event_returns.iloc[k-250:k-30]
            ab=np.linalg.lstsq(np.column_stack([np.ones(220),prior['^GSPC']]),prior[r.ticker],rcond=None)[0]
            for name,lo,hi in [('primary',-1,1),('short',0,1),('wide',-5,5)]:
                w=event_returns.iloc[k+lo:k+hi+1]
                assert np.isclose((w[r.ticker]-ab[0]-ab[1]*w['^GSPC']).sum(),getattr(r,'car_'+name),atol=1e-12)
        display(cars);display(Image(filename=str(Path('figures/fresh_classical_cars.png'))))
    ''')
    step('44. Security identity and historical provenance','SEC filings establish the ADS-to-BFH issuer/ticker change. A fresh adjusted history can support a new calculation but cannot authenticate a missing original file.', '''
        display(real_audit['ADS_identity'])
        comparison=pd.read_csv(real/'legacy_classical_comparison.csv')
        display(comparison.groupby('field').difference.agg(['min','max']))
        assert len(comparison)==42 and real_audit['original_missing_inputs_authenticated'] is False
        print('CTLT has no substituted observations. Synthetic Control is outside the submitted scope.')
    ''')
    step('45. Independent real-panel verification record','A separate implementation checks returns, direct prior-only OLS, calendar-block resampling and CARs. This complements, rather than replaces, source provenance.', '''
        independent_real=json.loads((frozen/'real_independent_audit.json').read_text())
        assert independent_real['passed'] and independent_real['numeric_comparisons']==39377
        display({k:independent_real[k] for k in ['passed','numeric_comparisons','maximum_absolute_difference','panel_dates']})
    ''')
    step('46. Regenerate publication figures and export tables','Rebuild the scientific figures from authenticated, independently checked evidence, then export the recomputed tables separately from frozen inputs.', '''
        import shutil
        from submission import final_figures as figures
        figure_inputs=generated/'figure_inputs'
        for name in ['real_analysis_v3','structure','final_interpretation']: (figure_inputs/name).mkdir(parents=True,exist_ok=True)
        for p in real.glob('*.csv'): shutil.copy2(p,figure_inputs/'real_analysis_v3'/p.name)
        for name,destination in [('real_audit.json','real_analysis_v3/audit.json'),('structure.json','structure/structure.json'),('interpretation.json','final_interpretation/interpretation.json')]: shutil.copy2(frozen/name,figure_inputs/destination)
        figures.BASE=figure_inputs;figures.OUT=generated/'figures';figures.OUT.mkdir()
        figures.real_figures();figures.structure_figures();figures.simulation_figures()
        assert len(list(figures.OUT.glob('*.png')))==7 and len(list(figures.OUT.glob('*.pdf')))==7
        summary.to_csv(generated/'simulation_summary.csv',index=False)
        pairs.to_csv(generated/'raw_pair_correlations.csv',index=False)
        residual_pairs.to_csv(generated/'residual_pair_correlations.csv',index=False)
        cars.to_csv(generated/'fresh_classical_event_study.csv',index=False)
        (generated/'campaign_audit.json').write_text(json.dumps(audited,indent=2))
        print('Generated tables:',[p.name for p in generated.iterdir()])
    ''')
    step('47. Interpretation and bounded conclusions','All registered controls pass. CR2 improves focal coverage, while grouped cross-fitting provides no material additional benefit under the registered rule. Few-regime and covariance assumptions still constrain generalization.', '''
        display({'controls_passed':interpretation['controls_all_passed'],
                 'H3_material_benefit':[r['registered_material_benefit'] for r in interpretation['focal_H3']],
                 'raw_correlation_difference':raw_boot['observed']['difference'],
                 'market_residual_difference':residual_boot['observed']['difference']})
        print('Nonsignificance is not equivalence. Real-data contrasts are descriptive. Historical originals remain unauthenticated.')
    ''')
    step('48. Reproducibility receipt','The clean-run wrapper records this notebook’s semantic source digest separately. This receipt records the exact bundle, recomputed counts and runtime versions.', '''
        receipt={'status':'PASS','bundle_sha256':expected_sha,'planned_blocks':audited['planned_blocks'],
                 'complete_blocks':audited['complete_blocks'],'interval_rows':len(intervals),
                 'controls_passed':bool(controls.passed.all()),'panel_dates':len(panel),
                 'real_bootstrap_reexecuted':True,'selected_actual_world_reexecuted':True,'publication_figures_regenerated':7,'versions':versions}
        (generated/'reproduction.json').write_text(json.dumps(receipt,indent=2))
        display(receipt)
    ''')
    md('''## References and project scope

Chernozhukov et al. (2018), *Double/debiased machine learning*, [doi:10.1111/ectj.12097](https://doi.org/10.1111/ectj.12097).
Pustejovsky & Tipton (2018), *Small-Sample Methods for Cluster-Robust Variance Estimation and Hypothesis Testing in Fixed Effects Models*, [doi:10.1080/07350015.2016.1247004](https://doi.org/10.1080/07350015.2016.1247004), with [2023 corrigendum](https://doi.org/10.1080/07350015.2023.2174123).
The [official clubSandwich documentation](https://jepusto.github.io/clubSandwich/articles/panel-data-CRVE.html) explains the established CR2/Satterthwaite method. Morris, White & Crowther (2019), [doi:10.1002/sim.8086](https://doi.org/10.1002/sim.8086), motivates explicit simulation aims, data generation, estimands, methods and performance measures.

No new estimator or theorem is claimed. Final analysis decisions and technical acceptance were delegated by Deeptanshu Kumar; no teammate signatures or mentor approval are fabricated. Video, Drive/Form submission and team-name/section entry are handled separately by the team. Synthetic Control is excluded by instruction.''')
    return cells
