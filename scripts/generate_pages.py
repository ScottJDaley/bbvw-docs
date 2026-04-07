import json
import os
import re

DATA_DIR = "scripts/data"
OUTPUT_BASE = "docs"

# Type Effectiveness Chart (Gen 5)
TYPE_CHART = {
    'normal': {'rock': 0.5, 'ghost': 0, 'steel': 0.5},
    'fire': {'fire': 0.5, 'water': 0.5, 'grass': 2, 'ice': 2, 'bug': 2, 'rock': 0.5, 'dragon': 0.5, 'steel': 2},
    'water': {'fire': 2, 'water': 0.5, 'grass': 0.5, 'ground': 2, 'rock': 2, 'dragon': 0.5},
    'electric': {'water': 2, 'electric': 0.5, 'grass': 0.5, 'ground': 0, 'flying': 2, 'dragon': 0.5},
    'grass': {'fire': 0.5, 'water': 2, 'grass': 0.5, 'poison': 0.5, 'ground': 2, 'flying': 0.5, 'bug': 0.5, 'rock': 2, 'dragon': 0.5, 'steel': 0.5},
    'ice': {'fire': 0.5, 'water': 0.5, 'grass': 2, 'ice': 0.5, 'ground': 2, 'flying': 2, 'dragon': 2, 'steel': 0.5},
    'fighting': {'normal': 2, 'ice': 2, 'poison': 0.5, 'flying': 0.5, 'psychic': 0.5, 'bug': 0.5, 'rock': 2, 'ghost': 0, 'dark': 2, 'steel': 2},
    'poison': {'grass': 2, 'poison': 0.5, 'ground': 0.5, 'rock': 0.5, 'ghost': 0.5, 'steel': 0},
    'ground': {'fire': 2, 'electric': 2, 'grass': 0.5, 'poison': 2, 'flying': 0, 'bug': 0.5, 'rock': 2, 'steel': 2},
    'flying': {'electric': 0.5, 'grass': 2, 'fighting': 2, 'bug': 2, 'rock': 0.5, 'steel': 0.5},
    'psychic': {'fighting': 2, 'poison': 2, 'psychic': 0.5, 'dark': 0, 'steel': 0.5},
    'bug': {'fire': 0.5, 'grass': 2, 'fighting': 0.5, 'poison': 0.5, 'flying': 0.5, 'psychic': 2, 'ghost': 0.5, 'dark': 2, 'steel': 0.5},
    'rock': {'fire': 2, 'ice': 2, 'fighting': 0.5, 'ground': 0.5, 'flying': 2, 'bug': 2, 'steel': 0.5},
    'ghost': {'normal': 0, 'psychic': 2, 'ghost': 2, 'dark': 0.5},
    'dragon': {'dragon': 2, 'steel': 0.5},
    'dark': {'fighting': 0.5, 'psychic': 2, 'ghost': 2, 'dark': 0.5},
    'steel': {'fire': 0.5, 'water': 0.5, 'electric': 0.5, 'ice': 2, 'rock': 2, 'steel': 0.5},
}

def get_type_effectiveness(types):
    effectiveness = {t: 1.0 for t in TYPE_CHART.keys()}
    for t_def in types:
        if t_def not in TYPE_CHART: continue
        for t_atk, chart in TYPE_CHART.items():
            if t_def in chart:
                effectiveness[t_atk] *= chart[t_def]
    return effectiveness

def load_data():
    with open(os.path.join(DATA_DIR, "base_data.json"), 'r') as f:
        base = json.load(f)
    with open(os.path.join(DATA_DIR, "romhack_data.json"), 'r') as f:
        romhack = json.load(f)
    return base, romhack

