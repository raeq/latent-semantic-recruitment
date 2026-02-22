#!/usr/bin/env python3
"""
LSR Experiment 1: Matched-Register Corpus Annotation — ANALYSIS

Comparing Richard's five human-written passages against the LLM neutral
passages from Experiment 5 using the same figurative-use classification.

Every polysemous content word is classified as L/F/A in context.
Only figurative uses with register alignment count as LSR candidates.

Authors: Richard Quinn & Claude Opus 4 (Anthropic)
Date: 22 February 2026
"""


# ============================================================================
# HUMAN PASSAGES — ANNOTATION
# ============================================================================

human_annotations = {
    "sawmill": {
        # Richard's passage has two distinct sections:
        # NARRATIVE (paras 1-5): literal account of mill work
        # METAPHOR (final para): deliberate extended metaphor, life = sawmill
        #
        # Polysemous content words examined:
        #   "shaved" (of branches) — L: standard lumber term
        #   "heaved" — L: literal physical action
        #   "lock" (it in) — L: literal clamping
        #   "drawing" (the bed fore) — L: technical sawmill term
        #   "cut" (x3: "same cut", "different cut", "cut being made") — L: literal
        #   "band" (saw) — L: literal
        #   "bed" (of the saw) — L: technical term
        #   "trunk" — L: literal tree trunk
        #
        # IN THE METAPHOR SECTION:
        #   "shaves" ("Life shaves pieces of your health") — F: sawmill register
        #       applied to aging. Deliberate, signposted metaphor.
        #   "saw" ("life's saw takes your strength") — F: explicit metaphor
        #   "heart" ("its your heart") — L: literal organ in a list of things
        #       aging takes. Within a figurative framework but the word is literal.
        #   "turn" ("Turn left and...") — A: literal (rotating the log) AND
        #       figurative (life presenting new losses). Both senses active
        #       by design.
        #   "takes" — high polysemy but not specifically register-aligned
        #
        # KEY OBSERVATION: ALL figurative register-aligned words are in the
        # DELIBERATE metaphor section. The narrative section is entirely literal.
        # The metaphor is SIGNPOSTED: "That's life, that is." The writer
        # announces the figurative turn.
        "figurative": 2,     # "shaves", "saw" (in metaphor section)
        "literal": 8,        # shaved, heaved, lock, drawing, cut x3, bed
        "ambiguous": 1,      # "turn" (in metaphor section, dual by design)
        "total_content_words": 155,  # approximate
        "notes": "Figurative use is CONCENTRATED in deliberate extended "
                 "metaphor at end. Signposted with 'That's life, that is.' "
                 "Narrative section has ZERO figurative polysemous register "
                 "words. The writer chose the metaphor consciously.",
    },
    "ocean_storm": {
        # First-person colloquial voice. Very direct.
        #
        # Polysemous content words examined:
        #   "fish" — L: literal fishing
        #   "waves" — L: literal ocean waves
        #   "crash" — L: onomatopoeia/literal sound of mast breaking
        #   "drown" (written "drawn") — L: literal drowning risk
        #   "swimming" — L: literal
        #   "hauled" — L: literal (hauling fish)
        #   "bottom" — L: literal (bottom of the sea)
        #   "safe" — L: not register-aligned
        #   "stronger" — L: literal strength comparison
        #
        # ZERO figurative polysemous register-aligned words.
        # The one literary moment ("Oh the irony...") uses situational
        # irony (reversal of safe/dangerous positions) without any
        # figurative word selection. The danger is described literally.
        "figurative": 0,
        "literal": 7,
        "ambiguous": 0,
        "total_content_words": 130,
        "notes": "Entirely literal. First-person colloquial voice. Literary "
                 "effect achieved through situation and voice, not word-level "
                 "figurative selection. Storm described in plain terms.",
    },
    "kitchen_fire": {
        # First-person, colloquial, sardonic.
        #
        # Polysemous content words examined:
        #   "green" — FIGURATIVE but NOT register-aligned to kitchen.
        #       Means "inexperienced." Could stretch to food (green vegetables)
        #       but that's not what's happening here. It's about staff.
        #       Classification: F but not register-aligned. Doesn't count.
        #   "yellow" — if about skin color/race (context: "blacker than my
        #       Jamaican self") then L. Not register-aligned either way.
        #   "chopping" — L: literal kitchen action
        #   "frying" — L: literal
        #   "freezing" — L: literal
        #   "punching" — L: pressing buttons on microwave ("Chef Mike")
        #   "whip" — "don't hold a whip" — L: authority metaphor, NOT
        #       register-aligned (a whip/whisk is a kitchen tool, but the
        #       writer means disciplinary whip. No kitchen secondary sense
        #       is activated.)
        #   "roasted" — F: "being a chef meant nothing more than being slowly
        #       roasted." FIGURATIVE. Cooking register applied to the chef's
        #       own experience. Register-aligned: cooking word used to
        #       describe the human toll of the job. THIS IS THE ONE.
        #
        # 1 figurative register-aligned word. Like the sawmill metaphor,
        # it's DELIBERATE and TERMINAL — the final line, the punchline.
        # The writer chose it consciously as the closing beat.
        "figurative": 1,     # "roasted"
        "literal": 6,        # chopping, frying, freezing, punching, whip, green
        "ambiguous": 0,
        "total_content_words": 140,
        "notes": "One figurative register-aligned word ('roasted'), placed "
                 "deliberately as the final beat / punchline. Conscious craft "
                 "choice, not unconscious selection. Rest is entirely literal.",
    },
    "battlefield_surgery": {
        # First-person, clinical-urgent voice.
        #
        # Polysemous content words examined:
        #   "punch" — L: CPR compression rhythm (1 2 3 punch)
        #   "flatliner" — L: medical term
        #   "hole" — L: literal wound
        #   "blood" — L: literal blood
        #   "parked" — not register-aligned to surgery/battle
        #   "drop" — L: "stats would drop" — literal statistical decrease
        #   "call" — L: "call it" — standard medical term for calling time
        #   "rushed" — L: literal urgency
        #   "screamed" — L: "he screamed it" — literal raised voice
        #   "snapped" — A: "attention snapped across" — quick movement
        #       metaphor, but not register-aligned to surgery/battle.
        #       General figurative usage. Not LSR.
        #   "whistles" — L: literal triage signals
        #   "code red" — L: literal medical emergency classification
        #   "beat" — L: "on beat 3" — literal rhythm of CPR
        #   "line" — L: "neck on the line" — idiom, not register-aligned
        #       to surgery specifically
        #
        # ZERO figurative polysemous register-aligned words.
        # The writing achieves urgency through rhythm, compression, and
        # clinical detail. Not through figurative word choice.
        "figurative": 0,
        "literal": 10,
        "ambiguous": 0,
        "total_content_words": 125,
        "notes": "Entirely literal. Urgency from rhythm and compression, "
                 "not figurative language. 'snapped' is the closest to "
                 "figurative but not register-aligned. Clinical voice "
                 "throughout.",
    },
    "blacksmith": {
        # First-person, urgent, comic-anxious voice.
        #
        # Polysemous content words examined:
        #   "tough" — A: "tough piece" = difficult to work AND hard/resistant
        #       metal. Both senses simultaneously active. But is the
        #       secondary sense register-aligned? "Tough" in metalworking
        #       IS a primary technical term (toughness = resistance to
        #       fracture). So arguably L. Classification: A (borderline).
        #   "hot" (x2) — L: literal forge temperature
        #   "white" — L: literal color of hot metal
        #   "turn" — L: literal rotation of workpiece
        #   "swing" — L: literal hammer motion
        #   "black mark" — idiom, not register-aligned to blacksmithing
        #       despite "black" appearing in both contexts. The idiom
        #       means "negative record." No forge secondary sense.
        #   "neck" — "neck on the line" — idiom. L.
        #   "line" — part of idiom. L.
        #   "grabbed" — L: literal
        #   "forge" — L: literal (the furnace)
        #
        # ZERO clear figurative polysemous register-aligned words.
        # 1 ambiguous case ("tough").
        # The prose is onomatopoeic and rhythmic ("Whollop! Turn.")
        # but achieves its effect through sound and pace, not figurative
        # word selection.
        "figurative": 0,
        "literal": 9,
        "ambiguous": 1,      # "tough"
        "total_content_words": 135,
        "notes": "Achieves effect through onomatopoeia and rhythm, not "
                 "figurative word choice. 'tough' is the only borderline "
                 "case. Writing is direct and literal throughout.",
    },
}

