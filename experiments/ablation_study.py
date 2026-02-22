#!/usr/bin/env python3
"""
Ablation Study: Three-Dimensional Orphanhood Model

Tests whether all three orphanhood dimensions (isolation, chain, preparation)
independently contribute discriminative power. Runs the detector with each
dimension removed in turn, measuring how Cohen's h changes with each ablation.

Configurations:
- Full model (all 3 dimensions)
- Remove isolation (chain + preparation only)
- Remove chain (isolation + preparation only)
- Remove preparation (isolation + chain only)

Authors: Richard Quinn & Claude Opus 4 (Anthropic)
Date: 22 February 2026
"""

import json
import re
import sys
sys.path.insert(0, "/sessions/wizardly-optimistic-bohr")

from lsr_detector_v3 import (
    DOMAIN_LITERAL, REGISTER_FIELDS, ALL_REGISTER_WORDS, STOPWORDS, PUNCT,
    INANIMATE_NOUNS, ANIMATE_VERBS,
    sentence_figurative_density, detect_personification,
    test_isolation, test_chain, test_preparation,
)
from statistical_tests import (
    fishers_exact_test, fishers_exact_two_sided,
    cohens_h, binomial_ci_clopper_pearson,
)


# ============================================================================
# ABLATED DETECTOR
# ============================================================================

def detect_ablated(text, domain, use_isolation=True, use_chain=True,
                   use_preparation=True, threshold=0.6):
    """
    Run the v3 detector with optional dimensions disabled.

    When a dimension is disabled, its score is excluded from the orphan_score
    calculation (the mean is taken over remaining dimensions only).
    """
    domain_lit = DOMAIN_LITERAL.get(domain, set())
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    if not sentences:
        return {"orphaned": [], "earned": [], "literal_filtered": 0}

    active_dims = []
    if use_isolation:
        active_dims.append("isolation")
    if use_chain:
        active_dims.append("chain")
    if use_preparation:
        active_dims.append("preparation")

    n_dims = len(active_dims)
    if n_dims == 0:
        return {"orphaned": [], "earned": [], "literal_filtered": 0}

    literal_count = 0
    orphaned = []
    earned = []

    for sent_idx, sentence in enumerate(sentences):
        persns = detect_personification(sentence)
        pers_verbs = {p["verb"] for p in persns}

        words = sentence.lower().split()
        for word_raw in words:
            word = PUNCT.sub('', word_raw).lower()
            if not word or len(word) < 3 or word in STOPWORDS:
                continue
            if word not in ALL_REGISTER_WORDS:
                continue
            if word in domain_lit:
                literal_count += 1
                continue

            matched_fields = []
            for field_name, field_words in REGISTER_FIELDS.items():
                if word in field_words:
                    matched_fields.append(field_name)
            if not matched_fields:
                continue

            # Figurativeness check (identical to v3)
            is_figurative = False
            if word in pers_verbs:
                is_figurative = True
            if word in ANIMATE_VERBS:
                is_figurative = True

            word_idx = None
            for wi, w in enumerate(words):
                if PUNCT.sub('', w).lower() == word:
                    word_idx = wi
                    break

            if word_idx is not None and word in {
                "hungry", "stubborn", "angry", "eager", "tired",
                "patient", "nervous", "reluctant", "willing"
            }:
                if word_idx + 1 < len(words):
                    next_w = PUNCT.sub('', words[word_idx + 1]).lower()
                    if next_w in INANIMATE_NOUNS or next_w in ALL_REGISTER_WORDS:
                        is_figurative = True
                if word_idx > 0:
                    for j in range(word_idx - 1, max(word_idx - 4, -1), -1):
                        prev_w = PUNCT.sub('', words[j]).lower()
                        if prev_w in INANIMATE_NOUNS:
                            is_figurative = True
                            break
                        if prev_w not in STOPWORDS and len(prev_w) > 2:
                            break

            if not is_figurative:
                continue

            # Run active tests
            scores = []
            if use_isolation:
                t1 = test_isolation(sent_idx, sentences, domain_lit)
                scores.append(t1["score"])
            if use_chain:
                t2 = test_chain(word, matched_fields, sent_idx, sentences, domain_lit)
                scores.append(t2["score"])
            if use_preparation:
                t3 = test_preparation(sent_idx, sentences)
                scores.append(t3["score"])

            orphan_score = sum(scores) / n_dims

            if orphan_score > threshold:
                orphaned.append({"word": word, "score": orphan_score})
            else:
                earned.append({"word": word, "score": orphan_score})

    return {
        "orphaned": orphaned,
        "earned": earned,
        "literal_filtered": literal_count,
    }


