import json
import re
import os

DATA_DIR = "scripts/data"

def parse_pokemon_changes():
    changes = {}
    with open(os.path.join(DATA_DIR, "Pokemon Changes.txt"), 'r') as f:
        content = f.read()
    
    entries = re.split(r'\n(?=#\d{3})', content)
    
    for entry in entries:
        lines = entry.strip().split('\n')
        if not lines: continue
        
        header = lines[0]
        # Regex to match #001 Name or #001 Name - #002 Name
        pkmn_matches = re.findall(r'#(\d{3})\s+([^-]+)', header)
        if not pkmn_matches: continue
        
        pokemon_names = []
        if ' - ' in header:
             # Handle range like #027 Sandshrew - #028 Sandslash
             parts = header.split(' - ')
             for p in parts:
                 m = re.search(r'#\d{3}\s+(.+)', p)
                 if m: pokemon_names.append(m.group(1).strip().lower())
        else:
            pokemon_names = [m[1].strip().lower() for m in pkmn_matches]

        data = {
            'stats': {},
            'abilities': {},
            'items': [],
            'evolution': [],
            'types': None,
            'tm_hm': []
        }
        
        for line in lines[1:]:
            line = line.strip()
            if not line: continue
            
            stat_match = re.match(r'(HP|Attack|Defense|Special Attack|Special Defense|Speed|Total):\s+(\d+)\s+à\s+(\d+)', line)
            if stat_match:
                stat_name = stat_match.group(1).lower().replace(' ', '_').replace('-', '_')
                data['stats'][stat_name] = {'old': int(stat_match.group(2)), 'new': int(stat_match.group(3))}
                continue
            
            ab_match = re.match(r'Ability (One|Two):\s+(.+)', line)
            if ab_match:
                slot = ab_match.group(1).lower()
                data['abilities'][slot] = ab_match.group(2).strip()
                continue
            
            type_match = re.match(r'Type:\s+(.+)', line)
            if type_match:
                data['types'] = [t.strip().lower() for t in type_match.group(1).split('/')]
                continue
            
            item_match = re.match(r'Items?:\s+(.+)', line)
            if item_match:
                data['items'] = [i.strip() for i in item_match.group(1).split(',')]
                continue
            
            evo_match = re.match(r'Evolution(?:\s+\((.+)\))?:\s+(.+)', line)
            if evo_match:
                data['evolution'].append({
                    'target': evo_match.group(1),
                    'method': evo_match.group(2)
                })
                continue
            
            tm_match = re.match(r'(TM|HM):\s+(.+)', line)
            if tm_match:
                data['tm_hm'].append(tm_match.group(2))
                continue

        for name in pokemon_names:
            if name:
                changes[name] = data
                
    return changes

def parse_wild_pokemon():
    routes = []
    with open(os.path.join(DATA_DIR, "Wild Pokemon.txt"), 'r') as f:
        content = f.read()
    
    sections = content.split('==================================================================')
    
    for section in sections:
        lines = section.strip().split('\n')
        if not lines: continue
        
        route_name = lines[0].strip()
        if not route_name or route_name == "Wild Pokémon": continue
        
        route_data = {'name': route_name, 'encounters': []}
        
        for line in lines[1:]:
            line = line.strip()
            enc_match = re.match(r'([^:]+):\s+(.+)', line)
            if enc_match:
                method = enc_match.group(1).strip()
                pkmn_list = enc_match.group(2).strip()
                pkmns = re.findall(r'([^(,]+)\s+\((\d+)%\)', pkmn_list)
                for pkmn, rate in pkmns:
                    route_data['encounters'].append({
                        'method': method,
                        'pokemon': pkmn.strip(),
                        'rate': int(rate)
                    })
        routes.append(route_data)
    return routes

def parse_move_changes():
    move_changes = {} # Map of pokemon -> moves
    move_stat_changes = {} # Map of move_name -> {bp: {old, new}, acc: {old, new}}
    
    with open(os.path.join(DATA_DIR, "Level Up Move Changes.txt"), 'r') as f:
        content = f.read()
    
    # Also look for the general move stat changes if they exist in the file
    # Example: Cut: Base Power 50 -> 60, Accuracy 95 -> 100
    stat_matches = re.findall(r'(\w+(?:\s+\w+)?):\s+Base Power\s+(\d+)\s+->\s+(\d+),\s+Accuracy\s+(\d+)\s+->\s+(\d+)', content)
    for name, bp_old, bp_new, acc_old, acc_new in stat_matches:
        move_stat_changes[name.lower().replace(' ', '-')] = {
            'power': {'old': int(bp_old), 'new': int(bp_new)},
            'accuracy': {'old': int(acc_old), 'new': int(acc_new)}
        }

    entries = re.split(r'\n(?=#\d{3})', content)
    for entry in entries:
        lines = entry.strip().split('\n')
        if not lines: continue
        
        header = lines[0]
        pkmn_match = re.search(r'#\d{3}\s+([^-\n]+)', header)
        if not pkmn_match: continue
        pkmn_name = pkmn_match.group(1).strip().lower()
        
        moves = []
        for line in lines[1:]:
            line = line.strip()
            if not line: continue
            move_match = re.match(r'Lv\s+(\d+):\s+(.+)', line)
            if move_match:
                lv = int(move_match.group(1))
                move_names = [m.strip().lower().replace(' ', '-') for m in move_match.group(2).split(',')]
                for mname in move_names:
                    moves.append({'level': lv, 'name': mname})
        
        move_changes[pkmn_name] = moves
    return move_changes, move_stat_changes

if __name__ == "__main__":
    pokemon_changes = parse_pokemon_changes()
    wild_pkmn = parse_wild_pokemon()
    move_changes, move_stat_changes = parse_move_changes()
    
    with open('scripts/data/romhack_data.json', 'w') as f:
        json.dump({
            'pokemon_changes': pokemon_changes,
            'wild_pokemon': wild_pkmn,
            'move_changes': move_changes,
            'move_stat_changes': move_stat_changes
        }, f, indent=2)
    print("Parsing complete.")
