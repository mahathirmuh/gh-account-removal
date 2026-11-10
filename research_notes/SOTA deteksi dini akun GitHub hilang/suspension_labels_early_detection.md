# Later suspension/deletion as labels, and early detection of abusive accounts, on platforms other than GitHub

Conventions. Everything cited was opened in this session unless it sits under a heading "Unverified". "(computed)" marks my own arithmetic on numbers from the source. Locations (abstract, §, table) refer to the copy I read, which was usually text-extracted from a PDF, so flattened tables are flagged where it matters. AAAI's OJS site (ojs.aaai.org) serves a bot wall to automated clients. I did not try to defeat it; for those open-access AAAI items I read the Internet Archive's stored copy of the same document, marked "Wayback copy". Today is 2026-11-10. Dates for preprints are arXiv dates. Project facts (GitHub 404 merges deletion and suspension, pilot rates, 31-month gap) come from the assignment and were not independently checked here.

## 1. Which studies use later suspension, deletion or ban as a label to predict from earlier behavior?

### Takeaway
Yes, this is a well-established design: retrospective status labels go back to at least 2011 on Twitter, and prediction of "to-be-deleted or suspended" accounts from earlier behavior is explicit in Volkova and Bell (2017). Bans as prediction targets appear on Wikipedia and news forums from 2015, and Facebook and WeChat use internal fake-account labels. On Mastodon/Fediverse I found no account-level ban prediction study (see search log under Question 5).

### Cited Findings

**Comparison table (verified entries; details in the cards below).**

| Study | Platform | Label source and check timing | Deletion vs suspension separated? | Positive rate | Predictive? | Headline result |
|---|---|---|---|---|---|---|
| Thomas et al. 2011 | Twitter | API "no record" then web redirect to `/suspended`, 2 weeks after 7-month collection | Yes | 3.3% (1.1M of 32.9M) | No (measurement) | 77% suspended ≤1 day after first tweet, 92% ≤3 days |
| Klausen et al. 2016 | Twitter | Suspended as of 23 Sep 2015 for accounts collected Jun 2015 | Not addressed in text read | 5.4% | Yes | AUC ≈ 0.83, new-account features only |
| Volkova & Bell 2017 | Twitter | API check Jan 2016 of Sep–Dec 2015 activity; Russian re-crawls Mar→Jun→Dec 2015 | Yes (API) | Balanced by design | Yes (D, S, ND) | F1 up to 0.92 (DS vs ND) |
| Cheng et al. 2015 | CNN, Breitbart, IGN (Disqus) | Platform-supplied banned-user list | N/A | 3.3%, 2.2%, 1.7% | Yes, first 10 posts | Mean AUC 0.82 matched on activity, 0.87 unmatched |
| Kumar et al. 2015 (VEWS) | Wikipedia | Blocked by admins Jan 2013–Jul 2014 | N/A | Balanced (17,027 vs 16,549) | Yes, first k edits | Accuracy 87.82%; first edit alone 77.4% |
| Alfifi & Caverlee 2017 | Twitter (Arabic) | Eventually suspended (2015 accounts) | Method not extracted | 23% of active accounts | Yes (balanced tasks) | 82% accuracy, 90% AUC from first 10% of lifetime |
| Zheng et al. 2019 (SAFE) | Twitter, Wikipedia | Status monitored every 3 days, Aug–Oct 2017 | Not addressed | 15.0% (Twitter) | Yes, survival model | F1 0.6537 Twitter, 0.7866 Wikipedia (avg @1–@5) |
| Kumar et al. 2019 (JODIE) | Reddit, Wikipedia | Ground-truth ban labels at interaction level | N/A | 0.05%, 0.14% of interactions | Yes | AUC 0.599 (Reddit), 0.831 (Wikipedia) |
| Seyler et al. 2021 | Twitter | Web redirect check of accounts from 2009 corpus | Suspension only | 5.1% before balancing | Yes, sliding windows | >80% accuracy with 10 tweets; 78% at 15 tweets earlier |
| Kapoor et al. 2021 | Twitter | Suspended as of 29 Jun 2019, re-checked 8 Oct 2019 | Suspended vs restored | 2.8% of 2.2M | Yes (3 classes) | F1 0.84 suspended vs normal |
| Shevtsov et al. 2023 (BotArtist v1) | Twitter | API compliance; suspended >6 months, recovered accounts removed | Not addressed | 4.04% (computed) | Yes | Hold-out ROC-AUC 0.796 |
| Çetinkaya & Elmas 2025 | Twitter/X | Withheld status (not suspension) | N/A | Constructed dataset | Yes | F1 0.73, AUC 0.83 |

**Cards (for the SOTA table).**

