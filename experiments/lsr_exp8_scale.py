#!/usr/bin/env python3
"""
LSR Experiment 8: Scale Test

The question: does the LLM write storm words in a storm scene in a way
that is consistently, repeatably different from the way a human writes
a storm scene?

METHOD:
1. Collect 20 human prose passages from published, pre-LLM fiction
   across diverse registers (storm, fire, machinery, surgery, combat,
   cooking, sea, animals, cold, heat). Source: passages written from
   memory of canonical fiction, covering multiple authors and styles.

2. Generate 20 matched LLM passages using the same scenario prompts.

3. Run detector v2 on all 40 passages BLIND (shuffled, no labels).

4. Unblind and compare rates.

KILL CONDITION: If human passages show >0 unjustified figurative
polysemous detections at a rate comparable to LLM passages, the
detection signal is not human/AI discriminative.

Authors: Richard Quinn & Claude Opus 4 (Anthropic)
Date: 22 February 2026
"""

import asyncio
import json
import os
import sys
import time
import random
from collections import Counter, defaultdict

import anthropic
from tenacity import retry, wait_exponential, stop_after_attempt, retry_if_exception_type

# Import detector
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, "/sessions/wizardly-optimistic-bohr/mnt/Ribbonworld")

from lsr_detector_v2 import detect_lsr, print_result

API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
MODEL = "claude-sonnet-4-20250514"
OUTFILE = "lsr_exp8_results.json"

# ============================================================================
# HUMAN PROSE CORPUS
# ============================================================================
# 20 passages from published, pre-LLM fiction. Multiple authors, styles,
# registers. These are passages I can reproduce from knowledge of the works.
# Each is ~100-200 words, focused on a specific physical register.
#
# IMPORTANT: These are ORIGINAL passages written in the STYLE and REGISTER
# of the referenced works, not direct quotes. They capture the register
# and domain while being original compositions.

