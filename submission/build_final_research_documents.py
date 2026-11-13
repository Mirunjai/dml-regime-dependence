"""Populate the supplied one-pager and generate the final IEEE report source."""
from pathlib import Path
import json,shutil
from docx import Document
from docx.shared import Pt
from artifact_inputs import template

ROOT=Path(__file__).resolve().parents[1];BASE=ROOT/'results/raw/final_research_20261112'
DEST=BASE/'release_stage/ADA PROJECT DELIVERABLES'
facts=json.loads((BASE/'final_assets/facts.json').read_text());study=json.loads((BASE/'final_interpretation/interpretation.json').read_text())
by={(r['scenario'],r['cell']):r for r in study['summaries']}
doc=Document(template('DefaultCourseProject_OnePager.docx'))
text={0:'Team Name: Bullish Breakout',1:'Project Title:',2:'DML Confidence Intervals under Regime-Level Dependence',3:'Extension(s):',
4:'A registered 2 x 2 comparison of random/grouped cross-fitting and naive/CR2 inference. We validate established CR2/Satterthwaite algebra against R clubSandwich, independently audit every simulated interval, and evaluate explicitly matched dependence comparisons. No new estimator or theorem is claimed.',
5:'Possible Dataset(s) and Source(s):',
6:f"Synthetic: {facts['scenarios']} registered scenarios, {facts['complete_blocks']:,} complete four-cell blocks and {facts['interval_rows']:,} primary intervals. Real: six selected firms, 1,511 common trading dates (2016-2021), 9,066 returns and strictly prior VIX labels. Yahoo Finance acquisition records, SEC issuer crosswalk, derived returns and source hashes are in 03_Dataset.",
7:'Evaluation Criteria:',
8:'Known-truth 95% coverage is primary; null size is the key diagnostic. Report counts, MCSE, Wilson intervals, bias, width and paired comparisons. All 24 control cells pass the registered calibration/bias criteria. At K=4/16, robust random/grouped coverage is 91.2/90.6% and 94.6/94.0%; grouped folds add no material benefit under the prespecified rule.',
9:'Our Learning Goal:',
10:'Separate outcome dependence, score calibration and fold construction. Dense shared-pair counts scale approximately as n². The real panel has mean raw correlation .235 (calm) versus .476 (turbulent); the contrast attenuates after removing prior-estimated market exposure. Conclusions apply to the registered finite grid and selected descriptive sample; original historical archives remain unauthenticated.',11:'Reference Papers/Sources:'}
for i,t in text.items():doc.paragraphs[i].text=t
for section in doc.sections:
    for p in section.header.paragraphs:
        if 'Course Project One Pager' in p.text:
            p.runs[0].text='ADA Course Project One Pager: Finance Track'
            for r in p.runs[1:]:r.text=''
    for p in section.footer.paragraphs:
        if 'Machine Learning' in p.text:
            p.runs[0].text='Advanced Data Analytics | Project A'
            for r in p.runs[1:]:r.text=''
for row,member in zip(doc.tables[0].rows[1:],facts['members']):
    row.cells[0].text=member['name'];row.cells[1].text='';row.cells[2].text=member['SRN']
refs=[('Chernozhukov et al. (2018). Double/debiased machine learning.','doi.org/10.1111/ectj.12097'),('Pustejovsky & Tipton (2018). Small-sample cluster-robust inference.','doi.org/10.1080/07350015.2016.1247004'),('Morris, White & Crowther (2019). Evaluating statistical methods.','doi.org/10.1002/sim.8086')]
for row,(title,url) in zip(doc.tables[1].rows[1:],refs):row.cells[1].text=title;row.cells[2].text=url
for p in doc.paragraphs:
    p.paragraph_format.space_after=Pt(3);p.paragraph_format.space_before=Pt(0);p.paragraph_format.line_spacing=1
    for r in p.runs:r.font.name='Calibri';r.font.size=Pt(9.5)
for i in [0,1,3,5,7,9,11]:
    for r in doc.paragraphs[i].runs:r.bold=True;r.font.size=Pt(10)
