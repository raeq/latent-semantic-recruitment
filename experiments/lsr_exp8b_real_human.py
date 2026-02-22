#!/usr/bin/env python3
"""
LSR Experiment 8b: Real Human Prose Test

The ACTUAL test Richard asked for. Uses:
  - HUMAN: Richard's own written prose (Chapters 1-2, prose samples)
  - LLM: API-generated passages from Experiment 8

The human passages in Exp 8 were Claude-written pastiches.
That's a mirror, not a test. This version uses Richard's chapters.

We segment the chapters into ~150-200 word passages, detect the
nearest domain for each, and run detector v2.

Authors: Richard Quinn & Claude Opus 4 (Anthropic)
Date: 22 February 2026
"""

import json
import os
import re
import sys
from collections import defaultdict

sys.path.insert(0, "/sessions/wizardly-optimistic-bohr/mnt/Ribbonworld")
sys.path.insert(0, "/sessions/wizardly-optimistic-bohr")

from lsr_detector_v2 import detect_lsr, print_result

# ============================================================================
# DOMAIN DETECTION
# ============================================================================
# We need to assign a domain to each passage so the detector knows which
# domain-literal set to use. This is simple keyword matching.

DOMAIN_KEYWORDS = {
    "ocean_storm": {"sea", "wave", "waves", "storm", "wind", "boat", "ship",
                    "sail", "water", "ocean", "rain", "gale", "helm",
                    "mast", "deck", "bow", "stern", "swimming", "drown"},
    "sawmill": {"saw", "mill", "sawmill", "lumber", "timber", "blade",
                "log", "logs", "plank", "board", "sawdust", "wood",
                "bandsaw", "cut", "cutting"},
    "kitchen_fire": {"kitchen", "cook", "chef", "stove", "oven", "pan",
                     "pot", "fry", "frying", "pasta", "dinner", "meal",
                     "soup", "food", "recipe", "burner", "grill"},
    "blacksmith": {"forge", "anvil", "smith", "blacksmith", "hammer",
                   "iron", "steel", "bellows", "tongs", "metal",
                   "quench", "temper"},
    "battlefield_surgery": {"surgery", "surgeon", "wound", "blood",
                           "hospital", "medic", "scalpel", "bandage",
                           "morphine", "tourniquet", "injury"},
    # General outdoor/wilderness — Richard's primary register in Ch 1-2
    "wilderness": {"tree", "trees", "forest", "woods", "mountain", "ridge",
                   "stream", "trail", "camp", "tent", "fire", "firewood",
                   "path", "rock", "rocks", "clearing", "slope", "snow",
                   "frost", "larch", "spruce", "needles", "bark"},
}


def detect_domain(text):
    """Detect the most likely domain for a passage."""
    words = set(re.findall(r'\b\w+\b', text.lower()))
    scores = {}
    for domain, keywords in DOMAIN_KEYWORDS.items():
        scores[domain] = len(words & keywords)
    best = max(scores, key=scores.get)
    if scores[best] == 0:
        return "general"
    return best


def segment_text(text, target_words=175, min_words=100):
    """
    Segment text into passages of approximately target_words length.
    Splits on paragraph boundaries (double newline or ---).
    """
    # Split on scene breaks and double newlines
    paragraphs = re.split(r'\n\s*\n|\n---\n', text)
    paragraphs = [p.strip() for p in paragraphs if p.strip()]
    # Remove markdown headers
    paragraphs = [re.sub(r'^#+\s+.*$', '', p, flags=re.MULTILINE).strip()
                  for p in paragraphs]
    paragraphs = [p for p in paragraphs if p]

    segments = []
    current = []
    current_len = 0

    for para in paragraphs:
        para_words = len(para.split())
        if current_len + para_words > target_words * 1.3 and current_len >= min_words:
            segments.append(" ".join(current))
            current = [para]
            current_len = para_words
        else:
            current.append(para)
            current_len += para_words

    if current and current_len >= min_words:
        segments.append(" ".join(current))
    elif current and segments:
        # Append remainder to last segment
        segments[-1] += " " + " ".join(current)

    return segments