def get_move_display(m_name, move_data, move_stat_changes, p_moves_base=None):
    m_info = move_data.get(m_name)
    if not m_info:
        return f"| - | {m_name.replace('-', ' ').capitalize()} | - | - | - | - | - |"
    
    m_rom = move_stat_changes.get(m_name, {})
    
    def format_stat(stat_name, base_val):
        rom_val = m_rom.get(stat_name)
        if rom_val:
            return f'<span class="change-new">{rom_val["new"]}</span> <span class="change-old">{rom_val["old"]}</span>'
        return str(base_val or '-')

    power = format_stat('power', m_info['power'])
    acc = format_stat('accuracy', m_info['accuracy'])
    
    type_icon = f'<img src="img/types/{m_info["type"]}.png" width="40" alt="{m_info["type"]}" />'
    cat_icon = f'<img src="img/types/{m_info["damage_class"]}.png" width="30" style="vertical-align:middle; object-fit:contain;" alt="{m_info["damage_class"]}" />'
    
    # Check if TM/HM
    tm_num = ""
    if p_moves_base:
        for bm in p_moves_base:
            if bm['name'] == m_name and bm['method'] == 'machine':
                # This is simplified, real TM numbers need mapping
                tm_num = "TM?? "
                break

    display_name = f"{tm_num}{m_info['name'].replace('-', ' ').capitalize()}"
    
    return f"| {type_icon} | [{display_name}](moves/{m_info['name']}.md) | {cat_icon} | {power} | {acc} | {m_info['pp']} |"

def get_default_evolution(p_base):
    def extract_evo(chain, target_name):
        if chain['species']['name'] == target_name:
            if not chain['evolution_details']: return "First Stage"
            details = chain['evolution_details'][0]
            method = details['trigger']['name']
            if method == 'level-up':
                if details['min_level']: return f"Level {details['min_level']}"
                if details['min_happiness']: return "Happiness"
                if details['held_item']: return f"Hold {details['held_item']['name']}"
                if details['location']: return f"Level up at {details['location']['name']}"
                if details['known_move']: return f"Know {details['known_move']['name']}"
            if method == 'use-item':
                return f"Use {details['item']['name']}"
            if method == 'trade':
                if details['held_item']: return f"Trade holding {details['held_item']['name']}"
                return "Trade"
            return method
        for evolves_to in chain['evolves_to']:
            res = extract_evo(evolves_to, target_name)
            if res: return res
        return None

    chain = p_base['evolution_chain']['chain']
    return extract_evo(chain, p_base['name'])

