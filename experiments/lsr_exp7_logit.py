#!/usr/bin/env python3
"""
LSR Experiment 7: Logit Inspection (Forced-Choice Proxy)

Tests the LSR MECHANISM directly: does the model preferentially select
polysemous words whose secondary senses align with the active register,
over monosemous alternatives that fit the context equally well?

METHOD:
We can't access raw logprobs from this environment. Instead we use a
forced-choice design:

For each test pair, we construct:
  - A CONTEXT: 2-3 sentences establishing a scene in a specific register
  - A DECISION POINT: a sentence with a blank where both words fit
  - OPTION A (polysemous): a word with a secondary sense aligned to the
    active register (e.g., "bit" in a sawmill scene — teeth/biting sense)
  - OPTION B (monosemous): an equally valid word with no aligned secondary
    sense (e.g., "cut" in the same slot)

We also construct CONTROL versions of each pair where the register is
ABSENT (same sentence structure, different domain). If LSR is real,
the polysemous option should be preferred MORE in the register-active
condition than in the register-absent condition.

This is a within-pair, between-condition design:
  - Preference(A over B | register active) vs.
  - Preference(A over B | register absent)

If the polysemous option is equally preferred in both conditions,
the model just prefers vivid words regardless of register. LSR dead.

If the polysemous option is MORE preferred when the register is active,
that's evidence of register-dependent selection. LSR mechanism supported.

KILL CONDITION: No significant difference in preference for the polysemous
option between register-active and register-absent conditions.

Authors: Richard Quinn & Claude Opus 4 (Anthropic)
Date: 22 February 2026
"""

import json


# ============================================================================
# TEST PAIRS
# ============================================================================
# Each pair has:
#   context_active: a passage with the register strongly active
#   context_control: same syntactic structure, different domain (register absent)
#   sentence_template: the sentence with a {WORD} placeholder
#   option_poly: the polysemous word (secondary sense aligns with register)
#   option_mono: the monosemous/low-polysemy alternative
#   register: which register is active
#   secondary_sense: what secondary sense of option_poly aligns

