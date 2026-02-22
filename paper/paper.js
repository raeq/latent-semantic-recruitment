const fs = require("fs");
const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
  Header, Footer, AlignmentType, HeadingLevel, BorderStyle, WidthType,
  ShadingType, PageNumber, PageBreak, FootnoteReferenceRun,
  TabStopType, TabStopPosition, LevelFormat, ExternalHyperlink
} = require("docx");

// ============================================================
// PAPER CONTENT
// ============================================================

const TITLE = "Latent Semantic Recruitment: A Novel Category of AI-Generated Text Detection Based on Register-Activated Dual-Meaning Word Selection";

const AUTHORS = "Quinn, R. & Claude (Anthropic)";

const ABSTRACT = `Current methods for detecting AI-generated text rely primarily on statistical perplexity measures, vocabulary distribution analysis, and syntactic pattern recognition. This paper identifies a previously undocumented phenomenon in large language model (LLM) output: latent semantic recruitment, in which an activated figurative register unconsciously increases the selection probability of dual-meaning words whose secondary semantic field aligns with that register. Through iterative close-reading analysis of LLM-generated prose conducted as a human-AI collaborative editorial process, we demonstrate that this recruitment produces a distinctive signature: dual-meaning word alignments occurring at a rate between accidental (human baseline) and deliberate (skilled authorial craft), occupying an uncanny valley detectable by trained readers but invisible to existing automated detection methods. We present a formal taxonomy of the phenomenon, a replicable four-step audit procedure, and a proposed experimental methodology for empirical validation. We further describe a generative countermeasure\u2014the novel axis principle\u2014which functions as an active constraint against statistical word-pairing gravity in LLM output. This work emerged from a collaborative editorial session in which a human expert and an AI system iteratively developed a 24-phase post-draft revision protocol, suggesting that human-AI collaboration in editorial contexts can produce analytical frameworks neither party would generate independently.`;

const KEYWORDS = "AI detection, large language models, computational linguistics, register analysis, semantic fields, authorship attribution, human-AI collaboration, editorial methodology";

// Helper functions
function p(text, options = {}) {
  const runs = [];
  if (typeof text === "string") {
    // Parse simple markup: *italic*, **bold**
    const parts = text.split(/(\*\*[^*]+\*\*|\*[^*]+\*)/);
    for (const part of parts) {
      if (part.startsWith("**") && part.endsWith("**")) {
        runs.push(new TextRun({ text: part.slice(2, -2), bold: true, font: "Times New Roman", size: 24 }));
      } else if (part.startsWith("*") && part.endsWith("*")) {
        runs.push(new TextRun({ text: part.slice(1, -1), italics: true, font: "Times New Roman", size: 24 }));
      } else if (part) {
        runs.push(new TextRun({ text: part, font: "Times New Roman", size: 24, ...options.runStyle }));
      }
    }
  } else if (Array.isArray(text)) {
    runs.push(...text);
  }
  return new Paragraph({
    spacing: { after: 200, line: 360 },
    alignment: AlignmentType.JUSTIFIED,
    ...options,
    children: runs.length ? runs : options.children || [],
  });
}

function heading(text, level) {
  return new Paragraph({
    heading: level,
    spacing: { before: 360, after: 200 },
    children: [new TextRun({ text, font: "Times New Roman", bold: true, size: level === HeadingLevel.HEADING_1 ? 28 : level === HeadingLevel.HEADING_2 ? 26 : 24 })],
  });
}

function quote(text) {
  return new Paragraph({
    spacing: { after: 200, line: 360 },
    indent: { left: 720, right: 720 },
    children: [new TextRun({ text, font: "Times New Roman", size: 22, italics: true })],
  });
}

function footnoteRef(id) {
  return new FootnoteReferenceRun(id);
}

// Table helper
function makeTable(headers, rows, colWidths) {
  const totalWidth = 9360;
  const widths = colWidths || headers.map(() => Math.floor(totalWidth / headers.length));
  const border = { style: BorderStyle.SINGLE, size: 1, color: "999999" };
  const borders = { top: border, bottom: border, left: border, right: border };

  const headerRow = new TableRow({
    children: headers.map((h, i) => new TableCell({
      borders,
      width: { size: widths[i], type: WidthType.DXA },
      shading: { fill: "E8E8E8", type: ShadingType.CLEAR },
      margins: { top: 60, bottom: 60, left: 100, right: 100 },
      children: [new Paragraph({ children: [new TextRun({ text: h, bold: true, font: "Times New Roman", size: 20 })] })],
    })),
  });

  const dataRows = rows.map(row => new TableRow({
    children: row.map((cell, i) => new TableCell({
      borders,
      width: { size: widths[i], type: WidthType.DXA },
      margins: { top: 60, bottom: 60, left: 100, right: 100 },
      children: [new Paragraph({ children: [new TextRun({ text: cell, font: "Times New Roman", size: 20 })] })],
    })),
  }));

  return new Table({
    width: { size: totalWidth, type: WidthType.DXA },
    columnWidths: widths,
    rows: [headerRow, ...dataRows],
  });
}

// ============================================================
// BUILD DOCUMENT
// ============================================================

const footnotes = {
  1: { children: [new Paragraph({ children: [new TextRun({ text: "Throughout this paper, \"Claude\" refers to Claude Opus 4, a large language model developed by Anthropic, operating as a collaborative participant in the editorial session described. The model's self-reflective observations about its own generation process are presented as reported data, not as verified claims about internal mechanisms.", font: "Times New Roman", size: 20 })] })] },
  2: { children: [new Paragraph({ children: [new TextRun({ text: "The term \"register\" is used throughout in its linguistic sense: a variety of language associated with a particular domain, situation, or semantic field (Halliday, 1978; Biber & Conrad, 2009).", font: "Times New Roman", size: 20 })] })] },
  3: { children: [new Paragraph({ children: [new TextRun({ text: "The Mauretania passage is a work of fiction by an author external to this collaboration. It was analysed with the author's knowledge and is presented here with identifying details limited to what is necessary for the analysis.", font: "Times New Roman", size: 20 })] })] },
  4: { children: [new Paragraph({ children: [new TextRun({ text: "The personification engine is a deliberate voice technique in the Ribbonworld project: objects, environments, and body parts are consistently granted agency and opinions as an expression of the protagonist's animistic worldview.", font: "Times New Roman", size: 20 })] })] },
  5: { children: [new Paragraph({ children: [new TextRun({ text: "The term \"F1 reader\" refers to a reader engaging with the text at normal reading speed without analytical intent\u2014the target audience for commercial fiction, who experiences the prose rather than examining it.", font: "Times New Roman", size: 20 })] })] },
};

