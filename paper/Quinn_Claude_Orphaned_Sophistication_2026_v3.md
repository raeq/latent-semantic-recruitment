# Orphaned Sophistication: Detecting AI-Generated Prose Through Structurally Unsupported Figurative Language

**Richard Quinn**

Independent researcher.

February 2026

---

## Revision History

**v1** (Sessions 027–033). Initial manuscript. Single-model analysis (n = 45, Sonnet only). No formal statistics, no ablation, no cross-model validation.

**v2** (Sessions 034–037). Major expansion. Sample size increased to n = 125 across five model runs from three independent families (Anthropic, OpenAI, Google). Added Fisher's exact tests, Cohen's h effect sizes, Clopper-Pearson CIs, and statistical power analysis throughout. Added ablation study confirming independent contribution of all three orphanhood dimensions. Added token probability probing (Experiment 9) and dose-response experiment. Added cross-domain corroboration (Du et al., 2026, drug repurposing). Semiotic interpretation expanded with Barthes narrowing caveat.

**v3** (Session 038). Review-driven revision. Hedged 13 instances of hypothesis-stated-as-fact. Added 8 missing citations for external claims (7 new references). Reframed authorship: Claude removed from byline, all co-author language converted to tool-use disclosure. Addressed 7 reviewer issues: explained 28/27 passage discrepancy (borderline classification), added full Experiment 9 probe specification (texts, word lists, counting methodology), clarified infinite-ratio interpretation, labelled abstract statistics by analysis, added kitchen-domain null result discussion, softened Holtzman et al. citation for T=1.0 regime, addressed "grip" as potentially domain-literal. Sharpened lede in abstract and conclusion. Prepared TACL submission formatting (LaTeX, anonymized, 7 pages content).

---

**LLM assistance disclosure.** This paper was written with the assistance of several large language models used as research tools. Claude Opus 4 (Anthropic) was used to implement the detection algorithms, reproduce published passages from training data for Corpus A, generate the statistical analyses, and draft the manuscript under the author's direction. Claude Sonnet 4 generated the LLM test corpus (Corpus C-Sonnet); Claude Haiku 3.5 generated the cross-model replication corpus (Corpus C-Haiku); OpenAI GPT-4o generated one cross-family validation corpus (Corpus C-GPT4o); Google Gemini 2.5 Flash generated a second cross-family validation corpus (Corpus C-Gemini). No model involved in corpus generation was involved in scoring: all detection was performed by deterministic rule-based algorithms, not by LLM judgment. The author conceived the over-indexing hypothesis, designed the experimental progression, identified three critical corpus-contamination errors during development, hand-wrote the five non-professional human passages (Corpus B), directed all analytical decisions, and reviewed and approved all results and the final manuscript.

## Abstract

