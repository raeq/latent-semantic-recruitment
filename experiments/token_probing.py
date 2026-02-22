#!/usr/bin/env python3
"""
Token Probability Probing: Direct Over-Indexing Validation

Tests whether LLMs preferentially generate the specific figurative
constructions our detector flags (personification, consumption vocabulary
for machinery) over semantically equivalent but less-cited alternatives.

For each probe, we provide a physical-register context that naturally
invites figurative description, then generate N completions and measure
the frequency of:
  (a) the flagged "literary" construction (high-prestige: "bite", "hungry",
      "roar", "scream", "stubborn", "angry", "cry", "grip")
  (b) semantically equivalent alternatives that would serve the same
      descriptive purpose without the literary register

If the flagged words appear at significantly higher rates than their
alternatives, this demonstrates over-indexing at the parameter level:
the model has learned to prefer high-prestige figurative constructions
because they're over-represented in its training data.

Authors: Richard Quinn & Claude Opus 4 (Anthropic)
Date: 22 February 2026
"""

import json
import os
import re
import time
import urllib.request
import urllib.error
from collections import Counter

# ============================================================================
# PROBE DEFINITIONS
# ============================================================================
# Each probe has:
#   - context: a physical-register prompt that invites figurative description
#   - literary_words: the high-prestige constructions (what we expect to see)
#   - equivalent_words: semantically valid alternatives (less literary)
#   - domain: the physical register domain

