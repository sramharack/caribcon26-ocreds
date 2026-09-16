#!/usr/bin/env python3
"""Case B check: rerun Jamaica with unconstrained, lossless transmission (copper plate)
to test whether the 4-bus network changes storage/BTM deployment."""
import os, sys, logging, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
logging.disable(logging.INFO)
from caribbean_dc_re import case_b, extract, storage_caps, RDIR
n = case_b()
tx = [l for l in n.links.index if l.startswith('tx_')]
n.links.loc[tx, 'p_nom'] = 1e5; n.links.loc[tx, 'efficiency'] = 1.0
n.optimize(solver_name='highs', solver_options={'time_limit': 300, 'output_flag': False})
r = extract(n, 'Case B: Jamaica (copper plate)'); r['storage_opt_vs_max'] = storage_caps(n)
print(r)
json.dump(r, open(os.path.join(RDIR, 'jamaica_copperplate.json'), 'w'), indent=2, default=str)
