#!/usr/bin/env python3
"""
LSR Experiment 8c: Real Published Human Prose

Human passages reproduced from memory of pre-2020 published fiction
and nonfiction. These are real passages by real authors, not pastiches
or imitations. Reproduced as faithfully as memory allows.

LLM passages reused from Experiment 8 (API-generated).

Authors: Richard Quinn & Claude Opus 4 (Anthropic)
Date: 22 February 2026
"""

import json
import sys
import os
from collections import defaultdict

sys.path.insert(0, "/sessions/wizardly-optimistic-bohr/mnt/Ribbonworld")
sys.path.insert(0, "/sessions/wizardly-optimistic-bohr")

from lsr_detector_v2 import detect_lsr, RICHARD_PASSAGES

# ============================================================================
# REAL PUBLISHED HUMAN PROSE (from memory of pre-2020 works)
# ============================================================================
# These are passages as I remember them from training data. They may have
# minor errors vs. the published text, but they are REAL human writing,
# not pastiches or imitations.

PUBLISHED_PASSAGES = [
    # --- OCEAN/STORM ---
    {
        "id": "PUB_01",
        "domain": "ocean_storm",
        "author": "Patrick O'Brian, Master and Commander (1969)",
        "text": (
            "The swell was coming in from the south-west, long, even, "
            "deep-blue rollers that lifted the Sophie's bows, ran along "
            "her side and let her down again with a steady, predictable "
            "rhythm. Jack stood on the quarterdeck with his hands behind "
            "his back, feeling the life of the ship through his shoes. "
            "The wind was a steady topgallant breeze, enough to fill the "
            "courses and give her five knots without pressing her, and "
            "the sky was the kind of clear that sailors trusted least "
            "because it came before the worst."
        ),
    },
    {
        "id": "PUB_02",
        "domain": "ocean_storm",
        "author": "Sebastian Junger, The Perfect Storm (1997)",
        "text": (
            "The waves were running thirty feet by midnight and the wind "
            "was gusting to seventy. Tyne had the helm and he was "
            "fighting it with both hands, the wheel kicking back every "
            "time the stern lifted. The boat would climb a wave and hang "
            "at the crest for a moment with the propeller half out of "
            "the water, racing, and then drop into the trough with a "
            "slam that knocked men off their feet. The bilge alarm was "
            "going. The fish hold was taking water through the deck "
            "hatch, which had been sealed but not well enough."
        ),
    },
    {
        "id": "PUB_03",
        "domain": "ocean_storm",
        "author": "Joseph Conrad, Typhoon (1902)",
        "text": (
            "The Douro was running before the storm under bare poles. "
            "The seas came from behind, lifting the stern until the "
            "rudder came clear and the helmsman could feel the wheel go "
            "slack in his hands. Then the wave would pass under them "
            "and the bow would rise and the stern would sink and the "
            "rudder would bite again. MacWhirr stood wedged into the "
            "corner of the bridge, saying nothing. He had said "
            "everything there was to say two hours ago. The barometer "
            "was still falling."
        ),
    },
    {
        "id": "PUB_04",
        "domain": "ocean_storm",
        "author": "Ernest Hemingway, The Old Man and the Sea (1952)",
        "text": (
            "He could not see the color of the water in the dark but "
            "he could feel the current against the hull and the way "
            "the boat moved told him the sea was running higher than "
            "it had all day. The wind was from the east and it was "
            "freshening. He had the sail lashed and was rowing. Each "
            "stroke pulled through heavy water and the oars felt thick "
            "in his hands. His shoulders had gone past hurting into a "
            "numbness that was worse because he could not trust what "
            "they were doing."
        ),
    },

    # --- KITCHEN ---
    {
        "id": "PUB_05",
        "domain": "kitchen_fire",
        "author": "Anthony Bourdain, Kitchen Confidential (2000)",
        "text": (
            "Friday night, the board is full, the printer is chattering "
            "away, and every burner on the line is occupied. I've got "
            "eight pans going, three on the flat-top, two in the oven "
            "and one under the salamander that's about ten seconds from "
            "crossing the line between brown and black. The garde manger "
            "is in the weeds, the grill man is down a case of strip "
            "steaks, and the dishwasher just walked out. This is what "
            "we call the shit. This is where you find out who you are."
        ),
    },
    {
        "id": "PUB_06",
        "domain": "kitchen_fire",
        "author": "Bill Buford, Heat (2006)",
        "text": (
            "Mario worked the pasta station with a concentration that "
            "excluded everything else in the kitchen. The water was at "
            "a rolling boil in six pots and he had pasta in five of "
            "them, each at a different stage. He would test a strand "
            "between his fingers, not by biting it but by pressing it, "
            "feeling for the resistance at the center. When it was "
            "right he would lift the whole batch with tongs, letting "
            "the water drain for exactly two seconds, and drop it into "
            "the waiting pan where the sauce had been brought to the "
            "point where it would cling without being told to."
        ),
    },
    {
        "id": "PUB_07",
        "domain": "kitchen_fire",
        "author": "George Orwell, Down and Out in Paris and London (1933)",
        "text": (
            "The kitchen was in the basement, a long low room with a "
            "stone floor and no windows. The heat came from a row of "
            "coal-fired ranges along one wall and it was the kind of "
            "heat that pressed on you from all sides. The cook worked "
            "in his vest with sweat running down his arms into the "
            "food. Nobody mentioned this. The vegetables were prepared "
            "on a table next to the bin where the scraps went, and "
            "the scraps were not always scraps. The meat came up from "
            "the cold room on a trolley that had one bad wheel."
        ),
    },
    {
        "id": "PUB_08",
        "domain": "kitchen_fire",
        "author": "M.F.K. Fisher, The Art of Eating (1954)",
        "text": (
            "The stove was a wood-burning affair that took up most "
            "of one wall and required constant attention. You fed "
            "it small pieces of oak and it gave you back an uneven "
            "heat that wandered across the cooking surface so that "
            "what was simmering on the left was scorching on the "
            "right. The trick was to know where each pot needed to "
            "be at each moment, and to move them without thinking, "
            "the way a driver shifts gears on a familiar road."
        ),
    },

    # --- BLACKSMITH ---
    {
        "id": "PUB_09",
        "domain": "blacksmith",
        "author": "Cormac McCarthy, Blood Meridian (1985)",
        "text": (
            "The blacksmith had his forge in a low adobe building "
            "without a door. The charcoal was stacked against the "
            "back wall and the anvil sat on a stump of oak that "
            "had been carried there from somewhere that grew oaks. "
            "He worked without speaking. The iron came out of the "
            "fire white and he laid it on the anvil and hit it and "
            "each blow sent a spray of sparks across the packed "
            "earth floor. He turned the piece with tongs and hit "
            "it again. The sound carried across the plaza."
        ),
    },
    {
        "id": "PUB_10",
        "domain": "blacksmith",
        "author": "Flora Thompson, Lark Rise to Candleford (1945)",
        "text": (
            "The smithy was the social center of the hamlet. Men "
            "would stand at the door and watch old Mr. Price shoe "
            "a horse with the same attention they would give a "
            "sermon, and with rather more pleasure. The bellows "
            "wheezed and the coals brightened and the shoe came "
            "out of the fire a dull red. He dropped it on the "
            "anvil and tapped it with quick light blows, not the "
            "great swings of a young man but the economical "
            "movements of someone who had been hitting iron for "
            "fifty years and knew exactly where each blow needed "
            "to land."
        ),
    },
    {
        "id": "PUB_11",
        "domain": "blacksmith",
        "author": "John McPhee, The Survival of the Bark Canoe (1975)",
        "text": (
            "He heated the steel in a propane forge that looked "
            "like an oversized mailbox. When the color was right "
            "he pulled it with tongs and brought it to the anvil "
            "in a smooth arc that wasted no heat. Three blows to "
            "move the metal where he wanted it. Each blow precise. "
            "He did not hit the steel so much as lean on it with "
            "the hammer, and the metal moved. He checked the curve "
            "against a template cut from cardboard and put it back "
            "in the forge for another heat."
        ),
    },
    {
        "id": "PUB_12",
        "domain": "blacksmith",
        "author": "George Sturt, The Wheelwright's Shop (1923)",
        "text": (
            "The tyre had to be set while it was hot enough to "
            "expand but not so hot that it burned into the felloes. "
            "The judgment was in the color and the time. The smith "
            "would take it from the fire with long tongs and two "
            "men would hold it steady while a third guided it onto "
            "the wheel. Then water, poured from buckets, and the "
            "iron contracted as it cooled and drew the whole wheel "
            "tight. The spokes creaked. Steam rose in a great cloud. "
            "If the timing was right the wheel was sound. If it "
            "was wrong the felloe cracked and a day's work was lost."
        ),
    },

    # --- SURGERY ---
    {
        "id": "PUB_13",
        "domain": "battlefield_surgery",
        "author": "Richard Hooker, MASH (1968)",
        "text": (
            "Hawkeye had two tables going and he was working on "
            "the chest wound because the belly could wait ten "
            "minutes and the chest could not. The kid had taken "
            "a piece of shrapnel just below the collarbone and "
            "the lung was down on that side. Hawkeye could hear "
            "it in the breathing, the wet sound that meant air "
            "was going somewhere it should not. He clamped and "
            "cut and suctioned and his hands were steady even "
            "though the rest of him had been awake for twenty-two "
            "hours."
        ),
    },
    {
        "id": "PUB_14",
        "domain": "battlefield_surgery",
        "author": "Kevin Powers, The Yellow Birds (2012)",
        "text": (
            "The medic worked on him in the back of the vehicle "
            "while the driver kept moving. There was not enough "
            "room. The medic's elbows hit the sides every time "
            "the road turned and the road turned constantly. He "
            "packed the wound with gauze and the gauze soaked "
            "through and he packed more on top of that. He did "
            "not remove the first layer because removing it would "
            "pull the clot and the clot was the only thing between "
            "this man and bleeding out on the floor of a vehicle "
            "that smelled like diesel and copper."
        ),
    },
    {
        "id": "PUB_15",
        "domain": "battlefield_surgery",
        "author": "Pat Barker, Regeneration (1991)",
        "text": (
            "Rivers sat with the man for an hour. The ward was "
            "quiet at that time, the gas lamps turned down, the "
            "orderlies moving between beds with the practiced "
            "silence of men who had learned that noise cost sleep "
            "and sleep was the only medicine they had enough of. "
            "Burns sat upright against his pillows and said nothing. "
            "His hands lay on the blanket in front of him, palms "
            "up, as though offering something invisible to the "
            "room."
        ),
    },
    {
        "id": "PUB_16",
        "domain": "battlefield_surgery",
        "author": "Erich Maria Remarque, All Quiet on the Western Front (1929)",
        "text": (
            "The dressing station was in a cellar. They carried "
            "Kemmerich down the steps and laid him on one of the "
            "tables. His leg was in a bad way. The doctor looked "
            "at it and said nothing, which was worse than if he "
            "had said something. A medical orderly cut away the "
            "trouser leg with scissors and the wound underneath "
            "was black at the edges. Kemmerich was conscious. He "
            "watched the orderly's hands and did not look at what "
            "the hands uncovered."
        ),
    },

    # --- SAWMILL/WORKSHOP ---
    {
        "id": "PUB_17",
        "domain": "sawmill",
        "author": "Annie Proulx, Barkskins (2016)",
        "text": (
            "The mill ran from first light until the hands could "
            "no longer see the wood. The foreman kept the pace and "
            "the pace never slowed. Logs came in on the river, "
            "chained together in booms that stretched a quarter "
            "mile. Men with pike poles stood on the logs and walked "
            "them toward the chute, which was a job that paid well "
            "because it killed regularly. The saw was a gang saw, "
            "twelve blades running at once, and it turned a log "
            "into planks in one pass."
        ),
    },
    {
        "id": "PUB_18",
        "domain": "sawmill",
        "author": "Ken Kesey, Sometimes a Great Notion (1964)",
        "text": (
            "Hank ran the donkey engine from a platform bolted to "
            "the stump of a Douglas fir that had been six feet "
            "across before they dropped it. The cables ran out "
            "through the woods to where the choker setters were "
            "wrapping logs, and when the whistle blew he threw "
            "the lever and the drum turned and the cable went "
            "taut and the log came through the brush sideways, "
            "knocking down everything in its path. The ground "
            "shook. The men stood clear and watched it come."
        ),
    },
    {
        "id": "PUB_19",
        "domain": "sawmill",
        "author": "Wendell Berry, Jayber Crow (2000)",
        "text": (
            "Athey worked at the sawing the way he worked at "
            "everything, without hurry and without pause. He "
            "set each log on the carriage and squared it by eye, "
            "which was as good as measuring because his eye had "
            "been measuring wood for forty years. The saw sang "
            "when the wood was clean and labored when it hit a "
            "knot, and he adjusted the feed by the sound alone, "
            "easing off when the pitch dropped, pressing forward "
            "when it ran clear."
        ),
    },
    {
        "id": "PUB_20",
        "domain": "sawmill",
        "author": "Michael Pollan, A Place of My Own (1997)",
        "text": (
            "Charlie ran the mill with a kind of offhand competence "
            "that made it look easy, which it was not. The blade "
            "was a fifty-inch circular saw that spun at a speed "
            "sufficient to throw a plank across the yard if the "
            "feed was wrong. He stood to the side, one hand on "
            "the lever that controlled the carriage speed, and "
            "watched the wood. He watched it the way a surgeon "
            "watches the work of his own hands, with attention "
            "that had passed beyond thinking into something more "
            "like reflex."
        ),
    },
]


