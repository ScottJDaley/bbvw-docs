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
        move_stat_changes[name.lower().replace(' ', '-')] = {'power': {'old': int(bp_old), 'new': int(bp_new)}, 'accuracy': {'old': int(acc_old), 'new': int(acc_new)}}
    entries = re.split(r'\n(?=#\d{3})', content)
    for entry in entries:
        lines = entry.strip().split('\n'); header = lines[0]
        pkmn_matches = re.findall(r'#(\d{3})\s+([^,\n]+)', header)
        if not pkmn_matches: continue
        target_group = [m[1].strip().lower() for m in pkmn_matches]
        moves_raw = []
        for line in lines[1:]:
            line = line.strip()
            move_match = re.match(r'([+\-=])\s+Level\s+(\d+)\s+-\s+([^(]+)(?:\s+\((.+)\))?', line)
            if move_match:
                marker, lv, mname, filter_text = move_match.groups()
                moves_raw.append({'level': int(lv), 'name': mname.strip().lower().replace(' ', '-'), 'marker': marker, 'filters': [f.strip().lower() for f in filter_text.split(',')] if filter_text else []})
            else:
                 move_match2 = re.match(r'([+\-=])\s+([^(]+)\s+-\s+Level\s+(\d+)(?:\s+\((.+)\))?', line)
                 if move_match2:
                     marker, mname, lv, filter_text = move_match2.groups()
                     moves_raw.append({'level': int(lv), 'name': mname.strip().lower().replace(' ', '-'), 'marker': marker, 'filters': [f.strip().lower() for f in filter_text.split(',')] if filter_text else []})
        for p_name in target_group:
            if p_name not in move_changes: move_changes[p_name] = []
            for mr in moves_raw:
                if not mr['filters'] or p_name in mr['filters']: move_changes[p_name].append({'level': mr['level'], 'name': mr['name'], 'marker': mr['marker']})
    return move_changes, move_stat_changes

def parse_trainers():
    important_rosters = {}
    with open(os.path.join(DATA_DIR, "Important Trainer Rosters.txt"), 'r', encoding='utf-8', errors='ignore') as f:
        imp_content = f.read().replace('Straition', 'Striaton').replace('Striation', 'Striaton')
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
                raw = match[0].strip(); items = [x.strip() for x in raw.split('\n') if x.strip()]
                if len(items) == 1 and ' ' in raw: items = [x.strip() for x in raw.split('  ') if x.strip()]
                return items
            s_list, l_list, i_list, a_list = split_list(re.findall(r'Species\|([^|]+)', entry)), split_list(re.findall(r'Level\|([^|]+)', entry)), split_list(re.findall(r'Item\|([^|]+)', entry)), split_list(re.findall(r'Ability\|([^|]+)', entry))
            m1, m2, m3, m4 = split_list(re.findall(r'Move #1\|([^|]+)', entry)), split_list(re.findall(r'Move #2\|([^|]+)', entry)), split_list(re.findall(r'Move #3\|([^|]+)', entry)), split_list(re.findall(r'Move #4\|([^|]+)', entry))
            for j in range(len(s_list)):
                p_data = {'name': s_list[j], 'level': l_list[j] if j < len(l_list) else "?", 'item': i_list[j] if j < len(i_list) else "-", 'ability': a_list[j] if j < len(a_list) else "-", 'moves': []}
                for ml in [m1, m2, m3, m4]:
                    if j < len(ml): p_data['moves'].append(ml[j])
                trainer_data['pokemon'].append(p_data)
            if current_location not in important_rosters: important_rosters[current_location] = []
            important_rosters[current_location].append(trainer_data)

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
                     name_key = t_line.replace('*', '').strip()
                     # Match from important_rosters
                     found = False
                     for loc, teams in important_rosters.items():
                         for team in teams:
                             if name_key.lower() in team['name'].lower():
                                 if location not in trainers: trainers[location] = []
                                 trainers[location].append(team); found = True; break
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