def load_chapter(path):
    """Load a chapter file."""
    with open(path) as f:
        return f.read()


def run_experiment():
    print("=" * 72)
    print("EXPERIMENT 8b: REAL HUMAN PROSE TEST")
    print("Richard's actual chapters vs LLM-generated passages")
    print("=" * 72)

    # Load Richard's chapters
    ch1_path = "/sessions/wizardly-optimistic-bohr/mnt/Ribbonworld/drafts/book_1/chapter_1.md"
    ch2_path = "/sessions/wizardly-optimistic-bohr/mnt/Ribbonworld/drafts/book_1/chapter_2.md"

    human_passages = []

    for path, label in [(ch1_path, "Ch1"), (ch2_path, "Ch2")]:
        if not os.path.exists(path):
            print(f"  WARNING: {path} not found, skipping")
            continue
        text = load_chapter(path)
        segments = segment_text(text)
        for i, seg in enumerate(segments):
            domain = detect_domain(seg)
            human_passages.append({
                "id": f"R_{label}_{i+1:02d}",
                "source": "human_richard",
                "domain": domain,
                "text": seg,
                "word_count": len(seg.split()),
            })
        print(f"  Loaded {label}: {len(segments)} passages")

    # Also load Richard's 5 original test passages from the detector
    from lsr_detector_v2 import RICHARD_PASSAGES
    for domain, text in RICHARD_PASSAGES.items():
        human_passages.append({
            "id": f"R_orig_{domain[:4]}",
            "source": "human_richard_original",
            "domain": domain,
            "text": text,
            "word_count": len(text.split()),
        })
    print(f"  Loaded original 5 test passages")

    # Load LLM passages from Experiment 8
    exp8_path = "/sessions/wizardly-optimistic-bohr/lsr_exp8_results.json"
    if os.path.exists(exp8_path):
        with open(exp8_path) as f:
            exp8_data = json.load(f)
        llm_passages = []
        for entry in exp8_data.get("llm_passages", []):
            llm_passages.append({
                "id": entry["id"],
                "source": "llm",
                "domain": entry["domain"],
                "text": entry["text"],
                "word_count": len(entry["text"].split()),
            })
        print(f"  Loaded {len(llm_passages)} LLM passages from Exp 8")
    else:
        print("  ERROR: No Exp 8 results found. Run lsr_exp8_scale.py first.")
        return

    print(f"\n  Total: {len(human_passages)} human, {len(llm_passages)} LLM")

    # Run detector on all passages
    print(f"\n{'=' * 72}")
    print("DETECTION RESULTS")
    print(f"{'=' * 72}\n")

    all_results = []

    print("  --- HUMAN (Richard) ---")
    h_total_lsr = 0
    h_total_pers = 0
    h_flagged = 0
    h_domain_counts = defaultdict(lambda: {"passages": 0, "lsr": 0})

    for entry in human_passages:
        detection = detect_lsr(entry["text"], entry["domain"])
        lsr_count = len(detection["lsr_candidates"])
        pers_count = len(detection["personifications"])
        h_total_lsr += lsr_count
        h_total_pers += pers_count
        h_domain_counts[entry["domain"]]["passages"] += 1
        h_domain_counts[entry["domain"]]["lsr"] += lsr_count

        flag = " ***" if lsr_count > 0 else ""
        if lsr_count > 0:
            h_flagged += 1

        result = {
            "id": entry["id"],
            "source": entry["source"],
            "domain": entry["domain"],
            "word_count": entry["word_count"],
            "lsr_count": lsr_count,
            "pers_count": pers_count,
            "lsr_details": detection["lsr_candidates"],
            "literal_filtered": detection["literal_filtered"],
        }
        all_results.append(result)

        if lsr_count > 0:
            print(f"  {entry['id']:<16} {entry['domain']:<16} "
                  f"LSR={lsr_count} pers={pers_count} "
                  f"lit={detection['literal_filtered']}{flag}")
            for det in detection["lsr_candidates"]:
                pers_tag = " [pers]" if det.get("is_personification") else ""
                print(f"    '{det['word']}' [{', '.join(det['register_fields'])}]{pers_tag}")
                print(f"    \"{det['sentence'][:100]}\"")

    h_n = len(human_passages)
    print(f"\n  Human summary: {h_total_lsr} LSR in {h_n} passages "
          f"({h_total_lsr/h_n:.2f}/passage), {h_flagged} passages flagged")

    print(f"\n  --- LLM ---")
    l_total_lsr = 0
    l_total_pers = 0
    l_flagged = 0
    l_domain_counts = defaultdict(lambda: {"passages": 0, "lsr": 0})

    for entry in llm_passages:
        detection = detect_lsr(entry["text"], entry["domain"])
        lsr_count = len(detection["lsr_candidates"])
        pers_count = len(detection["personifications"])
        l_total_lsr += lsr_count
        l_total_pers += pers_count
        l_domain_counts[entry["domain"]]["passages"] += 1
        l_domain_counts[entry["domain"]]["lsr"] += lsr_count

        flag = " ***" if lsr_count > 0 else ""
        if lsr_count > 0:
            l_flagged += 1

        result = {
            "id": entry["id"],
            "source": entry["source"],
            "domain": entry["domain"],
            "word_count": entry["word_count"],
            "lsr_count": lsr_count,
            "pers_count": pers_count,
            "lsr_details": detection["lsr_candidates"],
            "literal_filtered": detection["literal_filtered"],
        }
        all_results.append(result)

        if lsr_count > 0:
            print(f"  {entry['id']:<16} {entry['domain']:<16} "
                  f"LSR={lsr_count} pers={pers_count} "
                  f"lit={detection['literal_filtered']}{flag}")
            for det in detection["lsr_candidates"]:
                pers_tag = " [pers]" if det.get("is_personification") else ""
                print(f"    '{det['word']}' [{', '.join(det['register_fields'])}]{pers_tag}")
                print(f"    \"{det['sentence'][:100]}\"")

    l_n = len(llm_passages)
    print(f"\n  LLM summary: {l_total_lsr} LSR in {l_n} passages "
          f"({l_total_lsr/l_n:.2f}/passage), {l_flagged} passages flagged")

    # Final comparison
    print(f"\n\n{'=' * 72}")
    print("COMPARISON")
    print(f"{'=' * 72}")

    h_rate = h_total_lsr / h_n if h_n > 0 else 0
    l_rate = l_total_lsr / l_n if l_n > 0 else 0

    print(f"\n  {'Metric':<35} {'Human (n={h_n})':<20} {'LLM (n={l_n})':<20}")
    print(f"  {'-'*70}")
    print(f"  {'Total LSR candidates':<35} {h_total_lsr:<20} {l_total_lsr:<20}")
    print(f"  {'Mean LSR per passage':<35} {h_rate:<20.3f} {l_rate:<20.3f}")
    print(f"  {'Passages with LSR > 0':<35} {h_flagged:<20} {l_flagged:<20}")
    print(f"  {'% passages flagged':<35} {100*h_flagged/h_n:<20.1f} {100*l_flagged/l_n:<20.1f}")
    print(f"  {'Total personifications':<35} {h_total_pers:<20} {l_total_pers:<20}")

    # Ratio
    if h_rate > 0 and l_rate > 0:
        print(f"\n  LLM-to-Human ratio: {l_rate/h_rate:.1f}x")
    elif h_rate == 0 and l_rate > 0:
        print(f"\n  Human rate: ZERO. LLM rate: {l_rate:.3f}. Clean separation.")
    else:
        print(f"\n  Both rates near zero.")

    # Save
    outfile = "lsr_exp8b_results.json"
    with open(outfile, "w") as f:
        json.dump({
            "human_n": h_n, "llm_n": l_n,
            "human_total_lsr": h_total_lsr, "llm_total_lsr": l_total_lsr,
            "human_flagged": h_flagged, "llm_flagged": l_flagged,
            "human_rate": h_rate, "llm_rate": l_rate,
            "results": all_results,
        }, f, indent=2)
    print(f"\nResults saved to {outfile}")


if __name__ == "__main__":
    run_experiment()