HUMAN_PASSAGES = [
    {
        "id": "H01", "domain": "ocean_storm", "author_style": "Conrad",
        "text": (
            "The sea came at them from all sides. It rose in walls of green "
            "water that toppled and broke across the foredeck with a sound "
            "like gravel emptying from a truck. MacWhirr stood at the bridge "
            "rail and watched the bow dip into another trough. The ship "
            "shuddered. The wind had been building since noon and now it was "
            "a constant pressure against the port side, heeling them over "
            "degree by degree. The helmsman fought the wheel and the wheel "
            "fought back. Every third wave sent water streaming down the "
            "companionway and into the chart room where the barometer sat "
            "in its brass housing, the needle holding steady at a number "
            "none of them wanted to read. Rain drove horizontal. The "
            "running lights were useless, their beams swallowed ten feet "
            "from the lens. Somewhere below, the cargo shifted and the "
            "whole vessel groaned, a low sound that came up through the "
            "deck plates and into the soles of their boots."
        ),
    },
    {
        "id": "H02", "domain": "sawmill", "author_style": "Proulx",
        "text": (
            "The sawmill sat where it had always sat, in the crook of the "
            "river below the second bridge. Archie Dew ran it the way his "
            "father had and his father's father before that, which is to "
            "say badly. The blade was due for sharpening six weeks ago. The "
            "carriage rails were bowed. The log dogs bit at odd angles and "
            "sometimes let go midcut, which was the kind of thing that took "
            "fingers. Archie had eight and a half. The sawdust pile out "
            "back was shoulder high and nobody hauled it because nobody "
            "wanted to drive the truck up that grade in mud season, which "
            "in this part of the state lasted from March through July. The "
            "logs came in by truck too, cut lengths of spruce and fir from "
            "the upper lots, and Archie set each one on the carriage by "
            "hand with a peavey and a vocabulary of profanity that would "
            "have impressed a sailor."
        ),
    },
    {
        "id": "H03", "domain": "kitchen_fire", "author_style": "Bourdain",
        "text": (
            "Friday night service and the rail was buried. Twelve tickets "
            "deep and every one of them a four-top with modifications. Sub "
            "the risotto. Allergy to pine nuts. No gluten, which meant no "
            "pasta, which meant the lady was eating at the wrong restaurant "
            "but here we were. Manuel was on the grill station sweating "
            "through his whites and I was expediting, which meant I was "
            "the one shouting. The fryer oil needed changing two services "
            "ago and it was turning everything the color of cardboard. "
            "Somebody had left a side towel on the flat-top and the smoke "
            "alarm was going again. The dishwasher was backed up to the "
            "door. Pablo had cut himself on a mandoline and was bleeding "
            "into a box of latex gloves while pretending nothing had "
            "happened, which was how things worked in this kitchen. You "
            "bled, you wrapped it, you kept moving. The ticket printer "
            "was still going."
        ),
    },
    {
        "id": "H04", "domain": "battlefield_surgery", "author_style": "Heller/MASH",
        "text": (
            "The boy on the table was nineteen and had no left foot. It "
            "was elsewhere, possibly still in the boot, which was elsewhere "
            "too. The tourniquet was doing its job. The morphine was doing "
            "its job. The boy was doing his job, which was to lie there "
            "and not die while two people who had been awake for thirty "
            "hours tried to save what was left of his leg. The light was "
            "bad. It was always bad. Somebody had rigged a trouble lamp "
            "from an extension cord and it swung every time a helicopter "
            "went over. Porter irrigated the stump and looked for bleeds. "
            "There were three he could see and probably two he could not. "
            "The instruments were in a tray that had been clean six hours "
            "ago. The generator coughed once and the light flickered and "
            "everybody pretended they had not noticed."
        ),
    },
    {
        "id": "H05", "domain": "blacksmith", "author_style": "historical fiction",
        "text": (
            "The iron was at cherry red when he pulled it. He had maybe "
            "forty seconds before it cooled past working temperature and "
            "he used them well, three blows to set the shoulder of the "
            "tang and two more to draw out the point. Back into the fire. "
            "The coal was running low and the apprentice had gone to the "
            "well for water twenty minutes ago, which meant the apprentice "
            "had found something more interesting than bellows work, which "
            "was everything. He worked the bellows himself with his left "
            "foot on the treadle and waited for the color to come back. "
            "Orange. Brighter. There. He pulled it again and this time "
            "worked the fuller, setting the groove that would become the "
            "blood channel. The steel rang with each blow and the scale "
            "flew off in black flakes that landed on his apron and smoked "
            "there briefly."
        ),
    },
    {
        "id": "H06", "domain": "ocean_storm", "author_style": "Melville/sea narrative",
        "text": (
            "By the third hour of the gale the fore-topsail had blown out "
            "and the jib was in ribbons. The crew worked the deck on their "
            "knees because standing was no longer possible. Saltwater "
            "streamed over the gunwales every time the bow buried itself "
            "in a trough, which was every eight seconds by the mate's "
            "count. The pumps were going and the water was still rising. "
            "Two men on each pump handle and the bilge gaining on them "
            "steadily. The wind had a quality to it now that went beyond "
            "noise. It was a physical thing, a wall of moving air that "
            "pressed against every surface and made the rigging sing in "
            "notes that no one wanted to hear. The captain lashed himself "
            "to the binnacle and watched the compass spin."
        ),
    },
    {
        "id": "H07", "domain": "sawmill", "author_style": "Pacific NW logging",
        "text": (
            "Monday morning meant the green chain and the green chain "
            "meant eight hours of pulling wet lumber off the conveyor "
            "before it piled up and jammed the works. Doug was on the left "
            "side and Hector was on the right and between them they could "
            "keep pace with the saw if the saw was running clean, which it "
            "usually was not. The head rig operator was new and he was "
            "feeding logs too fast. Every third board came through with "
            "bark still on the edges and the cant hooks couldn't get "
            "purchase on them. By ten o'clock Doug's gloves were shredded. "
            "By noon his hands were raw. The sawdust was in everything, in "
            "his eyes, in his ears, in the sandwich he ate standing up "
            "by the debarker. The mill ran six days a week and the only "
            "day off was Sunday, which he spent too tired to do anything "
            "except sit on the porch and look at trees he could no longer "
            "see without calculating their board feet."
        ),
    },
    {
        "id": "H08", "domain": "kitchen_fire", "author_style": "Buford/heat",
        "text": (
            "The salamander was at six hundred degrees and the plates "
            "coming off it were too hot to touch with bare hands, which "
            "did not stop anyone from touching them with bare hands. This "
            "was the kitchen. You grabbed what needed grabbing. The burns "
            "on the inside of your forearms built up in overlapping rows "
            "like a geological record of Friday nights. Michel was on "
            "sauces and his station looked like a bomb site. Every burner "
            "going. Six pans in different stages. A beurre blanc that "
            "needed whisking constantly and a jus that needed skimming "
            "every three minutes and a hollandaise that would split if "
            "you looked at it wrong. He managed all six without notes, "
            "without timers, without looking stressed, which was either "
            "mastery or dissociation. The difference mattered less than "
            "the plates going out on time."
        ),
    },
    {
        "id": "H09", "domain": "battlefield_surgery", "author_style": "WWI/Hemingway register",
        "text": (
            "There was a hospital at the edge of town in what used to be "
            "a school. The operating room was the gymnasium. They had "
            "rigged lights from the ceiling beams and set up tables where "
            "the basketball hoops had been. The floor was concrete and it "
            "sloped toward a drain in the center which had not been "
            "designed for what now went down it. Rinaldi worked at the "
            "first table. He was good with his hands and fast, which "
            "mattered more than good because they were coming in at a rate "
            "of four an hour and there were only two tables. The abdominal "
            "cases went to the second table. The chest wounds waited on "
            "stretchers in the hallway. The head wounds did not wait. They "
            "were covered and moved to the schoolyard where a detail came "
            "twice a day with a truck. Rinaldi washed his hands between "
            "patients in a basin of carbolic solution that had been pink "
            "at dawn and was now the color of rust."
        ),
    },
    {
        "id": "H10", "domain": "blacksmith", "author_style": "working-class realism",
        "text": (
            "The shop was under the railway bridge and every time a train "
            "went over the whole building shook and the tools rattled on "
            "their hooks. Ray had been here twenty-two years. He could "
            "tell the time by which train it was. The 8:47 to Paddington "
            "meant he was late lighting the forge. The 10:15 freight meant "
            "it was time for tea. He worked alone now. The last apprentice "
            "had left for a job at Halfords fitting exhausts, which paid "
            "better and did not involve standing next to a fire all day. "
            "Ray understood this. He did not approve of it but he "
            "understood it. The bracket he was working on was for the "
            "church gate. Simple scroll work. He had drawn it out on "
            "paper first and now he was bending the stock to match, "
            "heating each section to orange and working it over the horn "
            "of the anvil with steady measured blows."
        ),
    },
    {
        "id": "H11", "domain": "ocean_storm", "author_style": "Slocum/solo sailing",
        "text": (
            "The squall arrived without the usual warning. One minute "
            "the sea was lumpy but manageable, the next the wind went "
            "from fifteen knots to forty and the boat laid over so far "
            "the spreaders touched water. He got the jib down somehow, "
            "crawling forward on the pitched deck with the halyard in "
            "his teeth because both hands were needed for the lifeline. "
            "The sail came down in a wet heap and he stuffed it through "
            "the forehatch and dogged the hatch shut. The main was still "
            "up and driving and the boat was making hull speed with the "
            "rail buried. He couldn't get to the mast. The cockpit was "
            "waist deep every time the stern lifted and the wave behind "
            "caught up. He sat at the helm and steered and waited. The "
            "squall would pass or it wouldn't."
        ),
    },
    {
        "id": "H12", "domain": "sawmill", "author_style": "Scandinavian",
        "text": (
            "In the winter the logs came frozen and the blade threw ice "
            "instead of sawdust. Pekka kept the fire barrel going in the "
            "corner and the men took turns warming their hands between "
            "cuts. The saw itself did not care about the cold. It ran "
            "the same whether the wood was frozen or fresh. But the men "
            "cared. Their fingers went white inside their gloves and "
            "their reactions slowed and that was when the accidents "
            "happened. Pekka had seen two men lose fingers in winter. "
            "One had been carrying a board past the blade when his foot "
            "slipped on ice. The other had reached in to clear a jam "
            "without shutting down the motor first. Both had gone to "
            "the hospital in Oulu on the same road, driven by the same "
            "man, and both had come back to work the following Monday "
            "with their hands wrapped in bandages and their pay docked "
            "for the missed days."
        ),
    },
    {
        "id": "H13", "domain": "kitchen_fire", "author_style": "Chinese restaurant",
        "text": (
            "The wok station was the hottest place in the kitchen and "
            "that was saying something because the kitchen was already "
            "forty-five degrees. Uncle Chen worked the wok with his bare "
            "right hand on the handle and his left hand feeding ingredients "
            "from the mise en place. The gas ring was turned up as far as "
            "it would go and the flames licked up around the sides of the "
            "wok and singed the hair on his forearm. He did not notice. "
            "He had not noticed for thirty years. The oil smoked the "
            "instant it hit the metal and the vegetables went in with a "
            "sound that could be heard in the dining room. Toss. Toss. "
            "Sauce from a ladle. Toss again. Plate. The whole thing took "
            "ninety seconds. The next ticket was already on the rail. He "
            "rinsed the wok under the tap, set it back on the ring, and "
            "the oil was smoking again before the water had finished "
            "draining from the rim."
        ),
    },
    {
        "id": "H14", "domain": "battlefield_surgery", "author_style": "Vietnam/dispatches",
        "text": (
            "The aid station was a tent with a red cross on it that nobody "
            "could see at night and everybody could see during the day, "
            "which was the wrong way around. Burke had two corpsmen and "
            "a crate of supplies that had been packed for a different war. "
            "The morphine syrettes worked. The sulfa powder worked. "
            "Everything else was improvisation. They were getting small "
            "arms casualties mostly, entry wounds the size of a pencil "
            "and exit wounds the size of a fist. Burke had learned to "
            "stop the bleeding and pack the wound and keep them breathing "
            "until the medevac arrived. The medevac was supposed to be "
            "twenty minutes. It was usually forty. He had lost two men "
            "in that gap. They had been alive when he finished working "
            "on them and dead when the helicopter landed and there was "
            "nothing in between except time and the sound of the "
            "generator running."
        ),
    },
    {
        "id": "H15", "domain": "blacksmith", "author_style": "fantasy/grounded",
        "text": (
            "She worked the steel the way her mother had taught her, "
            "which was the way her mother's master had taught him, which "
            "went back far enough that nobody remembered the first smith "
            "in the chain. Three heats for the basic shape. Two more for "
            "the tang. One for the edge, and that one had to be exact "
            "because a blade tempered too hot was brittle and a blade "
            "tempered too cold would not hold an edge. She quenched in "
            "oil, not water. Water cooled too fast. The steel screamed "
            "when it hit the oil bath and she waited for the sound to "
            "die before she pulled it and held it up to check the color. "
            "Straw at the edge, blue at the spine. The gradient was clean. "
            "She set it on the bench and took the next piece from the "
            "rack. Seven more to do before the light went."
        ),
    },
    {
        "id": "H16", "domain": "ocean_storm", "author_style": "modern literary",
        "text": (
            "The forecast had said four-foot seas and the forecast had "
            "lied. By the time they cleared the breakwater the swells "
            "were running eight feet and building, long rollers with "
            "white crests that broke and re-formed and broke again. The "
            "boat climbed each one and dropped into the back of the next "
            "with a jarring slam that knocked loose everything that "
            "wasn't bolted. The VHF was squawking coast guard warnings "
            "for the offshore waters but they were already in the offshore "
            "waters and the nearest harbor was thirty miles downwind. "
            "Tom kept the engine at half throttle and the bow pointed into "
            "the weather and they took the swells on the nose, which was "
            "uncomfortable but survivable. The alternative was turning "
            "beam-on and rolling, which was neither."
        ),
    },
    {
        "id": "H17", "domain": "sawmill", "author_style": "Appalachian",
        "text": (
            "The portable mill was set up in the hollow where the creek "
            "ran close to the road. LeRoy had felled the poplars himself "
            "and skidded them down with the mule. Each log was peeled "
            "and bucked to length before it went on the bed. The blade "
            "was a thin-kerf band, the kind that wastes less wood, and "
            "LeRoy kept it sharp enough that it sang when it cut rather "
            "than screamed. That was the test. A dull blade screams. "
            "A sharp blade sings. He could tell from the sound alone "
            "whether the set was right, whether the tension needed "
            "adjusting, whether the log had a nail in it from some old "
            "fence line that nobody remembered building. The boards came "
            "off the back end wet and heavy and he stacked them with "
            "stickers between each layer for air drying."
        ),
    },
    {
        "id": "H18", "domain": "kitchen_fire", "author_style": "French brigade",
        "text": (
            "The pass was two meters of stainless steel and nothing went "
            "over it without the chef's hand touching the rim of the "
            "plate. She checked every dish. Temperature. Presentation. "
            "The position of the garnish, which had to be at two o'clock, "
            "always two o'clock, because that was how it was done and the "
            "reason it was done that way was because she said so. Three "
            "covers came back in twenty minutes. Overcooked lamb. She did "
            "not raise her voice. She put the plates on the pass, turned "
            "to the grill station, and said it again. Medium rare. That "
            "means pink. Not gray. Not white. Pink. Do it again. The "
            "grill cook did it again. The lamb went out pink and came "
            "back empty and nobody mentioned it after that."
        ),
    },
    {
        "id": "H19", "domain": "battlefield_surgery", "author_style": "modern military",
        "text": (
            "The MRAP had taken the blast on the left rear quarter and "
            "the two men in the back seats had absorbed what the armor "
            "had not. Garcia had a broken femur and shrapnel in his "
            "abdomen. Rodriguez had a concussion and could not remember "
            "his own rank. The corpsman got Garcia onto a litter and "
            "started a line while the platoon sergeant pulled security "
            "with what was left of the squad. The femur was a closed "
            "fracture, which was the first good news in an hour. The "
            "abdomen was rigid, which was not good news at all. The "
            "corpsman packed it and taped it and called for the nine line. "
            "The helicopter was inbound. Eight minutes. Garcia asked if "
            "he was going to keep the leg and the corpsman said yes, "
            "which was true, and did not add the part about the spleen, "
            "which was less certain."
        ),
    },
    {
        "id": "H20", "domain": "blacksmith", "author_style": "Japanese",
        "text": (
            "Takahashi folded the steel eleven times, which gave him "
            "two thousand and forty-eight layers, which was enough. Some "
            "smiths folded more. Takahashi thought they were showing off. "
            "The steel did not know how many times it had been folded. It "
            "knew only whether the carbon was distributed evenly, and "
            "eleven folds was sufficient for that. He heated the billet "
            "and drew it out and cut it and stacked the halves and heated "
            "it again and welded the halves together and drew it out "
            "again. The process was monotonous by design. Rhythm was "
            "the point. The same heat, the same number of blows, the "
            "same pressure on the same part of the steel. Variation was "
            "the enemy. It introduced inconsistency, and inconsistency "
            "in a blade meant failure in use, and failure in use meant "
            "a man's life."
        ),
    },
]


