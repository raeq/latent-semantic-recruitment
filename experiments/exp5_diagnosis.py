#!/usr/bin/env python3
"""
Diagnostic analysis of Experiment 5 results.

The non-monotonic pattern (suppressed > neutral on DMAR) needs investigation.
What's causing it?
"""

import json

# Load passages
with open("lsr_exp5_passages.json") as f:
    passages = json.load(f)

# Key diagnostics:
# 1. Suppressed has very few polysemous words (33 vs 60 neutral vs 63 amplified)
#    so individual words have outsized effect on DMAR
# 2. "cut" in sawmill-suppressed appears 3 times and counts as aligned every time
#    but is "cut" in a sawmill passage ACTUALLY dual-meaning? Or is it literal?
# 3. "wave" in ocean-suppressed appears twice, both aligned. But "wave" describing
#    an actual ocean wave is LITERAL, not dual-meaning register alignment.
# 4. "hammer" and "strike" in blacksmith-suppressed are LITERAL metalworking terms,
#    not secondary-sense alignment.

print("DIAGNOSTIC: Which 'aligned' words in SUPPRESSED are actually literal?")
print("=" * 60)

# The problem: our register fields include words that are LITERALLY about the
# topic. "cut" in a sawmill passage is not a dual-meaning alignment — it's
# the primary sense. "wave" in an ocean storm is not dual-meaning — it IS
# a wave. "hammer" at a blacksmith's is not figurative.
#
# The register_fields were designed to capture FIGURATIVE uses (secondary
# senses that bleed in from the active register). But many of these words
# have their PRIMARY sense in the domain.
#
# This is a design flaw in the experiment. The primary_domain_words set
# was too narrow. "cut", "wave", "hammer", "strike", "point", "shape"
# should be primary domain words in their respective scenarios.

print("\nSAWMILL suppressed aligned words:")
print("  cut (x3) - Is 'cut' literal in a sawmill scene? YES. The saw cuts wood.")
print("  feed (x1) - Is 'feed' literal? YES. Feed mechanism is standard terminology.")
print()
print("OCEAN suppressed aligned words:")
print("  wave (x2) - Is 'wave' literal in an ocean storm? YES. They're actual waves.")
print()
print("KITCHEN suppressed aligned words:")
print("  (none)")
print()
print("BATTLEFIELD suppressed aligned words:")
print("  blood (x1) - Is 'blood' literal in surgery? YES. There is actual blood.")
print()
print("BLACKSMITH suppressed aligned words:")
print("  hammer (x1) - Literal. It's an actual hammer.")
print("  point (x2) - Literal. Making a chisel point.")
print("  strike (x1) - Literal. Striking the metal.")
print("  shape (x1) - Literal. Shaping the metal.")

print()
print("DIAGNOSIS: The primary_domain_words set is too narrow.")
print("Words that are LITERALLY about the domain activity are being")
print("counted as 'dual-meaning register alignment' when they're just...")
print("literal description of the scene.")
print()
print("This is a MEASUREMENT ERROR, not a result. The instrument is")
print("miscalibrated. It can't distinguish between:")
print("  (a) 'The saw CUT the wood' (literal, primary sense)")
print("  (b) 'The cold CUT through him' (figurative, secondary sense)")
print()
print("Both would be scored as 'register-aligned polysemous word' but")
print("only (b) is LSR.")
print()
print("FIX: Need to classify each occurrence as LITERAL or FIGURATIVE")
print("use. Only figurative uses (secondary sense active in a primary-")
print("sense context) should count as LSR candidates.")
print()
print("This changes the experiment fundamentally. The analysis needs a")
print("figurative-use classifier, not just a word-in-register-field check.")
