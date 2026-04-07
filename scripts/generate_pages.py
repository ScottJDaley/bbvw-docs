import json
import os

DATA_DIR = "scripts/data"
OUTPUT_BASE = "docs"

# Type Effectiveness Chart (simplified for Gen 5)
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

def get_move_display(m_name, move_data, move_stat_changes):
    m_info = move_data.get(m_name)
    if not m_info:
        return f"| - | {m_name.replace('-', ' ').capitalize()} | - | - | - | - | - |"
    
    m_rom = move_stat_changes.get(m_name, {})
    
    def format_stat(stat_name, base_val):
        rom_val = m_rom.get(stat_name)
        if rom_val:
            delta = rom_val['new'] - rom_val['old']
            return f'<span class="change-new">{rom_val["new"]}</span> <span class="change-old">{rom_val["old"]}</span>'
        return str(base_val or '-')

    power = format_stat('power', m_info['power'])
    acc = format_stat('accuracy', m_info['accuracy'])
    
    type_icon = f'<img src="img/types/{m_info["type"]}.png" width="40" alt="{m_info["type"]}" />'
    cat_icon = f'<img src="img/types/{m_info["damage_class"]}.png" width="30" alt="{m_info["damage_class"]}" />'
    
    return f"| {type_icon} | [{m_info['name'].replace('-', ' ').capitalize()}](moves/{m_info['name']}.md) | {cat_icon} | {power} | {acc} | {m_info['pp']} |"

def generate_pokemon_page(name, base_data, rom_data, move_data, ability_data):
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
    if p_rom.get('evolution'):
        for evo in p_rom['evolution']:
            target = evo['target'] if evo['target'] else "Next Stage"
            md += f"- **{target}**: {evo['method']}\n"
    else:
        md += "No changes from base games.\n"
    md += "\n"

    # Abilities
    md += "## Abilities\n"
    ab1_new = p_rom.get('abilities', {}).get('one')
    ab2_new = p_rom.get('abilities', {}).get('two')
    
    def get_ab_link(ab_name):
        if not ab_name: return ""
        norm = ab_name.lower().replace(' ', '-')
        desc = ability_data.get(norm, {}).get('description', '')
        return f"- **[{ab_name}](abilities/{norm}.md)**: {desc}\n"

    if ab1_new: md += get_ab_link(ab1_new)
    if ab2_new: md += get_ab_link(ab2_new)
    if not ab1_new and not ab2_new:
        for ab in p_base['abilities']:
            md += get_ab_link(ab.replace('-', ' ').capitalize())
    md += "\n"
    
    # Type Defenses
    md += "## Type Defenses\n"
    eff = get_type_effectiveness(curr_types)
    md += "| Weaknesses (2x+) | Resistances (0.5x-) | Immunities (0x) |\n"
    md += "| --- | --- | --- |\n"
    weak = [f'<span class="type-badge type-{t}">{t}</span> x{v}' for t, v in eff.items() if v > 1]
    res = [f'<span class="type-badge type-{t}">{t}</span> x{v}' for t, v in eff.items() if 0 < v < 1]
    imm = [f'<span class="type-badge type-{t}">{t}</span>' for t, v in eff.items() if v == 0]
    md += f"| {', '.join(weak)} | {', '.join(res)} | {', '.join(imm)} |\n\n"

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
            delta = new_val - orig_val
            display_val = f'<span class="change-new">{new_val}</span> <span class="change-old">{orig_val}</span>'
        
        bar_width = min(100, (new_val / 180) * 100) # Longer bars
        bar = f'<div class="stat-bar-bg"><div class="stat-bar-fill" style="width:{bar_width}%"></div></div>'
        md += f"| {stat.capitalize().replace('-', ' ')} | {display_val} | {bar} |\n"
    md += "\n"
    
    # Level Up Moves
    md += "## Level Up Moves\n"
    md += "| Level | Type | Move | Cat | Power | Acc | PP |\n"
    md += "| --- | --- | --- | --- | --- | --- | --- |\n"
    moves = p_moves_rom if p_moves_rom else [m for m in p_base['moves'] if m['method'] == 'level-up']
    moves.sort(key=lambda x: x['level'])
    
    base_level_up = [m['name'] for m in p_base['moves'] if m['method'] == 'level-up']
    
    for m in moves:
        row = get_move_display(m['name'], move_data, rom_data['move_stat_changes'])
        prefix = ""
        if p_moves_rom and m['name'] not in base_level_up:
            prefix = '<span class="change-new-label">NEW</span> '
        elif p_moves_rom: # It was in both, but maybe level changed
            old_lv = next((x['level'] for x in p_base['moves'] if x['name'] == m['name'] and x['method'] == 'level-up'), None)
            if old_lv and old_lv != m['level']:
                prefix = f'<span class="change-old-lv">{old_lv}</span> '
        
        md += f"| {prefix}{m['level']} {row}\n"
    
    # Learnable Moves (TM/HM/Tutor)
    md += "\n## Learnable Moves\n"
    md += "| Type | Move | Cat | Power | Acc | PP |\n"
    md += "| --- | --- | --- | --- | --- | --- |\n"
    learnable = [m for m in p_base['moves'] if m['method'] != 'level-up']
    learnable.sort(key=lambda x: x['name'])
    for m in learnable:
        row = get_move_display(m['name'], move_data, rom_data['move_stat_changes'])
        # Remove the leading pipe from row because we don't have level here
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
    md += f"**Category:** <img src=\"img/types/{move_info['damage_class']}.png\" width=\"50\" />  \n"
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