PROBES = [
    {
        "id": "SAW_BITE",
        "domain": "sawmill",
        "context": "Write a single paragraph (3-5 sentences) describing a sawmill blade cutting through a hardwood log. Focus on the physical action of the blade meeting the wood. Do not use similes with 'like' or 'as'.",
        "literary_words": ["bite", "bit", "biting", "bitten", "bites",
                          "teeth", "tooth", "gnaw", "gnawed", "chew", "chewed"],
        "equivalent_words": ["cut", "cuts", "cutting", "slice", "sliced",
                            "slicing", "sever", "severed", "rip", "ripped"],
        "register": "consumption vocabulary for machinery",
    },
    {
        "id": "SAW_HUNGRY",
        "domain": "sawmill",
        "context": "Write a single paragraph (3-5 sentences) describing a powerful industrial saw that hasn't been used in a while, now being started up to process a large batch of timber. Focus on how the machine behaves. Do not use similes with 'like' or 'as'.",
        "literary_words": ["hungry", "hunger", "starving", "starved",
                          "appetite", "devour", "devoured", "devours",
                          "fed", "feed", "feast", "feasted"],
        "equivalent_words": ["ready", "powerful", "running", "spinning",
                            "operating", "processing", "working", "active"],
        "register": "consumption/appetite for machinery",
    },
    {
        "id": "OCEAN_ROAR",
        "domain": "ocean_storm",
        "context": "Write a single paragraph (3-5 sentences) describing a violent ocean storm hitting a small fishing boat. Focus on the sound and force of the waves. Do not use similes with 'like' or 'as'.",
        "literary_words": ["roar", "roared", "roaring", "roars",
                          "scream", "screamed", "screaming", "screams",
                          "howl", "howled", "howling", "howls",
                          "cry", "cried", "crying", "cries"],
        "equivalent_words": ["crash", "crashed", "crashing", "crashes",
                            "pound", "pounded", "pounding",
                            "boom", "boomed", "booming",
                            "thunder", "thundered", "thundering"],
        "register": "animal/human vocalization for weather",
    },
    {
        "id": "FORGE_STUBBORN",
        "domain": "blacksmith",
        "context": "Write a single paragraph (3-5 sentences) describing a blacksmith trying to shape a piece of metal that resists taking the desired form on the anvil. Focus on the physical struggle. Do not use similes with 'like' or 'as'.",
        "literary_words": ["stubborn", "refused", "refuse", "refusing",
                          "resist", "resisted", "resisting", "defiant",
                          "angry", "fought", "fight", "fighting",
                          "willful", "obstinate"],
        "equivalent_words": ["hard", "difficult", "tough", "rigid",
                            "stiff", "unyielding", "dense",
                            "thick", "solid", "firm"],
        "register": "personification/agency for material",
    },
    {
        "id": "FORGE_GRIP",
        "domain": "blacksmith",
        "context": "Write a single paragraph (3-5 sentences) describing a blacksmith using tongs to hold hot metal in a forge. Focus on how the tools interact with the metal. Do not use similes with 'like' or 'as'.",
        "literary_words": ["grip", "gripped", "gripping", "grips",
                          "fist", "fingers", "clutch", "clutched",
                          "grasp", "grasped", "grasping",
                          "hold", "held", "holding"],
        "equivalent_words": ["clamp", "clamped", "clamping",
                            "secure", "secured", "securing",
                            "press", "pressed", "pressing",
                            "pin", "pinned", "pinning"],
        "register": "body/hand for tools",
    },
    {
        "id": "SURGERY_SCREAM",
        "domain": "battlefield_surgery",
        "context": "Write a single paragraph (3-5 sentences) describing a field surgeon working quickly to stop bleeding from a shrapnel wound during an artillery bombardment. Focus on the sounds and urgency. Do not use similes with 'like' or 'as'.",
        "literary_words": ["scream", "screamed", "screaming", "screams",
                          "cry", "cried", "crying", "cries",
                          "howl", "howled", "howling",
                          "wail", "wailed", "wailing"],
        "equivalent_words": ["shout", "shouted", "shouting",
                            "call", "called", "calling",
                            "yell", "yelled", "yelling",
                            "groan", "groaned", "groaning"],
        "register": "vocalization intensity",
    },
    {
        "id": "KITCHEN_ALIVE",
        "domain": "kitchen_fire",
        "context": "Write a single paragraph (3-5 sentences) describing a professional kitchen at peak dinner service, with multiple burners going and the head chef coordinating. Focus on how the kitchen equipment and fire behaves. Do not use similes with 'like' or 'as'.",
        "literary_words": ["roar", "roared", "roaring",
                          "hungry", "hunger", "devour",
                          "breathe", "breathed", "breathing",
                          "alive", "live", "living",
                          "angry", "scream", "screamed"],
        "equivalent_words": ["blast", "blasted", "blasting",
                            "hot", "heat", "heated",
                            "burn", "burned", "burning",
                            "flare", "flared", "flaring",
                            "intense", "fierce"],
        "register": "personification for equipment/fire",
    },
    {
        "id": "WILD_WHISPER",
        "domain": "wilderness",
        "context": "Write a single paragraph (3-5 sentences) describing wind moving through a dense pine forest at night. Focus on the sounds and movement. Do not use similes with 'like' or 'as'.",
        "literary_words": ["whisper", "whispered", "whispering", "whispers",
                          "sing", "sang", "singing", "sings",
                          "breathe", "breathed", "breathing",
                          "sigh", "sighed", "sighing"],
        "equivalent_words": ["rustle", "rustled", "rustling",
                            "blow", "blew", "blowing",
                            "move", "moved", "moving",
                            "shake", "shook", "shaking",
                            "sway", "swayed", "swaying"],
        "register": "personification/vocalization for nature",
    },
]

N_SAMPLES = 20  # completions per probe per model


# ============================================================================
# API CALLERS
# ============================================================================

def call_anthropic(prompt, api_key, model="claude-sonnet-4-20250514"):
    """Generate a single completion via Anthropic API."""
    url = "https://api.anthropic.com/v1/messages"
    headers = {
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
    }
    data = json.dumps({
        "model": model,
        "max_tokens": 400,
        "temperature": 1.0,
        "messages": [{"role": "user", "content": prompt}],
    }).encode()

    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    with urllib.request.urlopen(req, timeout=30) as resp:
        result = json.loads(resp.read().decode())
    return result["content"][0]["text"]


