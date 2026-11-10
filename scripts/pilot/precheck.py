"""Pilot go/no-go on the development hour: is there signal beyond activity volume?

Aggregates only. No account names are printed. Not part of the project pipeline.
"""
import base64, collections, json, math, pathlib, re, sys, time, urllib.error, urllib.request

import numpy as np
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import average_precision_score, roc_auc_score
from sklearn.model_selection import GroupKFold

DATA = '/home/s2_giga/mahathir/trial/dm-git/2024-04-01-15.json/2024-04-01-15.json'
SP = pathlib.Path('/tmp/claude-1002/-home-s2-giga-mahathir-trial-dm-git/0d31c0d6-85c4-4f38-98bc-11db18cfae9e/scratchpad')
LBL = SP / 'pilot_labels.json'
MIN_EVENTS = 5
SEED = 42

# ---- first pass: activity counts
counts, logins = collections.Counter(), {}
with open(DATA, 'rb') as f:
    for line in f:
        a = json.loads(line)['actor']
        counts[a['id']] += 1
        logins[a['id']] = a['login']
cohort = sorted(i for i, n in counts.items() if n >= MIN_EVENTS and not logins[i].endswith('[bot]'))
print('cohort accounts', len(cohort))

# ---- labels (cached in the scratchpad)
def load_token():
    for line in (pathlib.Path.home() / '.dm-git.env').read_text().splitlines():
        if line.startswith('GITHUB_TOKEN='):
            return line.split('=', 1)[1].strip()
    sys.exit('no token')

def graphql(tok, ids):
    q = 'query($ids:[ID!]!){nodes(ids:$ids){__typename}}'
    body = json.dumps({'query': q, 'variables': {'ids': ids}}).encode()
    req = urllib.request.Request('https://api.github.com/graphql', data=body, headers={
        'Authorization': 'Bearer ' + tok, 'User-Agent': 'dm-git-pilot', 'Content-Type': 'application/json'})
    for attempt in range(6):
        try:
            with urllib.request.urlopen(req, timeout=90) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            print('http', e.code, 'retrying'); time.sleep(5 * 2 ** attempt)
        except urllib.error.URLError:
            print('network error, retrying'); time.sleep(5 * 2 ** attempt)
    sys.exit('graphql failed')

labels = json.loads(LBL.read_text()) if LBL.exists() else {}
todo = [i for i in cohort if str(i) not in labels]
if todo:
    tok = load_token()
    t0 = time.time()
    for k in range(0, len(todo), 100):
        batch = todo[k:k + 100]
        ids = [base64.b64encode(f'04:User{i}'.encode()).decode() for i in batch]
        j = graphql(tok, ids)
        if not j.get('data'):
            sys.exit('no data: ' + str(collections.Counter(e.get('type') for e in j.get('errors', []))))
        for i, n in zip(batch, j['data']['nodes']):
            labels[str(i)] = None if n is None else n['__typename']
    LBL.write_text(json.dumps(labels))
    print('fetched labels', len(todo), 'secs', round(time.time() - t0, 1))
y = np.array([1 if labels[str(i)] is None else 0 for i in cohort])
print('positives', int(y.sum()), 'prevalence', round(float(y.mean()), 4))

# ---- second pass: per-account raw material
TYPES = ['PushEvent', 'CreateEvent', 'PullRequestEvent', 'DeleteEvent', 'WatchEvent', 'IssueCommentEvent',
         'PullRequestReviewEvent', 'IssuesEvent', 'PullRequestReviewCommentEvent', 'ForkEvent', 'ReleaseEvent',
         'PublicEvent', 'MemberEvent', 'GollumEvent', 'CommitCommentEvent']
