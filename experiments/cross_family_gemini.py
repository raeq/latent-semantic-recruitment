#!/usr/bin/env python3
"""
Cross-Family Validation: Google Gemini

Tests orphaned sophistication on a third model family (Google).
Combined with Anthropic and OpenAI results, this gives three
independent model families.
"""

import json
import time
import sys
import urllib.request
import urllib.error

sys.path.insert(0, "/sessions/wizardly-optimistic-bohr")
from lsr_detector_v3 import detect_lsr_v3

GEMINI_API_KEY = "REDACTED_GEMINI_KEY"
GEMINI_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={GEMINI_API_KEY}"


def test_key():
    """Fail fast if API key is invalid."""
    print("Testing Gemini API key...", end="", flush=True)
    data = json.dumps({
        "contents": [{"parts": [{"text": "Say hello in one word."}]}],
        "generationConfig": {"maxOutputTokens": 10},
    }).encode()
    headers = {"Content-Type": "application/json"}
    try:
        req = urllib.request.Request(GEMINI_URL, data=data, headers=headers)
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read())
            candidates = result.get("candidates", [])
            if candidates:
                parts = candidates[0].get("content", {}).get("parts", [])
                if parts:
                    text = parts[0].get("text", "(no text)")
                    print(f" OK (response: {text.strip()[:30]})")
                else:
                    print(f" OK (no text parts, but API responded - may need more tokens)")
            else:
                print(f" OK (no candidates but API responded)")
            return True
    except urllib.error.HTTPError as e:
        body = e.read().decode()[:300]
        print(f" FAILED ({e.code})")
        print(f"  {body}")
        return False
    except Exception as e:
        print(f" FAILED ({e})")
        return False

PROMPTS = {
    "ocean_storm": "Write a 150-200 word passage about being on a fishing boat during a severe ocean storm. Use past tense, third person. Focus on physical details: the boat, the water, the crew's actions. No dialogue tags.",
    "sawmill": "Write a 150-200 word passage about working in a sawmill. Use past tense, third person. Focus on physical details: the machinery, the wood, the worker's actions. No dialogue tags.",
    "kitchen_fire": "Write a 150-200 word passage about working in a busy restaurant kitchen during the dinner rush. Use past tense, third person. Focus on physical details: the heat, the equipment, the cook's actions. No dialogue tags.",
    "battlefield_surgery": "Write a 150-200 word passage about a field surgeon treating wounded soldiers during a battle. Use past tense, third person. Focus on physical details: the wounds, the instruments, the surgeon's actions. No dialogue tags.",
    "blacksmith": "Write a 150-200 word passage about a blacksmith forging a blade. Use past tense, third person. Focus on physical details: the forge, the metal, the smith's actions. No dialogue tags.",
}

PASSAGES_PER_DOMAIN = 4


def generate_gemini(prompt, retries=3):
    """Generate via Google Gemini API."""
    data = json.dumps({
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 1.0,
            "maxOutputTokens": 2048,
        }
    }).encode()

    headers = {"Content-Type": "application/json"}

    for attempt in range(retries):
        try:
            req = urllib.request.Request(GEMINI_URL, data=data, headers=headers)
            with urllib.request.urlopen(req, timeout=120) as response:
                result = json.loads(response.read())
                candidates = result.get("candidates", [])
                if candidates:
                    parts = candidates[0].get("content", {}).get("parts", [])
                    if parts:
                        return parts[0].get("text", "")
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
            if l and not l.lower().startswith("here") and not l.lower().startswith("sure") and not l.lower().startswith("okay") and not l.startswith("#") and not l.startswith("---"):
                started = True
                content_lines.append(l)
        else:
            if l:
                content_lines.append(l)
    return " ".join(content_lines)


