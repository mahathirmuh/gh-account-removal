# Creation batches, sequential account IDs and split-design leakage in fake-account, bot and abuse detection: novelty check for claim C4

## Q1. Which works use sequential account IDs, registration-time proximity or creation batches as features or cluster keys?

### Takeaway
Creation proximity is an established detection signal: LinkedIn clustered accounts by registration IP and date, Twitter botnets were defined partly by narrow numeric ID ranges, and WeChat and Facebook use registration patterns. None of the works opened here treats the creation batch as a unit for designing a train-test split.

### Cited Findings
- **Xiao, Freeman, Hwa (2015).** Cao Xiao, David Mandell Freeman, Theodore Hwa. "Detecting Clusters of Fake Accounts in Online Social Networks", AISec 2015, pp. 91-101, DOI 10.1145/2808769.2808779. [Source](https://theory.stanford.edu/~dfreeman/papers/clustering.pdf)
  - Data: LinkedIn accounts registered 1 Dec 2013 to 31 May 2014 (260,644 labeled, 153,019 fake), plus June 2014 as "out-of-sample" (30,550 accounts, 15,078 fake) (Section 5 data paragraph). Section 1.2 instead says "approximately 275,000" sampled accounts; the text read does not reconcile the two.
  - Batch use: clusters are formed by "registration IP address and registration date"; the authors chose this "primarily because this is a grouping for which we were able to obtain a large amount of manually labeled data" (Section 5). Features are statistics on name and email patterns within a cluster (abstract).
  - Cluster purity: 89% of clusters had either no fake accounts or all fake accounts; 3.8% had between 20% and 80% fake (Section 5.2).
  - Results: held-out 20% split gave AUC 0.98 and recall 0.90 at 95% precision; the later month gave AUC 0.95 and recall 0.72 at 95% precision (Section 1.2). Random forest out-of-sample: AUC 0.949, recall 0.720 at cluster level (Table 3); AUC 0.954, recall 0.713 at account level (Table 4). The authors attribute the drop to spammer patterns changing over time and say the model needs regular retraining (Section 5.3).
  - Limitations: one later month only; clusters are the classification unit, so there is no comparison between split designs; labels are LinkedIn restriction status at survey time.
- **Thomas et al. (2013).** Kurt Thomas, Damon McCoy, Chris Grier, Alek Kolcz, Vern Paxson. "Trafficking Fraudulent Accounts: The Role of the Underground Market in Twitter Spam and Abuse", 22nd USENIX Security Symposium, 2013. [Source](https://www.usenix.org/system/files/conference/usenixsecurity13/sec13-paper_thomas.pdf)
  - Data: 121,027 accounts purchased bi-weekly from 27 merchants, June 2012 to April 2013 (Introduction).
  - Batch use: "batches of accounts from a single seller that were all registered within 24 hours", in clusters of over 300 accounts, split in half by time for a capture-recapture estimate of merchant IP pools. Detection itself uses per-merchant regular-expression fingerprints over name, screen name and email domain; clusters under 10 accounts are dropped (Section 5.1).
  - Results: estimated precision 99.99%, recall 95% of purchased accounts (Table 7 and "Precision & Recall" paragraph); final tuned precision 99.9942% with recall 95% (text on suspending accounts).
  - Limitations: the authors state the approach "is not meant to sustain accuracy in an adversarial setting". The over-time test trains on accounts acquired up to time t but evaluates "on all accounts from the merchant, regardless of when we purchased the account", so it is not a strict forward test ("Performance Over Time" paragraph). A case-insensitive scan of the PDF text found no use of sequential or adjacent numeric account IDs.
- **Cao et al. (2014), SynchroTrap.** Qiang Cao, Xiaowei Yang, Jieqi Yu, Christopher Palow. "Uncovering Large Groups of Active Malicious Accounts in Online Social Networks", CCS 2014, pp. 477-488, DOI 10.1145/2660267.2660269. [Source](https://users.cs.duke.edu/~xwy/publications/SynchroTrap-ccs14.pdf)
  - Data and deployment: five applications at Facebook and Instagram (abstract).
  - Batch use: none. It clusters accounts by similarity of actions "at around the same time for a sustained period of time" (abstract). The PDF text uses "sequential" only for an algorithm and "batch" only for computation and one example of timed follows, not for account creation.
  - Results: more than two million malicious accounts and 1156 large attack campaigns within one month (abstract); manual inspection of a sample suggests precision above 99%; about 274K accounts caught per week on average (Section 1).
  - Limitations: no train-test evaluation; precision comes from inspecting a sample.
- **Echeverria, Besel, Zhou (2017), Bursty botnet.** Juan Echeverria, Christoph Besel, Shi Zhou. "Discovery of the Twitter Bursty Botnet", arXiv:1709.06740v2 (arXiv comment: accepted at Data Science for Cyber-Security 2017). [Source](https://arxiv.org/pdf/1709.06740)
  - Data: about 21 million users in the ID range 5e8 to 5.35e8, with account data and tweets up to September 2016 (Section 3.1).
  - Batch use: "the user IDs are allocated in a sequential manner such that a smaller ID means an earlier creation date" (text around Figure 2). The botnet is defined in part by registration in February and March 2012 with IDs between 5e8 and 5.35e8 (Section 3.1). The abstract states the Star Wars bots "were created in bursts or batches".
  - Results: more than 500,000 Bursty bots (abstract, Section 3.1).
  - Limitations: a hand-defined single botnet; descriptive; no classifier evaluation across batches.
- **Echeverría, Zhou (2017), Star Wars botnet.** Juan Echeverría, Shi Zhou. "Discovery, Retrieval, and Analysis of the 'Star Wars' Botnet in Twitter", arXiv:1701.02405v3 (arXiv comment: accepted at ASONAM 2017). [Source](https://arxiv.org/pdf/1701.02405)
  - Data: uniform 1% sample of the 32-bit user ID space in early 2015, yielding 6 million English-speaking users (data section).
  - Batch use: the bots' IDs "are densely concentrated within a narrow space between 1.5 x 10^9 and 1.6 x 10^9" (listed property of the bots). A footnote says Twitter has extended the ID space to 64 bits.
  - Results: a classifier using only tweet text reaches 99.8% accuracy (Table I). The botnet size of more than 350,000 is stated in the [Bursty paper's abstract](https://arxiv.org/pdf/1709.06740).
  - Limitations: as for the Bursty paper; ID concentration is a descriptive property, not a tested evaluation factor.
- **Xu et al. (2021), DEC.** Teng Xu, Gerard Goossen, Huseyin Kerem Cevahir, Sara Khodeir, Yingyezhe Jin, Frank Li, Shawn Shan, Sagar Patel, David Freeman, Paul Pearce. "Deep Entity Classification: Abusive Account Detection for Online Social Networks", USENIX Security 2021. Deep features include "the IP address that registers the account, as well as all the other accounts created from the IP address", so "the scripted activity of batch account registration can be easily detected" (features section). Performance numbers: not verified (only this section was read). [Source](https://www.usenix.org/system/files/sec21summer_xu.pdf)
- **Yuan et al. (2019), Ianus.** Dong Yuan, Yuanli Miao, Neil Zhenqiang Gong, Zheng Yang, Qi Li, Dawn Song, Qian Wang, Xiao Liang. "Detecting Fake Accounts in Online Social Networks at the Time of Registrations", CCS 2019, pp. 1423-1438, DOI 10.1145/3319535.3363198 (metadata checked on Crossref). A project page states "Sybils tend to have synchronized and abnormal registration patterns", uses a WeChat registration dataset with labeled Sybils, and reports about 400K Sybils per million new registrations per day with precision over 96% on average, by manual verification from the WeChat security team. [Source](https://netsec.ccert.edu.cn/publications/ccs18-ianus) Limitation: full text not opened, and the page text contains a stray passage from an unrelated paper.

### Inferences
- These works supply the mechanism C4 relies on: numeric IDs track creation order, and batches are close to label-pure (Xiao: 89% of clusters all-or-none). A random split on accounts would therefore tend to place same-batch neighbours on both sides. None of the works tests this directly.
- Bursty and Star Wars use ID adjacency as a discovery signal. For a SOTA table they show the signal exists; they say nothing about evaluation.

### Gaps
- No opened source analyses Twitter Snowflake IDs as a creation-batch signal. The Black Hat 2018 white paper that reportedly does is under Unverified. A text scan of [Pfeffer et al. (2023)](https://arxiv.org/pdf/2301.11429) found no occurrence of "snowflake".
- No peer-reviewed source on how GitHub allocates numeric IDs was found (see Search log, S11).

## Q2. Which works report that accounts from the same campaign, botnet or batch in both train and test inflate performance?

### Takeaway
Holding out a bot class or dataset produces large drops in several studies; the largest verified is LOBO, where mean recall on the target class falls from 94.29% to 57.51%. The held-out units in these studies are pre-existing datasets or labeled botnets, not creation adjacency or activity signatures. Rauchfleisch and Kaiser do not test train-test contamination.

### Cited Findings
- **Echeverría et al. (2018), LOBO.** Juan Echeverría, Emiliano De Cristofaro, Nicolas Kourtellis, Ilias Leontiadis, Gianluca Stringhini, Shi Zhou. "LOBO: Evaluation of Generalization Deficiencies in Twitter Bot Classifiers", ACSAC 2018, pp. 137-146, DOI 10.1145/3274694.3274738. [Source](https://arxiv.org/pdf/1809.09684)
  - Design: Leave One Botnet Out trains on all other bot classes and tests on the held-out class. Data: more than 200,000 data points (abstract); C30K of about 105,000 bots and 105,000 users; C500 of 14 bot classes with 500 accounts each (Section 6.1).
  - Result under random 70-30 splits: LightGBM reaches 97.84% accuracy on C30K and 93.93% on C500 (Table 3).
  - Result under LOBO: the mean accuracy on an unseen target class is 54.88% on C30K (Section 6.3). On C500, mean accuracy is 94.29% for the model trained with the target class present and 57.51% with it held out, a 36.78-point gap (Table 6). Accuracy equals recall here because only bots are tested (footnote 2). Per-class gaps range from -4.22 points (Bursty bots) to 93.31 points (Table 6).
  - Limitations: classes come from prior datasets; the "full model" baseline uses random 70-30 splits; recall only; no ID or activity-signature grouping; Twitter only.
- **Hays et al. (2023).** Chris Hays, Zachary Schutzman, Manish Raghavan, Erin Walk, Philipp Zimmer. "Simplistic Collection and Labeling Practices Limit the Utility of Benchmark Datasets for Twitter Bot Detection", WWW 2023, pp. 3660-3669, DOI 10.1145/3543507.3583214. [Source](https://arxiv.org/pdf/2301.07015)
  - Shallow decision trees of depth at most four match the state of the art within 10 accuracy points on all datasets but rtbust-2019, and within 5 points on all but rtbust-2019, gilani-2017 and caverlee-2011 (Section 4.1, Table 2). Example: cresci-2017 at depth 1 reaches 0.98 accuracy.
  - Random forests trained on one dataset and tested on another are mostly near chance balanced accuracy; for example training on twibot-2020 gives 0.49 to 0.56 off-diagonal against 0.72 on the diagonal (Table 3).
  - Leave-one-dataset-out: twibot-2020 balanced accuracy falls from 0.78 in-sample to 0.55 out-of-sample (Table 4). Results are "weaker in the cases where the held out dataset shares some data with the training dataset(s)" (Section 4 overview).
  - Account creation date is a key split in one tree, which the authors link to the collection process: "very few spambots in the dataset were created more than a month before data collection began" (Section 4.1, the caverlee-2011 dataset by its reference and collection period).
  - Limitations: the unit is the dataset; a text scan found "user identifiers" only in the context of re-hydrating data, so numeric IDs are not studied.
- **Yang et al. (2020).** Kai-Cheng Yang, Onur Varol, Pik-Mai Hui, Filippo Menczer. "Scalable and Generalizable Social Bot Detection through Data Selection", AAAI 2020, 34(01):1096-1103, DOI 10.1609/aaai.v34i01.5460. [Source](https://arxiv.org/pdf/1911.09179)
  - States that "good cross-validation performance, even on multiple datasets, does not guarantee generalization across unseen datasets" ("Model Evaluation").
  - Botometer baseline: 5-fold AUC 0.97, but AUC 0.67 on gilani-17 and 0.71 on cresci-rtbust. A model trained on all data (M246): 5-fold AUC 0.95, but 0.64 and 0.57 on the same sets (Table 4). F1 is 0.94 at the cross-validation threshold and 0.77 in cross-domain testing (text with Fig. 4).
- **Sayyadiharikandeh et al. (2020).** Mohsen Sayyadiharikandeh, Onur Varol, Kai-Cheng Yang, Alessandro Flammini, Filippo Menczer. "Detection of Novel Social Bots by Ensembles of Specialized Classifiers", CIKM 2020, pp. 2725-2732, DOI 10.1145/3340531.3412698. Supervised methods "suffer severe performance deterioration when attempting to detect behaviors not observed in the training data"; an ensemble gives an average 56% F1 improvement for unseen accounts across datasets (abstract). [Source](https://arxiv.org/pdf/2006.06867)
- **Rauchfleisch and Kaiser (2020).** Adrian Rauchfleisch, Jonas Kaiser. "The False positive problem of automatic bot detection in social science research", PLOS ONE 15(10):e0241045, DOI 10.1371/journal.pone.0241045. They measure Botometer on new labeled datasets and over time, and do not test train-test contamination. ROC-AUC is 0.85 on their complete data against 0.94 in the creators' paper, whose baseline model also got 0.85 (Results). Thresholds "are prone to variance", producing false negatives and false positives over time (abstract). [Source](https://journals.plos.org/plosone/article/file?id=10.1371/journal.pone.0241045&type=printable)
- **Cresci et al. (2023, arXiv v4 2025).** Stefano Cresci, Kai-Cheng Yang, Angelo Spognardi, Roberto Di Pietro, Filippo Menczer, Marinella Petrocchi. "Demystifying Misconceptions in Social Bots Research". "Leveraging features used to select and label the data can also be framed as a feature leakage issue". This names feature leakage in bot research but does not quantify split inflation. [Source](https://arxiv.org/pdf/2303.17251)
- **Counterpoint on magnitude: Roth (2026).** Simon Roth. "Which Leakage Types Matter? A Quantitative Landscape Across 2,047 Benchmark Datasets", arXiv:2604.04199v2 (single-author preprint). Random CV against GroupKFold on one click-prediction dataset grouped by ad_id shows +0.01 AUC (Experiment P); the author notes most public benchmarks strip ID columns, limiting scope. Temporal effect averages +0.023 AUC on genuinely temporal datasets (abstract). [Source](https://arxiv.org/pdf/2604.04199)
- **Current practice still uses random folds.** A 2026 preprint on account-history features (account age, counts, profile fields) reports ROC-AUC 0.977 from stratified five-fold cross-validation on 2,432 Twitter accounts, and itself warns that long-lived sleeper bots "will defeat account-age features". Gaurang Katyal, arXiv:2606.26127. [Source](https://arxiv.org/pdf/2606.26127)

### Inferences
- The LOBO-style gap mixes two effects: recognising a seen group, and real distribution shift between groups. A drop under batch exclusion in C4 would mix them too, and calling it all "leakage" would overstate it.
- Reported magnitudes run from +0.01 AUC (Roth, one dataset) to a 36.78-point recall gap (LOBO). C4 should report its own effect size and not borrow these.
- Hays et al. show a low-complexity tree can match complex models for reasons tied to data collection, which is close to the pilot's finding that a coarse baseline matches 48 behaviour features. It is an interpretive precedent, not a split-design audit.

### Gaps
- Per-class values in LOBO Table 5 did not reconcile with its column headers in the PDF text extraction, so only the 54.88% stated in the text is used from it.
- No opened bot-detection study defines its held-out unit by creation adjacency or identical activity signatures (see Search log S2, S5, S9, S14, S17, S18, A2, A3).

## Q3. What analogous concepts exist in other fields, and which give a citable recipe for block size or group definition?

### Takeaway
Consecutive IDs as a leak, identical feature vectors as a leak, time-consistent evaluation and blocked cross-validation are all documented elsewhere. Roberts et al. (2017) give the most usable recipe for block size, and ICANN (2026) gives a citable batch-detection procedure.

### Cited Findings
- **Consecutive IDs as leakage, Kaufman et al. (2012).** Shachar Kaufman, Saharon Rosset, Claudia Perlich, Ori Stitelman. "Leakage in Data Mining: Formulation, Detection, and Avoidance", ACM TKDD 6(4), DOI 10.1145/2382577.2382579 (metadata from Crossref; text read from a conference-format copy on a course page). In KDD-Cup 2008, the "Patient ID" feature had "tremendous and unexpected predictive power", and "Leakage was thus facilitated by assigning consecutive patient IDs for data from each source" (related-work section). Removing the ID may not suffice: "It is by no means obvious that removing this feature would leave a leakage-free dataset", since "different ID ranges" could leave other traces in the data. [Source](https://www.cs.umb.edu/~ding/history/470_670_fall_2011/papers/cs670_Tran_PreferredPaper_LeakingInDataMining.pdf)
- **Security pitfalls, Arp et al. (2022).** Daniel Arp, Erwin Quiring, Feargus Pendlebury, Alexander Warnecke, Fabio Pierazzi, Christian Wressnegger, Lorenzo Cavallaro, Konrad Rieck. "Dos and Don'ts of Machine Learning in Computer Security", USENIX Security 2022. Across 30 top-tier security papers, sampling bias and data snooping are at least partly present in 90% and 73% of papers (Section 3). Spurious correlation example: a model "may learn to detect a specific IP range instead of generic attack patterns" (Section 2, P4). [Source](https://www.usenix.org/system/files/sec22-arp.pdf)
- **Malware time-aware splits, Pendlebury et al. (2019).** Feargus Pendlebury, Fabio Pierazzi, Roberto Jordaney, Johannes Kinder, Lorenzo Cavallaro. "TESSERACT: Eliminating Experimental Bias in Malware Classification across Space and Time", USENIX Security 2019. With 10% malware in both training and testing, F1 falls from 0.91 (10-fold CV) to 0.58 (temporally consistent) for ALG1 and from 0.83 to 0.32 for ALG2 (Table 1). Constraint C1 requires training objects to be strictly temporally precedent to test objects (Section 4). [Source](https://www.usenix.org/system/files/sec19-pendlebury.pdf)
- **Identical feature vectors as leakage, Liu et al. (2024, arXiv v2 2025).** Guojun Liu, Doina Caragea, Xinming Ou, Sankardas Roy. "The Impact of Train-Test Leakage on Machine Learning-based Android Malware Detection", arXiv:2410.19364. About 10% to 40% of test apps in APIGraph and 10% to 30% in AndroZoo have feature vectors identical to a training app (case study text). After removing them, a graph model that lost to random forest on all data wins in seven of eight test windows (second case study). The paper separates memorization from generalization. [Source](https://arxiv.org/pdf/2410.19364)
- **Near-duplicates in code, Allamanis (2019).** Miltiadis Allamanis. "The Adverse Effects of Code Duplication in Machine Learning Models of Code", Onward! 2019, pp. 143-153, DOI 10.1145/3359591.3359735. Metrics "are sometimes inflated by up to 100%" (abstract). [Source](https://arxiv.org/pdf/1812.06469)
- **Record-wise against subject-wise CV, Saeb et al. (2017).** Sohrab Saeb, Luca Lonini, Arun Jayaraman, David C. Mohr, Konrad P. Kording. "The need to approximate the use-case in clinical machine learning", GigaScience 6(5), DOI 10.1093/gigascience/gix019. Of 62 reviewed papers, 28 used record-wise CV and 34 subject-wise; median classification error was 13.00% for subject-wise and 5.60% for record-wise among 47 papers with extractable accuracies, P < 0.01 (Systematic review). [Source](https://pmc.ncbi.nlm.nih.gov/articles/PMC5441397/)
- **Leakage taxonomy, Kapoor and Narayanan.** Sayash Kapoor, Arvind Narayanan. Patterns 4(9):100804, DOI 10.1016/j.patter.2023.100804. Preprint v1 lists 20 papers in 17 fields, collectively affecting 329 papers (Table 1), with categories including temporal leakage and duplicates. These counts are from arXiv v1; the published numbers were not checked. [Source](https://arxiv.org/pdf/2207.07048)
- **Reporting standard.** REFORMS item 6b asks for "Methods to address dependencies or duplicates between the training and test datasets (e.g. different samples from the same patients are kept in the same dataset partition)" (authors not verified; only this item was read). [Source](https://arxiv.org/pdf/2308.07832)
- **Chronological splits in rumor detection, Mu, Bontcheva, Aletras (2023).** "It's about Time: Rethinking Evaluation on Rumor Detection Benchmarks using Chronological Splits", EACL 2023 Findings (arXiv comment). Random splits "can significantly overestimate predictive performance across all datasets and models" (abstract), and also place near-identical posts on both sides (Introduction). [Source](https://arxiv.org/pdf/2302.03147)
- **Block-size recipe, Roberts et al. (2017).** David R. Roberts, Volker Bahn, Simone Ciuti, Mark S. Boyce, Jane Elith, Gurutzeta Guillera-Arroita, Severin Hauenstein, José J. Lahoz-Monfort, Boris Schröder, Wilfried Thuiller, David I. Warton, Brendan A. Wintle, Florian Hartig, Carsten F. Dormann. Ecography 40(8):913-929, DOI 10.1111/ecog.02881. [Source](https://www.biometrie.uni-freiburg.de/mitarbeiter/dormann/roberts-et-al-2017-ecography.pdf)
  - Block CV "is nearly universally more appropriate than random cross-validation if the goal is predicting to new data or predictor space" (abstract).
  - In simulation, "the size of the blocks needs to be substantially larger than the range of the spatial autocorrelation in the model residuals" (results).
  - Practical Step 1: assess dependence with autocorrelation plots, variograms or correlograms on raw data, as "rough guidance on the scale of blocking (at least as many units as the range of autocorrelation; at least at the most variable hierarchical level)".
  - Group definition: "blocks should be drawn so that similar structural conditions are grouped together", for example "time-slice blocks of similar duration as the one predicting to; herds as blocks when predicting to a new herd".
- **blockCV tutorial.** `cv_spatial_autocor` "estimates the effective range of spatial autocorrelation in the response or continuous predictor rasters. This tool is a guide, not an absolute rule", and these variograms "are not residual autocorrelation ranges and can under- or over-estimate the block size needed". [Source](https://cran.r-project.org/web/packages/blockCV/vignettes/tutorial_2.html) Note that this tutorial cites Roberts et al. for residual-based choice, while Roberts' Step 1 specifies raw data; the two should not be conflated.
- **Batch definition, ICANN OCTO-044 (2026).** Sam Cheadle, Siôn Lloyd, Carlos Hernández-Gañán, Samaneh Tajalizadehkhoob. "Associated Domain Analysis Using Public Data", 18 September 2026. A batch is "a group of domains registered close in time, through the same registrar, and served by the same authoritative nameservers", found by DBSCAN on creation timestamps within each group; epsilon values from 0.1 to 10 seconds were explored (Appendix A.1.1). [Source](https://www.icann.org/en/system/files/files/octo-044-18sep26-en.pdf)

### Inferences
- Kaufman et al. weaken any claim that ID adjacency as a leakage channel is a new idea, even though the setting is medical. C4 should cite it.
- The Roberts recipe can be transferred by treating numeric ID as a one-dimensional coordinate: compute a correlogram of out-of-fold residuals (and of raw activity) against ID distance, and set block width at or above the range. This adaptation has no direct precedent in the opened literature.
- A deployment framing decides the group definition (Roberts): if the target is accounts from new batches, the batch is the block, and a temporal-forward split alone is not enough.
- ICANN's DBSCAN procedure offers a tested template for defining batches from creation timestamps, with sensitivity analysis over epsilon. GitHub ID distances would replace seconds; that substitution is untested.

### Gaps
- The block-size guidance is from spatial and hierarchical ecology data. No equivalent for ID space exists in the sources opened.

## Q4. Has any work audited split-design inflation on GitHub or other software platform account data, or treated numeric ID adjacency as a leakage channel there?

### Takeaway
None was found in the searches listed. The GitHub account or abuse studies opened use a random stratified split, no train-test evaluation, or rules, and none treats ID adjacency as a leakage channel. This is absence of evidence from a bounded search.

### Cited Findings
- **He et al. (2026), StarScout.** Hao He, Haoqin Yang, Philipp Burckhardt, Alexandros Kapravelos, Bogdan Vasilescu, Christian Kästner. "Six Million (Suspected) Fake Stars on GitHub", ICSE 2026 Research Track ([listing](https://conf.researchr.org/details/icse-2026/icse-2026-research-track/14/Six-Million-Suspected-Fake-Stars-on-GitHub-A-Growing-Spiral-of-Popularity-Contests)); title wording varies slightly between arXiv metadata, PDF and listing. It applies low-activity and lockstep signatures to GitHub data from July 2019 to December 2024 in six-month chunks; no classifier train-test split appears in its evaluation section (Section 3.4). It identifies 301k accounts in fake-star campaigns; 57.07% of those accounts were deleted, against a baseline of 3.54% of sampled stargazers, as of January 2025 (Section 3.4, Table 1). A text scan found no use of numeric ID adjacency. [Source](https://arxiv.org/pdf/2412.13459)
- **Golzadeh et al. (2021), BoDeGHa.** Mehdi Golzadeh, Alexandre Decan, Damien Legay, Tom Mens. Journal of Systems and Software 175:110911, DOI 10.1016/j.jss.2021.110911. Commenter accounts are divided by a stratified 60/40 train-test split, and classifiers compared with 10-fold stratified shuffle splits (Section 5). No grouped or temporal split is described in that section. [Source](https://arxiv.org/pdf/2010.03303)
- **Cheng et al. (2026).** Yuli Cheng, Xiaoyu Zhang, Jiongchi Yu, Shiqing Ma, Chao Shen, Yang Liu. "Weaponizing the Commons: A Taxonomy and Detection Framework of Abuse on GitHub", JAWs 2026 at ICSE 2026 (arXiv comment). A rule-based framework evaluated on 392 manually labeled instances. [Source](https://arxiv.org/pdf/2604.17909)
- **Absence claim.** No prior audit of split-design inflation on GitHub or software-platform account data, and no treatment of numeric ID adjacency as leakage there, was found by queries S3, S8, S10, S11, S12, S17, S18, S20, A1 and A4 in the Search log.

### Inferences
- The GitHub part of C4 is a genuine gap in what was searched, but it is the transfer of an established idea to a new platform. That is a weaker contribution than a new idea.
- 57.07% against 3.54% (He et al.) shows deletion is enriched among abusive accounts but also occurs among ordinary ones. A 404 is therefore a noisy proxy for abuse, which matters for the wording of C4.

### Gaps
- Other GitHub bot detection tools (for example BIMAN and RABBIT) were not opened, so their split designs are unknown.
- DBLP queries failed (rate limited), so DBLP was not actually checked. See Search log.
- The arXiv boolean field queries are strict, and zero hits may reflect wording.

## Q5. Has any work tested feature coarsening or binning as a defence against fingerprint memorization of campaigns?

### Takeaway
No work testing this in bot, fake-account or abuse detection was found in the searches listed. The nearest analogues are API abstraction against malware aging and binning as a general overfitting control.

### Cited Findings
- **Abstraction against aging, Mariconti et al. (2017), MaMaDroid.** Enrico Mariconti, Lucky Onwuzurike, Panagiotis Andriotis, Emiliano De Cristofaro, Gordon Ross, Gianluca Stringhini. NDSS 2017, DOI 10.14722/ndss.2017.23353. "By abstracting calls to their packages or families, MaMaDroid maintains resilience to API changes and keeps the feature set size manageable"; F-measure up to 99%, and on average 87% and 73% one and two years after training (abstract). [Source](https://arxiv.org/pdf/1612.04433)
- **Binning as overfitting control.** LightGBM's tuning guide lists "Use small `max_bin`" under "Deal with Over-fitting", and suggests large `max_bin` for better accuracy. It says nothing about campaigns. [Source](https://lightgbm.readthedocs.io/en/latest/Parameters-Tuning.html)
- **Binning in leakage audits means something else.** Roth (2026) lists binning fit on full data under estimation leakage, with mean AUC inflation around +0.0004 (results table). This concerns preprocessing leakage, not coarsening as a defence. [Source](https://arxiv.org/pdf/2604.04199)
- **Absence claim.** No test of coarsening or binning against campaign fingerprint memorization in bot, fake-account or abuse detection was found by queries S4, S15, S21 and A5.

### Inferences
- MaMaDroid's abstraction is the best citable precedent, but it addresses API drift in malware, not memorization of account farms.
- The pilot's coarse baseline shows that coarse features can match a richer model. It does not show coarsening defends against memorization. That needs a direct test, such as whether coarsening shrinks the gap between random and batch-exclusion splits.
- Coarse account age is itself a proxy for creation period, so a coarse baseline may keep part of the batch signal. Kaufman et al. make the same point about removing an obvious ID leak.

### Gaps
- Whether discretization improves transfer to unseen campaigns is untested in the sources opened.

## Q6. What are the 3-5 works closest to C4, what does each overlap with, and does C4 survive?

### Takeaway
C4 needs narrowing. Its general form, quantifying how split design inflates detector performance, is already done in bots, malware and clinical ML. What remains unfound in the searches listed is an audit on GitHub account data, numeric ID adjacency used as a cross-validation group in abuse detection, and a test of coarsening against campaign memorization.

### Cited Findings: closest works
1. **Echeverría et al. (2018), [LOBO](https://arxiv.org/pdf/1809.09684).** Overlaps: holds out a bot group and quantifies the gap against random splits on account-level classifiers (94.29% to 57.51%, Table 6). Does not overlap: units are pre-labeled botnets on Twitter; no adjacency or signature grouping; no temporal-forward arm; no coarsening. This is the closest prior work on the core idea.
2. **Hays et al. (2023), [benchmark limits](https://arxiv.org/pdf/2301.07015).** Overlaps: shallow models near state of the art, collapse across datasets, and creation date as a collection artifact. Does not overlap: dataset-level evaluation, no audit of split design within one dataset, no numeric IDs.
3. **Liu et al. (2024), [Android train-test leakage](https://arxiv.org/pdf/2410.19364).** Overlaps: identical feature vectors as the leakage unit (the analogue of C4's activity signatures), measured effect, and a memorization framing. Does not overlap: apps rather than accounts; no batches or IDs.
4. **Xiao et al. (2015), [LinkedIn clusters](https://theory.stanford.edu/~dfreeman/papers/clustering.pdf).** Overlaps: registration batches as the unit, and a measured drop from a held-out split to a later month (recall at 95% precision 0.90 to 0.72). Does not overlap: the batch is the classification unit rather than a split-design variable; no comparison of split designs.
5. **Kaufman et al. (2012), [leakage](https://www.cs.umb.edu/~ding/history/470_670_fall_2011/papers/cs670_Tran_PreferredPaper_LeakingInDataMining.pdf).** Overlaps: consecutive numeric IDs named explicitly as a leakage channel, and the warning that removing the ID may not remove the leak. Does not overlap: medical data; no split audit or quantified inflation.
- Methodological ancestor for the temporal arm: [TESSERACT](https://www.usenix.org/system/files/sec19-pendlebury.pdf), which C4 should cite as the source of time-consistency constraints.

### Cited Findings: verified SOTA table entries

| Reference | Platform and data | Unit or signal | Evaluation | Key result and location | Relation to C4 |
|---|---|---|---|---|---|
| [Xiao, Freeman, Hwa 2015](https://theory.stanford.edu/~dfreeman/papers/clustering.pdf), AISec, DOI 10.1145/2808769.2808779 | LinkedIn; 260,644 labeled accounts (Sec. 5) plus 30,550 later | Registration IP and date clusters | 80-20 held-out; later month | AUC 0.98 to 0.95; recall at 95% precision 0.90 to 0.72 (Sec. 1.2) | Batch as cluster key; no split comparison |
| [Thomas et al. 2013](https://www.usenix.org/system/files/conference/usenixsecurity13/sec13-paper_thomas.pdf), USENIX Security | Twitter; 121,027 purchased accounts, 27 merchants | Per-merchant name patterns; 24-hour batches for IP pools | Patterns trained up to time t, evaluated on all | Precision 99.99%, recall 95% (Table 7) | Merchant as unit; no IDs |
| [Cao et al. 2014](https://users.cs.duke.edu/~xwy/publications/SynchroTrap-ccs14.pdf), CCS, DOI 10.1145/2660267.2660269 | Facebook, Instagram | Action synchrony clusters | Manual inspection of sample | More than 2M accounts, 1156 campaigns (abstract); precision above 99% (Sec. 1) | Activity grouping; no split audit |
| [Echeverria, Besel, Zhou 2017](https://arxiv.org/pdf/1709.06740), arXiv 1709.06740 | Twitter; about 21M users in an ID range | ID range plus bursty behaviour | Descriptive | More than 500,000 bots (abstract) | IDs as cluster key |
| [Echeverría, Zhou 2017](https://arxiv.org/pdf/1701.02405), arXiv 1701.02405 | Twitter; 1% uniform ID sample | Narrow ID band | Text classifier | 99.8% accuracy (Table I) | IDs as descriptive trace |
| [Yuan et al. 2019](https://netsec.ccert.edu.cn/publications/ccs18-ianus), CCS, DOI 10.1145/3319535.3363198 | WeChat registrations | Synchronized registration patterns | Manual verification | Precision over 96% (project page; full text not opened) | Registration signal |
| [Echeverría et al. 2018](https://arxiv.org/pdf/1809.09684), ACSAC, DOI 10.1145/3274694.3274738 | Twitter; more than 200,000 data points, 14 classes in C500 | Bot class held out | 70-30 random vs leave one botnet out | 94.29% to 57.51% mean recall (Table 6) | Closest group-held-out evaluation |
| [Hays et al. 2023](https://arxiv.org/pdf/2301.07015), WWW, DOI 10.1145/3543507.3583214 | Twitter; 11 benchmark datasets | Dataset | Shallow trees; train on one; leave one dataset out | twibot-2020 balanced accuracy 0.78 to 0.55 (Table 4) | Simple-model and dataset-level precedent |
| [Yang et al. 2020](https://arxiv.org/pdf/1911.09179), AAAI, DOI 10.1609/aaai.v34i01.5460 | Twitter; dataset combinations | Dataset held out | 5-fold vs unseen datasets | AUC 0.97 vs 0.67 and 0.71 (Table 4) | Dataset-level generalization |
| [Liu et al. 2024](https://arxiv.org/pdf/2410.19364), arXiv 2410.19364 | Android; APIGraph, AndroZoo | Identical feature vectors | Remove leaked test apps | 10% to 40% of test apps leaked; model ranking flips | Signature as leakage unit |
| [Kaufman et al. 2012](https://www.cs.umb.edu/~ding/history/470_670_fall_2011/papers/cs670_Tran_PreferredPaper_LeakingInDataMining.pdf), TKDD, DOI 10.1145/2382577.2382579 | KDD-Cup 2008 cancer data | Consecutive patient IDs | Conceptual | Patient ID strongly predictive (text; no effect size read) | ID-adjacency leak precedent |
| [Pendlebury et al. 2019](https://www.usenix.org/system/files/sec19-pendlebury.pdf), USENIX Security | Android; 2014-2016 | Time | 10-fold vs temporally consistent | F1 0.91 to 0.58 (ALG1), 0.83 to 0.32 (ALG2) (Table 1) | Temporal template |
| [He et al. 2026](https://arxiv.org/pdf/2412.13459), ICSE | GitHub 2019-2024 | Low-activity and lockstep signatures | No train-test split | 301k accounts; 57.07% deleted vs 3.54% (Sec. 3.4) | GitHub domain; no split audit |

### Inferences: verdict
- **Verdict: needs narrowing.** It is not already done as a whole, but the broad version is not new. The idea of grouped or time-aware evaluation is established, and applying it to GitHub is a transfer, which is a weaker contribution than a new idea.
- **What can be claimed, if the full experiment supports it:** to the extent of the searches listed, the first quantified comparison of split designs for account-removal prediction on GitHub, using numeric ID adjacency and identical activity signatures as grouping units.
- **Suggested wording:** "We quantify how split design changes measured performance for predicting GitHub account removal, using account-creation proximity (adjacent numeric IDs) and identical activity signatures as grouping units, across random, shared-artifact grouped, temporal-forward, and temporal-forward with batch-exclusion splits."
- **Replace "abuse detection" with "account-removal prediction".** The label is a 404 at about 31 months, and deletion also occurs among ordinary accounts (He et al. baseline 3.54%).
- **Drop or test the coarsening claim.** It needs a direct test (see Q5). The pilot alone does not support it.
- **Avoid "first to treat ID adjacency as leakage".** Kaufman et al. describe consecutive IDs as a leak. The narrower claim is using adjacency as a cross-validation group in account-level detection.
- **Do not generalize from the pilot.** One hour with 8,434 accounts and 519 removed (about 6.2%) is a pilot. Effect sizes need replication over more windows.
- **Attribute carefully.** A drop under batch exclusion combines leakage and real distribution shift (see Q2). Reporting performance on the non-leaked portion of the test set, as Liu et al. do, would help separate them.

### Gaps
- Absence claims rest on the queries below; they cannot prove non-existence. Paywalled or non-indexed work may exist.
- Group-held-out and temporal arms have not, in the sources opened, been combined with batch exclusion in account-level detection; this was not specifically proven absent beyond the queries below.

### Unverified
Items below were not opened in full, or only their metadata was checked. Do not cite their content without opening them.
- **Anise and Wright, "Don't @ Me: Hunting Twitter Bots at Scale", Black Hat USA 2018 white paper.** Unverified. [URL](https://i.blackhat.com/us-18/Wed-August-8/us-18-Anise-Wright-Dont-@-Me-Hunting-Twitter-Bots-at-Scale-wp.pdf) returned HTTP 403 and was not opened. A search snippet only says user IDs were first sequential unsigned 32-bit integers, allowing discovery of bot groups created around the same time, and mentions "Snowflake ID Backtracking".
- **Rosset, Perlich, Świrszcz, Melville, Liu (2010), "Medical data mining: insights from winning two competitions", DMKD 20(3):439-468, DOI 10.1007/s10618-009-0158-x.** Unverified content; metadata checked on Crossref. The patient-ID account above comes from Kaufman et al.
- **Valavi, Elith, Lahoz-Monfort, Guillera-Arroita (2019), blockCV, Methods in Ecology and Evolution 10(2):225-232, DOI 10.1111/2041-210x.13107.** Unverified content; metadata checked on Crossref. Only the CRAN tutorial was opened.
- **"Detecting Malicious Domain Registration Batches" (IEEE, 2025), [URL](https://ieeexplore.ieee.org/document/11327823/).** Unverified; search snippet only.
- **BOTection, [URL](https://dl.acm.org/doi/10.1145/3320269.3372202).** Unverified; search snippet only (F-measure 93.03% on unseen bot families).
- **BotSSCL "cross-botnet evaluation", [URL](https://www.sciencedirect.com/science/article/pii/S2468696425000199).** Unverified; search snippet only. The arXiv version (2402.03740v1) was opened and has no occurrence of "cross-botnet" or "CBE".
- **Rao et al., "Suspicious Massive Registration Detection via Dynamic Heterogeneous Graph Neural Networks", arXiv:2012.10831.** Unverified content; metadata checked on the arXiv API.
- **GitHub ID allocation claim (users, organizations and bots share one counter), [DEV Community post](https://dev.to/dalirnet/no-name-no-bio-no-rest-meet-githubs-busiest-account-45g8).** Unverified; search snippet only; anecdotal.
- **Press coverage of a "3 million" Twitter botnet with IDs reserved on one day ([SecurityWeek](https://www.securityweek.com/botnet-3-million-twitter-accounts-remains-undetected-years/)).** Unverified; search snippet only; not used.
- **Metadata checked on Crossref, content not opened, nothing used:** Zhao et al. 2021 (10.1145/3446905); Rossow et al. 2012 (10.1109/sp.2012.14); Allix et al. 2015 (10.1007/978-3-319-15618-7_5); Drichel et al. 2020 (10.1145/3407023.3407030); Whalen et al. 2022 (10.1038/s41576-021-00434-9); Cresci et al. 2017 (10.1145/3041021.3055135).
- **Meeder et al. (2011) on inferring link creation times from Twitter IDs.** Not verified and not cited. The DOI tried (10.1145/1963405.1963481) resolved to a different paper, so it should not be reused.

### Access notes
- Raw PDF text (pdftotext) was read for the sources linked to PDFs above. Saeb et al. was read as raw page text for the systematic-review figures, and blockCV Tutorial 2 as raw page text. WebFetch summaries were used for the Yuan project page, the LightGBM guide and the ICSE listing.
- DOIs in this note were checked on the Crossref API and arXiv IDs on the arXiv API in this session. The USENIX papers (Thomas, Pendlebury, Arp, Xu) have URLs instead of DOIs.
- Section numbers are given only where they were visible in the extracted text; otherwise the paragraph or table is named.

### Search log (audit trail for absence claims)
WebSearch queries, verbatim. "Domains" marks an allowed-domains filter.
- S1: sequential account IDs fake account detection batch registration
- S2: bot detection data leakage train test split same campaign inflated performance
- S3: GitHub fake accounts detection machine learning cross-validation leakage
- S4: feature coarsening binning defence memorization fingerprint campaign abuse detection generalization
- S5: leave-one-campaign-out evaluation fake accounts bot detection grouped split
- S6: Twitter user ID consecutive account creation time bot network created same day narrow window
- S7: "batch" registered malicious accounts detection registration sequence pattern paper
- S8: GitHub fake stars suspicious accounts created in batches low activity detection StarScout
- S9: social bot detection temporal split generalization evaluation pitfalls benchmark leakage 2024 2025
- S10: GitHub spam accounts detection classifier evaluation developer account suspended deleted prediction
- S11: GitHub account ID numeric sequential user id creation order inauthentic accounts research
- S12: bot account detection GitHub data leakage random split temporal evaluation inflated results (domains: arxiv.org, dl.acm.org, ieeexplore.ieee.org, link.springer.com, sciencedirect.com)
- S13: "Detecting Fake Accounts in Online Social Networks at the Time of Registrations" Ianus pdf WeChat
- S14: GroupKFold account-level split fraud bot detection same user train and test leakage inflated AUC (domains: arxiv.org, dl.acm.org, usenix.org, ndss-symposium.org, aclanthology.org)
- S15: feature abstraction discretization resilient classifier unseen campaigns malware aging bot detection coarse features (domains: arxiv.org, dl.acm.org, usenix.org, ndss-symposium.org)
- S16: account creation date feature artifact bot detection dataset account age confound label leakage (domains: arxiv.org, dl.acm.org, aaai.org, journals.plos.org, ojs.aaai.org)
- S17: "adjacent" user IDs train-test leakage account detection cross-validation numeric identifier
- S18: account creation batch group cross-validation abuse detection evaluation farm accounts same fold (domains: arxiv.org, dl.acm.org, usenix.org, ndss-symposium.org, ieeexplore.ieee.org)
- S19: Roberts 2017 cross-validation strategies block size residual autocorrelation range open access pdf Ecography
- S20: GitHub accounts disappeared deleted prediction GH Archive 404 account removal study
- S21: quantize features reduce memorization coordinated accounts bot classifier unseen botnet robustness coarse-grained (domains: arxiv.org, dl.acm.org, usenix.org, ojs.aaai.org)
- S22: "Detecting Clusters of Fake Accounts in Online Social Networks" pdf Xiao Freeman Hwa LinkedIn registration
- S23: SynchroTrap "Uncovering Large Groups of Active Malicious Accounts" pdf Facebook Instagram precision

arXiv API field queries, verbatim, with total hits (none relevant to the absence claims):
- A1: abs:github AND abs:leakage AND (abs:account OR abs:bot OR abs:spam) (2 hits, neither relevant)
- A2: abs:"data leakage" AND (abs:"bot detection" OR abs:"fake account") (0 hits)
- A3: abs:"train-test" AND abs:leakage AND (abs:bot OR abs:sybil OR abs:"fake account") (0 hits)
- A4: abs:"user id" AND abs:leakage AND abs:"cross-validation" (0 hits)
- A5: (abs:coarsening OR abs:discretization OR abs:binning) AND (abs:"bot detection" OR abs:"fake account" OR abs:sybil) (4 hits, none testing coarsening against campaign memorization by title; abstracts not read)

DBLP API queries attempted but failed (non-JSON response or HTTP 429), so DBLP was not checked: "github spam account"; "github fake account"; "github bot detection"; "github abuse detection"; "bot detection leakage"; "fake account leakage cross-validation"; "account creation batch"; "sequential id leakage". The Semantic Scholar batch endpoint also returned HTTP 429 on its second use.