# ============================================================================
# LOAD ALL PASSAGES
# ============================================================================

def load_all_passages():
    """Load all 125 passages (25 human + 100 LLM) with text and domain."""
    passages = []

    # 1. Richard's 5 hand-written passages
    from lsr_detector_v2 import RICHARD_PASSAGES
    for domain, text in RICHARD_PASSAGES.items():
        passages.append({
            "id": f"richard_{domain}",
            "source": "human",
            "model": "human_richard",
            "domain": domain,
            "text": text,
        })

    # 2. Published prose (20 passages)
    from lsr_exp8c_real_published import PUBLISHED_PASSAGES
    for entry in PUBLISHED_PASSAGES:
        passages.append({
            "id": entry["id"],
            "source": "human",
            "model": "human_published",
            "domain": entry["domain"],
            "text": entry["text"],
        })

    # 3. Original Sonnet (20 passages)
    with open("lsr_exp8_results.json") as f:
        exp8 = json.load(f)
    for entry in exp8["llm_passages"]:
        passages.append({
            "id": entry["id"],
            "source": "llm",
            "model": "sonnet_original",
            "domain": entry["domain"],
            "text": entry["text"],
        })

    # 4. Haiku + Sonnet replication (20 + 20)
    with open("cross_model_results.json") as f:
        cm = json.load(f)
    for entry in cm["haiku"]["passages"]:
        passages.append({
            "id": entry["id"],
            "source": "llm",
            "model": "haiku",
            "domain": entry["domain"],
            "text": entry["text"],
        })
    for entry in cm["sonnet"]["passages"]:
        passages.append({
            "id": entry["id"],
            "source": "llm",
            "model": "sonnet_replication",
            "domain": entry["domain"],
            "text": entry["text"],
        })

    # 5. GPT-4o (20 passages)
    with open("cross_family_gpt4o_results.json") as f:
        gpt = json.load(f)
    for entry in gpt["passages"]:
        passages.append({
            "id": entry["id"],
            "source": "llm",
            "model": "gpt4o",
            "domain": entry["domain"],
            "text": entry["text"],
        })

    # 6. Gemini (20 passages)
    with open("cross_family_gemini_results.json") as f:
        gem = json.load(f)
    for entry in gem["passages"]:
        passages.append({
            "id": entry["id"],
            "source": "llm",
            "model": "gemini",
            "domain": entry["domain"],
            "text": entry["text"],
        })

    return passages


# ============================================================================
# RUN ABLATION
# ============================================================================

CONFIGS = {
    "full":          {"use_isolation": True,  "use_chain": True,  "use_preparation": True},
    "no_isolation":  {"use_isolation": False, "use_chain": True,  "use_preparation": True},
    "no_chain":      {"use_isolation": True,  "use_chain": False, "use_preparation": True},
    "no_preparation":{"use_isolation": True,  "use_chain": True,  "use_preparation": False},
}


