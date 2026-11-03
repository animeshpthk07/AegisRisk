# AegisRisk learning curriculum and interview practice

A practical learning path for a B.Com Accounting & Finance student developing programming, analytics and banking-risk skills.

**Learning status: not assessed.** Saving this guide does not establish that the learner has completed the exercises or can explain the project independently. Record actual attempts and feedback below. AegisRisk uses fictional data; it is not a validated lending system, regulatory capital model or Deutsche Bank product. No bank endorsement is implied.

## Start with evidence and boundaries

At verified baseline [474866b](https://github.com/animeshpthk07/AegisRisk/commit/474866b05e99311224c6f9be84353ab4aeac3af8), the application includes deterministic expected loss, industry breakdowns, borrower concentration, custom stress multipliers, CSV/XLSX validation, optional snapshots, an isolated synthetic Model Lab and downloadable reports. Application verification [#170](https://github.com/animeshpthk07/AegisRisk/actions/runs/41634708166) and demo-container verification [#66](https://github.com/animeshpthk07/AegisRisk/actions/runs/41634708175) passed. This does not establish completion of the entire original brief.

Read [Model Lab](MODEL_LAB.md), [Architecture](ARCHITECTURE.md), [Contract](CONTRACT.md), [Release readiness](RELEASE_READINESS.md) and [Project presentation](PROJECT_PRESENTATION.md) before a demonstration. Verify later features against their own commits and checks.

- Portfolio calculations use supplied PDs; Model Lab does not replace them.
- Raw logistic contributions are not SHAP values, causal effects or calibrated-probability contributions.
- Synthetic scores are not evidence of accuracy on bank customers.
- Deterministic commentary does not establish external AI integration.
- A working container is not a public deployment. Hosting remains deferred by owner choice.

## Learning sequence

| Session | Focus | Evidence of understanding |
|---|---|---|
| 1 | Banking and credit risk | Explain a lending transaction and three risks |
| 2 | Credit mathematics | Independently recalculate the worked portfolio |
| 3 | Portfolio and stress analysis | Explain concentration and challenge a scenario assumption |
| 4 | Statistics and Model Lab | Explain discrimination, calibration and threshold errors |
| 5 | Architecture and reliability | Trace a request and explain a meaningful test |
| 6 | Project demonstration | Give a five-minute walkthrough with limitations |
| 7 | Interview practice | Answer unfamiliar follow-ups and record feedback |

These are sessions, not a promise of mastery in seven days. Repeat weak topics before advancing.

## 1. Banking context

Banks may accept deposits, lend, process payments and support investment activities; business models differ by institution and division. For a fictional equipment loan, distinguish:

- **Credit risk:** the borrower may fail to meet its obligations.
- **Market risk:** movements in market prices or rates may affect positions.
- **Operational risk:** failed processes, people, systems or external events may cause loss.
- **Counterparty risk:** the other party to a financial contract may fail to perform.
- **Liquidity risk:** obligations may become difficult to meet when due.

AegisRisk primarily demonstrates credit-portfolio analysis. Other categories are background knowledge, not implemented-model claims. Risk appetite concerns the types and amounts of risk an organization is willing to accept; an HHI calculation alone does not define it.

**Exercise:** Describe a fictional manufacturer borrowing for equipment. Identify information an analyst needs, two risk drivers and a limitation of historical ratios. Connect revenue, operating profit, cash flow, debt and interest expense. Explain how profit can rise while cash available for debt service falls.

## 2. Credit-risk mathematics

PD is a probability of default over a stated horizon. LGD is the assumed proportion of EAD lost conditional on default. EAD is the exposure assumed to exist at default. Educational formula: **EL = PD × LGD × EAD**. Use decimal probabilities: 2% = 0.02.

All figures below are illustrative, in INR, with the same one-year PD horizon.

| Facility | EAD | PD | LGD | EL |
|---|---:|---:|---:|---:|
| A | 100,000 | 2% | 40% | 800 |
| B | 300,000 | 6% | 50% | 9,000 |
| Portfolio | 400,000 | — | — | 9,800 |

A: 0.02 × 0.40 × 100,000 = 800. Portfolio EL is the sum of facility ELs. It is an expected value under the assumptions, not a prediction of precisely INR 9,800 of loss.

Exposure-weighted PD = (100,000 × 0.02 + 300,000 × 0.06) / 400,000 = **5%**.

Exposure-weighted LGD = (100,000 × 0.40 + 300,000 × 0.50) / 400,000 = **47.5%**.

**Do not multiply the two weighted averages to calculate portfolio EL.** That gives 0.05 × 0.475 × 400,000 = 9,500, not 9,800. Separate averages lose each facility's PD/LGD pairing.

Exercises:

1. Double A's EAD with unchanged PD/LGD. Answer: total EAD 500,000; EL 10,600; weighted PD 4.4%; weighted LGD 46%.
2. Explain zero PD, zero LGD and zero EAD cases. Each gives zero EL in this formula; that does not validate the assumption.
3. Explain why one-year and lifetime PDs cannot be mixed without explicit treatment.
4. Explain why INR and EUR exposures need a documented conversion method before aggregation.
5. Explain why EL is not unexpected loss, a capital requirement or a complete IFRS 9 calculation.

## 3. Concentration and stress

Aggregate facilities by borrower before calculating borrower exposure shares. If A and B belong to different borrowers, their shares are 25% and 75%:

**HHI = 0.25² + 0.75² = 0.625**, or 6,250 on the 0–10,000 convention. State the convention. If both facilities belong to one borrower, borrower HHI = 1 despite having two facilities.

HHI measures concentration, not PD. A concentrated portfolio is not automatically a high-default portfolio. Inspect industry and geography groupings separately; do not infer diversification solely from facility count.

Illustrative stress: PD × 1.5, LGD × 1.1, unchanged EAD.

| Facility | Stressed PD | Stressed LGD | Stressed EL |
|---|---:|---:|---:|
| A | 3% | 44% | 1,320 |
| B | 9% | 55% | 14,850 |
| Portfolio | — | — | 16,170 |

Absolute increase = 16,170 − 9,800 = **6,370**. Percentage increase = 6,370 / 9,800 = **65%**. These multipliers are assumptions, not a validated macroeconomic relationship. Apply probability/LGD bounds. When baseline EL is zero, percentage change is undefined; report absolute change.

**Exercise:** Explain what a sector shock should change, how unaffected sectors should behave and why preserving the baseline matters. Check current implementation before claiming named scenarios or segment-level outputs exist.

## 4. Statistics and explainable modeling

Logistic regression maps a linear score through a sigmoid to a probability. It is a useful interpretable baseline, not a substitute for validation.

Model Lab generates 3,000 fictional ratio profiles. Disjoint training/calibration/test splits contain 1,800/600/600 rows. Fit preprocessing and the model on training data, adjust probabilities on calibration data and evaluate the fixed procedure on the test data. Generated labels deliberately contain a learning signal; this is not external validation.

| Measure | Interpretation |
|---|---|
| ROC-AUC | Ranking discrimination across thresholds |
| Average precision | Precision–recall summary; consider event prevalence |
| Brier score | Mean squared error of predicted probabilities |
| Log loss | Penalizes incorrect probabilities, especially confident errors |
| Calibration | Agreement between predicted probabilities and observed frequencies |

High ROC-AUC does not imply good calibration. Calibration is measured, not guaranteed to improve the model. Average precision is the reported precision–recall summary; do not describe it as an identical numerical calculation to every PR-area convention.

Brier example: predictions [0.1,0.2,0.7,0.8], outcomes [0,1,1,0]. Score = (0.01 + 0.64 + 0.09 + 0.64) / 4 = **0.345**.

Threshold example: 100 cases, 10 simulated events; TP=6, FN=4, FP=9, TN=81.

- Precision = 6/15 = **40%**.
- Recall = 6/10 = **60%**.
- False-positive rate = 9/90 = **10%**.
- Accuracy = 87/100 = **87%**.

Predicting no event for everyone gives 90% accuracy while detecting no events. Lowering a threshold generally increases positive predictions, changing missed events and false alarms. Do not optimize on final test data and describe the resulting score as an untouched evaluation. Undefined denominators should be disclosed rather than replaced with misleading values.

Exercises: explain leakage, train-only scaling, calibration overfitting, temporal validation, distribution shift and why omitting protected attributes does not establish fairness. Distinguish predictive association from causation. Reconstruct a raw model score from its intercept and feature contributions; explain why those contributions do not sum to the calibrated probability.

## 5. Architecture and reliability

Trace browser input → validated API request → calculation → displayed result. Trace persistence separately: calculating does not necessarily save a dataset. Explain Next.js/React, FastAPI/Pydantic, SQLAlchemy/PostgreSQL and migrations using their roles in this flow.

Explain unit, integration and browser tests; type checking; Docker; continuous integration; upload bounds; secret handling; safe errors; and server authorization versus browser state cleanup.

Browser inactivity cleanup removes local credentials and displayed state in the supported mode. It is not identity-provider logout or server-side token revocation.

Distinguish restart persistence from backup recovery. The recovery check backs up fictional data, changes the source database, restores into a separate database and checks recovered evidence. The source change proves the result cannot simply be the unchanged source. This is not off-site recovery, production RPO/RTO or point-in-time recovery.

Exercises:

1. Pick one automated test: explain its inputs, assertion, the defect caught and a remaining blind spot.
2. Write an illustrative SQL aggregation: group fictional facilities by industry and sum EAD. Explain parameter binding for filters rather than concatenating user text into SQL.
3. Explain how a malicious or oversized XLSX differs from a normal spreadsheet, and why filename checking is insufficient.
4. Explain why a successful CI run cannot establish regulatory compliance or eliminate model risk.

## 6. Truthful project demonstration

Present yourself as a student, not an experienced banking-risk professional. A defensible introduction is: “I am a B.Com Accounting & Finance student developing practical analytics skills. I used AI assistance to build and review AegisRisk.” Follow with only the parts you can independently explain. Do not imply that you wrote every line unaided.

Five-minute walkthrough:

1. State the banking problem and fictional-data boundary.
2. Recalculate one facility's EL.
3. Explain concentration and a stress assumption.
4. Show model evidence and distinguish it from portfolio inputs.
5. Explain a meaningful test, your learning and an unresolved limitation.

Use [Project presentation](PROJECT_PRESENTATION.md) for shorter pitches. Never turn an illustrative number into a measured project achievement.

## 7. Interview questions and answer checkpoints

| Question | Strong answer includes |
|---|---|
| Why AegisRisk? | A specific learning objective and banking relevance |
| How does it differ from Finance Workbench? | Credit/portfolio risk versus financial operations/investigation |
| What are PD, LGD and EAD? | Units, horizon and conditional-loss meaning |
| Why sum facility ELs? | Aggregation and weighted-average counterexample |
| What does HHI tell you? | Grouping, scale, concentration; not default probability |
| What makes a stress scenario credible? | Transparent assumptions and limitations |
| Why logistic regression? | Reproducible interpretable baseline; limitations |
| How do you prevent leakage? | Split discipline, train-only preprocessing, no test tuning |
| Discrimination versus calibration? | Ranking versus probability reliability |
| Why not accuracy alone? | Class imbalance and error trade-offs |
| What do contributions explain? | Raw-score reconstruction; no causal claim |
| Why trust the calculations? | Independent arithmetic, edge cases, traceable assumptions |
| What does backup verification prove? | Actual recovery, source-change control, bounded scope |
| What would real bank data require? | Permission, governance, external/temporal validation, expert review |
| What did you personally learn? | A specific mistake, correction and reproducible explanation |
| Why Deutsche Bank and this role? | Verified role requirements, genuine motivation, honest eligibility |

Research an actual official vacancy before tailoring the last answer. Do not invent current programs, recruitment practices or eligibility. Prepare behavioral examples from real studies/projects: situation, task, action, result and learning. If you lack a relevant experience, say so and discuss your approach instead of inventing a story.

## Practice rubric and learning log

Score each answer 0–3: **0** incorrect/unsupported; **1** partial with important omissions; **2** correct with an example; **3** correct, independently worked and clear about limits. Maximum 48. Suggested learning target: at least 36, with no zero on PD/LGD/EAD, EL aggregation, leakage, explanation boundaries or real-data governance. This is not a hiring prediction.

Use follow-ups rather than memorized scripts: change a number, introduce missing data, challenge an assumption or trace an unfamiliar request. Revisit weak areas and record another actual attempt.

| Date | Exercise/question | Actual score/result | Specific gap | Next action | Recheck |
|---|---|---|---|---|---|
| Not attempted | — | Not assessed | — | Begin Session 1 | — |

No interview score, completed learning session or proficiency is recorded until the learner actually attempts it and receives feedback.