def generate_pokemon_page(name, base_data, rom_data, move_data, ability_data, locations):
    p_base = base_data.get(name)
    if not p_base: return
    
    p_rom = rom_data['pokemon_changes'].get(name, {})
    p_moves_rom = rom_data['move_changes'].get(name, [])
    
    md = f"# {name.capitalize()}\n\n"
    md += f'<img src="img/pokemon/{p_base["id"]:03}.png" width="150" />\n\n'
    
    # Types
    types_orig = p_base['types']
    types_new = p_rom.get('types')
    curr_types = types_new if types_new else types_orig
    md += "## Type\n"
    if types_new and types_new != types_orig:
        md += "Original: " + ' '.join([f'<img src="img/types/{t}.png" width="60" />' for t in types_orig]) + "  \n"
        md += "New: " + ' '.join([f'<img src="img/types/{t}.png" width="60" />' for t in types_new]) + "\n\n"
    else:
        md += ' '.join([f'<img src="img/types/{t}.png" width="60" />' for t in types_orig]) + "\n\n"
        
    # Evolution
    md += "## Evolution\n"
    default_evo = get_default_evolution(p_base)
    md += f"**Base Game:** {default_evo}  \n"
    if p_rom.get('evolution'):
        for evo in p_rom['evolution']:
            target = evo['target'] if evo['target'] else "Next Stage"
            md += f"**New:** {target}: {evo['method']}\n"
    md += "\n"

    # Abilities
    md += "## Abilities\n"
    ab1_new = p_rom.get('abilities', {}).get('one')
    ab2_new = p_rom.get('abilities', {}).get('two')
    orig_abs = [a.replace('-', ' ').capitalize() for a in p_base['abilities']]
    
    def get_ab_info(ab_name):
        norm = ab_name.lower().replace(' ', '-')
        desc = ability_data.get(norm, {}).get('description', '')
        return f"**[{ab_name}](abilities/{norm}.md)**: {desc}"

    if ab1_new or ab2_new:
        md += "| Slot | Original | New |\n"
        md += "| --- | --- | --- |\n"
        orig1 = orig_abs[0] if len(orig_abs) > 0 else "-"
        new1 = ab1_new if ab1_new else orig1
        md += f"| Ability 1 | {get_ab_info(orig1) if orig1 != '-' else '-'} | {get_ab_info(new1)} |\n"
        orig2 = orig_abs[1] if len(orig_abs) > 1 else "-"
        new2 = ab2_new if ab2_new else (orig2 if orig2 != "-" else "-")
        md += f"| Ability 2 | {get_ab_info(orig2) if orig2 != '-' else '-'} | {get_ab_info(new2) if new2 != '-' else '-'} |\n"
    else:
        for ab in orig_abs:
            md += f"- {get_ab_info(ab)}\n"
    md += "\n"
    
    # Type Defenses
    md += "## Type Defenses\n"
    eff = get_type_effectiveness(curr_types)
    md += "| Type | Effectiveness |\n"
    md += "| --- | --- |\n"
    sorted_eff = sorted(eff.items(), key=lambda x: x[1], reverse=True)
    for t, v in sorted_eff:
        if v != 1.0:
            md += f"| <img src='img/types/{t}.png' width='40' /> | x{v} |\n"
    md += "\n"

    # Base Stats
    md += "## Base Stats\n"
    md += "| Stat | Value | Bar |\n"
    md += "| --- | --- | --- |\n"
    stats_orig = p_base['stats']
    stats_new = p_rom.get('stats', {})
    for stat in ['hp', 'attack', 'defense', 'special-attack', 'special-defense', 'speed']:
        orig_val = stats_orig.get(stat, 0)
        new_data = stats_new.get(stat.replace('-', '_'))
        new_val = new_data['new'] if new_data else orig_val
        display_val = f"{new_val}"
        if new_data:
            display_val = f'<span class="change-new">{new_val}</span> <span class="change-old">{orig_val}</span>'
        bar_width = min(100, (new_val / 200) * 100)
        bar = f'<div class="stat-bar-bg"><div class="stat-bar-fill" style="width:{bar_width}%"></div></div>'
        md += f"| {stat.capitalize().replace('-', ' ')} | {display_val} | {bar} |\n"
    md += "\n"
    
    # Locations
    if name in locations:
        md += "## Locations\n"
        md += "| Route | Method | Rate |\n"
        md += "| --- | --- | --- |\n"
        for loc in locations[name]:
            fname = loc['route'].lower().replace(' ', '_').replace('’', '').replace("'", "").replace('/', '_')
            md += f"| [{loc['route']}](routes/{fname}.md) | {loc['method']} | {loc['rate']}% |\n"
        md += "\n"

    # Level Up Moves
    md += "## Level Up Moves\n"
    md += "| Level | Type | Move | Cat | Power | Acc | PP | Change |\n"
    md += "| --- | --- | --- | --- | --- | --- | --- | --- |\n"
    
    base_lv_moves = [m for m in p_base['moves'] if m['method'] == 'level-up']
    rom_moves = p_moves_rom
    
    all_moves = []
    
    if not rom_moves:
        for bm in base_lv_moves:
            all_moves.append({'level': bm['level'], 'name': bm['name'], 'marker': ''})
    else:
        # Add all ROM moves
        for rm in rom_moves:
            all_moves.append(rm)
        
        # Add base moves if they weren't replaced or shifted
        for bm in base_lv_moves:
            is_affected = False
            for rm in rom_moves:
                if rm['name'] == bm['name'] and rm['marker'] in ['-', '=']:
                    is_affected = True
                    break
            if not is_affected:
                all_moves.append({'level': bm['level'], 'name': bm['name'], 'marker': ''})
            else:
                # If it was replaced at THIS level, it's "REMOVED" from this level
                was_replaced_here = False
                for rm in rom_moves:
                    if rm['level'] == bm['level'] and rm['marker'] == '-':
                        was_replaced_here = True
                        break
                if was_replaced_here:
                    # Don't add base move if it was explicitly replaced by something else at the same level
                    pass

    all_moves.sort(key=lambda x: x['level'])
    
    for m in all_moves:
        row = get_move_display(m['name'], move_data, rom_data['move_stat_changes'])
        marker = m.get('marker', '')
        change_text = ""
        if marker == '+': change_text = '<span class="change-new-label">NEW</span>'
        elif marker == '-': change_text = '<span class="change-old-label">REPLACED</span>'
        elif marker == '=': 
            old_lv = next((x['level'] for x in base_lv_moves if x['name'] == m['name']), "?")
            change_text = f'<span class="change-move-shifted">SHIFTED (from {old_lv})</span>'
        
        md += f"| {m['level']} {row} {change_text} |\n"
    
    # Learnable Moves
    md += "\n## Learnable Moves\n"
    md += "| Type | Move | Cat | Power | Acc | PP |\n"
    md += "| --- | --- | --- | --- | --- | --- |\n"
    learnable = [m for m in p_base['moves'] if m['method'] != 'level-up']
    learnable.sort(key=lambda x: x['name'])
    for m in learnable:
        row = get_move_display(m['name'], move_data, rom_data['move_stat_changes'], p_base['moves'])
        row_parts = row.split('|')
        md += "|" + "|".join(row_parts[1:]) + "\n"
            
    return md

