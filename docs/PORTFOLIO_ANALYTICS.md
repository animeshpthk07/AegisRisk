# Portfolio concentration and loss contributions

AegisRisk groups the complete active fictional portfolio by industry, geography, rating band and borrower. The dashboard and structured JSON reports use the same server-side evidence. This is descriptive risk analysis, not an approval rule or validated regulatory capital model.

## Methodology

For facility i, EL_i = PD_i × LGD_i × EAD_i. The engine uses Decimal arithmetic before serializing numerical results. All accepted facilities use INR and a one-year horizon.

For a group g:

- Exposure = sum of EAD for its facilities.
- Expected loss = sum of facility EL, rather than multiplying independently averaged PD and LGD.
- Exposure share = group EAD / portfolio EAD.
- Loss share = group EL / portfolio EL.
- Exposure HHI = sum of squared group exposure shares, on the 0–1 scale.

Higher HHI indicates more concentration in that particular dimension. It is not a default probability, diversification guarantee or universal risk threshold. A single borrower can have several facilities; borrower grouping combines them. Rating bands are dataset labels, not external agency ratings.

A zero denominator produces null in the API and “Not defined” in the workbench. An empty portfolio has no groups or top contributors. Zero-exposure facilities are counted but contribute no exposure or loss. Group rows are sorted by label. Top facilities are ordered by expected loss descending, then facility ID ascending, and limited to ten. Their shares still use the entire portfolio denominator, so the displayed subset need not sum to 100%.

## Worked check

| Facility | Borrower | Industry | Geography | Rating | EAD | PD | LGD | EL |
| --- | --- | --- | --- | --- | ---: | ---: | ---: | ---: |
| SYN-A | Fictional A | Energy | West | A | 100 | 10% | 50% | 5 |
| SYN-B | Fictional A | Energy | East | B | 100 | 20% | 50% | 10 |
| SYN-C | Fictional B | Technology | East | C | 200 | 0% | 100% | 0 |

Total EAD is 400 and total EL is 15. Energy has 50% of exposure but 100% of expected loss. Industry and borrower HHI are 0.5; geography HHI is 0.625; rating HHI is 0.375. The expected-loss ranking is SYN-B, SYN-A, SYN-C. These are illustrative test inputs, not measured real-world banking results.

## Scope and review

The panel follows the active demo or saved snapshot. Changing the active portfolio resets grouping to industry. The facility search below the panel does not alter portfolio-wide calculations; this distinction is stated in the interface. Dedicated geographic/rating filters and borrower-detail analysis remain separate scope.

The browser checks group totals, shares, count conservation and HHI consistency before displaying this evidence. Missing or inconsistent evidence produces a clear panel error. This is a defensive presentation check; it does not substitute for backend validation or independent model validation.

The analytics object is additive in portfolio and structured baseline/scenario JSON evidence. Existing PDF and HTML report layouts do not yet render these new tables. Do not claim feature parity for those formats.

## Verification

Added numerical tests cover the worked example, group conservation, multiple facilities per borrower, reversed input order, zero loss, zero exposure, empty portfolios, deterministic ties and top-ten limits, plus API/JSON propagation.

Added browser checks cover all four groupings against API evidence, both themes at 1440px and 320px, keyboard grouping, page reflow, saved snapshot switching, undefined shares, rejected inconsistent evidence and recovery. Existing CI runs backend, frontend, three browser engines, security checks and the demo container. See the associated pull request for actual run outcomes; test definitions alone are not a passing result.

Hosting remains deferred by the owner. These additions do not complete the full product and career program.