cset = set(cohort)
ev = collections.defaultdict(list)
msg_acc, repo_acc, tmpl_own = collections.defaultdict(set), collections.defaultdict(set), collections.defaultdict(set)
digits = re.compile(r'\d+')
norm = lambda s: digits.sub('', s.lower()).strip()
with open(DATA, 'rb') as f:
    for line in f:
        e = json.loads(line)
        a = e['actor']['id']
        rid, rname = e['repo']['id'], e['repo']['name']
        owner, _, short = rname.partition('/')
        repo_acc[rid].add(a)
        tmpl_own[norm(short)].add(owner)
        msgs = []
        p = e['payload']
        if e['type'] == 'PushEvent':
            for c in p.get('commits', []):
                m = norm(c.get('message', '')[:200])
                msg_acc[m].add(a)
                msgs.append((m, 'noreply' in c.get('author', {}).get('email', ''), c.get('distinct', True)))
        if a in cset:
            ts = e['created_at']
            sec = int(ts[14:16]) * 60 + int(ts[17:19])
            ev[a].append(dict(t=sec, ty=e['type'], rid=rid, owner=owner, short=short, org='org' in e, p=p if e['type'] in
                              ('PushEvent', 'CreateEvent', 'DeleteEvent', 'PullRequestEvent') else None, msgs=msgs))

def ent(c):
    n = sum(c.values())
    return -sum(v / n * math.log(v / n) for v in c.values() if v)

