import json
import os

DATA_DIR = "scripts/data"
OUTPUT_DIR = "pokemon"

def load_data():
    with open(os.path.join(DATA_DIR, "base_data.json"), 'r') as f:
        base = json.load(f)
    with open(os.path.join(DATA_DIR, "romhack_data.json"), 'r') as f:
        romhack = json.load(f)
    return base, romhack

def generate_pokemon_page(name, base_data, rom_data, move_data, ability_data):
    p_base = base_data.get(name)
    if not p_base: return
    
    p_rom = rom_data['pokemon_changes'].get(name, {})
    p_moves_rom = rom_data['move_changes'].get(name, [])
    
    md = f"# {name.capitalize()}\n\n"
    
    # Sprite (using leading zeros for IDs)
    md += f'<img src="img/pokemon/{p_base["id"]:03}.png" width="150" />\n\n'
    
    # Types
    types_orig = p_base['types']
    types_new = p_rom.get('types')
    md += "## Type\n"
    if types_new and types_new != types_orig:
        md += "Original: " + ' '.join([f'<span class="type-badge type-{t}">{t}</span>' for t in types_orig]) + "  \n"
        md += "New: " + ' '.join([f'<span class="type-badge type-{t}">{t}</span>' for t in types_new]) + "\n\n"
    else:
        md += ' '.join([f'<span class="type-badge type-{t}">{t}</span>' for t in types_orig]) + "\n\n"
        
    # Abilities
    md += "## Abilities\n"
    ab1_new = p_rom.get('abilities', {}).get('one')
    ab2_new = p_rom.get('abilities', {}).get('two')
    
    def get_ab_desc(ab_name):
        if not ab_name: return ""
        norm_name = ab_name.lower().replace(' ', '-')
        return ability_data.get(norm_name, {}).get('description', '')

    if ab1_new:
        md += f"- **{ab1_new}**: {get_ab_desc(ab1_new)}\n"
    if ab2_new:
        md += f"- **{ab2_new}**: {get_ab_desc(ab2_new)}\n"
    
    if not ab1_new and not ab2_new:
        for ab in p_base['abilities']:
            md += f"- **{ab.capitalize()}**: {get_ab_desc(ab)}\n"
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
            delta = new_val - orig_val
            display_val = f'<span class="change-new">{new_val}</span> <span class="change-old">{orig_val}</span> <span class="change-delta">({"+" if delta > 0 else ""}{delta})</span>'
        
        # Simple bar (max assumed 255)
        bar_width = min(100, (new_val / 200) * 100)
        bar = f'<div class="stat-bar-bg"><div class="stat-bar-fill" style="width:{bar_width}%"></div></div>'
        
        md += f"| {stat.capitalize().replace('-', ' ')} | {display_val} | {bar} |\n"
    
    # Total
    orig_total = sum(stats_orig.values())
    new_total_data = stats_new.get('total')
    new_total = new_total_data['new'] if new_total_data else orig_total
    md += f"| **Total** | **{new_total}** | |\n\n"
    
    # Level Up Moves
    md += "## Level Up Moves\n"
    md += "| Level | Move | Type | Cat | Power | Acc | PP |\n"
    md += "| --- | --- | --- | --- | --- | --- | --- |\n"
    
    moves = p_moves_rom if p_moves_rom else [m for m in p_base['moves'] if m['method'] == 'level-up']
    # Sort moves by level
    moves.sort(key=lambda x: x['level'])
    
    for m in moves:
        m_info = move_data.get(m['name'])
        if m_info:
            md += f"| {m['level']} | [{m_info['name'].capitalize()}](moves/{m_info['name']}.md) | {m_info['type'].capitalize()} | {m_info['damage_class'].capitalize()} | {m_info['power'] or '-'} | {m_info['accuracy'] or '-'} | {m_info['pp']} |\n"
        else:
            md += f"| {m['level']} | {m['name'].capitalize()} | - | - | - | - | - |\n"
            
    return md

def generate_move_page(name, move_info, pokemon_list):
    md = f"# {name.capitalize()}\n\n"
    md += f"**Type:** {move_info['type'].capitalize()}  \n"
    md += f"**Category:** {move_info['damage_class'].capitalize()}  \n"
    md += f"**Power:** {move_info['power'] or '-'}  \n"
    md += f"**Accuracy:** {move_info['accuracy'] or '-'}  \n"
    md += f"**PP:** {move_info['pp']}  \n\n"
    md += f"## Description\n{move_info['description']}\n\n"
    md += "## Learned by\n"
    for p in sorted(pokemon_list):
        md += f"- [{p.capitalize()}](pokemon/{p}.md)\n"
    return md

def generate_ability_page(name, ability_info, pokemon_list):
    md = f"# {name.capitalize()}\n\n"
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
        md = generate_move_page(m_name, m_info, move_to_pokemon.get(m_name, []))
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
    for r_name, r_data in romhack['wild_pokemon'].items():
        md = generate_route_page(r_name, r_data)
        # Normalize filename
        fname = r_name.lower().replace(' ', '_').replace('’', '').replace("'", "").replace('/', '_')
        with open(os.path.join("docs/routes", f"{fname}.md"), 'w') as f: f.write(md)
        
    # 5. Sidebar
    with open("docs/_sidebar.md", 'w') as f:
        f.write("- [Home](README.md)\n")
        f.write("- Pokemon\n")
        for name in sorted(base['pokemon'].keys()):
            f.write(f"  - [{name.capitalize()}](pokemon/{name}.md)\n")
        f.write("- Routes\n")
        for r_name in sorted(romhack['wild_pokemon'].keys()):
            fname = r_name.lower().replace(' ', '_').replace('’', '').replace("'", "").replace('/', '_')
            f.write(f"  - [{r_name}](routes/{fname}.md)\n")
            
    print("All pages generated.")
