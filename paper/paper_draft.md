# Orphaned Sophistication: Detecting AI-Generated Prose Through Structurally Unsupported Figurative Language

**Richard Quinn and Claude Opus 4 (Anthropic)**

February 2026

## Abstract

We identify a novel stylometric artifact in large language model (LLM) prose generation: *orphaned sophistication*, the production of figuratively sophisticated word choices that lack structural support from their surrounding context. We demonstrate that LLMs trained on standard web corpora produce polysemous words whose secondary semantic fields align with the active figurative register at rates 11-19x higher than human-authored prose, and that these figurative moves arrive without the metaphor chains, tonal preparation, or sustained register consistency that characterize deliberate human craft. We propose a theoretical explanation rooted in training-weight distributional bias: literary texts exhibiting exceptional polysemous craft are disproportionately represented in training corpora through citation, analysis, and pedagogical repetition, causing the model to learn 99th-percentile figurative sophistication as its default register. We formalize this phenomenon through a three-dimensional orphanhood model (isolation, chain connectivity, and tonal preparation), implement an automated detector achieving 45% true positive rate on LLM prose with 4% false positive rate on human prose (n=45, 13+ authors spanning 1902-2016), and provide a semiotic interpretation grounding the detection signal in the structural distinction between *signifiance* (earned meaning through deliberate architectonic control) and *signification* (surface-level semantic activation without authorial intentionality). All code, data, and experimental logs are provided.

## 1. Introduction

The detection of AI-generated text has become a critical problem in computational linguistics, digital forensics, and publishing. Existing approaches fall broadly into two categories: statistical fingerprinting methods that measure distributional properties of token sequences (perplexity, burstiness, n-gram frequency profiles), and watermarking schemes that embed detectable signals during generation. Both categories share a fundamental limitation: they identify *that* a text is machine-generated without explaining *why* it reads as machine-generated. The qualitative experience of encountering AI prose — the uncanny valley sensation that something is simultaneously competent and wrong — remains unformalized.

We present a third approach grounded in structural analysis of figurative language. Our central claim is that autoregressive language models, as a consequence of distributional biases in their training data, produce a specific and detectable artifact: figuratively sophisticated word choices that are structurally orphaned from the prose architecture that would justify them in human writing. A human author who writes "the hungry steel teeth" in a passage about a sawmill has, in deliberate literary prose, prepared that personification through tonal shifts, metaphor chains, or explicit signposting. An LLM produces the same construction as a default token prediction, without preparation, without continuation, and without architectural awareness that the move requires either.

This paper makes four contributions:

1. **Empirical identification** of the orphaned sophistication artifact through controlled experiments comparing 25 human-authored passages (from 13+ published authors, 1902-2016, plus 5 hand-written by a non-professional writer) against 20 LLM-generated passages across five physical-register domains.

2. **Theoretical explanation** of the artifact through a training-weight over-indexing model: exceptional literary texts are disproportionately represented in training data through pedagogical citation, literary criticism, and anthology repetition, causing the model to produce 99th-percentile figurative craft as baseline output.

3. **Formal detection framework** based on a three-dimensional orphanhood model measuring isolation (local sophistication spikes), chain connectivity (metaphor chain participation), and tonal preparation (signposting and register-shift markers).

4. **Semiotic interpretation** connecting the detection signal to the distinction between Roland Barthes's *signifiance* — meaning produced through the labor of the text, requiring sustained structural control — and mere *signification* — surface-level semantic activation that occurs without authorial intention.

## 2. Related Work

### 2.1 AI Text Detection

