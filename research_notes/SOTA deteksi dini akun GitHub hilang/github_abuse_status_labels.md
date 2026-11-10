# Abuse, fake-account and malicious-activity detection on GitHub, and later account or repository status as labels

Checked 2026-11-10. Unless listed under "Unverified" (Question 7, Gaps), every source was opened in this session. "Via OpenAlex" means I read the bibliographic record and abstract from the OpenAlex API, not the full text. "Local measurement" means I computed the figure myself from the project file `2024-04-01-15.json`. "Computed" means simple arithmetic on figures from the cited source. No GitHub token was used. Individual accounts named in sources are deliberately not repeated here.

## 1. Which studies detect fake stars, spam, malicious repositories, abusive accounts, star or commit farming, or coordinated promotion on GitHub or with GH Archive?

### Takeaway

Four works form the core: GitSec (an account classifier trained on GitHub's own blocking status, 2019 and 2023), Du et al. (a paid-promoter classifier on GH Archive, 2020), StarScout (a fake-star measurement study, confirmed as He et al., ICSE 2026) and Cheng et al. (a small abuse taxonomy, 2026). The rest is repository-content malware detection or non-peer-reviewed industry reporting.

### Cited Findings

#### Peer-reviewed or preprint studies

**He et al. 2026, StarScout (verified)**
- **Citation.** Hao He, Haoqin Yang, Philipp Burckhardt, Alexandros Kapravelos, Bogdan Vasilescu, Christian Kästner. "Six Million (Suspected) Fake Stars on GitHub: A Growing Spiral of Popularity Contests, Spam, and Malware." ICSE 2026, 13 pages. DOI 10.1145/3744916.3764531 — [ICSE PDF, title page](https://cmustrudel.github.io/papers/icse2026fakestars.pdf).
- **Versions.** arXiv v1 (18 Dec 2024) was titled "4.5 Million (Suspected) Fake Stars in GitHub"; v2 (6 Sep 2025) carries the "Six Million" title with the wording "Spams" — [v1 record](https://arxiv.org/abs/2412.13459v1); [v2 record](https://arxiv.org/abs/2412.13459v2). Numbers below are from the ICSE PDF unless stated.
- **Task.** Detect suspected fake stars, repositories with fake-star campaigns and accounts in those campaigns — [Abstract, Section 3](https://cmustrudel.github.io/papers/icse2026fakestars.pdf).
- **Data.** GH Archive on BigQuery, covering 63.9 million users, 331 million repositories, 326 million stars and 6.7 billion other events as of January 2025 (Section 1); analysis period July 2019 to December 2024; more than 20 TB (Section 3.3) — [ICSE PDF](https://cmustrudel.github.io/papers/icse2026fakestars.pdf).
- **Label origin.** No training labels; the detector is heuristic. Recall was measured on the Stargazers Ghost Network dataset (847 repositories with more than 50 stars from 15,672 accounts). Precision was proxied by "criterion validity" using deletion ratios (Section 3.4) — [ICSE PDF](https://cmustrudel.github.io/papers/icse2026fakestars.pdf).
- **Features and method.** Low-activity signature: an account with one WatchEvent plus at most one other event in the same repository on the same day, restricted to repositories with at least 50 suspected fake stars. Lockstep signature: CopyCatch on the star bipartite graph with n=50, m=10, Δt=30 days, ρ=0.5, in interleaving six-month chunks. Postprocessing: a month with more than 50 fake stars and more than 50% fake share, and an all-time fake share above 10% (Sections 3.2, 3.3) — [ICSE PDF](https://cmustrudel.github.io/papers/icse2026fakestars.pdf).
- **Results.** 6.0 million suspected fake stars across 26,254 repositories before postprocessing (1.06 million low activity, 4.93 million lockstep); 18,617 repositories with campaigns and 301k accounts (3.81 million fake stars) after it (Section 3.3). Recall 688/847 = 81.23% of repositories and 11,903/15,672 = 75.95% of accounts (Section 3.4; the same paragraph also prints "82.23%" for repositories, which conflicts with its own count). 90.42% of repositories and 57.07% of accounts in campaigns were deleted (Table 1) — [ICSE PDF](https://cmustrudel.github.io/papers/icse2026fakestars.pdf).
- **Stated limitations.** Evidence is insufficient for disciplinary action, false positives remain possible, and heuristics and thresholds are ad hoc with limited sensitivity testing (Section 3.5). "GitHub does not preserve deleted repositories and users" (Section 1) — [ICSE PDF](https://cmustrudel.github.io/papers/icse2026fakestars.pdf).
- **Code and data.** Zenodo DOI 10.5281/zenodo.17009693 (Data Availability) — [ICSE PDF](https://cmustrudel.github.io/papers/icse2026fakestars.pdf); code and data at [hehao98/StarScout](https://raw.githubusercontent.com/hehao98/StarScout/main/README.md).

**Gong et al. 2019 and 2023, GitSec (closest prior work, see Questions 2, 3, 7)**
- **Citation.** Qingyuan Gong, Jiayun Zhang, Yang Chen, Qi Li, Yu Xiao, Xin Wang, Pan Hui. "Detecting Malicious Accounts in Online Developer Communities Using Deep Learning." CIKM 2019. DOI 10.1145/3357384.3357971 — [CIKM PDF](https://user.informatik.uni-goettingen.de/~ychen/papers/GitSec-CIKM19.pdf). Extended version with Yushan Liu added: IEEE TKDE 35(10):10633-10649, 2023, DOI 10.1109/TKDE.2023.3237838 — [open copy](https://aaltodoc.aalto.fi/bitstreams/9095077c-3398-4c13-9f15-5130dbe9b9b7/download); [volume and pages from the authors' README](https://raw.githubusercontent.com/chenyang03/developers/master/README.md).
- **Task.** Binary classification of GitHub accounts as malicious or legitimate — [CIKM abstract](https://user.informatik.uni-goettingen.de/~ychen/papers/GitSec-CIKM19.pdf).
- **Data.** 10,667,583 users drawn by ID-based random sampling from accounts registered by 31 Dec 2017, via `https://api.github.com/user/ID`, crawled 20 Jun to 27 Aug 2018, joined to GH Archive events. The CIKM evaluation used 59,857 users (44,892 legitimate, 14,965 malicious) with at least three events in the previous three years (Sections 2.2, 5.1) — [CIKM PDF](https://user.informatik.uni-goettingen.de/~ychen/papers/GitSec-CIKM19.pdf). The TKDE version states events from 1 Jan 2015 to 31 May 2018 and 2,955,783 legitimate plus 57,790 malicious users with at least three events, then samples "10,000 legitimate and malicious users" at the 21.5:78.5 ratio — [TKDE, Sections 2.2, 4.1](https://aaltodoc.aalto.fi/bitstreams/9095077c-3398-4c13-9f15-5130dbe9b9b7/download).
- **Label origin.** GitHub's own blocking status. A web profile returning 404 while the API still resolves means malicious; a web profile returning 200 means legitimate. Footnote: "Differently, self-deleted accounts cannot be accessed by the API." Details in Question 2 — [CIKM Section 2.2](https://user.informatik.uni-goettingen.de/~ychen/papers/GitSec-CIKM19.pdf).
- **Features and method.** Two event sequences (types and intervals) through parallel Phased LSTMs with attention, plus account and statistical features, into a CatBoost decision maker (Sections 3, 4, Table 1) — [CIKM PDF](https://user.informatik.uni-goettingen.de/~ychen/papers/GitSec-CIKM19.pdf). TKDE adds user-repository and user-user graphs using GraphSAGE and structural hole theory — [TKDE abstract, Section 3](https://aaltodoc.aalto.fi/bitstreams/9095077c-3398-4c13-9f15-5130dbe9b9b7/download).
- **Results.** CIKM: precision 0.951, recall 0.896, F1 0.922, AUC 0.940 (Table 3). Event features alone reach F1 0.911 and AUC 0.934; account features alone F1 0.633 and AUC 0.762 (Table 4) — [CIKM PDF](https://user.informatik.uni-goettingen.de/~ychen/papers/GitSec-CIKM19.pdf). TKDE: AUC 0.916 — [TKDE abstract](https://aaltodoc.aalto.fi/bitstreams/9095077c-3398-4c13-9f15-5130dbe9b9b7/download). TKDE per-metric tables did not extract cleanly from the PDF: not verified.
- **Evaluation design.** 7:3 stratified split with 5-fold cross-validation; no temporal or group-based split is described (CIKM Section 5.1; TKDE Section 4.1) — [CIKM PDF](https://user.informatik.uni-goettingen.de/~ychen/papers/GitSec-CIKM19.pdf).
- **Stated limitations.** The CIKM paper has no limitations section. TKDE tests label flipping and reports AUC of "almost 0.8" at around 35% corrupted labels (Section 4.2.7) — [TKDE](https://aaltodoc.aalto.fi/bitstreams/9095077c-3398-4c13-9f15-5130dbe9b9b7/download).
- **Code and data.** "The dataset is available upon request" (TKDE footnote 3) — [TKDE](https://aaltodoc.aalto.fi/bitstreams/9095077c-3398-4c13-9f15-5130dbe9b9b7/download). A dataset of 10,649,574 users is listed at DOI 10.7910/DVN/T6ZRJT — [authors' README](https://raw.githubusercontent.com/chenyang03/developers/master/README.md). A Figshare record gives a 10,000-user sample — [via OpenAlex](https://doi.org/10.6084/m9.figshare.21789566). No code release located.

**Du et al. 2020, Promotion-as-a-Service**
- **Citation.** Kun Du, Hao Yang, Yubao Zhang, Haixin Duan, Haining Wang, Shuang Hao, Zhou Li, Min Yang. "Understanding Promotion-as-a-Service on GitHub." ACSAC 2020. DOI 10.1145/3427228.3427258 — [PDF, title page](https://personal.utdallas.edu/~shao/papers/du_acsac20.pdf).
- **Task.** Detect accounts selling paid stars and forks, and characterise the market (Abstract) — [PDF](https://personal.utdallas.edu/~shao/papers/du_acsac20.pdf).
- **Data.** GH Archive 2015 to 2019, 4.79 TB (Section 1); 23,375,824 accounts extracted, more than 14 million after filtering (Sections 3.2, 3.3); GitHub API and web pages for profiles (Section 3.1) — [PDF](https://personal.utdallas.edu/~shao/papers/du_acsac20.pdf).
- **Label origin.** Positives: 1,023 accounts from purchasing promotions from 10 providers for a test repository. Negatives: 1,550 contributors to popular repositories (Sections 3.3, 3.4) — [PDF](https://personal.utdallas.edu/~shao/papers/du_acsac20.pdf).
- **Features and method.** Counts of 14 operation types, star and fork counts and ratio, and average adjacent-operation intervals at 1, 2 and 3 minutes and 1 hour (Table 3); six classifiers with 10-fold cross-validation (Section 3.6) — [PDF](https://personal.utdallas.edu/~shao/papers/du_acsac20.pdf).
- **Results.** SVM best: precision 98.5%, recall 99.7%, F1 0.991 (Table 4). Applied to all accounts, it flagged 63,872 suspected accounts. Accuracy with count features alone was 73.3%, with the ratio added 83.9%, and with time-distribution features added 98.5% (Section 3.6). For validation, 973 of 1,000 sampled accounts had starred or forked more than three suspected repositories (Section 3.7) — [PDF](https://personal.utdallas.edu/~shao/papers/du_acsac20.pdf).
- **Stated limitations.** Adversaries aware of the method could evade it by adding normal activity or slowing down (Section 6) — [PDF](https://personal.utdallas.edu/~shao/papers/du_acsac20.pdf).
- **Code and data.** No availability statement found in the PDF text (keyword check) — [PDF](https://personal.utdallas.edu/~shao/papers/du_acsac20.pdf).

**Cheng et al. 2026, Weaponizing the Commons**
- **Citation.** Yuli Cheng, Xiaoyu Zhang, Jiongchi Yu, Shiqing Ma, Chao Shen, Yang Liu. JAWs 2026 at ICSE 2026, 5 pages. arXiv 2604.17909 v1, 20 Apr 2026, DOI 10.48550/arXiv.2604.17909 — [arXiv record](https://arxiv.org/abs/2604.17909).
- **Task and data.** Taxonomy of eight abuse types and a unified detector. 392 manually annotated instances since 2020 (310 repositories, 82 accounts), balanced, from academic studies, security reports and grey literature (Section 4.1) — [PDF](https://arxiv.org/pdf/2604.17909).
- **Method.** StarScout for fake stars, MLP with TF-IDF for issue spam, BM25 for keyword stuffing, text similarity for typosquatting, and rule-based analysis for other categories (Section 4.1) — [PDF](https://arxiv.org/pdf/2604.17909).
- **Results.** All metrics above 89%; F1 93.2% for keyword stuffing and 93.6% for fake stats; lowest metrics 89.5% for issue spam and reputation farming (Section 4.2) — [PDF](https://arxiv.org/pdf/2604.17909).
- **Limitations.** Dataset "limited in scale" (Section 5). A keyword scan found no use of later account status — [PDF](https://arxiv.org/pdf/2604.17909).
- **Code.** github.com/Rasnd-yu/GitHub-Detector (footnote 1) — [PDF](https://arxiv.org/pdf/2604.17909).

**Repository-level malware detection (adjacent)**
- Qian, Zhang, Chawla, Ye, Zhang, "Malicious Repositories Detection with Adversarial Heterogeneous Graph Contrastive Learning," CIKM 2022, DOI 10.1145/3511808.3557384. Heterogeneous graph contrastive pre-training on "two collected datasets from GitHub". Sizes and metrics not verified (abstract only) — [via OpenAlex](https://api.openalex.org/works/doi:10.1145/3511808.3557384).
- El Yadmani, The, Gadyatskaya, "Beyond the Surface: Investigating Malicious CVE Proof of Concept Exploits on GitHub," arXiv 2210.08374 (v1 Oct 2022, v2 Jun 2023). Of 47,285 repositories for 2017 to 2021 vulnerabilities, 899 (1.9%) flagged using malicious IP calls, encoded malicious code and trojanized binaries (abstract) — [arXiv](https://arxiv.org/abs/2210.08374).
- Zhao, Wang, Wu, Zhao, Cheng, Wang, "MalTotal," ISSTA 2026, DOI 10.1145/3832228, arXiv 2608.03232. LLM-assisted slicing; average F1 93.1% across five languages; 564 previously unknown malicious repositories among 120K repositories (abstract) — [arXiv](https://arxiv.org/abs/2608.03232).
- Bae, Yagemann, "Beyond Takedown," arXiv 2606.26291, June 2026. 2,289 malicious Go module versions; at least 99.4% of artifacts "GitHub-unobservable (i.e., removed or suspended)" remained retrievable via the Go proxy; GitHub removed 684 repositories after disclosure (abstract) — [arXiv](https://arxiv.org/abs/2606.26291).

**Automated account detection (adjacent, not abuse)**
- Chidambaram, Mens, Decan, "RABBIT," MSR 2024, DOI 10.1145/3643991.3644877. Bot or human from up to 300 recent Events API events with XGBoost on six features; ground truth 644 bots and 691 humans; test precision, recall and F1 0.919, AUC 0.921 (Sections 3, 5, 6.1). Code: github.com/natarajan-chidambaram/RABBIT. Limitations: public events only and no prediction for accounts not recently active — [PDF](https://natarajan-chidambaram.github.io/papers/MSR2024_RABBIT_A_tool_for_identifying_bot_accounts_based_on_their_recent_GitHub_event_history.pdf).

#### Security-industry reports (non-peer-reviewed)

**Check Point Research 2024, Stargazers Ghost Network**
- **Citation.** Antonis Terefos, Check Point Research, 24 Jul 2024 — [report](https://research.checkpoint.com/2024/stargazers-ghost-network/).
- **Task and data.** Manual investigation of a distribution-as-a-service network using account roles (repository, commit, release, stargazer), monitored mid-May to mid-June 2024 for the profit estimates, with activity traced to about August 2022 — [report](https://research.checkpoint.com/2024/stargazers-ghost-network/).
- **Method.** Started from repositories with anomalous stars, then a repeatable naming pattern (`{username}1` repositories containing only a LICENSE and README) matched more than 1,100 repositories — [report](https://research.checkpoint.com/2024/stargazers-ghost-network/).
- **Results.** More than 2,200 malicious repositories with Ghost activity; more than 3,000 active Ghost accounts by "latest calculations"; GitHub took down approximately 1,559 repositories and related accounts since May 2024 — [report](https://research.checkpoint.com/2024/stargazers-ghost-network/).
- **Limitations.** Network size "unclear"; some accounts appear compromised rather than created by the operator; some repositories already removed — [report](https://research.checkpoint.com/2024/stargazers-ghost-network/).
- **Data.** Indicators of compromise and repository names are in the report. He et al. later used this campaign as recall ground truth — [He et al. Section 3.4](https://cmustrudel.github.io/papers/icse2026fakestars.pdf).

**Dagster 2023, "Tracking the Fake GitHub Star Black Market with Dagster, dbt and BigQuery"**
- Published 16 Mar 2023; author not named in the text I read. Bought stars for a dummy repository (500 from one vendor, 100 from another), then built a low-activity profile heuristic and clustering on GH Archive from 1 Jan 2022 onward. On the dummy repository the clustering heuristic reached 98% precision and 85% recall; false positive rate 0.17% on the Dagster repository. Within 48 hours of publication, all profiles used to star the test repository had been deleted. Code: dagster-io/fake-star-detector — [blog](https://dagster.io/blog/fake-stars).

**Orchid Files 2026, GH Archive-based malware campaign report**
- Published 18 Jun 2026; author not named. Used GH Archive for about five days (16 million commit pushes) and filtered repositories by update frequency and README-only commits, reaching about 10,000 matching repositories. No account counts. GitHub later deleted listed repositories, while a re-run's new repositories had "not been deleted" after 14 days — [report](https://orchidfiles.com/github-repositories-distributing-malware/); secondary coverage at [Cybersecurity News](https://cybersecuritynews.com/hackers-github-malicious-script/).

#### Data-source note
- GHTorrent's user table carries a `deleted` flag: the "user was once active on GitHub but GHTorrent can no longer get his/her details." The `fake` flag marks placeholder commit authors, not fraud — [GHTorrent schema](https://github.com/ghtorrent/ghtorrent.org/blob/master/relational.md). I found no study using `deleted` as an abuse label.

### Inferences
- Account-level supervised prediction on GitHub is thin: GitSec is effectively alone, while the rest is star-focused measurement or repository content analysis.
- Label origin varies by study: purchased promotions (Du, Dagster), heuristics with proxy validation (He), manual annotation (Cheng, RABBIT) and platform status (GitSec). The project sits in the last group, so GitSec is its natural baseline.
- GitSec is easy to miss from the fake-star literature. He et al. call Du et al. "the first and only academic report" on the star black market and the ICSE paper never mentions GitSec or Gong (text search of the PDF) — [He et al. Section 2.3](https://cmustrudel.github.io/papers/icse2026fakestars.pdf). OpenAlex's 24 works citing GitSec do not include He et al. — [OpenAlex citing list](https://api.openalex.org/works?filter=cites:W2987246247).
- Du et al.'s and GitSec's feature results both suggest that timing features separate accounts when counts do not, which bears directly on the project's "among equally active accounts" question.

### Gaps
- No full text read for Qian et al. 2022, so its dataset sizes and metrics are not verified.
- TKDE per-metric tables are not verified because the PDF text extraction was garbled.
- I did not survey commit-farming tools or Chinese-language venues in any depth.

## 2. Has any work used later GitHub account or repository status as a label or as validation?

### Takeaway

Yes. GitSec used GitHub blocking status as the training label for accounts in 2018, and StarScout and Du et al. used later status for validation or measurement. What I did not find is a GitHub study with a long fixed forward horizon that treats surviving accounts as unlabeled.

### Cited Findings

| Work | Entity | Status signal | Role | Gap between activity and status | Renames handled? | Noise handling | Positive rate |
|---|---|---|---|---|---|---|---|
| [GitSec CIKM 2019](https://user.informatik.uni-goettingen.de/~ychen/papers/GitSec-CIKM19.pdf), [TKDE 2023](https://aaltodoc.aalto.fi/bitstreams/9095077c-3398-4c13-9f15-5130dbe9b9b7/download) | Account | API `/user/ID` returns 200 and web profile returns 404 means malicious; API 404 means skipped as "Invalid user ID" | Training and test label | Events end 31 May 2018 and labels were collected 20 Jun to 27 Aug 2018, about 3 to 12 weeks (computed) | Not discussed. Lookup starts from the numeric ID and reads the current login from the API, so a rename is not treated as loss by construction | Web 200 treated as legitimate. TKDE reports label-flip robustness | 21.50% of 10,667,583 crawled; 1.92% of users with at least three events (57,790 of 3,013,573, computed); 25.0% in the CIKM evaluation set (14,965 of 59,857, computed) |
| [He et al. 2026](https://cmustrudel.github.io/papers/icse2026fakestars.pdf) | Repository and account | API lookup by login: [`user_info`](https://raw.githubusercontent.com/hehao98/StarScout/main/scripts/github.py) calls [`users/{username}`](https://raw.githubusercontent.com/cmustrudel/strudel.scraper/master/stscraper/github.py), and [404 is stored as deleted](https://raw.githubusercontent.com/hehao98/StarScout/main/scripts/analysis/get_stargazer_info.py) | Validation only | As of January 2025, with activity July 2019 to December 2024, so variable from near zero to about 5.5 years (computed) | No. Lookup uses `actor` login, so a rename registers as deleted (my reading of the code) | Comparison with random baseline samples; 10,000 detected accounts sampled | Accounts in campaigns 57.07%; all detected accounts 18.77%; printed baseline 3.54%. Repositories in campaigns 90.42%; printed baseline 5.03% (Table 1) |
| [Du et al. 2020](https://personal.utdallas.edu/~shao/papers/du_acsac20.pdf) | Account | Homepage 404, disambiguated from never-existing names by presence in GH Archive logs (Section 4.4) | Post-hoc measurement of GitHub enforcement | Not stated. Sample was 28,258 accounts detected in 2018 (Section 4.3) | Not discussed. Homepage check uses the login | None reported | 1,184 of 28,258 = 4.19% "banned" (Section 4.4) |
| [Check Point 2024](https://research.checkpoint.com/2024/stargazers-ghost-network/) | Repository and account | Observed bans and takedowns during monitoring | Campaign description | About mid-May to mid-June 2024 | Not applicable | None | About 1,559 repositories and related accounts |
| [Dagster 2023](https://dagster.io/blog/fake-stars) | Account | All purchased profiles deleted within 48 hours of publication | Anecdote | 48 hours | Not applicable | None | All test-repository profiles |
| [Bae, Yagemann 2026](https://arxiv.org/abs/2606.26291) | Repository (Go modules) | "Removed or suspended" as a category | Analysis of the takedown gap | Not verified | Not verified | Not verified | 684 repositories removed after disclosure |

**Exact GitSec label text.** "Profile pages of malicious users have been blocked by GitHub, whereas their basic information can still be accessed using GitHub API", with footnote 3: "Differently, self-deleted accounts cannot be accessed by the API." The check then requests the profile page: "If the HTTP status code returned '404' ... this user will be labeled as a malicious one. If the returned HTTP status code is '200', this user will be annotated as a legitimate one." — [CIKM Section 2.2](https://user.informatik.uni-goettingen.de/~ychen/papers/GitSec-CIKM19.pdf). TKDE adds: "We consulted GitHub and confirmed that the users whose profile pages have been blocked, whereas their basic information can still be accessed using GitHub API ... are the annotated malicious users," and its data-collection figure routes an API 404 to "Invalid user ID" — [TKDE Section 2.2](https://aaltodoc.aalto.fi/bitstreams/9095077c-3398-4c13-9f15-5130dbe9b9b7/download).

**StarScout version differences.** arXiv v1 reported deletion as of October 2024: repositories 90.75% with baseline 5.84%, accounts 61.95% with baseline 4.43% (Table II) — [v1](https://arxiv.org/html/2412.13459v1). The ICSE version reports January 2025: 90.42% and 57.07%, baselines 5.03% and 3.54% — [Table 1](https://cmustrudel.github.io/papers/icse2026fakestars.pdf).

**Discrepancy I found in StarScout's published baseline (my recomputation, not confirmed by the authors).** The authors' notebook divides the deleted count in the baseline sample by `len(repos)`, the number of detected repositories, instead of the sample size: `len(sample_user_info[sample_user_info.error.notnull()]) / len(repos)` — [notebook](https://raw.githubusercontent.com/hehao98/StarScout/main/evaluation-deletion-ratio.ipynb). The repository's data files have 10,000 baseline rows each, with 1,320 repositories lacking an ID and 930 accounts with an error — [sample_repo_ids.csv](https://raw.githubusercontent.com/hehao98/StarScout/main/data/250101/sample_repo_ids.csv); [sample_user_info.csv](https://raw.githubusercontent.com/hehao98/StarScout/main/data/250101/sample_user_info.csv). Dividing by the 26,254 detected repositories reproduces the published 5.03% and 3.54% exactly; dividing by the 10,000-row samples gives 13.20% and 9.30% (computed). The paper's "16x" would then be about 6.85x for repositories and 6.14x for accounts (computed). The notebook's other ratios use the correct denominators, for example 1,893 of 10,087 detected accounts = 18.77% — [notebook](https://raw.githubusercontent.com/hehao98/StarScout/main/evaluation-deletion-ratio.ipynb).

**Other platforms, for reference**
- Thomas, Grier, Song, Paxson, "Suspended accounts in retrospect," IMC 2011: more than 1.1 million accounts suspended by Twitter over seven months and 1.8 billion tweets (abstract) — [via OpenAlex](https://api.openalex.org/works/doi:10.1145/2068816.2068840).
- Saeed et al., TROLLMAGNIFIER, IEEE S&P 2022: on Reddit, "If the account was suspended, we get a 403 HTTP error; if it was deleted, the HTTP error code is 404"; 298 of 1,248 detected accounts were suspended or deleted — [arXiv PDF](https://arxiv.org/pdf/2112.00443).
- A 2025 survey warns that assuming "accounts deleted after a certain period are fake, while those that remain active are real" is "flawed, as sophisticated fake accounts can persist for a long time, and many real accounts may be closed for reasons unrelated to being a fake account" — [Graph-based fake account detection survey](https://arxiv.org/pdf/2507.06541).

### Inferences
- Using later status is established practice on GitHub, not new. What differs across works is the role (training label or validation) and how status is observed.
- GitSec and StarScout measure different things. GitSec's positives (API 200, web 404) are accounts that StarScout's API check would record as present, if GitSec's 2018 description still applies. StarScout's "deleted" count may therefore both miss blocked accounts and include renamed ones.
- Treat StarScout's 9.30% (recomputed), rather than 3.54%, as the more defensible comparator for the pilot, and note the populations differ (stargazers of repositories with at least 50 stars, against all accounts active in one hour).

### Gaps
- No work I read reports how much rename error affects login-based status checks on GitHub.
- The gap between Du et al.'s activity and their status check is not stated in the paper.

## 3. Has any work predicted account-level deletion, suspension or disappearance on GitHub? (Separated from churn.)

### Takeaway

GitSec is the only GitHub work I found that predicts a status-derived target, and that target is "blocked with the API still resolving", measured weeks after the features. I found no GitHub study predicting account deletion or disappearance at a long horizon. Churn work predicts project tenure or inactivity, which is a different target.

### Cited Findings

**Status-related prediction on GitHub**
- GitSec predicts malicious status defined by the web-profile block, reaching F1 0.922 and AUC 0.940 — [CIKM Table 3](https://user.informatik.uni-goettingen.de/~ychen/papers/GitSec-CIKM19.pdf); AUC 0.916 in the extension — [TKDE abstract](https://aaltodoc.aalto.fi/bitstreams/9095077c-3398-4c13-9f15-5130dbe9b9b7/download).

**Same target on other platforms**
- Volkova and Bell, ICWSM 2017, describe "a novel task – predicting suspicious e.g., to be deleted or suspended accounts in social media" using Twitter accounts in three languages, and find discourse more predictive than profile and network features (abstract) — [via OpenAlex](https://doi.org/10.1609/icwsm.v11i1.14874).
- Shevtsov et al., ASONAM 2023, predict Twitter suspension from 107.7 million tweets by 9.8 million users with machine learning and SHAP (abstract) — [via OpenAlex](https://api.openalex.org/works/doi:10.1145/3625007.3627317).
- Toraman, Şahinuç, Yılmaz, WebSci 2022, analyse about 500k users and 20 million tweets, including later deleted or suspended users (abstract) — [via OpenAlex](https://doi.org/10.1145/3501247.3531539).

**Closest churn or turnover work (different target)**
- Bao, Xia, Lo, Murphy, IEEE TSE (DOI 10.1109/TSE.2019.2918536): predict long-time contributors at 1, 2 and 3 year thresholds from monthly activity, on 917 projects and 75,046 contributors via GHTorrent; random forest AUC above 0.75; number of followers is the top feature (abstract) — [via OpenAlex](https://doi.org/10.1109/tse.2019.2918536).
- Eluri, Mazzuchi, Sarkani, Information and Software Technology 2021: 70,899 observations, 888 repositories, 56,766 contributors, 31 features at joining time; random forest precision 0.695, recall 0.079, F1 0.140, MCC 0.226, AUC 0.913 (abstract) — [via OpenAlex](https://doi.org/10.1016/j.infsof.2021.106616).
- Calefato, Gerosa, Iaffaldano, Lanubile, Steinmacher, Empirical Software Engineering 2022: inactivity states of core developers in 18 organizations; about 45% disengaged from a project for at least a year (abstract) — [via OpenAlex](https://doi.org/10.1007/s10664-021-10012-6).

### Inferences
- Churn studies model whether a person stops contributing to a project. The account usually still exists, so churn labels and account-existence labels measure different things, and churn results should not be cited as prior art for C1.
- Volkova and Bell is the closest framing of "predict later deletion or suspension" as a task, on another platform. Citing it would avoid implying that this task was invented for GitHub.
- None of the churn studies above uses account deletion or suspension as a target, at least in their abstracts.

### Gaps
- I could not open the full ACM page for Utzinger 2026 (see Unverified).

## 4. Has any work used a short window of GH Archive for account-level prediction?

### Takeaway

I found no study that classifies accounts from an hours-long GH Archive window. The nearest are RABBIT (up to 300 recent events per account from the Events API, bot or human) and a five-day repository-level analysis in a non-peer-reviewed report.

### Cited Findings
- RABBIT uses up to 300 recent events per account and reports accuracy by available event count: 86.3% for accounts with at most 100 events (214 of 248), 94.2% for 101 to 200 (81 of 86) and 98.5% for 201 to 300 (Section 6.1) — [PDF](https://natarajan-chidambaram.github.io/papers/MSR2024_RABBIT_A_tool_for_identifying_bot_accounts_based_on_their_recent_GitHub_event_history.pdf).
- The Orchid Files analysis uses about five days of GH Archive and works on repositories, reporting no account counts — [report](https://orchidfiles.com/github-repositories-distributing-malware/).
- Du et al. compute intervals at 1, 2, 3 and 60 minutes, but over multi-year per-account histories from 2015 to 2019 — [Table 3](https://personal.utdallas.edu/~shao/papers/du_acsac20.pdf).
- StarScout's low-activity signature uses a same-day rule, but deciding that an account starred only one repository requires the account's whole history in the analysis period — [Section 3.2](https://cmustrudel.github.io/papers/icse2026fakestars.pdf).
- Eluri et al. predict tenure from features at joining time, with no one-month waiting period (abstract) — [via OpenAlex](https://doi.org/10.1016/j.infsof.2021.106616).
- The GitHub Events API documentation states: "This API is not built to serve real-time use cases. Depending on the time of day, event latency can be anywhere from 30s to 6h." — [Events API docs](https://docs.github.com/en/rest/activity/events).

### Inferences
- A latency curve from 60 down to 5 minutes (C3) appears unoccupied on GitHub, but it should be presented as an evaluation of event-time windows on archived data. The documented 30-second to 6-hour API latency means a "5-minute" window is not a claim about real-time detection.
- RABBIT's result, that performance improves with the number of events, is the closest published analogue and worth citing against C3.

### Gaps
- Negative finding, audited by the search log under Question 7. Queries were title-and-abstract level and cannot exclude a method buried in a full text.

## 5. What does GitHub publicly document about suspended and deleted accounts?

### Takeaway

GitHub documents only 200 and 404 for its user lookup endpoints and gives no way to separate suspended from self-deleted accounts. The only published method (GitSec) says that in 2018 blocked accounts stayed visible on the API while their web profiles returned 404, and that self-deleted accounts returned 404 on the API. This conflicts with the project's premise that an API 404 on the numeric ID covers suspension. Research use of GitHub data is allowed only if resulting publications are open access.

### Cited Findings

**API behaviour**
- `GET /users/{username}` and `GET /user/{account_id}` each list status codes 200 and 404 ("Resource not found"). The ID endpoint "takes their durable user ID instead of their login, which can change over time." — [REST users docs](https://docs.github.com/en/rest/users/users).
- A text search of that page finds no mention of "suspended", "deleted", 410 or 451 — [REST users docs](https://docs.github.com/en/rest/users/users).
- HTTP 451 "will be returned for repositories and gists", with body "Repository access blocked" and a `block` reason such as `dmca`; accounts are not mentioned — [GitHub developer changelog, 2016](https://developer.github.com/changes/2016-03-17-the-451-status-code-is-now-supported/).
- I found no GitHub document stating what the API returns for a suspended account.

**Telling suspended from self-deleted**
- Official documentation: none found. The closest statement says "If your account is flagged, suspended, or otherwise restricted, Delete your account may be unavailable, disabled, or direct you to GitHub Support" — [Deleting your personal account](https://docs.github.com/en/account-and-profile/how-tos/account-management/deleting-your-personal-account).
- Empirical method: API 200 with web 404 means blocked, and API 404 means self-deleted, as stated in 2018-collected data and confirmed with GitHub according to the TKDE authors — [GitSec TKDE Section 2.2](https://aaltodoc.aalto.fi/bitstreams/9095077c-3398-4c13-9f15-5130dbe9b9b7/download).
- Du et al. state that a 404 page alone cannot separate "does not exist at all" from "banned", and use GH Archive presence to resolve it — [Section 4.4](https://personal.utdallas.edu/~shao/papers/du_acsac20.pdf).
- A 2022 developer blog reports that for suspended Russian accounts "Both the user account and the pull request result in a 404", that GitHub's staff said the mechanism "was built to target spammers", and that content was later restored. The post does not describe API responses — [Squires 2022](https://www.jessesquires.com/blog/2022/04/19/github-suspending-russian-accounts/).
- "Suspension" is not one state in GitHub's reporting. GitHub may "hide a user's account content ... while still giving the user the ability to access their account", or "restrict a user's access to their account ... while still giving other users the ability to access their shared content" — [Transparency data README](https://raw.githubusercontent.com/github/transparency/main/data/appeals_and_other_reinstatements/README.md).

**Renames, username reuse, deleted content**
- After a rename, "your old username becomes available for anyone else to claim" and links to the previous profile "will return a 404 error" — [Username changes](https://docs.github.com/en/account-and-profile/concepts/username-changes).
- After deletion, "After 90 days, the account name also becomes available to anyone else to use on a new account", and content becomes associated with the ghost user — [Account management concepts](https://docs.github.com/en/account-and-profile/concepts/account-management).

**Acceptable Use and API terms**
- Section 7: "You may use information from our Service for the following reasons, regardless of whether the information was scraped, collected through our API, or obtained otherwise: Researchers may use public, non-personal information from the Service for research purposes, only if any publications resulting from that research are open access." — [Acceptable Use Policies](https://docs.github.com/en/site-policy/acceptable-use-policies/github-acceptable-use-policies).
- "Scraping refers to extracting information from our Service via an automated process, such as a bot or webcrawler. Scraping does not refer to the collection of information through our API." Use "must comply with the GitHub Privacy Statement." — [Acceptable Use Policies, Section 7](https://docs.github.com/en/site-policy/acceptable-use-policies/github-acceptable-use-policies).
- Section 4 prohibits "inauthentic interactions, such as fake accounts and automated inauthentic activity" and "rank abuse, such as automated starring or following" — [Acceptable Use Policies](https://docs.github.com/en/site-policy/acceptable-use-policies/github-acceptable-use-policies).
- "Abuse or excessively frequent requests to GitHub via the API may result in the temporary or permanent suspension of your Account's access to the API", and "You may not share API tokens to exceed GitHub's rate limitations." — [Terms of Service, Section H](https://docs.github.com/en/site-policy/github-terms/github-terms-of-service).
- Rate limits are 60 requests per hour unauthenticated and 5,000 per hour for a personal token — [Rate limits docs](https://docs.github.com/en/rest/using-the-rest-api/rate-limits-for-the-rest-api).
- "GitHub has the right to suspend or terminate your access to all or any part of the Website at any time, with or without cause, with or without notice" — [Terms of Service, Section M](https://docs.github.com/en/site-policy/github-terms/github-terms-of-service).

**Published suspension statistics**

GitHub's structured transparency data on abuse-related account actions — [abuse_related_violations.csv](https://raw.githubusercontent.com/github/transparency/main/data/appeals_and_other_reinstatements/abuse_related_violations.csv):

| Year | Hidden | ...later unhidden | Access restricted | ...later unrestricted | Hidden and restricted | ...partially reinstated | ...fully reinstated | Projects disabled | ...re-enabled |
|---|---|---|---|---|---|---|---|---|---|
| 2025 | 9,171 | 230 | 480 | 19 | 77,402 | 258 | 336 | 16,121 | 220 |
| 2024 | 8,829 | 202 | 182 | 7 | 21,977 | 372 | 402 | 30,371 | 8 |
| 2023 | 28,632 | 683 | 13,498 | 359 | 13,452 | 347 | 331 | 8,840 | 130 |
| 2022 | 12,860 | 480 | 428 | 58 | 8,822 | 25 | 115 | 4,507 | 6 |
| 2021 | 4,585 | 341 | 69 | 23 | 4,240 | 8 | 28 | 2,257 | 55 |
| 2020 | 4,826 | 415 | 47 | 15 | 1,178 | 12 | 29 | 2,405 | 4 |

- Scope matters: this category is "violations of our Acceptable Use Policies, except for spam, phishing, and malware" — [README](https://raw.githubusercontent.com/github/transparency/main/data/appeals_and_other_reinstatements/README.md). The 2022 report uses the same definition — [2022 Transparency Report](https://github.blog/news-insights/policy-news-and-insights/2022-transparency-report/).
- A 2026 first-person report describes a suspension from late July to 17 September 2026 (about seven to eight weeks) followed by reinstatement, and a commenter says a repository "becomes 404 once flagged" — [GitHub Community discussion #208224](https://github.com/orgs/community/discussions/208224).

### Inferences
- **The project's positive class may be defined incorrectly.** If GitSec's account of API behaviour still holds, an API 404 on the numeric ID identifies self-deleted or purged accounts and not blocked ones, while suspended accounts would sit among the "still exists" accounts. GitSec's method routes API 404s out of its data entirely. Its evidence dates from 2018 and the current behaviour is undocumented, so this needs testing, not assuming.
- **Recommended check before relying on the label.** On the 1,000-account pilot, cross-tabulate `GET /user/{id}` against the web profile status of the login that the API returns. API 200 with web 404 would identify blocked accounts under GitSec's rule; a large cell there means the project needs two positive classes. Automated web-profile checks are what Section 7 calls scraping, while API lookups are not, but the open-access condition applies to the resulting publication in both cases.
- Numeric IDs are clearly the right key, because both errors are documented: renames break login lookups, and logins can be reclaimed after 90 days.
- Because GitHub's published statistics exclude spam, phishing and malware, they cannot be used to validate the project's disappearance rates, and no published statistic covers self-deletion.
- Reinstatement and restriction-only states are label noise sources, and access-restricted accounts may stay publicly visible, so they would not appear as disappearance.
- At 5,000 requests per hour, one status check of the 64,864 accounts in the April 2024 hour takes about 13 hours (computed; local measurement of the account count).

### Gaps
- Whether, in 2026, a suspended account returns 200 or 404 on `GET /user/{id}` is undocumented and I did not test it, since that would mean probing specific individuals' accounts.
- I read only the `appeals_and_other_reinstatements` folder of GitHub's transparency data, not the other folders.
- The GitHub Privacy Statement was not read in detail.

## 6. What are the known limitations of GH Archive, and are April 2024 hours affected?

### Takeaway

GH Archive has long-standing, unquantified event loss and severe degradation from May 2025 onward. I found nothing specific to April 2024, and the local April 2024 hour is structurally intact, with PushEvent commit lists truncated at 20 for 0.68% of pushes. The planned 2024 sampling avoids the later collapse.

### Cited Findings

**Documented scope and schema**
- Archives start 2/12/2011 (Timeline API until 12/31/2014, Events API from 1/1/2015). "Each archive contains JSON encoded events as reported by the GitHub API" and only public activity is recorded. The payload "may be updated by GitHub at any point" — [gharchive.org](https://www.gharchive.org/).
- The Events API "will include up to 300 events", only from the past 30 days, and "event latency can be anywhere from 30s to 6h" — [Events API docs](https://docs.github.com/en/rest/activity/events).

**Collection mechanics (code read at current master, so it may differ from April 2024)**
- The crawler polls `https://api.github.com/events?per_page=500` with `PAGE_LIMIT = 500`, re-polling 0.75 seconds after each response, and logs "Missed records.." only if a response has at least 500 new events — [crawler.rb](https://raw.githubusercontent.com/igrigorik/gharchive.org/master/crawler/crawler.rb). The API documents a maximum `per_page` of 100 — [Events API docs](https://docs.github.com/en/rest/activity/events).
- The crawler's `Obfuscate.email` replaces the local part of commit emails with a SHA-1 hash — [obfuscate.rb](https://raw.githubusercontent.com/igrigorik/gharchive.org/master/crawler/obfuscate.rb).

**Issue-tracker evidence of loss (user reports, not official)**
- 2019: only 10,542 distinct SHAs against 75,141 commits in a one-year window for a large mirrored repository; a reply in the thread said "I would expect some events to be missing, but no.. not 6/7th of them" — [#213](https://github.com/igrigorik/gharchive.org/issues/213).
- 2021: events and whole hourly files missing, including 21, 10 and 55 consecutive hours in 2019 and 2020 — [#245](https://github.com/igrigorik/gharchive.org/issues/245).
- 2023: missing PushEvents retrievable from the repository events API — [#290](https://github.com/igrigorik/gharchive.org/issues/290); missing PR and issue events — [#294](https://github.com/igrigorik/gharchive.org/issues/294).
- 2024-03-30: no event exists for repository creation, deletion or going private — [#302](https://github.com/igrigorik/gharchive.org/issues/302).
- 2025 onward: drop in events after 23 May 2025 — [#310](https://github.com/igrigorik/gharchive.org/issues/310); daily rows fell from 2,769,429 (2025-10-08) to 18,906 (2025-10-09) — [#312](https://github.com/igrigorik/gharchive.org/issues/312); WatchEvent capture reported falling from about 95-100% to under 20% in 2026 against the stargazers API — [#320](https://github.com/igrigorik/gharchive.org/issues/320); hourly archives down to about 3k events since 27 Oct 2026 (title only) — [issue list](https://github.com/igrigorik/gharchive.org/issues?q=is%3Aissue+2024-04).
- A commenter's event-ID gap analysis assumes IDs are consecutive, covers only May to June 2025 in its table, and no commenter confirms the assumption — [#310](https://github.com/igrigorik/gharchive.org/issues/310).

**Payload changes**
- GitHub announced on 8 Aug 2025 that Events API push events would lose commit summaries and counts, with `author_association` removed from several events, a brownout on 8 Sep and full implementation on 7 Oct 2025. Removed fields remain in the main REST API — [Changelog](https://github.blog/changelog/2025-08-08-upcoming-changes-to-github-events-api-payloads/).
- Current docs list PushEvent fields as only `repository_id`, `push_id`, `ref`, `head`, `before` — [Event types docs](https://docs.github.com/en/rest/using-the-rest-api/github-event-types).

**April 2024 hour: local measurement on `2024-04-01-15.json`**
- 272,191 events, all IDs unique, 15 event types, every `created_at` within 15:00 to 15:59 UTC, and all 60 minutes present with 4,131 to 4,904 events per minute (mean 4,536.5).
- `actor.id` is present on all events; 64,864 distinct actors and 83,187 distinct repositories. Logins ending in `[bot]` account for 47,250 events (17.4%).
- All 158,172 PushEvents have `size`, `distinct_size` and `commits`. The longest `commits` list is 20; 1,116 pushes list exactly 20 and 1,076 (0.68%) have `size` larger than the list length, so `size` preserves the true count.
- The event-ID span is 1,734,443 against 272,191 events (ratio 0.157). This cannot be read as a capture rate because ID consecutiveness is unconfirmed; for comparison, the first row of the #310 table gives 0.18 for 2025-05-01 (computed).
- Commit emails: of 213,778 addresses containing "@", none has a 40-character hexadecimal local part, so the SHA-1 obfuscation in the current crawler code is not visible in this file. 87,168 are GitHub noreply addresses and 7,646 use example.com. No address values were printed or copied.
- The issue tracker search for "2024-04" returned only #326, #320 and #310, whose titles concern 2025 and 2026 — [issue search](https://github.com/igrigorik/gharchive.org/issues?q=is%3Aissue+2024-04).

### Inferences
- The 2024 hourly files predate the May 2025 degradation and the October 2025 payload change, so those events should not affect them, provided the files were not rebuilt. I found no evidence of rebuilding.
- Sustained throughput in this hour was 75.6 events per second (computed), which is close to what one 100-event page every 0.75 seconds plus request time can capture. Combined with the crawler code, this suggests loss at peak hours is plausible, but it is unmeasured, and the April 2024 pipeline may have differed from the code I read: the code rotates files by processing time, yet every local event falls in the file's own hour.
- Because `created_at` is event time and the API can lag, any per-minute analysis (C3) should use `created_at` and should describe its windows as event-time windows.
- The local commit emails should be treated as personal data until confirmed otherwise. Under Section 7 the research exception covers "public, non-personal information", so dropping email fields at ingestion is the safe default.

### Gaps
- No source quantifies GH Archive's event loss rate for 2024.
- The issue-tracker search shows titles only, so an April 2024 problem described inside a comment could be missed.
- Only one hour was measured locally; the planned 24 sampled hours should each be checked the same way.

## 7. What are the 3-5 works closest to C1, what does each overlap with, and does C1 survive?

### Takeaway

**C1 does not survive as written and needs narrowing.** Its core, account-level labels from GitHub platform status using numeric IDs so renames do not count, was done by GitSec on 10.7 million accounts in 2018 and published at CIKM 2019 and TKDE 2023. What remains defensible is a narrower combination: a long fixed forward horizon from a short public event window, surviving accounts treated as unlabeled, and API 404 as an explicitly different positive class, which GitSec discards.

### Cited Findings

C1 components: (a) account-level label, (b) from later platform status, (c) on GitHub, (d) numeric ID, so renames do not count. Project design elements: (e) long horizon of about 31 months, (f) short input window, (g) survivors unlabeled rather than negative.

| Work | Overlaps with C1 | Does not overlap |
|---|---|---|
| [GitSec, CIKM 2019](https://user.informatik.uni-goettingen.de/~ychen/papers/GitSec-CIKM19.pdf) and [TKDE 2023](https://aaltodoc.aalto.fi/bitstreams/9095077c-3398-4c13-9f15-5130dbe9b9b7/download) | (a) yes, (b) yes, used as the training label, (c) yes, (d) in practice yes: numeric-ID lookup via `api.github.com/user/ID`, login read at crawl time. Also uses GH Archive events | (e) no: about 3 to 12 weeks. (f) no: events from 2015 to May 2018. (g) no: web 200 is "legitimate". Positive class differs: API 200 with web 404. API 404 is discarded as "Invalid user ID". Renames never discussed. Random split only |
| [He et al. 2026](https://cmustrudel.github.io/papers/icse2026fakestars.pdf) | (b) and (c) yes; (a) partly: a 10,000-account sample used for validation; large-scale GH Archive base | Not a prediction task. (d) no: [login-based lookup](https://raw.githubusercontent.com/hehao98/StarScout/main/scripts/analysis/get_stargazer_info.py), so renames count as deleted. (e) variable and not designed. (f) no. (g) not modelled |
| [Du et al. 2020](https://personal.utdallas.edu/~shao/papers/du_acsac20.pdf) | (a), (b), (c) as post-hoc measurement; uses GH Archive presence to disambiguate a 404 | Status is not a label. (d) no. (e) not stated. (f) no: interval features are minute-scale but computed over multi-year histories. (g) no |
| [Volkova and Bell 2017](https://doi.org/10.1609/icwsm.v11i1.14874) (via OpenAlex) | Same prediction task framing: later deleted or suspended accounts, (a) and (b) | (c) no: Twitter. (d) to (g) not verified |
| [Saeed et al., TROLLMAGNIFIER](https://arxiv.org/pdf/2112.00443) | (a) and (b) as validation; explicitly separates suspended (403) from deleted (404) | (c) no: Reddit. (d) to (g) no or not applicable |

**C2 and C3, at the level I tested them.**
- C2 was not defeated. StarScout's dense-block mining is CopyCatch on one event type (stars) — [Section 3.2](https://cmustrudel.github.io/papers/icse2026fakestars.pdf). GitSec's TKDE version uses user-repository and user-user graphs and event sequences of 14 types — [TKDE](https://aaltodoc.aalto.fi/bitstreams/9095077c-3398-4c13-9f15-5130dbe9b9b7/download). I found no GitHub work combining a multi-event-type tensor, positive-unlabeled learning and cluster-grouped splits (queries below). Evaluation in GitSec, Du et al. and others uses random splits or cross-validation with no group structure described, so the leakage point looks open.
- C3 was not defeated. RABBIT's accuracy-by-event-count bins are the closest analogue — [Section 6.1](https://natarajan-chidambaram.github.io/papers/MSR2024_RABBIT_A_tool_for_identifying_bot_accounts_based_on_their_recent_GitHub_event_history.pdf).

### Inferences

**Plain verdict by claim**
- **C1: already done in its broad form; narrow it.** Saying that GitHub status was used as a label with numeric IDs is not new.
- **C2: survives as a specific combination, with no prior GitHub work found.** Its components (dense-block mining, positive-unlabeled learning, grouped splits) are individually established.
- **C3: survives as an evaluation contribution**, worded in terms of event-time windows on archived data.

**A defensible narrowing of C1 (conditional on the check in Question 5)**
"To our knowledge, this is the first GitHub study to predict later account disappearance, defined as the API returning 404 for the account's durable numeric ID, at a fixed horizon of about 31 months from a short window of public events, while treating surviving accounts as unlabeled." The text should:
- Cite GitSec as prior art for GitHub status labels and numeric-ID collection, and state the difference in positive class.
- Avoid describing the label as "deleted or suspended" until the API and web cross-tabulation is done.
- Claim an improvement over He et al. and Du et al. on rename handling only, because GitSec already avoids rename errors by construction.

**Additional points for the writer**
- Activity-matched analysis ("among equally active accounts") appears open. GitSec's 21.50% overall against 1.92% among users with at least three events shows that activity filtering changes the base rate sharply, though for a different positive class than the project's. The pilot's rising rate with activity (0.8% to 39.2%) runs in the opposite direction, which is worth reporting and explaining rather than assuming comparability.
- Disappearance is not equivalent to abuse. The 2025 survey's warning applies directly, and it supports the project's positive-unlabeled framing.
- Report the StarScout baseline discrepancy with care, as a recomputation from the authors' public artefacts that the authors have not confirmed.

### Gaps

#### Search log (for all absence claims; run 2026-11-10)

Absence claims here mean "not found by these queries". Screening was by title and abstract of top-ranked results, so these are not proof of absence.

**WebSearch queries** (queries 10, 11 and 12 were restricted to GitHub-owned domains; the rest were unrestricted)
1. `StarScout fake stars GitHub He et al. 4.5 million suspected fake stars`
2. `deleted GitHub accounts label detection suspended account 404 API malicious accounts study`
3. `Check Point Stargazers Ghost Network GitHub accounts`
4. `predicting GitHub account suspension or deletion machine learning GH Archive abusive accounts`
5. `GitHub spam accounts detection dataset "GH Archive" fake accounts promotion malicious repositories`
6. `GHTorrent users table "deleted" flag fake accounts GitHub spam detection`
7. `GitHub accounts "no longer exist" OR "have been deleted" OR "were suspended" fake accounts detection arXiv ground truth validation repositories removed`
8. `developer churn prediction GitHub activity machine learning turnover open source early prediction`
9. `GitHub Events API missing events GH Archive data loss PushEvent commits truncated 20 commits payload change 2025`
10. `GitHub changelog 2025 events API payload changes commits removed PushEvent deprecation`
11. `GitHub transparency report account suspension statistics Terms of Service violations accounts restored`
12. `GitHub docs deleting personal account username available ghost user; suspended flagged account profile hidden`
13. `"Detecting Malicious Accounts in Online Developer Communities Using Deep Learning" Gong Chen GitHub CIKM`
14. `RABBIT tool identifying bot accounts GitHub event history activity sequences Events API`
15. `predicting developer disengagement or dropout open source GitHub activity features machine learning study`
16. `GitHub DMCA takedown repositories empirical study 451 removed repositories dataset`
17. `detecting malicious GitHub repositories malware campaign dataset repositories removed by GitHub later checked deleted arXiv 2025`
18. `GitHub 2025 transparency report accounts hidden restricted abuse Acceptable Use Policies figures`
19. `"GH Archive" OR "GHArchive" detect accounts single hour OR one-day window classification short observation window GitHub users early detection`

**OpenAlex works search** (`search=` parameter, `from_publication_date:2019-01-01`, top 10 to 12 by relevance)
- `GitHub account suspended prediction`
- `"GitHub" "deleted accounts"` (this surfaced GitSec)
- `"GitHub" "suspended accounts"`
- `"GitHub" "banned accounts"`
- `GitHub accounts deleted or suspended later label classifier`
- `GH Archive account classification fake malicious`
- `GitHub fake accounts detection machine learning`
- `GitHub positive-unlabeled learning accounts`
- `GitHub coordinated inauthentic behavior accounts`
- `GitHub malicious repositories taken down removal measurement`
- `GitHub dense subgraph detection fake accounts`
- `GitHub tensor dense block anomaly accounts repositories`
- `GitHub lockstep behavior detection accounts`
- `GitHub account activity early detection observation window`
- `GitHub short time window classification of accounts events`
- `GitHub user account lifetime survival analysis deleted`
- `GitHub platform moderation account removal empirical`
- `"GitHub" "deleted users" dataset`
- `detecting fake developer accounts GitHub profile activity`

**OpenAlex forward citations screened by title** (`filter=cites:`): W2987246247 (GitSec CIKM, 24 works), W3111184121 (Du et al., 11 works), W7212252056 (He et al., 25 works).

**arXiv API** (`search_query`, with total results): `abs:GitHub AND abs:"suspended"` (4); `abs:GitHub AND abs:"banned"` (6); `abs:GitHub AND abs:"deleted" AND abs:account` (1); `abs:GitHub AND abs:"fake accounts"` (2); `abs:GitHub AND abs:spam AND abs:account` (0); `abs:GitHub AND abs:"malicious accounts"` (0); `abs:GitHub AND abs:"GH Archive" AND abs:detect` (0); `abs:GitHub AND abs:"positive-unlabeled"` (1); `abs:GitHub AND abs:"inauthentic"` (1); `abs:GitHub AND abs:"coordinated" AND abs:accounts` (9); `abs:GitHub AND abs:"account deletion"` (1); `abs:GitHub AND (abs:"churn" OR abs:"turnover") AND abs:predict AND abs:developer` (0). None returned a relevant GitHub account-status study.

**GH Archive issue tracker:** `is:issue missing` (61 results, first 25 reviewed) and `is:issue 2024-04` (3 results).

**Not usable or not run.** DBLP's search API returned HTTP 429 and then non-JSON errors for every query, so no absence claim relies on DBLP. Semantic Scholar was not queried. No Chinese-language databases were searched.

#### Unverified

Items below could not be opened or were seen only in search-tool summaries. Do not cite them as verified.
- **Unverified:** a personal blog post at `pilot2254.github.io/blog/how-github-suspended-me/` (fetch returned HTTP 404) reportedly says a suspended account's user ID lookup returned 404 before reinstatement. If real, this bears directly on the Question 5 conflict.
- **Unverified:** Samuel Utzinger, "Early Forecasting of Developer Inactivity in Open Source Projects," ICSE-Companion 2026, DOI 10.1145/3774748.3787756. Title, author and venue come from an OpenAlex record, but the ACM page returned HTTP 403 and no abstract was available, so its content is unverified.
- **Unverified:** the Socket blog "3.7 Million Fake GitHub Stars" (search result only).
- **Unverified:** the GitHub Transparency Center live totals: the page is client-rendered, and the figures from search snippets ("19,035 accounts hidden, 17,596 accounts restricted") were not confirmed. Use the CSV instead.
- **Unverified:** a reported June 2025 GitHub restoration incident affecting about 12,285 managed accounts, seen only via a search summary of a dev.to post.
- **Unverified:** the Enterprise Server docs' older PushEvent schema with `size` and `commits`, seen only in a search summary. The local measurement covers this point for April 2024.
- **Unverified:** claims from search summaries that Twitter returns error code 63 for suspended accounts (arXiv 1804.04406) and on the operating details of "BIMBAS" (Chidambaram et al.). Neither was opened.
- **Abstract-level only (read via OpenAlex, full text not read):** Thomas et al. 2011; Volkova and Bell 2017; Shevtsov et al. 2023; Toraman et al. 2022; Bao et al.; Eluri et al. 2021; Calefato et al. 2022; Qian et al. 2022.