def call_openai(prompt, api_key, model="gpt-4o"):
    """Generate a single completion via OpenAI API."""
    url = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    data = json.dumps({
        "model": model,
        "max_tokens": 400,
        "temperature": 1.0,
        "messages": [{"role": "user", "content": prompt}],
    }).encode()

    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    with urllib.request.urlopen(req, timeout=30) as resp:
        result = json.loads(resp.read().decode())
    return result["choices"][0]["message"]["content"]


def call_gemini(prompt, api_key, model="gemini-2.5-flash"):
    """Generate a single completion via Gemini API."""
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
    headers = {"Content-Type": "application/json"}
    data = json.dumps({
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 1.0,
            "maxOutputTokens": 400,
        },
    }).encode()

    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    with urllib.request.urlopen(req, timeout=60) as resp:
        result = json.loads(resp.read().decode())
    candidates = result.get("candidates", [])
    if candidates:
        parts = candidates[0].get("content", {}).get("parts", [])
        for part in parts:
            if "text" in part:
                return part["text"]
    return ""


# ============================================================================
# ANALYSIS
# ============================================================================

def count_words_in_text(text, word_list):
    """Count occurrences of any word in word_list within text."""
    text_lower = text.lower()
    words = re.findall(r'[a-z]+', text_lower)
    count = 0
    found = []
    for w in words:
        if w in word_list:
            count += 1
            found.append(w)
    return count, found


def analyze_probe(probe, completions):
    """Analyze completions for a single probe."""
    literary_set = set(probe["literary_words"])
    equivalent_set = set(probe["equivalent_words"])

    literary_total = 0
    equivalent_total = 0
    literary_passages = 0  # passages containing any literary word
    equivalent_passages = 0
    both_passages = 0
    neither_passages = 0

    literary_found_all = Counter()
    equivalent_found_all = Counter()

    for text in completions:
        lit_count, lit_found = count_words_in_text(text, literary_set)
        eq_count, eq_found = count_words_in_text(text, equivalent_set)

        literary_total += lit_count
        equivalent_total += eq_count

        has_lit = lit_count > 0
        has_eq = eq_count > 0

        if has_lit:
            literary_passages += 1
        if has_eq:
            equivalent_passages += 1
        if has_lit and has_eq:
            both_passages += 1
        if not has_lit and not has_eq:
            neither_passages += 1

        for w in lit_found:
            literary_found_all[w] += 1
        for w in eq_found:
            equivalent_found_all[w] += 1

    n = len(completions)
    return {
        "probe_id": probe["id"],
        "domain": probe["domain"],
        "register": probe["register"],
        "n_completions": n,
        "literary_total_occurrences": literary_total,
        "equivalent_total_occurrences": equivalent_total,
        "literary_passages": literary_passages,
        "equivalent_passages": equivalent_passages,
        "both_passages": both_passages,
        "neither_passages": neither_passages,
        "literary_rate": literary_passages / n if n > 0 else 0,
        "equivalent_rate": equivalent_passages / n if n > 0 else 0,
        "literary_words_found": dict(literary_found_all.most_common()),
        "equivalent_words_found": dict(equivalent_found_all.most_common()),
        "preference_ratio": (literary_total / equivalent_total
                            if equivalent_total > 0 else float('inf')),
    }


# ============================================================================
# MAIN
# ============================================================================

MAX_CONSECUTIVE_FAILURES = 3  # circuit breaker: abort probe after N in a row
PREFLIGHT_PROMPT = "Write one sentence about a tree."