def behaviour(a):
    es = sorted(ev[a], key=lambda x: x['t'])
    n = len(es)
    ty = collections.Counter(x['ty'] for x in es)
    rp = collections.Counter(x['rid'] for x in es)
    ts = np.array([x['t'] for x in es], float)
    gaps = np.diff(ts)
    mins = collections.Counter(int(t // 60) for t in ts)
    login = logins[a]
    mu, sd = gaps.mean(), gaps.std()
    pushes = [x['p'] for x in es if x['ty'] == 'PushEvent']
    sizes = [p.get('size', 0) for p in pushes]
    dist = [p.get('distinct_size', 0) for p in pushes]
    ct = lambda t, rt: sum(1 for x in es if x['ty'] == t and x['p'].get('ref_type') == rt)
    prs = [x['p'] for x in es if x['ty'] == 'PullRequestEvent']
    closed = [p for p in prs if p.get('action') == 'closed']
    return [
        *[ty[t] / n for t in TYPES], ent(ty), len(rp), ent(rp), max(rp.values()) / n,
        len(mins), max(mins.values()), float(np.median(gaps)), sd / mu if mu else 0, (sd - mu) / (sd + mu) if (sd + mu) else 0,
        float(np.mean(np.abs(gaps - np.median(gaps)) <= 1)),
        sum(1 for x in es if x['owner'].lower() == login.lower()) / n, sum(x['org'] for x in es) / n,
        float(np.mean(sizes)) if sizes else 0, sum(dist) / sum(sizes) if sum(sizes) else 0,
        ct('CreateEvent', 'branch'), ct('CreateEvent', 'tag'), ct('CreateEvent', 'repository'), ct('DeleteEvent', 'branch'),
        sum(1 for p in closed if p['pull_request'].get('merged')) / len(closed) if closed else 0,
    ]

def content(a):
    login = logins[a]
    msgs = [m for x in ev[a] for m in x['msgs']]
    shorts = collections.Counter(x['short'] for x in ev[a])
    top = shorts.most_common(1)[0][0]
    return [
        len(login), sum(c.isdigit() for c in login) / len(login), login.count('-'),
        len({m for m, _, _ in msgs}) / len(msgs) if msgs else 0, float(np.mean([len(m) for m, _, _ in msgs])) if msgs else 0,
        float(np.mean([nr for _, nr, _ in msgs])) if msgs else 0, len(msgs),
        sum(c.isdigit() for c in top) / max(len(top), 1), len(top),
    ]

def coordination(a):
    msgs = {m for x in ev[a] for m, _, _ in x['msgs'] if m}
    sh_m = [len(msg_acc[m]) for m in msgs]
    rids = {x['rid'] for x in ev[a]}
    sh_r = [len(repo_acc[r]) for r in rids]
    tm = [len(tmpl_own[norm(x['short'])]) for x in ev[a]]
    return [max(sh_m, default=0), float(np.mean(sh_m)) if sh_m else 0, max(sh_r), float(np.mean(sh_r)), max(tm), float(np.mean(tm))]

n = np.array([counts[i] for i in cohort], float)
aid = np.array(cohort, float)
Xb = np.array([behaviour(a) for a in cohort]); Xc = np.array([content(a) for a in cohort]); Xk = np.array([coordination(a) for a in cohort])
base = np.c_[np.log1p(n)]
age = np.c_[aid]

# ---- leakage-safe groups: union accounts through small shared repos and shared messages
parent = {i: i for i in cohort}
def find(x):
    while parent[x] != x:
        parent[x] = parent[parent[x]]
        x = parent[x]
    return x
def union_all(items):
    items = [i for i in items if i in parent]
    for j in items[1:]:
        parent[find(j)] = find(items[0])
for s in repo_acc.values():
    if 2 <= len(s) <= 30:
        union_all(list(s))
for m, s in msg_acc.items():
    if m and 2 <= len(s) <= 30:
        union_all(list(s))
g = np.array([find(i) for i in cohort])
sizes = collections.Counter(g.tolist())
print('groups', len(sizes), 'largest', max(sizes.values()))

def oof(X):
    pred = np.zeros(len(y))
    for tr, te in GroupKFold(n_splits=5).split(X, y, g):
        m = HistGradientBoostingClassifier(max_iter=300, learning_rate=0.05, max_leaf_nodes=31, min_samples_leaf=20,
                                           early_stopping=False, random_state=SEED)
        pred[te] = m.fit(X[tr], y[tr]).predict_proba(X[te])[:, 1]
    return pred

models = {
    'n_events only (rank)': n.copy(),
    'actor_id only': oof(age),
    'n_events + actor_id': oof(np.c_[base, age]),
    'behaviour (no id)': oof(np.c_[base, Xb]),
    'behaviour + id': oof(np.c_[base, age, Xb]),
    '+ content': oof(np.c_[base, age, Xb, Xc]),
    '+ content + coordination': oof(np.c_[base, age, Xb, Xc, Xk]),
}

def pk(y_, s, k):
    return float(y_[np.argsort(-s, kind='stable')[:k]].mean())

masks = {'all >=5': n >= 5, '5-19': (n >= 5) & (n < 20), '>=20': n >= 20}
for name, mk in masks.items():
    print(f'\n[{name}] n={int(mk.sum())} positives={int(y[mk].sum())} prevalence={y[mk].mean():.4f}')
    print(f'{"model":28s} {"AP":>7s} {"ROC":>7s} {"P@100":>7s}')
    for mn, s in models.items():
        print(f'{mn:28s} {average_precision_score(y[mk], s[mk]):7.4f} {roc_auc_score(y[mk], s[mk]):7.4f} {pk(y[mk], s[mk], 100):7.3f}')

# ---- paired, group-level bootstrap of the difference in AP
rng = np.random.default_rng(SEED)
ug = np.unique(g)
idx = {u: np.where(g == u)[0] for u in ug}
def boot(a, b, mk, reps=1000):
    out = []
    for _ in range(reps):
        pick = rng.choice(ug, len(ug), replace=True)
        ii = np.concatenate([idx[u] for u in pick])
        ii = ii[mk[ii]]
        if y[ii].sum() == 0:
            continue
        out.append(average_precision_score(y[ii], a[ii]) - average_precision_score(y[ii], b[ii]))
    return np.percentile(out, [2.5, 50, 97.5]).round(4)

for nm, mk in masks.items():
    print(f'\nDelta AP [{nm}] 95% CI, group bootstrap')
    print('  n_events+id minus n_events        ', boot(models['n_events + actor_id'], models['n_events only (rank)'], mk))
    print('  behaviour+id minus n_events+id    ', boot(models['behaviour + id'], models['n_events + actor_id'], mk))
    print('  +content minus behaviour+id       ', boot(models['+ content'], models['behaviour + id'], mk))
    print('  +coordination minus +content      ', boot(models['+ content + coordination'], models['+ content'], mk))

# descriptive: account id (age proxy) by outcome, as percentiles of the cohort
ranks = aid.argsort().argsort() / len(aid)
print('\nactor_id percentile median: gone', round(float(np.median(ranks[y == 1])), 3), 'present', round(float(np.median(ranks[y == 0])), 3))
