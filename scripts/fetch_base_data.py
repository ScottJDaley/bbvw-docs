import requests
import json
import os
import re
import time

BASE_URL = "https://pokeapi.co/api/v2"
GEN5_MAX_POKEMON = 649
CACHE_DIR = "scripts/data/cache"

if not os.path.exists(CACHE_DIR):
    os.makedirs(CACHE_DIR)

def get_json(url, cache_name=None):
    if cache_name:
        cache_path = os.path.join(CACHE_DIR, cache_name + ".json")
        if os.path.exists(cache_path):
            with open(cache_path, 'r', encoding='utf-8') as f:
                return json.load(f)
    
    print(f"Fetching {url}...")
    try:
        r = requests.get(url)
        if r.status_code != 200:
            print(f"Error fetching {url}: {r.status_code}")
            return None
        data = r.json()
    except Exception as e:
        print(f"Exception fetching {url}: {e}")
        return None
    
    if cache_name:
        with open(cache_path, 'w', encoding='utf-8') as f:
            json.dump(data, f)
    
    return data

def get_gen5_move_stats(move_data):
    stats = {
        'power': move_data.get('power'),
        'accuracy': move_data.get('accuracy'),
        'pp': move_data.get('pp'),
        'type': move_data['type']['name']
    }
    past_values = move_data.get('past_values', [])
    if not past_values:
        return stats

    def get_v_id(url):
        return int(url.split('/')[-2])

    past_values.sort(key=lambda x: get_v_id(x['version_group']['url']))
    for past in past_values:
        v_id = get_v_id(past['version_group']['url'])
        if v_id > 14:
            if past.get('power') is not None: stats['power'] = past['power']
            if past.get('accuracy') is not None: stats['accuracy'] = past['accuracy']
            if past.get('pp') is not None: stats['pp'] = past['pp']
            if past.get('type') is not None: stats['type'] = past['type']['name']
            break
    return stats

def normalize_item_name(name):
    if not name: return ""
    name = name.lower().strip()
    tm_match = re.match(r'(tm|hm)(\d+)\s*(.*)', name)
    if tm_match:
        return f"{tm_match.group(1)}{int(tm_match.group(2)):02}"
    name = re.sub(r'\s*\*\s*\d+', '', name)
    name = name.replace('(npc)', '').strip()
    name = name.replace('poké', 'poke')
    name = name.replace(' ', '-').replace("'", "").replace('.', '').replace('/', '-')
    while '--' in name: name = name.replace('--', '-')
    return name.strip('-')