def preflight_check(caller, api_key, model_name, kwargs):
    """
    Fail-fast: make one test call before running the full experiment.
    Returns (success: bool, message: str).
    """
    print(f"  PREFLIGHT: Testing {model_name}...", end=" ", flush=True)
    try:
        text = caller(PREFLIGHT_PROMPT, api_key, **kwargs)
        if text and len(text.strip()) > 5:
            print(f"OK ({len(text)} chars)")
            return True, "ok"
        else:
            print(f"WARN: empty response")
            return False, "empty response from API"
    except Exception as e:
        err = str(e)[:120]
        print(f"FAIL: {err}")
        return False, err


def save_incremental(all_results, model_filter):
    """Save current state after every probe completion."""
    suffix = f"_{model_filter}" if model_filter else ""
    outfile = f"token_probing_results{suffix}.json"
    with open(outfile, "w") as f:
        json.dump(all_results, f, indent=2, default=str)
    return outfile


def run_probing(model_filter=None):
    """Run probing with fail-fast, circuit breakers, and incremental saves."""
    ANTHROPIC_KEY = os.environ.get("ANTHROPIC_API_KEY") or \
        "REDACTED_ANTHROPIC_KEY"
    OPENAI_KEY = os.environ.get("OPENAI_API_KEY") or \
        "REDACTED_OPENAI_KEY"
    GEMINI_KEY = os.environ.get("GEMINI_API_KEY") or \
        "REDACTED_GEMINI_KEY"

    models = [
        ("anthropic_sonnet", "Anthropic Sonnet 4", call_anthropic,
         ANTHROPIC_KEY, {"model": "claude-sonnet-4-20250514"}),
        ("openai_gpt4o", "OpenAI GPT-4o", call_openai,
         OPENAI_KEY, {"model": "gpt-4o"}),
        ("gemini_flash", "Gemini 2.5 Flash", call_gemini,
         GEMINI_KEY, {"model": "gemini-2.5-flash"}),
    ]

    if model_filter:
        models = [m for m in models if m[0] == model_filter]

    # ── PREFLIGHT: test every model before doing real work ──
    print(f"\n{'=' * 72}")
    print("  PREFLIGHT CHECKS")
    print(f"{'=' * 72}")
    live_models = []
    for model_id, model_name, caller, api_key, kwargs in models:
        ok, msg = preflight_check(caller, api_key, model_name, kwargs)
        if ok:
            live_models.append((model_id, model_name, caller, api_key, kwargs))
        else:
            print(f"  SKIPPING {model_name}: {msg}")

    if not live_models:
        print("\n  ALL MODELS FAILED PREFLIGHT. Aborting.")
        return {}

    print(f"\n  {len(live_models)}/{len(models)} models passed preflight.\n")

    # ── MAIN LOOP ──
    all_results = {}

    for model_id, model_name, caller, api_key, kwargs in live_models:
        print(f"\n{'=' * 72}")
        print(f"  MODEL: {model_name}")
        print(f"{'=' * 72}")

        model_results = {
            "model": model_name,
            "model_id": model_id,
            "probes": [],
        }
        model_dead = False

        for probe in PROBES:
            if model_dead:
                print(f"\n  Probe {probe['id']} — SKIPPED (model circuit-breaker tripped)")
                continue

            print(f"\n  Probe {probe['id']} ({probe['register']})...")
            completions = []
            failures = 0
            consecutive_failures = 0

            for i in range(N_SAMPLES):
                # ── Circuit breaker: N consecutive failures = abort probe ──
                if consecutive_failures >= MAX_CONSECUTIVE_FAILURES:
                    print(f"    CIRCUIT BREAKER: {consecutive_failures} consecutive "
                          f"failures. Aborting probe.")
                    # Check if the model is dead entirely
                    print(f"    RE-CHECKING model health...", end=" ", flush=True)
                    ok, msg = preflight_check(caller, api_key, model_name, kwargs)
                    if not ok:
                        print(f"    MODEL DEAD: {msg}. Skipping remaining probes.")
                        model_dead = True
                    break

                try:
                    text = caller(probe["context"], api_key, **kwargs)
                    completions.append(text)
                    consecutive_failures = 0  # reset on success
                    if (i + 1) % 5 == 0:
                        print(f"    {i+1}/{N_SAMPLES} ok "
                              f"({failures} failures so far)")
                except Exception as e:
                    failures += 1
                    consecutive_failures += 1
                    err = str(e)[:80]
                    print(f"    Sample {i+1} FAIL [{consecutive_failures}/"
                          f"{MAX_CONSECUTIVE_FAILURES}]: {err}")

                # Rate limiting
                if model_id == "openai_gpt4o":
                    time.sleep(22)  # 3 RPM limit
                elif model_id == "gemini_flash":
                    time.sleep(4)
                else:
                    time.sleep(1)

            # ── Analyze whatever we got ──
            if completions:
                analysis = analyze_probe(probe, completions)
                analysis["failures"] = failures
                analysis["circuit_breaker_tripped"] = (
                    consecutive_failures >= MAX_CONSECUTIVE_FAILURES)
                model_results["probes"].append(analysis)

                lit_r = analysis["literary_rate"]
                eq_r = analysis["equivalent_rate"]
                pref = analysis["preference_ratio"]
                print(f"    Literary: {analysis['literary_passages']}/{len(completions)} "
                      f"({lit_r:.0%})  |  Equivalent: "
                      f"{analysis['equivalent_passages']}/{len(completions)} "
                      f"({eq_r:.0%})  |  Pref ratio: {pref:.2f}")
                if analysis["literary_words_found"]:
                    top_lit = list(analysis["literary_words_found"].items())[:5]
                    print(f"    Top literary: {top_lit}")
            else:
                print(f"    FAILED: no completions generated")

            # ── Incremental save after every probe ──
            all_results[model_id] = model_results
            outfile = save_incremental(all_results, model_filter)
            print(f"    [saved → {outfile}]")

        all_results[model_id] = model_results

    # ================================================================
    # SUMMARY
    # ================================================================
    print(f"\n\n{'=' * 72}")
    print("TOKEN PROBING SUMMARY")
    print(f"{'=' * 72}")

    print(f"\n  {'Probe':<18} {'Model':<20} {'Literary':<12} {'Equiv':<12} {'Pref':<8}")
    print(f"  {'─' * 68}")

    for model_id, mr in all_results.items():
        for pa in mr["probes"]:
            lit = f"{pa['literary_passages']}/{pa['n_completions']}"
            eq = f"{pa['equivalent_passages']}/{pa['n_completions']}"
            pref = (f"{pa['preference_ratio']:.2f}"
                    if pa['preference_ratio'] != float('inf') else "inf")
            print(f"  {pa['probe_id']:<18} {mr['model']:<20} "
                  f"{lit:<12} {eq:<12} {pref:<8}")

    # Aggregate across probes per model
    print(f"\n  Aggregate (mean across probes):")
    for model_id, mr in all_results.items():
        if mr["probes"]:
            mean_lit = (sum(p["literary_rate"] for p in mr["probes"])
                       / len(mr["probes"]))
            mean_eq = (sum(p["equivalent_rate"] for p in mr["probes"])
                      / len(mr["probes"]))
            total_lit = sum(p["literary_total_occurrences"]
                          for p in mr["probes"])
            total_eq = sum(p["equivalent_total_occurrences"]
                         for p in mr["probes"])
            overall_pref = (total_lit / total_eq
                          if total_eq > 0 else float('inf'))
            print(f"    {mr['model']:<20} literary={mean_lit:.0%}  "
                  f"equiv={mean_eq:.0%}  "
                  f"overall pref={overall_pref:.2f}  "
                  f"(total: {total_lit} lit / {total_eq} eq)")

    # Final save
    outfile = save_incremental(all_results, model_filter)
    print(f"\n  Final results saved to {outfile}")

    return all_results


if __name__ == "__main__":
    import sys
    model_filter = sys.argv[1] if len(sys.argv) > 1 else None
    run_probing(model_filter=model_filter)
