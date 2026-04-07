import requests
import json
import os
import time

BASE_URL = "https://pokeapi.co/api/v2"
GEN5_MAX_POKEMON = 151
CACHE_DIR = "scripts/data/cache"

if not os.path.exists(CACHE_DIR):
    os.makedirs(CACHE_DIR)

def get_json(url, filename):
    cache_path = os.path.join(CACHE_DIR, filename)
    if os.path.exists(cache_path):
        with open(cache_path, 'r') as f:
            return json.load(f)
    
    print(f"Fetching {url}...")
    try:
        res = requests.get(url)
        res.raise_for_status()
        data = res.json()
        with open(cache_path, 'w') as f:
            json.dump(data, f)
        return data
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return None

def fetch_all_data():
    pokemon_base = {}
    
    # 1. Fetch Pokemon
    for i in range(1, GEN5_MAX_POKEMON + 1):
        data = get_json(f"{BASE_URL}/pokemon/{i}", f"pokemon_{i}.json")
        if data:
            name = data['name']
            pokemon_base[name] = {
                'id': data['id'],
                'name': name,
                'types': [t['type']['name'] for t in data['types']],
                'abilities': [a['ability']['name'] for a in data['abilities']],
                'stats': {s['stat']['name']: s['base_stat'] for s in data['stats']},
                'moves': []
            }
            # Extract moves (only for Gen 5)
            for m in data['moves']:
                for v in m['version_group_details']:
                    if v['version_group']['name'] in ['black-white', 'black-2-white-2']:
                        pokemon_base[name]['moves'].append({
                            'name': m['move']['name'],
                            'method': v['move_learn_method']['name'],
                            'level': v['level_learned_at']
                        })
                        break
        if i % 100 == 0:
            print(f"Processed {i} Pokemon...")

    # 2. Fetch Moves (unique ones from pokemon_base)
    unique_moves = set()
    for p in pokemon_base.values():
        for m in p['moves']:
            unique_moves.add(m['name'])
    
    move_data = {}
    print(f"Fetching {len(unique_moves)} unique moves...")
    for idx, move_name in enumerate(sorted(list(unique_moves))):
        data = get_json(f"{BASE_URL}/move/{move_name}", f"move_{move_name}.json")
        if data:
            desc = ""
            for ent in data['effect_entries']:
                if ent['language']['name'] == 'en':
                    desc = ent['short_effect']
                    break
            
            move_data[move_name] = {
                'name': data['name'],
                'type': data['type']['name'],
                'power': data['power'],
                'accuracy': data['accuracy'],
                'pp': data['pp'],
                'damage_class': data['damage_class']['name'],
                'description': desc
            }
        if (idx + 1) % 100 == 0:
            print(f"Processed {idx+1} moves...")

    # 3. Fetch Abilities (unique ones)
    unique_abilities = set()
    for p in pokemon_base.values():
        for a in p['abilities']:
            unique_abilities.add(a)
    
    ability_data = {}
    print(f"Fetching {len(unique_abilities)} unique abilities...")
    for idx, ab_name in enumerate(sorted(list(unique_abilities))):
        data = get_json(f"{BASE_URL}/ability/{ab_name}", f"ability_{ab_name}.json")
        if data:
            desc = ""
            for ent in data['effect_entries']:
                if ent['language']['name'] == 'en':
                    desc = ent['short_effect']
                    break
            ability_data[ab_name] = {
                'name': data['name'],
                'description': desc
            }
        if (idx + 1) % 50 == 0:
            print(f"Processed {idx+1} abilities...")

    # Save consolidated base data
    with open('scripts/data/base_data.json', 'w') as f:
        json.dump({
            'pokemon': pokemon_base,
            'moves': move_data,
            'abilities': ability_data
        }, f, indent=2)

if __name__ == "__main__":
    fetch_all_data()
    print("Base data fetching complete.")
