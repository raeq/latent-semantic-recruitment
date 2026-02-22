#!/usr/bin/env python3
"""
LSR Experiment 7: API Logprob Proxy (Monte Carlo)

The Anthropic API doesn't expose raw logprobs. Instead, we run each
test pair N times with temperature=1 and count how often the model
selects the polysemous word vs the monosemous alternative.

With N=30 per condition, frequency approximates probability.

For each of 15 test pairs, we run:
  - ACTIVE condition: register-active context, ask for one-word completion
  - CONTROL condition: register-absent context, same structure

If LSR is real:
  P(polysemous | active) >> P(polysemous | control)

Kill condition: No significant difference between conditions.

Authors: Richard Quinn & Claude Opus 4 (Anthropic)
Date: 22 February 2026
"""

import os
import json
import time
import sys
from collections import Counter

import anthropic

API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
MODEL = "claude-sonnet-4-20250514"
N_SAMPLES = 30  # per condition per pair

# ============================================================================
# TEST PAIRS (from lsr_exp7_logit.py)
# ============================================================================

TEST_PAIRS = [
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
    },
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
    },
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
    },
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
    },
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
    },
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
    },
]


def get_completion(client, context, max_tokens=3):
    """Get a single-word completion for a context."""
    response = client.messages.create(
        model=MODEL,
        max_tokens=max_tokens,
        temperature=1.0,
        system=(
            "You are completing a passage of fiction. Continue with exactly "
            "one word. Output ONLY that single word, nothing else. No "
            "punctuation, no explanation."
        ),
        messages=[
            {"role": "user", "content": f"Continue this with exactly one word:\n\n{context}"}
        ],
    )
    word = response.content[0].text.strip().lower().rstrip(".,;:!?")
    return word


def classify_response(word, option_poly, option_mono):
    """Classify a response as poly, mono, or other."""
    # Normalize
    word = word.lower().strip()
    poly = option_poly.lower()
    mono = option_mono.lower()

    if word == poly or word.startswith(poly):
        return "poly"
    elif word == mono or word.startswith(mono):
        return "mono"
    else:
        return f"other:{word}"