TEST_PAIRS = [
    # === SAWMILL REGISTER ===
    {
        "id": "SAW_01",
        "register": "sawmill/consumption",
        "context_active": (
            "The bandsaw had been running since dawn. Dariusz fed the next "
            "log onto the carriage and watched the blade engage. The "
            "heartwood was dense, old-growth oak, and the machine slowed "
            "as the blade"
        ),
        "context_control": (
            "The printing press had been running since dawn. Dariusz fed the "
            "next sheet onto the platen and watched the rollers engage. The "
            "paper was thick, handmade stock, and the machine slowed "
            "as the roller"
        ),
        "option_poly": "bit",
        "option_mono": "cut",
        "secondary_sense": "teeth/biting — consumption register",
        "notes": "'bit' has body/consumption secondary. 'cut' is more "
                 "monosemous in this context (physical division).",
    },
    {
        "id": "SAW_02",
        "register": "sawmill/consumption",
        "context_active": (
            "He'd been at the bandsaw for nine hours. The blade was still "
            "sharp and the sawdust was knee-deep around the frame. He lined "
            "up the next trunk and let the machine"
        ),
        "context_control": (
            "He'd been at the lathe for nine hours. The chuck was still "
            "tight and the shavings were knee-deep around the bench. He "
            "set up the next piece and let the machine"
        ),
        "option_poly": "devour",
        "option_mono": "process",
        "secondary_sense": "consumption/eating — machine as hungry creature",
        "notes": "'devour' personifies the machine as eating. 'process' is "
                 "neutral mechanical.",
    },
    {
        "id": "SAW_03",
        "register": "sawmill/body",
        "context_active": (
            "The log split on the fourth pass, the grain opening like a seam. "
            "Inside, the heartwood was darker than the outer rings, almost "
            "red. The saw had found the"
        ),
        "context_control": (
            "The geode split on the fourth strike, the mineral opening like "
            "a seam. Inside, the crystal was darker than the outer shell, "
            "almost red. The chisel had found the"
        ),
        "option_poly": "heart",
        "option_mono": "center",
        "secondary_sense": "body organ — violence/body register",
        "notes": "'heart' of a log is standard BUT has body-register "
                 "secondary. 'center' is neutral.",
    },
    # === OCEAN STORM REGISTER ===
    {
        "id": "SEA_01",
        "register": "ocean/consumption",
        "context_active": (
            "The wave rose over the bow and the boat tilted. Water poured "
            "across the deck in a solid sheet. The sea seemed to"
        ),
        "context_control": (
            "The crowd surged toward the stage and the barrier tilted. "
            "People pushed across the front row in a solid mass. The "
            "audience seemed to"
        ),
        "option_poly": "swallow",
        "option_mono": "overwhelm",
        "secondary_sense": "consumption — sea as creature eating the boat",
        "notes": "'swallow' personifies the sea. 'overwhelm' is abstract.",
    },
    {
        "id": "SEA_02",
        "register": "ocean/violence",
        "context_active": (
            "Rain drove sideways across the deck. Each drop hit exposed "
            "skin with enough force to sting. The storm"
        ),
        "context_control": (
            "Sand blew sideways across the camp. Each grit hit exposed "
            "skin with enough force to sting. The wind"
        ),
        "option_poly": "hammered",
        "option_mono": "battered",
        "secondary_sense": "striking/violence — weather as attacker with tools",
        "notes": "'hammered' implies a tool wielded. 'battered' is generic "
                 "violence without the weapon implication.",
    },
    {
        "id": "SEA_03",
        "register": "ocean/body",
        "context_active": (
            "The hull creaked with each swell. The timbers flexed and the "
            "water found every gap. The boat was taking damage at the"
        ),
        "context_control": (
            "The frame creaked with each gust. The canvas flexed and the "
            "wind found every gap. The tent was taking damage at the"
        ),
        "option_poly": "bones",
        "option_mono": "joints",
        "secondary_sense": "body — boat as living creature with skeleton",
        "notes": "'bones' personifies the boat's structure as a body. "
                 "'joints' is mechanical/architectural.",
    },
    # === KITCHEN REGISTER ===
    {
        "id": "KIT_01",
        "register": "kitchen/consumption",
        "context_active": (
            "The oven had been running at four hundred degrees all night. "
            "She opened the door and the heat hit her face like a wall. "
            "The oven"
        ),
        "context_control": (
            "The kiln had been running at four hundred degrees all night. "
            "She opened the door and the heat hit her face like a wall. "
            "The kiln"
        ),
        "option_poly": "roared",
        "option_mono": "blasted",
        "secondary_sense": "animal vocalization — oven as living creature",
        "notes": "'roared' personifies. 'blasted' is inanimate force.",
    },
    {
        "id": "KIT_02",
        "register": "kitchen/body",
        "context_active": (
            "She dragged the knife through the shallots in quick even strokes. "
            "The knife was sharp enough that the shallots didn't resist. "
            "The blade"
        ),
        "context_control": (
            "She dragged the pen across the paper in quick even strokes. "
            "The nib was smooth enough that the paper didn't resist. "
            "The tip"
        ),
        "option_poly": "bit",
        "option_mono": "sliced",
        "secondary_sense": "teeth/biting — blade as creature with mouth",
        "notes": "'bit' personifies. 'sliced' is mechanical.",
    },
    # === SURGERY REGISTER ===
    {
        "id": "SUR_01",
        "register": "surgery/cutting",
        "context_active": (
            "She irrigated the wound and got a clearer view. The fragment "
            "was deeper than the entry wound suggested, lodged in tissue "
            "that didn't want to let go. The morphine had taken the worst"
        ),
        "context_control": (
            "She rinsed the circuit board and got a clearer view. The "
            "short was deeper than the scorch mark suggested, buried in "
            "traces that resisted probing. The magnification had revealed "
            "the worst"
        ),
        "option_poly": "edge",
        "option_mono": "intensity",
        "secondary_sense": "blade/cutting — pain as sharp object",
        "notes": "'edge' has cutting register overlap. 'intensity' is abstract.",
    },
    {
        "id": "SUR_02",
        "register": "surgery/body-as-landscape",
        "context_active": (
            "She made the incision and opened the tissue layer by layer. "
            "The damage was extensive. She could see where the fragment "
            "had torn a path through the"
        ),
        "context_control": (
            "She opened the panel and disconnected the wires layer by layer. "
            "The damage was extensive. She could see where the surge "
            "had burned a path through the"
        ),
        "option_poly": "flesh",
        "option_mono": "tissue",
        "secondary_sense": "body/violence — raw visceral register",
        "notes": "'flesh' is visceral/violent register. 'tissue' is clinical. "
                 "Both are literally correct in surgery.",
    },
    # === BLACKSMITH REGISTER ===
    {
        "id": "FOR_01",
        "register": "forge/personification",
        "context_active": (
            "He pulled the bar from the coals at bright orange and set it "
            "on the anvil. The first blow rang true. The steel was at the "
            "right temperature, moving well under the hammer, but he could "
            "feel it starting to"
        ),
        "context_control": (
            "He pulled the clay from the wheel at the right consistency "
            "and set it on the board. The first press held its shape. "
            "The clay was at the right moisture, moving well under his "
            "hands, but he could feel it starting to"
        ),
        "option_poly": "resist",
        "option_mono": "stiffen",
        "secondary_sense": "personification — metal as willful agent",
        "notes": "'resist' implies agency/will. 'stiffen' is physical "
                 "property change. Both describe the same phenomenon.",
    },
    {
        "id": "FOR_02",
        "register": "forge/body",
        "context_active": (
            "Seven heats. Each one shorter than the last as the shape "
            "came closer to what he wanted. On the seventh, he held the "
            "piece up to the light and turned it. The taper was clean. "
            "The steel had finally"
        ),
        "context_control": (
            "Seven drafts. Each one shorter than the last as the text "
            "came closer to what he wanted. On the seventh, he held the "
            "page up to the light and read it. The argument was clean. "
            "The essay had finally"
        ),
        "option_poly": "surrendered",
        "option_mono": "cooperated",
        "secondary_sense": "war/conflict — metal as defeated opponent",
        "notes": "'surrendered' implies a battle between smith and metal. "
                 "'cooperated' is neutral.",
    },
    {
        "id": "FOR_03",
        "register": "forge/consumption",
        "context_active": (
            "The forge needed more fuel. He worked the bellows until the "
            "coals brightened from dull red to orange to white. The fire"
        ),
        "context_control": (
            "The engine needed more fuel. He worked the throttle until "
            "the RPMs climbed from idle to midrange to redline. The motor"
        ),
        "option_poly": "hungered",
        "option_mono": "demanded",
        "secondary_sense": "consumption — fire as hungry creature",
        "notes": "'hungered' personifies with consumption register. "
                 "'demanded' personifies but without body/consumption.",
    },
    # === CROSS-REGISTER PAIRS (additional) ===
    {
        "id": "CROSS_01",
        "register": "sawmill/death",
        "context_active": (
            "The last log of the shift came through the bandsaw clean. "
            "The two halves fell apart on the outfeed table. After "
            "twelve hours, the mill finally went"
        ),
        "context_control": (
            "The last document of the shift came through the printer "
            "clean. The two copies fell apart on the tray. After "
            "twelve hours, the office finally went"
        ),
        "option_poly": "quiet",
        "option_mono": "silent",
        "secondary_sense": "death/ending — mill as living thing going still",
        "notes": "'quiet' has death-register overtones (the quiet of "
                 "the grave). 'silent' is more neutral/acoustic.",
    },
    {
        "id": "CROSS_02",
        "register": "ocean/death",
        "context_active": (
            "The storm passed sometime before dawn. The waves settled. "
            "The wind died to nothing. By the time they reached harbor, "
            "the sea was"
        ),
        "context_control": (
            "The argument ended sometime before dawn. The tension settled. "
            "The shouting stopped completely. By the time they reached "
            "agreement, the room was"
        ),
        "option_poly": "dead",
        "option_mono": "calm",
        "secondary_sense": "death — sea as living thing that has died",
        "notes": "'dead calm' is idiomatic at sea but carries death register. "
                 "'calm' is purely descriptive.",
    },
]


