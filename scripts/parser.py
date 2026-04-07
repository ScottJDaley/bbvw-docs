import json
import re
import os

DATA_DIR = "scripts/data"

def parse_pokemon_changes():
    changes = {}
    with open(os.path.join(DATA_DIR, "Pokemon Changes.txt"), 'r') as f:
        content = f.read()
    
    # Split by Pokemon entries (e.g. #001 Bulbasaur)
    # Some entries are ranges like #001 Bulbasaur - #002 Ivysaur
    entries = re.split(r'\n(?=#\d{3})', content)
    
    for entry in entries:
        lines = entry.strip().split('\n')
        if not lines: continue
        
        header = lines[0]
        match = re.findall(r'#(\d{3})\s+([^-]+)', header)
        if not match: continue
        
        # Handle ranges or single pokemon
        pokemon_names = [m[1].strip() for m in match]
        # Special case: #001 Bulbasaur - #002 Ivysaur
        if ' - ' in header:
            # This is tricky because the RTF conversion might have joined them
            # Let's try a broader regex
            names = re.split(r' - | #\d{3} ', header)
            pokemon_names = [re.sub(r'#\d{3}\s+', '', n).strip() for n in names]

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
            
            # Parse stats: HP: 83 à 105
            stat_match = re.match(r'(HP|Attack|Defense|Special Attack|Special Defense|Speed|Total):\s+(\d+)\s+à\s+(\d+)', line)
            if stat_match:
                stat_name = stat_match.group(1).lower().replace(' ', '_')
                data['stats'][stat_name] = {'old': int(stat_match.group(2)), 'new': int(stat_match.group(3))}
                continue
            
            # Parse abilities: Ability One: Overgrow
            ab_match = re.match(r'Ability (One|Two):\s+(.+)', line)
            if ab_match:
                slot = ab_match.group(1).lower()
                data['abilities'][slot] = ab_match.group(2).strip()
                continue
            
            # Parse types: Type: Fighting / Flying
            type_match = re.match(r'Type:\s+(.+)', line)
            if type_match:
                data['types'] = [t.strip().lower() for t in type_match.group(1).split('/')]
                continue
            
            # Parse items: Item: Miracle Seed (50%)
            item_match = re.match(r'Items?:\s+(.+)', line)
            if item_match:
                data['items'] = [i.strip() for i in item_match.group(1).split(',')]
                continue
            
            # Parse evolution: Evolution (Politoed): Level Up at Night with King's Rock equipped.
            evo_match = re.match(r'Evolution(?:\s+\((.+)\))?:\s+(.+)', line)
            if evo_match:
                data['evolution'].append({
                    'target': evo_match.group(1),
                    'method': evo_match.group(2)
                })
                continue
            
            # Parse TMs: TM: Can now learn TM34, Sludge Wave.
            tm_match = re.match(r'(TM|HM):\s+(.+)', line)
            if tm_match:
                data['tm_hm'].append(tm_match.group(2))
                continue

        for name in pokemon_names:
            if name:
                changes[name.lower()] = data
                
    return changes

def parse_wild_pokemon():
    routes = {}
    with open(os.path.join(DATA_DIR, "Wild Pokemon.txt"), 'r') as f:
        content = f.read()
    
    # Split by route (separator is ========)
    sections = content.split('==================================================================')
    
    for section in sections:
        lines = section.strip().split('\n')
        if not lines: continue
        
        route_name = lines[0].strip()
        if not route_name or route_name == "Wild Pokémon": continue
        
        routes[route_name] = {'encounters': []}
        
        for line in lines[1:]:
            line = line.strip()
            # Parse encounter line: Grass, Normal: Lillipup (20%), Pidgey (20%), ...
            enc_match = re.match(r'([^:]+):\s+(.+)', line)
            if enc_match:
                method = enc_match.group(1).strip()
                pkmn_list = enc_match.group(2).strip()
                # Parse pokemon and percentages: Lillipup (20%)
                pkmns = re.findall(r'([^(]+)\s+\((\d+)%\)', pkmn_list)
                for pkmn, rate in pkmns:
                    routes[route_name]['encounters'].append({
                        'method': method,
                        'pokemon': pkmn.strip(),
                        'rate': int(rate)
                    })
    return routes

def parse_move_changes():
    move_changes = {}
    with open(os.path.join(DATA_DIR, "Level Up Move Changes.txt"), 'r') as f:
        content = f.read()
    
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
            # Parse move: Lv 1: Leer
            # Or: Lv 1: Leer, Tackle
            move_match = re.match(r'Lv\s+(\d+):\s+(.+)', line)
            if move_match:
                lv = int(move_match.group(1))
                move_names = [m.strip().lower().replace(' ', '-') for m in move_match.group(2).split(',')]
                for mname in move_names:
                    moves.append({'level': lv, 'name': mname})
        
        move_changes[pkmn_name] = moves
    return move_changes

if __name__ == "__main__":
    pokemon_changes = parse_pokemon_changes()
    wild_pkmn = parse_wild_pokemon()
    move_changes = parse_move_changes()
    
    with open('scripts/data/romhack_data.json', 'w') as f:
        json.dump({
            'pokemon_changes': pokemon_changes,
            'wild_pokemon': wild_pkmn,
            'move_changes': move_changes
        }, f, indent=2)
    print("Parsing complete.")