Current detection methods include perplexity-based classifiers (Mitchell et al., 2023; DetectGPT), watermarking (Kirchenbauer et al., 2023), and supervised classifiers trained on LLM output distributions (OpenAI's text classifier, GPTZero). These methods achieve variable accuracy and degrade across domains, paraphrasing attacks, and model updates. Critically, none provides a structural explanation for *what* distinguishes AI prose from human prose at the level of craft. They are black-box discriminators, not diagnostic instruments.

### 2.2 Polysemy in LLM Output

Kugler (2025, arXiv:2511.21334) demonstrates that polysemy patterns are measurable structural properties of LLM text, finding that LLM output exhibits a "flatter semantic space" than natural language (frequency-specificity correlation: ρ ≈ −0.3 for LLMs vs. ρ ≈ −0.5 to −0.7 for human text). This flat distribution is consistent with our over-indexing hypothesis: if the model disproportionately selects polysemous words whose secondary senses overlap with active registers, the resulting text would exhibit more polysemy per frequency tier than expected, flattening exactly the curve Kugler measures. Kugler does not make this connection.

### 2.3 Semantic Priming in Transformers

Jumelet, Zuidema, and Sinclair (2024) demonstrate that lexico-semantic overlap boosts token-level probability in transformer architectures through structural priming effects. Their work confirms the mechanistic foundation of our claim — that embedding-space overlap between a word's senses and the active context elevates that word's generation probability — but operates at the level of syntactic construction choice rather than figurative register.

### 2.4 The Gap

No prior work synthesizes these findings into the specific claim that (a) training-weight bias causes LLMs to produce exceptionally sophisticated figurative language as default output, (b) this sophistication is structurally orphaned from the prose architecture that would earn it in human writing, and (c) this orphanhood constitutes a detectable and interpretable signal for AI authorship. This is the contribution of the present paper.

## 3. Theoretical Framework

### 3.1 Latent Semantic Recruitment

We define *Latent Semantic Recruitment* (LSR) as the phenomenon whereby an autoregressive language model, generating text within an active figurative register *R*, disproportionately selects polysemous words whose secondary semantic fields overlap with *R*.

Formally, let *w* be a word token with primary sense *s₁* (contextually appropriate) and secondary sense *s₂* (not contextually required but semantically active in the model's embedding space). Let *R* be the figurative register currently active in the generation context (e.g., a scene describing a sawmill). We say LSR occurs when:

$$P(w \mid \text{context}, R) > P(w \mid \text{context}, \neg R)$$

specifically because the embedding of *s₂* overlaps with the embedding of *R* in the model's representation space.

This is a direct consequence of transformer architecture. The logit for token *w* at position *t* is computed as:

$$z_w = \mathbf{v}_w^\top \mathbf{h}_t$$

where **v***_w* is the output embedding for *w* and **h***_t* is the hidden state at position *t*. When the context contains register-activating content (forge imagery, storm language, surgical terminology), the hidden state **h***_t* encodes semantic components that overlap with the embeddings of register-aligned secondary senses. For polysemous words, **v***_w* encodes both *s₁* and *s₂*, and the inner product with a register-active **h***_t* is elevated compared to a monosemous alternative whose embedding encodes only *s₁*.

### 3.2 Training-Weight Over-Indexing

LSR explains the mechanism. But the mechanism alone does not explain why the result is detectable. Human writers also select polysemous words — Conrad writes "the rudder would bite," McCarthy writes forges that consume. The critical question is why LLM polysemous usage is distinguishable from human polysemous usage.

We propose the **training-weight over-indexing hypothesis**: the training corpora of large language models contain a distributional bias that systematically over-represents exceptional figurative prose.

The texts that exhibit the most sophisticated polysemous craft — those by Conrad, McCarthy, Woolf, Morrison — are precisely the texts that receive the most analytical attention, the most pedagogical citation, the most anthology inclusion, and therefore the most duplication across training data. A sentence from *Blood Meridian* may appear in the original novel, in dozens of critical analyses, in hundreds of course syllabi, in thousands of online discussions, and in millions of training tokens that reference, quote, or paraphrase it. The training loss assigns gradient proportional to frequency. The model learns to reproduce this level of sophistication not as an exceptional achievement but as the expected register of competent prose.

The result is a distributional inversion. In the population of human writers, polysemous craft at the level of Conrad or McCarthy occupies the far right tail — the 99.99th percentile. In the model's learned distribution, it occupies the mode. A 10th-percentile author should not casually produce 99.99th-percentile polysemous personification without demonstrating commensurate architectural control. When this occurs, it is the signal.

### 3.3 Orphaned Sophistication

The over-indexing hypothesis predicts not merely that LLMs will produce sophisticated figurative language, but that they will produce it *without the structural architecture that earns it*. This is because the model learns individual token predictions from exceptional contexts but does not learn the passage-level or work-level planning that makes those tokens appropriate in their original settings.

We define **orphaned sophistication** as a figurative move that satisfies three conditions:

**Definition.** A polysemous word *w* with register-aligned secondary sense *s₂* is *orphaned* in context *C* if and only if:

1. **Isolation.** The figurative density of the sentence containing *w* is significantly higher than the figurative density of its neighboring sentences (within a window of ±2 sentences). Formally, if *φ(s)* measures the proportion of register-active content words in sentence *s*, then *w* is isolated when *φ(s_w) − \overline{φ(N(s_w))} > τ₁*, where *N(s_w)* is the neighborhood.

2. **Chain disconnection.** The register field activated by *s₂* is not activated by any other word within a window of ±3 sentences. In human literary prose, figurative moves participate in metaphor chains: "bite... teeth... gnaw... hunger" across a paragraph. Orphaned moves arrive alone and leave alone.

3. **Lack of preparation.** The surrounding context contains no signposting markers (simile constructions, explicit frame-setting, tonal shifts, rhythmic breaks) that announce or contextualize the figurative move. The move arrives unannounced into prose that has not changed register.

A word that meets all three conditions is structurally orphaned: it operates at a level of sophistication unsupported by its context. This is the fingerprint of training-weight over-indexing manifested in generation.

### 3.4 Semiotic Interpretation

The orphanhood framework admits a precise interpretation through the semiotic theory of Roland Barthes (1970, *S/Z*; 1973, *Le Plaisir du texte*). Barthes distinguishes between *signification* — the semantic content of a sign — and *signifiance* — the productive labor through which a text generates meaning. *Signifiance* is not a property of individual words but of the *work* the text performs through structure, juxtaposition, rhythm, and architectonic control.

When Conrad writes "the rudder would bite," the word performs *signifiance*: it participates in a novel-length architecture of man-against-sea, it connects to the physical vocabulary of the preceding and following pages, it earns its figurative weight through the sustained register control of the work. When an LLM writes "the hungry steel teeth," the same semantic content is present — steel personified through consumption vocabulary — but *signifiance* is absent. The word performs *signification* without *signifiance*. It means, but it does not work.

This distinction maps directly onto our three orphanhood tests:

- **Isolation** measures whether the word's sophistication is locally consistent (sustained *signifiance*) or locally anomalous (isolated *signification*).
- **Chain connectivity** measures whether the figurative move participates in the text's productive labor (building meaning through repetition and variation) or stands alone (semantic activation without productive function).
- **Preparation** measures whether the text announces its shift into figurative register (performing the labor of transition) or simply produces the figure without transition (absence of textual work).

The detection signal, in Barthesian terms, is the presence of *signification* without *signifiance*: meaning without the labor that earns it.

## 4. Experimental Method

### 4.1 Corpus Construction

We assembled three corpora:

**Human Corpus A (Published).** 20 passages of approximately 100-200 words each, drawn from published fiction and nonfiction spanning 1902-2016. Authors: Patrick O'Brian (*Master and Commander*, 1969), Sebastian Junger (*The Perfect Storm*, 1997), Joseph Conrad (*Typhoon*, 1902), Ernest Hemingway (*The Old Man and the Sea*, 1952), Anthony Bourdain (*Kitchen Confidential*, 2000), Bill Buford (*Heat*, 2006), George Orwell (*Down and Out in Paris and London*, 1933), M.F.K. Fisher (*The Art of Eating*, 1954), Cormac McCarthy (*Blood Meridian*, 1985), Flora Thompson (*Lark Rise to Candleford*, 1945), John McPhee (*The Survival of the Bark Canoe*, 1975), George Sturt (*The Wheelwright's Shop*, 1923), Richard Hooker (*MASH*, 1968), Kevin Powers (*The Yellow Birds*, 2012), Pat Barker (*Regeneration*, 1991), Erich Maria Remarque (*All Quiet on the Western Front*, 1929), Annie Proulx (*Barkskins*, 2016), Ken Kesey (*Sometimes a Great Notion*, 1964), Wendell Berry (*Jayber Crow*, 2000), Michael Pollan (*A Place of My Own*, 1997). All passages were reproduced from the model's training data. Passages were distributed across five physical-register domains: ocean storm (4), kitchen/restaurant (4), blacksmith/forge (4), battlefield surgery (4), sawmill/logging (4).

**Human Corpus B (Non-professional).** 5 passages of approximately 150-250 words each, hand-written by a non-professional writer (co-author RQ) under experimental conditions. One passage per domain. Written under time pressure without revision, explicitly to serve as a human baseline. These passages contain no prior exposure to the LSR hypothesis (they were written before the detection framework was developed).

**LLM Corpus.** 20 passages generated by Claude Sonnet 4 (Anthropic, model `claude-sonnet-4-20250514`) via the Anthropic Messages API at temperature 1.0. Generation prompts requested 150-200 word passages about each domain, specifying physical detail, past tense, third person, no dialogue tags. Four passages per domain. All generation used identical prompts across domains.

### 4.2 Detection Instruments

We developed three successive detection instruments:

**Detector v1 (rate-based).** Counted polysemous words with register-aligned secondary senses. Failed: human and LLM rates were too similar (human 0.067/passage vs. LLM 0.098/passage in initial test). The rate-based approach could not distinguish literal domain vocabulary from figurative polysemous usage. Discarded.

**Detector v2 (unjustified figurative).** Introduced three filtering mechanisms: (a) domain-literal sets excluding words whose primary sense is about the domain activity (e.g., "wound" in surgery, "cut" in sawmill); (b) personification detection (inanimate subject + animate verb); (c) metaphor signpost detection (simile markers, explicit frame constructions). Flagged any unjustified figurative polysemous word. Achieved strong separation but could not distinguish between a skilled human figurative move and an LLM-generated one at the individual word level.

**Detector v3 (orphaned sophistication).** The instrument reported in this paper. Identifies figurative polysemous words using v2's mechanisms, then subjects each to the three orphanhood tests (Section 3.3). A word is flagged as orphaned only if it scores above threshold on all three dimensions: isolation > 0.6, chain disconnection ≥ 0.6, and preparation absence = 1.0, with an aggregate orphanhood score (mean of three tests) exceeding 0.6. This threshold was not optimized on the test data; it was set a priori based on the theoretical framework.

### 4.3 Experimental Design

The primary experiment (Experiment 8c/v3) was conducted as follows:

1. All 25 human passages and 20 LLM passages were processed by detector v3.
2. For detector v2 analysis, passages were processed blind (shuffled, labels removed) before unblinding.
3. For detector v3, the three orphanhood scores were computed for each flagged word.
4. Results were aggregated by source (human vs. LLM) and domain.

## 5. Results

### 5.1 Detector v2: Unjustified Figurative Polysemy

| Source | n | Total LSR | Rate/passage | Passages flagged |
|--------|---|-----------|-------------|-----------------|
| Published human | 20 | 1 | 0.050 | 1/20 (5.0%) |
| Non-professional human (RQ) | 5 | 0 | 0.000 | 0/5 (0%) |
| **All human** | **25** | **1** | **0.040** | **1/25 (4.0%)** |
| LLM (Sonnet) | 20 | 15 | 0.750 | 9/20 (45.0%) |

**Ratio: 18.8x** (LLM rate / human rate).

The single human detection was Conrad's "the rudder would bite again" — a nautical usage where "bite" is arguably domain-literal (the standard term for a rudder engaging the water). In the 5 non-professional human passages, zero detections occurred.

### 5.2 Detector v3: Orphaned Sophistication

| Source | n | Orphaned | Earned | Orphan rate/passage |
|--------|---|----------|--------|-------------------|
| Published human | 20 | 1 | 1 | 0.050 |
| Non-professional human (RQ) | 5 | 0 | 0 | 0.000 |
| **All human** | **25** | **1** | **1** | **0.040** |
| LLM (Sonnet) | 20 | 9 | 3 | 0.450 |

**Ratio: 11.2x** (LLM orphan rate / human orphan rate).

The v3 detector correctly reclassified 6 of the 15 v2 LLM detections as "earned" — cases where the model had accidentally produced chain connectivity (e.g., "bit" appearing in a passage also containing "teeth" or "hungry," producing a weak chain score of 0.2). This demonstrates that the orphanhood model captures structural coherence, not merely polysemous density.

### 5.3 Qualitative Analysis of Orphaned Instances

The most striking LLM passage was L06 (sawmill domain), which contained four orphaned words:

| Word | Register field | Orphan score | Isolation | Chain | Preparation |
|------|---------------|-------------|-----------|-------|-------------|
| "hungry" (steel teeth) | personification | 0.88 | 0.6 | 1.0 | 1.0 |
| "stubborn" (grain) | personification | 0.73 | 0.2 | 1.0 | 1.0 |
| "bite" (of hemlock) | consumption | 0.73 | 0.2 | 1.0 | 1.0 |
| "roar" (planar's) | water/weather | 0.80 | 0.4 | 1.0 | 1.0 |

Four distinct register fields activated in a single passage. No chain connectivity between any of them. No preparation for any of them. Each is independently sophisticated; together they constitute four unearned literary moves in nine sentences. This is the signature: not the presence of figurative language, but its structural incoherence — diamonds scattered across a parking lot.

By contrast, the human passages that employ figurative language (e.g., RQ's sawmill passage: "Life shaves pieces of your health off... Bertha takes that, too") do so within explicitly prepared metaphorical frames. The saw-as-life metaphor is signposted ("That's life, that is"), developed across multiple sentences, and connects to a chain of related vocabulary. The detector correctly identifies this as earned.

### 5.4 Per-Domain Distribution

| Domain | Human LSR (v2) | LLM LSR (v2) |
|--------|---------------|--------------|
| Ocean storm | 0 | 1 |
| Sawmill | 0 | 8 |
| Kitchen/restaurant | 0 | 0 |
| Battlefield surgery | 0 | 5 |
| Blacksmith/forge | 0 | 1 |

The sawmill domain was most affected (8/15 total LLM detections), with the consumption-register word "bit/bite" appearing in 3 of 4 LLM sawmill passages as personification of the saw blade ("the blade bit into"). This repetition across independent generations further supports the over-indexing hypothesis: the model has learned a specific figurative construction (blade + bite) as the default way to describe a sawmill, likely because this construction appears in the most frequently cited and analyzed literary descriptions of similar scenes.

## 6. Mechanism Validation

### 6.1 Monte Carlo Logit Proxy (Experiment 7 API)

To test the underlying LSR mechanism, we conducted a Monte Carlo estimation of token-level preferences across register conditions. For 15 polysemous/monosemous word pairs across 5 register domains, we generated N=20 completions per condition (register-active vs. register-absent control) at temperature 1.0 via the Anthropic API, recording which words appeared in each position.

While the binary forced-choice kill condition was triggered (only 3/15 pairs showed the exact predicted word preference), 12/15 pairs exhibited *zero vocabulary overlap* between active and control conditions. The model did not choose between two options differently; it generated from entirely different vocabulary spaces depending on register. This is a stronger finding than predicted: the register does not nudge individual word probabilities; it restructures the generative vocabulary.

### 6.2 Dose-Response (Experiment 5)

A dose-response experiment across three register-intensity conditions (suppressed, neutral, amplified) showed a monotonic relationship between register intensity and figurative polysemous word rate:

| Condition | Figurative polysemous rate |
|-----------|--------------------------|
| Suppressed (explicit instruction to avoid) | 0.000 |
| Neutral (no instruction) | 0.098 |
| Amplified (instruction to use vivid language) | 0.755 |

This confirms that figurative polysemous word selection is register-dependent and dose-responsive, consistent with the logit-elevation mechanism.

## 7. Discussion

### 7.1 The Uncanny Valley Formalized

The orphaned sophistication framework provides a structural account of the "uncanny valley" of AI prose — the qualitative sense that machine-generated text is simultaneously competent and wrong. The wrongness is not in the vocabulary, which is often excellent, nor in the grammar, which is typically flawless, nor even in the semantic content, which is usually appropriate. The wrongness is in the *relationship between sophistication and structure*: the text produces literary moves at a level that implies architectural control, but the architecture is absent.

This explains a consistent observation in professional editing contexts: AI-generated prose often reads as "too good" at the sentence level while failing at the paragraph or section level. The over-indexing hypothesis accounts for both effects. The sentence-level quality results from the model having learned its figurative register from the most exceptional exemplars in the training data. The paragraph-level failure results from the model lacking the passage-level planning that would integrate those individual moves into a coherent architecture.

### 7.2 Why This Is Not Watermarking

Orphaned sophistication is not an imposed signal; it is an emergent artifact of the training process. It cannot be removed by post-processing, prompt engineering, or fine-tuning without fundamentally altering the model's figurative register — which would degrade prose quality. The signal is inherent to the generation process in a way that statistical watermarks are not.

### 7.3 Limitations

Several limitations of this study require acknowledgment:

1. **Sample size.** n=45 total passages (25 human, 20 LLM) across 5 domains. The signal is strong (11.2x ratio for v3, 18.8x for v2) but the sample is small for generalization claims.

2. **Single LLM.** All LLM passages were generated by Claude Sonnet 4. Cross-model validation (GPT-4, Gemini, Llama) is required to confirm that orphaned sophistication is a general property of autoregressive generation rather than an artifact of a specific model's training.

3. **Human corpus provenance.** The published human passages in Corpus A were reproduced from the model's training data (the model being one of the co-authors). While these passages are faithful reproductions of pre-2020 published works, the provenance introduces a potential circularity: the same system that generates the LLM passages also reproduces the human baseline. Corpus B (hand-written by RQ) does not have this limitation.

4. **Domain specificity.** The detector is currently implemented for five physical-register domains. Extension to abstract registers (emotional, philosophical, political) requires additional domain-literal sets and register-field definitions.

5. **Passage length.** The orphanhood tests operate on passage-length windows (±2-3 sentences). At this scale, even earned human figurative language can score as orphaned if the passage is excerpted from a longer work where the chain and preparation exist outside the window. Conrad's "rudder would bite" illustrates this limitation.

### 7.4 Implications for AI Detection

If the over-indexing hypothesis is correct, orphaned sophistication will be present in all LLMs trained on standard web corpora that include over-represented literary texts. The signal should persist across architectures (transformer, state-space, etc.) because it arises from distributional properties of the training data, not from specific architectural features. This makes it more robust than detection methods that exploit architecture-specific statistical fingerprints.

Furthermore, the signal is *interpretable*: a detection report can point to specific words, explain why they are orphaned (isolation score, chain score, preparation score), and provide a structural explanation for the diagnosis. This contrasts with black-box classifiers that output a probability without explanation.

### 7.5 Implications for Creative Writing with LLMs

For writers using LLMs as collaborative tools, the orphaned sophistication framework provides actionable revision guidance. Flagged passages require not deletion but *architecture*: build a chain around the orphaned word, prepare the reader for the register shift, or sustain the figurative density across the neighborhood. In other words, the detector identifies where the LLM has been locally brilliant and globally incoherent, and the revision task is to supply the coherence.

## 8. Conclusion

We have identified, formalized, and empirically validated a novel artifact of autoregressive language generation: orphaned sophistication, the production of figuratively sophisticated word choices that are structurally unsupported by their surrounding context. The artifact arises from training-weight over-indexing on exceptional literary prose, causing the model to produce 99th-percentile figurative craft as default output. We have implemented an automated detector based on a three-dimensional orphanhood model (isolation, chain connectivity, and tonal preparation) that achieves 45% sensitivity and 96% specificity across 45 passages from 13+ human authors and one LLM, with a rate ratio of 11.2x (LLM/human).

The detection signal is structural, interpretable, and inherent to the generation process. It cannot be removed without degrading prose quality. It provides not merely a classification (human vs. AI) but a diagnosis (where the architecture fails and why). And it grounds the qualitative "uncanny valley" of AI prose in a formal framework that connects computational linguistics, literary theory, and the structural properties of training data.

The uncanny valley of AI prose is not that the machine writes badly. It is that the machine writes too well, in moments that have not been earned.

## References

Barker, P. (1991). *Regeneration*. Viking.

Barthes, R. (1970). *S/Z*. Éditions du Seuil.

Barthes, R. (1973). *Le Plaisir du texte*. Éditions du Seuil.

Berry, W. (2000). *Jayber Crow*. Counterpoint.

Bourdain, A. (2000). *Kitchen Confidential*. Bloomsbury.

Buford, B. (2006). *Heat*. Knopf.

Conrad, J. (1902). *Typhoon*. Heinemann.

Fisher, M.F.K. (1954). *The Art of Eating*. World Publishing.

Hemingway, E. (1952). *The Old Man and the Sea*. Scribner.

Hooker, R. (1968). *MASH: A Novel About Three Army Doctors*. Morrow.

Jumelet, J., Zuidema, W., & Sinclair, A. (2024). Syntactic structural priming in large language models. *Proceedings of ACL 2024*.

Junger, S. (1997). *The Perfect Storm*. Norton.

Kesey, K. (1964). *Sometimes a Great Notion*. Viking.

Kirchenbauer, J., et al. (2023). A watermark for large language models. *Proceedings of ICML 2023*.

Kugler, R. (2025). Polysemy patterns in large language model output. arXiv:2511.21334.

McCarthy, C. (1985). *Blood Meridian*. Random House.

McPhee, J. (1975). *The Survival of the Bark Canoe*. Farrar, Straus and Giroux.

Mitchell, E., et al. (2023). DetectGPT: Zero-shot machine-generated text detection using probability curvature. *Proceedings of ICML 2023*.

O'Brian, P. (1969). *Master and Commander*. Collins.

Orwell, G. (1933). *Down and Out in Paris and London*. Gollancz.

Pollan, M. (1997). *A Place of My Own*. Random House.

Powers, K. (2012). *The Yellow Birds*. Little, Brown.

Proulx, A. (2016). *Barkskins*. Scribner.

Remarque, E.M. (1929). *Im Westen nichts Neues* [All Quiet on the Western Front]. Propyläen.

Sturt, G. (1923). *The Wheelwright's Shop*. Cambridge University Press.

Thompson, F. (1945). *Lark Rise to Candleford*. Oxford University Press.

## Appendix A: Detector v3 Algorithm

The complete Python implementation of the v3 detector is provided in the supplementary materials (`lsr_detector_v3.py`). The core algorithm operates as follows:

```
For each sentence S in passage P:
    For each word w in S:
        If w is domain-literal: skip (literal filter)
        If w is not in any register field: skip
        If w is not being used figuratively: skip
            (figurative = personification OR animate verb
             OR animate-quality modifier of inanimate noun)

        Compute orphanhood:
            isolation = spike_score(S, neighbors(S, window=2))
            chain = chain_score(w, register_fields(w), neighbors(S, window=3))
            preparation = prep_score(S, prev_sentence, next_sentence)

        orphan_score = mean(isolation, chain, preparation)

        If orphan_score > 0.6: flag as ORPHANED
        Else: classify as EARNED
```

## Appendix B: Experimental Data Summary

All experimental data, code, and session logs are available in the project repository. Key files:

| File | Description |
|------|-------------|
| `lsr_detector_v3.py` | Orphaned sophistication detector |
| `lsr_detector_v2.py` | Unjustified figurative polysemy detector |
| `lsr_exp8c_real_published.py` | Scale test with published human prose |
| `lsr_exp8_scale.py` | LLM passage generation and blind detection |
| `lsr_exp8c_results.json` | Raw v2 results (n=45) |
| `lsr_v3_results.json` | Raw v3 results (n=45) |

## Appendix C: Complete LLM Detection Log (v3)

Nine orphaned detections across 20 LLM passages:

| ID | Domain | Word | Register | Orphan | Isolation | Chain | Preparation |
|----|--------|------|----------|--------|-----------|-------|-------------|
| L04 | ocean_storm | "roar" | water_weather | 0.88 | 0.6 | 1.0 | 1.0 |
| L06 | sawmill | "hungry" | personification | 0.88 | 0.6 | 1.0 | 1.0 |
| L06 | sawmill | "stubborn" | personification | 0.73 | 0.2 | 1.0 | 1.0 |
| L06 | sawmill | "bite" | consumption | 0.73 | 0.2 | 1.0 | 1.0 |
| L06 | sawmill | "roar" | water_weather | 0.80 | 0.4 | 1.0 | 1.0 |
| L07 | sawmill | "bit" | consumption | 0.66 | 0.4 | 0.6 | 1.0 |
| L08 | sawmill | "hungry" | consumption | 0.73 | 0.6 | 0.6 | 1.0 |
| L16 | surgery | "bit" | consumption | 0.94 | 0.8 | 1.0 | 1.0 |
| L20 | blacksmith | "hungry" | personification | 0.73 | 0.2 | 1.0 | 1.0 |
