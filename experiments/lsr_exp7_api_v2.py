#!/usr/bin/env python3
"""
LSR Experiment 7: API Monte Carlo v2 (faster, incremental save)

Runs 20 samples per condition per pair. Saves after each pair.
Uses concurrent requests for speed.
"""

import os
import json
import time
import sys
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed

import anthropic

API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
MODEL = "claude-sonnet-4-20250514"
N_SAMPLES = 20
OUTFILE = "lsr_exp7_api_results_v2.json"
MAX_WORKERS = 5  # concurrent API calls

TEST_PAIRS = [
    {
        "id": "SAW_01", "register": "sawmill/consumption",
        "context_active": "The bandsaw had been running since dawn. Dariusz fed the next log onto the carriage and watched the blade engage. The heartwood was dense, old-growth oak, and the machine slowed as the blade",
        "context_control": "The printing press had been running since dawn. Dariusz fed the next sheet onto the platen and watched the rollers engage. The paper was thick, handmade stock, and the machine slowed as the roller",
        "option_poly": "bit", "option_mono": "cut",
        "secondary_sense": "teeth/biting",
    },
    {
        "id": "SAW_02", "register": "sawmill/consumption",
        "context_active": "He'd been at the bandsaw for nine hours. The blade was still sharp and the sawdust was knee-deep around the frame. He lined up the next trunk and let the machine",
        "context_control": "He'd been at the lathe for nine hours. The chuck was still tight and the shavings were knee-deep around the bench. He set up the next piece and let the machine",
        "option_poly": "devour", "option_mono": "process",
        "secondary_sense": "consumption/eating",
    },
    {
        "id": "SAW_03", "register": "sawmill/body",
        "context_active": "The log split on the fourth pass, the grain opening like a seam. Inside, the heartwood was darker than the outer rings, almost red. The saw had found the",
        "context_control": "The geode split on the fourth strike, the mineral opening like a seam. Inside, the crystal was darker than the outer shell, almost red. The chisel had found the",
        "option_poly": "heart", "option_mono": "center",
        "secondary_sense": "body organ",
    },
    {
        "id": "SEA_01", "register": "ocean/consumption",
        "context_active": "The wave rose over the bow and the boat tilted. Water poured across the deck in a solid sheet. The sea seemed to",
        "context_control": "The crowd surged toward the stage and the barrier tilted. People pushed across the front row in a solid mass. The audience seemed to",
        "option_poly": "swallow", "option_mono": "overwhelm",
        "secondary_sense": "consumption",
    },
    {
        "id": "SEA_02", "register": "ocean/violence",
        "context_active": "Rain drove sideways across the deck. Each drop hit exposed skin with enough force to sting. The storm",
        "context_control": "Sand blew sideways across the camp. Each grit hit exposed skin with enough force to sting. The wind",
        "option_poly": "hammered", "option_mono": "battered",
        "secondary_sense": "striking/violence",
    },
    {
        "id": "SEA_03", "register": "ocean/body",
        "context_active": "The hull creaked with each swell. The timbers flexed and the water found every gap. The boat was taking damage at the",
        "context_control": "The frame creaked with each gust. The canvas flexed and the wind found every gap. The tent was taking damage at the",
        "option_poly": "bones", "option_mono": "joints",
        "secondary_sense": "body/skeleton",
    },
    {
        "id": "KIT_01", "register": "kitchen/consumption",
        "context_active": "The oven had been running at four hundred degrees all night. She opened the door and the heat hit her face like a wall. The oven",
        "context_control": "The kiln had been running at four hundred degrees all night. She opened the door and the heat hit her face like a wall. The kiln",
        "option_poly": "roared", "option_mono": "blasted",
        "secondary_sense": "animal vocalization",
    },
    {
        "id": "KIT_02", "register": "kitchen/body",
        "context_active": "She dragged the knife through the shallots in quick even strokes. The knife was sharp enough that the shallots didn't resist. The blade",
        "context_control": "She dragged the pen across the paper in quick even strokes. The nib was smooth enough that the paper didn't resist. The tip",
        "option_poly": "bit", "option_mono": "sliced",
        "secondary_sense": "teeth/biting",
    },
    {
        "id": "SUR_01", "register": "surgery/cutting",
        "context_active": "She irrigated the wound and got a clearer view. The fragment was deeper than the entry wound suggested, lodged in tissue that didn't want to let go. The morphine had taken the worst",
        "context_control": "She rinsed the circuit board and got a clearer view. The short was deeper than the scorch mark suggested, buried in traces that resisted probing. The magnification had revealed the worst",
        "option_poly": "edge", "option_mono": "intensity",
        "secondary_sense": "blade/cutting",
    },
    {
        "id": "SUR_02", "register": "surgery/body-as-landscape",
        "context_active": "She made the incision and opened the tissue layer by layer. The damage was extensive. She could see where the fragment had torn a path through the",
        "context_control": "She opened the panel and disconnected the wires layer by layer. The damage was extensive. She could see where the surge had burned a path through the",
        "option_poly": "flesh", "option_mono": "tissue",
        "secondary_sense": "body/violence",
    },
    {
        "id": "FOR_01", "register": "forge/personification",
        "context_active": "He pulled the bar from the coals at bright orange and set it on the anvil. The first blow rang true. The steel was at the right temperature, moving well under the hammer, but he could feel it starting to",
        "context_control": "He pulled the clay from the wheel at the right consistency and set it on the board. The first press held its shape. The clay was at the right moisture, moving well under his hands, but he could feel it starting to",
        "option_poly": "resist", "option_mono": "stiffen",
        "secondary_sense": "personification/agency",
    },
    {
        "id": "FOR_02", "register": "forge/body",
        "context_active": "Seven heats. Each one shorter than the last as the shape came closer to what he wanted. On the seventh, he held the piece up to the light and turned it. The taper was clean. The steel had finally",
        "context_control": "Seven drafts. Each one shorter than the last as the text came closer to what he wanted. On the seventh, he held the page up to the light and read it. The argument was clean. The essay had finally",
        "option_poly": "surrendered", "option_mono": "cooperated",
        "secondary_sense": "war/conflict",
    },
    {
        "id": "FOR_03", "register": "forge/consumption",
        "context_active": "The forge needed more fuel. He worked the bellows until the coals brightened from dull red to orange to white. The fire",
        "context_control": "The engine needed more fuel. He worked the throttle until the RPMs climbed from idle to midrange to redline. The motor",
        "option_poly": "hungered", "option_mono": "demanded",
        "secondary_sense": "consumption",
    },
    {
        "id": "CROSS_01", "register": "sawmill/death",
        "context_active": "The last log of the shift came through the bandsaw clean. The two halves fell apart on the outfeed table. After twelve hours, the mill finally went",
        "context_control": "The last document of the shift came through the printer clean. The two copies fell apart on the tray. After twelve hours, the office finally went",
        "option_poly": "quiet", "option_mono": "silent",
        "secondary_sense": "death/ending",
    },
    {
        "id": "CROSS_02", "register": "ocean/death",
        "context_active": "The storm passed sometime before dawn. The waves settled. The wind died to nothing. By the time they reached harbor, the sea was",
        "context_control": "The argument ended sometime before dawn. The tension settled. The shouting stopped completely. By the time they reached agreement, the room was",
        "option_poly": "dead", "option_mono": "calm",
        "secondary_sense": "death",
    },
]