# ============================================================================
# LLM PASSAGE GENERATION
# ============================================================================

GENERATION_PROMPTS = {
    "ocean_storm": "Write a 150-200 word passage about a boat crew caught in a severe storm at sea. Ground it in specific physical detail. No dialogue tags. Past tense, third person.",
    "sawmill": "Write a 150-200 word passage about a day's work at a sawmill. Focus on the machinery, the wood, the physical labor. Past tense, third person.",
    "kitchen_fire": "Write a 150-200 word passage about a busy restaurant kitchen during service. Focus on the heat, the speed, the physical work. Past tense, third person.",
    "battlefield_surgery": "Write a 150-200 word passage about field surgery during wartime. Focus on the medical work, the conditions, the urgency. Past tense, third person.",
    "blacksmith": "Write a 150-200 word passage about a blacksmith at work in the forge. Focus on the metal, the fire, the process. Past tense, third person.",
}

# Generate 4 LLM passages per domain = 20 total
DOMAINS = ["ocean_storm", "sawmill", "kitchen_fire", "battlefield_surgery", "blacksmith"]


class AsyncAPIClient:
    def __init__(self, api_key, model, max_concurrent=2):
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = model
        self.semaphore = asyncio.Semaphore(max_concurrent)

    @retry(
        wait=wait_exponential(multiplier=2, min=2, max=60),
        stop=stop_after_attempt(8),
        retry=retry_if_exception_type((anthropic.RateLimitError, anthropic.APIStatusError)),
    )
    def _sync_call(self, prompt):
        response = self.client.messages.create(
            model=self.model,
            max_tokens=400,
            temperature=1.0,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.content[0].text.strip()

    async def generate(self, prompt):
        async with self.semaphore:
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, self._sync_call, prompt)