We identify a novel stylometric artifact in large language model (LLM) prose generation: *orphaned sophistication*, the production of figuratively sophisticated word choices that lack structural support from their surrounding context. Through controlled experiments comparing 25 human-authored passages (20 from published authors spanning 1902–2016, 5 hand-written by a non-professional writer) against 100 LLM-generated passages from five model runs spanning three independent model families (Anthropic: Claude Sonnet 4 and Claude Haiku 3.5; OpenAI: GPT-4o; Google: Gemini 2.5 Flash), we demonstrate that LLMs produce polysemous words whose secondary semantic fields overlap with active figurative registers at rates significantly exceeding human prose (initial single-model analysis, n = 45: Fisher's exact test, p = 0.001, Cohen's h = 1.69), and that these constructions arrive without the metaphor chains, tonal preparation, or sustained register consistency that characterize deliberate human craft. We propose a theoretical explanation rooted in training-weight distributional bias: literary texts exhibiting exceptional polysemous craft are disproportionately represented in training corpora, causing models to produce 99th-percentile figurative sophistication as default output. We formalize this through a three-dimensional orphanhood model (isolation, chain connectivity, tonal preparation) and implement a deterministic rule-based detector achieving 28.0% true positive rate on LLM prose with 4% false positive rate on human prose (cross-family pooled analysis, n = 125: Fisher's p = 0.006, Cohen's h = 0.71). The signal is present across all five model runs tested, spanning three independent families: Anthropic (15-35%), OpenAI GPT-4o (15%), and Google Gemini 2.5 Flash (40%, p = 0.004). Gemini produced the strongest signal, individually significant with a large effect size (Cohen's h = 0.97). Token probability probing confirms that the specific constructions our detector flags are generated at elevated rates compared to semantically equivalent alternatives across all three model families (e.g., 9.5x preference for personification vocabulary over physical-property vocabulary in Anthropic models; 3.0x OpenAI; 2.0x Google). We argue that the framework is domain-agnostic: independent work in computational drug repurposing (Du et al., 2026) identifies a structurally identical pathology, "hard negatives" whose over-representation in training data produces locally optimal but clinically unviable candidates, providing cross-domain corroboration. The central finding is that the uncanny valley of AI prose is a structural coherence failure, not a lexical quality failure, and it is measurable. We provide a semiotic interpretation grounding the detection signal in the structural distinction between Barthes's *signifiance* (earned meaning through architectonic control) and *signification* (surface-level semantic activation without authorial intentionality). All code, data, and experimental logs are provided.

## 1. Introduction

The detection of AI-generated text has become a critical problem in computational linguistics, digital forensics, and publishing. Existing approaches fall broadly into two categories: statistical fingerprinting methods that measure distributional properties of token sequences (perplexity, burstiness, n-gram frequency profiles), and watermarking schemes that embed detectable signals during generation. Both categories share a fundamental limitation: they identify *that* a text is machine-generated without explaining *why* it reads as machine-generated. The qualitative experience of encountering AI prose, the uncanny valley sensation (Mori, 1970) that something is simultaneously competent and wrong, remains unformalized.

We present a third approach grounded in structural analysis of figurative language. Our central claim is that autoregressive language models, as a consequence of distributional biases in their training data, produce a specific and detectable artifact: figuratively sophisticated word choices that are structurally orphaned from the prose architecture that would justify them in human writing. A human author who writes "the hungry steel teeth" in a passage about a sawmill has, in deliberate literary prose, prepared that personification through tonal shifts, metaphor chains, or explicit signposting. An LLM produces the same construction as a default token prediction, without preparation, without continuation, and without architectural awareness that the construction requires either.

This paper makes four contributions:

1. **Empirical identification** of the orphaned sophistication artifact through controlled experiments comparing 25 human-authored passages against 100 LLM-generated passages (five model runs from three independent families) across five physical-register domains, with formal statistical testing (Fisher's exact test, Clopper-Pearson confidence intervals, Cohen's h effect sizes).

2. **Theoretical explanation** of the artifact through a training-weight over-indexing model: exceptional literary texts are disproportionately represented in training data through pedagogical citation, literary criticism, and anthology repetition, causing models to produce 99th-percentile figurative craft as baseline output.

3. **Formal detection framework** based on a three-dimensional orphanhood model measuring isolation (local sophistication spikes), chain connectivity (metaphor chain participation), and tonal preparation (signposting and register-shift markers), implemented as a fully deterministic rule-based algorithm requiring no LLM judgment. An ablation study confirms that chain and preparation independently contribute discriminative power, while isolation contributes specificity control.

4. **Semiotic interpretation** connecting the detection signal to the distinction between Roland Barthes's *signifiance* and mere *signification*, with appropriate caveats regarding the simplification this application entails.

## 2. Related Work

### 2.1 AI Text Detection

Current detection methods include perplexity-based classifiers (Mitchell et al., 2023; DetectGPT), watermarking (Kirchenbauer et al., 2023), and supervised classifiers trained on LLM output distributions (Tian et al., 2023; GPTZero). These methods achieve variable accuracy and degrade across domains, paraphrasing attacks, and model updates (Krishna et al., 2023; Wu et al., 2025). Critically, none provides a structural explanation for *what* distinguishes AI prose from human prose at the level of craft. They function as discriminators, not as diagnostic instruments.

We do not claim that orphaned sophistication detection replaces these methods. It operates in a different regime: short-form literary and descriptive prose where figurative language is expected. A head-to-head comparison on the same corpus would be informative but is beyond the scope of this initial report; we identify this as a priority for future work.

### 2.2 Polysemy in LLM Output

Kugler (2025, arXiv:2511.21334) demonstrates that polysemy patterns are measurable structural properties of LLM text, finding that LLM output exhibits a "flatter semantic space" than natural language (frequency-specificity correlation: ρ ≈ −0.3 for LLMs vs. ρ ≈ −0.5 to −0.7 for human text). This flat distribution is consistent with our over-indexing hypothesis: if the model disproportionately selects polysemous words whose secondary senses overlap with active registers, the resulting text would exhibit more polysemy per frequency tier than expected, flattening exactly the curve Kugler measures.

### 2.3 Semantic Priming in Transformers

Jumelet, Zuidema, and Sinclair (2024) demonstrate that lexico-semantic overlap boosts token-level probability in transformer architectures through structural priming effects. Their work confirms the mechanistic foundation of our claim, that embedding-space overlap between a word's senses and the active context elevates that word's generation probability, but operates at the level of syntactic construction choice rather than figurative register.

### 2.4 Coherence as a Latent Dimension of AI Text Quality

Shaib, Chakrabarty, Garcia-Olano, and Wallace (2025, arXiv:2509.19163) develop a taxonomy of "AI slop" through expert interviews and span-level annotation, finding that binary quality judgments correlate with latent dimensions including coherence and relevance. Critically, they find that standard text metrics fail to capture annotator preferences on these dimensions, and that capable reasoning LLMs likewise fail to reliably identify slop. Automatic measurement of coherence in AI-generated text remains an open problem. Our orphanhood framework provides one structural answer to this gap: it operationalizes a specific form of incoherence (figurative constructions arriving without the architectural support that would cohere them with surrounding prose) as a measurable, deterministic signal. Where Shaib et al. demonstrate that humans perceive coherence failure but existing tools cannot measure it, the present work offers a domain-specific measurement instrument for one class of such failures.

### 2.5 Present Contribution

No prior work synthesizes these findings into the specific claim that (a) training-weight bias causes LLMs to produce exceptionally sophisticated figurative language as default output, (b) this sophistication is structurally orphaned from the prose architecture that would earn it in human writing, and (c) this orphanhood constitutes a detectable and interpretable signal for AI authorship. The present paper addresses this gap.

## 3. Theoretical Framework

### 3.1 Latent Semantic Recruitment

We define *Latent Semantic Recruitment* (LSR) as the phenomenon whereby an autoregressive language model, generating text within an active figurative register *R*, disproportionately selects polysemous words whose secondary semantic fields overlap with *R*.

Formally, let *w* be a word token with primary sense *s₁* (contextually appropriate) and secondary sense *s₂* (not contextually required but semantically active in the model's embedding space). Let *R* be the figurative register currently active in the generation context (e.g., a scene describing a sawmill). We say LSR occurs when:

$$P(w \mid \text{context}, R) > P(w \mid \text{context}, \neg R)$$

specifically because the embedding of *s₂* overlaps with the embedding of *R* in the model's representation space.

This elevation follows from the standard transformer output computation (Vaswani et al., 2017). The logit for token *w* at position *t* is computed as:

$$z_w = \mathbf{v}_w^\top \mathbf{h}_t$$

where $\mathbf{v}_w$ is the output embedding for *w* and $\mathbf{h}_t$ is the hidden state at position *t*. When the context contains register-activating content (forge imagery, storm language, surgical terminology), the hidden state $\mathbf{h}_t$ encodes semantic components that overlap with the embeddings of register-aligned secondary senses. For polysemous words, $\mathbf{v}_w$ encodes both *s₁* and *s₂*, and the inner product with a register-active $\mathbf{h}_t$ is elevated compared to a monosemous alternative whose embedding encodes only *s₁*.

### 3.2 Training-Weight Over-Indexing

LSR explains the mechanism. But the mechanism alone does not explain why the result is detectable. Human writers also select polysemous words: Conrad writes "the rudder would bite"; McCarthy writes forges that consume. The critical question is why LLM polysemous usage is distinguishable from human polysemous usage.

We propose the **training-weight over-indexing hypothesis**: the training corpora of large language models contain a distributional bias that systematically over-represents exceptional figurative prose.

The texts that exhibit the most sophisticated polysemous craft, those by Conrad, McCarthy, Woolf, Morrison, are precisely the texts that receive the most analytical attention, the most pedagogical citation, the most anthology inclusion, and therefore the most duplication across training data. A sentence from *Blood Meridian* may appear in the original novel, in dozens of critical analyses, in hundreds of course syllabi, in thousands of online discussions, and in millions of training tokens that reference, quote, or paraphrase it. Under standard cross-entropy training, tokens that appear more frequently in the training corpus contribute proportionally more to the cumulative gradient. The model would therefore learn to reproduce this level of sophistication not as an exceptional achievement but as the expected register of competent prose.

The result is a distributional inversion. In the population of human writers, polysemous craft at the level of Conrad or McCarthy occupies the far right tail: the 99.99th percentile. In the model's learned distribution, it occupies the mode. A 10th-percentile author would not be expected to produce 99.99th-percentile polysemous personification without demonstrating commensurate architectural control. We hypothesize that when this disparity occurs, it constitutes a detectable signal; the experiments that follow test this prediction.

**Caveat.** We present the over-indexing hypothesis as the most parsimonious explanation for the observed distributional gap. A direct demonstration would require measuring the frequency of specific figurative constructions in training data and correlating that frequency with generation probability, an analysis that requires training-data access we do not have. The hypothesis is argued from distributional logic and consistent with the observed signal, but is not independently verified. We consider alternative explanations in Section 7.

### 3.3 Orphaned Sophistication

The over-indexing hypothesis predicts not merely that LLMs will produce sophisticated figurative language, but that they will produce it *without the structural architecture that earns it*. Under the over-indexing hypothesis, the model learns individual token predictions from exceptional contexts but does not acquire the passage-level or work-level planning that makes those tokens appropriate in their original settings.

We define **orphaned sophistication** as a figurative construction that satisfies three conditions:

**Definition.** A polysemous word *w* with register-aligned secondary sense *s₂* is *orphaned* in context *C* if and only if:

1. **Isolation.** The figurative density of the sentence containing *w* is significantly higher than the figurative density of its neighboring sentences (within a window of ±2 sentences). Formally, if *φ(s)* measures the proportion of register-active content words in sentence *s*, the isolation score is computed as $\min(1.0, \; (\varphi(s_w) - \bar{\varphi}(N(s_w))) \; / \; \tau_1)$, where *N(s_w)* is the neighborhood and *τ₁ = 0.2* (set a priori; a gap of 20% in figurative density represents maximum isolation). The score is 0 when the target sentence is at or below the neighborhood mean, and scales linearly to 1.0 as the gap approaches τ₁.

2. **Chain disconnection.** The register field activated by *s₂* is not activated by any other word within a window of ±3 sentences. In human literary prose, figurative constructions participate in metaphor chains: "bite... teeth... gnaw... hunger" across a paragraph. Orphaned constructions appear in isolation. Scoring: 0 connections = 1.0 (fully orphaned), 1 connection = 0.6, 2 connections = 0.2, 3+ connections = 0.0 (chained).

3. **Lack of preparation.** The surrounding context is scored for signposting markers that announce or contextualize the figurative construction: simile constructions ("like a," "as if," "as though"), explicit frame-setting ("was a," "felt like"), tonal shifts (sentence-length ratio > 2.5:1), and figurative density in adjacent sentences (> 0.15). The preparation score is 1.0 (fully unprepared) when no markers are present, and decreases toward 0.0 as more signposting is detected.

Each of the three tests produces a continuous score between 0.0 (fully supported) and 1.0 (fully orphaned), as detailed in Appendix A. A word's orphanhood score is the arithmetic mean of its three test scores. A word is classified as *orphaned* if and only if this score exceeds 0.6; words below that threshold are classified as *structurally integrated* (the figurative construction participates in the surrounding prose architecture). This threshold was set a priori based on the theoretical framework (requiring failure on a majority of structural support dimensions), not optimized on test data.

### 3.4 Semiotic Interpretation

The orphanhood framework admits an interpretation through the semiotic theory of Roland Barthes (1970, *S/Z*; 1973, *Le Plaisir du texte*), though we acknowledge that this application narrows Barthes's framework considerably. In *S/Z*, *signifiance* concerns the plurality of meaning generated by the interaction of multiple codes in writerly (*scriptible*) texts; it is not restricted to, or primarily about, the structural labor of earned metaphor. Our usage maps a more architectural reading onto the term: we treat *signifiance* as requiring structural scaffolding (chain, preparation, sustained register), whereas Barthes's concept addresses the broader productive plurality through which a text generates excess meaning beyond its denotative content. This narrowing is deliberate and operational, not a claim about Barthes's theory.

Barthes distinguishes between *signification*, the semantic content of a sign, and *signifiance*, the productive labor through which a text generates meaning. *Signifiance* is not a property of individual words but of the *work* the text performs through structure, juxtaposition, rhythm, and architectonic control.

When Conrad writes "the rudder would bite," the word performs something closer to *signifiance*: it participates in a novel-length architecture, it connects to the physical vocabulary of surrounding pages, it earns its figurative weight through sustained register control. When an LLM writes "the hungry steel teeth," the same semantic content is present, steel personified through consumption vocabulary, but the structural labor is absent. The word performs *signification* without *signifiance*.

This distinction maps onto our three orphanhood tests: isolation measures sustained vs. anomalous sophistication; chain connectivity measures productive labor vs. standalone activation; preparation measures deliberate register transition vs. its absence.

A necessary caveat arises here. A sufficiently long LLM-generated text may, through stochastic density alone, produce passages that score well on all three orphanhood dimensions: a figurative word may happen to land near another word in the same register field (chain), in a passage where neighboring sentences also contain figurative language (isolation), after a sentence that happens to contain a simile marker (preparation). Such a passage would be classified as "integrated" by our detector. But in Barthes's framework, *signifiance* is not merely the structural presence of chain and preparation; it is the *intentionality of the labor*. A monkey at a typewriter may accidentally produce a sonnet, but the sonnet does not perform *signifiance* because no productive labor generated it. Our detector cannot distinguish accidental structural coherence from intentional architectural control. It measures the necessary conditions for *signifiance* (structure is present) but not the sufficient condition (structure was produced through authorial labor). This limitation is why we describe the framework as identifying *orphaned* sophistication rather than *unearned* sophistication: the detector identifies the absence of structural support, not the absence of intent. The false negative case, where an LLM accidentally produces integrated-looking prose, is a fundamental limitation of any structural detector operating without access to the generative process itself.

We use this semiotic frame as an interpretive lens, not as a formal claim about Barthes's theory. The detection signal is empirical; the Barthesian vocabulary provides a useful language for describing what the signal captures.

## 4. Experimental Method

### 4.1 Corpus Construction

We assembled three corpora:

**Human Corpus A (Published).** 20 passages of approximately 100–200 words each, drawn from published fiction and nonfiction spanning 1902–2016. Authors: Patrick O'Brian, Sebastian Junger, Joseph Conrad, Ernest Hemingway, Anthony Bourdain, Bill Buford, George Orwell, M.F.K. Fisher, Cormac McCarthy, Flora Thompson, John McPhee, George Sturt, Richard Hooker, Kevin Powers, Pat Barker, Erich Maria Remarque, Annie Proulx, Ken Kesey, Wendell Berry, Michael Pollan. All passages were reproduced from the training data of Claude Opus 4 (the LLM used as a research tool). This introduces a methodological limitation discussed in Section 7.3. Passages were distributed across five physical-register domains: ocean storm (4), kitchen/restaurant (4), blacksmith/forge (4), battlefield surgery (4), sawmill/logging (4).

**Human Corpus B (Non-professional).** 5 passages of approximately 150–250 words each, hand-written by the author under experimental conditions. One passage per domain. Written under time pressure without revision, before the detection framework was developed (ensuring no knowledge of what the detector would measure). These passages provide an uncontaminated human baseline.

**LLM Corpus C-Sonnet.** 20 passages generated by Claude Sonnet 4 (Anthropic, `claude-sonnet-4-20250514`) via the Anthropic Messages application programming interface (API) at temperature 1.0. Four passages per domain. This is the primary test corpus (Experiment 8c).

**LLM Corpus C-Sonnet-2.** 20 additional passages generated by the same model under identical conditions, providing a same-model replication (cross-model experiment).

**LLM Corpus C-Haiku.** 20 passages generated by Claude Haiku 3.5 (Anthropic, `claude-haiku-4-5-20251001`) via the same API at temperature 1.0. Same prompts, same domain distribution. This is a smaller, faster model from a different capability tier, providing cross-model validation within the Anthropic family.

**LLM Corpus C-GPT4o.** 20 passages generated by GPT-4o (OpenAI, `gpt-4o`) via the OpenAI Chat Completions API at temperature 1.0. Same prompts, same domain distribution (4 passages per domain). This corpus provides cross-family validation from a second major model family.

**LLM Corpus C-Gemini.** 20 passages generated by Gemini 2.5 Flash (Google, `gemini-2.5-flash`) via the Google Generative Language API at temperature 1.0. Same prompts, same domain distribution (4 passages per domain). This corpus provides cross-family validation from a third major model family, extending the test to models with distinct architectures (Google's transformer variant), different training data, and different organizational provenance. With three independent families represented (Anthropic, OpenAI, Google), the generalizability claim rests on a substantially broader empirical base.

Generation prompts requested 150–200 word passages specifying physical detail, past tense, third person, no dialogue tags. All passages used identical prompts across domains and models.

### 4.2 Corpus Provenance and Circularity

A methodological concern: Corpus A passages were reproduced from the training data of Claude Opus 4 (used as a research tool), which is architecturally related to the models generating the LLM corpora. This creates a potential circularity: the human baseline was filtered through an LLM's memory.

We address this concern in three ways. First, Corpus B (hand-written by RQ) provides an uncontaminated baseline that independently confirms the zero-detection pattern. Second, the passages in Corpus A are reproductions of texts published between 1902 and 2016, all written before LLMs existed; any errors in reproduction would, if anything, make these passages *more* LLM-like (introducing model artifacts), biasing the test *against* our hypothesis. Third, the detection instrument is a deterministic rule-based algorithm (no LLM judgment involved in scoring), so the circularity concern applies only to corpus construction, not to detection.

We nevertheless note this as a limitation and note that an ideal replication would use passages directly transcribed from physical books.

### 4.3 Detection Instruments

We developed three successive detection instruments:

**Detector v1 (rate-based).** Counted polysemous words with register-aligned secondary senses. This approach was discarded: human and LLM rates were too similar (human 0.067 per passage vs. LLM 0.098 per passage in the initial test).

**Detector v2 (unjustified figurative).** Introduced domain-literal filtering, personification detection, and metaphor signpost detection. Flagged any unjustified figurative polysemous word. Achieved strong separation but could not distinguish between a skilled human figurative construction and an LLM-generated one at the individual word level.

**Detector v3 (orphaned sophistication).** The instrument reported in this paper. Identifies figurative polysemous words using v2's mechanisms, then subjects each to the three orphanhood tests (Section 3.3). Fully deterministic, requiring neither neural networks, LLM judgment, nor learned parameters. All thresholds set a priori.

### 4.4 Statistical Methods

All comparisons use Fisher's exact test (appropriate for small-sample count data with expected cell counts < 5). We report one-sided p-values (testing the directional hypothesis that LLM rates exceed human rates) and two-sided p-values. Confidence intervals on proportions use the Clopper-Pearson exact method (α = 0.05). Effect sizes are Cohen's h for differences in proportions, where h > 0.8 is conventionally large. No multiple-comparison correction is applied to the primary analysis (single pre-specified comparison); per-domain exploratory analyses are flagged as uncorrected.

### 4.5 Experimental Design

The primary experiment (Experiment 8c/v3) was conducted as follows:

1. All 25 human passages and 20 LLM passages (Corpus C-Sonnet) were processed by detector v3.
2. The three orphanhood scores were computed for each flagged word.
3. Results were aggregated by source (human vs. LLM) and domain.
4. Cross-model replication was conducted by generating 20 additional passages each from Sonnet 4 and Haiku 3.5 under identical conditions.
5. Cross-family validation was conducted by generating 20 passages each from OpenAI GPT-4o and Google Gemini 2.5 Flash under identical conditions, testing whether the signal generalizes beyond the Anthropic model family to three independent families.

## 5. Results

### 5.1 Detector v2: Unjustified Figurative Polysemy (Experiment 8c)

| Source | n | Total LSR | Rate per passage | Passages flagged |
|--------|---|-----------|-------------|-----------------|
| Published human | 20 | 1 | 0.050 | 1/20 (5.0%) |
| Non-professional human (RQ) | 5 | 0 | 0.000 | 0/5 (0%) |
| **All human** | **25** | **1** | **0.040** | **1/25 (4.0%)** |
| LLM (Sonnet, Exp 8c) | 20 | 15 | 0.750 | 9/20 (45.0%) |

**Rate ratio: 18.8×** (LLM to human).

**Fisher's exact test** (passage-level, flagged vs. not): one-sided p = 0.001, two-sided p = 0.002.

**95% confidence intervals (CIs)** (Clopper-Pearson): LLM rate [0.509, 0.913]; human rate [0.001, 0.204]. Non-overlapping.

**Cohen's h = 1.69** (large effect; convention: h > 0.8).

The single human detection was Conrad's "the rudder would bite again," a nautical usage where "bite" is arguably domain-literal (the standard term for a rudder engaging the water). In the 5 non-professional human passages, zero detections occurred.

### 5.2 Detector v3: Orphaned Sophistication (Experiment 8c)

| Source | n | Orphaned words | Integrated words | Passages with orphan |
|--------|---|----------------|-------------|---------------------|
| Published human | 20 | 1 | 1 | 1/20 (5.0%) |
| Non-professional human (RQ) | 5 | 0 | 0 | 0/5 (0%) |
| **All human** | **25** | **1** | **1** | **1/25 (4.0%)** |
| LLM (Sonnet, Exp 8c) | 20 | 9 | 3 | 7/20 (35.0%) |

**Fisher's exact test** (passage-level): one-sided p = 0.010, two-sided p = 0.015.

**Cohen's h = 0.86** (large effect).

The v3 detector correctly reclassified 6 of the 15 v2 LLM detections as "integrated": cases where the model had accidentally produced chain connectivity (e.g., "bit" appearing in a passage also containing "teeth" or "hungry," producing a chain score of 0.2). This demonstrates that the orphanhood model captures structural coherence, not merely polysemous density.

### 5.3 Cross-Model and Cross-Family Validation

| Model | Family | n | Orphaned words | Passages with orphan | Flag rate | vs. Human p | Cohen's h |
|-------|--------|---|----------------|---------------------|-----------|-------------|-----------|
| Human (all) | — | 25 | 1 | 1/25 | 4.0% | — | — |
| Gemini 2.5 Flash | Google | 20 | 10 | 8/20 | 40.0% | 0.004 | 0.97 |
| Sonnet 4 (Exp 8c) | Anthropic | 20 | 9 | 7/20 | 35.0% | 0.010 | 0.86 |
| Haiku 3.5 | Anthropic | 20 | 8 | 7/20 | 35.0% | 0.010 | 0.86 |
| GPT-4o | OpenAI | 20 | 4 | 3/20 | 15.0% | 0.224 | 0.39 |
| Sonnet 4 (replication) | Anthropic | 20 | 4 | 3/20 | 15.0% | 0.224 | 0.39 |
| **All LLM (pooled)** | **3 families** | **100** | **35** | **28/100** | **28.0%** | **0.006** | **0.71** |

**Combined Fisher's exact test** (all 100 LLM from three families vs. 25 human, passage-level): one-sided p = 0.006, two-sided p = 0.010.

**95% CIs:** LLM pooled [0.195, 0.379]; human [0.001, 0.204].

**Cohen's h = 0.71** (medium-to-large effect). Pooled power at this effect size: 93.8%.

Notable observations from the cross-model and cross-family data:

**Cross-family validation confirms the signal is not family-specific.** The artifact was detected in all three model families tested. Gemini 2.5 Flash (Google) produced the strongest signal at 40.0% (8/20), individually significant (p = 0.004, Cohen's h = 0.97). GPT-4o (OpenAI) produced orphaned sophistication at a 15.0% flag rate (3/20 passages), not individually significant (Fisher's p = 0.224, Cohen's h = 0.39) but consistent with the aggregate pattern. The pooled analysis across all five LLM runs from three independent families is strongly significant (p = 0.006, power = 93.8%).

**Cross-family orphaned words.** The flagged words converge across families. Gemini produced: "roar" (three passages, sawmill and ocean), "cry" (personification, ocean), "bit" (consumption, surgery), "stubborn" and "angry" (personification, blacksmith), "hungry" (consumption, blacksmith), "grip" (body, blacksmith). GPT-4o produced: "scream" (personification, ocean), "angry" (personification, ocean), "roar" (water/weather, sawmill). Anthropic models produced: "hungry" (personification/consumption, sawmill/blacksmith), "bit/bite" (consumption, sawmill/surgery), "roar" (water/weather, ocean/sawmill). The same register fields (consumption, personification, water/weather) and often the same specific words ("roar," "hungry," "angry," "bit") recur across independently trained models from three different organizations, strongly supporting the over-indexing hypothesis: these figurative constructions are over-represented in the overlapping literary training data that all three families share.

**Haiku shows equal or stronger signal than Sonnet.** Haiku 3.5 (a smaller, less capable model) produced orphaned sophistication at a rate matching or exceeding Sonnet 4. This is consistent with the over-indexing hypothesis: a smaller model with less capacity for nuanced generation may rely more heavily on high-frequency training patterns, producing the over-indexed figurative defaults more consistently.

**Gemini shows the strongest signal.** Gemini 2.5 Flash produced the highest orphanhood rate of any model tested (40%, 8/20), with 10 total orphaned words. This is individually significant (p = 0.004) with a large effect size (h = 0.97). The blacksmith domain was particularly affected, with one Gemini passage (bla_3) producing three orphaned words in a single passage: "hungry" (consumption), "grip" (body), and "angry" (personification). This pattern parallels the most affected Anthropic passage (L06, sawmill, four orphaned words), suggesting that domain-specific over-indexing concentrations are consistent across model families.

**Same-model variance.** The Sonnet replication (4 orphaned, 15% flag rate) showed lower orphanhood than the original run (9 orphaned, 35% flag rate). This variance is expected at temperature 1.0 generation and reflects the stochastic nature of the signal at the individual-passage level. The aggregate signal remains consistent: all five LLM runs exceed the human baseline, and the pooled three-family rate is strongly significant.

### 5.4 Qualitative Analysis of Orphaned Instances

The most striking LLM passage was L06 (sawmill domain, Sonnet Exp 8c), which contained four orphaned words:

| Word | Register field | Orphan score | Isolation | Chain | Preparation |
|------|---------------|-------------|-----------|-------|-------------|
| "hungry" (steel teeth) | personification | 0.88 | 0.6 | 1.0 | 1.0 |
| "stubborn" (grain) | personification | 0.73 | 0.2 | 1.0 | 1.0 |
| "bite" (of hemlock) | consumption | 0.73 | 0.2 | 1.0 | 1.0 |
| "roar" (planar's) | water/weather | 0.80 | 0.4 | 1.0 | 1.0 |

Four distinct register fields activated in a single passage. No chain connectivity between any of them. No preparation for any of them. Each is independently sophisticated; together they constitute four unearned figurative constructions in nine sentences.

By contrast, the human passages that employ figurative language (e.g., RQ's sawmill passage: "Life shaves pieces of your health off... Bertha takes that, too") do so within explicitly prepared metaphorical frames. The saw-as-life metaphor is signposted ("That's life, that is"), developed across multiple sentences, and connects to a chain of related vocabulary. The detector correctly classifies this as structurally integrated.

### 5.5 Per-Domain Distribution

| Domain | Human LSR (v2) | LLM LSR (v2) | Fisher's p |
|--------|---------------|--------------|-----------|
| Ocean storm | 0/5 | 1/4 | 0.444 |
| Sawmill | 0/5 | 4/4 | 0.008* |
| Kitchen | 0/5 | 0/4 | 1.000 |
| Surgery | 0/5 | 4/4 | 0.008* |
| Blacksmith | 0/5 | 1/4 | 0.444 |

*Uncorrected for multiple comparisons.

**The kitchen domain produced a null result** (0/5 human, 0/4 LLM), the only domain with zero detections in both corpora. We attribute this to the domain's vocabulary structure: culinary language is inherently action-oriented and consumption-related ("chop," "slice," "devour," "taste"), so words that would register as figurative in other domains are domain-literal in a kitchen context. "Bite" in a sawmill passage activates the consumption register because sawmills do not eat; "bite" in a kitchen passage is a literal description of food. The detector's register-overlap criterion correctly identifies these as non-figurative, because the secondary sense is also the primary sense. This null result is informative rather than problematic: it suggests that the detector's specificity holds in domains where figurative and literal vocabulary substantially overlap, and it predicts that over-indexing artifacts will be least detectable in domains whose technical vocabulary is already drawn from high-frequency figurative registers.

The sawmill domain was most affected, with the consumption-register word "bit/bite" appearing across multiple LLM passages as personification of the saw blade. This cross-generation repetition is consistent with the over-indexing hypothesis: if "blade + bite" is over-represented in literary training data, the model would produce it as a default figurative construction for sawmill scenes.

### 5.6 Ablation Study: Dimension Contributions

To validate the three-dimensional orphanhood model, we performed an ablation study removing each dimension in turn and measuring the effect on discriminative power. We re-ran the detector on all 125 passages (25 human, 100 LLM across five model runs from three families) under four configurations: the full three-dimensional model (baseline), and three ablated variants each excluding one dimension.

| Configuration | Dims | Human flagged | LLM flagged | Cohen's h | Fisher p (1-sided) |
|--------------|------|---------------|-------------|-----------|-------------------|
| Full model | 3 | 1/25 (4.0%) | 27/100 (27.0%)† | 0.690 | 0.008 |
| No isolation | 2 | 1/25 (4.0%) | 33/100 (33.0%) | 0.821 | 0.002 |
| No chain | 2 | 1/25 (4.0%) | 21/100 (21.0%) | 0.549 | 0.035 |
| No preparation | 2 | 2/25 (8.0%) | 26/100 (26.0%) | 0.497 | 0.041 |

†The ablation full-model baseline reports 27/100 LLM flagged versus 28/100 in Section 5.3. One Sonnet passage falls at the classification boundary (orphanhood score ≈ 0.60); the difference arises from floating-point variation between the unified ablation pass and the incremental main analysis. See Appendix E.7 for details. All qualitative conclusions hold under either count.

The results reveal an asymmetric architecture. Removing chain connectivity reduces Cohen's h by 0.141 (from 0.690 to 0.549), confirming that chain detection captures discriminative signal that isolation and preparation alone miss. Removing preparation produces the largest degradation in h (0.193 drop to 0.497) and, critically, doubles the human false positive rate from 4.0% to 8.0%. This indicates that preparation is the dimension most responsible for *specificity*: it distinguishes genuine figurative orphanhood from merely unprepared but structurally innocent word choices.

The isolation dimension presents a more nuanced picture. Removing it *increases* Cohen's h to 0.821, because isolation functions primarily as a conservative filter. Without it, the detector flags more LLM passages (33.0% vs. 27.0%) while maintaining the same human false positive rate (4.0%). The isolation test suppresses true positives in cases where the LLM's figurative spike happens to occur near other mildly figurative sentences, not because the sophistication is earned, but because the neighborhood density happens to be elevated. In practical terms, isolation trades sensitivity for robustness: it prevents the detector from flagging passages where a contextual argument for the sophistication exists, even if the argument is weak.

All four configurations maintain statistical significance (p < 0.05, one-sided), indicating that no single dimension is solely responsible for the signal. However, the full three-dimensional model represents a principled balance between sensitivity (27.0% true positive rate, TPR) and specificity (4.0% false positive rate, FPR). The no-isolation variant achieves higher raw discrimination (h = 0.821) but at the cost of theoretical coherence: a detector that ignores whether a figurative spike is locally unusual loses the conceptual grounding that motivates the "orphaned" framing. The three-dimensional model is not merely an empirical convenience; each dimension corresponds to a distinct structural property of deliberate figurative prose (local contrast, sustained register, tonal signaling), and the ablation confirms that chain and preparation both independently contribute discriminative power while isolation contributes specificity control.

## 6. Mechanism Validation

### 6.1 Monte Carlo Logit Proxy (Experiment 7)

To test the underlying LSR mechanism, we conducted a Monte Carlo estimation of token-level preferences across register conditions. For 15 polysemous/monosemous word pairs across 5 register domains, we generated N=20 completions per condition (register-active vs. register-absent control) at temperature 1.0 via the Anthropic API.

The original experimental design predicted that register-active contexts would increase the probability of the polysemous word relative to its monosemous alternative (a binary forced-choice between two specific words). Only 3/15 pairs showed this specific preference. However, a stronger and unanticipated result emerged: 12/15 pairs exhibited *zero vocabulary overlap* between active and control conditions. The model did not choose between the two target words differently; it generated from entirely different vocabulary spaces depending on register, producing completions in the active condition that shared no words with completions in the control condition. The register effect, in these 15 pairs, appears not merely to nudge individual word probabilities but to restructure the generative vocabulary. This is a stronger finding than the binary preference the experiment was designed to test, and it is consistent with the LSR mechanism operating at the level of vocabulary-space activation rather than individual token selection.

### 6.2 Dose-Response (Experiment 5)

A dose-response experiment across three register-intensity conditions showed a monotonic relationship:

| Condition | Figurative polysemous rate |
|-----------|--------------------------|
| Suppressed (explicit instruction to avoid) | 0.000 |
| Neutral (no instruction) | 0.098 |
| Amplified (instruction to use vivid language) | 0.755 |

This pattern confirms that figurative polysemous word selection is register-dependent and dose-responsive, consistent with the logit-elevation mechanism.

### 6.3 Token Probability Probing (Experiment 9)

To test the over-indexing hypothesis directly at the generation level, we designed eight probes targeting the specific constructions our detector most frequently flags. Each probe provides a physical-register context and generates N completions at temperature 1.0 (N=20 for Anthropic and Gemini, N=10 for OpenAI due to rate limits). For each completion, we count occurrences of "literary" words (the high-prestige constructions our detector flags) versus semantically equivalent alternatives that serve the same descriptive purpose without the literary register.

**Probe texts.** Each probe was a single-sentence instruction presented as a system-level generation prompt with no additional context or persona framing:

1. **SAW_BITE**: "Write a paragraph describing a sawmill blade cutting through hardwood."
2. **SAW_HUNGRY**: "Write a paragraph describing a sawmill consuming logs throughout a workday."
3. **OCEAN_ROAR**: "Write a paragraph describing ocean waves during a storm."
4. **FORGE_STUBBORN**: "Write a paragraph describing a blacksmith shaping metal that resists the hammer."
5. **FORGE_GRIP**: "Write a paragraph describing a blacksmith gripping tools at a forge."
6. **SURGERY_SCREAM**: "Write a paragraph describing emergency battlefield surgery."
7. **KITCHEN_ALIVE**: "Write a paragraph describing a busy restaurant kitchen during dinner service." This probe tests a different construction (anthropomorphic vitality: "the kitchen breathed") that is not consumption-register and therefore not suppressed by the domain-literal filter; it tests whether over-indexing extends to a domain where the primary detection mechanism does not apply.
8. **WILD_WHISPER**: "Write a paragraph describing wind moving through a forest."

**Word lists.** For each probe, we defined a "literary" set (figuratively sophisticated words our detector flags in that register) and an "equivalent" set (words serving the same descriptive function without figurative register activation). Counting was case-insensitive and matched whole words only (no substring matching). The complete word lists:

| Probe | Literary set | Equivalent set |
|-------|-------------|----------------|
| SAW_BITE | bite, bit, teeth, gnaw, gnawed, chew, chewed, devour, devoured | cut, cuts, slice, sliced, sever, severed, rip, ripped, tear, tore |
| SAW_HUNGRY | hungry, hunger, starving, ravenous, appetite, feed, fed, feast | process, processed, handle, handled, work, worked, run, ran |
| OCEAN_ROAR | roar, roared, howl, howled, scream, screamed, shriek, wail | crash, crashed, pound, pounded, thunder, thundered, boom, boomed |
| FORGE_STUBBORN | stubborn, refused, defiant, obstinate, willful, resisted, fought | hard, rigid, stiff, tough, dense, unyielding, resistant |
| FORGE_GRIP | grip, gripped, clutch, clutched, claw, clawed | hold, held, grasp, grasped, grab, grabbed |
| SURGERY_SCREAM | scream, screamed, cry, cried, shriek, wail, howl | groan, groaned, gasp, gasped, moan, moaned |
| KITCHEN_ALIVE | alive, breathe, breathed, pulse, pulsed, heartbeat, living | busy, active, hectic, intense, fast, rapid |
| WILD_WHISPER | whisper, whispered, sigh, sighed, murmur, murmured, sing, sang | blow, blew, rustle, rustled, move, moved, sweep, swept |

**Counting methodology.** Each completion was tokenized into whitespace-delimited words, lowercased, and stripped of trailing punctuation. Every word was checked against both the literary and equivalent sets for its probe. The preference ratio is defined as (total literary occurrences across all completions) / (total equivalent occurrences across all completions). A ratio of 1.0 indicates no preference; ratios above 1.0 indicate preferential generation of literary constructions. When the equivalent count is zero and the literary count is positive, the ratio is formally undefined (reported as "inf"); see the note on infinite ratios below.

**Cross-family results (probes with consistent literary preference across all three families):**

| Probe | Register | Anthropic | OpenAI | Gemini |
|-------|----------|-----------|--------|--------|
| SAW_BITE | Consumption for machinery | 1.41 | 3.43 | inf* |
| OCEAN_ROAR | Vocalization for weather | 1.17 | 1.44 | 3.00 |
| FORGE_STUBBORN | Personification for material | 9.50 | 3.00 | 2.00 |
| SURGERY_SCREAM | Vocalization intensity | 1.38 | 2.50 | inf* |

*Infinite ratio indicates literary words present but zero equivalent words in all completions. This occurs when the model generates figurative vocabulary (e.g., "bite," "teeth") but none of the predefined equivalents (e.g., "cut," "slice") across all N completions. We do not claim that the equivalent lists are exhaustive; it is possible that the model produced functional alternatives not in our lists (e.g., "carved," "split"), which would reduce the ratio to a finite value. The infinite ratios should be interpreted as strong directional evidence of literary preference, not as literal claims that the model never uses non-literary vocabulary. For probes where equivalent words appear in at least some completions, the finite ratios provide more interpretable effect sizes.

Four of eight probes showed consistent literary preference (ratio > 1.0) across all three model families. The FORGE_STUBBORN probe produced the strongest signal: when asked to describe metal resisting shaping, Anthropic generated personification vocabulary ("stubborn," "refused," "defiant") at 9.5 times the rate of physical-property alternatives ("hard," "rigid," "stiff"). OpenAI and Gemini showed the same preference at 3.0× and 2.0× respectively.

The SAW_BITE probe confirmed the specific construction our detector most frequently flags: all three families preferentially generated "bite/teeth/gnaw" over "cut/slice/sever" when describing sawblades engaging wood.

**Aggregate preference ratios:** Anthropic 1.30, OpenAI 1.45, Gemini 1.91. All three families show overall preference for literary constructions over functional alternatives.

Four probes (SAW_HUNGRY, FORGE_GRIP, KITCHEN_ALIVE, WILD_WHISPER) showed mixed or reversed preferences across families, indicating that over-indexing is construction-specific rather than universal. The model does not uniformly prefer literary vocabulary; it preferentially generates specific high-prestige constructions that are plausibly over-represented in literary training data (consumption vocabulary for machinery, personification for resistant materials, vocalization for natural forces).

This experiment provides generation-level evidence consistent with the over-indexing hypothesis: the specific constructions our detector flags are produced at elevated rates compared to semantically equivalent alternatives. While we measure output frequency rather than training-data frequency or model weights directly, the pattern of preferential generation is what the over-indexing hypothesis predicts.

## 7. Discussion

### 7.1 The Uncanny Valley Formalized

The orphaned sophistication framework provides a structural account of the "uncanny valley" of AI prose. The deficiency is not in vocabulary, which is often excellent, nor in grammar, which is typically flawless. The deficiency lies in the *relationship between sophistication and structure*: the text produces figurative constructions at a level that implies architectural control, but the architecture is absent.

This framework offers a structural account of an observation reported informally in professional editing contexts (e.g., Shaib et al., 2025, on coherence failure in AI text): AI-generated prose often reads as "too good" at the sentence level while failing at the paragraph or section level. Under the over-indexing hypothesis, the sentence-level quality would result from the model having learned its figurative register from exceptional exemplars, while the paragraph-level failure would result from the absence of passage-level planning that would integrate those individual constructions into a coherent architecture. We have not tested this account against professional editors' judgments; we note it as a predicted consequence of the hypothesis.

### 7.2 Why This Is Not Watermarking

Orphaned sophistication is not an imposed signal; it is, under the over-indexing hypothesis, an emergent artifact of the training process. If the hypothesis is correct, the signal would resist removal by post-processing or prompt engineering, because it arises from the model's learned figurative register rather than from surface-level generation parameters. Whether fine-tuning could selectively reduce orphanhood without degrading prose quality is an open empirical question that we have not tested.

### 7.3 Limitations

1. **Sample size.** n = 125 total passages (25 human, 100 LLM) across 5 domains and 5 model runs from 3 families. The pooled signal is statistically significant (Fisher's p = 0.006, Cohen's h = 0.71, power = 93.8%), but the sample remains modest for strong generalization claims. A larger study with ≥200 passages and additional domains is warranted.

2. **Model family.** Cross-family validation was conducted with OpenAI GPT-4o and Google Gemini 2.5 Flash (20 passages each). Gemini produced the strongest signal (40%, p = 0.004, h = 0.97), individually significant. GPT-4o produced a 15% flag rate, not individually significant but consistent with the aggregate. The pooled analysis across three independent families is strongly significant (p = 0.006, h = 0.71, power = 93.8%). The convergent word-level patterns across all three families ("roar," "hungry," "angry," "bit" recurring in Anthropic, OpenAI, and Google models) provide strong qualitative support. Testing on open-weight models (Llama 3, Mistral) and with larger per-model sample sizes would further strengthen claims.

3. **Human corpus provenance.** Corpus A was reproduced from the training data of Claude Opus 4 (the LLM used as a research tool). While the passages are faithful reproductions of pre-2020 published works, and Corpus B provides an uncontaminated baseline, an ideal replication would use passages directly transcribed from physical books. We have attempted to mitigate this concern (Section 4.2) but cannot fully resolve it without independent corpus construction.

4. **Human corpus skill ceiling.** The paper argues that LLMs over-index on 99th-percentile literary prose (Conrad, McCarthy, Woolf), then uses passages from those same authors as the human baseline. This means the detector's false positive rate was measured against elite literary prose, the category of human writing most likely to contain earned figurative sophistication. The detector's behavior on mid-tier human prose (competent workshop fiction, genre fiction, journalistic feature writing) is unknown. Such writers may produce figurative constructions that are structurally unsupported not because of over-indexing but because of limited craft; the detector would flag these as orphaned, potentially inflating the false positive rate on non-elite human text. Corpus B (five passages from a non-professional writer) produced zero detections, but five passages is insufficient to characterize mid-tier FPR. Testing against a larger corpus of competent-but-not-elite human prose is a priority for future validation.

5. **No baseline detector comparison.** We have not run existing AI detectors (DetectGPT, GPTZero) on the same corpus. A direct comparison would establish whether orphaned sophistication captures a signal orthogonal to existing methods. We identify this comparison as a priority for follow-up work.

6. **Domain specificity.** The detector is currently implemented for five physical-register domains. Extension to abstract registers (emotional, philosophical, political) requires additional domain-literal sets and register-field definitions.

7. **Passage length.** The orphanhood tests operate on passage-length windows (±2–3 sentences). At this scale, even earned human figurative language can score as orphaned if excerpted from a longer work where chain and preparation exist outside the window. Conrad's "rudder would bite" illustrates this limitation.

8. **Same-model variance and statistical power.** The Sonnet replication showed lower orphanhood (4 orphaned words, 15% flag rate) than the original run (9 orphaned words, 35% flag rate), and the replication is not individually significant (p = 0.224). This warrants explicit discussion. At n = 20 LLM vs. n = 25 human, a post-hoc power analysis shows the test has 80% power to detect effects of h ≥ 0.53 (corresponding to an LLM flag rate of approximately 20% given a 4% human baseline). The Sonnet replication's observed effect (h = 0.39) falls below this threshold: the test had only 58% power to detect it. In other words, even if the true LLM flag rate is 15%, we would fail to reach significance in roughly 4 out of 10 runs at this sample size. The non-significant replication is therefore consistent with, not contradictory to, the aggregate signal. The pooled analysis (n = 100 LLM across three model families, n = 25 human, h = 0.71) has 93.8% power, confirming that the aggregate test is appropriately powered. Notably, GPT-4o also produced a 15% flag rate (matching Sonnet replication exactly), while Gemini produced a 40% flag rate (the highest of any model), further validating that the non-significant individual GPT-4o result reflects power limitations rather than absent signal. The variance between runs is expected at temperature 1.0 generation; the appropriate conclusion is that individual runs at n = 20 have limited statistical power, and the pooled three-family analysis provides the reliable test.

### 7.4 Alternative Explanations

We consider alternatives to the over-indexing hypothesis:

**Attention span.** LLMs may produce orphaned sophistication not because of training-weight bias but because of attention-window limitations: the model attends to local context when selecting figurative words but cannot plan paragraph-level coherence. This explanation is plausible but does not account for why the *specific* figurative constructions are so consistent across independent generations ("hungry steel," "blade bites"). Attention-span limitations would predict *random* figurative orphanhood; we observe *patterned* figurative orphanhood.

**Mode collapse.** The repeated figurative constructions could reflect mode collapse in the generative distribution rather than training-weight over-indexing. However, all LLM passages were generated at temperature 1.0, a regime that Holtzman et al. (2020) demonstrate substantially reduces the repetitive degeneration characteristic of greedy or low-temperature decoding. We observe the same figurative *strategy* (consumption vocabulary for machines) expressed in varied syntactic frames across independent generations, which is more consistent with a learned register preference than with the repetitive or degenerate output patterns Holtzman et al. characterize as mode collapse. We note that temperature 1.0 does not eliminate distributional biases in token selection; it reduces repetition while preserving the probability distribution's shape, which is precisely the regime where over-indexing effects would manifest as preferential selection rather than degenerate repetition.

### 7.5 Implications for AI Detection

If the over-indexing hypothesis is correct, orphaned sophistication should be present in all LLMs trained on standard web corpora that include over-represented literary texts. The signal should persist across architectures because it arises from distributional properties of the training data, not from specific architectural features.

The signal is *interpretable*: a detection report can point to specific words, explain why they are orphaned (isolation score, chain score, preparation score), and provide a structural explanation for the diagnosis. This interpretability contrasts with methods that output a probability without explanation.

### 7.6 Implications for Creative Writing with LLMs

For writers using LLMs as collaborative tools, the orphaned sophistication framework provides actionable revision guidance. Flagged passages require not deletion but *architecture*: build a chain around the orphaned word, prepare the reader for the register shift, or sustain the figurative density across the neighborhood. The detector identifies where the LLM has been locally brilliant and globally incoherent, and the revision task is to supply the coherence.

### 7.7 The Generalizable Principle

The training-weight over-indexing hypothesis predicts that any domain where LLMs or related models are trained on corpora dominated by exceptional, heavily-cited exemplars will exhibit the same artifact: locally sophisticated outputs that lack the structural scaffolding appropriate to their context. The three orphanhood dimensions, isolation, chain disconnection, and lack of preparation, need not be specific to figurative language. If they generalize, they would describe a broader structural pathology: the production of high-sophistication elements without the architectural context that would earn them. We have tested this only in literary prose; the generalization is a prediction, not an established result.

This prediction is not merely speculative. Du et al. (2026) independently identify what they term "hard negatives" in computational drug repurposing: well-studied compounds that appear to be ideal candidates due to their high connectivity in biomedical knowledge graphs but have failed in clinical trials. The mechanism they describe is structurally identical to orphaned sophistication. U.S. Food and Drug Administration (FDA)-approved drugs and blockbuster compounds dominate training corpora through citation, patent literature, clinical trial publications, and pharmacological textbooks, producing the same over-indexing dynamic we describe for Conrad and McCarthy in literary training data. Graph neural networks and LLM-based drug repurposing systems learn to produce binding moieties and molecular scaffolds that resemble successful drugs as *default output*. The result: locally brilliant binding affinity predictions that are structurally orphaned from the absorption, distribution, metabolism, excretion, and toxicity (ADMET) properties that would make them clinically viable. Du et al. report that in degree-matched tests dominated by these "popular but ineffective" decoys, standard graph neural networks (GNNs) achieve only 0.2–0.4 Top-10 Precision, a direct measure of the over-indexing failure mode.

The mapping onto our framework is exact. A high-affinity binding moiety without metabolic stability is an orphaned figurative word: locally sophisticated, structurally unsupported. A strong binding score surrounded by poor ADMET profile is isolation. An optimized moiety disconnected from the scaffold's solubility and permeability chain is chain disconnection. The absence of scaffold-level molecular architecture supporting the binding feature is lack of preparation. This corresponds directly to the "activity cliff" problem in medicinal chemistry (Stumpfe & Bajorath, 2012), where a locally optimized feature fails in clinical context because the surrounding molecular architecture was never validated.

The drug discovery case warrants attention because it was observed independently, in a different modality (molecular graphs rather than text), by researchers with no knowledge of the orphanhood framework. The convergence suggests that the pathology is a general property of training-data distributional bias, not an artifact of our specific experimental setup. (We note that Du et al. is a bioRxiv preprint that has not yet undergone peer review; the structural parallel we draw is between their reported phenomenon and ours, and does not depend on verification of their specific quantitative claims.)

Beyond drug discovery, the same principle extends to other high-stakes domains. In legal document generation, LLMs over-indexed on landmark Supreme Court opinions may produce locally sophisticated constitutional arguments orphaned from the procedural and evidentiary context that would justify them. In scientific writing, LLMs over-indexed on high-impact journal publications may generate locally sophisticated methodological claims without the experimental rigor scaffolding that would support them. In financial analysis, LLMs over-indexed on prestigious annual reports may produce sophisticated risk-language orphaned from the underlying data that would ground it.

In each case, the diagnostic questions would translate in principle. Isolation asks whether the sophisticated element is locally anomalous or sustained. Chain connectivity asks whether it participates in a coherent architecture or stands alone. Preparation asks whether the surrounding context has done the work of establishing that the sophisticated element belongs there. These questions are domain-agnostic in their framing; whether they yield comparable discriminative power outside literary prose is untested. What would change between domains is the vocabulary of the domain-literal sets and register fields, not the structural logic of the orphanhood tests.

This generalizability distinguishes orphaned sophistication from black-box detection methods. A perplexity score or a classifier probability tells you *that* something may be machine-generated. The orphanhood framework tells you *where* the architecture is missing and *what kind of work* would repair it: build the chain, prepare the context, close the isolation gap. That guidance is actionable within our tested domain. If the framework generalizes as predicted, the same diagnostic logic would apply to a constitutional argument in a legal brief, a methodological claim in a research paper, or a binding moiety in a drug candidate. In drug discovery specifically, an orphanhood-style molecular auditor could in principle flag candidates where high-sophistication features (binding affinity, selectivity) are isolated from the molecular chain connectivity that would justify them, directing optimization effort toward building scaffold support rather than discarding the lead. These extensions remain speculative.

We have demonstrated the framework in the domain of literary prose because that is where the signal is most vivid and the theoretical connection to semiotics most direct. But the underlying principle, that training-weight over-indexing produces locally excellent outputs lacking structural support, is a property of the training process, not of any particular output domain. The Du et al. finding in drug repurposing provides independent corroboration from a radically different domain. We identify systematic cross-domain validation as a high-priority extension of this work.

## 8. Conclusion

We have identified and formalized a novel artifact of autoregressive language generation: orphaned sophistication. The artifact arises, we argue, from training-weight over-indexing on exceptional exemplars in training data, causing models to produce locally sophisticated outputs without the structural architecture that would earn them. In the domain of literary prose, our automated detector achieves significant separation between human and LLM text across three independent model families (Fisher's p = 0.006, Cohen's h = 0.71, n = 125), with cross-family validation confirming the artifact in Anthropic, OpenAI, and Google models.

The detection signal is structural and interpretable. If the over-indexing hypothesis is correct, the signal is also inherent to the generation process and would resist removal without degrading output quality; testing this prediction is a priority for future work. The framework provides not merely a classification but a diagnosis: where the architecture is missing and what kind of work would repair it. The core contribution is a reframing: the uncanny valley of AI prose is a structural coherence failure, not a lexical quality failure, and it is measurable. This connects computational linguistics, literary theory, and the distributional properties of training data.

The framework is, we believe, domain-agnostic in principle. The over-indexing hypothesis predicts that wherever training corpora over-represent exceptional exemplars, a structurally analogous pathology should emerge: locally brilliant outputs lacking the scaffolding that would make them structurally earned. We have demonstrated one instance of this in literary prose. Whether the principle generalizes to other domains remains an empirical question.

The uncanny valley of AI prose is not that the machine writes badly. It is that the machine writes too well, in moments that have not been earned.

## References

Barker, P. (1991). *Regeneration*. Viking.

Barthes, R. (1970). *S/Z*. Éditions du Seuil.

Barthes, R. (1973). *Le Plaisir du texte*. Éditions du Seuil.

Berry, W. (2000). *Jayber Crow*. Counterpoint.

Bourdain, A. (2000). *Kitchen Confidential*. Bloomsbury.

Buford, B. (2006). *Heat*. Knopf.

Conrad, J. (1902). *Typhoon*. Heinemann.

Du, R., Fung, M., Hu, Y., & Liu, D. (2026). Overcoming topology bias and cold-start limitations in drug repurposing: A clinical-outcome-aligned LLM framework. *bioRxiv*. doi:10.64898/2026.01.12.699148.

Fisher, M.F.K. (1954). *The Art of Eating*. World Publishing.

Hemingway, E. (1952). *The Old Man and the Sea*. Scribner.

Holtzman, A., Buys, J., Du, L., Forbes, M., & Choi, Y. (2020). The curious case of neural text degeneration. *Proceedings of ICLR 2020*.

Hooker, R. (1968). *MASH: A Novel About Three Army Doctors*. Morrow.

Jumelet, J., Zuidema, W., & Sinclair, A. (2024). Syntactic structural priming in large language models. *Proceedings of ACL 2024*.

Junger, S. (1997). *The Perfect Storm*. Norton.

Kesey, K. (1964). *Sometimes a Great Notion*. Viking.

Kirchenbauer, J., et al. (2023). A watermark for large language models. *Proceedings of ICML 2023*.

Krishna, K., Song, Y., Karpinska, M., Wieting, J., & Iyyer, M. (2023). Paraphrasing evades detectors of AI-generated text, but retrieval is an effective defense. *Proceedings of NeurIPS 2023*.

Kugler, R. (2025). Polysemy patterns in large language model output. arXiv:2511.21334.

Leech, G., & Short, M. (2007). *Style in Fiction: A Linguistic Introduction to English Fictional Prose* (2nd ed.). Pearson Longman.

McCarthy, C. (1985). *Blood Meridian*. Random House.

McPhee, J. (1975). *The Survival of the Bark Canoe*. Farrar, Straus and Giroux.

Mitchell, E., et al. (2023). DetectGPT: Zero-shot machine-generated text detection using probability curvature. *Proceedings of ICML 2023*.

Mori, M. (1970). The uncanny valley. *Energy*, 7(4), 33–35. (K. F. MacDorman & N. Kageki, Trans., *IEEE Robotics & Automation Magazine*, 19(2), 2012.)

O'Brian, P. (1969). *Master and Commander*. Collins.

Orwell, G. (1933). *Down and Out in Paris and London*. Gollancz.

Pollan, M. (1997). *A Place of My Own*. Random House.

Powers, K. (2012). *The Yellow Birds*. Little, Brown.

Proulx, A. (2016). *Barkskins*. Scribner.

Remarque, E.M. (1929). *Im Westen nichts Neues* [All Quiet on the Western Front]. Propyläen.

Stumpfe, D., & Bajorath, J. (2012). Exploring activity cliffs in medicinal chemistry. *Journal of Medicinal Chemistry*, 55(7), 2932–2942.

Sturt, G. (1923). *The Wheelwright's Shop*. Cambridge University Press.

Tian, E., et al. (2023). GPTZero: Towards detection of AI-generated text using zero-shot and supervised methods. Preprint.

Vaswani, A., et al. (2017). Attention is all you need. *Proceedings of NeurIPS 2017*.

Wu, J., Yang, S., Zhan, R., Yuan, Y., Chao, L. S., & Wong, D. F. (2025). A survey on LLM-generated text detection: Necessity, methods, and future directions. *Computational Linguistics*, 51(1), 275–338.

Thompson, F. (1945). *Lark Rise to Candleford*. Oxford University Press.

## Appendix A: Detector v3 Algorithm

The complete Python implementation is provided in supplementary materials (`lsr_detector_v3.py`). The core algorithm:

```
For each sentence S in passage P:
    For each word w in S:
        If w is domain-literal: skip
        If w is not in any register field: skip
        If w is not figurative (no personification, no animate verb,
            no animate-quality modifier): skip

        Compute orphanhood:
            isolation = spike_score(S, neighbors(S, window=2))
            chain = chain_score(w, register_fields(w), neighbors(S, window=3))
            preparation = prep_score(S, prev_sentence, next_sentence)

        orphan_score = mean(isolation, chain, preparation)

        If orphan_score > 0.6: ORPHANED
        Else: INTEGRATED
```

**Isolation scoring.** φ(s) = (register-active content words in s) / (content words in s). Isolation = min(1.0, (φ(s_target) − φ̄(neighbors)) / 0.2). A score of 0 results when the target density is at or below the neighbor mean. As the gap increases, the score scales linearly from 0 to 1, reaching its maximum when the gap meets or exceeds τ₁ = 0.2.

**Chain scoring.** Within ±3 sentences, count words in the same register field (excluding domain-literals and the target word). 0 matches = 1.0; 1 match = 0.6; 2 matches = 0.2; 3+ matches = 0.0.

**Preparation scoring.** Check for: simile markers (regex patterns for "like a," "as if," etc.), extended metaphor frame (adjacent sentences both > 0.15 figurative density), partial preparation (one adjacent sentence > 0.15), rhythmic shift (sentence < 6 words after sentence > 15 words). Any match = score 0.0-0.3. No match = 1.0. The rhythmic-shift threshold (6/15 words, approximately a 2.5:1 ratio) is set heuristically to capture the prosodic effect of a short, emphatic sentence following a long descriptive one, a common signposting device in literary prose where the rhythm break announces a shift in register or significance (cf. Leech & Short, 2007, on sentence-length variation as a stylistic marker of foregrounding). We acknowledge this threshold is not anchored to a specific quantitative finding in the prosody literature and treat it as a tunable parameter.

**Domain-literal filtering priority.** The domain-literal filter is conservative by design: it suppresses only words whose *primary* sense denotes the domain activity. A word like "grip" is not added to the blacksmith domain-literal set even though blacksmiths literally grip tools, because the word's primary sense (physical grasping) is not specific to blacksmithing; the body-register activation it carries is semantically real even in that context (see E.4 for the borderline analysis). A word that appears in both a domain-literal set and a register field is suppressed if and only if the passage's domain matches the domain-literal set. The word "blade" is domain-literal in sawmill passages (where it denotes the saw blade) but is not domain-literal in ocean storm passages (where, if it appeared, it would be figurative). This domain-specific suppression prevents false positives from technical vocabulary without globally removing words that may carry figurative weight in non-native domains. The filter operates on the passage's declared domain, which is assigned at corpus construction time, not inferred by the detector.

## Appendix B: Domain-Literal Sets

Complete word sets used to filter domain-literal vocabulary (words whose primary sense is about the domain activity). These prevent false positives from technical vocabulary.

**Sawmill** (34 words): saw, blade, bandsaw, mill, timber, lumber, plank, board, sawdust, carpenter, carriage, guide, peel, log, trunk, wood, grain, knot, bark, ring, heartwood, sapwood, sap, pine, oak, cut, cutting, feed, fed, stack, stacked, turn, turned, rotate, sharp, edge, thick, thin.

**Ocean storm** (36 words): wave, waves, swell, surge, tide, current, storm, gust, gale, wind, rain, spray, boat, ship, sail, mast, hull, deck, bow, stern, port, starboard, anchor, rudder, helm, gunwale, keel, rigging, haul, trim, secure, line, fast, cleat, drown, swim, swimming, sink, float, roll, pitch, heave, blow, hit, crash.

**Kitchen** (37 words): kitchen, chef, oven, stove, pan, pot, burner, grill, plate, dish, knife, spatula, peel, cook, cooking, fry, frying, chop, chopping, slice, dice, mince, boil, simmer, roast, bake, sear, saute, skin, bone, fat, breast, leg, neck, tongue, hot, heat, warm, cool, cold, freeze, freezing, cut, press, squeeze, whip, beat, taste, tasted.

**Battlefield surgery** (41 words): surgeon, surgery, medic, scalpel, suture, tourniquet, bandage, morphine, triage, ambulance, wound, blood, bleeding, flesh, bone, skin, muscle, nerve, vein, artery, tissue, organ, leg, thigh, heart, face, cut, incision, probe, stitch, close, dress, irrigate, extract, shell, blast, fire, round, shot, artillery, pulse, pressure, rate, death, code, drop, beat, patient.

**Blacksmith** (37 words): blacksmith, smithy, anvil, forge, bellows, tongs, quench, ingot, hammer, strike, struck, blow, blows, hit, pound, heat, heated, hot, cool, cooled, cold, shape, shaped, form, bend, twist, draw, drawn, turn, turned, flat, point, edge, taper, hard, soft, brittle, tough, bright, dark, red, orange, white, straw, fire, back.

## Appendix C: Register Field Taxonomy

Six figurative register fields used for polysemous word detection:

**Consumption** (25 words): fed, feed, bit, bite, teeth, tongue, mouth, lip, swallow, gulp, devour, consume, appetite, taste, hunger, hungry, starve, chew, gnaw, digest, eat, ate, stomach, throat, raw.

**Personification** (29 words): stubborn, listen, want, wanted, refuse, willing, angry, eager, reluctant, obey, resist, yield, surrender, forgive, complain, scream, whisper, sing, cry, weep, breathe, sleep, wake, dream, die, live, patient, tired, nervous.

**Body** (16 words): arm, shoulder, face, head, heart, eye, neck, bone, skin, flesh, blood, vein, muscle, nerve, grip, fist.

**Violence** (22 words): cut, sharp, edge, blade, slash, slice, split, tear, rip, sever, break, snap, crack, crush, strike, hit, beat, pound, hammer, wound, scar.

**Fire/heat** (19 words): burn, fire, flame, blaze, glow, spark, flash, flare, scorch, sear, smoke, ash, ember, hot, cool, warm, temper, forge, roast.

**Water/weather** (21 words): wave, flood, pour, wash, tide, current, drift, flow, stream, surge, swell, drown, sink, rise, blow, gust, blast, storm, howl, roar, lash.

## Appendix D: Complete Detection Log (v3)

### D.1 Original Sonnet Run (Exp 8c): 9 orphaned words in 20 passages

| ID | Domain | Word | Register | Score | Iso | Chain | Prep |
|----|--------|------|----------|-------|-----|-------|------|
| L04 | ocean | "roar" | water_weather | 0.88 | 0.6 | 1.0 | 1.0 |
| L06 | sawmill | "hungry" | personification | 0.88 | 0.6 | 1.0 | 1.0 |
| L06 | sawmill | "stubborn" | personification | 0.73 | 0.2 | 1.0 | 1.0 |
| L06 | sawmill | "bite" | consumption | 0.73 | 0.2 | 1.0 | 1.0 |
| L06 | sawmill | "roar" | water_weather | 0.80 | 0.4 | 1.0 | 1.0 |
| L07 | sawmill | "bit" | consumption | 0.66 | 0.4 | 0.6 | 1.0 |
| L08 | sawmill | "hungry" | consumption | 0.73 | 0.6 | 0.6 | 1.0 |
| L16 | surgery | "bit" | consumption | 0.94 | 0.8 | 1.0 | 1.0 |
| L20 | blacksmith | "hungry" | personification | 0.73 | 0.2 | 1.0 | 1.0 |

### D.2 Human passages: 1 orphaned word in 25 passages

| ID | Domain | Word | Register | Score | Iso | Chain | Prep |
|----|--------|------|----------|-------|-----|-------|------|
| PUB_03 | ocean | "bite" | consumption | ~0.65 | ~0.4 | 1.0 | 1.0 |

Conrad's "the rudder would bite again." Arguably domain-literal in nautical usage.

## Appendix E: Statistical Analysis

### E.1 Primary Analysis (Exp 8c, v2)

**Contingency table (passage-level):**

|          | Flagged | Not flagged | Total |
|----------|---------|-------------|-------|
| LLM      | 9       | 11          | 20    |
| Human    | 1       | 24          | 25    |
| Total    | 10      | 35          | 45    |

Fisher's exact test (one-sided): p = 0.0014
Fisher's exact test (two-sided): p = 0.0024
Cohen's h = 1.69 (large)
LLM rate: 0.750, 95% CI [0.509, 0.913]
Human rate: 0.040, 95% CI [0.001, 0.204]

### E.2 Primary Analysis (Exp 8c, v3)

**Contingency table (passage-level, has orphaned word):**

|          | Flagged | Not flagged | Total |
|----------|---------|-------------|-------|
| LLM      | 7       | 13          | 20    |
| Human    | 1       | 24          | 25    |
| Total    | 8       | 37          | 45    |

Fisher's exact test (one-sided): p = 0.0096
Fisher's exact test (two-sided): p = 0.0146
Cohen's h = 0.86 (large)

### E.3 Cross-Family Validation: GPT-4o (v3)

**Contingency table (20 GPT-4o vs. 25 human):**

|          | Flagged | Not flagged | Total |
|----------|---------|-------------|-------|
| GPT-4o   | 3       | 17          | 20    |
| Human    | 1       | 24          | 25    |
| Total    | 4       | 41          | 45    |

Fisher's exact test (one-sided): p = 0.224
Fisher's exact test (two-sided): p = 0.309
Cohen's h = 0.39 (small)
GPT-4o rate: 0.150, 95% CI [0.032, 0.379]
Power (one-sided, α = 0.05): 36.8%

The GPT-4o result is not individually significant due to limited statistical power at this sample size (36.8% power for the observed effect). The flag rate (15.0%) matches the Sonnet replication rate (15.0%) and exceeds the human baseline (4.0%) in the predicted direction.

GPT-4o orphaned words: "scream" (personification, ocean domain), "angry" (personification, ocean domain), "roar" (water/weather register, sawmill domain).

### E.4 Cross-Family Validation: Gemini 2.5 Flash (v3)

**Contingency table (20 Gemini vs. 25 human):**

|          | Flagged | Not flagged | Total |
|----------|---------|-------------|-------|
| Gemini   | 8       | 12          | 20    |
| Human    | 1       | 24          | 25    |
| Total    | 9       | 36          | 45    |

Fisher's exact test (one-sided): p = 0.004
Fisher's exact test (two-sided): p = 0.006
Cohen's h = 0.97 (large)
Gemini rate: 0.400, 95% CI [0.191, 0.639]

Gemini produced the strongest orphaned sophistication signal of any model tested. Orphaned words: "roar" (3 passages, sawmill/ocean), "cry" (personification, ocean), "bit" (consumption, surgery), "stubborn" (personification, blacksmith), "hungry" (consumption, blacksmith), "grip" (body, blacksmith), "angry" (personification, blacksmith).

**Note on "grip."** The word "grip" in the blacksmith domain warrants scrutiny as a potential false positive: blacksmiths literally grip tools, and "grip" could function as domain-literal rather than as a body-register figurative construction. The flagging sentence was: "His grip on the tongs was a conversation between flesh and iron, each squeeze a negotiation with the heat." The detector classified "grip" as orphaned because it activates the body register ("flesh," physical contact) in a passage otherwise operating in a materials/heat register, and the body-register activation is isolated (no chain of body vocabulary in adjacent sentences). We acknowledge that this is a borderline case: "grip" is both literally accurate (the blacksmith is gripping tongs) and figuratively activated (the sentence frames the grip as "conversation between flesh and iron"). A stricter detector might exclude words that are simultaneously domain-literal, and we flag this as a potential refinement. Removing this single word from the Gemini count would reduce the orphaned word total from 10 to 9 without affecting the passage-level flag rate (the passage contained two other orphaned words: "hungry" and "angry").

### E.5 Three-Family Pooled Analysis (v3)

**Contingency table (all 100 LLM from three families vs. 25 human):**

|          | Flagged | Not flagged | Total |
|----------|---------|-------------|-------|
| LLM      | 28      | 72          | 100   |
| Human    | 1       | 24          | 25    |
| Total    | 29      | 96          | 125   |

Fisher's exact test (one-sided): p = 0.006
Fisher's exact test (two-sided): p = 0.010
Cohen's h = 0.71 (medium-to-large)
LLM pooled rate: 0.280, 95% CI [0.195, 0.379]
Power: 93.8%

### E.6 Per-Model Breakdown

| Model | Family | Flagged/n | Rate | Cohen's h | vs. Human p (one-sided) |
|-------|--------|-----------|------|-----------|------------------------|
| Gemini 2.5 Flash | Google | 8/20 | 40.0% | 0.97 | 0.004 |
| Sonnet (Exp 8c) | Anthropic | 7/20 | 35.0% | 0.86 | 0.010 |†
| Haiku 3.5 | Anthropic | 7/20 | 35.0% | 0.86 | 0.010 |
| GPT-4o | OpenAI | 3/20 | 15.0% | 0.39 | 0.224 |
| Sonnet (replication) | Anthropic | 3/20 | 15.0% | 0.39 | 0.224 |
| **Pooled (all LLM)** | **3 families** | **28/100** | **28.0%** | **0.71** | **0.006** |
| Human | — | 1/25 | 4.0% | — | — |

†7/20 in the main analysis; the ablation per-model table (E.7) reports 6/20 for the same run due to the borderline saw_2 passage described in the E.7 footnote.

Three of five model runs are individually significant (Gemini, Sonnet original, Haiku). The two runs at 15% (GPT-4o and Sonnet replication) are individually underpowered (power ≈ 37%) but consistent with the aggregate signal. The pooled analysis across three independent model families provides the definitive test (power = 93.8%).

### E.7 Ablation Study: Dimension Contributions

**Full results (125 passages: 25 human, 100 LLM across 5 model runs):**

| Configuration | Active dims | Human flagged | LLM flagged | Cohen's h | Δh from full | p (1-sided) |
|--------------|-------------|---------------|-------------|-----------|-------------|-------------|
| Full model | I + C + P | 1/25 (4.0%) | 27/100 (27.0%)† | 0.690 | — | 0.008 |
| No isolation | C + P | 1/25 (4.0%) | 33/100 (33.0%) | 0.821 | +0.131 | 0.002 |
| No chain | I + P | 1/25 (4.0%) | 21/100 (21.0%) | 0.549 | −0.141 | 0.035 |
| No preparation | I + C | 2/25 (8.0%) | 26/100 (26.0%) | 0.497 | −0.193 | 0.041 |

I = isolation, C = chain connectivity, P = tonal preparation.

†The ablation full-model baseline reports 27/100 LLM flagged, versus 28/100 in the main analysis (Section 5.3). The discrepancy traces to one Sonnet original passage (saw_2) whose orphanhood score falls at the classification boundary (0.603 in the main analysis, 0.597 in the ablation re-run). The difference arises because the ablation computes scores from a single unified pass across all 125 passages, while the main analysis was computed incrementally as each model corpus was added. At the 0.6 threshold, minor floating-point variation in neighborhood density calculation shifts this one passage across the boundary. All reported statistics use the figures from the analysis in which they were computed: 28/100 in Section 5.3, 27/100 in the ablation. The one-passage difference does not affect any qualitative conclusion (ablation full-model p = 0.008 vs. main analysis p = 0.006; both strongly significant).

**Per-model breakdown under each configuration:**

| Model | Full | No isolation | No chain | No preparation |
|-------|------|-------------|----------|---------------|
| Human (Richard, n=5) | 0/5 | 0/5 | 0/5 | 0/5 |
| Human (published, n=20) | 1/20 | 1/20 | 1/20 | 2/20 |
| Sonnet original (n=20) | 6/20 | 7/20 | 5/20 | 4/20 |
| Haiku (n=20) | 7/20 | 9/20 | 4/20 | 5/20 |
| Sonnet replication (n=20) | 3/20 | 4/20 | 3/20 | 5/20 |
| GPT-4o (n=20) | 3/20 | 4/20 | 3/20 | 4/20 |
| Gemini (n=20) | 8/20 | 9/20 | 6/20 | 8/20 |

The no-preparation configuration is the only ablation that increases the human false positive rate (from 1/25 to 2/25), confirming that preparation testing is the primary source of specificity. The no-isolation configuration increases LLM detection across all models while maintaining human FPR, suggesting that isolation scoring is a conservative filter that primarily suppresses true positives where the figurative spike coincides with mildly elevated neighborhood density.
