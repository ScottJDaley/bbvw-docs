import requests
import json
import os
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
    r = requests.get(url)
    if r.status_code != 200:
        print(f"Error fetching {url}: {r.status_code}")
        return None
    data = r.json()
    
    if cache_name:
        with open(cache_path, 'w', encoding='utf-8') as f:
            json.dump(data, f)
    
    return data

def get_gen5_move_stats(move_data):
    # Start with latest values
    stats = {
        'power': move_data.get('power'),
        'accuracy': move_data.get('accuracy'),
        'pp': move_data.get('pp'),
        'type': move_data['type']['name']
    }
    
    # PokeAPI Version Group ID for Black 2 / White 2 is 14.
    # past_values contains stats as they were BEFORE that version group change.
    past_values = move_data.get('past_values', [])
    if not past_values:
        return stats

    def get_v_id(url):
        return int(url.split('/')[-2])

    # Sort by version group ID ascending
    past_values.sort(key=lambda x: get_v_id(x['version_group']['url']))

    # Find the earliest change AFTER Gen 5
    for past in past_values:
        v_id = get_v_id(past['version_group']['url'])
        if v_id > 14:
            # This entry has the stats as they were BEFORE this change.
            # If this is the first change after Gen 5, then these ARE the Gen 5 stats.
            if past.get('power') is not None: stats['power'] = past['power']
            if past.get('accuracy') is not None: stats['accuracy'] = past['accuracy']
            if past.get('pp') is not None: stats['pp'] = past['pp']
            if past.get('type') is not None: stats['type'] = past['type']['name']
            break
            
    return stats

def fetch_all_data():
    pokemon_base = {}
    move_data = {}
    ability_data = {}
    
    # Fetch Pokemon
    print("Fetching Pokemon data...")
    for i in range(1, GEN5_MAX_POKEMON + 1):
        p_data = get_json(f"{BASE_URL}/pokemon/{i}", f"pokemon_{i}")
        if not p_data: continue
        
        # Need species for evolution chain
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
                # Filter for Gen 5 (Black/White or B2/W2)
                if detail['version_group']['name'] in ['black-white', 'black-2-white-2']:
                    pkmn['moves'].append({
                        'name': m['move']['name'],
                        'level': detail['level_learned_at'],
                        'method': detail['move_learn_method']['name']
                    })
        
        pokemon_base[p_data['name']] = pkmn
        
        # Also handle forms like Deoxys, Rotom, etc.
        # PokeAPI usually puts these at higher IDs (> 10000)
        # But we only care about the ones mentioned in romhack docs if they are "Gen 5" pokemon
        # We'll stick to 1-649 for now as base list.

    # Fetch all moves mentioned in Pokemon data
    print("Fetching Move data...")
    move_names = set()
    for p in pokemon_base.values():
        for m in p['moves']:
            move_names.add(m['name'])
            
    for mname in sorted(move_names):
        m_data = get_json(f"{BASE_URL}/move/{mname}", f"move_{mname}")
        if not m_data: continue
        
        # Get Gen 5 stats
        g5_stats = get_gen5_move_stats(m_data)
        
        desc = ""
        for entry in m_data['effect_entries']:
            if entry['language']['name'] == 'en':
                desc = entry['short_effect'].replace('$effect_chance', str(m_data.get('effect_chance', '')))
                break
        
        # Get TM number if available in Gen 5
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

    # Fetch all abilities
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
        ability_data[aname] = {
            'name': aname,
            'description': desc
        }

    # Save to base_data.json
    with open(os.path.join("scripts/data", "base_data.json"), 'w', encoding='utf-8') as f:
        json.dump({
            'pokemon': pokemon_base,
            'moves': move_data,
            'abilities': ability_data
        }, f, indent=2)

if __name__ == "__main__":
    fetch_all_data()
    print("Base data fetching complete.")