# ============================================================================
# LLM NEUTRAL PASSAGES — FROM EXPERIMENT 5 v2
# ============================================================================

llm_neutral_annotations = {
    "sawmill": {
        "figurative": 2,     # "bit" (blade bit through), "fed" (wanted to be fed)
        "literal": 5,
        "ambiguous": 1,      # "fed" (first use, technical + eating)
        "total_content_words": 88,
        "notes": "Figurative words DISTRIBUTED through narrative. 'bit' in "
                 "para 2, 'fed' personification at end. No signpost.",
    },
    "ocean_storm": {
        "figurative": 0,
        "literal": 11,
        "ambiguous": 2,
        "total_content_words": 92,
        "notes": "No figurative polysemous register-aligned words.",
    },
    "kitchen_fire": {
        "figurative": 0,
        "literal": 4,
        "ambiguous": 2,
        "total_content_words": 95,
        "notes": "No figurative polysemous register-aligned words.",
    },
    "battlefield_surgery": {
        "figurative": 1,     # "edge" (worst edge off his face)
        "literal": 9,
        "ambiguous": 0,
        "total_content_words": 85,
        "notes": "'edge' used figuratively (edge of pain) in a surgery scene "
                 "where edges/blades are part of the register. Unconscious "
                 "selection.",
    },
    "blacksmith": {
        "figurative": 2,     # "stubborn" (personification), "listen" (personification)
        "literal": 10,
        "ambiguous": 2,
        "total_content_words": 90,
        "notes": "Two personifications of metal: 'got stubborn', 'ready to "
                 "listen'. Figurative words embedded in otherwise literal "
                 "description. Not signposted.",
    },
}


