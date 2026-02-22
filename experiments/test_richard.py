import sys
sys.path.insert(0, '/sessions/wizardly-optimistic-bohr/mnt/Ribbonworld')
from lsr_detector_v2 import detect_lsr, RICHARD_PASSAGES

print("RICHARD'S 5 HAND-WRITTEN PASSAGES")
print("=" * 60)

total_lsr = 0
flagged = 0
for domain, text in RICHARD_PASSAGES.items():
    result = detect_lsr(text, domain)
    lsr = len(result['lsr_candidates'])
    total_lsr += lsr
    if lsr > 0:
        flagged += 1
    flag = " ***" if lsr > 0 else ""
    print(f"\n  {domain:<24} LSR={lsr}  pers={len(result['personifications'])}  lit={result['literal_filtered']}{flag}")
    for c in result['lsr_candidates']:
        pers = " [pers]" if c.get("is_personification") else ""
        fields = ", ".join(c["register_fields"])
        print(f"    '{c['word']}' [{fields}]{pers}")
        sent = c["sentence"][:120]
        print(f'    "{sent}"')

print(f"\n  TOTAL: {total_lsr} LSR across 5 passages ({total_lsr/5:.2f}/passage)")
print(f"  Passages flagged: {flagged}/5")
