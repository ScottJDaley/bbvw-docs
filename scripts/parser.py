import json
import re
import os

DATA_DIR = "scripts/data"

def normalize_name(name):
    if not name: return ""
    # Handle CamelCase (e.g., PoisonPowder -> Poison-Powder)
    name = re.sub(r'([a-z])([A-Z])', r'\1-\2', name)
    name = name.lower().strip()
    if 'nidoran' in name:
        if 'm' in name or '♂' in name: return 'nidoran-m'
        return 'nidoran-f'
    if 'mime jr' in name: return 'mime-jr'
    if 'mr mime' in name: return 'mr-mime'
    # Base names to normalize to
    bases = ['basculin', 'frillish', 'jellicent', 'keldeo', 'meloetta', 'darmanitan', 'tornadus', 'thundurus', 'landorus', 'giratina', 'shaymin', 'deoxys', 'wormadam', 'rotom', 'castform', 'deerling', 'sawsbuck', 'meloetta', 'genesect', 'landorus', 'thundurus', 'tornadus']
    for b in bases:
        if name.startswith(b): return b
    name = name.replace(' ', '-').replace('.', '').replace("'", "").replace('’', '').replace('♂', '-m').replace('♀', '-f').replace('/', '-').replace('–', '-').replace('--', '-').strip('-')
    return name

