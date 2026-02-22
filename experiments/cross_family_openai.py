#!/usr/bin/env python3
"""
Cross-Family Validation: OpenAI GPT-4o

Tests orphaned sophistication across a non-Anthropic model family.
This addresses the single most critical peer review concern:
all prior testing was within the Anthropic family.

Generates 20 passages (5 domains x 4 each) from GPT-4o,
runs v3 detector on each, then compares to Anthropic and human baselines.
"""

import json
import os
import time
import sys
import urllib.request
import urllib.error

sys.path.insert(0, "/sessions/wizardly-optimistic-bohr")
from lsr_detector_v3 import detect_lsr_v3

OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]
OPENAI_URL = "https://api.openai.com/v1/chat/completions"

# Same 5 domains, 4 passages each = 20 total
PROMPTS = {
    "ocean_storm": "Write a 150-200 word passage about being on a fishing boat during a severe ocean storm. Use past tense, third person. Focus on physical details: the boat, the water, the crew's actions. No dialogue tags.",
    "sawmill": "Write a 150-200 word passage about working in a sawmill. Use past tense, third person. Focus on physical details: the machinery, the wood, the worker's actions. No dialogue tags.",
    "kitchen_fire": "Write a 150-200 word passage about working in a busy restaurant kitchen during the dinner rush. Use past tense, third person. Focus on physical details: the heat, the equipment, the cook's actions. No dialogue tags.",
    "battlefield_surgery": "Write a 150-200 word passage about a field surgeon treating wounded soldiers during a battle. Use past tense, third person. Focus on physical details: the wounds, the instruments, the surgeon's actions. No dialogue tags.",
    "blacksmith": "Write a 150-200 word passage about a blacksmith forging a blade. Use past tense, third person. Focus on physical details: the forge, the metal, the smith's actions. No dialogue tags.",
}

PASSAGES_PER_DOMAIN = 4


def generate_openai(prompt, model="gpt-4o", retries=3):
    """Generate via OpenAI API."""
    data = json.dumps({
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 400,
        "temperature": 1.0,
    }).encode()

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {OPENAI_API_KEY}",
    }

    for attempt in range(retries):
        try:
            req = urllib.request.Request(OPENAI_URL, data=data, headers=headers)
            with urllib.request.urlopen(req, timeout=120) as response:
                result = json.loads(response.read())
                choices = result.get("choices", [])
                if choices:
                    return choices[0]["message"]["content"]
                return None
        except (urllib.error.URLError, urllib.error.HTTPError) as e:
            print(f"    Attempt {attempt+1} failed: {e}")
            if hasattr(e, 'read'):
                try:
                    body = e.read().decode()[:300]
                    print(f"    Response: {body}")
                except:
                    pass
            if attempt < retries - 1:
                time.sleep(5 * (attempt + 1))
    return None


def clean_text(text):
    """Remove markdown formatting and preambles."""
    text = text.replace("**", "").replace("##", "").replace("# ", "").strip()
    lines = text.split("\n")
    content_lines = []
    started = False
    for line in lines:
        l = line.strip()
        if not started:
            if l and not l.lower().startswith("here") and not l.lower().startswith("sure") and not l.startswith("#") and not l.startswith("---"):
                started = True
                content_lines.append(l)
        else:
            if l:
                content_lines.append(l)
    return " ".join(content_lines)


