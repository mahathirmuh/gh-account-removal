"""Pilot: what does a 404 account label mean? Inspect authored objects on other people's repositories.

deleted account  -> object survives, author becomes the 'ghost' user
hidden/suspended -> object may survive still attributed to the account, or disappear
Aggregates only. Requests are restricted to api.github.com because a token is attached.
"""
import collections, json, pathlib, random, sys, time, urllib.error, urllib.request

DATA = '/home/s2_giga/mahathir/trial/dm-git/2024-04-01-15.json/2024-04-01-15.json'
SP = pathlib.Path('/tmp/claude-1002/-home-s2-giga-mahathir-trial-dm-git/0d31c0d6-85c4-4f38-98bc-11db18cfae9e/scratchpad')
labels = json.loads((SP / 'pilot_labels.json').read_text())
gone = {int(k) for k, v in labels.items() if v is None}
present = {int(k) for k, v in labels.items() if v is not None}
rng = random.Random(42)
PREFIX = 'https://api.github.com/repos/'

tok = None
for line in (pathlib.Path.home() / '.dm-git.env').read_text().splitlines():
    if line.startswith('GITHUB_TOKEN='):
        tok = line.split('=', 1)[1].strip()
if not tok:
    sys.exit('no token')

objs = collections.defaultdict(list)
with open(DATA, 'rb') as f:
    for line in f:
        e = json.loads(line)
        a, t, p = e['actor'], e['type'], e['payload']
        url = None
        if t in ('IssueCommentEvent', 'PullRequestReviewCommentEvent', 'CommitCommentEvent'):
            url = p['comment']['url']
        elif t == 'IssuesEvent' and p.get('action') == 'opened':
            url = p['issue']['url']
        elif t == 'PullRequestEvent' and p.get('action') == 'opened':
            url = p['pull_request']['url']
        if url and url.startswith(PREFIX) and e['repo']['name'].split('/')[0].lower() != a['login'].lower():
            objs[a['id']].append(url)

def get(url):
    assert url.startswith(PREFIX)
    req = urllib.request.Request(url, headers={'Authorization': 'Bearer ' + tok, 'User-Agent': 'dm-git-pilot',
                                               'Accept': 'application/vnd.github+json'})
    for attempt in range(5):
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                return r.status, json.load(r)
        except urllib.error.HTTPError as e:
            if e.code in (403, 429, 502, 503) and attempt < 4:
                time.sleep(10 * 2 ** attempt)
                continue
            return e.code, None
        except urllib.error.URLError:
            time.sleep(10 * 2 ** attempt)
    return 0, None

def classify(aid):
    urls = objs[aid][:]
    rng.shuffle(urls)
    res = collections.Counter()
    for u in urls[:3]:
        s, j = get(u)
        if s == 200:
            who = (j.get('user') or {})
            if who.get('login') == 'ghost':
                res['ghost'] += 1
            elif who.get('id') == aid:
                res['attributed'] += 1
            else:
                res['other_author'] += 1
        else:
            res[f'http_{s}'] += 1
    return res

def outcome(res):
    if res['ghost']:
        return 'ghost'
    if res['attributed']:
        return 'attributed'
    if res['other_author']:
        return 'other_author'
    return 'object_unavailable'

g_with = sorted(a for a in gone if objs[a])
p_with = sorted(a for a in present if objs[a])
control = rng.sample(p_with, min(150, len(p_with)))
print('gone accounts', len(gone), 'with authored objects on others repos', len(g_with))
print('present accounts', len(present), 'with such objects', len(p_with), 'control sample', len(control))

for name, group in (('GONE', g_with), ('PRESENT (control)', control)):
    per_acc, per_obj = collections.Counter(), collections.Counter()
    for a in group:
        r = classify(a)
        per_obj.update(r)
        per_acc[outcome(r)] += 1
    print(f'\n{name}: accounts by outcome', dict(per_acc), ' n=', len(group))
    print('  objects by result', dict(per_obj))
