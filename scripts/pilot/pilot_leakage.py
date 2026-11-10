"""Throwaway leakage stress test on the development hour, using cached labels and features."""
import collections
import json
import pathlib

import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import average_precision_score
from sklearn.model_selection import StratifiedGroupKFold

SCRATCH = pathlib.Path('/tmp/claude-1002/-home-s2-giga-mahathir-trial-dm-git/0d31c0d6-85c4-4f38-98bc-11db18cfae9e/scratchpad')
d = np.load(SCRATCH / 'pilot_arrays.npz')
V, G, B, C, y, n_events, comp, ids = (d[k] for k in ['V', 'G', 'B', 'C', 'y', 'n_events', 'comp', 'ids'])
n = len(ids)
SEED = 42
FAMILIES = {'type_mix': range(0, 16), 'temporal': range(16, 27), 'repo': range(27, 33), 'push': range(33, 37),
            'commit_msg': range(37, 41), 'create_pr': range(41, 45), 'repo_names': range(45, 48)}


def merge(base, links):
    r, c = [], []
    first = {}
    for k, g in enumerate(base):
        if g in first:
            r.append(first[g]); c.append(k)
        else:
            first[g] = k
    for a, b in links:
        r.append(a); c.append(b)
    return connected_components(coo_matrix((np.ones(len(r)), (r, c)), shape=(n, n)), directed=False)[1]


order = np.argsort(ids)
sorted_ids = ids[order]
gaps = np.diff(sorted_ids)
print('sample of id gaps (accounts >=5 events): median', int(np.median(gaps)), 'p10', int(np.percentile(gaps, 10)), 'p1', int(np.percentile(gaps, 1)))


def id_links(delta):
    return [(int(order[k]), int(order[k + 1])) for k in range(n - 1) if gaps[k] <= delta]


sig = collections.defaultdict(list)
repos = B[:, 27]
minutes = B[:, 16]
for k in range(n):
    if n_events[k] >= 10:
        sig[(int(n_events[k]), int(repos[k]), int(minutes[k]))].append(k)
sig_links = [(v[0], w) for v in sig.values() if len(v) > 1 for w in v[1:]]

groupings = {
    'G0_shared_repo_msg': comp,
    'G1_+id_gap<=1000': merge(comp, id_links(1000)),
    'G2_+id_gap<=5000': merge(comp, id_links(5000)),
    'G3_G2+signature': merge(comp, id_links(5000) + sig_links),
}
for name, g in groupings.items():
    s = np.bincount(g)
    pos_groups = np.bincount(g, weights=y)
    top = np.sort(pos_groups)[::-1]
    print(f"{name:22s} groups={len(s):5d} largest={np.sort(s)[::-1][:4].tolist()} accounts_in_multi={int(s[s > 1].sum()):5d} groups_with_pos={int((pos_groups > 0).sum()):4d} top5_share_of_pos={top[:5].sum() / y.sum():.3f}")

deciles = np.quantile(G[:, 0], np.linspace(0, 1, 13)[1:-1])
A1 = np.digitize(G[:, 0], deciles).reshape(-1, 1).astype(float)
V2 = np.floor(np.log2(n_events)).reshape(-1, 1)
FEATS = {
    'events': V,
    'events_coarse': V2,
    'events+id_raw': np.hstack([V, G]),
    'events+age12': np.hstack([V, A1]),
    'coarse_events+age12': np.hstack([V2, A1]),
    'events+id_raw+behav': np.hstack([V, G, B]),
    'events+age12+behav': np.hstack([V, A1, B]),
    'coarse_events+age12+behav': np.hstack([V2, A1, B]),
    'events+age12+behav+coord': np.hstack([V, A1, B, C]),
}
masks = {'all>=5': n_events >= 5, '5-19': (n_events >= 5) & (n_events <= 19), '20+': n_events >= 20}


def oof(X, g, seed=SEED):
    p = np.zeros(n)
    for tr, te in StratifiedGroupKFold(n_splits=5, shuffle=True, random_state=seed).split(X, y, g):
        m = HistGradientBoostingClassifier(max_iter=300, learning_rate=0.05, max_leaf_nodes=15, l2_regularization=1.0,
                                           min_samples_leaf=20, early_stopping=False, random_state=seed)
        m.fit(X[tr], y[tr])
        p[te] = m.predict_proba(X[te])[:, 1]
    return p


out = {}
print('\nAP (base all>=5 %.3f, 5-19 %.3f, 20+ %.3f)' % tuple(y[m].mean() for m in masks.values()))
header = f"{'features':28s}" + ''.join(f'{g[:10]:>26s}' for g in groupings)
print(header)
print(f"{'':28s}" + ''.join(f"{'all / 5-19 / 20+':>26s}" for _ in groupings))
for fname, X in FEATS.items():
    cells = []
    for gname, g in groupings.items():
        p = oof(X, g)
        vals = [average_precision_score(y[m], p[m]) for m in masks.values()]
        out.setdefault(fname, {})[gname] = vals
        cells.append(' / '.join(f'{v:.3f}' for v in vals))
    print(f'{fname:28s}' + ''.join(f'{c:>26s}' for c in cells), flush=True)

print('\nFamily ablation under G3, features events+age12+behav (drop one family at a time)')
g3 = groupings['G3_G2+signature']
base = np.hstack([V, A1, B])
full = oof(base, g3)
full_vals = [average_precision_score(y[m], full[m]) for m in masks.values()]
print(f"{'none dropped':14s}" + '  '.join(f'{v:.3f}' for v in full_vals))
for fam, idxs in FAMILIES.items():
    keep = [k for k in range(B.shape[1]) if k not in idxs]
    p = oof(np.hstack([V, A1, B[:, keep]]), g3)
    vals = [average_precision_score(y[m], p[m]) for m in masks.values()]
    print(f'{fam:14s}' + '  '.join(f'{v:.3f} ({v - b:+.3f})' for v, b in zip(vals, full_vals)), flush=True)
    only = oof(np.hstack([V, A1, B[:, list(idxs)]]), g3)
    only_vals = [average_precision_score(y[m], only[m]) for m in masks.values()]
    out.setdefault('family_only', {})[fam] = only_vals
    out.setdefault('family_drop', {})[fam] = vals
print('\nSingle-family models (events+age12+only that family) under G3')
for fam, vals in out['family_only'].items():
    print(f'{fam:14s}' + '  '.join(f'{v:.3f}' for v in vals))
(SCRATCH / 'pilot_leakage_result.json').write_text(json.dumps(out, indent=1))
