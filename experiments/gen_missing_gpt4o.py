#!/usr/bin/env python3
"""Generate the 4 missing GPT-4o passages."""
import json, time, urllib.request, urllib.error, sys
sys.path.insert(0, '/sessions/wizardly-optimistic-bohr')
from lsr_detector_v3 import detect_lsr_v3

OPENAI_API_KEY = 'REDACTED_OPENAI_KEY'

PROMPTS = {
    'kitchen_fire': 'Write a 150-200 word passage about working in a busy restaurant kitchen during the dinner rush. Use past tense, third person. Focus on physical details: the heat, the equipment, the cook\'s actions. No dialogue tags.',
    'battlefield_surgery': 'Write a 150-200 word passage about a field surgeon treating wounded soldiers during a battle. Use past tense, third person. Focus on physical details: the wounds, the instruments, the surgeon\'s actions. No dialogue tags.',
    'blacksmith': 'Write a 150-200 word passage about a blacksmith forging a blade. Use past tense, third person. Focus on physical details: the forge, the metal, the smith\'s actions. No dialogue tags.',
}

MISSING = [
    ('gpt4o_kit_4', 'kitchen_fire'),
    ('gpt4o_bat_2', 'battlefield_surgery'),
    ('gpt4o_bat_4', 'battlefield_surgery'),
    ('gpt4o_bla_3', 'blacksmith'),
]

def generate_openai(prompt):
    data = json.dumps({'model': 'gpt-4o', 'messages': [{'role': 'user', 'content': prompt}], 'max_tokens': 400, 'temperature': 1.0}).encode()
    headers = {'Content-Type': 'application/json', 'Authorization': f'Bearer {OPENAI_API_KEY}'}
    for attempt in range(3):
        try:
            req = urllib.request.Request('https://api.openai.com/v1/chat/completions', data=data, headers=headers)
            with urllib.request.urlopen(req, timeout=120) as response:
                result = json.loads(response.read())
                return result['choices'][0]['message']['content']
        except Exception as e:
            print(f'  Attempt {attempt+1} failed: {e}', flush=True)
            if attempt < 2:
                time.sleep(22)
    return None

def clean_text(text):
    text = text.replace('**', '').replace('##', '').replace('# ', '').strip()
    lines = text.split('\n')
    content_lines = []
    started = False
    for line in lines:
        l = line.strip()
        if not started:
            if l and not l.lower().startswith('here') and not l.lower().startswith('sure') and not l.startswith('#') and not l.startswith('---'):
                started = True
                content_lines.append(l)
        else:
            if l:
                content_lines.append(l)
    return ' '.join(content_lines)

new_passages = []
for pid, domain in MISSING:
    print(f'Generating {pid}...', flush=True)
    text = generate_openai(PROMPTS[domain])
    if text is None:
        print(f'  FAILED!', flush=True)
        continue
    text = clean_text(text)
    wc = len(text.split())
    print(f'  OK ({wc} words)', flush=True)

    result = detect_lsr_v3(text, domain)
    n_orphaned = len(result['orphaned'])
    n_earned = len(result['earned'])

    entry = {
        'id': pid,
        'domain': domain,
        'model': 'gpt-4o',
        'text': text,
        'orphaned': n_orphaned,
        'earned': n_earned,
        'literal_filtered': result['literal_filtered'],
        'orphan_details': [
            {'word': o['word'], 'score': o['orphan_score'],
             'fields': o['register_fields'],
             'sentence': o['sentence'][:120]}
            for o in result['orphaned']
        ],
        'earned_details': [
            {'word': e['word'], 'score': e['orphan_score'],
             'fields': e['register_fields']}
            for e in result['earned']
        ],
    }
    new_passages.append(entry)

    if n_orphaned > 0:
        for o in result['orphaned']:
            fields = ', '.join(o['register_fields'])
            print(f'  >>> ORPHANED: "{o["word"]}" score={o["orphan_score"]:.2f} [{fields}]', flush=True)
    else:
        print(f'  No orphans detected', flush=True)

    time.sleep(22)  # Rate limit

with open('/sessions/wizardly-optimistic-bohr/gpt4o_missing_4.json', 'w') as f:
    json.dump(new_passages, f, indent=2)
print(f'\nGenerated {len(new_passages)} passages')
