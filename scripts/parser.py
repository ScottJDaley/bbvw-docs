import json
import re
import os

DATA_DIR = "scripts/data"

def parse_pokemon_changes():
    changes = {}
    with open(os.path.join(DATA_DIR, "Pokemon Changes.txt"), 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
    
    entries = re.split(r'\n(?=#\d{3})', content)
    
    for entry in entries:
        lines = entry.strip().split('\n')
        if not lines: continue
        
        header = lines[0]
        pkmn_matches = re.findall(r'#(\d{3})\s+([^-]+)', header)
        if not pkmn_matches: continue
        
        pokemon_names = []
        if ' - ' in header:
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
    with open(os.path.join(DATA_DIR, "Wild Pokemon.txt"), 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
    
    sections = re.split(r'={10,}', content)
    
    for section in sections:
        lines = section.strip().split('\n')
        if not lines: continue
        
        route_name = ""
        header_idx = -1
        for i, line in enumerate(lines):
            line = line.strip()
            if line and line != "Wild Pokémon" and "Recall that" not in line and "Serebii.net" not in line and "649" not in line:
                route_name = line
                header_idx = i
                break
        
        if not route_name: continue
        
        route_data = {'name': route_name, 'encounters': []}
        
        for line in lines[header_idx+1:]:
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
        if route_data['encounters']:
            routes.append(route_data)
    return routes

def parse_move_changes():
    move_changes = {} 
    move_stat_changes = {} 
    
    with open(os.path.join(DATA_DIR, "Level Up Move Changes.txt"), 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
    
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
            move_match = re.match(r'([+\-=])\s+Level\s+(\d+)\s+-\s+(.+)', line)
            if move_match:
                marker = move_match.group(1)
                lv = int(move_match.group(2))
                mname = move_match.group(3).strip().lower().replace(' ', '-')
                moves.append({'level': lv, 'name': mname, 'marker': marker})
            else:
                 move_match2 = re.match(r'([+\-=])\s+(.+)\s+-\s+Level\s+(\d+)', line)
                 if move_match2:
                     marker = move_match2.group(1)
                     mname = move_match2.group(2).strip().lower().replace(' ', '-')
                     lv = int(move_match2.group(3))
                     moves.append({'level': lv, 'name': mname, 'marker': marker})
        
        move_changes[pkmn_name] = moves
    return move_changes, move_stat_changes

def parse_trainers():
    trainers = {} 
    with open(os.path.join(DATA_DIR, "Important Trainer Rosters.txt"), 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
    
    entries = re.split(r'\n(?=Rival|Gym Leader|PKMN Trainer|Elite Four|Team Plasma|Champion|GAME Freak)', content)
    
    for entry in entries:
        lines = entry.strip().split('\n')
        if not lines: continue
        
        name = lines[0].strip()
        location = ""
        for line in lines:
            if 'Location:' in line:
                location = line.replace('Location:', '').strip()
                break
        
        if not location: continue
        
        trainer_data = {'name': name, 'pokemon': []}
        species = re.findall(r'Species\|([^|]+)', entry)
        levels = re.findall(r'Level\|([^|]+)', entry)
        items = re.findall(r'Item\|([^|]+)', entry)
        abilities = re.findall(r'Ability\|([^|]+)', entry)
        moves1 = re.findall(r'Move #1\|([^|]+)', entry)
        moves2 = re.findall(r'Move #2\|([^|]+)', entry)
        moves3 = re.findall(r'Move #3\|([^|]+)', entry)
        moves4 = re.findall(r'Move #4\|([^|]+)', entry)

        def split_list(match):
            if not match: return []
            return [x.strip() for x in match[0].strip().split('\n') if x.strip()]

        s_list = split_list(species)
        l_list = split_list(levels)
        i_list = split_list(items)
        a_list = split_list(abilities)
        m1_list = split_list(moves1)
        m2_list = split_list(moves2)
        m3_list = split_list(moves3)
        m4_list = split_list(moves4)

        for j in range(len(s_list)):
            p_data = {
                'name': s_list[j],
                'level': l_list[j] if j < len(l_list) else "?",
                'item': i_list[j] if j < len(i_list) else "-",
                'ability': a_list[j] if j < len(a_list) else "-",
                'moves': []
            }
            if j < len(m1_list): p_data['moves'].append(m1_list[j])
            if j < len(m2_list): p_data['moves'].append(m2_list[j])
            if j < len(m3_list): p_data['moves'].append(m3_list[j])
            if j < len(m4_list): p_data['moves'].append(m4_list[j])
            trainer_data['pokemon'].append(p_data)
        
        if location not in trainers: trainers[location] = []
        trainers[location].append(trainer_data)
        
    return trainers

if __name__ == "__main__":
    pokemon_changes = parse_pokemon_changes()
    wild_pkmn = parse_wild_pokemon()
    move_changes, move_stat_changes = parse_move_changes()
    trainer_data = parse_trainers()
    
    with open('scripts/data/romhack_data.json', 'w') as f:
        json.dump({
            'pokemon_changes': pokemon_changes,
            'wild_pokemon': wild_pkmn,
            'move_changes': move_changes,
            'move_stat_changes': move_stat_changes,
            'trainers': trainer_data
        }, f, indent=2)
    print("Parsing complete.")
