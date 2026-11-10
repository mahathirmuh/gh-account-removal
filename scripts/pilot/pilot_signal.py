"""Throwaway feasibility pilot: is there signal beyond event count on the development hour?

Reads the one local GH Archive hour, fetches account status for accounts with >=5 events,
and compares nested feature sets with group-aware cross-validation. Prints aggregates only.
"""
import base64
import collections
import hashlib
import json
import math
import pathlib
import sys
import time
import urllib.error
import urllib.request

import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import average_precision_score, roc_auc_score
from sklearn.model_selection import StratifiedGroupKFold

SCRATCH = pathlib.Path('/tmp/claude-1002/-home-s2-giga-mahathir-trial-dm-git/0d31c0d6-85c4-4f38-98bc-11db18cfae9e/scratchpad')
DATA = '/home/s2_giga/mahathir/trial/dm-git/2024-04-01-15.json/2024-04-01-15.json'
LABELS = SCRATCH / 'labels_h0_ge5.json'
RESULT = SCRATCH / 'pilot_signal_result.json'
TYPES = ['PushEvent', 'CreateEvent', 'PullRequestEvent', 'DeleteEvent', 'WatchEvent', 'IssueCommentEvent',
         'PullRequestReviewEvent', 'IssuesEvent', 'PullRequestReviewCommentEvent', 'ForkEvent', 'ReleaseEvent',
         'PublicEvent', 'MemberEvent', 'GollumEvent', 'CommitCommentEvent']
MIN_EVENTS = 5
SEEDS = [42, 43, 44]
BOOT = 1000


def new_actor():
    return {'secs': [], 'types': collections.Counter(), 'repos': collections.Counter(), 'own': 0, 'org': 0,
            'push_sizes': [], 'push_distinct': [], 'msgs': [], 'shorts': [], 'new_repo': 0, 'new_branch': 0,
            'new_tag': 0, 'pr_none': 0, 'pr_opened': 0}


A = collections.defaultdict(new_actor)
msg_acc = collections.defaultdict(set)
repo_acc = collections.defaultdict(set)
short_acc = collections.defaultdict(set)
with open(DATA, 'rb') as f:
    for line in f:
        e = json.loads(line)
        a = e['actor']
        login = a['login']
        if login.endswith('[bot]'):
            continue
        i = a['id']
        r = e['repo']
        t = e['created_at']
        owner, short = r['name'].split('/', 1) if '/' in r['name'] else ('', r['name'])
        x = A[i]
        typ = e['type']
        x['secs'].append(int(t[14:16]) * 60 + int(t[17:19]))
        x['types'][typ] += 1
        x['repos'][r['id']] += 1
        x['own'] += owner.lower() == login.lower()
        x['org'] += 'org' in e
        x['shorts'].append(short)
        repo_acc[r['id']].add(i)
        short_acc[short.lower()].add(i)
        p = e['payload']
        if typ == 'PushEvent':
            x['push_sizes'].append(p.get('size', 0))
            x['push_distinct'].append(p.get('distinct_size', 0))
            for c in p.get('commits') or []:
                m = (c.get('message') or '').strip()
                h = hashlib.blake2b(m.encode('utf-8', 'ignore'), digest_size=8).hexdigest()
                x['msgs'].append((h, len(m)))
                msg_acc[h].add(i)
        elif typ == 'CreateEvent':
            rt = p.get('ref_type')
            x['new_repo'] += rt == 'repository'
            x['new_branch'] += rt == 'branch'
            x['new_tag'] += rt == 'tag'
        elif typ == 'PullRequestEvent' and p.get('action') == 'opened':
            x['pr_opened'] += 1
            x['pr_none'] += (p.get('pull_request') or {}).get('author_association') == 'NONE'

ids = sorted(i for i, x in A.items() if sum(x['types'].values()) >= MIN_EVENTS)
print('accounts with >=5 events (excl. [bot])', len(ids), flush=True)


def load_token():
    tok = ''
    for line in (pathlib.Path.home() / '.dm-git.env').read_text().splitlines():
        if line.startswith('GITHUB_TOKEN='):
            tok = line.split('=', 1)[1].strip()
    if not tok:
        sys.exit('no token')
    return tok


def graphql(tok, body):
    headers = {'Authorization': 'Bearer ' + tok, 'User-Agent': 'dm-git-pilot', 'Content-Type': 'application/json'}
    last = None
    for attempt in range(4):
        req = urllib.request.Request('https://api.github.com/graphql', data=json.dumps(body).encode(), headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=90) as r:
                return json.load(r)
        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError) as err:
            last = getattr(err, 'code', type(err).__name__)
            time.sleep(2 ** (attempt + 1))
    sys.exit(f'graphql failed after retries: {last}')