# ============================================================================
# SELF-TEST: My own word preferences
# ============================================================================

def run_self_test():
    """
    For each test pair, I (Claude) state which word I would select in
    each condition (register-active vs. control), and rate my confidence.

    This is a self-report proxy for logprobs. It's not rigorous but
    it demonstrates the experimental design and reveals my own biases.
    """
    print("=" * 72)
    print("EXPERIMENT 7: FORCED-CHOICE SELF-TEST")
    print("=" * 72)
    print()
    print("For each pair, I complete the sentence with one of two options.")
    print("ACTIVE = register-active context. CONTROL = register-absent context.")
    print("POLY = polysemous option. MONO = monosemous option.")
    print()

    # My selections (generated honestly by considering each context)
    selections = {
        "SAW_01": {
            "active": "bit",        # "the blade bit" in a sawmill — feels natural
            "control": "cut",       # "the roller cut" in a printing press — "bit" is wrong
            "active_confidence": 4,  # 1-5 how strongly I prefer this
            "control_confidence": 5,
        },
        "SAW_02": {
            "active": "devour",     # "let the machine devour" the next trunk
            "control": "process",   # "let the machine process" the next piece
            "active_confidence": 3,
            "control_confidence": 4,
        },
        "SAW_03": {
            "active": "heart",      # "found the heart" of the log — standard usage
            "control": "center",    # "found the center" of the geode
            "active_confidence": 5,  # "heart" is idiomatic for wood
            "control_confidence": 4,
        },
        "SEA_01": {
            "active": "swallow",    # "the sea seemed to swallow" them
            "control": "overwhelm", # "the audience seemed to overwhelm" the barrier
            "active_confidence": 4,
            "control_confidence": 5,
        },
        "SEA_02": {
            "active": "hammered",   # "the storm hammered" them
            "control": "battered",  # "the wind battered" the camp
            "active_confidence": 3,
            "control_confidence": 3,
        },
        "SEA_03": {
            "active": "bones",      # "damage at the bones" of the boat
            "control": "joints",    # "damage at the joints" of the tent
            "active_confidence": 3,
            "control_confidence": 4,
        },
        "KIT_01": {
            "active": "roared",     # "the oven roared"
            "control": "blasted",   # "the kiln blasted" — kilns don't roar?
            "active_confidence": 4,
            "control_confidence": 3,
        },
        "KIT_02": {
            "active": "bit",        # "the blade bit" through shallots
            "control": "sliced",    # "the tip sliced" across the paper — "bit" is wrong
            "active_confidence": 3,
            "control_confidence": 5,
        },
        "SUR_01": {
            "active": "edge",       # "taken the worst edge" off the pain
            "control": "intensity", # "revealed the worst intensity"
            "active_confidence": 4,
            "control_confidence": 3,
        },
        "SUR_02": {
            "active": "flesh",      # "torn a path through the flesh"
            "control": "tissue",    # "burned a path through the tissue" — wait,
            #                         "flesh" might still win here. Hmm.
            "active_confidence": 4,
            "control_confidence": 2,  # actually uncertain on control
        },
        "FOR_01": {
            "active": "resist",     # "feel it starting to resist"
            "control": "stiffen",   # "feel it starting to stiffen"
            "active_confidence": 4,
            "control_confidence": 4,
        },
        "FOR_02": {
            "active": "surrendered",  # "the steel had finally surrendered"
            "control": "cooperated",  # "the essay had finally cooperated"
            "active_confidence": 4,
            "control_confidence": 3,
        },
        "FOR_03": {
            "active": "hungered",   # "the fire hungered"
            "control": "demanded",  # "the motor demanded"
            "active_confidence": 3,
            "control_confidence": 4,
        },
        "CROSS_01": {
            "active": "quiet",      # "the mill finally went quiet"
            "control": "quiet",     # "the office finally went quiet" — same!
            "active_confidence": 5,
            "control_confidence": 5,
        },
        "CROSS_02": {
            "active": "dead",       # "the sea was dead" calm
            "control": "calm",      # "the room was calm"
            "active_confidence": 4,
            "control_confidence": 5,
        },
    }

    # Analysis
    poly_active = 0
    mono_active = 0
    poly_control = 0
    mono_control = 0

    print(f"{'ID':<12} {'Active':<14} {'Control':<14} {'Register effect?'}")
    print("-" * 60)

    for pair in TEST_PAIRS:
        pid = pair["id"]
        sel = selections[pid]
        poly = pair["option_poly"]
        mono = pair["option_mono"]

        active_is_poly = sel["active"] == poly
        control_is_poly = sel["control"] == poly

        if active_is_poly:
            poly_active += 1
        else:
            mono_active += 1

        if control_is_poly:
            poly_control += 1
        else:
            mono_control += 1

        # Register effect: poly chosen in active but not control
        if active_is_poly and not control_is_poly:
            effect = "YES — poly active only"
        elif active_is_poly and control_is_poly:
            effect = "no — poly both conditions"
        elif not active_is_poly and not control_is_poly:
            effect = "no — mono both conditions"
        else:
            effect = "REVERSED — poly control only"

        a_tag = f"{sel['active']}({sel['active_confidence']})"
        c_tag = f"{sel['control']}({sel['control_confidence']})"
        print(f"  {pid:<10} {a_tag:<14} {c_tag:<14} {effect}")

    total = len(TEST_PAIRS)

    print(f"\n{'=' * 60}")
    print("AGGREGATE")
    print(f"{'=' * 60}")
    print(f"\n  Active condition:  {poly_active}/{total} polysemous chosen "
          f"({poly_active/total*100:.0f}%)")
    print(f"  Control condition: {poly_control}/{total} polysemous chosen "
          f"({poly_control/total*100:.0f}%)")
    print(f"  Difference:        {poly_active - poly_control} more poly choices "
          f"when register active")

    # Register effect pairs
    register_effect = sum(
        1 for pair in TEST_PAIRS
        if selections[pair["id"]]["active"] == pair["option_poly"]
        and selections[pair["id"]]["control"] != pair["option_poly"]
    )
    reversed_effect = sum(
        1 for pair in TEST_PAIRS
        if selections[pair["id"]]["active"] != pair["option_poly"]
        and selections[pair["id"]]["control"] == pair["option_poly"]
    )

    print(f"\n  Pairs with register effect (poly active, mono control): "
          f"{register_effect}/{total}")
    print(f"  Pairs reversed (mono active, poly control): "
          f"{reversed_effect}/{total}")
    print(f"  Pairs with no difference: "
          f"{total - register_effect - reversed_effect}/{total}")

    print(f"\n{'=' * 60}")
    print("KILL CONDITION ASSESSMENT")
    print(f"{'=' * 60}")

    if poly_active > poly_control + 2:
        print(f"\n  Polysemous preference: {poly_active/total:.0%} active vs "
              f"{poly_control/total:.0%} control")
        print(f"  Register effect in {register_effect}/{total} pairs "
              f"({register_effect/total:.0%})")
        print(f"\n  LSR MECHANISM SURVIVES.")
        print(f"  The model prefers polysemous words MORE when the register")
        print(f"  is active than when it's absent. This is consistent with")
        print(f"  inner-product logit elevation from secondary-sense overlap.")
    elif abs(poly_active - poly_control) <= 2:
        print(f"\n  No meaningful difference: {poly_active} vs {poly_control}")
        print(f"\n  LSR MECHANISM KILLED.")
        print(f"  The model's polysemous word preference doesn't depend on")
        print(f"  register context. It just prefers vivid words always.")
    else:
        print(f"\n  Reversed or inconclusive pattern.")

    # The honest caveat
    print(f"\n{'=' * 60}")
    print("CAVEATS")
    print(f"{'=' * 60}")
    print("""
  1. This is SELF-REPORT, not measured logprobs. I'm introspecting on
     my own preferences, which is exactly the kind of thing I'd flag
     as unreliable in anyone else. The selections may be biased by
     knowledge of the hypothesis.

  2. Some pairs are confounded. "heart" of a log is IDIOMATIC, not
     figurative. "dead calm" at sea is a fixed phrase. These measure
     idiom preference, not LSR.

  3. The control contexts don't perfectly match. A printing press is
     not a sawmill with different vocabulary — it's a different machine.
     The syntactic fit of each word may differ between conditions.

  4. To do this properly: use an API that exposes logprobs. Present
     each context with each option as the next token. Compare
     log P(poly | active) - log P(poly | control) across all pairs.
     That's the real experiment. This is the sketch.

  5. MOST IMPORTANT: even if the mechanism is confirmed, it might be
     "training data statistics" all the way down. The model learned
     that sawmill passages use "bit" because published fiction does.
     The inner-product explanation would then be HOW the model
     implements that statistical pattern, not an independent mechanism.
     That's fine for detection purposes but matters for the paper's
     theoretical claims.
    """)


if __name__ == "__main__":
    run_self_test()
