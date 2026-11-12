# Literature and attribution verification - 12 November 2026

Only primary papers, publisher records and author-maintained sources support the
technical references below. This is a scoped reference audit, not a systematic
review or novelty proof. No source code was copied from these papers.

| Reference | Verified identity and status | Relevance and limit |
|---|---|---|
| Chernozhukov et al. (2018), *Double/debiased machine learning for treatment and structural parameters* | Econometrics Journal 21(1), C1-C68; [DOI](https://doi.org/10.1111/ectj.12097) | Orthogonal scores and cross-fitting; not a guarantee for arbitrary dense dependence or our finite-sample variance. |
| Chiang, Kato, **Yukun Ma**, Sasaki (2022), *Multiway Cluster Robust Double/Debiased Machine Learning* | JBES 40(3),1046-1056; [publisher DOI](https://doi.org/10.1080/07350015.2021.1895815), [paper](https://arxiv.org/abs/1909.03489) | Specific multiway sampling assumptions. Our any-regime-sharing graph is not automatically covered by that theory. |
| Correction to Chiang et al. | JBES 39(4),1080 (2021); [publisher correction](https://doi.org/10.1080/07350015.2021.1970572) | Updated empirical Table 2 from corrected computer code. Do not cite the original table as unaffected; does not establish a theorem for our graph. |
| Salvador V. Balkus, Hasan Laith, Nima S. Hejazi (2026), *On the use of cross-fitting in causal machine learning with correlated units* | [arXiv:2601.10899v3](https://arxiv.org/abs/2601.10899v3), revised 29 July 2026; still listed under **Preprints** on the [author's site](https://salbalkus.github.io/papers.html) checked 12 November. [Author code](https://github.com/salbalkus/cross-fitting-dependent-data). | Distinguishes cross-fitting from predictive cross-validation; conditional rate/dependence arguments for bias and comparisons of precision. Does not make every covariance estimator valid or guarantee dense-regime coverage. Search snippets confusing the adjacent JRSS-B article were checked against the full author page; the JRSS-B article is a different work. |
| Paul Goldsmith-Pinkham, Tianshu Lyu (2025), *Causal Inference in Financial Event Studies* | [arXiv:2511.15123](https://arxiv.org/abs/2511.15123); working paper | Factor-model misspecification and synthetic controls motivate context; we did not execute their applications or establish SCM performance. |
| Kolari and Pynnonen (2010), *Event study testing with cross-sectional correlation of abnormal returns* | RFS23(11),3996-4025; [publisher](https://doi.org/10.1093/rfs/hhq072) | Classical cross-sectional-correlation issue; no DML finite-sample theorem follows. |
| Morris, White and Crowther (2019), *Using simulation studies to evaluate statistical methods* | Statistics in Medicine38(11),2074-2102; [full paper](https://pmc.ncbi.nlm.nih.gov/articles/PMC6492164/), doi10.1002/sim.8086 | ADEMP, MCSEs and missing estimates support transparent simulation reporting. Our paired MCSE is the sample-mean variance calculation. |
| Abadie, Diamond and Hainmueller (2010), *Synthetic Control Methods for Comparative Case Studies* | JASA105(490),493-505; [DOI](https://doi.org/10.1198/jasa.2009.ap08746) | Convex donor matching motivates the existing helper. Donor eligibility/data were not validated; SCM is NOT EXECUTED. |

The project implements and audits a bounded experimental comparison. It introduces
no new estimator or theorem, and does not claim the first study of dependent DML.
The report uses paper titles and author lists verified above. No claim is made
that a non-significant grouped/random contrast proves equivalence.