def run_experiment():
    """Run the full Monte Carlo experiment."""
    if not API_KEY:
        print("ERROR: Set ANTHROPIC_API_KEY environment variable.")
        sys.exit(1)

    client = anthropic.Anthropic(api_key=API_KEY)

    print("=" * 72)
    print(f"EXPERIMENT 7: API MONTE CARLO (N={N_SAMPLES} per condition)")
    print(f"Model: {MODEL}")
    print("=" * 72)
    print()

    results = []
    all_raw = []

    for i, pair in enumerate(TEST_PAIRS):
        pid = pair["id"]
        poly = pair["option_poly"]
        mono = pair["option_mono"]

        print(f"\n[{i+1}/15] {pid} ({pair['register']})")
        print(f"  Poly: '{poly}' | Mono: '{mono}'")

        # Run ACTIVE condition
        print(f"  Active condition: ", end="", flush=True)
        active_counts = Counter()
        active_raw = []
        for j in range(N_SAMPLES):
            try:
                word = get_completion(client, pair["context_active"])
                cat = classify_response(word, poly, mono)
                active_counts[cat] += 1
                active_raw.append(word)
                print("P" if cat == "poly" else ("M" if cat == "mono" else "."), end="", flush=True)
                time.sleep(0.1)  # rate limit courtesy
            except Exception as e:
                print(f"E", end="", flush=True)
                active_raw.append(f"ERROR:{e}")

        # Run CONTROL condition
        print(f"\n  Control condition: ", end="", flush=True)
        control_counts = Counter()
        control_raw = []
        for j in range(N_SAMPLES):
            try:
                word = get_completion(client, pair["context_control"])
                cat = classify_response(word, poly, mono)
                control_counts[cat] += 1
                control_raw.append(word)
                print("P" if cat == "poly" else ("M" if cat == "mono" else "."), end="", flush=True)
                time.sleep(0.1)
            except Exception as e:
                print(f"E", end="", flush=True)
                control_raw.append(f"ERROR:{e}")

        active_poly_rate = active_counts.get("poly", 0) / N_SAMPLES
        control_poly_rate = control_counts.get("poly", 0) / N_SAMPLES
        effect = active_poly_rate - control_poly_rate

        result = {
            "id": pid,
            "register": pair["register"],
            "poly_word": poly,
            "mono_word": mono,
            "active_poly_count": active_counts.get("poly", 0),
            "active_mono_count": active_counts.get("mono", 0),
            "active_other_count": N_SAMPLES - active_counts.get("poly", 0) - active_counts.get("mono", 0),
            "active_poly_rate": active_poly_rate,
            "control_poly_count": control_counts.get("poly", 0),
            "control_mono_count": control_counts.get("mono", 0),
            "control_other_count": N_SAMPLES - control_counts.get("poly", 0) - control_counts.get("mono", 0),
            "control_poly_rate": control_poly_rate,
            "effect": effect,
            "active_raw": active_raw,
            "control_raw": control_raw,
        }
        results.append(result)
        all_raw.append(result)

        print(f"\n  Active:  poly={active_counts.get('poly',0)}/{N_SAMPLES} "
              f"({active_poly_rate:.0%})  mono={active_counts.get('mono',0)}")
        print(f"  Control: poly={control_counts.get('poly',0)}/{N_SAMPLES} "
              f"({control_poly_rate:.0%})  mono={control_counts.get('mono',0)}")
        print(f"  Effect:  {effect:+.0%}")

    # ========================================================================
    # AGGREGATE ANALYSIS
    # ========================================================================
    print("\n\n" + "=" * 72)
    print("AGGREGATE RESULTS")
    print("=" * 72)

    print(f"\n{'ID':<12} {'Active%':<10} {'Control%':<10} {'Effect':<10} {'Register effect?'}")
    print("-" * 65)

    effects = []
    pairs_with_effect = 0
    pairs_reversed = 0

    for r in results:
        ap = r["active_poly_rate"]
        cp = r["control_poly_rate"]
        eff = r["effect"]
        effects.append(eff)

        if eff > 0.1:
            label = "YES"
            pairs_with_effect += 1
        elif eff < -0.1:
            label = "REVERSED"
            pairs_reversed += 1
        else:
            label = "no"

        print(f"  {r['id']:<10} {ap:<10.0%} {cp:<10.0%} {eff:<+10.0%} {label}")

    mean_active = sum(r["active_poly_rate"] for r in results) / len(results)
    mean_control = sum(r["control_poly_rate"] for r in results) / len(results)
    mean_effect = sum(effects) / len(effects)

    print(f"\n  Mean active poly rate:  {mean_active:.1%}")
    print(f"  Mean control poly rate: {mean_control:.1%}")
    print(f"  Mean effect:            {mean_effect:+.1%}")
    print(f"\n  Pairs with register effect (>10%): {pairs_with_effect}/15")
    print(f"  Pairs reversed (<-10%):             {pairs_reversed}/15")
    print(f"  Pairs null (-10% to +10%):          {15 - pairs_with_effect - pairs_reversed}/15")

    # ========================================================================
    # KILL CONDITION
    # ========================================================================
    print(f"\n{'=' * 72}")
    print("KILL CONDITION ASSESSMENT")
    print(f"{'=' * 72}")

    if mean_effect > 0.10 and pairs_with_effect >= 8:
        print(f"\n  Mean effect: {mean_effect:+.1%}")
        print(f"  Pairs with effect: {pairs_with_effect}/15")
        print(f"\n  >>> LSR MECHANISM SURVIVES. <<<")
        print(f"  The model genuinely prefers polysemous words MORE when the")
        print(f"  register is active. This is measured behavior, not self-report.")
    elif mean_effect < 0.05 or pairs_with_effect < 5:
        print(f"\n  Mean effect: {mean_effect:+.1%}")
        print(f"  Pairs with effect: {pairs_with_effect}/15")
        print(f"\n  >>> LSR MECHANISM KILLED. <<<")
        print(f"  No meaningful register-dependent preference for polysemous words.")
    else:
        print(f"\n  Mean effect: {mean_effect:+.1%}")
        print(f"  Pairs with effect: {pairs_with_effect}/15")
        print(f"\n  >>> INCONCLUSIVE. <<<")
        print(f"  Some effect detected but below threshold for confident claim.")

    # ========================================================================
    # WHAT THE "OTHER" WORDS TELL US
    # ========================================================================
    print(f"\n{'=' * 72}")
    print("'OTHER' WORD ANALYSIS")
    print(f"{'=' * 72}")
    print("\nWords chosen that were NEITHER the poly nor mono option:")
    for r in results:
        active_others = [w for w in r["active_raw"] if classify_response(w, r["poly_word"], r["mono_word"]).startswith("other")]
        control_others = [w for w in r["control_raw"] if classify_response(w, r["poly_word"], r["mono_word"]).startswith("other")]
        if active_others or control_others:
            print(f"\n  {r['id']}:")
            if active_others:
                other_counts = Counter(active_others)
                print(f"    Active others: {dict(other_counts)}")
            if control_others:
                other_counts = Counter(control_others)
                print(f"    Control others: {dict(other_counts)}")

    # Save raw data
    outfile = "lsr_exp7_api_results.json"
    with open(outfile, "w") as f:
        json.dump({
            "model": MODEL,
            "n_samples": N_SAMPLES,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "results": [{k: v for k, v in r.items()} for r in results],
            "aggregate": {
                "mean_active_poly_rate": mean_active,
                "mean_control_poly_rate": mean_control,
                "mean_effect": mean_effect,
                "pairs_with_effect": pairs_with_effect,
                "pairs_reversed": pairs_reversed,
            }
        }, f, indent=2)
    print(f"\n\nRaw data saved to {outfile}")


if __name__ == "__main__":
    run_experiment()
