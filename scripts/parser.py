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
            if not line or line == "Wild Pokémon" or "Recall that" in line or "Serebii.net" in line or "649" in line or "Note that" in line or "'Special' refers" in line:
                continue
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
                pkmns = re.findall(r'([^,(]+)\s+\((\d+)%\)', pkmn_list)
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
    
    # 1. Parse Important Trainers
    with open(os.path.join(DATA_DIR, "Important Trainer Rosters.txt"), 'r', encoding='utf-8', errors='ignore') as f:
        imp_content = f.read()
    
    entries = re.split(r'\n\s*\n(?=Rival|Gym Leader|PKMN Trainer|Elite Four|Team Plasma|Champion|GAME Freak|N’s Team|Bianca’s Team|Cheren’s Team)', imp_content)
    
    current_trainer = None
    current_location = None
    important_data = {} # Keyed by name for matching later

    for entry in entries:
        lines = entry.strip().split('\n')
        if not lines: continue
        header = lines[0].strip()
        
        loc_match = re.search(r'Location:\s+(.+)', entry)
        if loc_match: current_location = loc_match.group(1).strip()
        
        if any(x in header for x in ["Rival", "Gym Leader", "PKMN Trainer", "Elite Four", "Team Plasma", "Champion", "GAME Freak"]):
            current_trainer = header
            if "–" in header and not current_location:
                parts = header.split("–")
                if len(parts) > 1 and any(x in parts[1] for x in ["Route", "Town", "City", "Gym"]):
                    current_location = parts[1].strip()

        if "Team" in header and current_location:
            trainer_name = current_trainer if current_trainer else header
            trainer_data = {'name': trainer_name, 'pokemon': [], 'important': True}
            
            species = re.findall(r'Species\|([^|]+)', entry)
            levels = re.findall(r'Level\|([^|]+)', entry)
            items = re.findall(r'Item\|([^|]+)', entry)
            abilities = re.findall(r'Ability\|([^|]+)', entry)
            m1 = re.findall(r'Move #1\|([^|]+)', entry)
            m2 = re.findall(r'Move #2\|([^|]+)', entry)
            m3 = re.findall(r'Move #3\|([^|]+)', entry)
            m4 = re.findall(r'Move #4\|([^|]+)', entry)

            def split_list(match):
                if not match: return []
                raw = match[0].strip()
                items = [x.strip() for x in raw.split('\n') if x.strip()]
                if len(items) == 1 and ' ' in raw: items = [x.strip() for x in raw.split('  ') if x.strip()]
                return items

            s_list, l_list, i_list, a_list = split_list(species), split_list(levels), split_list(items), split_list(abilities)
            m1_list, m2_list, m3_list, m4_list = split_list(m1), split_list(m2), split_list(m3), split_list(m4)

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
            
            if current_location not in trainers: trainers[current_location] = []
            trainers[current_location].append(trainer_data)
            # Save for name-based lookup from other doc
            short_name = trainer_name.split('–')[0].split('-')[0].replace('Rival', '').replace('PKMN Trainer', '').strip()
            important_data[short_name] = trainer_data

    # 2. Parse General Trainers
    with open(os.path.join(DATA_DIR, "Trainer Rosters.txt"), 'r', encoding='utf-8', errors='ignore') as f:
        gen_content = f.read()
    
    sections = gen_content.split('\n---\n')
    for i in range(0, len(sections)-1):
        # Format is likely: Location \n --- \n Trainers...
        loc_lines = sections[i].strip().split('\n')
        location = loc_lines[-1].strip()
        trainer_lines = sections[i+1].strip().split('\n')
        # Stop before next location
        if i+1 < len(sections):
             # The next location is actually the last line of the current trainer list
             location = loc_lines[-1].strip()
             trainer_list = []
             for line in trainer_lines:
                 if not line.strip() or line.strip() == location: continue
                 # Check if this line is actually the NEXT location (if it only has one line)
                 trainer_list.append(line.strip())
             
             for t_line in trainer_list:
                 if t_line.startswith('*'):
                     # This refers to an important trainer
                     name = t_line.replace('*', '').strip()
                     # If we already added it from Important Roster, skip or update?
                     continue
                 
                 # Format: Class Name: Pkmn1 L10, Pkmn2 L12
                 match = re.match(r'([^:]+):\s+(.+)', t_line)
                 if match:
                     t_name = match.group(1).strip()
                     pkmn_raw = match.group(2).strip()
                     pkmn_entries = pkmn_raw.split(',')
                     trainer_data = {'name': t_name, 'pokemon': [], 'important': False}
                     for pk_entry in pkmn_entries:
                         # Pkmn1 L10
                         pk_match = re.match(r'(.+)\s+L(\d+)', pk_entry.strip())
                         if pk_match:
                             trainer_data['pokemon'].append({
                                 'name': pk_match.group(1).strip(),
                                 'level': pk_match.group(2).strip(),
                                 'moves': [], 'item': '-', 'ability': '-'
                             })
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