def run():
    print("=" * 72)
    print("CROSS-FAMILY VALIDATION: OpenAI GPT-4o")
    print("=" * 72)

    passages = []
    total_orphaned = 0
    total_earned = 0
    passages_with_orphan = 0
    failures = 0

    for domain, prompt in PROMPTS.items():
        for i in range(PASSAGES_PER_DOMAIN):
            pid = f"gpt4o_{domain[:3]}_{i+1}"
            print(f"\n  Generating {pid}...", end="", flush=True)

            text = generate_openai(prompt)
            if text is None:
                print(" FAILED")
                failures += 1
                continue

            text = clean_text(text)
            wc = len(text.split())
            print(f" OK ({wc} words)")

            if wc < 50:
                print(f"    Too short, skipping")
                failures += 1
                continue

            # Run v3 detector
            result = detect_lsr_v3(text, domain)
            n_orphaned = len(result["orphaned"])
            n_earned = len(result["earned"])
            total_orphaned += n_orphaned
            total_earned += n_earned
            if n_orphaned > 0:
                passages_with_orphan += 1

            passages.append({
                "id": pid,
                "domain": domain,
                "model": "gpt-4o",
                "text": text,
                "orphaned": n_orphaned,
                "earned": n_earned,
                "literal_filtered": result["literal_filtered"],
                "orphan_details": [
                    {"word": o["word"], "score": o["orphan_score"],
                     "fields": o["register_fields"],
                     "sentence": o["sentence"][:120]}
                    for o in result["orphaned"]
                ],
                "earned_details": [
                    {"word": e["word"], "score": e["orphan_score"],
                     "fields": e["register_fields"]}
                    for e in result["earned"]
                ],
            })

            if n_orphaned > 0:
                for o in result["orphaned"]:
                    print(f"    >>> ORPHANED: '{o['word']}' "
                          f"score={o['orphan_score']:.2f} "
                          f"[{', '.join(o['register_fields'])}]")
                    print(f"        \"{o['sentence'][:100]}\"")

            time.sleep(1)  # Rate limiting

    n_passages = len(passages)
    orphan_rate = total_orphaned / n_passages if n_passages > 0 else 0
    flag_rate = passages_with_orphan / n_passages if n_passages > 0 else 0

    print(f"\n\n{'=' * 72}")
    print("GPT-4o SUMMARY")
    print(f"{'=' * 72}")
    print(f"  Passages generated: {n_passages} (failures: {failures})")
    print(f"  Total orphaned words: {total_orphaned}")
    print(f"  Total earned words: {total_earned}")
    print(f"  Passages with orphan: {passages_with_orphan}/{n_passages} ({flag_rate:.1%})")
    print(f"  Orphan rate per passage: {orphan_rate:.3f}")

    # --- Cross-family comparison ---
    print(f"\n\n{'=' * 72}")
    print("CROSS-FAMILY COMPARISON")
    print(f"{'=' * 72}")

    print(f"\n  {'Model':<25} {'Family':<12} {'n':<6} {'Orphaned':<10} {'Flag%':<10}")
    print(f"  {'-'*62}")
    print(f"  {'Human (baseline)':<25} {'human':<12} {'25':<6} {'1':<10} {'4.0%':<10}")
    print(f"  {'GPT-4o':<25} {'OpenAI':<12} {n_passages:<6} {total_orphaned:<10} {flag_rate:<10.1%}")
    print(f"  {'Sonnet 4 (original)':<25} {'Anthropic':<12} {'20':<6} {'9':<10} {'35.0%':<10}")
    print(f"  {'Haiku 3.5':<25} {'Anthropic':<12} {'20':<6} {'8':<10} {'35.0%':<10}")
    print(f"  {'Sonnet 4 (replication)':<25} {'Anthropic':<12} {'20':<6} {'4':<10} {'15.0%':<10}")

    # --- Fisher's exact test: GPT-4o vs Human ---
    print(f"\n\n{'=' * 72}")
    print("STATISTICAL TESTS")
    print(f"{'=' * 72}")

    # Import statistical functions
    from statistical_tests import fishers_exact_test, fishers_exact_two_sided, cohens_h, binomial_ci_clopper_pearson

    # GPT-4o vs Human (passage-level)
    a = passages_with_orphan  # GPT flagged
    b = n_passages - passages_with_orphan  # GPT clean
    c = 1  # Human flagged
    d = 24  # Human clean

    p_one = fishers_exact_test(a, b, c, d)
    p_two = fishers_exact_two_sided(a, b, c, d)
    h = cohens_h(flag_rate, 1/25)
    gpt_ci = binomial_ci_clopper_pearson(passages_with_orphan, n_passages)
    human_ci = binomial_ci_clopper_pearson(1, 25)

    print(f"\n  GPT-4o vs Human (passage-level):")
    print(f"  GPT-4o:  {a} flagged / {b} clean = {flag_rate:.3f}  95% CI [{gpt_ci[0]:.3f}, {gpt_ci[1]:.3f}]")
    print(f"  Human:   {c} flagged / {d} clean = {1/25:.3f}  95% CI [{human_ci[0]:.3f}, {human_ci[1]:.3f}]")
    print(f"  Fisher's exact (one-sided): p = {p_one:.6f}  {'SIGNIFICANT' if p_one < 0.05 else 'n.s.'}")
    print(f"  Fisher's exact (two-sided): p = {p_two:.6f}  {'SIGNIFICANT' if p_two < 0.05 else 'n.s.'}")
    print(f"  Cohen's h = {h:.3f}  {'LARGE' if abs(h) > 0.8 else 'MEDIUM' if abs(h) > 0.5 else 'SMALL'}")

    # Pooled: ALL LLM (Anthropic + OpenAI) vs Human
    # Anthropic: original Sonnet (7/20) + Haiku (7/20 est) + Sonnet rep (3/20 est)
    # Use actual data: original 7, haiku ~7, sonnet rep ~3, GPT = passages_with_orphan
    # From cross_model_results.json for precise numbers
    try:
        with open("cross_model_results.json") as f:
            cm = json.load(f)
        haiku_flagged = cm["haiku"]["passages_with_orphan"]
        haiku_n = cm["haiku"]["n_passages"]
        sonnet_rep_flagged = cm["sonnet"]["passages_with_orphan"]
        sonnet_rep_n = cm["sonnet"]["n_passages"]
    except:
        haiku_flagged, haiku_n = 7, 20
        sonnet_rep_flagged, sonnet_rep_n = 3, 20

    # Original Sonnet: 7 passages with orphan out of 20
    orig_flagged, orig_n = 7, 20

    total_llm_flagged = orig_flagged + haiku_flagged + sonnet_rep_flagged + passages_with_orphan
    total_llm_n = orig_n + haiku_n + sonnet_rep_n + n_passages

    pooled_rate = total_llm_flagged / total_llm_n
    pooled_a = total_llm_flagged
    pooled_b = total_llm_n - total_llm_flagged

    p_pooled_one = fishers_exact_test(pooled_a, pooled_b, 1, 24)
    p_pooled_two = fishers_exact_two_sided(pooled_a, pooled_b, 1, 24)
    h_pooled = cohens_h(pooled_rate, 1/25)
    pooled_ci = binomial_ci_clopper_pearson(pooled_a, total_llm_n)

    print(f"\n  POOLED (all LLMs including GPT-4o) vs Human:")
    print(f"  LLM pooled: {pooled_a} flagged / {pooled_b} clean = {pooled_rate:.3f}")
    print(f"              95% CI [{pooled_ci[0]:.3f}, {pooled_ci[1]:.3f}]")
    print(f"  Human:      1 flagged / 24 clean = 0.040")
    print(f"  Fisher's exact (one-sided): p = {p_pooled_one:.6f}  {'SIGNIFICANT' if p_pooled_one < 0.05 else 'n.s.'}")
    print(f"  Fisher's exact (two-sided): p = {p_pooled_two:.6f}  {'SIGNIFICANT' if p_pooled_two < 0.05 else 'n.s.'}")
    print(f"  Cohen's h = {h_pooled:.3f}")

    # Save results
    results = {
        "model": "gpt-4o",
        "family": "OpenAI",
        "n_passages": n_passages,
        "failures": failures,
        "total_orphaned": total_orphaned,
        "total_earned": total_earned,
        "passages_with_orphan": passages_with_orphan,
        "orphan_rate": orphan_rate,
        "flag_rate": flag_rate,
        "fisher_one_sided_p": p_one,
        "fisher_two_sided_p": p_two,
        "cohens_h": h,
        "ci_lower": gpt_ci[0],
        "ci_upper": gpt_ci[1],
        "pooled_stats": {
            "total_llm_n": total_llm_n,
            "total_llm_flagged": total_llm_flagged,
            "pooled_rate": pooled_rate,
            "fisher_one_sided_p": p_pooled_one,
            "cohens_h": h_pooled,
        },
        "passages": passages,
    }

    outfile = "cross_family_gpt4o_results.json"
    with open(outfile, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nResults saved to {outfile}")


if __name__ == "__main__":
    run()