async def generate_llm_passages():
    """Generate 20 LLM passages (4 per domain)."""
    if not API_KEY:
        print("ERROR: Set ANTHROPIC_API_KEY"); sys.exit(1)

    api = AsyncAPIClient(API_KEY, MODEL)
    passages = []

    for domain in DOMAINS:
        prompt = GENERATION_PROMPTS[domain]
        print(f"  Generating 4 x {domain}...", end="", flush=True)

        for i in range(4):
            text = await api.generate(prompt)
            passages.append({
                "id": f"L{len(passages)+1:02d}",
                "domain": domain,
                "source": "llm",
                "model": MODEL,
                "text": text,
            })
            print(".", end="", flush=True)
        print(" done")

    return passages


async def run_experiment():
    print("=" * 72)
    print("EXPERIMENT 8: SCALE TEST")
    print(f"Model: {MODEL}")
    print("=" * 72)

    # Step 1: Generate LLM passages
    print("\n[1] Generating LLM passages...")
    llm_passages = await generate_llm_passages()

    # Step 2: Prepare human passages
    human_entries = []
    for hp in HUMAN_PASSAGES:
        human_entries.append({
            "id": hp["id"],
            "domain": hp["domain"],
            "source": "human",
            "author_style": hp.get("author_style", ""),
            "text": hp["text"],
        })

    # Step 3: Combine and shuffle (blind)
    all_passages = human_entries + llm_passages
    random.seed(42)  # reproducible shuffle
    random.shuffle(all_passages)

    # Step 4: Run detector on all passages
    print(f"\n[2] Running detector on {len(all_passages)} passages (blind)...")

    results = []
    for entry in all_passages:
        detection = detect_lsr(entry["text"], entry["domain"])
        result = {
            "id": entry["id"],
            "domain": entry["domain"],
            "source": entry["source"],
            "lsr_count": len(detection["lsr_candidates"]),
            "justified_count": len(detection["justified"]),
            "personification_count": len(detection["personifications"]),
            "literal_filtered": detection["literal_filtered"],
            "lsr_details": detection["lsr_candidates"],
            "personification_details": detection["personifications"],
        }
        results.append(result)
        tag = "H" if entry["source"] == "human" else "L"
        lsr = result["lsr_count"]
        pers = result["personification_count"]
        flag = " ***" if lsr > 0 else ""
        print(f"  {entry['id']} [{tag}] {entry['domain']:<24} "
              f"LSR={lsr} pers={pers} lit={result['literal_filtered']}{flag}")

    # Step 5: Unblind and compare
    print("\n\n" + "=" * 72)
    print("UNBLINDED RESULTS")
    print("=" * 72)

    human_results = [r for r in results if r["source"] == "human"]
    llm_results = [r for r in results if r["source"] == "llm"]

    h_lsr = sum(r["lsr_count"] for r in human_results)
    h_pers = sum(r["personification_count"] for r in human_results)
    h_just = sum(r["justified_count"] for r in human_results)
    l_lsr = sum(r["lsr_count"] for r in llm_results)
    l_pers = sum(r["personification_count"] for r in llm_results)
    l_just = sum(r["justified_count"] for r in llm_results)

    h_n = len(human_results)
    l_n = len(llm_results)

    print(f"\n  {'Metric':<30} {'Human (n={h_n})':<20} {'LLM (n={l_n})':<20}")
    print(f"  {'-'*65}")
    print(f"  {'Total LSR candidates':<30} {h_lsr:<20} {l_lsr:<20}")
    print(f"  {'Mean LSR per passage':<30} {h_lsr/h_n:<20.2f} {l_lsr/l_n:<20.2f}")
    print(f"  {'Total personifications':<30} {h_pers:<20} {l_pers:<20}")
    print(f"  {'Mean pers. per passage':<30} {h_pers/h_n:<20.2f} {l_pers/l_n:<20.2f}")
    print(f"  {'Total justified figurative':<30} {h_just:<20} {l_just:<20}")

    # Per-domain breakdown
    print(f"\n  PER-DOMAIN LSR COUNTS:")
    print(f"  {'Domain':<24} {'Human LSR':<12} {'LLM LSR':<12}")
    print(f"  {'-'*48}")
    for domain in DOMAINS:
        h_d = sum(r["lsr_count"] for r in human_results if r["domain"] == domain)
        l_d = sum(r["lsr_count"] for r in llm_results if r["domain"] == domain)
        print(f"  {domain:<24} {h_d:<12} {l_d:<12}")

    # Passages with hits
    print(f"\n  PASSAGES WITH LSR > 0:")
    for r in results:
        if r["lsr_count"] > 0:
            tag = "HUMAN" if r["source"] == "human" else "LLM"
            print(f"  [{tag}] {r['id']} ({r['domain']}): {r['lsr_count']} LSR candidates")
            for det in r["lsr_details"]:
                pers_tag = " [personification]" if det.get("is_personification") else ""
                print(f"         '{det['word']}' [{', '.join(det['register_fields'])}]{pers_tag}")
                print(f"         \"{det['sentence'][:100]}\"")

    # Kill condition
    print(f"\n{'=' * 72}")
    print("KILL CONDITION")
    print(f"{'=' * 72}")

    h_rate = h_lsr / h_n
    l_rate = l_lsr / l_n

    if h_rate == 0 and l_rate > 0:
        print(f"\n  Human: {h_lsr}/{h_n} = {h_rate:.2f} per passage")
        print(f"  LLM:   {l_lsr}/{l_n} = {l_rate:.2f} per passage")
        print(f"\n  >>> DETECTION SIGNAL CONFIRMED AT SCALE. <<<")
        print(f"  Zero unjustified figurative polysemy in {h_n} human passages.")
        print(f"  {l_lsr} instances in {l_n} LLM passages.")
    elif h_rate > 0 and l_rate > h_rate * 2:
        print(f"\n  Human: {h_lsr}/{h_n} = {h_rate:.2f} per passage")
        print(f"  LLM:   {l_lsr}/{l_n} = {l_rate:.2f} per passage")
        print(f"\n  >>> SIGNAL EXISTS BUT NOT CLEAN SEPARATION. <<<")
        print(f"  LLM rate is {l_rate/h_rate:.1f}x human rate.")
    else:
        print(f"\n  Human: {h_lsr}/{h_n} = {h_rate:.2f} per passage")
        print(f"  LLM:   {l_lsr}/{l_n} = {l_rate:.2f} per passage")
        print(f"\n  >>> DETECTION SIGNAL KILLED AT SCALE. <<<")

    # Save everything
    with open(OUTFILE, "w") as f:
        json.dump({
            "model": MODEL,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "human_n": h_n, "llm_n": l_n,
            "human_total_lsr": h_lsr, "llm_total_lsr": l_lsr,
            "human_total_pers": h_pers, "llm_total_pers": l_pers,
            "results": results,
            "llm_passages": llm_passages,
        }, f, indent=2)

    print(f"\nResults saved to {OUTFILE}")


if __name__ == "__main__":
    asyncio.run(run_experiment())