def generate_move_page(name, move_info, pokemon_list, m_rom):
    md = f"# {name.replace('-', ' ').capitalize()}\n\n"
    def format_stat(stat_name, base_val):
        rom_val = m_rom.get(stat_name)
        if rom_val:
            return f'<span class="change-new">{rom_val["new"]}</span> <span class="change-old">{rom_val["old"]}</span>'
        return str(base_val or '-')
    power = format_stat('power', move_info['power'])
    acc = format_stat('accuracy', move_info['accuracy'])
    md += f"**Type:** <img src=\"img/types/{move_info['type']}.png\" width=\"60\" />  \n"
    md += f"**Category:** <img src=\"img/types/{move_info['damage_class']}.png\" width=\"50\" style=\"object-fit:contain;\" />  \n"
    md += f"**Power:** {power}  \n"
    md += f"**Accuracy:** {acc}  \n"
    md += f"**PP:** {move_info['pp']}  \n\n"
    md += f"## Description\n{move_info['description']}\n\n"
    md += "## Learned by\n"
    for p in sorted(pokemon_list):
        md += f"- [{p.capitalize()}](pokemon/{p}.md)\n"
    return md

def generate_ability_page(name, ability_info, pokemon_list):
    md = f"# {name.replace('-', ' ').capitalize()}\n\n"
    md += f"## Description\n{ability_info['description']}\n\n"
    md += "## Pokemon with this Ability\n"
    for p in sorted(pokemon_list):
        md += f"- [{p.capitalize()}](pokemon/{p}.md)\n"
    return md

def generate_route_page(name, route_data, base_data, trainer_data):
    md = f"# {name}\n\n"
    
    methods = {}
    for enc in route_data['encounters']:
        m = enc['method']
        if m not in methods: methods[m] = []
        methods[m].append(enc)
        
    for m, encs in methods.items():
        m_lower = m.lower()
        icon_name = "grass-normal.png"
        if 'doubles' in m_lower: icon_name = "grass-doubles.png"
        elif 'special' in m_lower: icon_name = "grass-special.png"
        elif 'surf' in m_lower: icon_name = "surf-normal.png"
        elif 'fish' in m_lower: icon_name = "fishing-normal.png"
        
        md += f"## <img src='img/items/{icon_name}' width='30' style='vertical-align:middle;' /> {m}\n"
        md += "| Sprite | Pokemon | Rate |\n"
        md += "| --- | --- | --- |\n"
        for enc in encs:
            p_name = enc['pokemon'].lower().replace(' ', '-').replace('.', '')
            p_info = base_data.get(p_name)
            sprite = f'<img src="img/pokemon/{p_info["id"]:03}.png" width="40" />' if p_info else ""
            md += f"| {sprite} | [{enc['pokemon']}](pokemon/{p_name}.md) | {enc['rate']}% |\n"
        md += "\n"
    
    location_trainers = trainer_data.get(name)
    if location_trainers:
        md += "\n## Trainers\n"
        for trainer in location_trainers:
            md += f"### {trainer['name']}\n"
            md += "| Sprite | Pokemon | Level | Ability | Item | Moves |\n"
            md += "| --- | --- | --- | --- | --- | --- |\n"
            for p in trainer['pokemon']:
                p_norm = p['name'].lower().replace(' ', '-').replace('.', '')
                p_base = base_data.get(p_norm)
                sprite = f'<img src="img/pokemon/{p_base["id"]:03}.png" width="40" />' if p_base else ""
                md += f"| {sprite} | {p['name']} | {p['level']} | {p['ability']} | {p['item']} | {', '.join(p['moves'])} |\n"
            md += "\n"

    return md

