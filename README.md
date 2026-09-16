# OCREDS: Optimal Co-location of Renewable Energy and Data Centers in Caribbean SIDS | IEEE CaribCon 2026

Code, results and manuscript for *"Optimal Co-location of Data Centers and Renewable Energy Systems in Caribbean SIDS: A PyPSA Framework with Multi-Criteria Siting Analysis."*

PyPSA capacity-expansion LP (2,190 h, Q1) for two cases:
- **Case A – Trinidad & Tobago**: single bus, 1,800 MW gas fleet, Brechin Castle 92 MWac PV, 5 MW DC at Point Lisas.
- **Case B – Jamaica**: 4-bus JPS 138 kV backbone (KGN–OH–MP–MB), 15 MW DC at Kingston.

The model also includes a post-hoc hurricane resilience stress test and a 10-factor siting score.

## Layout
```
src/caribbean_dc_re.py        main model: both cases, figures, DRO, results.json
src/sensitivity_trinidad.py   Case A one-at-a-time sensitivity (gas, CO2, solar CAPEX)
src/copperplate_jamaica.py    Case B with unconstrained lossless transmission
results/                      JSON/CSV outputs used in the paper
figures/                      generated figures (PNG + PDF)
paper/paper.tex               revised manuscript (paper_submitted.tex = original)
paper/apply_revisions.py      script that turns the submitted tex into the revision
docs/                         DRO parameter basis, siting rubric, reviewer response
legacy/                       exact v4 code + results as first submitted
```

## Reproduce
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cd src
python caribbean_dc_re.py          # ~80 s; Case A/B, figures, results/results.json
python sensitivity_trinidad.py     # ~1 min; results/sensitivity_trinidad.csv
python copperplate_jamaica.py      # ~60 s; results/jamaica_copperplate.json
cd ../paper && pdflatex paper.tex && pdflatex paper.tex
```
Tested with PyPSA 1.3.0 and HiGHS (highspy) on Python 3.12. Profiles are synthetic and seeded, so runs are deterministic.

## Headline results
| | Trinidad | Jamaica (4-bus) | Jamaica (copper plate) |
|---|---|---|---|
| Cost (M USD/yr) | 443 | 511 | 507 |
| RE share | 1.8% | 42.5% | 42.9% |
| New PV / wind (MW) | 0 / 0 | 405 / 278 | 400 / 281 |
| Grid BESS / BTM (MWh) | 0 / 0 | 800 / 84 | 800 / 84 |

For Trinidad, solar enters (300 MW, RE 7.5%) at gas ≥ $70/MWh, CO₂ ≥ $50/t, or solar CAPEX ≤ $800/kW. See `results/sensitivity_trinidad.csv`.

## Known limitations
Synthetic AR(1) profiles; Q1-only horizon; daily-average workload flexibility; illustrative hurricane parameters (see `docs/dro_parameters.md`); expert-scored siting prototype (`docs/siting_rubric.md`). Full discussion is in Section VII of the paper.