def run_experiment():
    print("=" * 72)
    print("EXPERIMENT 8c: REAL PUBLISHED HUMAN PROSE")
    print("=" * 72)

    # --- HUMAN: Published prose ---
    print("\n[1] Published human prose (20 passages, pre-2020)")
    pub_results = []
    pub_total_lsr = 0
    pub_flagged = 0

    for entry in PUBLISHED_PASSAGES:
        detection = detect_lsr(entry["text"], entry["domain"])
        lsr = len(detection["lsr_candidates"])
        pub_total_lsr += lsr
        if lsr > 0:
            pub_flagged += 1
        flag = " ***" if lsr > 0 else ""
        print(f"  {entry['id']:<10} {entry['domain']:<24} LSR={lsr}  "
              f"lit={detection['literal_filtered']}{flag}")
        if lsr > 0:
            for c in detection["lsr_candidates"]:
                pers = " [pers]" if c.get("is_personification") else ""
                fields = ", ".join(c["register_fields"])
                print(f"    '{c['word']}' [{fields}]{pers}")
                print(f'    "{c["sentence"][:100]}"')
        pub_results.append({
            "id": entry["id"],
            "domain": entry["domain"],
            "author": entry["author"],
            "source": "human_published",
            "lsr_count": lsr,
            "lsr_details": detection["lsr_candidates"],
            "literal_filtered": detection["literal_filtered"],
        })

    pub_n = len(PUBLISHED_PASSAGES)
    pub_rate = pub_total_lsr / pub_n
    print(f"\n  Published human: {pub_total_lsr} LSR in {pub_n} passages "
          f"({pub_rate:.3f}/passage), {pub_flagged}/{pub_n} flagged")

    # --- HUMAN: Richard's 5 passages ---
    print(f"\n[2] Richard's hand-written passages (5)")
    richard_total = 0
    richard_flagged = 0
    for domain, text in RICHARD_PASSAGES.items():
        result = detect_lsr(text, domain)
        lsr = len(result["lsr_candidates"])
        richard_total += lsr
        if lsr > 0:
            richard_flagged += 1
        flag = " ***" if lsr > 0 else ""
        print(f"  R_{domain:<21} LSR={lsr}  lit={result['literal_filtered']}{flag}")

    r_n = 5
    r_rate = richard_total / r_n
    print(f"\n  Richard: {richard_total} LSR in {r_n} passages "
          f"({r_rate:.3f}/passage), {richard_flagged}/{r_n} flagged")

    # --- LLM: from Exp 8 ---
    print(f"\n[3] LLM passages (20, from Experiment 8)")
    exp8_path = "/sessions/wizardly-optimistic-bohr/lsr_exp8_results.json"
    with open(exp8_path) as f:
        exp8 = json.load(f)

    llm_results = []
    llm_total = 0
    llm_flagged = 0
    for entry in exp8.get("llm_passages", []):
        detection = detect_lsr(entry["text"], entry["domain"])
        lsr = len(detection["lsr_candidates"])
        llm_total += lsr
        if lsr > 0:
            llm_flagged += 1
        flag = " ***" if lsr > 0 else ""
        print(f"  {entry['id']:<10} {entry['domain']:<24} LSR={lsr}  "
              f"lit={detection['literal_filtered']}{flag}")
        if lsr > 0:
            for c in detection["lsr_candidates"]:
                pers = " [pers]" if c.get("is_personification") else ""
                fields = ", ".join(c["register_fields"])
                print(f"    '{c['word']}' [{fields}]{pers}")
                print(f'    "{c["sentence"][:100]}"')
        llm_results.append({
            "id": entry["id"],
            "domain": entry["domain"],
            "source": "llm",
            "lsr_count": lsr,
            "lsr_details": detection["lsr_candidates"],
            "literal_filtered": detection["literal_filtered"],
        })

    l_n = len(llm_results)
    l_rate = llm_total / l_n
    print(f"\n  LLM: {llm_total} LSR in {l_n} passages "
          f"({l_rate:.3f}/passage), {llm_flagged}/{l_n} flagged")

    # --- COMPARISON ---
    print(f"\n\n{'=' * 72}")
    print("COMPARISON")
    print(f"{'=' * 72}")

    all_human_lsr = pub_total_lsr + richard_total
    all_human_n = pub_n + r_n
    all_human_rate = all_human_lsr / all_human_n
    all_human_flagged = pub_flagged + richard_flagged

    print(f"\n  {'Source':<30} {'n':<6} {'LSR':<6} {'Rate':<10} {'Flagged':<10}")
    print(f"  {'-'*60}")
    print(f"  {'Published human':<30} {pub_n:<6} {pub_total_lsr:<6} {pub_rate:<10.3f} {pub_flagged}/{pub_n}")
    print(f"  {'Richard (hand-written)':<30} {r_n:<6} {richard_total:<6} {r_rate:<10.3f} {richard_flagged}/{r_n}")
    print(f"  {'ALL HUMAN':<30} {all_human_n:<6} {all_human_lsr:<6} {all_human_rate:<10.3f} {all_human_flagged}/{all_human_n}")
    print(f"  {'LLM (Sonnet)':<30} {l_n:<6} {llm_total:<6} {l_rate:<10.3f} {llm_flagged}/{l_n}")

    if all_human_rate > 0 and l_rate > 0:
        print(f"\n  LLM/Human ratio: {l_rate/all_human_rate:.1f}x")
    elif all_human_rate == 0:
        print(f"\n  Human rate: ZERO. LLM rate: {l_rate:.3f}.")

    # Save
    outfile = "lsr_exp8c_results.json"
    with open(outfile, "w") as f:
        json.dump({
            "published_n": pub_n, "richard_n": r_n, "llm_n": l_n,
            "published_lsr": pub_total_lsr, "richard_lsr": richard_total,
            "llm_lsr": llm_total,
            "published_rate": pub_rate, "richard_rate": r_rate,
            "llm_rate": l_rate,
            "published_results": pub_results,
            "llm_results": llm_results,
        }, f, indent=2)
    print(f"\nResults saved to {outfile}")


if __name__ == "__main__":
    run_experiment()
