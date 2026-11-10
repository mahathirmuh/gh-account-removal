"""Throwaway check: fixed-width ID blocks instead of chained ID links, plus within-cell ranking."""
import json
import pathlib

import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import average_precision_score, roc_auc_score
from sklearn.model_selection import StratifiedGroupKFold

SCRATCH = pathlib.Path('/tmp/claude-1002/-home-s2-giga-mahathir-trial-dm-git/0d31c0d6-85c4-4f38-98bc-11db18cfae9e/scratchpad')
d = np.load(SCRATCH / 'pilot_arrays.npz')
V, G, B, C, y, n_events, comp, ids = (d[k] for k in ['V', 'G', 'B', 'C', 'y', 'n_events', 'comp', 'ids'])
n = len(ids)
SEEDS = [42, 43, 44]
DROP_FINGERPRINT = list(range(16, 33)) + list(range(45, 48))  # temporal, repo, repo_names families


def merge(a, b):
    r, c = [], []
    for labels in (a, b):
        first = {}
        for k, g in enumerate(labels):
            if g in first:
                r.append(first[g]); c.append(k)
            else:
                first[g] = k
    return connected_components(coo_matrix((np.ones(len(r)), (r, c)), shape=(n, n)), directed=False)[1]


groupings = {'random': np.arange(n), 'G0_shared': comp}
for w in (1000, 5000, 20000):
    bins = (ids // w).astype(int)
    groupings[f'blocks_w{w}'] = bins
    groupings[f'G0+blocks_w{w}'] = merge(comp, bins)
for name, g in groupings.items():
    s = np.bincount(np.unique(g, return_inverse=True)[1])
    print(f'{name:18s} groups={len(s):5d} largest={np.sort(s)[::-1][:3].tolist()}')

age_edges = np.quantile(G[:, 0], np.linspace(0, 1, 13)[1:-1])
A12 = np.digitize(G[:, 0], age_edges).reshape(-1, 1).astype(float)
V2 = np.floor(np.log2(n_events)).reshape(-1, 1)
keep = [k for k in range(B.shape[1]) if k not in DROP_FINGERPRINT]
FEATS = {
    'rank_coarse_events': None,
    'coarse_events+age12': np.hstack([V2, A12]),
    '+behaviour_all48': np.hstack([V2, A12, B]),
    '+behaviour_robust28': np.hstack([V2, A12, B[:, keep]]),
    '+behaviour_all+coord': np.hstack([V2, A12, B, C]),
    '+behaviour_robust+coord': np.hstack([V2, A12, B[:, keep], C]),
}
masks = {'all>=5': n_events >= 5, '5-19': (n_events >= 5) & (n_events <= 19), '20+': n_events >= 20}


def oof(X, g):
    out = []
    for seed in SEEDS:
        p = np.zeros(n)
        for tr, te in StratifiedGroupKFold(n_splits=5, shuffle=True, random_state=seed).split(X, y, g):
            m = HistGradientBoostingClassifier(max_iter=200, learning_rate=0.05, max_leaf_nodes=7, l2_regularization=5.0,
                                               min_samples_leaf=30, early_stopping=False, random_state=seed)
            m.fit(X[tr], y[tr])
            p[te] = m.predict_proba(X[te])[:, 1]
        out.append(p)
    return np.mean(out, axis=0)


results = {}
print('\nAP all / 5-19 / 20+  (base %.3f / %.3f / %.3f)' % tuple(y[m].mean() for m in masks.values()))
names = list(groupings)
print(f"{'features':26s}" + ''.join(f'{g[:15]:>22s}' for g in names))
preds = {}
for fname, X in FEATS.items():
    cells = []
    for gname in names:
        g = groupings[gname]
        if X is None:
            p = V2.ravel().astype(float)
        else:
            p = oof(X, g)
        preds[(fname, gname)] = p
        vals = [float(average_precision_score(y[m], p[m])) for m in masks.values()]
        results.setdefault(fname, {})[gname] = vals
        cells.append('/'.join(f'{v:.3f}' for v in vals))
    print(f'{fname:26s}' + ''.join(f'{c:>22s}' for c in cells), flush=True)

cells = np.array([f'{int(a)}_{int(b)}' for a, b in zip(V2.ravel(), A12.ravel())])
print('\nWithin-cell ranking (cells = coarse events x age bin), AUC of model score inside each cell, weighted by positives')
print(f"{'features':26s}" + ''.join(f'{g[:15]:>22s}' for g in names))
for fname in FEATS:
    if FEATS[fname] is None:
        continue
    row = []
    for gname in names:
        p = preds[(fname, gname)]
        tot, wsum, used = 0.0, 0.0, 0
        for cell in np.unique(cells):
            mask = cells == cell
            pos = int(y[mask].sum())
            if 0 < pos < mask.sum():
                wsum += pos * roc_auc_score(y[mask], p[mask])
                tot += pos
                used += 1
        row.append(f'{wsum / tot:.3f} ({int(tot)}p/{used}c)')
        results.setdefault('within_cell_auc', {}).setdefault(fname, {})[gname] = wsum / tot
    print(f'{fname:26s}' + ''.join(f'{c:>22s}' for c in row), flush=True)

age_rate = [(int(b), int((A12.ravel() == b).sum()), float(y[A12.ravel() == b].mean())) for b in np.unique(A12)]
print('\nDisappearance rate by age bin (0 = oldest IDs, 11 = newest), n, rate')
for b, cnt, rate in age_rate:
    print(f'  bin {b:2d}  n={cnt:5d}  rate={rate:.3f}  min_id~{int(G[A12.ravel() == b, 0].min())}')
(SCRATCH / 'pilot_blocks_result.json').write_text(json.dumps(results, indent=1))
