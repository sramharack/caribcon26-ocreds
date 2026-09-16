#!/usr/bin/env python3
"""Case A (Trinidad) sensitivity: gas marginal cost, solar CAPEX, carbon price.
One-at-a-time sweeps around the base case (gas 55 $/MWh, solar 1100 $/kW, CO2 0).
Writes results/sensitivity_trinidad.csv"""
import os, sys, logging, pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
logging.disable(logging.INFO)
from caribbean_dc_re import case_a, extract, RDIR

RUNS = [('base', dict())]
RUNS += [(f'gas_{g}', dict(gas_mc=g)) for g in (45, 60, 65, 70, 85, 100)]
RUNS += [('solar_800', dict(solar_capex=800))]
RUNS += [(f'co2_{p}', dict(co2_price=p)) for p in (25, 50)]

rows = []
for tag, kw in RUNS:
    n = case_a(**kw)
    n.optimize(solver_name='highs', solver_options={'time_limit': 300, 'output_flag': False})
    r = extract(n, tag); r.update(kw); rows.append(r)
    print(f"{tag:<12} cost={r['cost']:.0f} RE={r['re_frac']:.1%} sol={r['sol_mw']:.0f} "
          f"wnd={r['wnd_mw']:.0f} bess={r['bess_mwh']:.0f} btm={r['btm_mwh']:.0f} co2={r['co2_kt']:.0f}", flush=True)
pd.DataFrame(rows).to_csv(os.path.join(RDIR, 'sensitivity_trinidad.csv'), index=False)