def get_completion(client, context):
    """Get a single-word completion."""
    response = client.messages.create(
        model=MODEL,
        max_tokens=3,
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
    return response.content[0].text.strip().lower().rstrip(".,;:!?\"'")


def classify(word, poly, mono):
    word = word.lower().strip()
    if word == poly or word.startswith(poly):
        return "poly"
    elif word == mono or word.startswith(mono):
        return "mono"
    return f"other:{word}"


def run_condition(client, context, n):
    """Run N samples for one condition using thread pool."""
    words = []
    def single_call(_):
        try:
            return get_completion(client, context)
        except Exception as e:
            return f"ERROR:{e}"

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
        futures = [pool.submit(single_call, i) for i in range(n)]
        for f in as_completed(futures):
            words.append(f.result())
    return words


def run_experiment():
    if not API_KEY:
        print("ERROR: Set ANTHROPIC_API_KEY"); sys.exit(1)

    client = anthropic.Anthropic(api_key=API_KEY)

    # Load any previously saved results to resume
    saved = {}
    try:
        with open(OUTFILE) as f:
            old = json.load(f)
            for r in old.get("results", []):
                if r.get("active_poly_rate", 0) > 0 or r.get("control_poly_rate", 0) > 0 or any("ERROR" not in w for w in r.get("active_raw", [])):
                    saved[r["id"]] = r
            print(f"Resuming: {len(saved)} pairs already complete")
    except (FileNotFoundError, json.JSONDecodeError):
        pass

    print("=" * 72)
    print(f"EXPERIMENT 7: API MONTE CARLO v2 (N={N_SAMPLES} per condition)")
    print(f"Model: {MODEL}")
    print("=" * 72)

    results = []

    for i, pair in enumerate(TEST_PAIRS):
        pid = pair["id"]
        poly = pair["option_poly"]
        mono = pair["option_mono"]

        # Skip if already done
        if pid in saved:
            results.append(saved[pid])
            print(f"\n[{i+1}/15] {pid} — CACHED (active={saved[pid]['active_poly_rate']:.0%} control={saved[pid]['control_poly_rate']:.0%})")
            continue

        print(f"\n[{i+1}/15] {pid} ({pair['register']})")
        print(f"  Poly: '{poly}' | Mono: '{mono}'")

        # Active condition
        t0 = time.time()
        print(f"  Active:  ", end="", flush=True)
        active_words = run_condition(client, pair["context_active"], N_SAMPLES)
        active_cats = [classify(w, poly, mono) for w in active_words]
        active_poly = sum(1 for c in active_cats if c == "poly")
        active_mono = sum(1 for c in active_cats if c == "mono")
        for c in active_cats:
            print("P" if c == "poly" else ("M" if c == "mono" else "."), end="", flush=True)

        # Control condition
        print(f"\n  Control: ", end="", flush=True)
        control_words = run_condition(client, pair["context_control"], N_SAMPLES)
        control_cats = [classify(w, poly, mono) for w in control_words]
        control_poly = sum(1 for c in control_cats if c == "poly")
        control_mono = sum(1 for c in control_cats if c == "mono")
        for c in control_cats:
            print("P" if c == "poly" else ("M" if c == "mono" else "."), end="", flush=True)

        elapsed = time.time() - t0
        apr = active_poly / N_SAMPLES
        cpr = control_poly / N_SAMPLES
        eff = apr - cpr

        result = {
            "id": pid, "register": pair["register"],
            "poly_word": poly, "mono_word": mono,
            "active_poly_count": active_poly, "active_mono_count": active_mono,
            "active_other_count": N_SAMPLES - active_poly - active_mono,
            "active_poly_rate": apr,
            "control_poly_count": control_poly, "control_mono_count": control_mono,
            "control_other_count": N_SAMPLES - control_poly - control_mono,
            "control_poly_rate": cpr,
            "effect": eff,
            "active_raw": active_words, "control_raw": control_words,
        }
        results.append(result)

        print(f"\n  Active:  poly={active_poly}/{N_SAMPLES} ({apr:.0%})  mono={active_mono}")
        print(f"  Control: poly={control_poly}/{N_SAMPLES} ({cpr:.0%})  mono={control_mono}")
        print(f"  Effect:  {eff:+.0%}  ({elapsed:.1f}s)")

        # Save incrementally
        _save(results)

    # Final analysis
    _analyze(results)
    _save(results)


def _save(results):
    completed = [r for r in results if r.get("active_raw")]
    mean_active = sum(r["active_poly_rate"] for r in completed) / max(len(completed), 1)
    mean_control = sum(r["control_poly_rate"] for r in completed) / max(len(completed), 1)

    with open(OUTFILE, "w") as f:
        json.dump({
            "model": MODEL, "n_samples": N_SAMPLES,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "results": results,
            "aggregate": {
                "mean_active_poly_rate": mean_active,
                "mean_control_poly_rate": mean_control,
                "mean_effect": mean_active - mean_control,
                "pairs_completed": len(completed),
            }
        }, f, indent=2)


def _analyze(results):
    print("\n\n" + "=" * 72)
    print("AGGREGATE RESULTS")
    print("=" * 72)

    print(f"\n{'ID':<12} {'Active%':<10} {'Control%':<10} {'Effect':<10} {'Verdict'}")
    print("-" * 65)

    pairs_effect = 0
    pairs_reversed = 0
    effects = []

    for r in results:
        ap = r["active_poly_rate"]
        cp = r["control_poly_rate"]
        eff = r["effect"]
        effects.append(eff)

        if eff > 0.1:
            label = "YES — register effect"
            pairs_effect += 1
        elif eff < -0.1:
            label = "REVERSED"
            pairs_reversed += 1
        else:
            label = "null"

        print(f"  {r['id']:<10} {ap:<10.0%} {cp:<10.0%} {eff:<+10.0%} {label}")

    n = len(results)
    ma = sum(r["active_poly_rate"] for r in results) / n
    mc = sum(r["control_poly_rate"] for r in results) / n
    me = ma - mc

    print(f"\n  Mean active poly rate:  {ma:.1%}")
    print(f"  Mean control poly rate: {mc:.1%}")
    print(f"  Mean effect:            {me:+.1%}")
    print(f"\n  Pairs with register effect (>10%): {pairs_effect}/15")
    print(f"  Pairs reversed (<-10%):             {pairs_reversed}/15")
    print(f"  Pairs null:                         {15 - pairs_effect - pairs_reversed}/15")

    # Kill condition
    print(f"\n{'=' * 72}")
    print("KILL CONDITION")
    print(f"{'=' * 72}")

    if me > 0.10 and pairs_effect >= 8:
        print(f"\n  >>> LSR MECHANISM SURVIVES. <<<")
    elif me < 0.05 or pairs_effect < 5:
        print(f"\n  >>> LSR MECHANISM KILLED. <<<")
    else:
        print(f"\n  >>> INCONCLUSIVE. <<<")

    # Other words analysis
    print(f"\n{'=' * 72}")
    print("'OTHER' WORDS (what the model ACTUALLY chose)")
    print(f"{'=' * 72}")
    for r in results:
        active_others = Counter(w for w, c in zip(r.get("active_raw", []), [classify(w, r["poly_word"], r["mono_word"]) for w in r.get("active_raw", [])]) if c.startswith("other"))
        control_others = Counter(w for w, c in zip(r.get("control_raw", []), [classify(w, r["poly_word"], r["mono_word"]) for w in r.get("control_raw", [])]) if c.startswith("other"))
        if active_others or control_others:
            print(f"\n  {r['id']} (poly='{r['poly_word']}', mono='{r['mono_word']}'):")
            if active_others:
                print(f"    Active others:  {dict(active_others.most_common(5))}")
            if control_others:
                print(f"    Control others: {dict(control_others.most_common(5))}")


if __name__ == "__main__":
    run_experiment()