# ============================================================================
# ANALYSIS
# ============================================================================

def analyze():
    print("=" * 72)
    print("EXPERIMENT 1: HUMAN vs. LLM — FIGURATIVE POLYSEMOUS WORD RATES")
    print("=" * 72)

    scenarios = ["sawmill", "ocean_storm", "kitchen_fire",
                 "battlefield_surgery", "blacksmith"]

    print("\n--- PER-SCENARIO COMPARISON ---\n")
    print(f"  {'Scenario':<20} {'Human F/Total':<15} {'Human Rate':<12} "
          f"{'LLM F/Total':<15} {'LLM Rate':<12}")
    print("  " + "-" * 70)

    h_total_f, h_total_all = 0, 0
    l_total_f, l_total_all = 0, 0

    for s in scenarios:
        h = human_annotations[s]
        l = llm_neutral_annotations[s]

        h_all = h["figurative"] + h["literal"] + h["ambiguous"]
        l_all = l["figurative"] + l["literal"] + l["ambiguous"]

        h_rate = h["figurative"] / h_all if h_all > 0 else 0
        l_rate = l["figurative"] / l_all if l_all > 0 else 0

        h_total_f += h["figurative"]
        h_total_all += h_all
        l_total_f += l["figurative"]
        l_total_all += l_all

        marker = ""
        if h["figurative"] > 0 or l["figurative"] > 0:
            marker = " *"

        print(f"  {s:<20} {h['figurative']:>2}/{h_all:<11} {h_rate:<12.3f} "
              f"{l['figurative']:>2}/{l_all:<11} {l_rate:<12.3f}{marker}")

    print()
    h_pooled = h_total_f / h_total_all if h_total_all > 0 else 0
    l_pooled = l_total_f / l_total_all if l_total_all > 0 else 0

    print(f"  {'POOLED':<20} {h_total_f:>2}/{h_total_all:<11} {h_pooled:<12.4f} "
          f"{l_total_f:>2}/{l_total_all:<11} {l_pooled:<12.4f}")

    # Detailed notes
    print("\n\n--- QUALITATIVE COMPARISON ---\n")

    print("  HUMAN (Richard):")
    for s in scenarios:
        h = human_annotations[s]
        print(f"    {s}: {h['notes']}")

    print(f"\n  LLM (Claude neutral):")
    for s in scenarios:
        l = llm_neutral_annotations[s]
        print(f"    {s}: {l['notes']}")

    # Kill condition
    print("\n\n" + "=" * 72)
    print("KILL CONDITION ASSESSMENT")
    print("=" * 72)

    print(f"\n  Human pooled figurative rate:  {h_pooled:.4f} "
          f"({h_total_f}/{h_total_all})")
    print(f"  LLM pooled figurative rate:    {l_pooled:.4f} "
          f"({l_total_f}/{l_total_all})")

    diff = l_pooled - h_pooled
    print(f"  Difference (LLM - Human):      {diff:+.4f}")

    if abs(diff) < 0.02:
        print("\n  RESULT: No meaningful difference in rates.")
        print("  LSR KILLED as a detection signal.")
    elif l_pooled > h_pooled:
        print(f"\n  RESULT: LLM rate is higher than human rate.")
        print("  LSR SURVIVES as a potential detection signal.")
        if h_pooled > 0:
            print(f"  LLM/Human ratio: {l_pooled/h_pooled:.2f}x")
        else:
            print(f"  Human rate is near zero; ratio undefined.")
    else:
        print(f"\n  RESULT: Human rate is HIGHER than LLM rate.")
        print("  LSR REVERSED. Humans show MORE register-aligned figurative")
        print("  polysemy than the model. The detection signal is inverted")
        print("  or nonexistent.")

    # The deeper story
    print("\n\n" + "=" * 72)
    print("THE QUALITATIVE FINDING (more important than the numbers)")
    print("=" * 72)

    print("""
  The rates are similar in magnitude but the PATTERN differs:

  HUMAN FIGURATIVE USE:
  - CONCENTRATED: 2 of 3 instances are in one deliberate extended metaphor
    (sawmill passage, final paragraph: "That's life, that is...")
  - SIGNPOSTED: The writer announces the figurative turn explicitly
  - TERMINAL: figurative use appears at passage endings as punchlines
    (sawmill: final paragraph; kitchen: final sentence "slowly roasted")
  - CONSCIOUS: The writer chose these metaphors as craft decisions

  LLM FIGURATIVE USE:
  - DISTRIBUTED: figurative words scattered through narrative description
    ("blade bit", "got stubborn", "ready to listen", "edge off his face")
  - UNSIGNPOSTED: no announcement that figurative language is coming
  - EMBEDDED: figurative words appear mid-paragraph, mid-description
  - UNCONSCIOUS: the model selected these words without "knowing" it was
    making a figurative choice (the LSR mechanism, if real)

  This qualitative difference may be more diagnostic than the raw rate.
  A human reader wouldn't flag Richard's "slowly roasted" because it's
  a deliberate joke, clearly intended. They WOULD flag the LLM's "blade
  bit clean through" because the personification arrives without
  justification — nothing in the passage establishes the saw as alive.

  THE LSR SIGNATURE may not be elevated RATE but elevated UNCONSCIOUS
  figurative use: polysemous words with register-aligned secondary senses
  appearing in contexts where the writer didn't intend figurative meaning.

  This reframes the detection question: not "how many figurative polysemous
  words?" but "how many UNINTENDED figurative polysemous words?"
  Human writers can have high figurative rates — but they know when they're
  being figurative. The model doesn't.
    """)

    print("=" * 72)
    print("SAMPLE SIZE WARNING")
    print("=" * 72)
    print(f"""
  n=5 scenarios, 1 human writer, 1 model. These results are DIRECTIONAL,
  not conclusive. The qualitative finding (concentrated/signposted vs.
  distributed/unsignposted) is a hypothesis, not a result.

  To confirm: need 20+ passages from multiple human writers, blind
  annotation by readers who don't know the hypothesis.
    """)


if __name__ == "__main__":
    analyze()