if LABELS.exists():
    gone = {int(k): v for k, v in json.loads(LABELS.read_text()).items()}
    print('labels loaded from cache', len(gone), flush=True)
else:
    tok = load_token()
    Q = 'query($ids:[ID!]!){rateLimit{cost remaining} nodes(ids:$ids){__typename}}'
    gone = {}
    t0 = time.time()
    for k in range(0, len(ids), 100):
        batch = ids[k:k + 100]
        j = graphql(tok, {'query': Q, 'variables': {'ids': [base64.b64encode(f'04:User{i}'.encode()).decode() for i in batch]}})
        if not j.get('data'):
            sys.exit('graphql returned no data; error types: ' + str(collections.Counter(e.get('type') for e in j.get('errors', []))))
        for i, n in zip(batch, j['data']['nodes']):
            gone[i] = int(n is None)
        time.sleep(0.2)
    LABELS.write_text(json.dumps(gone))
    print('labels fetched', len(gone), 'secs', round(time.time() - t0, 1), flush=True)

y = np.array([gone[i] for i in ids])
n_events = np.array([sum(A[i]['types'].values()) for i in ids])
print('positives', int(y.sum()), 'rate', round(float(y.mean()), 4), flush=True)


def entropy(values):
    total = sum(values)
    return -sum((v / total) * math.log(v / total) for v in values if v)


