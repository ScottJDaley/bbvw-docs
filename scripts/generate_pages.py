import json
import os
import re

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
            return f'<span class="change-new">{rom_val["new"]}</span> <span class="change-old">{rom_val["old"]}</span>'
        return str(base_val or '-')

    power = format_stat('power', m_info['power'])
    acc = format_stat('accuracy', m_info['accuracy'])
    
    type_icon = f'<img src="img/types/{m_info["type"]}.png" width="40" alt="{m_info["type"]}" />'
    cat_icon = f'<img src="img/types/{m_info["damage_class"]}.png" width="30" alt="{m_info["damage_class"]}" />'
    
    return f"| {type_icon} | [{m_info['name'].replace('-', ' ').capitalize()}](moves/{m_info['name']}.md) | {cat_icon} | {power} | {acc} | {m_info['pp']} |"

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
    
    def get_ab_link(ab_name, is_new=False):
        if not ab_name: return ""
        norm = ab_name.lower().replace(' ', '-')
        desc = ability_data.get(norm, {}).get('description', '')
        prefix = '<span class="change-new-label">NEW</span> ' if is_new else ""
        return f"- {prefix}**[{ab_name}](abilities/{norm}.md)**: {desc}\n"

    orig_abs = [a.replace('-', ' ').capitalize() for a in p_base['abilities']]
    if ab1_new: md += get_ab_link(ab1_new, ab1_new not in orig_abs)
    if ab2_new: md += get_ab_link(ab2_new, ab2_new not in orig_abs)
    if not ab1_new and not ab2_new:
        for ab in orig_abs:
            md += get_ab_link(ab)
    md += "\n"
    
    # Type Defenses
    md += "## Type Defenses\n"
    eff = get_type_effectiveness(curr_types)
    md += "| Weaknesses (2x+) | Resistances (0.5x-) | Immunities (0x) |\n"
    md += "| --- | --- | --- |\n"
    
    def format_eff_list(filter_fn):
        res = []
        for t, v in eff.items():
            if filter_fn(v):
                res.append(f'<img src="img/types/{t}.png" width="40" /> x{v}')
        return ", ".join(res)

    weak = format_eff_list(lambda v: v > 1)
    resist = format_eff_list(lambda v: 0 < v < 1)
    imm = format_eff_list(lambda v: v == 0)
    md += f"| {weak} | {resist} | {imm} |\n\n"

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
    
    # Level Up Moves
    md += "## Level Up Moves\n"
    md += "| Level | Type | Move | Cat | Power | Acc | PP |\n"
    md += "| --- | --- | --- | --- | --- | --- | --- |\n"
    
    moves = p_moves_rom if p_moves_rom else [m for m in p_base['moves'] if m['method'] == 'level-up']
    moves.sort(key=lambda x: x['level'])
    
    for m in moves:
        row = get_move_display(m['name'], move_data, rom_data['move_stat_changes'])
        marker = m.get('marker', '')
        prefix = ""
        if marker == '+': prefix = '<span class="change-new-label">NEW</span> '
        elif marker == '-': prefix = '<span class="change-old-label">REPLACED</span> '
        elif marker == '=': prefix = '<span class="change-move-shifted">SHIFTED</span> '
        
        md += f"| {prefix}{m['level']} {row}\n"
    
    # Learnable Moves
    md += "\n## Learnable Moves\n"
    md += "| Type | Move | Cat | Power | Acc | PP |\n"
    md += "| --- | --- | --- | --- | --- | --- |\n"
    learnable = [m for m in p_base['moves'] if m['method'] != 'level-up']
    learnable.sort(key=lambda x: x['name'])
    for m in learnable:
        row = get_move_display(m['name'], move_data, rom_data['move_stat_changes'])
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

def generate_route_page(name, route_data, base_data, trainer_data):
    md = f"# {name}\n\n"
    
    # Encounters
    md += "## Encounters\n"
    md += "| Method | Sprite | Pokemon | Rate |\n"
    md += "| --- | --- | --- | --- |\n"
    for enc in route_data['encounters']:
        p_name = enc['pokemon'].lower()
        p_info = base_data.get(p_name)
        sprite = f'<img src="img/pokemon/{p_info["id"]:03}.png" width="40" />' if p_info else ""
        method = enc['method'].lower()
        m_icon = ""
        if 'grass' in method: m_icon = '<img src="img/items/grass.png" width="30" />'
        elif 'fish' in method: m_icon = '<img src="img/items/fishing-rod.png" width="30" />'
        elif 'surf' in method: m_icon = '<img src="img/items/surf.png" width="30" />'
        md += f"| {m_icon} {enc['method']} | {sprite} | [{enc['pokemon']}](pokemon/{p_name}.md) | {enc['rate']}% |\n"
    
    # Trainers
    location_trainers = trainer_data.get(name)
    if location_trainers:
        md += "\n## Trainers\n"
        for trainer in location_trainers:
            md += f"### {trainer['name']}\n"
            md += "| Sprite | Pokemon | Level | Ability | Item | Moves |\n"
            md += "| --- | --- | --- | --- | --- | --- |\n"
            for p in trainer['pokemon']:
                p_base = base_data.get(p['name'].lower())
                sprite = f'<img src="img/pokemon/{p_base["id"]:03}.png" width="40" />' if p_base else ""
                md += f"| {sprite} | {p['name']} | {p['level']} | {p['ability']} | {p['item']} | {', '.join(p['moves'])} |\n"
            md += "\n"

    return md

if __name__ == "__main__":
    base, romhack = load_data()
    if not os.path.exists("docs/pokemon"): os.makedirs("docs/pokemon")
    for name in base['pokemon']:
        md = generate_pokemon_page(name, base['pokemon'], romhack, base['moves'], base['abilities'])
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