- **Thomas, Grier, Song, Paxson (2011), "Suspended accounts in retrospect: an analysis of Twitter spam", IMC 2011, DOI [10.1145/2068816.2068840](https://doi.org/10.1145/2068816.2068840) (author order per Crossref).** [Paper PDF](https://people.eecs.berkeley.edu/~dawnsong/papers/2011%20Suspended%20accounts%20in%20retrospect%20an%20analysis%20of%20Twitter%20spam.pdf).
  - Data and labels: 1.8B tweets from 32.9M accounts via streaming API, 17 Aug 2010 to 4 Mar 2011; they wait two weeks after collection ends "due to delays in Twitter's account suspension algorithm", then a bulk API query finds accounts with no record (deleted or suspended), and each missing profile is requested on the web to catch redirects to `twitter.com/suspended` (§3, Methodology) — [PDF](https://people.eecs.berkeley.edu/~dawnsong/papers/2011%20Suspended%20accounts%20in%20retrospect%20an%20analysis%20of%20Twitter%20spam.pdf).
  - Positive rate: 1.1M suspended, roughly 3.3% of accounts (§3) — [PDF](https://people.eecs.berkeley.edu/~dawnsong/papers/2011%20Suspended%20accounts%20in%20retrospect%20an%20analysis%20of%20Twitter%20spam.pdf).
  - Result type: measurement with no predictive model. 77% of spam accounts are suspended within a day of their first post, 92% within three days (Abstract; Fig. 4, sample of 100,000 accounts) — [PDF](https://people.eecs.berkeley.edu/~dawnsong/papers/2011%20Suspended%20accounts%20in%20retrospect%20an%20analysis%20of%20Twitter%20spam.pdf).
  - Limitations stated: suspension removes history, so activity is rebuilt only from the sampled stream (§3) — [PDF](https://people.eecs.berkeley.edu/~dawnsong/papers/2011%20Suspended%20accounts%20in%20retrospect%20an%20analysis%20of%20Twitter%20spam.pdf).

- **Volkova, Bell (2017), "Identifying Effective Signals to Predict Deleted and Suspended Accounts on Twitter Across Languages", ICWSM 2017, pp. 290–298, DOI [10.1609/icwsm.v11i1.14874](https://doi.org/10.1609/icwsm.v11i1.14874).** Pages per [OSTI record](https://www.osti.gov/biblio/1440690); text read from [Wayback copy](https://web.archive.org/web/20240111165300id_/https://ojs.aaai.org/index.php/ICWSM/article/download/14874/14724).
  - Labels: English/Spanish tweets from the 1% feed for 1 Sep–30 Dec 2015, then in January 2016 batches of users were queried against the API; active profiles became non-deleted, missing profiles became deleted, and a further API query separated user deletion from suspension (Data section) — [Wayback copy](https://web.archive.org/web/20240111165300id_/https://ojs.aaai.org/index.php/ICWSM/article/download/14874/14724). Time gap is therefore about 1 to 4 months (computed).
  - Russian data: re-crawl in Jun 2015 of a 1M random sample from Mar 2015 found 30% no longer active; re-crawl in Dec 2015 confirmed still-non-active accounts as DS = 94,170, with 94,170 matched active accounts (Data section) — [Wayback copy](https://web.archive.org/web/20240111165300id_/https://ojs.aaai.org/index.php/ICWSM/article/download/14874/14724).
  - Class counts (Table 1): English D 82,435, S 17,565, ND 100,000; Spanish D 91,161, S 8,839, ND 100,000; Russian D 13,845, S 80,325, ND 94,170 — [Wayback copy](https://web.archive.org/web/20240111165300id_/https://ojs.aaai.org/index.php/ICWSM/article/download/14874/14724). No natural base rate is reported for the prediction task; DS vs ND is balanced by construction.
  - Features and model: profile, syntax/style, n-grams, LSA, topics, embeddings, hashtags/mentions, sentiment/emotion, image features; log-linear models and LSTM, 10-fold CV (Table 2, Table 3) — [Wayback copy](https://web.archive.org/web/20240111165300id_/https://ojs.aaai.org/index.php/ICWSM/article/download/14874/14724).
  - Metrics (Table 3, F1, read from flattened layout): DS vs ND log-linear Tweets 0.88 English, 0.87 Russian, 0.79 Spanish; LSTM Tweets+Network 0.85 English, 0.92 Russian, 0.80 Spanish; deleted vs suspended (D-S) LSTM 0.95 English, 0.98 Russian — [Wayback copy](https://web.archive.org/web/20240111165300id_/https://ojs.aaai.org/index.php/ICWSM/article/download/14874/14724).
  - Limitations: I found no dedicated limitations section in the text read; the authors note comparison with other systems "is not fair" because the data differ (Comparison section) — [Wayback copy](https://web.archive.org/web/20240111165300id_/https://ojs.aaai.org/index.php/ICWSM/article/download/14874/14724).

- **Seyler, Tan, Li, Zhang, Li (2021), "Textual Analysis and Timely Detection of Suspended Social Media Accounts", ICWSM 2021, pp. 644–655, DOI [10.1609/icwsm.v15i1.18091](https://doi.org/10.1609/icwsm.v15i1.18091).** Text read from [Wayback copy](https://web.archive.org/web/20260502120329id_/https://ojs.aaai.org/index.php/ICWSM/article/download/18091/17894).
  - Labels: corpus of ~467M tweets from 20M users, Jun–Dec 2009 (Yang & Leskovec 2011); suspended status obtained by requesting each account's URL and checking redirect to `twitter.com/account/suspended`; since the suspension date cannot be inferred, suspended accounts that tweeted after 1 Dec 2009 are removed; accounts created after 31 Dec 2009 are removed; minimum 20 tweets (§3.1) — [Wayback copy](https://web.archive.org/web/20260502120329id_/https://ojs.aaai.org/index.php/ICWSM/article/download/18091/17894).
  - Positive rate: 5.1% suspended before undersampling; final balanced set 83,321 suspended and 83,321 regular (Table 4), split by account into 80/10/10 — [Wayback copy](https://web.archive.org/web/20260502120329id_/https://ojs.aaai.org/index.php/ICWSM/article/download/18091/17894).
  - Deletion: only suspension is modelled in what I read; the date of the status crawl is not stated, so the feature-label gap is not verified.
  - Models: SVM, CNN, LSTM variants, CNN-LSTM, BERT, with statistical features ("+all") (§5) — [Wayback copy](https://web.archive.org/web/20260502120329id_/https://ojs.aaai.org/index.php/ICWSM/article/download/18091/17894).
  - Metrics: accuracy above 80% with only 10 tweets at inference, and 78% accuracy "15 tweets earlier than Twitter" (Introduction); sliding window W=10 moved back from the suspension point in steps of 5, accuracy 0.8134 to 0.668 for its top model (named CNN-LSTM+all in the adjacent text) and 0.8057 to 0.661 for CNN; F1 for CNN+all falls from 0.7990 at [-10,0] to 0.7276 at [-50,-40] (§6.3, Table 5) — [Wayback copy](https://web.archive.org/web/20260502120329id_/https://ojs.aaai.org/index.php/ICWSM/article/download/18091/17894).
  - Limitations: tweets are "an imperfect representation of time"; the setup does not re-create Twitter's automated detection because suspensions are partly user reported; models trained on 2009 data "might not perform as effectively" if deployed now (§5.4 and footnotes) — [Wayback copy](https://web.archive.org/web/20260502120329id_/https://ojs.aaai.org/index.php/ICWSM/article/download/18091/17894).

- **Klausen, Marks, Zaman (2016), "Finding Online Extremists in Social Networks", arXiv:1610.06242.** [arXiv PDF](https://arxiv.org/pdf/1610.06242).
  - Labels: any account suspended by Twitter is labelled extremist; of 646,961 accounts collected in Jun 2015, 35,080 (5.4%) were suspended as of 23 Sep 2015 (§2–3) — [arXiv PDF](https://arxiv.org/pdf/1610.06242).
  - Features/model: account metadata and connections, restricted to what can be measured for an unseen new account, with logistic regression; AUC ≈ 0.83, about 60% of suspended users at 10% FPR (§3) — [arXiv PDF](https://arxiv.org/pdf/1610.06242).
  - Limitations: non-suspended accounts may still be suspended later or should be but evaded detection; sampled false positives included ISIS supporters as well as researchers and media (§3) — [arXiv PDF](https://arxiv.org/pdf/1610.06242).
  - Identity handling: accounts are tracked by Twitter user ID, "which does not change even if a user changes his or her screen name" (§4, before §4.4) — [arXiv PDF](https://arxiv.org/pdf/1610.06242).

- **Cheng, Danescu-Niculescu-Mizil, Leskovec (2015), "Antisocial Behavior in Online Discussion Communities", ICWSM, DOI [10.1609/icwsm.v9i1.14583](https://doi.org/10.1609/icwsm.v9i1.14583) (Crossref shows issued 2021; Semantic Scholar lists 2015).** [arXiv PDF](https://arxiv.org/pdf/1504.00680).
  - Labels and rate: Disqus supplied a complete trace (Mar 2012–Aug 2013) and a list of banned users; banned shares are 3.3% CNN (37,627), 1.7% IGN (5,706), 2.2% Breitbart (5,350) (Table 1) — [arXiv PDF](https://arxiv.org/pdf/1504.00680).
  - Design: Future-Banned Users are matched to similarly active Never-Banned Users; the task observes the first ten posts and predicts eventual banning; balanced N = 18,758 CNN, 1,164 IGN, 1,138 Breitbart; random forest, 10-fold CV — [arXiv PDF](https://arxiv.org/pdf/1504.00680).
  - Metrics: mean AUC 0.82, accuracy 0.74, F1 0.71 (matched); mean AUC 0.87 against all other users; without moderator features 0.79; proportion of deleted posts alone 0.73; bag-of-words 0.69 (§Predicting, Table 4; per-community full model CNN 0.84, IGN 0.83, Breitbart 0.78) — [arXiv PDF](https://arxiv.org/pdf/1504.00680).
  - Limitations: a finer-grained labelling may reveal more behaviors; covert antisocial behavior may differ from overt behavior (Discussion & Conclusion) — [arXiv PDF](https://arxiv.org/pdf/1504.00680).

- **Kumar, Spezzano, Subrahmanian (2015), "VEWS: A Wikipedia Vandal Early Warning System", KDD 2015, DOI [10.1145/2783258.2783367](https://doi.org/10.1145/2783258.2783367).** [arXiv PDF](https://arxiv.org/pdf/1507.01272).
  - Labels: 17,027 users blocked for vandalism by Wikipedia administrators, Jan 2013–Jul 2014, against 16,549 random non-blacklisted users (balanced) (§3) — [arXiv PDF](https://arxiv.org/pdf/1507.01272).
  - Metrics: VEWS accuracy 87.82% (10-fold, Table 2); on average flags a vandal after 2.13 edits vs 3.78 for ClueBot NG (Introduction); first-k-edits curve described under Question 3 below — [arXiv PDF](https://arxiv.org/pdf/1507.01272).

- **Zheng, Yuan, Wu (2019), "SAFE: A Neural Survival Analysis Model for Fraud Early Detection", AAAI 2019, DOI [10.1609/aaai.v33i01.33011278](https://doi.org/10.1609/aaai.v33i01.33011278).** [arXiv PDF](https://arxiv.org/pdf/1809.04683).
  - Data: Twitter, 51,608 users monitored every 3 days from 13 Aug to 13 Oct 2017 (21 timestamps); 7,790 (15.0%) suspended, 43,818 right-censored; balanced subset 2,770/2,770. Wikipedia: 1,759 users from UMDWikipedia (Experimental Settings) — [arXiv PDF](https://arxiv.org/pdf/1809.04683).
  - Metrics (Table 1, average of @1 to @5): SAFE precision 0.8198, recall 0.5569, F1 0.6537, accuracy 0.7180 on Twitter; F1 0.7866, accuracy 0.7640 on Wikipedia — [arXiv PDF](https://arxiv.org/pdf/1809.04683).

- **Kumar, Zhang, Leskovec (2019), JODIE, KDD 2019, DOI [10.1145/3292500.3330895](https://doi.org/10.1145/3292500.3330895).** [arXiv PDF](https://arxiv.org/pdf/1908.01207).
  - Reddit bans: 366 positive labels among 672,447 interactions (0.05%); Wikipedia bans: 217 among 157,474 (0.14%). Table 4 AUC (flattened text): JODIE 0.599 Reddit, 0.831 Wikipedia. Labels are on interactions, not accounts (Experiment 2) — [arXiv PDF](https://arxiv.org/pdf/1908.01207).

- **Alfifi, Caverlee (2017), "Badly Evolved? Exploring Long-Surviving Suspicious Users on Twitter", SocInfo, DOI [10.1007/978-3-319-67217-5_14](https://doi.org/10.1007/978-3-319-67217-5_14).** [Author PDF](https://people.engr.tamu.edu/caverlee/pubs/alfifi17socinfo.pdf).
  - Scale: Arabic Twitter 2015, 26.7M accounts, 6.2M eventually suspended (23% of active accounts); 17,909 long-surviving suspended accounts studied (Fig. 1, Introduction). Balanced tasks, accuracy (AUC) 85% (93%), 86% (92%), 88% (94%) (§4); from the first 10% of account lifetime, 82% accuracy, 90% AUC (Conclusion) — [Author PDF](https://people.engr.tamu.edu/caverlee/pubs/alfifi17socinfo.pdf).

- **Kapoor, Jain, Prabhu, Karandikar, Kumaraguru (2021), "I'll be back: Examining Restored Accounts On Twitter", WI-IAT, DOI [10.1145/3486622.3493959](https://doi.org/10.1145/3486622.3493959).** [arXiv PDF](https://arxiv.org/pdf/2111.12395). 56,927 accounts (2.8% of 2.2M) were suspended as of 29 Jun 2019; re-query on 8 Oct 2019 found 1,626 active again (§3); F1 0.84008 suspended vs normal, 0.71242 restored vs normal (Table 6) — [arXiv PDF](https://arxiv.org/pdf/2111.12395).

- **Shevtsov, Antonakaki, Lamprou, Pratikakis, Ioannidis (2023), BotArtist, arXiv:2306.00037.** [v1 PDF](https://arxiv.org/pdf/2306.00037v1). The v1 title reads "based on Twitter suspension"; 343,322 suspended ("bots", kept only if suspended for more than six months) vs 8,159,204 normal, with accounts that were suspended and recovered removed; XGBoost, hold-out ROC-AUC 0.796, profile features only (Dataset section, §Results) — [v1 PDF](https://arxiv.org/pdf/2306.00037v1). The latest [arXiv version](https://arxiv.org/abs/2306.00037) reframes this around nine public datasets.

- **Çetinkaya, Elmas (2025), "State & Geopolitical Censorship on Twitter (X)", arXiv:2508.13375.** [arXiv PDF](https://arxiv.org/pdf/2508.13375). Predicts withholding (not suspension) from up to 50 tweets per user; 2,227 withheld and 3,156 non-withheld accounts; F1 0.73, AUC 0.83 (Abstract, §4). Limitation: 1%/10% samples and matched controls on follower counts only — [arXiv PDF](https://arxiv.org/pdf/2508.13375).

**Characterization studies with later-status labels but no predictive model (useful for label validity).**
- Toraman, Şahinuç, Yilmaz (2022), WebSci, DOI [10.1145/3501247.3531539](https://doi.org/10.1145/3501247.3531539): 500,234 users, tweets collected 7 Apr–15 Jun 2020, account status checked December 2020 and split into active, deleted, suspended (mechanism not stated in text read); Table 1 gives Deleted 66,775 + 3,982 and Suspended 54,839 + 4,646 — [arXiv PDF](https://arxiv.org/pdf/2110.00070).
- Chowdhury, Saha, Hasan, Saha, Mueen (2021), ASONAM: 355,573 suspended users from about 21M election-discussing users, comparing suspended with "(yet) non-suspended" controls; suspended users are short-lived with fewer followers (Introduction) — [arXiv PDF](https://arxiv.org/pdf/2101.09575).
- Pierri, Luceri, Chen, Ferrara (2023), EPJ Data Science, DOI [10.1140/epjds/s13688-023-00420-7](https://doi.org/10.1140/epjds/s13688-023-00420-7): 270M tweets by 16M users; almost 2M suspended identified on 23 May via the compliance endpoint (Methods) — [arXiv PDF](https://arxiv.org/pdf/2209.07614).

**Other platforms.**
- Reddit: I found ban labels only at interaction level in JODIE (above), not a dedicated account-level "who will be banned" study (search log under Question 5).
- Facebook: SybilEdge trains on labels from Facebook's internal classifiers, with a calibrated label for accounts older than 30 days (§3.1) — [arXiv PDF](https://arxiv.org/pdf/2004.04834).
- Telegram: La Morgia, Mei, Mongardini, Wu (arXiv:2111.13530, whose front page points to published successors at ICWS 2023 and ACM TWEB 2024) study 35,382 channels and Telegram's own verified and scam marks; fake-channel classifier accuracy 86%, weighted F1 85.7%, on channels rather than user accounts (Abstract, §5) — [arXiv PDF](https://arxiv.org/pdf/2111.13530).
- Mastodon/Fediverse: FedMod (Bin Zia, Raman, Castro, Tyson, 2025) uses Perspective API scores as a proxy for administrator labels and states that human labels by real administrators "would be preferable" but are not available (§3.1.3) — [arXiv PDF](https://arxiv.org/pdf/2501.05871). Colglazier, TeBlunthuis, Shaw (2024) and Damie, Cyffers (2025) work at server-level defederation, not account suspension — [arXiv 2404.02109](https://arxiv.org/abs/2404.02109); [arXiv 2505.20882](https://arxiv.org/abs/2505.20882).

### Inferences
- The target in C1 is structurally the same as Volkova and Bell's DS-vs-ND task: "existed earlier, gone later", merging deletion and suspension. The difference is platform and that the GitHub 404 cannot be split afterwards the way Twitter statuses could.
- Positive rates in comparable account-level studies (1.7–5.4% before balancing) are close to the project's lower activity buckets, which makes the 39.2% bucket the unusual one.
- Most predictive studies balance positives 1:1, so their AUC and accuracy figures are not comparable with an unbalanced PU evaluation on the natural rate.

### Gaps
- I could not confirm when Seyler et al. ran the status crawl; the feature-label gap in that study is therefore not verified.
- No study I read reports natural base rates of deletion alone vs suspension alone for general-population accounts over a long horizon.

### Unverified
- Xiao, Freeman, Hwa (2015), "Detecting Clusters of Fake Accounts in Online Social Networks", AISec, DOI [10.1145/2808769.2808779](https://doi.org/10.1145/2808769.2808779) (metadata confirmed in Crossref; abstract excerpts seen on [Sciweavers](https://sciweavers.org/publications/detecting-clusters-fake-accounts-online-social-networks)). Metric figures (AUC 0.98/0.95, 250,000 accounts) came only from a search-engine summary. Unverified.
- Cola, Mazza, Tesconi: study of new-account detection seconds after registration; the [CNR PDF](https://iris.cnr.it/retrieve/b944b0d6-f2c7-4a3c-a344-60fe4a391880/prod_489466-doc_203838.pdf) returned HTTP 403 and details came from a search summary. Unverified.
- Chowdhury, Allen, Yousuf, Mueen (2020), "On Twitter Purge: A Retrospective Analysis of Suspended Users", WWW Companion, DOI [10.1145/3366424.3383298](https://doi.org/10.1145/3366424.3383298): the author PDF returned HTTP 403. Metadata is confirmed in Crossref; methods (two snapshots of about 560M users, 2.4M purged users, API error code 63) are known only from the secondary [WS-DL blog summary](https://ws-dl.blogspot.com/2023/01/2023-01-18-paper-summary-on-twitter.html). Primary text unverified.
- Le et al. (2019), Majó-Vázquez et al. (2021) and Wei et al. (2015) are cited inside Pierri et al. and Seyler et al. as suspended-account studies; none of these was opened. Unverified. Seyler et al. report, citing Wei et al. (2015), that half of the Twitter accounts created in 2014 were ultimately suspended.

## 2. What validity problems does the literature document for suspension-as-ground-truth, and what mitigations are used?

### Takeaway
Every threat listed in the assignment is documented: self-deletion mixing, false positives and reversals, false negatives, label delay, policy-driven selection, and temporal drift. Mitigations are mostly operational: waiting periods, repeated status checks, persistence filters, manual audits of samples, and matched controls. I found no study that quantifies how label validity changes with horizon length at the scale of years.

### Cited Findings
**Self-deletion mixed with suspension.**
- The share of suspensions among disappeared accounts varied strongly by sample in Volkova and Bell: 17.6% English, 8.8% Spanish, 85.3% Russian (computed from Table 1) — [Wayback copy](https://web.archive.org/web/20240111165300id_/https://ojs.aaai.org/index.php/ICWSM/article/download/14874/14724).
- Deletion vs suspension can be told apart on Twitter through a web redirect ([Thomas et al.](https://people.eecs.berkeley.edu/~dawnsong/papers/2011%20Suspended%20accounts%20in%20retrospect%20an%20analysis%20of%20Twitter%20spam.pdf)) or an API error code 63 (according to the secondary [WS-DL summary](https://ws-dl.blogspot.com/2023/01/2023-01-18-paper-summary-on-twitter.html) of Chowdhury et al. 2020).
- LSTM models separated deleted from suspended accounts with F1 0.95 to 0.98, which suggests different behavior in the two groups (Table 3) — [Wayback copy](https://web.archive.org/web/20240111165300id_/https://ojs.aaai.org/index.php/ICWSM/article/download/14874/14724).

**False positives and reversals.**
- Manual analysis estimated that 93% of suspended accounts were spammers, the remaining 7% suspended for mimicking news services and aggressive marketing — [Thomas et al.](https://people.eecs.berkeley.edu/~dawnsong/papers/2011%20Suspended%20accounts%20in%20retrospect%20an%20analysis%20of%20Twitter%20spam.pdf).
- 1,626 of 56,927 suspended accounts were active again about three months later, 2.86% (computed); the authors note suspensions "are sometimes temporary and even incorrect" — [Kapoor et al.](https://arxiv.org/pdf/2111.12395).
- Suspended accounts are often assumed to be bots, and the assumption that they "were suspended because they were bots is only" an assumption — [Overdorf, Schwartz (2020)](https://arxiv.org/pdf/2006.04959).

**False negatives.**
- Of 31M non-suspended accounts, 6% were estimated to be overlooked spam, about 1.9M accounts — [Thomas et al.](https://people.eecs.berkeley.edu/~dawnsong/papers/2011%20Suspended%20accounts%20in%20retrospect%20an%20analysis%20of%20Twitter%20spam.pdf).
- In a manual check of accounts flagged by their classifier among not-suspended accounts, roughly 15% were judged wrongly labelled benign in the gold standard (manual analysis, Table 6) — [Seyler et al.](https://web.archive.org/web/20260502120329id_/https://ojs.aaai.org/index.php/ICWSM/article/download/18091/17894).
- Non-suspended accounts may be suspended later or should have been — [Klausen et al.](https://arxiv.org/pdf/1610.06242).
- GitHub-specific: fewer than 5% of 63,872 suspected promotion accounts had been banned by GitHub at the time of the study — [Du et al. 2020](https://personal.utdallas.edu/~shao/papers/du_acsac20.pdf), DOI [10.1145/3427228.3427258](https://doi.org/10.1145/3427228.3427258).

**Label delay.**
- Thomas et al. waited two weeks after collection specifically because of suspension delays — [PDF](https://people.eecs.berkeley.edu/~dawnsong/papers/2011%20Suspended%20accounts%20in%20retrospect%20an%20analysis%20of%20Twitter%20spam.pdf).
- 87.6% of Seyler's suspended accounts had posted at least 25 tweets before suspension, read as evidence that Twitter does not act immediately (Table 1) — [Wayback copy](https://web.archive.org/web/20260502120329id_/https://ojs.aaai.org/index.php/ICWSM/article/download/18091/17894).
- A two-month lag in Twitter's labeling was reported for the 2020 US election; after six months, 51% of tool-labelled bots had been suspended and 34% removed, against 1.9% and 6.3% of normal accounts — [Shevtsov et al.](https://arxiv.org/pdf/2112.04913), DOI 10.1609/icwsm.v16i1.19349 per Semantic Scholar.
- Retrospective API checks made "with a considerable delay (sometimes years)" prevent determining when and why accounts were suspended, and the API gives no suspension time; Pierri et al. use last appearance as a proxy, with median lifespan of 1 day for new suspended accounts (Introduction, Fig. 6) — [Pierri et al.](https://arxiv.org/pdf/2209.07614).
- Banned forum users survived 42 days on average on CNN, 103 on IGN, 82 on Breitbart — [Cheng et al.](https://arxiv.org/pdf/1504.00680).
- SAFE addresses the gap directly: labels record suspension time, not the time of the fraudulent action, so the survival loss is revised (Abstract) — [SAFE](https://arxiv.org/pdf/1809.04683).

**Selection bias and policy dependence.**
- Twitter's suspension patterns were found not to fit political trolling in the Portuguese Twittersphere — [Ramalho (2021)](https://arxiv.org/abs/2102.04293).
- Account suspensions are the primary factor in data removal, and data persistence differs politically (Abstract) — [Elmas (2023)](https://arxiv.org/pdf/2303.00902), DOI [10.1145/3578503.3583630](https://doi.org/10.1145/3578503.3583630).
- Benchmark bot-detection performance depends heavily on collection and labeling procedures rather than bot vs human differences — [Hays et al. (2023)](https://arxiv.org/pdf/2301.07015), DOI [10.1145/3543507.3583214](https://doi.org/10.1145/3543507.3583214).
- PU learning usually assumes labeled positives are selected completely at random (SCAR); the SAR alternative lets selection depend on attributes, which matches labeling driven by moderation policy — [Bekker, Davis (2020)](https://arxiv.org/pdf/1811.04820), DOI [10.1007/s10994-020-05877-5](https://doi.org/10.1007/s10994-020-05877-5).

**Temporal drift.**
- Pierri et al. note moderation may differ by event and "policies are likely to change over time" (Limitations) — [Pierri et al.](https://arxiv.org/pdf/2209.07614).
- VEWS tests temporal splits (train on prior months, Figure 5) — [VEWS](https://arxiv.org/pdf/1507.01272). Seyler et al. flag decade-old training data as a deployment risk — [Wayback copy](https://web.archive.org/web/20260502120329id_/https://ojs.aaai.org/index.php/ICWSM/article/download/18091/17894).

**Mitigations seen in the literature.**
| Mitigation | Example |
|---|---|
| Wait before labeling | Two-week wait — [Thomas et al.](https://people.eecs.berkeley.edu/~dawnsong/papers/2011%20Suspended%20accounts%20in%20retrospect%20an%20analysis%20of%20Twitter%20spam.pdf) |
| Repeated status checks | Mar, Jun and Dec 2015 re-crawls — [Volkova, Bell](https://web.archive.org/web/20240111165300id_/https://ojs.aaai.org/index.php/ICWSM/article/download/14874/14724) |
| Persistence filter, excluding reversals | Suspended over six months, recovered accounts removed — [BotArtist v1](https://arxiv.org/pdf/2306.00037v1) |
| Exclude accounts near the crawl boundary | Remove suspended accounts tweeting after 1 Dec 2009 — [Seyler et al.](https://web.archive.org/web/20260502120329id_/https://ojs.aaai.org/index.php/ICWSM/article/download/18091/17894) |
| Manual audit of samples | Suspended-account spam check — [Thomas et al.](https://people.eecs.berkeley.edu/~dawnsong/papers/2011%20Suspended%20accounts%20in%20retrospect%20an%20analysis%20of%20Twitter%20spam.pdf); human review of a random sample for production precision (never below 0.97) — [DEC](https://www.usenix.org/system/files/sec21-xu-teng.pdf) |
| Matched controls on activity | FBU/NBU matching — [Cheng et al.](https://arxiv.org/pdf/1504.00680) |
| Robustness to label noise | 0–30% injected noise tests — [SybilEdge](https://arxiv.org/pdf/2004.04834) |

### Inferences
- GitHub's merged 404 is weaker than Twitter's status signal: studies on Twitter could separate deletion from suspension, and the project cannot. This should be stated as a limitation, with a manual audit of a labelled sample as mitigation.
- Du et al.'s finding that under 5% of suspected promotion accounts were banned suggests the unlabeled class may contain many positives, which supports the PU framing and also warns that recall of the "disappeared" signal could be low.
- A long horizon such as 31 months likely increases non-abuse disappearance (account closures, inactivity policy changes) compared with the months-long gaps most studies use. This is an inference; no source I read measured it.
- Because the project samples accounts active in a given hour, accounts suspended within hours or days of creation (the 77% within one day in Thomas et al.) may be systematically underrepresented or overrepresented relative to the population. The direction is unknown and should be examined.

### Gaps
- No source quantified label validity as a function of horizon length (for example 1, 6, 12, 31 months).
- No source measured what share of disappearances on GitHub are self-deletions vs moderation.

## 3. What methods exist for early detection of abusive or fake accounts, and which report performance against observation length?

### Takeaway
The literature distinguishes detection at registration, early detection after a few actions, and detection after extended activity. Performance-versus-observation curves exist, but almost always measured in actions (posts, edits, friend requests) or account age, not wall-clock minutes. Minute-level deadline curves exist in rumor and fake-news detection, for items rather than accounts.

### Cited Findings
**Taxonomy.** Detection time is categorised as at registration, early detection, and after extended activity — [Dehkordi, Zehmakan (2025) survey](https://arxiv.org/pdf/2507.06541).

**At registration.**
- Ianus (Yuan, Miao, Gong, Yang, Li, Song, Wang, Liang, CCS 2019, DOI [10.1145/3319535.3363198](https://doi.org/10.1145/3319535.3363198)): catches Sybils immediately after registration on WeChat; precision over 96% on average by manual verification; recall not stated in the abstract page I read (the page also contains a misplaced paragraph about another paper) — [Project page](http://netsec.ccert.edu.cn/publications/ccs18-ianus).
- UFA is described as an unsupervised at-registration system using a registration-feature graph and community detection — [survey](https://arxiv.org/pdf/2507.06541); performance numbers are under Unverified.

**After first actions.**
- SybilEdge (Breuer, Eilat, Weinsberg, WWW 2020, DOI [10.1145/3366423.3380204](https://doi.org/10.1145/3366423.3380204)): new accounts defined as under 7 days old or under 50 friend requests; AUC rises with the number of requests sent and converges to 0.91 for users sending more than 15; evaluated on accounts as young as 1 day (§3.1, Fig. 2) — [arXiv PDF](https://arxiv.org/pdf/2004.04834).
- PreAttacK (Breuer, Khosravani, Tingley, Cottel, 2023): AUC ≈ 0.9 after 20 not-yet-answered friend requests (Abstract) — [arXiv PDF](https://arxiv.org/pdf/2308.05353).
- Muses (Yang, Wang, Li, Yuan, Liu, Gong, Liu, Li, Liang, Hu, ACSAC 2021, DOI [10.1145/3485832.3488013](https://doi.org/10.1145/3485832.3488013)): first-week action records of about 440k WeChat accounts, labels from WeChat's security team; precision 90%, recall 82%, AUC 0.95 (conference slides) — [Slides](https://www.acsac.org/2021/program/files/acsac21-3a-3.pdf).
- DEC at Facebook (Xu, Goossen, Cevahir, Khodeir, Jin, Li, Shan, Patel, Freeman, Pearce, USENIX Security 2021) classifies abusive accounts using deep features from linked entities, training on over 30M approximate labels and 240,000 human labels (Table 3); AUC 0.90 and recall 50% at precision 0.95 for the multi-stage model (evaluation section) — [PDF](https://www.usenix.org/system/files/sec21-xu-teng.pdf).
- Facebook's report of over 2.2B accounts disabled in Q1 2019, with the vast majority during or within minutes of creation — as cited in [Breuer et al.](https://arxiv.org/pdf/2004.04834).

**Performance as a function of observation length.**
- VEWS Experiment 4: accuracy vs first k edits for k=1 to 500; the first edit alone gives 77.4%, accuracy rises fast to k=10 then flattens; 87.82% at k=500 (Fig. 7) — [arXiv PDF](https://arxiv.org/pdf/1507.01272).
- Cheng et al.: AUC vs first N posts rises as more posts are observed, and users who live longer are harder to identify early; with a sliding five-post window, performance decreases with distance from the ban (Fig. 7a, 7b) — [arXiv PDF](https://arxiv.org/pdf/1504.00680).
- Seyler et al.: accuracy and F1 as a function of the amount of text and of distance before suspension (§5.5, §6.3, Table 5) — [Wayback copy](https://web.archive.org/web/20260502120329id_/https://ojs.aaai.org/index.php/ICWSM/article/download/18091/17894). They deliberately use tweet counts instead of time bins, because uneven bins distort measurements — same source (§5.4).
- SAFE reports performance per early timestep (@1 to @5), and the share of fraudsters detected early by suspension timestamp, for example 92% at timestamp 12 versus 54% for M-LSTM (Tables 1–2, Fig. 4) — [arXiv PDF](https://arxiv.org/pdf/1809.04683).
- Niverthi, Verma, Kumar (2022), WWW, DOI [10.1145/3485447.3512133](https://doi.org/10.1145/3485447.3512133): early evasion detection after k=3 edits, AUC 0.85 (§6.2) — [arXiv PDF](https://arxiv.org/pdf/2202.05257).
- Single-observation limit: Kudugunta, Ferrara (2018), AUC above 96% from a single tweet, on labeled spam-bot datasets — [arXiv PDF](https://arxiv.org/pdf/1802.04289).

**Wall-clock deadlines, cross-domain.**
- Liu, Wu (2018), AAAI, DOI [10.1609/aaai.v32i1.11268](https://doi.org/10.1609/aaai.v32i1.11268): fake-news accuracy 85% and 92% on Twitter and Weibo within 5 minutes after a story starts to spread (Abstract) — [Wayback copy](https://web.archive.org/web/20260305040253/https://ojs.aaai.org/index.php/AAAI/article/view/11268).
- Bian, Xiao, Xu, Zhao, Huang, Rong, Huang (2020), BiGCN, AAAI 2020: early detection using a series of detection deadlines, using only posts released before each deadline (§Early Rumor Detection, Fig. 4; deadline values not extracted) — [arXiv PDF](https://arxiv.org/pdf/2001.06362).

### Inferences
- Windows are defined in three different ways in this literature: account-relative prefixes (first N actions), label-relative windows (the last N posts before a ban), and item-relative deadlines (time since a story started). A wall-clock window applied across all accounts in a sampled hour is a fourth variant. The project should say which it uses, since accounts in an hour differ in event count.
- Seyler's argument against time bins directly challenges a minutes-only design: wall-clock windows give accounts very different event counts, so results should be stratified by activity bucket, which the project already plans.

### Gaps
- I found no account-level study reporting performance at minute granularity (5, 15, 30, 60 minutes); see search log under Question 5.

### Unverified
- UFA (WeChat, at-registration): performance figures (precision about 93–94%, recall about 80%, 500 accounts per day) came from a search-engine summary. The method description is verified via the [survey](https://arxiv.org/pdf/2507.06541); the numbers are unverified.
- DeBot (Chavoshi, Hamooni, Mueen, ICDM 2016): near-real-time warped-correlation bot detection with 94% precision came from a search-engine summary; paper not opened. Unverified.
- GitSec (malicious GitHub accounts, AUC 0.916): search-engine summary only. Unverified.
- Ianus and Muses: full papers not opened. Ianus is cited from its project abstract page and Muses from its conference slides, as labelled above; anything beyond those pages is unverified.

## 4. Which metrics exist for early detection, and which best suits a window-shrinking analysis?

### Takeaway
ERDE and F_latency are the established metrics for sequential early-risk decisions, but they assume each user receives an individual decision at a moment k. For a window-shrinking design, where every account gets the same window length, the better choice is standard threshold-free or fixed-operating-point metrics per window (AP, recall at fixed precision), with time-to-detection statistics as a complement.

### Cited Findings
- **ERDE** (Early Risk Detection Error), introduced by Losada and Crestani, DOI [10.1007/978-3-319-44564-9_3](https://doi.org/10.1007/978-3-319-44564-9_3) (metadata confirmed in Crossref; original not opened): for decision d after k items, cost = c_fp if d=positive and truth negative; c_fn if d=negative and truth positive; lc_o(k)·c_tp if true positive; 0 if true negative; with lc_o(k) = 1 − 1/(1 + e^(k−o)), and o as a deadline — [Burdisso, Errecalde, Montes-y-Gómez (2019), experimental section](https://arxiv.org/pdf/1911.06147); [Trotzek et al. (2018)](https://arxiv.org/pdf/1804.07000). In eRisk 2017, c_fn = c_tp = 1 and c_fp = n_tp/n_u — [Trotzek et al.](https://arxiv.org/pdf/1804.07000).
- **Problems with ERDE**: users with about ten or more messages per chunk (ERDE_5) cannot be predicted correctly because the cost approaches c_fn; optimizing ERDE_5 does not necessarily mean better classification — [Trotzek et al. (metric section and Conclusion)](https://arxiv.org/pdf/1804.07000). ERDE is described as hard to compare across systems — [DeepCare at eRisk 2026](https://ceur-ws.org/Vol-4283/paper136.pdf).
- **ERDE^o%**: cost is based on the percentage of a user's documents read rather than an absolute count, so it grows equally for all users regardless of how many messages they have — [Trotzek et al.](https://arxiv.org/pdf/1804.07000).
- **F_latency** (Sadeque, Xu, Bethard 2018, WSDM, DOI [10.1145/3159652.3159725](https://doi.org/10.1145/3159652.3159725), metadata confirmed; original not opened): F_latency = F1 · (1 − median{ρ(k_u): u ∈ TP}), ρ(k) = −1 + 2/(1 + e^(−γ(k−1))), with γ = 0.0078 used by eRisk organisers — [DeepCare at eRisk 2026](https://ceur-ws.org/Vol-4283/paper136.pdf). It gives a penalty of 0.5 at the median number of posts in the dataset and was adopted by eRisk in 2019 — [Trotzek et al.](https://arxiv.org/pdf/1804.07000); [eRisk 2024 overview](https://tec.citius.usc.es/ir/pdf/ECIR_2024_erisk.pdf).
- **Earliness**: E = (T − t)/T × 100 for an early classifier using t of T points, in early classification of time series — [Gupta et al. (2020) review](https://arxiv.org/pdf/2005.02595).
- **Window-based time-to-detection scoring**: the Numenta Anomaly Benchmark uses anomaly windows and a sigmoidal scoring function that rewards earlier detections — [Lavin, Ahmad (2015)](https://arxiv.org/pdf/1510.03336), DOI [10.1109/icmla.2015.141](https://doi.org/10.1109/icmla.2015.141).
- **Per-window evaluation in accounts**: VEWS uses accuracy at k edits, Cheng et al. AUC at N posts, SAFE precision/recall/F1 at timesteps @1–@5 (sources under Question 3).

### Inferences
- Recommendation for a 60-to-5-minute shrinking analysis: report AP (PR-AUC) and recall at a fixed precision for each window, with bootstrap intervals, stratified by event-count bucket, and using splits grouped by coordination cluster. This matches the way VEWS and Cheng et al. report curves but uses metrics suited to rare positives.
- ERDE and F_latency are poor primary metrics here. Their latency term is per-account, and in a fixed-window design all accounts have the same window, so the latency term becomes a function of window length and adds no new information. They become meaningful only if the study simulates account-specific alerting (a decision made at the first window where a threshold is exceeded), and then latency must be defined in minutes with o or γ chosen for that scale, which is a free parameter that should be justified.
- A useful complement is a time-to-detection distribution: for a chosen precision, the earliest window at which each eventually-disappearing account is flagged. This mirrors SAFE's early-detected percentage and the "suspended within 1 day" framing in Thomas et al.
- Under PU labels, measured precision is against observed disappearance, not true abuse, and this should be stated explicitly when reporting AP.

### Gaps
- No source validated a latency-weighted metric for wall-clock windows on account-level, long-horizon labels; the recommendation above is my inference.

### Unverified
- Original texts of Losada and Crestani (2016, ERDE) and Sadeque, Xu, Bethard (2018, F_latency) were not opened. Their definitions above are taken from papers that I did open (Burdisso et al., Trotzek et al., DeepCare at eRisk 2026) and their bibliographic metadata was confirmed in Crossref. Cite the originals, but check the formulas against them before final use.

## 5. Closest prior work to C1 and C3, overlap, and plain verdicts

### Takeaway
C1 needs narrowing: retrospective account-status labels, including merged deletion-plus-suspension and numeric-ID identity, are established elsewhere, and GitHub account accessibility has already been checked in StarScout and Du et al., though as validation rather than a prediction target. C3 survives only in narrowed form: performance-vs-observation curves are established in action counts and minute-level deadlines exist for rumor items, but I found no account-level, minute-granularity curve for later disappearance from a public event stream. Both are mainly transfers of established ideas, which is a weaker contribution than a new idea and should be stated that way.

### Cited Findings

**C1 — closest works** (account-level retrospective labels from current platform status on GitHub, numeric IDs).

| Work | Overlaps with C1 | Does not overlap |
|---|---|---|
| [Volkova & Bell 2017](https://web.archive.org/web/20240111165300id_/https://ojs.aaai.org/index.php/ICWSM/article/download/14874/14724) | Predicts accounts that later become deleted or suspended, from status checks after a prior observation window; DS merged as one target | Twitter; deletion and suspension separable by API; text-driven features; balanced evaluation, not PU; 1–4 month gap in the main data |
| [Thomas et al. 2011](https://people.eecs.berkeley.edu/~dawnsong/papers/2011%20Suspended%20accounts%20in%20retrospect%20an%20analysis%20of%20Twitter%20spam.pdf) | Retrospective status labels over a stream-collected population, with deletion/suspension separated and manual validity audit | Measurement only, no prediction; Twitter; two-week wait |
| [Seyler et al. 2021](https://web.archive.org/web/20260502120329id_/https://ojs.aaai.org/index.php/ICWSM/article/download/18091/17894) | Labels from later platform status (redirect) for accounts from an older corpus | Twitter; suspension only; text features; balanced; not PU |
| [Klausen et al. 2016](https://arxiv.org/pdf/1610.06242) | Later-status label plus explicit use of stable user IDs across screen-name changes; notes non-suspended accounts may be suspended later | Twitter; extremist-seeded sample; ID use is for linking profiles, not for label construction |
| [He, Yang, Burckhardt, Kapravelos, Vasilescu, Kästner 2024 (StarScout), ICSE 2026](https://arxiv.org/pdf/2412.13459) | GitHub, GH Archive; checks via GitHub API whether accounts remain accessible, reports 57.07% of campaign accounts deleted vs 3.54% baseline | Deletion used to validate a heuristic detector, not as a prediction target; 10,000-account sample; no rename treatment seen in the text read |
| [Du, Yang, Zhang, Duan, Wang, Hao, Li, Yang 2020 (ACSAC)](https://personal.utdallas.edu/~shao/papers/du_acsac20.pdf) | GitHub; checks account homepages for bans of suspected promotion accounts | Validation/measurement, not prediction; under 5% banned |

**C3 — closest works** (detection-latency curve as the window shrinks from 60 to 5 minutes, public event stream only, no per-account API at inference).

| Work | Overlaps with C3 | Does not overlap |
|---|---|---|
| [Cheng et al. 2015](https://arxiv.org/pdf/1504.00680) | Performance vs amount observed (first N posts), sliding windows, later ban label, matched on activity | Posts not minutes; platform-supplied full traces and moderator features |
| [VEWS 2015](https://arxiv.org/pdf/1507.01272) | Accuracy vs first k edits (k=1–500), ban-based labels, explicit early-warning goal | Edits not minutes; full edit logs |
| [Seyler et al. 2021](https://web.archive.org/web/20260502120329id_/https://ojs.aaai.org/index.php/ICWSM/article/download/18091/17894) | Performance vs amount of text and vs distance before suspension, text only at inference | Tweet counts, argues against time bins; label-relative windows |
| [SybilEdge 2020](https://arxiv.org/pdf/2004.04834) and [PreAttacK 2023](https://arxiv.org/pdf/2308.05353) | AUC vs early actions for accounts days old, rapid early detection goal | Private Facebook data; friend requests not minutes |
| [Liu & Wu 2018](https://web.archive.org/web/20260305040253/https://ojs.aaai.org/index.php/AAAI/article/view/11268) and [BiGCN 2020](https://arxiv.org/pdf/2001.06362) | Wall-clock deadlines in minutes with performance reported | Items (stories), not accounts |
| [SAFE 2019](https://arxiv.org/pdf/1809.04683) | Time-indexed early detection with suspension labels and right-censoring | 3-day steps; profile-count features |
| [Kudugunta & Ferrara 2018](https://arxiv.org/pdf/1802.04289) | Inference from a single public post, no account history | Tweet object carries profile metadata; benchmark labels with known issues per [Hays et al.](https://arxiv.org/pdf/2301.07015) |
| [RABBIT (Chidambaram, Mens, Decan), MSR 2024 Data and Tool Showcase](https://2024.msrconf.org/details/msr-2024-data-and-tool-showcase-track/15/RABBIT-A-tool-for-identifying-bot-accounts-based-on-their-recent-GitHub-event-histor) (GitHub) | Classifies GitHub accounts from recent events | Bot vs human; queries GitHub Events API per account (up to 3 queries), so it needs per-account API access that C3 avoids |

**Note on activity stratification.** Cheng et al.'s matching on activity is the closest precedent for the project's main question ("among equally active accounts, what distinguishes..."), with AUC dropping from 0.87 unmatched to 0.82 matched — [arXiv PDF](https://arxiv.org/pdf/1504.00680). Per-activity-quartile AUC reporting appears in a small 2026 arXiv study of 2,432 manually labelled Twitter accounts (behavioral random forest: Q1 0.957 lowest, Q3 0.996 highest; weak evidence, not peer reviewed) — [Katyal 2026](https://arxiv.org/pdf/2606.26127).

**Adjacent to C2 (out of scope here).** StarScout implements CopyCatch lockstep detection on GH Archive — [He et al.](https://arxiv.org/pdf/2412.13459).

### Inferences
**Verdict on C1: needs narrowing.** Do not claim retrospective status labels, merged deletion-plus-suspension targets, or numeric-ID identity as new; these are documented on other platforms, and GitHub status checks exist in StarScout and Du et al. A defensible wording is: "to our knowledge, the first to use later GitHub account disappearance as a prediction target for accounts observed in a short public event window, with numeric-ID matching so renames are not counted, treating still-existing accounts as unlabeled." Present this as a transfer plus a GitHub-specific label audit, not as a new labeling idea.

**Verdict on C3: survives only if narrowed, and is weak as an idea.** Curves of performance against observation amount exist since at least 2015 for accounts, and minute-level deadlines exist for rumors. A defensible wording is: "to our knowledge, the first minute-granularity detection-latency curve for later account disappearance on GitHub using only public event data at inference, stratified by activity level." The contribution is an empirical benchmark, and its value depends on whether degradation differs by activity stratum and on a clear baseline (raw event count) at each window.

Practical framing: claim the combination and the validity audit, not the concepts. The strongest parts of the project are likely the numeric-ID label construction with an explicit limitation on the 404 merge, the PU evaluation, and showing what remains predictable once activity is matched.

### Gaps and auditable search log for absence claims
Absence statements here mean "not found", not "does not exist". Several indexes were rate-limited, so coverage is incomplete.

Failed or unusable: DBLP search API returned HTTP 429, then parse errors and HTTP 500, for queries including "GitHub suspended accounts", "account suspension prediction", "early detection fake accounts" (no usable results). Semantic Scholar search returned HTTP 429 for all six attempted queries; its batch endpoint worked for metadata only. Crossref returned 429 for "predicting account suspension from earlier behavior" and "GitHub deleted suspended accounts".

**WebSearch queries run (standard mode):**
- predicting deleted and suspended accounts Twitter from earlier behavior
- early detection of suspended social media accounts timely detection
- predict users who will be banned Reddit account suspension prediction early
- detecting fake accounts at time of registration online social networks
- suspended accounts as ground truth bias limitations bot detection labels
- Twitter purge retrospective analysis of suspended users Chowdhury Mueen
- deleted and suspended users Twitter analysis 2020 BlackLivesMatter Toraman; data persistence bias suspended accounts
- Mastodon moderation suspended accounts prediction dataset fediverse banned users classifier
- Telegram scam accounts channel banned detection label prediction fake channels dataset
- predicting X Twitter account suspension machine learning 2024 2025 users later suspended classifier
- GitHub suspended accounts research GH Archive 404 deleted users fake stars dataset ground truth
- survival analysis time to suspension Twitter accounts hazard moderation latency measurement
- bot detection first hour of activity after account creation observation window length classifier performance
- "minutes after" account creation malicious account classifier early detection time window evaluation social network
- GitHub public event stream real-time malicious accounts detection early minutes event window classifier

**arXiv API queries run (export.arxiv.org):** `ti:"account suspension"`; `abs:"suspended accounts" AND abs:predict`; `ti:"retrospective" AND abs:suspended`; `abs:"positive-unlabeled" AND abs:bot`; `abs:"positive and unlabeled" AND abs:suspended`; `all:"GH Archive" AND all:suspended`; `all:GitHub AND all:"suspended accounts"`; `abs:"fake accounts" AND abs:"early detection"`; `abs:"observation window" AND abs:bot`; `abs:"time window" AND abs:"fake accounts"`; `ti:"early detection" AND abs:bot AND abs:Twitter`; `all:"early detection" AND all:"bot" AND all:"accounts"`; `all:"suspended accounts" AND all:classifier`; `abs:"account suspension" AND abs:predict`; `all:GitHub AND all:"deleted accounts"`; `all:GitHub AND all:"suspended"AND all:account AND all:malicious`; `all:GitHub AND all:ghost AND all:deleted AND all:users`; `all:GitHub AND all:"fake accounts"`; `all:GitHub AND all:"spam" AND all:accounts AND all:detection`; `ti:bluesky AND abs:moderation`. No result matched the C1 or C3 gaps as stated; the nearest hits are the works cited above. The `abs:"positive-unlabeled" AND abs:bot` query returned Botcha, which concerns web traffic, not account suspension.

**Crossref (`query.bibliographic`) queries run:** predict which accounts will be suspended; retrospective labels suspended accounts machine learning; GitHub account suspension detection; detection latency abusive accounts observation window; early detection fake accounts first actions; early detection bot accounts first tweets; time to detection spam accounts; performance as a function of observation window account detection; positive unlabeled learning suspended accounts. Top hits relevant to this topic were Volkova and Bell (2017) and Breuer et al. (2020); the others were unrelated. Two 2026 items appeared that I could not assess: "Early Screening of Fake Social Media Accounts Under Limited Profile Signals and Time Shift" (preprint, DOI 10.20944/preprints202608.0136.v1; preprints.org returned HTTP 403, so it is unverified and could bear on C3) and an IJCOPE 2026 paper on early fake and bot account detection (not opened, unverified).

**Absence claims this log supports (each as "not found"):**
1. No account-level ban/suspension prediction study on Mastodon/Fediverse.
2. No dedicated account-level "who will be banned" prediction study specifically on Reddit, beyond interaction-level ban labels in JODIE.
3. No GitHub study using later account disappearance as a prediction target, as opposed to a validation signal.
4. No account-level study reporting performance on a wall-clock window grid such as 5, 15, 30 and 60 minutes.