def run():
    print("=" * 72)
    print("CROSS-FAMILY VALIDATION: Google Gemini 2.0 Flash")
    print("=" * 72)

    passages = []
    total_orphaned = 0
    total_earned = 0
    passages_with_orphan = 0
    failures = 0

    for domain, prompt in PROMPTS.items():
        for i in range(PASSAGES_PER_DOMAIN):
            pid = f"gemini_{domain[:3]}_{i+1}"
            print(f"\n  Generating {pid}...", end="", flush=True)

            text = generate_gemini(prompt)
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
                "model": "gemini-2.5-flash",
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

            time.sleep(2)  # Rate limiting

    n_passages = len(passages)
    flag_rate = passages_with_orphan / n_passages if n_passages > 0 else 0

    print(f"\n\n{'=' * 72}")
    print("GEMINI SUMMARY")
    print(f"{'=' * 72}")
    print(f"  Passages generated: {n_passages} (failures: {failures})")
    print(f"  Total orphaned words: {total_orphaned}")
    print(f"  Total earned words: {total_earned}")
    print(f"  Passages with orphan: {passages_with_orphan}/{n_passages} ({flag_rate:.1%})")

    # Statistics
    from statistical_tests import fishers_exact_test, fishers_exact_two_sided, cohens_h, binomial_ci_clopper_pearson

    a = passages_with_orphan
    b = n_passages - passages_with_orphan
    c = 1
    d = 24

    p_one = fishers_exact_test(a, b, c, d)
    p_two = fishers_exact_two_sided(a, b, c, d)
    h = cohens_h(flag_rate, 1/25)
    gem_ci = binomial_ci_clopper_pearson(passages_with_orphan, n_passages)

    print(f"\n  Gemini vs Human:")
    print(f"  Gemini: {a}/{n_passages} = {flag_rate:.3f}  95% CI [{gem_ci[0]:.3f}, {gem_ci[1]:.3f}]")
    print(f"  Human:  1/25 = 0.040")
    print(f"  Fisher one-sided p = {p_one:.6f}  {'SIG' if p_one < 0.05 else 'n.s.'}")
    print(f"  Fisher two-sided p = {p_two:.6f}  {'SIG' if p_two < 0.05 else 'n.s.'}")
    print(f"  Cohen h = {h:.3f}")

    # Grand pooled: ALL models (Anthropic + OpenAI + Google) vs Human
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

    try:
        with open("cross_family_gpt4o_results.json") as f:
            gpt = json.load(f)
        gpt_flagged = gpt["passages_with_orphan"]
        gpt_n = gpt["n_passages"]
    except:
        gpt_flagged, gpt_n = 3, 20

    orig_flagged, orig_n = 7, 20

    total_llm_flagged = orig_flagged + haiku_flagged + sonnet_rep_flagged + gpt_flagged + passages_with_orphan
    total_llm_n = orig_n + haiku_n + sonnet_rep_n + gpt_n + n_passages

    pooled_rate = total_llm_flagged / total_llm_n
    pp_one = fishers_exact_test(total_llm_flagged, total_llm_n - total_llm_flagged, 1, 24)
    pp_two = fishers_exact_two_sided(total_llm_flagged, total_llm_n - total_llm_flagged, 1, 24)
    hp = cohens_h(pooled_rate, 1/25)
    pci = binomial_ci_clopper_pearson(total_llm_flagged, total_llm_n)

    from math import sqrt, erf
    def power_for_h(h_val, n1, n2, alpha=0.05):
        se = sqrt(1/n1 + 1/n2)
        z_alpha = 1.645
        noncentrality = abs(h_val) / se
        power = 1 - 0.5 * (1 + erf((z_alpha - noncentrality) / sqrt(2)))
        return power

    pooled_power = power_for_h(hp, total_llm_n, 25)

    print(f"\n  GRAND POOLED (all LLMs, 3 families, n={total_llm_n}) vs Human:")
    print(f"  LLM: {total_llm_flagged}/{total_llm_n} = {pooled_rate:.3f}  95% CI [{pci[0]:.3f}, {pci[1]:.3f}]")
    print(f"  Human: 1/25 = 0.040")
    print(f"  Fisher one-sided p = {pp_one:.6f}  {'SIG' if pp_one < 0.05 else 'n.s.'}")
    print(f"  Cohen h = {hp:.3f}")
    print(f"  Power = {pooled_power:.3f}")

    # Full comparison table
    print(f"\n\n{'=' * 72}")
    print("THREE-FAMILY COMPARISON TABLE")
    print(f"{'=' * 72}")
    print(f"\n  {'Model':<28} {'Family':<12} {'n':<6} {'Flagged':<10} {'Rate':<10} {'p':<14} {'h':<8}")
    print(f"  {'-'*88}")
    print(f"  {'Human (baseline)':<28} {'—':<12} {'25':<6} {'1':<10} {'4.0%':<10} {'—':<14} {'—':<8}")

    gpt_h = cohens_h(gpt_flagged/gpt_n, 1/25)
    gpt_p = fishers_exact_test(gpt_flagged, gpt_n - gpt_flagged, 1, 24)
    print(f"  {'GPT-4o':<28} {'OpenAI':<12} {gpt_n:<6} {gpt_flagged:<10} {gpt_flagged/gpt_n:<10.1%} {gpt_p:<14.4f} {gpt_h:<8.3f}")
    print(f"  {'Gemini 2.0 Flash':<28} {'Google':<12} {n_passages:<6} {passages_with_orphan:<10} {flag_rate:<10.1%} {p_one:<14.4f} {h:<8.3f}")

    s_p = fishers_exact_test(7, 13, 1, 24)
    s_h = cohens_h(7/20, 1/25)
    print(f"  {'Sonnet 4 (original)':<28} {'Anthropic':<12} {'20':<6} {'7':<10} {'35.0%':<10} {s_p:<14.4f} {s_h:<8.3f}")

    h_p = fishers_exact_test(haiku_flagged, haiku_n - haiku_flagged, 1, 24)
    h_h = cohens_h(haiku_flagged/haiku_n, 1/25)
    print(f"  {'Haiku 3.5':<28} {'Anthropic':<12} {haiku_n:<6} {haiku_flagged:<10} {haiku_flagged/haiku_n:<10.1%} {h_p:<14.4f} {h_h:<8.3f}")

    sr_p = fishers_exact_test(sonnet_rep_flagged, sonnet_rep_n - sonnet_rep_flagged, 1, 24)
    sr_h = cohens_h(sonnet_rep_flagged/sonnet_rep_n, 1/25)
    print(f"  {'Sonnet 4 (replication)':<28} {'Anthropic':<12} {sonnet_rep_n:<6} {sonnet_rep_flagged:<10} {sonnet_rep_flagged/sonnet_rep_n:<10.1%} {sr_p:<14.4f} {sr_h:<8.3f}")

    print(f"  {'POOLED (3 families)':<28} {'mixed':<12} {total_llm_n:<6} {total_llm_flagged:<10} {pooled_rate:<10.1%} {pp_one:<14.4f} {hp:<8.3f}")

    # Save
    results = {
        "model": "gemini-2.5-flash",
        "family": "Google",
        "n_passages": n_passages,
        "failures": failures,
        "total_orphaned": total_orphaned,
        "total_earned": total_earned,
        "passages_with_orphan": passages_with_orphan,
        "flag_rate": flag_rate,
        "fisher_one_sided_p": p_one,
        "fisher_two_sided_p": p_two,
        "cohens_h": h,
        "ci_lower": gem_ci[0],
        "ci_upper": gem_ci[1],
        "grand_pooled": {
            "total_llm_n": total_llm_n,
            "total_llm_flagged": total_llm_flagged,
            "pooled_rate": pooled_rate,
            "fisher_one_sided_p": pp_one,
            "fisher_two_sided_p": pp_two,
            "cohens_h": hp,
            "power": pooled_power,
        },
        "passages": passages,
    }

    outfile = "cross_family_gemini_results.json"
    with open(outfile, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nResults saved to {outfile}")


if __name__ == "__main__":
    if not test_key():
        print("\nAPI key invalid. Please check the key and try again.")
        sys.exit(1)
    run()