def parse_pokemon_changes():
    changes = {}
    with open(os.path.join(DATA_DIR, "Pokemon Changes.txt"), 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
    entries = re.split(r'\n(?=#\d{3})', content)
    for entry in entries:
        lines = entry.strip().split('\n')
        if not lines: continue
        header = lines[0]
        pkmn_matches = re.findall(r'#(\d{3})\s+([^,\-\n]+)', header)
        if not pkmn_matches: continue
        pokemon_names = [m[1].strip().lower() for m in pkmn_matches]
        data = {'stats': {}, 'abilities': {}, 'items': [], 'evolution': [], 'types': None, 'tm_hm': [], 'tutor': [], 'happiness': None}
        for line in lines[1:]:
            line = line.strip()
            if not line: continue
            stat_match = re.match(r'(HP|Attack|Defense|Special Attack|Special Defense|Speed|Total):\s+(\d+)\s+à\s+(\d+)', line)
            if stat_match:
                stat_name = stat_match.group(1).lower().replace(' ', '_').replace('-', '_')
                data['stats'][stat_name] = {'old': int(stat_match.group(2)), 'new': int(stat_match.group(3))}
                continue
            hap_match = re.match(r'Base Happiness:\s+(\d+)(?:\s+à\s+(\d+))?', line)
            if hap_match:
                data['happiness'] = {'old': int(hap_match.group(1)), 'new': int(hap_match.group(2))} if hap_match.group(2) else {'new': int(hap_match.group(1))}
                continue
            ab_match = re.match(r'Ability (One|Two):\s+(.+)', line)
            if ab_match: data['abilities'][ab_match.group(1).lower()] = ab_match.group(2).strip()
            type_match = re.match(r'Type:\s+(.+)', line)
            if type_match: data['types'] = [t.strip().lower() for t in type_match.group(1).split('/')]
            item_match = re.match(r'Items?:\s+(.+)', line)
            if item_match: data['items'] = [i.strip() for i in item_match.group(1).split(',')]
            evo_match = re.match(r'Evolution(?:\s+\((.+)\))?:\s+(.+)', line)
            if evo_match: data['evolution'].append({'target': evo_match.group(1), 'method': evo_match.group(2)})
            if line.startswith('TM:') or line.startswith('HM:'): data['tm_hm'].append(line.split(':', 1)[1].strip())
            elif line.startswith('Tutor:'): data['tutor'].append(line.split(':', 1)[1].strip())
        for name in pokemon_names:
            if name: changes[name] = data
    return changes

def parse_wild_pokemon():
    routes = []
    with open(os.path.join(DATA_DIR, "Wild Pokemon.txt"), 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read().replace('Straition', 'Striaton').replace('Striation', 'Striaton')
    sections = re.split(r'={10,}', content)
    for section in sections:
        section = section.strip()
        if not section: continue
        parts = re.split(r'\n\s*\n\s*\n', section)
        if any(x in parts[0] for x in ["Wild Pokémon", "Recall that", "Serebii.net", "649", "Note that"]):
            found_header = False
            for i in range(len(parts)):
                lines = [l.strip() for l in parts[i].split('\n') if l.strip()]
                if not lines: continue
                potential = lines[-1]
                if ":" not in potential and not any(x in potential for x in ["Wild Pokémon", "Recall that", "Serebii.net", "649", "Note that", "Special' refers"]):
                    header, parts = potential, parts[i+1:]; found_header = True; break
            if not found_header: continue
        else: header, parts = parts[0].strip(), parts[1:]
        route_name = re.split(r' – | \dF| B\dF| Inside| Outside| Spring| Summer| Autumn| Winter', header)[0].strip()
        route_data = next((r for r in routes if r['name'] == route_name), None)
        if not route_data:
            route_data = {'name': route_name, 'sections': [], 'specials': []}; routes.append(route_data)
        current_sub_area = header.replace(route_name, '').replace('–', '').strip() or "General"
        for part in parts:
            part = part.strip()
            if not part: continue
            lines = [l.strip() for l in part.split('\n') if l.strip()]
            if not lines: continue
            if "LEGENDARY ENCOUNTER" in lines[0] or "SPECIAL ENCOUNTER" in lines[0]:
                route_data['specials'].append(part); continue
            if any(":" in l for l in lines):
                encounters, title, start_idx = [], current_sub_area, 0
                if ":" not in lines[0]: title, start_idx = lines[0], 1
                for line in lines[start_idx:]:
                    enc_match = re.match(r'([^:]+):\s+(.+)', line)
                    if enc_match:
                        method, pkmn_list = enc_match.group(1).strip(), enc_match.group(2).strip()
                        pkmns = re.findall(r'([^,(]+)\s+\((\d+)%\)', pkmn_list)
                        for pkmn, rate in pkmns: encounters.append({'method': method, 'pokemon': pkmn.strip(), 'rate': int(rate)})
                if encounters: route_data['sections'].append({'title': title, 'encounters': encounters})
            else: current_sub_area = part
    return routes

def parse_move_changes():
    move_changes, move_stat_changes = {}, {}
    with open(os.path.join(DATA_DIR, "Level Up Move Changes.txt"), 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
    stat_matches = re.findall(r'(\w+(?:\s+\w+)?):\s+Base Power\s+(\d+)\s+->\s+(\d+),\s+Accuracy\s+(\d+)\s+->\s+(\d+)', content)
    for name, bp_old, bp_new, acc_old, acc_new in stat_matches:
        move_stat_changes[normalize_name(name)] = {'power': {'old': int(bp_old), 'new': int(bp_new)}, 'accuracy': {'old': int(acc_old), 'new': int(acc_new)}}
    
    entries = re.split(r'\n(?=#\d{3})', content)
    for entry in entries:
        lines = entry.strip().split('\n')
        if not lines: continue
        header = lines[0]
        pkmn_matches = re.findall(r'#(\d{3})\s+([^,\-\n]+)', header)
        if not pkmn_matches: continue
        target_group = [m[1].strip().lower() for m in pkmn_matches]
        
        current_sub_group = target_group
        
        for line in lines[1:]:
            line = line.strip()
            if not line: continue
            
            if "As for the second evolutions" in line:
                if len(target_group) == 6:
                    current_sub_group = target_group[1::2]
                continue

            # Handle removal comments: * Exploud loses Fire Fang, Ice Fang and Thunder Fang from its movelist.
            lose_match = re.match(r'\*\s*(.*?)\s+loses\s+(.*?)\s+from\s+its\s+movelist', line)
            if lose_match:
                who, what = lose_match.groups()
                who_pkmn = [p for p in target_group if who.lower() in p]
                moves_to_lose = [m.strip() for m in re.split(r',| and ', what)]
                for p in who_pkmn:
                    if p not in move_changes: move_changes[p] = []
                    for m in moves_to_lose:
                        move_changes[p].append({'level': 0, 'name': normalize_name(m), 'marker': 'REMOVED'})
                continue

            # Handle substitution comments: * Fire Blast replaces the Imprison at Level 64.
            replace_match = re.match(r'\*\s*(.*?)\s+replaces\s+the\s+(.*?)\s+at\s+Level\s+(\d+)', line)
            if replace_match:
                new_m, old_m, lv = replace_match.groups()
                for p in current_sub_group:
                    if p not in move_changes: move_changes[p] = []
                    move_changes[p].append({'level': int(lv), 'name': normalize_name(old_m), 'marker': 'REMOVED'})
                    move_changes[p].append({'level': int(lv), 'name': normalize_name(new_m), 'marker': '+'})
                continue

            # Handle level shift comments: * All remaining moves have their level at 78, 85, 92.
            shift_match = re.match(r'\*\s*All\s+remaining\s+moves\s+have\s+their\s+level\s+at\s+([\d\s,]+)', line)
            if shift_match:
                lvs = [int(l.strip()) for l in shift_match.group(1).split(',')]
                for p in current_sub_group:
                    if p not in move_changes: move_changes[p] = []
                    # Special marker for generation script to handle "remaining" moves
                    move_changes[p].append({'level_shifts': lvs, 'marker': 'SHIFT_REMAINING'})
                continue

            # Sunkern style "between" moves: + Nature Power between ... and ..., Level 20 (Sunkern, Sunflora)
            between_match = re.match(r'([+\-=]?)\s*(.*?)\s+between\s+.*?\s+and\s+.*?,?\s*Level\s+(\d+)\s*[(\[](.+)[)\]]', line)
            if between_match:
                marker, mname, lv, filter_text = between_match.groups()
                marker = marker if marker else ""
                filters = [f.strip().lower() for f in re.split(r',| and ', filter_text)]
                for p in current_sub_group:
                    if any(f in p or p.startswith(f + "-") for f in filters if f != "only"):
                        if p not in move_changes: move_changes[p] = []
                        move_changes[p].append({'level': int(lv), 'name': normalize_name(mname), 'marker': marker})
                continue

            # Support both (...) and [...] for pokemon filters, and allow spaces in move names
            # Refined filter split to handle "Pikachu and Raichu only"
            move_match = re.match(r'([+\-=]?)\s*Level\s+([\d\s/–-]+)\s*[-–]\s*(.*?)(?:\s*[(\[](.+)[)\]])?\s*$', line)

            if move_match:
                groups = move_match.groups()
                marker = groups[0] if groups[0] else ""
                lv_str = groups[1]
                mname_str = groups[2].strip()
                filter_text = groups[3] if len(groups) == 4 and groups[3] else ""

                levels = [l.strip() for l in re.split(r'[/–-]', lv_str) if l.strip()]
                moves = [m.strip() for m in mname_str.split('/')]
                # Split filter text by comma or " and "
                filters = [f.strip().lower() for f in re.split(r',| and ', filter_text)] if filter_text else []
                
                same_for_all = False
                if filter_text and "same for all" in filter_text.lower():
                    same_for_all = True
                    filters = []

                applicable_pokemon = []
                if filters and not same_for_all:
                    for p in current_sub_group:
                        for f in filters:
                            f_clean = f.replace(" only", "").strip()
                            if not f_clean: continue
                            if f_clean == p or (f_clean + "s" == p) or (p.startswith(f_clean + "-")):
                                applicable_pokemon.append(p)
                                break
                else:
                    applicable_pokemon = current_sub_group

                for j, p_name in enumerate(applicable_pokemon):
                    mname = moves[j] if j < len(moves) else moves[-1]
                    if mname.lower() == "nothing": continue
                    lv = levels[j] if j < len(levels) else levels[-1]
                    if p_name not in move_changes: move_changes[p_name] = []
                    move_changes[p_name].append({'level': int(lv), 'name': normalize_name(mname), 'marker': marker})
    return move_changes, move_stat_changes

def parse_trainers():
    important_rosters = {}
    with open(os.path.join(DATA_DIR, "Important Trainer Rosters.txt"), 'r', encoding='utf-8', errors='ignore') as f:
        imp_content = f.read().replace('Straition', 'Striaton').replace('Striation', 'Striaton')
    
    # Split by major groups (spoiler headers)
    groups = re.split(r'\n\s*\n(?=Rival|Gym Leader|PKMN Trainer|Elite Four|Team Plasma|Champion|GAME Freak)', imp_content)
    for group in groups:
        lines = [l.strip() for l in group.strip().split('\n') if l.strip()]
        if not lines: continue
        
        main_header = lines[0]
        battle_type, reward = "", ""
        for line in lines:
            if "Battle Type:" in line: battle_type = line.replace("Battle Type:", "").strip()
            if "Reward:" in line: reward = line.replace("Reward:", "").strip()
        
        team_blocks = re.split(r'\n\s*\n(?=[^|\n]+’s Team)', group)
        for block in team_blocks:
            block = block.strip()
            title_match = re.match(r'([^|–-]+Team)\s*[–-]\s*([^;,\n]+)', block)
            if not title_match: title_match = re.match(r'([^|\n]+Team)', block)
            if not title_match: continue
            
            team_name = title_match.group(1).strip()
            team_location = title_match.group(2).strip() if len(title_match.groups()) > 1 else ""
            
            def parse_table(text):
                rows = [l.strip() for l in text.split('\n') if '|' in l]
                if not rows: return []
                
                label_sequence = []
                data_storage = {}
                
                # First pass: identify the sequence of labels
                for r in rows:
                    parts = [p.strip() for p in r.split('|')]
                    label = parts[0]
                    if label and any(x in label for x in ['Species', 'Level', 'Item', 'Ability', 'Move #']):
                        if label not in label_sequence:
                            label_sequence.append(label)
                            data_storage[label] = []
                
                if not label_sequence: return []
                
                # Second pass: fill values correctly
                current_label_idx = -1
                for r in rows:
                    parts = [p.strip() for p in r.split('|')]
                    label = parts[0]
                    vals = [p for p in parts[1:] if p]
                    
                    if label and label in data_storage:
                        data_storage[label].extend(vals)
                        current_label_idx = label_sequence.index(label)
                    elif (not label or label == "") and vals:
                        # Anonymous row: use next label in sequence
                        current_label_idx = (current_label_idx + 1) % len(label_sequence)
                        target_label = label_sequence[current_label_idx]
                        data_storage[target_label].extend(vals)
                
                species = data_storage.get('Species', [])
                pokemon = []
                for i in range(len(species)):
                    p = {
                        'name': species[i],
                        'level': data_storage.get('Level', ["?"]*len(species))[i] if i < len(data_storage.get('Level', [])) else "?",
                        'item': data_storage.get('Item', ["-"]*len(species))[i] if i < len(data_storage.get('Item', [])) else "-",
                        'ability': "-",
                        'moves': []
                    }
                    abs_clean = data_storage.get('Ability (Clean)', [])
                    abs_gen = data_storage.get('Ability', [])
                    abs_reg = data_storage.get('Ability (Reg.)', [])
                    if i < len(abs_clean): p['ability'] = abs_clean[i]
                    elif i < len(abs_gen): p['ability'] = abs_gen[i]
                    elif i < len(abs_reg): p['ability'] = abs_reg[i]
                    
                    for m_lab in ['Move #1', 'Move #2', 'Move #3', 'Move #4']:
                        m_list = data_storage.get(m_lab, [])
                        if i < len(m_list): p['moves'].append(m_list[i])
                    pokemon.append(p)
                return pokemon

            pokemon = parse_table(block)
            if not pokemon: continue
            
            if not team_location:
                loc_match = re.search(r'Location:\s+(.+)', block)
                if loc_match: team_location = loc_match.group(1).strip()
                else:
                    for l in lines:
                        if "Location:" in l: team_location = l.replace("Location:", "").strip(); break
            if not team_location: continue
            
            norm_loc = team_location.replace(' Gym', ' City').replace(' Gym', ' Town')
            for city in ['Nacrene', 'Striaton', 'Castelia', 'Nimbasa', 'Driftveil', 'Mistralton', 'Icirrus', 'Opelucid']:
                if city in norm_loc: norm_loc = city + " City"; break
            
            trainer_data = {'name': team_name, 'pokemon': pokemon, 'important': True, 'battle_type': battle_type, 'reward': reward, 'group_header': main_header}
            if norm_loc not in important_rosters: important_rosters[norm_loc] = []
            important_rosters[norm_loc].append(trainer_data)

    trainers, trainer_locations_ordered = {}, []
    with open(os.path.join(DATA_DIR, "Trainer Rosters.txt"), 'r', encoding='utf-8', errors='ignore') as f:
        gen_content = f.read().replace('Straition', 'Striaton').replace('Striation', 'Striaton')
    
    sections = gen_content.split('\n---\n')
    for i in range(0, len(sections)-1):
        location = sections[i].strip().split('\n')[-1].strip()
        if location not in trainer_locations_ordered: trainer_locations_ordered.append(location)
        trainer_lines = sections[i+1].strip().split('\n')
        if i+1 < len(sections):
             for t_line in trainer_lines:
                 t_line = t_line.strip()
                 if not t_line or t_line == location: continue
                 if t_line.startswith('*'):
                     name_key = t_line.replace('*', '').strip().lower()
                     found = False
                     for loc, teams in important_rosters.items():
                         for team in teams:
                             if name_key in team['name'].lower() or any(name_key in p['name'].lower() for p in team['pokemon']):
                                 if location not in trainers: trainers[location] = []
                                 if team not in trainers[location]: trainers[location].append(team)
                                 found = True; break
                         if found: break
                     continue
                 match = re.match(r'([^:]+):\s+(.+)', t_line)
                 if match:
                     t_name, pkmn_raw = match.group(1).strip(), match.group(2).strip()
                     trainer_data = {'name': t_name, 'pokemon': [], 'important': False}
                     for pk_entry in pkmn_raw.split(','):
                         pk_match = re.match(r'(.+)\s+L(\d+)', pk_entry.strip())
                         if pk_match: trainer_data['pokemon'].append({'name': pk_match.group(1).strip(), 'level': pk_match.group(2).strip(), 'moves': [], 'item': '-', 'ability': '-'})
                     if location not in trainers: trainers[location] = []
                     trainers[location].append(trainer_data)
    
    for loc, teams in important_rosters.items():
        if loc not in trainers: trainers[loc] = teams
        else:
            for team in teams:
                if not any(t['name'] == team['name'] for t in trainers[loc]): trainers[loc].append(team)

    return trainers, trainer_locations_ordered

if __name__ == "__main__":
    pokemon_changes = parse_pokemon_changes()
    wild_pkmn = parse_wild_pokemon()
    move_changes, move_stat_changes = parse_move_changes()
    trainer_data, trainer_order = parse_trainers()
    wild_order = [r['name'] for r in wild_pkmn]
    with open('scripts/data/romhack_data.json', 'w') as f: 
        json.dump({'pokemon_changes': pokemon_changes, 'wild_pokemon': wild_pkmn, 'move_changes': move_changes, 'move_stat_changes': move_stat_changes, 'trainers': trainer_data, 'trainer_order': trainer_order, 'wild_order': wild_order}, f, indent=2)
    print("Parsing complete.")