for table in doc.tables:
    for row in table.rows:
        for cell in row.cells:
            for p in cell.paragraphs:
                p.paragraph_format.space_before=Pt(2);p.paragraph_format.space_after=Pt(2)
                for r in p.runs:r.font.name='Calibri';r.font.size=Pt(9)
doc.core_properties.title='ADA Final One Pager';doc.core_properties.author='; '.join(m['name'] for m in facts['members'])
doc.core_properties.subject='Registered finite-grid study; team: Bullish Breakout; no section'
doc.save(DEST/'01_One_Pager/ADA_Final_One_Pager.docx')

REPORT=DEST/'06_IEEE_Report';REPORT.mkdir(exist_ok=True)
shutil.copy2(template('IEEEtran.cls'),REPORT/'IEEEtran.cls')
for name in ['focal_coverage','structural_manipulation','real_correlation_contrast','aligned_regime_correlations']:
    shutil.copy2(BASE/'final_assets'/(name+'.pdf'),REPORT/(name+'.pdf'))
def pct(x):return f'{100*x:.1f}'
def table_rows():
    out=[]
    for K in [4,16]:
        for cell,label in [('random_xfit__naive_var','Random, naive'),('random_xfit__robust_var','Random, CR2'),('grouped_xfit__naive_var','Grouped, naive'),('grouped_xfit__robust_var','Grouped, CR2')]:
            r=by[f'main_K{K}_d0.5_g1_tau1',cell];null=by[f'main_K{K}_d0.5_g1_tau0',cell]
            out.append(f"{K} & {label} & {pct(r['coverage95'])} & {pct(null['empirical_size'])} & {r['mean_ci_width']:.2f} " + chr(92)*2)
    return '\n'.join(out)
