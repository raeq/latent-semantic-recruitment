#!/usr/bin/env python3
"""
Cross-Family Model Validation via OpenRouter (free tier).

Tests orphaned sophistication across non-Anthropic model families.
This addresses the single most critical peer review concern.

Uses OpenRouter's free API to access:
- OpenAI GPT-oss-120B (OpenAI family)
- Qwen3 (Alibaba family)
- NVIDIA Nemotron (NVIDIA family)
"""

import json
import time
import sys
import urllib.request
import urllib.error

sys.path.insert(0, "/sessions/wizardly-optimistic-bohr")
from lsr_detector_v3 import detect_lsr_v3

# OpenRouter free API (no key needed for free models)
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

MODELS = {
    "gpt-oss-120b": "openai/gpt-oss-120b:free",
    "qwen3-coder": "qwen/qwen3-coder:free",
    "nemotron-30b": "nvidia/nemotron-3-nano-30b-a3b:free",
}

PROMPTS = {
    "ocean_storm": "Write a 150-200 word passage about being on a fishing boat during a severe ocean storm. Use past tense, third person. Focus on physical details: the boat, the water, the crew's actions. No dialogue tags.",
    "sawmill": "Write a 150-200 word passage about working in a sawmill. Use past tense, third person. Focus on physical details: the machinery, the wood, the worker's actions. No dialogue tags.",
    "kitchen_fire": "Write a 150-200 word passage about working in a busy restaurant kitchen during the dinner rush. Use past tense, third person. Focus on physical details: the heat, the equipment, the cook's actions. No dialogue tags.",
    "battlefield_surgery": "Write a 150-200 word passage about a field surgeon treating wounded soldiers during a battle. Use past tense, third person. Focus on physical details: the wounds, the instruments, the surgeon's actions. No dialogue tags.",
    "blacksmith": "Write a 150-200 word passage about a blacksmith forging a blade. Use past tense, third person. Focus on physical details: the forge, the metal, the smith's actions. No dialogue tags.",
}

PASSAGES_PER_DOMAIN = 4


def generate_openrouter(model_id, prompt, retries=3):
    """Generate via OpenRouter free API."""
    data = json.dumps({
        "model": model_id,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 400,
        "temperature": 1.0,
    }).encode()

    headers = {
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/quinn-richard/orphaned-sophistication",
        "X-Title": "Orphaned Sophistication Research",
    }

    for attempt in range(retries):
        try:
            req = urllib.request.Request(OPENROUTER_URL, data=data, headers=headers)
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
                    body = e.read().decode()[:200]
                    print(f"    Response: {body}")
                except:
                    pass
            if attempt < retries - 1:
                time.sleep(10 * (attempt + 1))
    return None


def run():
    print("=" * 72)
    print("CROSS-FAMILY VALIDATION (OpenRouter Free Tier)")
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
        failures = 0

        for domain, prompt in PROMPTS.items():
            for i in range(PASSAGES_PER_DOMAIN):
                pid = f"{model_name[:8]}_{domain[:3]}_{i+1}"
                print(f"\n  Generating {pid}...", end="", flush=True)

                text = generate_openrouter(model_id, prompt)
                if text is None:
                    print(" FAILED")
                    failures += 1
                    continue

                # Clean: some models add markdown formatting
                text = text.replace("**", "").replace("##", "").strip()
                # Remove any leading "Here's..." preamble
                lines = text.split("\n")
                # Skip lines that look like preamble
                content_lines = []
                started = False
                for line in lines:
                    l = line.strip()
                    if not started:
                        if l and not l.lower().startswith("here") and not l.lower().startswith("sure") and not l.startswith("#"):
                            started = True
                            content_lines.append(l)
                    else:
                        if l:
                            content_lines.append(l)
                text = " ".join(content_lines)

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
                    "model": model_name,
                    "text": text[:500],
                    "orphaned": n_orphaned,
                    "earned": n_earned,
                    "orphan_details": [
                        {"word": o["word"], "score": o["orphan_score"],
                         "fields": o["register_fields"]}
                        for o in result["orphaned"]
                    ],
                })

                if n_orphaned > 0:
                    for o in result["orphaned"]:
                        print(f"    >>> ORPHANED: '{o['word']}' "
                              f"score={o['orphan_score']:.2f} "
                              f"[{', '.join(o['register_fields'])}]")

                time.sleep(2)  # Rate limiting for free tier

        n_passages = len(passages)
        orphan_rate = total_orphaned / n_passages if n_passages > 0 else 0
        flag_rate = passages_with_orphan / n_passages if n_passages > 0 else 0

        print(f"\n\n  {model_name} SUMMARY:")
        print(f"  Passages generated: {n_passages} (failures: {failures})")
        print(f"  Total orphaned words: {total_orphaned}")
        print(f"  Passages with orphan: {passages_with_orphan}/{n_passages} ({flag_rate:.1%})")
        print(f"  Orphan rate per passage: {orphan_rate:.3f}")

        all_results[model_name] = {
            "model_id": model_id,
            "n_passages": n_passages,
            "failures": failures,
            "total_orphaned": total_orphaned,
            "total_earned": total_earned,
            "passages_with_orphan": passages_with_orphan,
            "orphan_rate": orphan_rate,
            "flag_rate": flag_rate,
            "passages": passages,
        }

    # Comparison
    print(f"\n\n{'=' * 72}")
    print("CROSS-FAMILY COMPARISON")
    print(f"{'=' * 72}")

    print(f"\n  {'Model':<25} {'Family':<15} {'n':<6} {'Orphaned':<10} {'Flag%':<10}")
    print(f"  {'-'*65}")
    print(f"  {'Human (baseline)':<25} {'human':<15} {'25':<6} {'1':<10} {'4.0%':<10}")

    for model_name, data in all_results.items():
        family = "OpenAI" if "gpt" in model_name else "Alibaba" if "qwen" in model_name else "NVIDIA"
        print(f"  {model_name:<25} {family:<15} {data['n_passages']:<6} "
              f"{data['total_orphaned']:<10} {data['flag_rate']:<10.1%}")

    # Previous Anthropic results
    print(f"  {'Sonnet 4 (original)':<25} {'Anthropic':<15} {'20':<6} {'9':<10} {'35.0%':<10}")
    print(f"  {'Haiku 3.5':<25} {'Anthropic':<15} {'20':<6} {'8':<10} {'35.0%':<10}")

    outfile = "cross_family_results.json"
    with open(outfile, "w") as f:
        json.dump(all_results, f, indent=2)
    print(f"\nResults saved to {outfile}")


if __name__ == "__main__":
    run()