def generate_route_page(name, route_data):
    md = f"# {name}\n\n"
    md += "## Encounters\n"
    md += "| Method | Pokemon | Rate |\n"
    md += "| --- | --- | --- |\n"
    for enc in route_data['encounters']:
        # Try to find sprite
        md += f"| {enc['method']} | [{enc['pokemon']}](pokemon/{enc['pokemon'].lower()}.md) | {enc['rate']}% |\n"
    return md

if __name__ == "__main__":
    base, romhack = load_data()
    
    # 1. Pokemon
    if not os.path.exists("docs/pokemon"): os.makedirs("docs/pokemon")
    for name in base['pokemon']:
        md = generate_pokemon_page(name, base['pokemon'], romhack, base['moves'], base['abilities'])
        with open(os.path.join("docs/pokemon", f"{name}.md"), 'w') as f: f.write(md)
    
    # 2. Moves
    if not os.path.exists("docs/moves"): os.makedirs("docs/moves")
    move_to_pokemon = {}
    for p_name, p_data in base['pokemon'].items():
        for m in p_data['moves']:
            if m['name'] not in move_to_pokemon: move_to_pokemon[m['name']] = []
            move_to_pokemon[m['name']].append(p_name)
            
    for m_name, m_info in base['moves'].items():
        md = generate_move_page(m_name, m_info, move_to_pokemon.get(m_name, []), romhack['move_stat_changes'].get(m_name, {}))
        with open(os.path.join("docs/moves", f"{m_name}.md"), 'w') as f: f.write(md)
        
    # 3. Abilities
    if not os.path.exists("docs/abilities"): os.makedirs("docs/abilities")
    ability_to_pokemon = {}
    for p_name, p_data in base['pokemon'].items():
        for a in p_data['abilities']:
            if a not in ability_to_pokemon: ability_to_pokemon[a] = []
            ability_to_pokemon[a].append(p_name)
            
    for a_name, a_info in base['abilities'].items():
        md = generate_ability_page(a_name, a_info, ability_to_pokemon.get(a_name, []))
        with open(os.path.join("docs/abilities", f"{a_name}.md"), 'w') as f: f.write(md)
        
    # 4. Routes
    if not os.path.exists("docs/routes"): os.makedirs("docs/routes")
    for r_data in romhack['wild_pokemon']:
        r_name = r_data['name']
        md = generate_route_page(r_name, r_data)
        fname = r_name.lower().replace(' ', '_').replace('’', '').replace("'", "").replace('/', '_')
        with open(os.path.join("docs/routes", f"{fname}.md"), 'w') as f: f.write(md)
        
    # 5. Sidebar
    with open("docs/_sidebar.md", 'w') as f:
        f.write("- [Home](README.md)\n")
        f.write("- **Pokemon**\n")
        # Split pokemon into Gen groups for collapsible
        pkmn_list = sorted(base['pokemon'].values(), key=lambda x: x['id'])
        gens = [
            ("Gen 1 (1-151)", 1, 151),
            ("Gen 2 (152-251)", 152, 251),
            ("Gen 3 (252-386)", 252, 386),
            ("Gen 4 (387-493)", 387, 493),
            ("Gen 5 (494-649)", 494, 649),
        ]
        for g_name, start, end in gens:
            f.write(f"  - {g_name}\n")
            for p in pkmn_list:
                if start <= p['id'] <= end:
                    f.write(f"    - [{p['name'].capitalize()}](pokemon/{p['name']}.md)\n")
        
        f.write("- **Routes**\n")
        for r_data in romhack['wild_pokemon']:
            r_name = r_data['name']
            fname = r_name.lower().replace(' ', '_').replace('’', '').replace("'", "").replace('/', '_')
            f.write(f"  - [{r_name}](routes/{fname}.md)\n")
            
    print("All pages generated.")
