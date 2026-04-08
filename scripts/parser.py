import json
import re
import os

DATA_DIR = "scripts/data"

def normalize_name(name):
    if not name: return ""
    name = name.replace('NidoranM', 'nidoran-m').replace('NidoranF', 'nidoran-f')
    name = name.replace('Mime Jr.', 'mime-jr').replace('Mr. Mime', 'mr-mime')
    if name.lower().startswith('basculin'): return 'basculin'
    return name.lower().replace(' ', '-').replace('.', '').replace("'", "").replace('’', '').replace('♂', '-m').replace('♀', '-f').replace('/', '-').replace('–', '-').strip()

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
        data = {'stats': {}, 'abilities': {}, 'items': [], 'evolution': [], 'types': None, 'tm_hm': []}
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
                data['abilities'][ab_match.group(1).lower()] = ab_match.group(2).strip()
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
                data['evolution'].append({'target': evo_match.group(1), 'method': evo_match.group(2)})
                continue
            tm_match = re.match(r'(TM|HM):\s+(.+)', line)
            if tm_match:
                data['tm_hm'].append(tm_match.group(2))
                continue
        for name in pokemon_names:
            if name: changes[name] = data
    return changes

def parse_wild_pokemon():
    routes = []
    with open(os.path.join(DATA_DIR, "Wild Pokemon.txt"), 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
    
    sections = re.split(r'={10,}', content)
    for section in sections:
        section = section.strip()
        if not section: continue
        
        blocks = re.split(r'\n\s*\n', section)
        main_area_name = ""
        route_data = None

        for block in blocks:
            block = block.strip()
            if not block: continue
            lines = [l.strip() for l in block.split('\n') if l.strip()]
            if not lines: continue
            
            if any(x in lines[0] for x in ["Wild Pokémon", "Recall that", "Serebii.net", "649", "Note that", "Special' refers", "Thanks go to", "You won’t be able", "There are a couple"]):
                continue

            if "LEGENDARY ENCOUNTER" in lines[0] or "SPECIAL ENCOUNTER" in lines[0]:
                if route_data: route_data['specials'].append(block)
                continue

            if not any(":" in l for l in lines):
                potential_name = lines[0]
                if not main_area_name:
                    main_area_name = potential_name
                    clean_name = re.split(r' – | \dF| B\dF| Inside| Outside', main_area_name)[0].strip()
                    route_data = next((r for r in routes if r['name'] == clean_name), None)
                    if not route_data:
                        route_data = {'name': clean_name, 'sections': [], 'specials': []}
                        routes.append(route_data)
                continue

            if any(":" in l for l in lines):
                if not route_data: continue
                
                encounters = []
                title = "General"
                start_idx = 0
                if ":" not in lines[0]:
                    title = lines[0]
                    start_idx = 1
                
                for line in lines[start_idx:]:
                    enc_match = re.match(r'([^:]+):\s+(.+)', line)
                    if enc_match:
                        method = enc_match.group(1).strip()
                        pkmn_list = enc_match.group(2).strip()
                        pkmns = re.findall(r'([^,(]+)\s+\((\d+)%\)', pkmn_list)
                        for pkmn, rate in pkmns:
                            encounters.append({'method': method, 'pokemon': pkmn.strip(), 'rate': int(rate)})
                
                if encounters:
                    route_data['sections'].append({'title': title, 'encounters': encounters})
                    
    return routes

def parse_move_changes():
    move_changes = {} 
    move_stat_changes = {} 
    with open(os.path.join(DATA_DIR, "Level Up Move Changes.txt"), 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
    stat_matches = re.findall(r'(\w+(?:\s+\w+)?):\s+Base Power\s+(\d+)\s+->\s+(\d+),\s+Accuracy\s+(\d+)\s+->\s+(\d+)', content)
    for name, bp_old, bp_new, acc_old, acc_new in stat_matches:
        move_stat_changes[name.lower().replace(' ', '-')] = {'power': {'old': int(bp_old), 'new': int(bp_new)}, 'accuracy': {'old': int(acc_old), 'new': int(acc_new)}}
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
                moves.append({'level': int(move_match.group(2)), 'name': move_match.group(3).strip().lower().replace(' ', '-'), 'marker': move_match.group(1)})
            else:
                 move_match2 = re.match(r'([+\-=])\s+(.+)\s+-\s+Level\s+(\d+)', line)
                 if move_match2:
                     moves.append({'level': int(move_match2.group(3)), 'name': move_match2.group(2).strip().lower().replace(' ', '-'), 'marker': move_match2.group(1)})
        move_changes[pkmn_name] = moves
    return move_changes, move_stat_changes

def parse_trainers():
    trainers = {} 
    with open(os.path.join(DATA_DIR, "Important Trainer Rosters.txt"), 'r', encoding='utf-8', errors='ignore') as f:
        imp_content = f.read()
    entries = re.split(r'\n\s*\n(?=Rival|Gym Leader|PKMN Trainer|Elite Four|Team Plasma|Champion|GAME Freak|N’s Team|Bianca’s Team|Cheren’s Team)', imp_content)
    current_trainer, current_location = None, None
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
                if len(parts) > 1 and any(x in parts[1] for x in ["Route", "Town", "City", "Gym"]): current_location = parts[1].strip()
        if "Team" in header and current_location:
            trainer_name = current_trainer if current_trainer else header
            trainer_data = {'name': trainer_name, 'pokemon': [], 'important': True}
            def split_list(match):
                if not match: return []
                raw = match[0].strip()
                items = [x.strip() for x in raw.split('\n') if x.strip()]
                if len(items) == 1 and ' ' in raw: items = [x.strip() for x in raw.split('  ') if x.strip()]
                return items
            s_list = split_list(re.findall(r'Species\|([^|]+)', entry))
            l_list = split_list(re.findall(r'Level\|([^|]+)', entry))
            i_list = split_list(re.findall(r'Item\|([^|]+)', entry))
            a_list = split_list(re.findall(r'Ability\|([^|]+)', entry))
            m1_list = split_list(re.findall(r'Move #1\|([^|]+)', entry))
            m2_list = split_list(re.findall(r'Move #2\|([^|]+)', entry))
            m3_list = split_list(re.findall(r'Move #3\|([^|]+)', entry))
            m4_list = split_list(re.findall(r'Move #4\|([^|]+)', entry))
            for j in range(len(s_list)):
                p_data = {'name': s_list[j], 'level': l_list[j] if j < len(l_list) else "?", 'item': i_list[j] if j < len(i_list) else "-", 'ability': a_list[j] if j < len(a_list) else "-", 'moves': []}
                if j < len(m1_list): p_data['moves'].append(m1_list[j])
                if j < len(m2_list): p_data['moves'].append(m2_list[j])
                if j < len(m3_list): p_data['moves'].append(m3_list[j])
                if j < len(m4_list): p_data['moves'].append(m4_list[j])
                trainer_data['pokemon'].append(p_data)
            if current_location not in trainers: trainers[current_location] = []
            trainers[current_location].append(trainer_data)
    
    with open(os.path.join(DATA_DIR, "Trainer Rosters.txt"), 'r', encoding='utf-8', errors='ignore') as f:
        gen_content = f.read()
    
    # We want to capture the order of locations in Trainer Rosters too
    trainer_locations_ordered = []
    sections = gen_content.split('\n---\n')
    for i in range(0, len(sections)-1):
        loc_lines = sections[i].strip().split('\n')
        location = loc_lines[-1].strip()
        if location not in trainer_locations_ordered: trainer_locations_ordered.append(location)
        trainer_lines = sections[i+1].strip().split('\n')
        if i+1 < len(sections):
             trainer_list = []
             for line in trainer_lines:
                 if not line.strip() or line.strip() == location: continue
                 trainer_list.append(line.strip())
             for t_line in trainer_list:
                 if t_line.startswith('*'): continue
                 match = re.match(r'([^:]+):\s+(.+)', t_line)
                 if match:
                     t_name, pkmn_raw = match.group(1).strip(), match.group(2).strip()
                     trainer_data = {'name': t_name, 'pokemon': [], 'important': False}
                     for pk_entry in pkmn_raw.split(','):
                         pk_match = re.match(r'(.+)\s+L(\d+)', pk_entry.strip())
                         if pk_match: trainer_data['pokemon'].append({'name': pk_match.group(1).strip(), 'level': pk_match.group(2).strip(), 'moves': [], 'item': '-', 'ability': '-'})
                     if location not in trainers: trainers[location] = []
                     trainers[location].append(trainer_data)
    return trainers, trainer_locations_ordered

if __name__ == "__main__":
    pokemon_changes = parse_pokemon_changes()
    wild_pkmn = parse_wild_pokemon()
    move_changes, move_stat_changes = parse_move_changes()
    trainer_data, trainer_order = parse_trainers()
    
    # Identify unique route names from wild_pkmn to preserve order
    wild_order = [r['name'] for r in wild_pkmn]
    
    with open('scripts/data/romhack_data.json', 'w') as f: 
        json.dump({
            'pokemon_changes': pokemon_changes, 
            'wild_pokemon': wild_pkmn, 
            'move_changes': move_changes, 
            'move_stat_changes': move_stat_changes, 
            'trainers': trainer_data,
            'trainer_order': trainer_order,
            'wild_order': wild_order
        }, f, indent=2)
    print("Parsing complete.")