def fetch_all_data():
    pokemon_base = {}
    move_data = {}
    ability_data = {}
    item_data = {}
    
    print("Fetching Pokemon data...")
    for i in range(1, GEN5_MAX_POKEMON + 1):
        p_data = get_json(f"{BASE_URL}/pokemon/{i}", f"pokemon_{i}")
        if not p_data: continue
        s_data = get_json(p_data['species']['url'], f"species_{i}")
        evo_data = get_json(s_data['evolution_chain']['url'], f"evo_{s_data['evolution_chain']['url'].split('/')[-2]}")
        pkmn = {
            'id': p_data['id'],
            'name': p_data['name'],
            'types': [t['type']['name'] for t in p_data['types']],
            'abilities': [a['ability']['name'] for a in p_data['abilities']],
            'stats': {s['stat']['name']: s['base_stat'] for s in p_data['stats']},
            'moves': [],
            'evolution_chain': evo_data
        }
        for m in p_data['moves']:
            for detail in m['version_group_details']:
                if detail['version_group']['name'] in ['black-white', 'black-2-white-2']:
                    pkmn['moves'].append({
                        'name': m['move']['name'],
                        'level': detail['level_learned_at'],
                        'method': detail['move_learn_method']['name']
                    })
        pokemon_base[p_data['name']] = pkmn

    print("Fetching Move data...")
    move_names = set()
    for p in pokemon_base.values():
        for m in p['moves']:
            move_names.add(m['name'])
    for mname in sorted(move_names):
        m_data = get_json(f"{BASE_URL}/move/{mname}", f"move_{mname}")
        if not m_data: continue
        g5_stats = get_gen5_move_stats(m_data)
        desc = ""
        for entry in m_data['effect_entries']:
            if entry['language']['name'] == 'en':
                desc = entry['short_effect'].replace('$effect_chance', str(m_data.get('effect_chance', '')))
                break
        tm_num = "-"
        for machine in m_data.get('machines', []):
            m_info = get_json(machine['machine']['url'], f"machine_{machine['machine']['url'].split('/')[-2]}")
            if m_info and m_info['version_group']['name'] in ['black-white', 'black-2-white-2']:
                tm_num = f"TM{m_info['item']['name'].replace('tm', '')}" if 'tm' in m_info['item']['name'] else f"HM{m_info['item']['name'].replace('hm', '')}"
                break
        move_data[mname] = {
            'name': mname,
            'type': g5_stats['type'],
            'damage_class': m_data['damage_class']['name'],
            'power': g5_stats['power'],
            'accuracy': g5_stats['accuracy'],
            'pp': g5_stats['pp'],
            'description': desc,
            'tm_num': tm_num
        }

    print("Fetching Ability data...")
    ability_names = set()
    for p in pokemon_base.values():
        for a in p['abilities']:
            ability_names.add(a)
    for aname in sorted(ability_names):
        a_data = get_json(f"{BASE_URL}/ability/{aname}", f"ability_{aname}")
        if not a_data: continue
        desc = ""
        for entry in a_data['effect_entries']:
            if entry['language']['name'] == 'en':
                desc = entry['short_effect']
                break
        ability_data[aname] = { 'name': aname, 'description': desc }

    print("Fetching Item data...")
    items_to_fetch = set()
    # TMs/HMs
    for i in range(1, 101): items_to_fetch.add(f"tm{i:02}")
    for i in range(1, 7): items_to_fetch.add(f"hm{i:02}")
    
    # Common items
    common_items = ['pokeball', 'great-ball', 'ultra-ball', 'master-ball', 'potion', 'super-potion', 'hyper-potion', 'max-potion', 'full-restore', 'revive', 'max-revive', 'full-heal', 'antidote', 'burn-heal', 'ice-heal', 'awakening', 'paralyze-heal', 'escape-rope', 'repel', 'super-repel', 'max-repel', 'exp-share', 'lucky-egg', 'bicycle', 'super-rod', 'old-rod', 'good-rod', 'everstone', 'oval-stone', 'sun-stone', 'shiny-stone', 'thunder-stone', 'leaf-stone', 'fire-stone', 'water-stone', 'dusk-stone', 'dawn-stone', 'razor-fang', 'razor-claw', 'prism-scale', 'protector', 'reaper-cloth', 'dubious-disc', 'electirizer', 'magmarizer', 'up-grade', 'dragon-scale', 'metal-coat', 'kings-rock', 'soothe-bell', 'amulet-coin', 'lucky-punch', 'quick-powder', 'thick-club', 'stick', 'light-ball', 'choice-band', 'choice-specs', 'choice-scarf', 'life-orb', 'focus-sash', 'focus-band', 'expert-belt', 'muscle-band', 'wise-glasses', 'metronome', 'binding-band', 'grip-claw', 'shed-shell', 'light-clay', 'black-sludge', 'zoom-lens', 'wide-lens', 'power-herb', 'white-herb', 'mental-herb', 'air-balloon', 'soul-dew', 'rage-candy-bar', 'old-amber', 'helix-fossil', 'dome-fossil', 'root-fossil', 'claw-fossil', 'skull-fossil', 'armor-fossil', 'cover-fossil', 'plume-fossil']
    for item in common_items: items_to_fetch.add(item)

    # Parse Item & Trade Changes.txt for more items
    try:
        with open(os.path.join("Documentation", "Item & Trade Changes.txt"), 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            # Extract all item names between " -> " or listed in the "edited into Use items" section
            matches = re.findall(r'(\w+(?:\s+\w+)*)(?:\s+\* \d+)?\s*->\s*(\w+(?:\s+\w+)*)', content)
            for m in matches:
                items_to_fetch.add(normalize_item_name(m[0]))
                items_to_fetch.add(normalize_item_name(m[1]))
            # Handle "Use" items section
            use_match = re.search(r'edited into "Use" items:\n---\n(.*?)\n\n', content, re.DOTALL)
            if use_match:
                for line in use_match.group(1).split('\n'):
                    if line.strip(): items_to_fetch.add(normalize_item_name(line))
    except Exception as e:
        print(f"Error parsing Item Changes for fetching: {e}")

    for item in sorted(items_to_fetch):
        if not item: continue
        get_json(f"{BASE_URL}/item/{item}", f"item_{item}")

    # Gather all items from cache
    for filename in os.listdir(CACHE_DIR):
        if filename.startswith("item_") and filename.endswith(".json"):
            with open(os.path.join(CACHE_DIR, filename), 'r', encoding='utf-8') as f:
                try:
                    it_data = json.load(f)
                    desc = ""
                    for entry in it_data.get('effect_entries', []):
                        if entry['language']['name'] == 'en':
                            desc = entry['short_effect']
                            break
                    item_data[it_data['name']] = {
                        'name': it_data['name'],
                        'description': desc,
                        'category': it_data['category']['name'] if it_data.get('category') else 'misc',
                        'cost': it_data.get('cost', 0)
                    }
                except: continue

    with open(os.path.join("scripts/data", "base_data.json"), 'w', encoding='utf-8') as f:
        json.dump({
            'pokemon': pokemon_base,
            'moves': move_data,
            'abilities': ability_data,
            'items': item_data
        }, f, indent=2)

if __name__ == "__main__":
    fetch_all_data()
    print("Base data fetching complete.")
