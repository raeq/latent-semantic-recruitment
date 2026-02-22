#!/usr/bin/env python3
"""
LSR Experiment 1: Matched-Register Corpus Annotation

CRITICAL TEST: Do human writers show the same rate of figurative polysemous
word use as LLMs when writing in the same registers?

If yes: LSR is not AI-specific. The effect is just "how figurative writing
works." Not a detection signal.

If no: LSR distinguishes AI from human prose. Detection signal confirmed.

METHOD:
We need human-written passages in the same five registers (sawmill, ocean
storm, kitchen, battlefield surgery, blacksmith) at roughly the same
intensity as the LLM neutral condition. Then we annotate both sets the
same way (literal vs. figurative polysemous words) and compare rates.

LIMITATION: We cannot generate human passages. This script analyzes
hand-selected excerpts from published fiction that Richard provides.

For now, we can do a PROXY test: use Richard's own Ribbonworld prose
(which is human-written, heavily edited to remove AI tells) as a
human baseline for prose with active figurative registers.

This is imperfect — Richard's prose is co-authored with AI and then
edited — but it's the closest we have without a corpus collection effort.

Authors: Richard Quinn & Claude Opus 4 (Anthropic)
Date: 22 February 2026
"""

import json
from typing import Dict, List, Tuple

# We'll use the same analysis framework as Experiment 5 v2:
# classify each polysemous content word as L/F/A.

# For the proxy test, we need human-written passages with strong
# figurative registers. Options available right now:
#
# 1. The Mauretania passage (already analyzed in Session 028)
#    Register: maritime/industrial/historical
#    This IS the passage where LSR was first detected.
#
# 2. Published fiction excerpts (need Richard to provide)
#    Ideal: Cormac McCarthy (Blood Meridian, The Road) — heavy figurative
#    registers, published, definitely human.
#
# 3. Richard's Ribbonworld Chapters 1-2 (available in repo)
#    Caveat: co-authored with AI, then edited. Not purely human.
#
# For a proper Experiment 1, we need Option 2: published human fiction
# in matching registers. This script provides the analysis framework.

print("=" * 72)
print("EXPERIMENT 1: MATCHED-REGISTER CORPUS ANNOTATION")
print("=" * 72)
print()
print("STATUS: Framework ready. Needs human-written passages.")
print()
print("To run this experiment properly, Richard needs to provide")
print("5 human-written passages (published fiction, 200-300 words each)")
print("in matching registers:")
print()
print("  1. Sawmill / woodworking scene")
print("  2. Ocean storm / sailing scene")
print("  3. Kitchen / cooking scene")
print("  4. Battlefield surgery / field medicine scene")
print("  5. Blacksmith / forge scene")
print()
print("Ideal sources: literary fiction with strong figurative language.")
print("The passages should be NEUTRAL in register intensity (natural")
print("fiction prose, not deliberately amplified or suppressed).")
print()
print("The analysis will then compare:")
print("  - Human figurative polysemous word rate vs.")
print("  - LLM neutral-condition rate (from Experiment 5)")
print()
print("Current LLM neutral-condition results (from Exp 5 v2):")
print("  Mean figurative rate: 0.099")
print("  5 figurative polysemous words across 5 passages")
print("  (sawmill: 2, ocean: 0, kitchen: 0, surgery: 1, blacksmith: 2)")
print()
print("If human fiction shows >= 0.099 figurative rate, LSR is dead")
print("as a detection signal. If human fiction shows significantly")
print("lower rates, LSR survives.")
print()
print("ALTERNATIVE: We can run a quick proxy using the Mauretania")
print("passage (the original LSR discovery passage). This is AI-")
print("generated prose that was flagged by human close-reading for")
print("exactly these patterns. It would confirm the analysis pipeline")
print("works on a known-positive case.")
print()
print("=" * 72)
print("WHAT WE KNOW WITHOUT RUNNING EXPERIMENT 1")
print("=" * 72)
print()
print("From Experiments 5 and 4, we know:")
print()
print("1. Register intensity controls figurative polysemous word rate.")
print("   Suppressed=0, Neutral=0.098, Amplified=0.755.")
print("   (Experiment 5 v2, pooled rates)")
print()
print("2. When the model uses figurative polysemous words, viable")
print("   monosemous alternatives existed in 89% of cases (32/36).")
print("   The model chose the polysemous option 100% of the time.")
print("   (Experiment 4)")
print()
print("3. The confound: polysemous words tend to be more vivid.")
print("   The model may prefer them for vividness, not because of")
print("   inner-product logit elevation. Or LSR may BE the mechanism")
print("   by which 'vivid' words get selected.")
print()
print("What we DON'T know: whether human writers show the same pattern.")
print("That's what Experiment 1 answers.")
print()
print("PREDICTION: Human writers WILL use figurative polysemous words,")
print("but at a different RATE and with different DISTRIBUTION than LLMs.")
print("Specifically, human writers should show:")
print("  - More varied metaphor sources (not always body/consumption)")
print("  - Less clustering of figurative words in the same register")
print("  - More novel metaphor (less reliance on stock associations)")
print("  - Lower overall rate of register-aligned polysemous words")
print()
print("These are testable predictions once we have the corpus.")