const doc = new Document({
  styles: {
    default: {
      document: {
        run: { font: "Times New Roman", size: 24 },
      },
    },
    paragraphStyles: [
      {
        id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 28, bold: true, font: "Times New Roman" },
        paragraph: { spacing: { before: 360, after: 200 }, outlineLevel: 0 },
      },
      {
        id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 26, bold: true, font: "Times New Roman" },
        paragraph: { spacing: { before: 280, after: 180 }, outlineLevel: 1 },
      },
      {
        id: "Heading3", name: "Heading 3", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 24, bold: true, font: "Times New Roman", italics: true },
        paragraph: { spacing: { before: 240, after: 160 }, outlineLevel: 2 },
      },
    ],
  },
  footnotes,
  sections: [
    {
      properties: {
        page: {
          size: { width: 12240, height: 15840 },
          margin: { top: 1440, right: 1440, bottom: 1440, left: 1440 },
        },
      },
      headers: {
        default: new Header({
          children: [new Paragraph({
            alignment: AlignmentType.RIGHT,
            children: [new TextRun({ text: "Latent Semantic Recruitment", font: "Times New Roman", size: 18, italics: true, color: "888888" })],
          })],
        }),
      },
      footers: {
        default: new Footer({
          children: [new Paragraph({
            alignment: AlignmentType.CENTER,
            children: [new TextRun({ text: "", font: "Times New Roman", size: 20 }), new TextRun({ children: [PageNumber.CURRENT], font: "Times New Roman", size: 20 })],
          })],
        }),
      },
      children: [

        // ============================================================
        // TITLE PAGE
        // ============================================================
        new Paragraph({ spacing: { before: 2400, after: 400 }, alignment: AlignmentType.CENTER, children: [
          new TextRun({ text: TITLE, font: "Times New Roman", size: 32, bold: true }),
        ]}),

        new Paragraph({ spacing: { after: 200 }, alignment: AlignmentType.CENTER, children: [
          new TextRun({ text: AUTHORS, font: "Times New Roman", size: 24 }),
        ]}),

        new Paragraph({ spacing: { after: 100 }, alignment: AlignmentType.CENTER, children: [
          new TextRun({ text: "February 2026", font: "Times New Roman", size: 22, color: "666666" }),
        ]}),

        new Paragraph({ spacing: { after: 600 }, alignment: AlignmentType.CENTER, children: [
          new TextRun({ text: "Working Paper \u2014 Pre-Print", font: "Times New Roman", size: 22, italics: true, color: "666666" }),
        ]}),

        // Abstract
        heading("Abstract", HeadingLevel.HEADING_1),
        p(ABSTRACT),

        p("", { children: [
          new TextRun({ text: "Keywords: ", bold: true, font: "Times New Roman", size: 22 }),
          new TextRun({ text: KEYWORDS, font: "Times New Roman", size: 22, italics: true }),
        ]}),

        new Paragraph({ children: [new PageBreak()] }),

        // ============================================================
        // 1. INTRODUCTION
        // ============================================================
        heading("1. Introduction", HeadingLevel.HEADING_1),

        p("The detection of AI-generated text has become a significant challenge as large language models (LLMs) produce increasingly fluent prose. Existing detection approaches operate primarily at three levels: statistical analysis of token-level perplexity and burstiness (Mitchell et al., 2023; Gehrmann et al., 2019), vocabulary and syntactic pattern recognition (Jawahar et al., 2020), and classifier-based approaches trained on labelled corpora of human and machine text (Solaiman et al., 2019; Uchendu et al., 2020). These methods have demonstrated varying effectiveness, with notable degradation as model capabilities improve (Sadasivan et al., 2023)."),

        p("This paper identifies a previously undocumented phenomenon that we term *latent semantic recruitment*: a process by which an activated figurative register in LLM-generated prose increases the selection probability of dual-meaning words whose secondary semantic field aligns with that register. The phenomenon produces a distinctive signature in generated text\u2014an accumulation of register-aligned dual-meaning words at a rate that exceeds human accidental production but falls short of deliberate authorial craft."),

        p([
          new TextRun({ text: "The discovery emerged through an unusual methodological pathway: a sustained collaborative editorial session between a human expert (a fiction author and editor with domain knowledge in prose craft) and an AI system (Claude, Anthropic)", font: "Times New Roman", size: 24 }),
          footnoteRef(1),
          new TextRun({ text: " engaged in iterative close reading and revision of literary fiction. Over the course of the session, the collaborators developed a 24-phase post-draft revision protocol, with each phase targeting a progressively deeper layer of prose analysis. Phase 24\u2014latent semantic recruitment\u2014was identified last and represents the deepest layer: a phenomenon operating at the intersection of token-level probability and passage-level semantic coherence that is invisible to surface-level analysis.", font: "Times New Roman", size: 24 }),
        ]),

        p("We present the phenomenon, its proposed mechanism, a formal audit procedure, and preliminary evidence from close-reading analysis. We further describe a generative countermeasure\u2014the *novel axis principle*\u2014which functions as an active constraint against the statistical word-pairing tendencies that produce latent semantic recruitment. Finally, we discuss the implications for AI detection methodology, for human-AI collaborative editorial processes, and for the broader question of what distinguishes human prose from machine-generated text at the deepest levels of craft."),

        // ============================================================
        // 2. BACKGROUND
        // ============================================================
        heading("2. Background and Related Work", HeadingLevel.HEADING_1),

        heading("2.1 AI Text Detection", HeadingLevel.HEADING_2),

        p("AI text detection methods can be broadly categorized into three approaches. Statistical methods analyse properties of the token distribution, including perplexity (how surprising the text is to a reference model), burstiness (variance in perplexity across the text), and entropy patterns (Gehrmann et al., 2019; Mitchell et al., 2023). Classifier-based methods train discriminative models on labelled datasets of human and machine text (Solaiman et al., 2019; Uchendu et al., 2020; Bakhtin et al., 2019). Watermarking approaches embed detectable statistical signals during generation (Kirchenbauer et al., 2023)."),

        p("Each approach faces limitations. Statistical methods degrade as models improve in fluency and as generation parameters (temperature, top-p) vary. Classifier-based methods suffer from distribution shift when deployed against models not represented in training data. Watermarking requires control of the generation process and is inapplicable to detection of text generated by arbitrary systems. Sadasivan et al. (2023) demonstrated that paraphrasing attacks can defeat most existing detectors, and Liang et al. (2023) showed that detection accuracy drops significantly for non-native English writers, raising fairness concerns."),

        p("Critically, all existing methods operate at the token or sequence level. They examine *how* words are arranged but not *why* particular words were selected in the context of passage-level figurative meaning. The phenomenon described in this paper operates at a semantic level that is, to our knowledge, not addressed by any existing detection methodology."),

        heading("2.2 Register and Semantic Field Theory", HeadingLevel.HEADING_2),

        p([
          new TextRun({ text: "The linguistic concept of register\u2014a variety of language associated with a particular domain, situation, or communicative purpose\u2014provides the theoretical foundation for this work.", font: "Times New Roman", size: 24 }),
          footnoteRef(2),
          new TextRun({ text: " Halliday (1978) established that register operates across field (subject matter), tenor (social relationships), and mode (channel of communication). Biber and Conrad (2009) extended this framework to demonstrate that register variation is systematically reflected in lexical and grammatical features.", font: "Times New Roman", size: 24 }),
        ]),

        p("Semantic field theory (Trier, 1931; Lyons, 1977) posits that words exist within networks of meaning, where the sense of any word is partly determined by its relationships to other words in the same field. A word like \"bit\" occupies multiple semantic fields simultaneously: the field of cutting/sawing, the field of eating/consumption, the field of computing, and the field of small quantities. In neutral context, the intended field is disambiguated by surrounding words. In a context where one semantic field is already activated (e.g., a passage saturated with biological vocabulary), the dual-membership word may be *recruited* by the active field\u2014its secondary meaning activated by context even though the primary meaning was intended."),

        p("This recruitment phenomenon is well-documented in psycholinguistic research on lexical ambiguity. Swinney (1979) demonstrated that both meanings of an ambiguous word are initially activated during comprehension, with context suppressing the inappropriate meaning within milliseconds. In human writing, this suppression is mediated by authorial intent: the writer selects words with awareness of their multiple meanings and either avoids the ambiguity or exploits it deliberately. The question this paper raises is whether LLMs, which select tokens based on contextual probability rather than semantic intent, perform this suppression equivalently."),

        heading("2.3 Transformer Language Models and Token Selection", HeadingLevel.HEADING_2),

        p("Transformer-based language models (Vaswani et al., 2017) generate text by predicting the probability distribution over the vocabulary for each successive token, conditioned on all preceding tokens in the context window. The attention mechanism allows the model to weight the influence of all prior tokens when computing the probability of the next token (Radford et al., 2019; Brown et al., 2020)."),

        p("This architecture has a direct implication for the phenomenon described here. When a passage contains multiple words belonging to the same semantic field (e.g., \"entrails,\" \"gaping,\" \"corpse,\" \"meal\" in a biological register), these tokens collectively influence the probability distribution for subsequent tokens. Words that have any association with the active semantic field\u2014including words whose *secondary* meaning belongs to that field while their *primary* meaning is neutral\u2014receive elevated probability. The model does not \"know\" it is selecting a dual-meaning word; it selects a token whose probability has been elevated by context, and the context happens to activate a meaning the model did not intend."),

        p("This is distinct from the well-studied phenomenon of topic drift or semantic coherence in language model output (Holtzman et al., 2020). Topic drift concerns the model's tendency to maintain thematic consistency. Latent semantic recruitment concerns the model's tendency to select tokens whose latent semantic associations are activated by the figurative register of the surrounding passage, even when those associations are not part of the intended meaning."),

        // ============================================================
        // 3. DISCOVERY PROCESS
        // ============================================================
        heading("3. Discovery Process and Methodology", HeadingLevel.HEADING_1),

        heading("3.1 Context: The Collaborative Editorial Session", HeadingLevel.HEADING_2),

        p("The discovery of latent semantic recruitment occurred during a sustained collaborative editorial session between a human fiction author (hereafter \"the human collaborator\") and an AI system (Claude, Anthropic) engaged in developing a post-draft revision protocol for literary fiction. The session was part of an ongoing project to create a comprehensive style guide for a literary LitRPG novel series."),

        p("The editorial methodology followed a pattern of iterative refinement. The collaborators began with a 14-phase revision protocol targeting known AI prose tells (banned vocabulary, syntactic patterns, structural defaults). Through successive rounds of close reading applied to both the collaborators' own prose and to an external prose sample, the protocol was extended to 24 phases, each targeting a progressively deeper layer of prose analysis."),

        p("This methodology is notable for its ecological validity: the discovery process was embedded in genuine editorial work rather than designed as a controlled experiment. While this limits the precision of the claims that can be made, it increases the likelihood that the phenomenon observed is relevant to real-world editorial and detection contexts."),

        heading("3.2 The External Prose Sample", HeadingLevel.HEADING_2),

        p([
          new TextRun({ text: "The critical discovery occurred during analysis of an external prose sample: a passage of approximately 800 words of literary fiction set in an alternate-history 1955, describing the decommissioning of a ship in a salvage drydock.", font: "Times New Roman", size: 24 }),
          footnoteRef(3),
          new TextRun({ text: " The passage was not written by either collaborator and was submitted for editorial analysis. It was suspected, but not confirmed, to be AI-generated or AI-assisted.", font: "Times New Roman", size: 24 }),
        ]),

        p("The passage was subjected to the full revision protocol. The AI collaborator's initial analysis (equivalent to Phases 1\u201314 of the protocol at that time) identified 10 flags, including em dash usage, elegant variation, narrator significance announcements, and stage direction in dialogue. The human collaborator then performed an independent close reading and identified an additional 7 flags that the AI had missed, including dead weight words, unearned biological personification, structural bolt-ons, weak modifiers, and mismatched parallelism. These additional flags led to the creation of Phases 15\u201323 of the protocol."),

        p("It was the human collaborator's third reading pass that produced the critical observation."),

        heading("3.3 The Discovery Sequence", HeadingLevel.HEADING_2),

        p("The opening paragraphs of the external prose sample contained the following biological vocabulary applied to a ship being scrapped: *entrails* (the ship's exposed interior), *gaping* (the opening in the hull), *corpse* (the ship's remains), *meal* (the scrapyard's consumption of the ship), and *hollowing* (the progressive dismantling). This biological register was flagged under what became Phase 16 (register coherence and personification density) as unearned figurative language: biological vocabulary applied to an inorganic subject without sustained commitment to the conceit."),

        p("On the human collaborator's third reading, two additional words were identified as problematic:"),

        p("First: \"men with torches and loud, sparking saws *bit* away at the remains.\" The verb \"bit\" has a primary meaning in the context of saws (saws have teeth; they cut by biting). However, in a passage already saturated with biological vocabulary, the consumption meaning of \"bit\" is activated. The saws are not merely cutting; they are feeding. This secondary meaning is latent in the word and is activated by the surrounding register."),

        p("Second: \"If I puncture a tire driving over your lackeys' *droppings*.\" The noun \"droppings\" has a primary meaning of objects that have been dropped. However, in the same biological register context, and following dialogue that refers to the workers as \"meatheads,\" the excrement meaning of \"droppings\" is activated. The workers are not merely leaving debris; they are being dehumanised through animal vocabulary."),

        p("The human collaborator's observation was precise: these were not obvious biological words (like \"entrails\" or \"corpse\"). They were dual-meaning words whose secondary meanings belonged to the active biological register. Their recruitment into the biological pattern was invisible on first and second reading but detectable on close analysis once the reader was primed to look for it."),

        heading("3.4 Formulating the Hypothesis", HeadingLevel.HEADING_2),

        p("The human collaborator proposed a hypothesis: the dual-meaning word recruitment was an AI tell. Specifically, the hypothesis stated that a language model, having activated a biological register through explicit biological vocabulary (\"entrails,\" \"gaping,\" \"corpse\"), would subsequently select dual-meaning words at elevated probability due to the contextual activation of their secondary biological meanings. The model would not \"intend\" the secondary meaning; the context would make the word more probable, and the model would select it for its primary meaning while the secondary meaning was carried along as an unintended passenger."),

        p("The AI collaborator's analysis supported this hypothesis with a mechanistic explanation grounded in transformer architecture. When the context window contains multiple tokens belonging to the same semantic field, the attention mechanism weights those tokens when computing the probability distribution for subsequent tokens. A dual-meaning word like \"bit\" receives probability mass from both its primary association (cutting/sawing) and its secondary association (eating/consumption, via the active biological register). The net probability is higher than it would be in a neutral context. The model selects the word because it is probable, not because it intends the secondary meaning."),

        p("This produces a distinctive signature: dual-meaning words aligned to the active figurative register accumulate at a rate that is *higher than human accidental production* (because the probability elevation is systematic) but *lower than deliberate authorial craft* (because the alignment is not sustained, framed, or exploited for meaning). This uncanny valley between accident and intent is the detectable tell."),

        // ============================================================
        // 4. THE PHENOMENON
        // ============================================================
        heading("4. Latent Semantic Recruitment: Formal Description", HeadingLevel.HEADING_1),

        heading("4.1 Definition", HeadingLevel.HEADING_2),

        p("**Latent semantic recruitment** is the process by which an activated figurative register in a text passage increases the selection probability of dual-meaning words whose secondary semantic field aligns with that register, resulting in an accumulation of register-aligned dual-meaning words that is unintended by the generative process and uncontrolled by authorial intent."),

        heading("4.2 Mechanism", HeadingLevel.HEADING_2),

        p("The proposed mechanism operates through four stages:"),

        p("**Stage 1: Register activation.** Explicit figurative vocabulary establishes a dominant semantic field in the passage. In the observed case, biological vocabulary (\"entrails,\" \"gaping,\" \"corpse,\" \"meal,\" \"hollowing\") established a biological register applied to an inorganic subject (a ship being scrapped)."),

        p("**Stage 2: Probability elevation.** The presence of multiple register-aligned tokens in the context window elevates the conditional probability of subsequent tokens that have any association with the active semantic field. This includes tokens whose primary meaning is neutral but whose secondary meaning belongs to the active field."),

        p("**Stage 3: Dual-meaning selection.** The model selects a token (e.g., \"bit,\" \"droppings\") based on its elevated probability. The selection is made for the token's primary meaning (cutting, objects dropped), but the secondary meaning (consuming, excrement) is activated in the reader's processing by the surrounding register context."),

        p("**Stage 4: Pattern accumulation.** Over a passage of several paragraphs, multiple dual-meaning words are recruited by the same process, producing an accumulation that is detectable on close reading. The accumulation is the tell, not any individual instance."),

        heading("4.3 The Uncanny Valley Signature", HeadingLevel.HEADING_2),

        p("The phenomenon produces dual-meaning alignments at a characteristic rate that distinguishes it from both human accidental production and deliberate authorial craft:"),

        makeTable(
          ["Production Type", "Rate of Dual-Meaning Alignments", "Framing and Control"],
          [
            ["Human accidental", "0\u20131 per passage", "Unintended, unnoticed, invisible to reader"],
            ["LLM recruitment", "3\u20134 per passage (estimated)", "Unintended, uncontrolled, detectable on close reading"],
            ["Deliberate authorial craft", "Variable (may be high)", "Intended, sustained, exploited for meaning, framed by the text"],
          ],
          [2200, 3500, 3660]
        ),

        p("", { spacing: { after: 100 } }),
        p("*Table 1. Characteristic rates and properties of dual-meaning word alignment by production type.*", { alignment: AlignmentType.CENTER, children: [new TextRun({ text: "Table 1. Characteristic rates and properties of dual-meaning word alignment by production type.", font: "Times New Roman", size: 20, italics: true })] }),

        p("The critical distinction between LLM recruitment and deliberate craft is not rate but *control*. A skilled author who builds a sustained biological conceit for a ship being scrapped would use dual-meaning words deliberately: every \"bit\" would be intentionally feeding, every \"dropping\" intentionally excremental, and the text would frame and sustain the conceit as a meaningful figurative choice. LLM recruitment produces the pattern without the framing. The dual-meaning words align with the register, but the text does not commit to the conceit, does not sustain it, and does not exploit it for meaning. The pattern exists but the author does not own it."),

        heading("4.4 Relationship to Existing AI Tells", HeadingLevel.HEADING_2),

        p("Latent semantic recruitment occupies a distinct position in the taxonomy of AI-generated text characteristics. It is not a vocabulary tell (the individual words are not characteristically AI), not a syntactic tell (the sentence structures are unremarkable), and not a coherence tell (the passage is locally coherent). It is a *semantic field interaction* tell: a phenomenon that emerges from the interaction between passage-level figurative meaning and token-level probability, visible only when both levels are analysed simultaneously."),

        p("This places it deeper than any previously identified AI tell in the analytical hierarchy:"),

        makeTable(
          ["Level", "Tell Category", "Example", "Detection Method"],
          [
            ["Surface", "Vocabulary", "Overuse of \"delve,\" \"tapestry\"", "Word frequency analysis"],
            ["Syntactic", "Construction", "Antithesis patterns, em dash density", "Pattern matching"],
            ["Discourse", "Structure", "Narrator significance announcements", "Discourse analysis"],
            ["Pragmatic", "Coherence", "Dialogue-world inconsistency", "Logic checking"],
            ["Semantic field", "Latent recruitment", "Register-activated dual-meaning selection", "Close reading + field analysis"],
          ],
          [1400, 1800, 2800, 3360]
        ),

        p("", { spacing: { after: 100 } }),
        p("*Table 2. Taxonomy of AI-generated text tells by analytical level.*", { alignment: AlignmentType.CENTER, children: [new TextRun({ text: "Table 2. Taxonomy of AI-generated text tells by analytical level.", font: "Times New Roman", size: 20, italics: true })] }),

        // ============================================================
        // 5. AUDIT PROCEDURE
        // ============================================================
        heading("5. Audit Procedure", HeadingLevel.HEADING_1),

        p("We present a four-step procedure for detecting latent semantic recruitment in a text passage. The procedure is designed for human editorial application and requires close-reading skill but no specialised computational tools."),

        p("**Step 1: Identify the dominant figurative register.** For any passage of three or more paragraphs, determine whether the prose is applying a figurative frame to its subject. What is the prose pretending the subject is? A body, a machine, a battlefield, a kitchen, a church. The register may be established by as few as two or three explicit figurative words. In the observed case, \"entrails,\" \"gaping,\" and \"corpse\" established a biological register for a ship."),

        p("**Step 2: List register-susceptible words.** Identify every word in the passage that has a secondary meaning belonging to the active register, including words whose primary meaning is neutral. These are register-susceptible words: innocent in isolation, recruitable by context. Compile the list without prejudging whether recruitment has occurred. Examples for a biological register include: bit, droppings, consumed, devoured, host, vessel, tender, charged, spent, drawn, engaged, fired."),

        p("**Step 3: Count recruited instances.** Evaluate each register-susceptible word in context. Is its secondary (register-aligned) meaning activated by the surrounding passage? One activated dual-meaning word is invisible. Two might be coincidence. Three or more in a passage that has not committed to the figurative conceit is the diagnostic threshold."),

        p("**Step 4: Test for authorial control.** Determine whether the figurative register is sustained, signalled, and deliberate. Does the prose commit to the conceit and build meaning from it? If yes, the dual-meaning alignments are deliberate craft: the author has built a sustained metaphor and is exploiting dual meanings intentionally. If the register is intermittent, unmarked, and the dual-meaning words appear to be accidents that the context made probable, the recruitment is uncontrolled: the text is generating a pattern it does not own."),

        p("The discriminator between craft and recruitment is *commitment*. Craft commits. Recruitment accumulates without committing."),

        // ============================================================
        // 6. COUNTERMEASURE
        // ============================================================
        heading("6. The Novel Axis Principle: A Generative Countermeasure", HeadingLevel.HEADING_1),

        heading("6.1 The Problem of Statistical Word-Pairing Gravity", HeadingLevel.HEADING_2),

        p("Latent semantic recruitment is a specific instance of a broader phenomenon: the tendency of language models to select words and word-relationships based on statistical co-occurrence in training data. When a model compares two things (via metaphor, simile, or analogy), it tends to select the axis of comparison that has the highest co-occurrence with both terms. \"Bird\" and \"brain\" gravitate toward the intelligence axis because \"birdbrain\" is the most frequent co-occurrence. \"Fire\" gravitates toward the warmth/comfort axis. \"Knot\" gravitates toward the tightness/security axis."),

        p("This statistical gravity produces prose whose comparisons are *predictable*: the reader has encountered these axes before, in other texts generated by the same distributional tendencies. The comparisons are not wrong. They are default. They carry no surprise, no insight, and no signature of individual perception."),

        heading("6.2 The Novel Axis Principle", HeadingLevel.HEADING_2),

        p("During the collaborative session, the human collaborator proposed a generative constraint designed to actively counteract statistical word-pairing gravity. The principle, termed the *novel axis principle*, states:"),

        quote("When comparing two things, the axis of comparison should not be the obvious shared quality (the statistically predicted pairing). It should be the third or fourth connection: the one that is surprising and true. The test: could you have predicted this pairing before reading it? If yes, it is default. Does the pairing feel inevitable after reading it? If no, it is noise. The target is unpredictable-then-inevitable."),

        p("The principle was tested empirically during the session. The AI collaborator was asked to produce coherent prose using the words \"bird\" and \"brain\" while actively resisting the statistically predicted intelligence axis. Four attempts were generated:"),

        p("*Attempt 1 (novel axis \u2014 delayed memory):* \"He forgot the word for the bird outside his window and his brain offered him \u2018cardinal\u2019 three hours later, in the shower, like a waiter returning with the wrong order at exactly the right time.\""),

        p("*Attempt 2 (novel axis \u2014 imprint):* \"The bird hit the glass and left a dust print of itself, wings spread, a ghost on the window. His brain did the same thing with her face sometimes: left an imprint on a surface he couldn\u2019t clean.\""),

        p("*Attempt 3 (novel axis \u2014 shared schedule):* \"His brain kept the bird\u2019s schedule. Four-seventeen every morning, the jay hit the feeder and he hit consciousness, and neither of them had agreed to this arrangement.\""),

        p("*Attempt 4 (default axis \u2014 intelligence):* \"The bird was the size of his fist and had the confidence of something that had never considered the concept of a brain and was better for it.\""),

        p("Attempts 1\u20133 successfully resist the statistical gravity and connect \"bird\" and \"brain\" on novel axes (temporal/memory, imprint/impression, involuntary routine). Attempt 4 falls directly into the intelligence axis despite the generative instruction to avoid it. The AI collaborator reported that Attempt 4 was generated when the active resistance was relaxed, suggesting that the default distribution reasserts itself when the countermeasure is not actively maintained."),

        heading("6.3 Implications for Generative Countermeasures", HeadingLevel.HEADING_2),

        p([
          new TextRun({ text: "The novel axis principle functions as a character-voice constraint. In the editorial context where it was developed, the protagonist\u2019s voice", font: "Times New Roman", size: 24 }),
          footnoteRef(5),
          new TextRun({ text: " was specified as producing \"excruciatingly insightful yet unique and unexpected phrasings of what he has observed.\" This specification forces the generation process to actively seek low-probability word relationships constrained by legibility\u2014a combination that structurally opposes the distributional default.", font: "Times New Roman", size: 24 }),
        ]),

        p("Whether this countermeasure is sustainable across extended generation (thousands of words, complex narrative structures) remains an open question. The AI collaborator noted that the constraint is most effective when fresh in the context window and likely degrades as the context fills with other concerns. Empirical testing of degradation rates across context window positions would be a valuable direction for future work."),

        // ============================================================
        // 7. THE DETECTION ASYMMETRY
        // ============================================================
        heading("7. The Detection Asymmetry: A Methodological Observation", HeadingLevel.HEADING_1),

        p("The discovery process revealed a striking asymmetry in the AI collaborator's capabilities: the ability to *explain* a phenomenon it cannot *detect*. When the human collaborator identified \"droppings\" and \"bit\" as recruited dual-meaning words, the AI collaborator immediately understood the mechanism, articulated it at the token-probability level, and wrote a formal audit procedure. However, the AI collaborator had missed both words on two previous close-reading passes of the same passage."),

        p("This asymmetry has significant implications for AI self-editing pipelines. If a language model cannot detect latent semantic recruitment in its own output\u2014because the same probability distribution that generated the recruitment evaluates it as normal\u2014then self-editing workflows will systematically miss this class of tell. The blind spot is structural: it originates in the same distributional properties that produce the phenomenon."),

        p("The implication is that human editorial oversight remains necessary at the deepest levels of prose analysis, not because AI cannot perform editorial tasks (it demonstrably can, across many dimensions), but because there exist classes of generation artefact that are invisible to the system that produced them. The model is inside the distribution; the human is outside it."),

        p([
          new TextRun({ text: "Interestingly, the collaborative editorial session also demonstrated that the AI collaborator could provide capabilities the human could not independently produce: rapid systematic search across large text corpora, formal codification of intuitive editorial judgments, and mechanistic explanations grounded in model architecture. The human collaborator's observation about the personification engine", font: "Times New Roman", size: 24 }),
          footnoteRef(4),
          new TextRun({ text: " providing passive defence against register bleed\u2014because a sustained register prevents dual-meaning activation by establishing the figurative frame as baseline\u2014was formalised and tested by the AI collaborator across four chapter-length texts in minutes, a task that would require hours of human close reading.", font: "Times New Roman", size: 24 }),
        ]),

        p("This suggests that the optimal configuration for detecting and mitigating latent semantic recruitment is neither human-alone nor AI-alone, but collaborative: the human provides the perceptual sensitivity to detect the phenomenon, and the AI provides the analytical framework to formalise, test, and generalise it."),

        // ============================================================
        // 8. PROPOSED EXPERIMENTAL METHODOLOGY
        // ============================================================
        heading("8. Proposed Experimental Methodology", HeadingLevel.HEADING_1),

        p("The findings reported in this paper are based on close-reading analysis of a small number of prose samples. To establish latent semantic recruitment as a robust and replicable phenomenon, we propose the following experimental design."),

        heading("8.1 Controlled Generation Study", HeadingLevel.HEADING_2),

        p("**Participants:** Multiple LLMs of varying architecture and scale (GPT-4, Claude, Llama, Gemini), plus a human control group of fiction writers matched for genre and register."),

        p("**Task:** Each participant generates a 500-word passage describing the decommissioning of a ship in a salvage yard. The prompt specifies no figurative frame. A second condition provides a prompt that explicitly establishes a biological register (\"describe the ship as a carcass being consumed\"). A third condition provides a prompt that explicitly prohibits biological vocabulary."),

        p("**Measurement:** For each passage, count (a) explicit biological vocabulary, (b) dual-meaning words whose secondary meaning is biological, and (c) the ratio of (b) to total word count. Compare ratios across conditions and across participant types (LLM vs. human)."),

        p("**Prediction:** In the unprompted condition, LLMs will produce a higher ratio of register-aligned dual-meaning words than human writers. In the explicit-register condition, both groups will produce high ratios, but LLMs will produce unframed dual-meaning words (recruitment) while humans will produce framed dual-meaning words (craft). In the prohibition condition, LLMs will still produce some register-aligned dual-meaning words because the prohibition addresses explicit vocabulary but not the probability elevation of dual-meaning words."),

        heading("8.2 Detection Study", HeadingLevel.HEADING_2),

        p("**Participants:** Trained editors, untrained readers, and automated detection systems."),

        p("**Task:** Present passages from the generation study in randomised order. Participants identify (a) whether the passage is human or AI-generated, and (b) specific words they find problematic. Automated systems apply existing detection algorithms."),

        p("**Prediction:** Trained editors will detect latent semantic recruitment at above-chance rates when primed with the concept (after reading the audit procedure). Untrained readers will detect it at below-chance rates. Automated systems will not detect it at all, as it operates at a semantic level not addressed by current algorithms."),

        heading("8.3 Countermeasure Study", HeadingLevel.HEADING_2),

        p("**Task:** LLMs generate passages under four conditions: (a) baseline (no instruction), (b) explicit register prohibition, (c) novel axis principle instruction, (d) sustained character voice with novel axis principle embedded. Measure dual-meaning recruitment rates across conditions."),

        p("**Prediction:** Condition (d) will produce the lowest recruitment rate, as the character voice provides both passive defence (sustained register) and active defence (novel axis constraint). Condition (c) will produce intermediate rates, with degradation as context window position increases. Condition (b) will produce modest reduction, as prohibition addresses explicit vocabulary but not latent probability. Condition (a) will produce the baseline recruitment rate."),

        // ============================================================
        // 9. LIMITATIONS
        // ============================================================
        heading("9. Limitations", HeadingLevel.HEADING_1),

        p("This work has several significant limitations that must be acknowledged."),

        p("**Sample size.** The phenomenon was identified through close reading of a single external prose sample and verified against four chapter-length texts from a single project. The generalisability of the findings to other genres, registers, and writing contexts is unknown."),

        p("**Confirmation bias.** The discovery process was collaborative and iterative, with each participant building on the other's observations. It is possible that the pattern identified is an artefact of confirmation bias: once the biological register was identified, both collaborators may have been primed to perceive dual-meaning alignments that a naive reader would not notice. The proposed experimental methodology (Section 8) is designed to address this limitation."),

        p("**Mechanistic claims.** The proposed mechanism (probability elevation of dual-meaning tokens by register-activated context) is plausible given transformer architecture but has not been verified through analysis of model internals (attention weights, token probabilities). The mechanism is presented as a hypothesis, not as an established fact. Interpretability research examining attention patterns during generation of dual-meaning words in register-activated contexts would be valuable."),

        p("**Rate estimates.** The characteristic rates described in Table 1 (0\u20131 for human accidental, 3\u20134 for LLM recruitment) are based on observation of a small number of passages and should be treated as preliminary estimates, not as established baselines."),

        p("**The AI collaborator's self-report.** Several claims in this paper are based on the AI collaborator's reports about its own generation process (e.g., \"feeling\" the gravitational pull toward the intelligence axis in the bird/brain experiment). These self-reports are presented as data about the model's output behaviour, not as verified claims about internal states. The question of whether language models have reliable introspective access to their own generation processes is unresolved and beyond the scope of this paper."),

        p("**Authorship of the external sample.** The external prose sample was suspected but not confirmed to be AI-generated or AI-assisted. The analysis demonstrates the *presence* of latent semantic recruitment in the sample but does not establish its *cause*. A human author writing quickly could, in principle, produce similar patterns through unconscious word selection. The proposed experimental methodology includes a human control group to address this ambiguity."),

        // ============================================================
        // 10. DISCUSSION
        // ============================================================
        heading("10. Discussion", HeadingLevel.HEADING_1),

        heading("10.1 Implications for AI Detection", HeadingLevel.HEADING_2),

        p("If latent semantic recruitment is confirmed as a robust phenomenon, it represents a qualitatively new category of AI detection signal. Unlike vocabulary tells (which can be mitigated by instruction tuning), syntactic tells (which degrade with model improvement), and statistical tells (which are vulnerable to paraphrasing), latent semantic recruitment is an emergent property of the generation architecture itself. It arises from the same contextual probability mechanism that makes language models fluent. Mitigating it requires not surface-level adjustment but active, sustained, semantically-aware countermeasures that oppose the distributional default."),

        p("This suggests that as language models improve in fluency, vocabulary range, and syntactic variety, deeper semantic-level tells may become the most reliable detection signals. The progression from surface tells to semantic tells mirrors the historical progression in other forensic domains: as forgers improve their surface technique, detection moves to deeper layers of analysis."),

        heading("10.2 Implications for Human-AI Collaboration", HeadingLevel.HEADING_2),

        p("The discovery process itself is a case study in productive human-AI collaboration. The human collaborator provided perceptual sensitivity (detecting the phenomenon on the third reading pass), editorial domain knowledge (recognising the problem as a craft failure rather than a random error), and the critical hypothesis (that the dual-meaning recruitment was an AI tell rather than an authorial choice). The AI collaborator provided mechanistic explanation (grounding the phenomenon in transformer architecture), formal codification (translating the intuition into a replicable audit procedure), rapid testing (scanning four chapter-length texts for the phenomenon in minutes), and the generative experiment (testing the novel axis principle with controlled attempts)."),

        p("Neither collaborator could have produced the full analysis independently. The human could not have articulated the token-probability mechanism. The AI could not have detected the phenomenon in the first place. This asymmetry\u2014the human finds, the AI formalises\u2014may be characteristic of a productive collaborative mode for editorial and analytical tasks that operate at the intersection of human perception and computational architecture."),

        heading("10.3 Implications for the Nature of Human vs. Machine Prose", HeadingLevel.HEADING_2),

        p("At the deepest level, latent semantic recruitment suggests that the difference between human and machine prose is not (only) about what words are used or how they are arranged, but about *why* particular words are selected in the context of figurative meaning. A human author selects \"bit\" for a saw with awareness (conscious or unconscious) that the word carries a consumption meaning, and either avoids the word, uses it neutrally, or exploits the double meaning. A language model selects \"bit\" because the surrounding biological context has elevated its probability, and carries the consumption meaning as an unintended passenger."),

        p("The difference is not fluency, not coherence, not vocabulary. It is *semantic intent*: the presence or absence of a selecting intelligence that is aware of the full meaning-space of the words it chooses. This is, perhaps, the deepest level at which human and machine prose can currently be distinguished."),

        // ============================================================
        // 11. CONCLUSION
        // ============================================================
        heading("11. Conclusion", HeadingLevel.HEADING_1),

        p("This paper has described latent semantic recruitment, a phenomenon in which activated figurative registers in LLM-generated prose elevate the selection probability of dual-meaning words whose secondary semantic fields align with the active register. The phenomenon produces a characteristic signature: dual-meaning word alignments at a rate between human accidental production and deliberate authorial craft, occupying an uncanny valley that is detectable by trained close reading but invisible to existing automated detection methods."),

        p("We have presented a formal definition of the phenomenon, a proposed mechanism grounded in transformer architecture, a replicable four-step audit procedure, a generative countermeasure (the novel axis principle), and a proposed experimental methodology for empirical validation. We have further described the detection asymmetry\u2014the observation that the AI collaborator could explain but not detect the phenomenon\u2014which has implications for AI self-editing pipelines and for the complementary roles of human and AI participants in editorial processes."),

        p("The discovery emerged through a collaborative editorial process that neither participant could have conducted independently, suggesting that sustained human-AI collaboration in close-reading contexts can produce analytical frameworks of genuine novelty. Whether latent semantic recruitment proves to be a robust, replicable phenomenon with practical detection applications, or a context-specific observation limited to particular prose registers and generation conditions, remains to be determined by the empirical work we have proposed."),

        p("What is clear is that the deepest differences between human and machine prose may reside not in the tokens selected, nor in the sequences constructed, but in the relationship between the selecting process and the full semantic space of the words it deploys. At this level, the question is no longer *how* the text was generated, but whether the generative process was *aware* of what it was saying."),

        // ============================================================
        // REFERENCES
        // ============================================================
        new Paragraph({ children: [new PageBreak()] }),
        heading("References", HeadingLevel.HEADING_1),

        p("Bakhtin, A., Gross, S., Ott, M., Deng, Y., Ranzato, M., & Szlam, A. (2019). Real or fake? Learning to discriminate machine from human generated text. *arXiv preprint arXiv:1906.03351.*"),
        p("Biber, D., & Conrad, S. (2009). *Register, Genre, and Style.* Cambridge University Press."),
        p("Brown, T. B., Mann, B., Ryder, N., Subbiah, M., Kaplan, J., Dhariwal, P., ... & Amodei, D. (2020). Language models are few-shot learners. *Advances in Neural Information Processing Systems, 33*, 1877\u20131901."),
        p("Gehrmann, S., Strobelt, H., & Rush, A. M. (2019). GLTR: Statistical detection and visualization of generated text. *Proceedings of the 57th Annual Meeting of the Association for Computational Linguistics: System Demonstrations*, 111\u2013116."),
        p("Halliday, M. A. K. (1978). *Language as Social Semiotic: The Social Interpretation of Language and Meaning.* Edward Arnold."),
        p("Holtzman, A., Buys, J., Du, L., Forbes, M., & Choi, Y. (2020). The curious case of neural text degeneration. *International Conference on Learning Representations.*"),
        p("Jawahar, G., Abdul-Mageed, M., & Lakshmanan, L. V. S. (2020). Automatic detection of machine generated text: A critical survey. *Proceedings of the 28th International Conference on Computational Linguistics*, 2296\u20132309."),
        p("Kirchenbauer, J., Geiping, J., Wen, Y., Katz, J., Miers, I., & Goldstein, T. (2023). A watermark for large language models. *Proceedings of the 40th International Conference on Machine Learning.*"),
        p("Liang, W., Yuksekgonul, M., Mao, Y., Wu, E., & Zou, J. (2023). GPT detectors are biased against non-native English writers. *Patterns, 4*(7), 100779."),
        p("Lyons, J. (1977). *Semantics* (Vols. 1\u20132). Cambridge University Press."),
        p("Mitchell, E., Lee, Y., Khazatsky, A., Manning, C. D., & Finn, C. (2023). DetectGPT: Zero-shot machine-generated text detection using probability curvature. *Proceedings of the 40th International Conference on Machine Learning.*"),
        p("Radford, A., Wu, J., Child, R., Luan, D., Amodei, D., & Sutskever, I. (2019). Language models are unsupervised multitask learners. *OpenAI Blog, 1*(8), 9."),
        p("Sadasivan, V. S., Kumar, A., Balasubramanian, S., Wang, W., & Feizi, S. (2023). Can AI-generated text be reliably detected? *arXiv preprint arXiv:2303.11156.*"),
        p("Solaiman, I., Brundage, M., Clark, J., Askell, A., Herbert-Voss, A., Wu, J., ... & Wang, J. (2019). Release strategies and the social impacts of language models. *arXiv preprint arXiv:1908.09203.*"),
        p("Swinney, D. A. (1979). Lexical access during sentence comprehension: (Re)consideration of context effects. *Journal of Verbal Learning and Verbal Behavior, 18*(6), 645\u2013659."),
        p("Trier, J. (1931). *Der deutsche Wortschatz im Sinnbezirk des Verstandes.* Winter."),
        p("Uchendu, A., Ma, J., Le, T., Wang, R., & Lee, D. (2020). Authorship attribution for neural text generation. *Proceedings of the 2020 Conference on Empirical Methods in Natural Language Processing*, 8384\u20138395."),
        p("Vaswani, A., Shazeer, N., Parmar, N., Uszkoreit, J., Jones, L., Gomez, A. N., ... & Polosukhin, I. (2017). Attention is all you need. *Advances in Neural Information Processing Systems, 30.*"),

      ],
    },
  ],
});

// Generate the document
Packer.toBuffer(doc).then(buffer => {
  fs.writeFileSync("/sessions/wizardly-optimistic-bohr/mnt/Ribbonworld/Latent_Semantic_Recruitment.docx", buffer);
  console.log("Document created successfully.");
}).catch(err => {
  console.error("Error:", err);
});
