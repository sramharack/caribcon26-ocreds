# Response to Reviewer Comments – CaribCon 2026

We thank the reviewer for the positive assessment. Changes are listed below; section and table numbers refer to the revised manuscript.

**1. Robustness / sensitivity for Trinidad.**
We added one-at-a-time sensitivity runs on gas cost ($45–100/MWh), carbon price ($25, $50/tCO₂) and solar CAPEX ($800/kW). They are reported in the new Table IV and the "Robustness" paragraph of Section V.
- The zero-new-RE result holds up to a gas cost of $65/MWh.
- Solar (the full 300 MW candidate) enters between $65 and $70/MWh, at a carbon price between $25 and $50/t, or at $800/kW CAPEX.
- Uptake is limited (RE 7.5–9.9%, CO₂ −6 to −8%) by the candidate caps and the gas fleet's 25% minimum stable output.
- Cost figures include carbon payments where a carbon price applies.
- Code: `src/sensitivity_trinidad.py`.

**2. Empirical basis of hurricane parameters and ε.**
Section III-D was rewritten.
- It now states the exact computation (Eqs. 9–10) and makes clear that the adversarial tilt is a tractable surrogate, not an exact Wasserstein DRO solve.
- It gives the basis for each parameter: HURDAT2-consistent category shares, engineering-judgement outage depth and duration, a relative exposure multiplier, and ε as a sensitivity range aligned with IPCC AR6.
- It flags calibration to utility restoration records as future work.
- Details are in `docs/dro_parameters.md`.

**3. Siting score rationale.**
The framework is now explicitly described as an expert-elicited prototype. A new Table V gives the anchors for scores of 1 and 5 for each factor, along with the data sources behind the scores. Formal MCDA remains future work (Section VII-5). See `docs/siting_rubric.md`.

**4. Readability.**
We tightened the Discussion paragraphs ("Why this work matters", "Brechin Castle", "Societal factors"), the PyPSA justification and the Acknowledgments. The paper remains at 6 pages.

## Additional corrections found during revision (author-initiated)
- **Jamaica BTM driver.** The submitted text attributed BTM deployment to transmission congestion and claimed it would be invisible in a single-bus model. A copper-plate rerun (`src/copperplate_jamaica.py`) contradicts this: it deploys identical storage (800 MWh grid, 84 MWh BTM) at 0.8% lower cost. Congestion occurs on only 54 h (MP→OH) and 13 h (OH→KGN) out of 2,190 h. Grid and BTM storage both sit at their build limits. The Results, Discussion and Conclusion were corrected accordingly.
- **Solar deployment wording.** "Maxing May Pen and Old Harbour caps" was removed: 405 MW is below the 550 MW combined cap.
- **Jamaica resilience value.** R(ε=0.2) was corrected from 0.970 to 0.987, matching the code output. The "wind asset vulnerability" explanation was removed because wind assets are not modeled in the stress test.
- **DRO input consistency.** The Jamaica BTM input to the DRO was aligned with the modeled 84 MWh (previously 100). The effect is below 0.001 in R.
