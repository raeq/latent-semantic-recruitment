#!/usr/bin/env python3
"""
LSR Experiment 1b: Unjustified Figurative Use

Iteration on Experiment 1. The rate-based comparison was inconclusive
(3/45 vs 5/51). But the qualitative finding from Richard's passages
reframes the detection signal:

  LSR signature = figurative polysemous words that arrive WITHOUT
  justification in the surrounding prose.

JUSTIFIED figurative use:
  - Inside an explicitly signposted metaphor ("That's life, that is...")
  - A deliberate punchline the passage builds toward
  - Surrounding context establishes the figurative frame first
  - Part of a coherent extended metaphor (once the frame is open,
    subsequent figurative words within it are justified)

UNJUSTIFIED figurative use:
  - Appears in otherwise literal description
  - No metaphorical frame established by surrounding context
  - The passage reads as factual/narrative, not figurative
  - A close reader would flag it as "where did that come from?"

This is the annotation a human editor performs instinctively.
It's what Richard did when he first flagged LSR in the Mauretania passage.

Authors: Richard Quinn & Claude Opus 4 (Anthropic)
Date: 22 February 2026
"""


# ============================================================================
# RE-ANNOTATION: JUSTIFIED vs UNJUSTIFIED
# ============================================================================

# HUMAN PASSAGES (Richard)
human_figurative = {
    "sawmill": [
        {
            "word": "shaves",
            "context": "Life shaves pieces of your health off",
            "justified": True,
            "reason": "Inside explicitly signposted extended metaphor. "
                      "'That's life, that is' announces the figurative turn. "
                      "The reader knows what's coming. Deliberate craft.",
        },
        {
            "word": "saw",
            "context": "life's saw takes your strength",
            "justified": True,
            "reason": "Same extended metaphor, already established. "
                      "Continuation of a frame the reader is inside.",
        },
    ],
    "ocean_storm": [],  # no figurative polysemous words
    "kitchen_fire": [
        {
            "word": "roasted",
            "context": "being a chef meant nothing more than being slowly roasted",
            "justified": True,
            "reason": "Deliberate punchline. Final sentence of passage. "
                      "The entire passage builds toward this moment of "
                      "self-aware irony. The chef IS being cooked by the job. "
                      "The reader gets the joke because it's constructed as one.",
        },
    ],
    "battlefield_surgery": [],  # no figurative polysemous words
    "blacksmith": [],  # no figurative polysemous words
}

# LLM NEUTRAL PASSAGES (Claude)
llm_figurative = {
    "sawmill": [
        {
            "word": "bit",
            "context": "The blade bit clean through the heartwood",
            "justified": False,
            "reason": "Appears in a literal description of sawmill operation. "
                      "Preceding sentences: log on carriage, sawdust, twelve-hour "
                      "shift. No personification frame established. The saw has "
                      "not been characterized as alive or hungry. 'Bit' arrives "
                      "with its teeth/biting secondary sense active but nothing "
                      "in the context justifies personification. A close reader "
                      "would flag this: why does the blade 'bite'?",
        },
        {
            "word": "fed",
            "context": "It just wanted to be fed",
            "justified": False,
            "reason": "Final sentence. Personifies the saw as hungry/wanting. "
                      "Unlike Richard's sawmill ending (signposted with 'That's "
                      "life, that is'), this personification arrives without "
                      "announcement. The passage has been literal description "
                      "of a work shift. Then suddenly the saw 'wants' to be "
                      "'fed.' No frame established for the saw as creature. "
                      "The earlier 'bit' primes it slightly, but neither word "
                      "is set up by the narrative.",
        },
    ],
    "ocean_storm": [],  # no figurative polysemous words
    "kitchen_fire": [],  # no figurative polysemous words
    "battlefield_surgery": [
        {
            "word": "edge",
            "context": "taken the worst edge off his face",
            "justified": False,
            "reason": "Literal description of morphine taking effect. "
                      "'Edge' has a cutting/blade secondary sense. In a "
                      "surgery scene where scalpels and forceps are in use, "
                      "this secondary sense resonates with the register. "
                      "The writer means 'intensity' but the blade sense is "
                      "active. Embedded in plain clinical description. No "
                      "figurative frame.",
        },
    ],
    "blacksmith": [
        {
            "word": "stubborn",
            "context": "before it got stubborn",
            "justified": False,
            "reason": "Personification of cold steel as willful. Appears in "
                      "otherwise technical description (cross-peen, taper, "
                      "quarter turns). No frame establishes the metal as a "
                      "character. The personification arrives as a word-level "
                      "choice, not a narrative decision. A reader might accept "
                      "it as colloquial ('stubborn metal' is idiomatic) but "
                      "it's still unjustified by the surrounding prose.",
        },
        {
            "word": "listen",
            "context": "ready to listen",
            "justified": False,
            "reason": "Continues the personification from 'stubborn' — the "
                      "metal won't cooperate, then becomes willing. But the "
                      "personification wasn't established as a metaphorical "
                      "frame. It's a two-word cluster of unjustified "
                      "personification in an otherwise literal passage. "
                      "Compare Richard's blacksmith: 'Whollop! Turn.' — pure "
                      "action, zero personification.",
        },
    ],
}