def run_ablation():
    passages = load_all_passages()

    human = [p for p in passages if p["source"] == "human"]
    llm = [p for p in passages if p["source"] == "llm"]

    print("=" * 72)
    print("ABLATION STUDY: THREE-DIMENSIONAL ORPHANHOOD MODEL")
    print("=" * 72)
    print(f"\n  Total passages: {len(passages)} (human: {len(human)}, LLM: {len(llm)})")

    results = {}

    for config_name, kwargs in CONFIGS.items():
        print(f"\n\n{'─' * 72}")
        dims = [k.replace("use_", "") for k, v in kwargs.items() if v]
        print(f"  CONFIG: {config_name}  (active: {', '.join(dims)})")
        print(f"{'─' * 72}")

        human_flagged = 0
        llm_flagged = 0
        human_total = len(human)
        llm_total = len(llm)

        # Per-model tracking
        model_stats = {}

        for p in passages:
            result = detect_ablated(p["text"], p["domain"], **kwargs)
            has_orphan = len(result["orphaned"]) > 0

            model = p["model"]
            if model not in model_stats:
                model_stats[model] = {"n": 0, "flagged": 0}
            model_stats[model]["n"] += 1
            if has_orphan:
                model_stats[model]["flagged"] += 1

            if p["source"] == "human":
                if has_orphan:
                    human_flagged += 1
            else:
                if has_orphan:
                    llm_flagged += 1

        human_rate = human_flagged / human_total
        llm_rate = llm_flagged / llm_total

        h = cohens_h(llm_rate, human_rate)
        p_val = fishers_exact_test(llm_flagged, llm_total - llm_flagged,
                                    human_flagged, human_total - human_flagged)
        p_two = fishers_exact_two_sided(llm_flagged, llm_total - llm_flagged,
                                         human_flagged, human_total - human_flagged)
        llm_ci = binomial_ci_clopper_pearson(llm_flagged, llm_total)
        human_ci = binomial_ci_clopper_pearson(human_flagged, human_total)

        print(f"\n  Human:  {human_flagged}/{human_total} = {human_rate:.3f}  "
              f"95% CI [{human_ci[0]:.3f}, {human_ci[1]:.3f}]")
        print(f"  LLM:    {llm_flagged}/{llm_total} = {llm_rate:.3f}  "
              f"95% CI [{llm_ci[0]:.3f}, {llm_ci[1]:.3f}]")
        print(f"  Fisher one-sided p = {p_val:.6f}  {'SIG' if p_val < 0.05 else 'n.s.'}")
        print(f"  Fisher two-sided p = {p_two:.6f}  {'SIG' if p_two < 0.05 else 'n.s.'}")
        print(f"  Cohen's h = {h:.3f}")

        print(f"\n  Per-model breakdown:")
        for model_name in ["human_richard", "human_published", "sonnet_original",
                           "haiku", "sonnet_replication", "gpt4o", "gemini"]:
            if model_name in model_stats:
                ms = model_stats[model_name]
                rate = ms["flagged"] / ms["n"] if ms["n"] > 0 else 0
                print(f"    {model_name:<22} {ms['flagged']:>3}/{ms['n']:<3} = {rate:.1%}")

        results[config_name] = {
            "active_dimensions": dims,
            "human_flagged": human_flagged,
            "human_total": human_total,
            "human_rate": human_rate,
            "llm_flagged": llm_flagged,
            "llm_total": llm_total,
            "llm_rate": llm_rate,
            "cohens_h": h,
            "fisher_one_sided_p": p_val,
            "fisher_two_sided_p": p_two,
            "per_model": model_stats,
        }

    # Summary comparison table
    print(f"\n\n{'=' * 72}")
    print("ABLATION SUMMARY")
    print(f"{'=' * 72}")

    print(f"\n  {'Configuration':<22} {'Dims':<4} {'Human':<12} {'LLM':<12} "
          f"{'h':<8} {'p(1)':<10} {'Sig?':<5}")
    print(f"  {'─' * 72}")

    full_h = results["full"]["cohens_h"]

    for config_name in ["full", "no_isolation", "no_chain", "no_preparation"]:
        r = results[config_name]
        n_dims = len(r["active_dimensions"])
        h_human = f"{r['human_flagged']}/{r['human_total']}"
        h_llm = f"{r['llm_flagged']}/{r['llm_total']}"
        sig = "YES" if r["fisher_one_sided_p"] < 0.05 else "no"
        delta = r["cohens_h"] - full_h if config_name != "full" else 0
        delta_str = f" (Δh={delta:+.3f})" if config_name != "full" else ""

        print(f"  {config_name:<22} {n_dims:<4} {h_human:<12} {h_llm:<12} "
              f"{r['cohens_h']:<8.3f} {r['fisher_one_sided_p']:<10.4f} {sig:<5}"
              f"{delta_str}")

    # Impact analysis
    print(f"\n  Dimension impact (change in Cohen's h when removed):")
    for config_name in ["no_isolation", "no_chain", "no_preparation"]:
        removed = config_name.replace("no_", "")
        delta = results[config_name]["cohens_h"] - full_h
        direction = "↓" if delta < 0 else "↑"
        print(f"    Remove {removed:<15} h: {full_h:.3f} → "
              f"{results[config_name]['cohens_h']:.3f}  "
              f"({direction} {abs(delta):.3f})")

    # Save
    outfile = "ablation_results.json"
    with open(outfile, "w") as f:
        # Convert model_stats for JSON
        for config_name in results:
            results[config_name]["per_model"] = {
                k: v for k, v in results[config_name]["per_model"].items()
            }
        json.dump(results, f, indent=2)
    print(f"\n  Results saved to {outfile}")

    return results


if __name__ == "__main__":
    run_ablation()
