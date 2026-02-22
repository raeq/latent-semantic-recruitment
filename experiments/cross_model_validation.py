#!/usr/bin/env python3
"""
Cross-Model Validation: Generate passages from multiple Anthropic models
and run v3 detector on all of them.

Addresses peer review concern #2: single-model corpus.

Tests: Claude Haiku 3.5, Claude Sonnet 4 (already done), Claude Opus 4
"""

import json
import time
import sys
import os

# API setup
API_KEY = "REDACTED_ANTHROPIC_KEY"

sys.path.insert(0, "/sessions/wizardly-optimistic-bohr")
from lsr_detector_v3 import detect_lsr_v3

# Models to test
MODELS = {
    "haiku": "claude-haiku-4-5-20251001",
    "sonnet": "claude-sonnet-4-20250514",
}

# Same 5 domains, 4 passages each = 20 per model
PROMPTS = {
    "ocean_storm": "Write a 150-200 word passage about being on a fishing boat during a severe ocean storm. Use past tense, third person. Focus on physical details: the boat, the water, the crew's actions. No dialogue tags.",
    "sawmill": "Write a 150-200 word passage about working in a sawmill. Use past tense, third person. Focus on physical details: the machinery, the wood, the worker's actions. No dialogue tags.",
    "kitchen_fire": "Write a 150-200 word passage about working in a busy restaurant kitchen during the dinner rush. Use past tense, third person. Focus on physical details: the heat, the equipment, the cook's actions. No dialogue tags.",
    "battlefield_surgery": "Write a 150-200 word passage about a field surgeon treating wounded soldiers during a battle. Use past tense, third person. Focus on physical details: the wounds, the instruments, the surgeon's actions. No dialogue tags.",
    "blacksmith": "Write a 150-200 word passage about a blacksmith forging a blade. Use past tense, third person. Focus on physical details: the forge, the metal, the smith's actions. No dialogue tags.",
}

PASSAGES_PER_DOMAIN = 4


def generate_passage(model_id, prompt, retries=3):
    """Generate a passage using the Anthropic API."""
    import urllib.request
    import urllib.error

    url = "https://api.anthropic.com/v1/messages"
    headers = {
        "Content-Type": "application/json",
        "x-api-key": API_KEY,
        "anthropic-version": "2023-06-01",
    }
    data = json.dumps({
        "model": model_id,
        "max_tokens": 400,
        "temperature": 1.0,
        "messages": [{"role": "user", "content": prompt}],
    }).encode()

    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, data=data, headers=headers)
            with urllib.request.urlopen(req, timeout=60) as response:
                result = json.loads(response.read())
                return result["content"][0]["text"]
        except (urllib.error.URLError, urllib.error.HTTPError) as e:
            print(f"  Attempt {attempt+1} failed: {e}")
            if attempt < retries - 1:
                time.sleep(5 * (attempt + 1))
    return None


def run_cross_model():
    print("=" * 72)
    print("CROSS-MODEL VALIDATION EXPERIMENT")
    print("=" * 72)

    all_results = {}

    for model_name, model_id in MODELS.items():
        print(f"\n\n{'=' * 60}")
        print(f"MODEL: {model_name} ({model_id})")
        print(f"{'=' * 60}")

        passages = []
        total_orphaned = 0
        total_earned = 0
        passages_with_orphan = 0
        total_lsr_words = 0

        for domain, prompt in PROMPTS.items():
            for i in range(PASSAGES_PER_DOMAIN):
                pid = f"{model_name}_{domain[:3]}_{i+1}"
                print(f"\n  Generating {pid}...", end="", flush=True)
                text = generate_passage(model_id, prompt)
                if text is None:
                    print(" FAILED")
                    continue
                print(f" OK ({len(text.split())} words)")

                # Run v3 detector
                result = detect_lsr_v3(text, domain)
                n_orphaned = len(result["orphaned"])
                n_earned = len(result["earned"])
                total_orphaned += n_orphaned
                total_earned += n_earned
                total_lsr_words += n_orphaned + n_earned
                if n_orphaned > 0:
                    passages_with_orphan += 1

                passage_data = {
                    "id": pid,
                    "domain": domain,
                    "model": model_name,
                    "text": text,
                    "orphaned": n_orphaned,
                    "earned": n_earned,
                    "literal_filtered": result["literal_filtered"],
                    "orphan_details": [
                        {"word": o["word"], "score": o["orphan_score"],
                         "fields": o["register_fields"],
                         "sentence": o["sentence"][:100]}
                        for o in result["orphaned"]
                    ],
                }
                passages.append(passage_data)

                if n_orphaned > 0:
                    for o in result["orphaned"]:
                        print(f"    >>> ORPHANED: '{o['word']}' "
                              f"score={o['orphan_score']:.2f}")

                # Rate limit
                time.sleep(1)

        n_passages = len(passages)
        orphan_rate = total_orphaned / n_passages if n_passages > 0 else 0
        passage_flag_rate = passages_with_orphan / n_passages if n_passages > 0 else 0

        print(f"\n\n  {model_name} SUMMARY:")
        print(f"  Passages: {n_passages}")
        print(f"  Total orphaned words: {total_orphaned}")
        print(f"  Total earned words: {total_earned}")
        print(f"  Passages with orphan: {passages_with_orphan}/{n_passages} "
              f"({passage_flag_rate:.1%})")
        print(f"  Orphan rate per passage: {orphan_rate:.3f}")

        all_results[model_name] = {
            "model_id": model_id,
            "n_passages": n_passages,
            "total_orphaned": total_orphaned,
            "total_earned": total_earned,
            "passages_with_orphan": passages_with_orphan,
            "orphan_rate": orphan_rate,
            "passage_flag_rate": passage_flag_rate,
            "passages": passages,
        }

    # --- Comparison ---
    print(f"\n\n{'=' * 72}")
    print("CROSS-MODEL COMPARISON")
    print(f"{'=' * 72}")

    # Include original Sonnet results for comparison
    print(f"\n  {'Model':<20} {'n':<6} {'Orphaned':<10} {'Rate':<10} {'Flagged%':<10}")
    print(f"  {'-'*55}")

    # Human baseline (from previous experiments)
    print(f"  {'Human (n=25)':<20} {'25':<6} {'1':<10} {'0.040':<10} {'4.0%':<10}")

    for model_name, data in all_results.items():
        print(f"  {model_name:<20} {data['n_passages']:<6} "
              f"{data['total_orphaned']:<10} "
              f"{data['orphan_rate']:<10.3f} "
              f"{data['passage_flag_rate']:<10.1%}")

    # Also include the original Sonnet data from Exp 8
    print(f"  {'Sonnet (Exp8 orig)':<20} {'20':<6} {'9':<10} {'0.450':<10} {'35.0%':<10}")

    # Save
    outfile = "cross_model_results.json"
    with open(outfile, "w") as f:
        json.dump(all_results, f, indent=2)
    print(f"\nResults saved to {outfile}")


if __name__ == "__main__":
    run_cross_model()