def features(i):
    x = A[i]
    n = sum(x['types'].values())
    s = sorted(x['secs'])
    g = np.diff(s).astype(float) if len(s) > 1 else np.array([0.0])
    mu, sd = g.mean(), g.std()
    minutes = collections.Counter(v // 60 for v in s)
    gap_mode = collections.Counter(g.tolist()).most_common(1)[0][1] / len(g)
    rv = list(x['repos'].values())
    ps = x['push_sizes'] or [0]
    pd_ = x['push_distinct'] or [0]
    msgs = x['msgs']
    hashes = [h for h, _ in msgs]
    msg_counts = collections.Counter(hashes)
    shorts = x['shorts']
    behaviour = [x['types'][t] / n for t in TYPES] + [
        len(x['types']), len(minutes), mu, sd, sd / (mu + 1e-9), (sd - mu) / (sd + mu + 1e-9), g.min(),
        float(np.mean(g == 0)), gap_mode, s[-1] - s[0], entropy(list(minutes.values())), max(minutes.values()),
        len(rv), len(rv) / n, entropy(rv), max(rv) / n, x['own'] / n, x['org'] / n,
        float(np.mean(ps)), max(ps), sum(ps), sum(pd_) / (sum(ps) + 1e-9),
        len(msgs), len(msg_counts) / (len(msgs) + 1e-9),
        float(np.mean([m for _, m in msgs])) if msgs else 0.0,
        max(msg_counts.values()) / len(msgs) if msgs else 0.0,
        x['new_repo'], x['new_branch'], x['new_tag'],
        x['pr_none'] / x['pr_opened'] if x['pr_opened'] else -1.0,
        float(np.mean([len(v) for v in shorts])), float(np.mean([any(c.isdigit() for c in v) for v in shorts])),
        len(set(shorts)) / n,
    ]
    msg_others = [len(msg_acc[h]) - 1 for h in msg_counts]
    repo_others = [len(repo_acc[r]) - 1 for r in x['repos']]
    short_others = [len(short_acc[v.lower()]) - 1 for v in set(shorts)]
    coordination = [
        max(msg_others) if msg_others else -1,
        float(np.mean(np.log1p(msg_others))) if msg_others else -1.0,
        float(np.mean([o >= 1 for o in msg_others])) if msg_others else -1.0,
        float(np.mean([1 <= o <= 50 for o in msg_others])) if msg_others else -1.0,
        max(repo_others), float(np.mean(np.log1p(repo_others))), float(np.mean([o >= 1 for o in repo_others])),
        max(short_others), float(np.mean(np.log1p(short_others))), float(np.mean([o >= 1 for o in short_others])),
    ]
    return [math.log1p(n)], [float(i)], behaviour, coordination


rows = [features(i) for i in ids]
V = np.array([r[0] for r in rows])
G = np.array([r[1] for r in rows])
B = np.array([r[2] for r in rows])
C = np.array([r[3] for r in rows])
print('feature counts: volume', V.shape[1], 'age proxy', G.shape[1], 'behaviour', B.shape[1], 'coordination proxies', C.shape[1], flush=True)
SETS = {
    'S1_events': V,
    'S2_events+age': np.hstack([V, G]),
    'S3_+behaviour': np.hstack([V, G, B]),
    'S4_+coordination': np.hstack([V, G, B, C]),
}

idx = {i: k for k, i in enumerate(ids)}
e_rows, e_cols = [], []
for group in list(repo_acc.values()) + list(msg_acc.values()):
    if 2 <= len(group) <= 50:
        g = [idx[a] for a in group if a in idx]
        for b in g[1:]:
            e_rows.append(g[0])
            e_cols.append(b)
n = len(ids)
_, comp = connected_components(coo_matrix((np.ones(len(e_rows)), (e_rows, e_cols)), shape=(n, n)), directed=False)
sizes = np.bincount(comp)
print('groups', len(sizes), 'largest', sorted(sizes.tolist(), reverse=True)[:5], 'accounts in groups >1', int(sizes[sizes > 1].sum()), flush=True)
np.savez(SCRATCH / 'pilot_arrays.npz', V=V, G=G, B=B, C=C, y=y, n_events=n_events, comp=comp, ids=np.array(ids))
import os
if os.environ.get('DUMP_ONLY'):
    sys.exit(0)


def oof(X, seed):
    p = np.zeros(len(y))
    for tr, te in StratifiedGroupKFold(n_splits=5, shuffle=True, random_state=seed).split(X, y, comp):
        m = HistGradientBoostingClassifier(max_iter=300, learning_rate=0.05, max_leaf_nodes=15, l2_regularization=1.0,
                                           min_samples_leaf=20, early_stopping=False, random_state=seed)
        m.fit(X[tr], y[tr])
        p[te] = m.predict_proba(X[te])[:, 1]
    return p


def precision_at(scores, labels, k):
    order = np.argsort(-scores, kind='stable')[:k]
    return float(labels[order].mean())


def summarize(scores, mask):
    labels = y[mask]
    s = scores[mask]
    return {'n': int(mask.sum()), 'pos': int(labels.sum()), 'base': float(labels.mean()),
            'ap': float(average_precision_score(labels, s)), 'auc': float(roc_auc_score(labels, s))}


masks = {'all>=5': n_events >= 5, '5-19': (n_events >= 5) & (n_events <= 19), '20+': n_events >= 20}
scores = {'S0_rank_events': n_events.astype(float)}
for name, X in SETS.items():
    t0 = time.time()
    per_seed = [oof(X, sd) for sd in SEEDS]
    scores[name] = np.mean(per_seed, axis=0)
    print(name, 'fit secs', round(time.time() - t0, 1), 'AP per seed', [round(float(average_precision_score(y, p)), 4) for p in per_seed], flush=True)

report = {}
for stratum, mask in masks.items():
    print(f'\n[{stratum}]')
    for name, s in scores.items():
        r = summarize(s, mask)
        r['p_at_50'] = precision_at(s[mask], y[mask], 50)
        r['p_at_100'] = precision_at(s[mask], y[mask], 100)
        report.setdefault(stratum, {})[name] = r
        print(f"  {name:18s} n={r['n']:5d} pos={r['pos']:4d} base={r['base']:.3f} AP={r['ap']:.4f} AUC={r['auc']:.4f} P@50={r['p_at_50']:.3f} P@100={r['p_at_100']:.3f}")

members = [np.where(comp == c)[0] for c in range(len(sizes))]
rng = np.random.default_rng(42)
pairs = [('S2_events+age', 'S1_events'), ('S3_+behaviour', 'S2_events+age'), ('S4_+coordination', 'S3_+behaviour'), ('S4_+coordination', 'S1_events')]
draws = {}
for stratum, mask in masks.items():
    draws[stratum] = {p: [] for p in pairs}
for b in range(BOOT):
    chosen = rng.integers(0, len(members), len(members))
    sel = np.concatenate([members[c] for c in chosen])
    for stratum, mask in masks.items():
        s_sel = sel[mask[sel]]
        labels = y[s_sel]
        if labels.sum() == 0 or labels.sum() == len(labels):
            continue
        for a, c in pairs:
            draws[stratum][(a, c)].append(average_precision_score(labels, scores[a][s_sel]) - average_precision_score(labels, scores[c][s_sel]))

print('\nCluster-bootstrap delta AP, 95% CI')
ci_report = {}
for stratum in masks:
    for a, c in pairs:
        arr = np.array(draws[stratum][(a, c)])
        lo, hi = np.percentile(arr, [2.5, 97.5])
        delta = report[stratum][a]['ap'] - report[stratum][c]['ap']
        ci_report[f'{stratum}|{a}-{c}'] = [float(delta), float(lo), float(hi)]
        print(f'  [{stratum:7s}] {a} - {c}: {delta:+.4f} [{lo:+.4f}, {hi:+.4f}]')

RESULT.write_text(json.dumps({'report': report, 'delta_ap_ci': ci_report, 'n_groups': int(len(sizes)), 'largest_group': int(sizes.max())}, indent=1))
print('\nsaved aggregates to scratchpad')
