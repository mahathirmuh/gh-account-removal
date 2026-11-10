"""Exploratory check on the development hour: do ID-neighbourhood co-activity features add signal?

Features use only the public event stream and no labels. Neighbours are other accounts active in the same
hour whose numeric IDs are within +-W. Aggregates only. Splits avoid chained groups, which collapse into one
giant fold.
"""
import json
import pathlib

import numpy as np
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import average_precision_score, roc_auc_score
from sklearn.model_selection import StratifiedGroupKFold

SCRATCH = pathlib.Path('/tmp/claude-1002/-home-s2-giga-mahathir-trial-dm-git/0d31c0d6-85c4-4f38-98bc-11db18cfae9e/scratchpad')
DATA = '/home/s2_giga/mahathir/trial/dm-git/2024-04-01-15.json/2024-04-01-15.json'
d = np.load(SCRATCH / 'pilot_arrays.npz')
G, B, y, n_events, ids = (d[k] for k in ['G', 'B', 'y', 'n_events', 'ids'])
n = len(ids)
SEEDS = [42, 43, 44]
WIDTHS = [100, 1000, 5000]

# every account active in the hour, including those below the cohort threshold
count = {}
with open(DATA, 'rb') as f:
    for line in f:
        a = json.loads(line)['actor']
        if not a['login'].endswith('[bot]'):
            count[a['id']] = count.get(a['id'], 0) + 1
all_ids = np.array(sorted(count))
all_cnt = np.array([count[i] for i in all_ids], float)
prefix = np.concatenate([[0.0], np.cumsum(np.log1p(all_cnt))])
prefix5 = np.concatenate([[0.0], np.cumsum(all_cnt >= 5)])
print('active non-bot accounts', len(all_ids))


def neighbour_features(i):
    out = []
    for w in WIDTHS:
        lo, hi = np.searchsorted(all_ids, i - w, 'left'), np.searchsorted(all_ids, i + w, 'right')
        others = hi - lo - 1
        own = np.log1p(count[int(i)])
        mean_activity = (prefix[hi] - prefix[lo] - own) / others if others else 0.0
        busy = prefix5[hi] - prefix5[lo] - (count[int(i)] >= 5)
        out += [others, mean_activity, busy]
    return out


N = np.array([neighbour_features(i) for i in ids], float)
age_edges = np.quantile(G[:, 0], np.linspace(0, 1, 13)[1:-1])
A12 = np.digitize(G[:, 0], age_edges).reshape(-1, 1).astype(float)
V2 = np.floor(np.log2(n_events)).reshape(-1, 1)
FEATS = {
    'baseline: coarse events + age12': np.hstack([V2, A12]),
    'baseline + ID-neighbour': np.hstack([V2, A12, N]),
    'baseline + behaviour48': np.hstack([V2, A12, B]),
    'baseline + behaviour48 + ID-neighbour': np.hstack([V2, A12, B, N]),
}
groupings = {'random': np.arange(n), 'blocks_w5000': (ids // 5000).astype(int), 'blocks_w20000': (ids // 20000).astype(int),
             'blocks_w100000': (ids // 100000).astype(int)}
for name, g in groupings.items():
    u, inv = np.unique(g, return_inverse=True)
    sz, pos = np.bincount(inv), np.bincount(inv, weights=y)
    print(f'{name:16s} groups={len(u):5d} largest={int(sz.max()):4d} max positives in one group={int(pos.max()):3d}')
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


cells = np.array([f'{int(a)}_{int(b)}' for a, b in zip(V2.ravel(), A12.ravel())])


def within_cell(p):
    tot, wsum = 0.0, 0.0
    for cell in np.unique(cells):
        mask = cells == cell
        pos = int(y[mask].sum())
        if 0 < pos < mask.sum():
            wsum += pos * roc_auc_score(y[mask], p[mask])
            tot += pos
    return wsum / tot


print('\nAP all / 5-19 / 20+ ; within-cell AUC')
results = {}
for fname, X in FEATS.items():
    for gname, g in groupings.items():
        p = oof(X, g)
        vals = [float(average_precision_score(y[m], p[m])) for m in masks.values()]
        wc = float(within_cell(p))
        results.setdefault(fname, {})[gname] = vals + [wc]
        print(f'{fname:40s} {gname:16s} ' + ' / '.join(f'{v:.3f}' for v in vals) + f' ; {wc:.3f}', flush=True)
(SCRATCH / 'pilot_neighbors_result.json').write_text(json.dumps(results, indent=1))
