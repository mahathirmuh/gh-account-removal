"""Throwaway check: does GitHub API status agree with public web-profile status?

Small sample, HEAD requests only, about one per 1.2 seconds, no token sent to github.com,
prints aggregate counts only and writes no account names to disk.
"""
import base64
import collections
import json
import pathlib
import sys
import time
import urllib.error
import urllib.request

import numpy as np

SCRATCH = pathlib.Path('/tmp/claude-1002/-home-s2-giga-mahathir-trial-dm-git/0d31c0d6-85c4-4f38-98bc-11db18cfae9e/scratchpad')
DATA = '/home/s2_giga/mahathir/trial/dm-git/2024-04-01-15.json/2024-04-01-15.json'
d = np.load(SCRATCH / 'pilot_arrays.npz')
ids, y, n_events = d['ids'], d['y'], d['n_events']
NEWEST = 164029354
rng = np.random.default_rng(7)


def pick(mask, k):
    pool = np.where(mask)[0]
    return pool if len(pool) <= k else rng.choice(pool, k, replace=False)


groups = {
    'A_api_gone': pick(y == 1, 60),
    'B_api_ok_newest_20plus': pick((y == 0) & (ids >= NEWEST) & (n_events >= 20), 120),
    'C_api_ok_newest_under20': pick((y == 0) & (ids >= NEWEST) & (n_events < 20), 80),
    'D_api_ok_older': pick((y == 0) & (ids < NEWEST), 100),
}
print({k: len(v) for k, v in groups.items()}, flush=True)

tok = ''
for line in (pathlib.Path.home() / '.dm-git.env').read_text().splitlines():
    if line.startswith('GITHUB_TOKEN='):
        tok = line.split('=', 1)[1].strip()

wanted = {int(ids[k]) for v in groups.values() for k in v}
event_login = {}
with open(DATA, 'rb') as f:
    for line in f:
        a = json.loads(line)['actor']
        if a['id'] in wanted:
            event_login[a['id']] = a['login']

alive = [int(ids[k]) for name, v in groups.items() if name != 'A_api_gone' for k in v]
current = {}
types = collections.Counter()
Q = 'query($ids:[ID!]!){nodes(ids:$ids){__typename ... on User{login} ... on Organization{login}}}'
for k in range(0, len(alive), 100):
    batch = alive[k:k + 100]
    body = json.dumps({'query': Q, 'variables': {'ids': [base64.b64encode(f'04:User{i}'.encode()).decode() for i in batch]}}).encode()
    req = urllib.request.Request('https://api.github.com/graphql', data=body, headers={'Authorization': 'Bearer ' + tok, 'User-Agent': 'dm-git-pilot', 'Content-Type': 'application/json'})
    with urllib.request.urlopen(req, timeout=90) as r:
        j = json.load(r)
    for i, n in zip(batch, j['data']['nodes']):
        if n:
            current[i] = n['login']
            types[n['__typename']] += 1
print('graphql alive resolved', len(current), dict(types), flush=True)


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None


opener = urllib.request.build_opener(NoRedirect)
limited = 0


def web_status(login):
    global limited
    req = urllib.request.Request(f'https://github.com/{login}', method='HEAD', headers={'User-Agent': 'dm-git-research/0.1'})
    try:
        with opener.open(req, timeout=30) as r:
            return r.status
    except urllib.error.HTTPError as e:
        if e.code == 429:
            limited += 1
            time.sleep(min(int(e.headers.get('Retry-After') or 60), 120))
            if limited >= 3:
                print('stopping: rate limited three times', flush=True)
                print_table()
                sys.exit(0)
        return e.code
    except Exception as e:
        return type(e).__name__


table = collections.defaultdict(collections.Counter)
renamed = 0


def print_table():
    print('\ngroup                      web-status counts')
    for name in groups:
        print(f'{name:26s}', dict(table[name]))
    print('alive accounts whose current login differs from event login', renamed)


for name, members in groups.items():
    for k in members:
        i = int(ids[k])
        if name == 'A_api_gone':
            login = event_login[i]
        else:
            if i not in current:
                table[name]['api_now_gone'] += 1
                continue
            login = current[i]
            renamed += login.lower() != event_login[i].lower()
        table[name][web_status(login)] += 1
        time.sleep(1.2)
    print(name, 'done', dict(table[name]), flush=True)

print_table()
(SCRATCH / 'pilot_webcheck_result.json').write_text(json.dumps({k: {str(a): b for a, b in v.items()} for k, v in table.items()}, indent=1))