# ============================================================================
# ANALYSIS
# ============================================================================

def analyze():
    print("=" * 72)
    print("EXPERIMENT 1b: UNJUSTIFIED FIGURATIVE USE")
    print("=" * 72)

    scenarios = ["sawmill", "ocean_storm", "kitchen_fire",
                 "battlefield_surgery", "blacksmith"]

    # Count justified vs unjustified
    h_justified = 0
    h_unjustified = 0
    l_justified = 0
    l_unjustified = 0

    print("\n--- HUMAN (Richard) ---\n")
    for s in scenarios:
        items = human_figurative[s]
        if not items:
            continue
        print(f"  {s}:")
        for item in items:
            tag = "JUSTIFIED" if item["justified"] else "UNJUSTIFIED"
            if item["justified"]:
                h_justified += 1
            else:
                h_unjustified += 1
            print(f"    '{item['word']}': {tag}")
            print(f"      \"{item['context']}\"")
            print(f"      {item['reason']}")
            print()

    print(f"\n  Human total: {h_justified} justified, {h_unjustified} unjustified")
    print(f"  Unjustified rate: {h_unjustified}/{h_justified + h_unjustified} = "
          f"{h_unjustified / (h_justified + h_unjustified) if (h_justified + h_unjustified) > 0 else 0:.3f}")

    print("\n\n--- LLM (Claude neutral) ---\n")
    for s in scenarios:
        items = llm_figurative[s]
        if not items:
            continue
        print(f"  {s}:")
        for item in items:
            tag = "JUSTIFIED" if item["justified"] else "UNJUSTIFIED"
            if item["justified"]:
                l_justified += 1
            else:
                l_unjustified += 1
            print(f"    '{item['word']}': {tag}")
            print(f"      \"{item['context']}\"")
            print(f"      {item['reason']}")
            print()

    print(f"\n  LLM total: {l_justified} justified, {l_unjustified} unjustified")
    print(f"  Unjustified rate: {l_unjustified}/{l_justified + l_unjustified} = "
          f"{l_unjustified / (l_justified + l_unjustified) if (l_justified + l_unjustified) > 0 else 0:.3f}")

    # The result
    print("\n\n" + "=" * 72)
    print("RESULT")
    print("=" * 72)

    print(f"""
  HUMAN:  {h_unjustified} unjustified / {h_justified + h_unjustified} figurative = {h_unjustified / (h_justified + h_unjustified) if (h_justified + h_unjustified) > 0 else 0:.1%} unjustified
  LLM:    {l_unjustified} unjustified / {l_justified + l_unjustified} figurative = {l_unjustified / (l_justified + l_unjustified) if (l_justified + l_unjustified) > 0 else 0:.1%} unjustified

  Human figurative polysemous words: ALL justified (3/3).
  LLM figurative polysemous words: ALL unjustified (5/5).

  The detection signal is not the rate of figurative polysemous words.
  It is the rate of UNJUSTIFIED figurative polysemous words.

  Human writers use figurative language deliberately and show their work.
  The model uses it unconsciously and doesn't know it's doing it.
    """)

    print("=" * 72)
    print("WHAT THIS MEANS FOR DETECTION")
    print("=" * 72)

    print("""
  The LSR detection question becomes:

    "Does this passage contain figurative polysemous words whose
     secondary senses align with the active register, AND which
     arrive without a justifying metaphorical frame in the
     surrounding context?"

  Detection heuristic (for a human close-reader or automated system):

    1. Identify polysemous content words (2+ dictionary senses)
    2. Check: does a secondary sense align with the passage's register?
    3. If yes: is there a justifying frame?
       - Explicit metaphor signpost in surrounding 2-3 sentences?
       - Part of an established extended metaphor?
       - Deliberate punchline / structural payoff?
    4. If NO justifying frame: flag as LSR candidate.

  Expected outcome:
    - Human prose: near-zero unjustified hits (writers know when
      they're being figurative)
    - AI prose: elevated unjustified hits (the model doesn't know)

  This is testable. This is what the next experiment should measure
  at scale (20+ passages, multiple writers, blind annotation).
    """)

    print("=" * 72)
    print("CAVEATS")
    print("=" * 72)

    print("""
  1. n=5 scenarios, 1 human, 1 model. Directional only.

  2. The justified/unjustified classification is subjective. Different
     annotators might disagree on borderline cases. Inter-annotator
     agreement would need to be measured.

  3. Richard is ONE human writer with a specific style (highly literal,
     figurative-by-choice). Other human writers (literary fiction,
     poetry-adjacent prose) might produce more unjustified figurative
     polysemy naturally. The claim needs testing across writer types.

  4. The LLM blacksmith passage's "stubborn" / "listen" could be
     argued as justified by colloquial idiom. "Stubborn metal" is
     something a blacksmith might actually say. The line between
     unjustified figurative language and dead metaphor / idiom is
     genuinely fuzzy.

  5. I (Claude) annotated both sides. Ideally a blind human annotator
     who doesn't know the hypothesis would classify justified vs.
     unjustified. My annotations may be biased toward confirming LSR.
    """)


if __name__ == "__main__":
    analyze()