if __name__ == "__main__":
    base, romhack = load_data()
    
    locations = {}
    for r_data in romhack['wild_pokemon']:
        r_name = r_data['name']
        for enc in r_data['encounters']:
            p_name = enc['pokemon'].lower().replace(' ', '-').replace('.', '')
            if p_name not in locations: locations[p_name] = []
            locations[p_name].append({'route': r_name, 'method': enc['method'], 'rate': enc['rate']})

    if not os.path.exists("docs/pokemon"): os.makedirs("docs/pokemon")
    for name in base['pokemon']:
        md = generate_pokemon_page(name, base['pokemon'], romhack, base['moves'], base['abilities'], locations)
        with open(os.path.join("docs/pokemon", f"{name}.md"), 'w') as f: f.write(md)
    if not os.path.exists("docs/moves"): os.makedirs("docs/moves")
    move_to_pokemon = {}
    for p_name, p_data in base['pokemon'].items():
        for m in p_data['moves']:
            if m['name'] not in move_to_pokemon: move_to_pokemon[m['name']] = []
            move_to_pokemon[m['name']].append(p_name)
    for m_name, m_info in base['moves'].items():
        md = generate_move_page(m_name, m_info, move_to_pokemon.get(m_name, []), romhack['move_stat_changes'].get(m_name, {}))
        with open(os.path.join("docs/moves", f"{m_name}.md"), 'w') as f: f.write(md)
    if not os.path.exists("docs/abilities"): os.makedirs("docs/abilities")
    ability_to_pokemon = {}
    for p_name, p_data in base['pokemon'].items():
        for a in p_data['abilities']:
            if a not in ability_to_pokemon: ability_to_pokemon[a] = []
            ability_to_pokemon[a].append(p_name)
    for a_name, a_info in base['abilities'].items():
        md = generate_ability_page(a_name, a_info, ability_to_pokemon.get(a_name, []))
        with open(os.path.join("docs/abilities", f"{a_name}.md"), 'w') as f: f.write(md)
    if not os.path.exists("docs/routes"): os.makedirs("docs/routes")
    for r_data in romhack['wild_pokemon']:
        r_name = r_data['name']
        md = generate_route_page(r_name, r_data, base['pokemon'], romhack['trainers'])
        fname = r_name.lower().replace(' ', '_').replace('’', '').replace("'", "").replace('/', '_')
        with open(os.path.join("docs/routes", f"{fname}.md"), 'w') as f: f.write(md)
    with open("docs/_sidebar.md", 'w') as f:
        f.write("- [Home](README.md)\n")
        f.write("- **Pokemon**\n")
        pkmn_list = sorted(base['pokemon'].values(), key=lambda x: x['id'])
        gens = [("Gen 1 (1-151)", 1, 151), ("Gen 2 (152-251)", 152, 251), ("Gen 3 (252-386)", 252, 386), ("Gen 4 (387-493)", 387, 493), ("Gen 5 (494-649)", 494, 649)]
        for g_name, start, end in gens:
            f.write(f"  - {g_name}\n")
            for p in pkmn_list:
                if start <= p['id'] <= end: f.write(f"    - [{p['name'].capitalize()}](pokemon/{p['name']}.md)\n")
        f.write("- **Routes**\n")
        for r_data in romhack['wild_pokemon']:
            r_name = r_data['name']
            fname = r_name.lower().replace(' ', '_').replace('’', '').replace("'", "").replace('/', '_')
            f.write(f"  - [{r_name}](routes/{fname}.md)\n")
    print("All pages generated.")