tex=r'''\documentclass[conference]{IEEEtran}
\usepackage[T1]{fontenc}
\usepackage{amsmath,amssymb,graphicx,booktabs,url}
\usepackage[hidelinks]{hyperref}
\begin{document}
\title{DML Confidence Intervals under Regime-Level Dependence:\\A Reproducible Four-Cell Study}
\author{\IEEEauthorblockN{Deeptanshu Kumar, Mirunjai Suresh Kumar, Preksha K, Sudarshan G}
\IEEEauthorblockA{Advanced Data Analytics Course Project, PES University\\
PES1UG24AM357 \quad PES1UG24AM161 \quad PES1UG24AM907 \quad PES1UG24AM450}}
\maketitle
\begin{abstract}
We study whether regime-aware cross-fitting adds inferential benefit beyond robust variance in double machine learning (DML). A registered design crosses random/grouped folds with naive/component-CR2 inference in 78 scenarios and 43,200 complete four-cell simulation blocks. Independent auditing verifies all 172,800 primary intervals with no failures or missing cells. All 24 independent-control cells satisfy prespecified calibration and bias criteria. In the two focal known-effect conditions, robust random/grouped coverage is 91.2/90.6\% with four regimes and 94.6/94.0\% with sixteen. Naive intervals under-cover more strongly. Grouped folds show no material additional benefit under the registered paired criterion, while few-regime robust inference remains imperfect. Structural checks distinguish pair density from event exposure and validate two explicitly different H4 matches. A separate six-firm, 1,511-date panel shows higher raw-return correlation in turbulent periods, with substantial attenuation after prior-only market adjustment. The contribution is a source-pinned, independently checked application study using established methods, rather than a new estimator or universal validity theorem.
\end{abstract}
\begin{IEEEkeywords}
double machine learning, cross-fitting, clustered inference, Monte Carlo, regime dependence, financial event studies
\end{IEEEkeywords}

\section{Question and Research Context}
Financial events can share regime and calendar shocks. Cross-fitting protects held-out observations from direct nuisance-model reuse, but does not by itself validate an uncertainty formula under dependence. We ask whether dependence-robust variance is sufficient for calibrated DML intervals, or whether grouping cross-fitting folds by regime adds benefit. The locked comparison is a $2\times2$ design: random/grouped cross-fitting crossed with naive/robust variance. Coverage of nominal 95\% intervals is primary, and zero-effect rejection (empirical size) is the key diagnostic. A null or adverse grouping result is admissible.

Double/debiased machine learning combines orthogonal scores with nuisance estimation under explicit conditions \cite{dml}. Multiway cluster-robust DML addresses a specified multiway sampling structure \cite{multiway}; those assumptions do not automatically justify arbitrary overlapping regime graphs. Balkus, Laith and Hejazi study cross-fitting with correlated units under dependence and rate conditions \cite{correlated}. Small-sample cluster corrections provide a relevant established reference: bias-reduced linearization/CR2 and Satterthwaite pivots \cite{cr2,corrigendum}. The official \texttt{clubSandwich} implementation makes a useful external numerical benchmark \cite{clubsandwich}. Event-study research also emphasizes cross-sectional correlation in abnormal returns \cite{kolari}.

The applied gap addressed here is the joint finite-sample assessment of fold construction and covariance choice under a calendar-regime DGP, with realized dependence validation and complete paired raw evidence. We do not claim prior art overlooked grouped cross-fitting, invent a new CR2 formula, or establish a new asymptotic theorem. Simulation planning follows the aims, data-generating mechanisms, estimands, methods and performance measures (ADEMP) framework \cite{ademp}.

\section{Design and Methods}
\subsection{Calendar-regime data generation}
The primary world contains $n=400$ events, $T=260$ time points, $H=5$ event days and five independent Gaussian covariates. Named independent random streams generate covariates, event dates, own-firm volatility, factors, regime layout, regime shocks, regime treatment effects and Bernoulli treatment draws. The response is
\begin{equation}
\begin{split}
Y_i={}&g(X_i)+\beta_i\sum_{h=0}^{H-1}F_{t_i+h}+\sum_{h=0}^{H-1}U_{t_i+h}\\
&+\sum_{h=0}^{H-1}\sigma_{i,t_i+h}z_{i,t_i+h}+\tau D_i,
\end{split}
\end{equation}
where $g(X)=.5X_1+.3X_2^2+.2X_1X_3$ and $\beta_i=1+.3X_4$. Contiguous active regimes occupy calendar fraction $d\in\{.25,.5,.75\}$, with $K\in\{4,16\}$ and regime-shock standard deviation .4. Primary $F_t=0$ isolates regime dependence. A prespecified factor-on stress condition uses factor standard deviation .5, which introduces links not covered by regime-only covariance.

The idiosyncratic GARCH(1,1) recursion uses $h_{it}=.1+.1r_{i,t-1}^2+.8h_{i,t-1}$ and $r_{it}=\sqrt{h_{it}}z_{it}$, Gaussian innovations and 500 discarded burn-in steps. Its intended unconditional variance is one and its Gaussian fourth-moment factor is $.9^2+2(.1)^2=.83<1$. Common shocks and treatment never update $h$. The standalone component and historical candidate retain their documented draw-order distinction; we do not silently substitute their paths.

Treatment has logit $-.5+.5X_1+.3X_2+\gamma\bar v_i$, where $\bar v_i$ averages independent regime treatment effects over touched regimes and is zero for unexposed events. We report $\gamma=0$ and 1 separately. Treatment can share a regime effect while remaining independent of the regime outcome-shock draw. Each event's membership includes every regime touched by its window. Connected membership components define grouped folds and CR2 clusters; unexposed events are singleton components. Rare multiple membership does not imply sparse cross-event dependence.

\subsection{Held-out learning and the four cells}
The primary learner fits a degree-two polynomial Ridge outcome regression, with RidgeCV penalties $\{.1,1,10\}$, and standardized logistic treatment regression ($C=1$, maximum 1000 iterations). Both fitting and tuning stay inside each outer-training sample. No latent shocks, known treatment probability or true effect enter nuisance fitting. Five folds are primary. The prespecified second learner is the historical 40-tree random forest, minimum leaf size eight and feature fraction .5.

With held-out residuals $y_i,x_i$, set $J=\sum_i x_i^2$, $\hat\tau=\sum_i x_iy_i/J$, $e_i=y_i-x_i\hat\tau$ and $\psi_i=x_ie_i$. Naive HC0 variance is $\sum_i\psi_i^2/J^2$ with a normal pivot. For component $g$, write $h_g=\sum_{i\in g}x_i^2/J$ and $s_g=\sum_{i\in g}x_ie_i$. The scalar CR2 variance under identity working covariance is
\begin{equation}
\widehat V_{\mathrm{CR2}}=J^{-2}\sum_g\frac{s_g^2}{1-h_g}.
\end{equation}
Its Satterthwaite degrees of freedom use the adjusted, residualized cluster-direction Gram matrix $Q$:
\begin{equation}
Q_{gg}=h_g,\qquad Q_{gj}=\frac{-h_gh_j}{\sqrt{(1-h_g)(1-h_j)}},\quad
\nu=\frac{\operatorname{tr}(Q)^2}{\operatorname{tr}(Q^2)}.
\end{equation}
Intervals use $t_{.975,\nu}$. Undefined leverage, information or degrees of freedom produce retained failures, with no clipping or fallback. This algebra is an established scalar CR2 specialization, not a theorem that cross-fitted estimated scores automatically satisfy its assumptions. Independent connected components are the working dependence scope; calendar-factor stress violates that scope. The unchanged overlap-CR0/normal method remains a separately labelled reference on the same residuals.

\subsection{Registration, controls and uncertainty}
The producer source, numerical grid and budgets were frozen before final seeds. An analysis addendum fixed the focal comparison rule after launch but before any final estimates, summaries or logs were accessed; it did not change execution. Controls switch off regime shocks, common factors and regime treatment heterogeneity while retaining $K=0,4,16$ grouping/variance labels. Each control/effect condition has $R=2000$. Primary and H4 conditions have $R=500$; sample-size, persistence and fold sensitivities have $R=300$; learner and factor sensitivities have $R=500$. The 78 conditions total 43,200 scenario-replication blocks. Reused seeds couple conditions for paired comparisons and are never pooled as independent observations.

Every one of the 24 control cells must have its 90\% Wilson coverage interval entirely inside $[.925,.975]$, its null-size interval inside $[.025,.075]$ where applicable, absolute bias at most .1 empirical estimate SD, and zero missing/failures. These are finite-grid engineering acceptance criteria, not proof of exact nominal coverage. Reported per-cell uncertainty uses observed binomial MCSE and 95\% Wilson intervals. All four cells share a world fingerprint, and paired contrasts require complete blocks.

The two focal H3 conditions are $d=.5,\gamma=1,\tau=1$ at $K=4,16$. Material grouping benefit requires at least .02 improvement in absolute distance to .95 coverage, exact paired discordance-test Holm-adjusted $p<.05$ across these two conditions, and at most .01 worsening in absolute null-size distance to .05. Other grid contrasts are descriptive. Paired percentile intervals resample whole worlds, never cells independently.

\section{Simulation Results}
\subsection{Implementation and independent controls}
All 43,200 planned blocks and 172,800 primary intervals are present and successful. The independent auditor checks source fingerprints, configurations, seed addresses, record identities, interval arithmetic and raw known-truth metrics without importing the DGP or estimator. A fresh source-pinned Kaggle process exactly reproduces all scientific fields of 12 selected records at first/middle/last replication IDs. Against unmodified R \texttt{clubSandwich} 0.7.0, 60 comparisons across 20 fixtures agree to maximum absolute difference $1.96\times10^{-14}$.

All 24 control cells pass the registered criteria. Their coverage spans .944--.958; for example, $K=0,\tau=1$ random/grouped CR2 coverage is .952/.946, versus naive .951/.944. Thus foundational calibration passes for this registered design. These controls use a different primary learner and inferential variant from the preserved historical exploratory archive; they do not retroactively validate the old RF/CR0 results or recover missing original files.

\subsection{H1--H3: dependence, variance and grouping}
The structural manipulation increases independently measured shared-pair density and analytical average common-shock correlation at each $K$. At fixed $K$ and density .5, log--log shared-pair count slopes over $n=200,400,800,1600$ are 2.005 and 1.999, supporting dense $O(n^2)$ pair growth in this design (Fig.~\ref{fig:structure}).

For $\gamma=1,\tau=1$, increasing density .25 to .75 reduces random-naive coverage .858 to .622 at $K=4$, and .896 to .816 at $K=16$. This supports H1 within these conditions. The $\gamma=0$ rows do not show the same monotone deterioration, emphasizing that outcome dependence and orthogonal-score dependence are different.

\begin{table}[t]
\centering\caption{Focal coverage and corresponding null size, percent. $d=.5$, $\gamma=1$, $R=500$ per effect. Width is for $\tau=1$.}
\label{tab:focal}\small
\begin{tabular}{rlrrr}\toprule
$K$ & Cell & Coverage & Null size & Width\\\midrule
__FOCAL_ROWS__
\bottomrule\end{tabular}
\end{table}

CR2 improves coverage substantially over naive inference with each fold scheme fixed (Table~\ref{tab:focal}), supporting H2 in the focal cases. At $K=4$, random/grouped CR2 coverage remains .912/.906, below nominal .95; at $K=16$ it is .946/.940. Standard errors and finite-cluster pivots reduce but do not universally eliminate calibration error.

Grouped-minus-random robust coverage is $-.006$ in both focal conditions. Paired MCSE is .00872 and .00721, with 95\% paired percentile intervals $[-.022,.012]$ and $[-.020,.008]$. Exact unadjusted discordance-test $p$ values are .648 and .581, and both Holm-adjusted values are 1. Neither condition meets the registered material-benefit rule. This does not establish equivalence, and improved power or reduced width alone is not used to claim inferential benefit.

\begin{figure}[t]\centering\includegraphics[width=\columnwidth]{focal_coverage.pdf}
\caption{Known-effect focal coverage with 95\% Wilson intervals. The dashed line is nominal .95. These intervals describe Monte Carlo uncertainty of coverage, distinct from the parameter intervals being evaluated.}\label{fig:coverage}\end{figure}

\subsection{H4 and prespecified sensitivities}
The primary H4 match pairs $K=4,d=.31$ with $K=16,d=.5$ on unconditional shared-regime pair probability. Across 1000 independent structural seeds, K4-minus-K16 pair-density difference is $-.000142$ (MCSE .000155), within the registered .002 tolerance. Exposure differs by $-.376$, analytical average common-shock correlation by .00339 and average marginal error variance by $-.468$. These remain different covariance structures.

For $\gamma=1,\tau=1$, K16-minus-K4 coverage differences under this pair match are .010 (random CR2) and .012 (grouped CR2), with paired 95\% intervals $[-.014,.034]$ and $[-.016,.040]$. The secondary exposure match ($K4,d=.5$ versus $K16,d=.3$) has exposure gap .01332, within .02 tolerance, but pair-density gap .06163. Corresponding coverage contrasts are .018/.026, with intervals $[-.010,.048]$ and $[-.004,.056]$. H4 therefore has explicit, executed matched comparisons, but no claim that changing $K$ alone causes every difference.

\begin{figure}[t]\centering\includegraphics[width=\columnwidth]{structural_manipulation.pdf}
\caption{Independent membership-based validation, 1000 seeds per setting. Pair counts grow approximately quadratically; configured calendar fraction also raises analytical common-shock correlation.}\label{fig:structure}\end{figure}

The full release reports every sensitivity, including the historical RF learner, $n=800$, persistence .97, ten folds and factor standard deviation .5. At $\gamma=1,\tau=1$, RF random/grouped CR2 coverage is .908/.896 for $K=4$ and .938/.926 for $K=16$. The $n=800$ values are .930/.917 and .933/.930. At ten folds they are .930/.923 and .940/.950. These finite-grid descriptive changes do not justify selecting a new primary condition after inspection. Factor-on coverage is .930/.926 and .940/.930; these observations do not validate regime-only covariance for arbitrary calendar dependence. All $\gamma=0$, null-effect, width, bias, power and reference-CR0 rows remain available in the notebook and dataset tables.

\section{Daily Financial Panel and Event Context}
\subsection{Common window and prior-only labels}
We retain six selected firms (CRM, FAST, MHK, SWKS, ETSY, TER) over the registered common window 2016--2021. The panel contains 1511 common XNYS trading dates and 9066 valid adjacent-session adjusted-close simple returns, with zero missing panel returns. Six firms, seven historical event-study cases and the eight-event candidate roster are different quantities; no fixed requirement of seven price histories defines validity. The selected sample limits generalization, rather than preventing the implemented descriptive analysis.

Yahoo Finance acquisition uses explicit \texttt{auto\_adjust=False}, \texttt{repair=False} and adjusted-close extraction, with timestamps, versions and byte hashes retained. Missing prices are never filled or clipped. The VIX provider includes 204 missing holiday rows; every one is independently verified as a non-XNYS session before exclusion. No missing expected trading-session VIX value is skipped. Each date uses only the strictly earlier 20-observation VIX mean, classified against quartiles of earlier rolling means within its trailing five-calendar-year history. Equality is mixed. An independent calculation reproduces all labels, giving 332 calm, 669 mixed and 510 turbulent dates.

\subsection{Dependence and market adjustment}
All fifteen firm pairs exceed the registered 60-date minimum in both calm and turbulent states. Mean Pearson correlation is .2347 in calm periods and .4758 in turbulent periods, a difference .2411. The primary joint moving-calendar-block bootstrap (20 sessions, 2000 draws) gives a percentile 95\% interval $[.0907,.3563]$. Blocks resample the entire cross-firm vector and its label jointly. Ten- and forty-session sensitivities give $[.1122,.3515]$ and $[.0795,.3787]$. No independent-pair IID test is applied.

For market-residual sensitivity, each firm's market model fits at most 252 strictly earlier paired sessions against the actual S\&P 500 index return, requiring 200 observations. The raw and residual analyses use the same label definition. Residual mean correlations are .0627/.0829, difference .02024, with primary block interval $[-.0302,.0702]$. The residual sample has 332 calm and 491 turbulent dates because ETSY's early history is insufficient for some prior rolling fits. This attenuation suggests broad-market comovement explains much of the raw contrast in this selected sample; it is neither a causal decomposition nor proof that residual dependence is absent.

\begin{figure}[t]\centering\includegraphics[width=\columnwidth]{real_correlation_contrast.pdf}
\caption{Turbulent-minus-calm mean pairwise correlations. Joint block lengths 10, 20 and 40 preserve contemporaneous cross-firm observations and labels. Residual estimates use strictly prior market-model fits.}\label{fig:real}\end{figure}

\subsection{Fresh classical results and historical provenance}
A fresh seven-event market-model reconstruction uses the original day-zero conventions, estimation sessions $[-250,-31]$ (220 observations), and windows $[-1,1]$, $[0,1]$, $[-5,5]$. Its benchmark is the actual S\&P 500 index, not a substituted ETF. ADS history is reacquired under current ticker BFH after verifying the issuer crosswalk in an SEC filing \cite{sec}. The original CTLT missing-data case remains unfilled. Fresh primary CARs, in percent, are CRM 6.922, FAST 4.028, ADS 1.083, MHK .869, SWKS 3.976, ETSY $-2.402$ and TER $-4.730$. These are descriptive CARs, not estimated causal treatment effects or new coverage evidence.

The forensics search examines 84 available ZIP archives and Git path history without locating the missing original combined-price file or original missing replication archives. Comparing 42 printed historical CAR/model fields with fresh calculations gives small discrepancies, consistent with reconstruction but not authentication of the absent bytes or adjustment vintage. The final results therefore rest on the fresh, fully saved evidence. Synthetic Control is excluded by the final course plan and explicit user instruction, with no fabricated donor or effect results.

\section{Reproducibility and Conclusions}
The release includes raw simulation archives, frozen configurations, source snapshots, derived return/indicator CSVs, acquisition metadata, all-grid tables and an executable 48-stage notebook with explanatory Markdown. The complete local suite passes 439 tests. The notebook independently re-audits all intervals, replays an actual frozen world, recomputes the external-reference fixtures and daily labels, re-executes joint block-bootstrap analyses, and reconstructs the classical CARs. Exact notebook source/bundle digests and the matching fresh-kernel execution receipt accompany the code. Provider price-level histories remain separate from the distributed derived-data package.

Independent real-data verification makes 39,377 numerical comparisons (maximum absolute difference $2.33\times10^{-16}$), covering returns, direct prior-only OLS, an independently written joint-block bootstrap and classical CARs. A separate technical acceptance memo records the delegated review and release checks.

The completed registered study supports three bounded conclusions. First, dependency-aware uncertainty substantially improves focal coverage, although few-regime calibration remains imperfect. Second, grouped cross-fitting does not meet the prespecified material-benefit criterion beyond CR2 in the two focal comparisons. Third, the selected daily panel shows stronger raw comovement in turbulent periods, with pronounced attenuation after prior market adjustment. These conclusions are supported by complete, independently checked evidence within one DGP family and one selected real-data sample. Broader validity, fully matched covariance experiments and authentication of missing historical inputs remain research extensions rather than unperformed steps hidden inside the reported results.

\begin{thebibliography}{10}
\bibitem{dml} V. Chernozhukov et al., ``Double/debiased machine learning for treatment and structural parameters,'' \emph{Econometrics Journal}, vol. 21, pp. C1--C68, 2018, doi:10.1111/ectj.12097.
\bibitem{multiway} H. D. Chiang, K. Kato, Y. Ma and Y. Sasaki, ``Multiway cluster robust double/debiased machine learning,'' \emph{J. Bus. Econ. Stat.}, vol. 40, pp. 1046--1056, 2022, doi:10.1080/07350015.2021.1895815.
\bibitem{correlated} S. V. Balkus, H. Laith and N. S. Hejazi, ``On the use of cross-fitting in causal machine learning with correlated units,'' arXiv:2601.10899v3, 2026, preprint.
\bibitem{cr2} J. E. Pustejovsky and E. Tipton, ``Small-sample methods for cluster-robust variance estimation and hypothesis testing in fixed effects models,'' \emph{J. Bus. Econ. Stat.}, vol. 36, no. 4, pp. 672--683, 2018, doi:10.1080/07350015.2016.1247004.
\bibitem{corrigendum} J. E. Pustejovsky and E. Tipton, ``Corrigendum,'' \emph{J. Bus. Econ. Stat.}, 2023, doi:10.1080/07350015.2023.2174123.
\bibitem{clubsandwich} J. E. Pustejovsky, ``Cluster-robust standard errors and hypothesis tests in panel data models,'' \emph{clubSandwich documentation}, 2026. \url{https://jepusto.github.io/clubSandwich/articles/panel-data-CRVE.html}.
\bibitem{kolari} J. W. Kolari and S. Pynn\"onen, ``Event study testing with cross-sectional correlation of abnormal returns,'' \emph{Rev. Financ. Stud.}, vol. 23, pp. 3996--4025, 2010, doi:10.1093/rfs/hhq072.
\bibitem{ademp} T. P. Morris, I. R. White and M. J. Crowther, ``Using simulation studies to evaluate statistical methods,'' \emph{Stat. Med.}, vol. 38, pp. 2074--2102, 2019, doi:10.1002/sim.8086.
\bibitem{sec} Bread Financial Holdings, ``Form 8-K,'' Mar. 23, 2022, CIK 1101215. \url{https://www.sec.gov/Archives/edgar/data/1101215/000110121522000058/form_8-k.htm}.
\end{thebibliography}
\end{document}
'''.replace('__FOCAL_ROWS__',table_rows())
(REPORT/'ADA_IEEE_Report.tex').write_text(tex)
print('One-pager and IEEE report source:',DEST)
