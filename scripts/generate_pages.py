import json
import os
import re
import yaml

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

def normalize_name(name):
    if not name: return ""
    name = name.replace('NidoranM', 'nidoran-m').replace('NidoranF', 'nidoran-f')
    name = name.replace('Mime Jr.', 'mime-jr').replace('Mr. Mime', 'mr-mime')
    if name.lower().startswith('basculin'): return 'basculin'
    return name.lower().replace(' ', '-').replace('.', '').replace("'", "").replace('’', '').replace('♂', '-m').replace('♀', '-f').replace('/', '-').replace('–', '-').strip()

def get_type_effectiveness(types):
    effectiveness = {t: 1.0 for t in TYPE_CHART.keys()}
    for t_def in types:
        if t_def not in TYPE_CHART: continue
        for t_atk, chart in TYPE_CHART.items():
            if t_def in chart: effectiveness[t_atk] *= chart[t_def]
    return effectiveness

def extract_specific_ability(raw, target_name):
    if not raw: return ""
    if '/' in raw:
        parts = raw.split('/')
        for p in parts:
            if f"({target_name.capitalize()})" in p or f"({target_name.lower()})" in p:
                return re.sub(r'\(.*?\)', '', p).strip()
        return re.sub(r'\(.*?\)', '', parts[0]).strip()
    return raw

def load_data():
    with open(os.path.join(DATA_DIR, "base_data.json"), 'r') as f: base = json.load(f)
    with open(os.path.join(DATA_DIR, "romhack_data.json"), 'r') as f: romhack = json.load(f)
    return base, romhack

def get_move_display(m_name, move_data, move_stat_changes, base_path="../", show_tm=False):
    m_info = move_data.get(m_name)
    if not m_info: return f"| - | {m_name.replace('-', ' ').capitalize()} | - | - | - | - |"
    
    m_rom = move_stat_changes.get(m_name, {})
    def format_stat(stat_name, base_val):
        rom_val = m_rom.get(stat_name)
        if rom_val: return f'<span style="color:green; font-weight:bold;">{rom_val["new"]}</span> <span style="text-decoration:line-through; color:red; font-size:0.9em;">{rom_val["old"]}</span>'
        return str(base_val or '-')

    power = format_stat('power', m_info['power'])
    acc = format_stat('accuracy', m_info['accuracy'])
    type_icon = f'![{m_info["type"]}]({base_path}img/types/{m_info["type"]}.png)'
    cat_icon = f'![{m_info["damage_class"]}]({base_path}img/types/{m_info["damage_class"]}.png){{ style="vertical-align:middle; object-fit:contain;" }}'
    
    display_name = m_info['name'].replace('-', ' ').capitalize()
    
    if show_tm:
        tm_num = m_info.get('tm_num', '-')
        return f"| {tm_num} | {type_icon} | [{display_name}]({base_path}moves/{m_info['name']}.md) | {cat_icon} | {power} | {acc} | {m_info['pp']} |"
    
    return f"| {type_icon} | [{display_name}]({base_path}moves/{m_info['name']}.md) | {cat_icon} | {power} | {acc} | {m_info['pp']} |"

def get_full_evolution_chains(p_base):
    chain = p_base['evolution_chain']['chain']
    paths = []
    def traverse(node, current_path):
        name = node['species']['name']
        method = ""
        if node['evolution_details']:
            d = node['evolution_details'][0]
            m_parts = []
            if d['trigger']['name'] == 'level-up':
                if d['min_level']: m_parts.append(f"Lv. {d['min_level']}")
                if d['min_happiness']: m_parts.append("Happiness")
                if d['held_item']: m_parts.append(f"Hold {d['held_item']['name']}")
                if d['location']: m_parts.append(f"At {d['location']['name']}")
                if d['known_move']: m_parts.append(f"Know {d['known_move']['name']}")
                if d['known_move_type']: m_parts.append(f"Know {d['known_move_type']['name']} move")
                if d['gender']: m_parts.append("Male" if d['gender'] == 2 else "Female")
                if d['relative_physical_stats'] is not None:
                    if d['relative_physical_stats'] == 1: m_parts.append("Atk > Def")
                    elif d['relative_physical_stats'] == -1: m_parts.append("Def > Atk")
                    else: m_parts.append("Atk = Def")
                if not m_parts: m_parts.append("Level Up")
            elif d['trigger']['name'] == 'use-item': m_parts.append(f"Use {d['item']['name']}")
            elif d['trigger']['name'] == 'trade':
                if d['held_item']: m_parts.append(f"Trade hold {d['held_item']['name']}")
                else: m_parts.append("Trade")
            method = ", ".join(m_parts)
        
        new_path = current_path + [{'name': name, 'method': method}]
        if not node['evolves_to']: paths.append(new_path)
        else:
            for next_node in node['evolves_to']: traverse(next_node, new_path)
    traverse(chain, [])
    return paths

def generate_pokemon_page(name, base_data, rom_data, move_data, ability_data, locations):
    p_base = base_data.get(normalize_name(name))
    if not p_base: return
    p_rom = rom_data['pokemon_changes'].get(name.lower(), {})
    p_moves_rom = rom_data['move_changes'].get(name.lower(), [])
    
    md = f"# {name.capitalize()}\n\n"
    md += f'![{name}](../img/pokemon/{p_base["id"]:03}.png)\n\n'
    
    # Types
    types_orig = p_base['types']
    types_new = p_rom.get('types')
    curr_types = types_new if types_new else types_orig
    md += "## Type\n"
    if types_new and types_new != types_orig:
        md += "Original: " + ' '.join([f'![{t}](../img/types/{t}.png)' for t in types_orig]) + "  \n"
        md += "New: " + ' '.join([f'![{t}](../img/types/{t}.png)' for t in types_new]) + "\n\n"
    else:
        md += ' '.join([f'![{t}](../img/types/{t}.png)' for t in types_orig]) + "\n\n"
        
    # Evolution (Markdown Table for vertical alignment)
    md += "## Evolution\n"
    paths = get_full_evolution_chains(p_base)
    # Determine max stages across all paths
    max_stages = max(len(p) for p in paths)
    
    # We'll use a 2n-1 column table (Stage, Arrow, Stage, Arrow...)
    header = "|" + " | ".join(["Stage" if i%2==0 else "" for i in range(2*max_stages-1)]) + " |"
    sep = "|" + " | ".join([":---:" for i in range(2*max_stages-1)]) + " |"
    md += header + "\n" + sep + "\n"
    
    for path in paths:
        row = "|"
        for i in range(max_stages):
            if i < len(path):
                step = path[i]
                p_norm = normalize_name(step['name'])
                p_info = base_data.get(p_norm)
                sprite = f'![{step["name"]}](../img/pokemon/{p_info["id"]:03}.png)' if p_info else ""
                rom_method = ""
                if p_rom.get('evolution'):
                    for rev in p_rom['evolution']:
                        if rev['target'] and normalize_name(rev['target']) == p_norm: rom_method = rev['method']
                
                method_txt = rom_method if rom_method else step['method']
                label_style = ' <span class="rom-label">ROM</span>' if rom_method else ""
                
                # First col is pkmn
                row += f" {sprite}<br>**[{step['name'].capitalize()}]( {p_norm}.md)** |"
                # Next col is arrow/method if not last in path
                if i < max_stages - 1:
                    if i < len(path) - 1:
                        next_method = path[i+1]['method']
                        # Check ROM for next step
                        next_p_norm = normalize_name(path[i+1]['name'])
                        next_p_rom = rom_data['pokemon_changes'].get(path[i+1]['name'].lower(), {})
                        next_rom_method = ""
                        # Wait, we need the ROM method for the NEXT pokemon in the chain relative to THIS pokemon
                        # Actually we already checked it above for 'step'
                        # Let's just use the current step's method for the arrow leading TO it.
                        row += " |" # Arrow column placeholder, we'll fill it in next iteration? No.
                    else:
                        row += " |"
            else:
                row += " | |" # Empty stage and arrow
        
        # Correct row building: 
        # Path: [A, B, C]
        # Cols: A | arrow B | B | arrow C | C
        row_parts = []
        for i in range(max_stages):
            if i < len(path):
                step = path[i]
                p_norm = normalize_name(step['name'])
                p_info = base_data.get(p_norm)
                sprite = f'![{step["name"]}](../img/pokemon/{p_info["id"]:03}.png)' if p_info else ""
                row_parts.append(f"{sprite}<br>**[{step['name'].capitalize()}]( {p_norm}.md)**")
                if i < max_stages - 1:
                    if i + 1 < len(path):
                        # Arrow to next
                        next_step = path[i+1]
                        next_p_norm = normalize_name(next_step['name'])
                        # Check for ROM method FOR NEXT POKEMON
                        rom_method = ""
                        # Evolution changes are stored in the ROM data of the BASE pokemon
                        # But wait, our p_rom is for the CURRENT page pokemon. 
                        # We need the p_rom for the pokemon that IS evolving.
                        current_p_rom = rom_data['pokemon_changes'].get(step['name'].lower(), {})
                        if current_p_rom.get('evolution'):
                            for rev in current_p_rom['evolution']:
                                if rev['target'] and normalize_name(rev['target']) == next_p_norm:
                                    rom_method = rev['method']
                        
                        m_txt = rom_method if rom_method else next_step['method']
                        style = ' <br><span class="rom-label">ROM</span>' if rom_method else ""
                        row_parts.append(f"➡️<br>{m_txt}{style}")
                    else:
                        row_parts.append("")
            else:
                row_parts.append("")
                if i < max_stages - 1: row_parts.append("")
        
        md += "|" + " | ".join(row_parts) + " |\n"
    md += "\n"

    # Abilities
    md += "## Abilities\n"
    ab1_new = extract_specific_ability(p_rom.get('abilities', {}).get('one', ''), name)
    ab2_new = extract_specific_ability(p_rom.get('abilities', {}).get('two', ''), name)
    orig_abs = [a.replace('-', ' ').capitalize() for a in p_base['abilities']]
    def get_ab_info(ab_name):
        norm = normalize_name(ab_name)
        desc = ability_data.get(norm, {}).get('description', '')
        return f"**[{ab_name}](../abilities/{norm}.md)**: {desc}"
    md += "| Slot | Original | New |\n| --- | --- | --- |\n"
    orig1 = orig_abs[0] if len(orig_abs) > 0 else "-"
    new1 = ab1_new if ab1_new else orig1
    md += f"| Ability 1 | {get_ab_info(orig1) if orig1 != '-' else '-'} | {get_ab_info(new1)} |\n"
    orig2 = orig_abs[1] if len(orig_abs) > 1 else "-"
    new2 = ab2_new if ab2_new else (orig2 if orig2 != "-" else "-")
    md += f"| Ability 2 | {get_ab_info(orig2) if orig2 != '-' else '-'} | {get_ab_info(new2) if new2 != '-' else '-'} |\n\n"
    
    # Base Happiness
    md += "## Base Happiness\n"
    hap = p_rom.get('happiness')
    if hap:
        if 'old' in hap: md += f'<span style="color:green; font-weight:bold;">{hap["new"]}</span> <span style="text-decoration:line-through; color:red; font-size:0.9em;">{hap["old"]}</span>\n\n'
        else: md += f'{hap["new"]}\n\n'
    else: md += "70\n\n"

    # Held Items
    md += "## Held Items\n"
    if p_rom.get('items'):
        for item in p_rom['items']:
            item_name = item.split('(')[0].strip()
            item_norm = normalize_name(item_name)
            md += f"- ![{item_name}](../img/items/{item_norm}.png) {item}\n"
    else: md += "None\n"
    md += "\n"

    # Type Defenses
    md += "## Type Defenses\n"
    eff = get_type_effectiveness(curr_types)
    md += "| 0x | 0.5x | 1x | 2x | 4x |\n| --- | --- | --- | --- | --- |\n"
    col0 = [f"![{t}](../img/types/{t}.png)" for t, v in eff.items() if v == 0]
    col05 = [f"![{t}](../img/types/{t}.png)" for t, v in eff.items() if v == 0.5 or v == 0.25]
    col1 = [f"![{t}](../img/types/{t}.png)" for t, v in eff.items() if v == 1]
    col2 = [f"![{t}](../img/types/{t}.png)" for t, v in eff.items() if v == 2]
    col4 = [f"![{t}](../img/types/{t}.png)" for t, v in eff.items() if v == 4]
    for i in range(max(len(col0), len(col05), len(col1), len(col2), len(col4))):
        md += f"| {col0[i] if i < len(col0) else ''} | {col05[i] if i < len(col05) else ''} | {col1[i] if i < len(col1) else ''} | {col2[i] if i < len(col2) else ''} | {col4[i] if i < len(col4) else ''} |\n"
    md += "\n"

    md += "## Base Stats\n| Stat | Value | Bar |\n| --- | --- | --- |\n"
    total_val = 0
    for stat in ['hp', 'attack', 'defense', 'special-attack', 'special-defense', 'speed']:
        orig_val = p_base['stats'].get(stat, 0)
        new_data = p_rom.get('stats', {}).get(stat.replace('-', '_'))
        new_val = new_data['new'] if new_data else orig_val
        total_val += new_val
        display_val = f'<span style="color:green; font-weight:bold;">{new_val}</span> <span style="text-decoration:line-through; color:red; font-size:0.9em;">{orig_val}</span>' if new_data else str(new_val)
        b_color = "#FFDD57"
        if new_val >= 150: b_color = "#23CD5E"
        elif new_val >= 110: b_color = "#A0E515"
        elif new_val >= 70: b_color = "#FFDD57"
        elif new_val >= 40: b_color = "#FF7F0E"
        else: b_color = "#F34444"
        md += f"| {stat.capitalize().replace('-', ' ')} | {display_val} | <div style='background:#eee; width:300px; height:15px; border-radius:10px; overflow:hidden; border:1px solid #ddd;'><div style='height:100%; width:{min(100, (new_val/200)*100)}%; background:{b_color};'></div></div> |\n"
    
    orig_total = sum(p_base['stats'].values())
    total_new_data = p_rom.get('stats', {}).get('total')
    total_new = total_new_data['new'] if total_new_data else total_val
    total_display = f'<span style="color:green; font-weight:bold;">{total_new}</span> <span style="text-decoration:line-through; color:red; font-size:0.9em;">{orig_total}</span>' if total_new_data else f"**{total_new}**"
    md += f"| **Total** | {total_display} | |\n\n"
    
    p_norm = normalize_name(name)
    md += "## Locations\n"
    if p_norm in locations:
        md += "| Route | Method | Rate |\n| --- | --- | --- |\n"
        for loc in locations[p_norm]:
            fname = normalize_name(loc['route'])
            m_lower = loc['method'].lower()
            icon = "grass-normal.png"
            if 'doubles' in m_lower: icon = "grass-doubles.png"
            elif 'special' in m_lower: icon = "grass-special.png"
            elif 'surf special' in m_lower: icon = "surf-special.png"
            elif 'surf' in m_lower: icon = "surf-normal.png"
            elif 'fish special' in m_lower: icon = "fishing-special.png"
            elif 'fish' in m_lower: icon = "fishing-normal.png"
            elif 'cave special' in m_lower: icon = "cave-special.png"
            elif 'cave' in m_lower: icon = "cave-normal.png"
            md += f"| [{loc['route']}](../routes/{fname}.md) | ![{m_lower}](../img/items/{icon}) {loc['method']} | {loc['rate']}% |\n"
    else:
        chain = p_base['evolution_chain']['chain']
        def find_base(node, target):
            for e in node['evolves_to']:
                if e['species']['name'] == target: return node['species']['name']
                res = find_base(e, target)
                if res: return res
            return None
        base_pkmn = find_base(chain, p_base['name'])
        if base_pkmn: md += f"Evolve from [{base_pkmn.capitalize()}](../pokemon/{normalize_name(base_pkmn)}.md)\n"
        else: md += "No known wild location.\n"
    md += "\n"

    md += "## Level Up Moves\n| Level | Type | Move | Cat | Power | Acc | PP |\n| :--- | :--- | :--- | :--- | :--- | :--- | :--- |\n"
    base_lv_moves = [m for m in p_base['moves'] if m['method'] == 'level-up']
    all_moves = []
    if not p_moves_rom:
        for bm in base_lv_moves: all_moves.append({'level': bm['level'], 'name': bm['name'], 'marker': ''})
    else:
        for rm in p_moves_rom: all_moves.append(rm)
        for bm in base_lv_moves:
            is_replaced = any(rm['level'] == bm['level'] and rm['marker'] == '-' for rm in p_moves_rom)
            was_shifted = any(rm['name'] == bm['name'] and rm['marker'] == '=' for rm in p_moves_rom)
            if is_replaced: all_moves.append({'level': bm['level'], 'name': bm['name'], 'marker': 'REMOVED'})
            elif not was_shifted and not any(rm['name'] == bm['name'] for rm in p_moves_rom): all_moves.append({'level': bm['level'], 'name': bm['name'], 'marker': ''})
    all_moves.sort(key=lambda x: x['level'])
    for m in all_moves:
        row = get_move_display(m['name'], move_data, rom_data['move_stat_changes'])
        marker, change_text = m.get('marker', ''), ""
        if marker in ['+', '-']: change_text = ' <span class="pill pill-new">NEW</span>'
        elif marker == 'REMOVED': change_text = ' <span class="pill pill-removed">REMOVED</span>'
        elif marker == '=':
            old_lv = next((x['level'] for x in base_lv_moves if x['name'] == m['name']), "?")
            change_text = f' <span class="pill pill-shifted">SHIFTED (from {old_lv})</span>'
        md += f"| {m['level']}{change_text} {row}\n"
    
    learnable = [m for m in p_base['moves'] if m['method'] != 'level-up']
    rom_machines = p_rom.get('tm_hm', [])
    for rm_line in rom_machines:
        tm_match = re.findall(r'(TM|HM)(\d+)\s*,?\s*([^,.\n]+)', rm_line)
        for pref, num, mname in tm_match:
            m_norm = normalize_name(mname)
            if not any(m['name'] == m_norm for m in learnable): learnable.append({'name': m_norm, 'method': 'machine', 'rom_new': True})

    def gen_move_table(title, moves_list):
        if not moves_list: return ""
        res = f"\n## {title}\n| No. | Type | Move | Cat | Power | Acc | PP |\n| :--- | :--- | :--- | :--- | :--- | :--- | :--- |\n"
        moves_list.sort(key=lambda x: x['name'])
        for m in moves_list:
            row = get_move_display(m['name'], move_data, rom_data['move_stat_changes'], show_tm=True)
            # Add NEW pill to No. column if rom_new
            if m.get('rom_new'):
                row_parts = row.split('|')
                row_parts[1] = row_parts[1] + ' <span class="pill pill-new">NEW</span>'
                row = "|".join(row_parts)
            res += row + "\n"
        return res
    md += gen_move_table("TM Moves", [m for m in learnable if m['method'] == 'machine' and move_data.get(m['name'], {}).get('tm_num', '').startswith('TM')])
    md += gen_move_table("HM Moves", [m for m in learnable if m['method'] == 'machine' and move_data.get(m['name'], {}).get('tm_num', '').startswith('HM')])
    md += gen_move_table("Egg Moves", [m for m in learnable if m['method'] == 'egg'])
    md += gen_move_table("Tutor Moves", [m for m in learnable if m['method'] == 'tutor'])
    return md

def generate_move_page(name, move_info, pokemon_list, m_rom):
    md = f"# {name.replace('-', ' ').capitalize()}\n\n"
    def format_stat(stat_name, base_val):
        rom_val = m_rom.get(stat_name)
        if rom_val: return f'<span style="color:green; font-weight:bold;">{rom_val["new"]}</span> <span style="text-decoration:line-through; color:red; font-size:0.9em;">{rom_val["old"]}</span>'
        return str(base_val or '-')
    md += f"**TM/HM:** {move_info.get('tm_num', '-')}\n\n"
    md += f"**Type:** ![{move_info['type']}](../img/types/{move_info['type']}.png)  \n"
    md += f"**Category:** ![{move_info['damage_class']}](../img/types/{move_info['damage_class']}.png){{ style='object-fit:contain;' }}  \n"
    md += f"**Power:** {format_stat('power', move_info['power'])}  \n"
    md += f"**Accuracy:** {format_stat('accuracy', move_info['accuracy'])}  \n"
    md += f"**PP:** {move_info['pp']}  \n\n"
    md += f"## Description\n{move_info['description']}\n\n"
    md += "## Learned by\n"
    for p in sorted(pokemon_list): md += f"- [{p.capitalize()}](../pokemon/{normalize_name(p)}.md)\n"
    return md

def generate_ability_page(name, ability_info, pokemon_list):
    md = f"# {name.replace('-', ' ').capitalize()}\n\n"
    md += f"## Description\n{ability_info['description']}\n\n"
    md += "## Pokemon with this Ability\n"
    for p in sorted(pokemon_list): md += f"- [{p.capitalize()}](../pokemon/{normalize_name(p)}.md)\n"
    return md

def generate_route_page(name, route_data, base_data, trainer_data):
    md = f"# {name}\n\n"
    if route_data:
        for sec in route_data['sections']:
            md += f"## {sec['title']}\n"
            methods = {}
            for enc in sec['encounters']:
                m = enc['method']
                if m not in methods: methods[m] = []
                methods[m].append(enc)
            for m, encs in methods.items():
                m_lower = m.lower()
                icon = "grass-normal.png"
                if 'doubles' in m_lower: icon = "grass-doubles.png"
                elif 'special' in m_lower: icon = "grass-special.png"
                elif 'surf special' in m_lower: icon = "surf-special.png"
                elif 'surf' in m_lower: icon = "surf-normal.png"
                elif 'fish special' in m_lower: icon = "fishing-special.png"
                elif 'fish' in m_lower: icon = "fishing-normal.png"
                elif 'cave special' in m_lower: icon = "cave-special.png"
                elif 'cave' in m_lower: icon = "cave-normal.png"
                md += f"### ![{m}](../img/items/{icon}){{ style='vertical-align:middle;' }} {m}\n"
                md += "| Sprite | Pokemon | Rate |\n| --- | --- | --- |\n"
                for enc in encs:
                    p_norm = normalize_name(enc['pokemon'])
                    p_info = base_data.get(p_norm)
                    sprite = f'![{enc["pokemon"]}](../img/pokemon/{p_info["id"]:03}.png)' if p_info else ""
                    md += f"| {sprite} | [{enc['pokemon']}](../pokemon/{p_norm}.md) | {enc['rate']}% |\n"
                md += "\n"
        if route_data.get('specials'):
            md += "## Special Encounters\n"
            for s in route_data['specials']:
                md += f"!!! info\n"
                for l in s.split('\n'): md += f"    {l}\n"
                md += "\n"
    location_trainers = trainer_data.get(name)
    if location_trainers:
        md += "\n## Trainers\n"
        for trainer in location_trainers:
            md += f"### {trainer['name']}\n"
            md += "| Sprite | Pokemon | Level | Ability | Item | Moves |\n| --- | --- | --- | --- | --- | --- |\n"
            for p in trainer['pokemon']:
                p_norm = normalize_name(p['name'])
                p_base = base_data.get(p_norm)
                sprite = f'![{p["name"]}](../img/pokemon/{p_base["id"]:03}.png)' if p_base else ""
                md += f"| {sprite} | [{p['name']}](../pokemon/{p_norm}.md) | {p['level']} | {p['ability']} | {p['item']} | {', '.join(p['moves'])} |\n"
            md += "\n"
    return md

if __name__ == "__main__":
    base, romhack = load_data()
    if 'basculin-red-striped' in base['pokemon']: base['pokemon']['basculin'] = base['pokemon']['basculin-red-striped']
    locations = {}
    for r_data in romhack['wild_pokemon']:
        for sec in r_data['sections']:
            for enc in sec['encounters']:
                p_norm = normalize_name(enc['pokemon'])
                if p_norm not in locations: locations[p_norm] = []
                locations[p_norm].append({'route': r_data['name'], 'method': enc['method'], 'rate': enc['rate']})
    all_locations = []
    for loc in romhack['trainer_order']: all_locations.append(loc)
    for r in romhack['wild_pokemon']:
        if r['name'] not in all_locations: all_locations.append(r['name'])
    if not os.path.exists("docs/pokemon"): os.makedirs("docs/pokemon")
    pkmn_list = sorted(base['pokemon'].values(), key=lambda x: x['id'])
    for p in pkmn_list:
        md = generate_pokemon_page(p['name'], base['pokemon'], romhack, base['moves'], base['abilities'], locations)
        with open(os.path.join("docs/pokemon", f"{normalize_name(p['name'])}.md"), 'w') as f: f.write(md)
    with open("docs/pokemon/index.md", 'w') as f:
        f.write("# Pokemon\n\n")
        for p in pkmn_list: f.write(f"- [{p['name'].capitalize()}]({normalize_name(p['name'])}.md)\n")
    if not os.path.exists("docs/moves"): os.makedirs("docs/moves")
    move_to_pokemon = {}
    for p_name, p_data in base['pokemon'].items():
        for m in p_data['moves']:
            if m['name'] not in move_to_pokemon: move_to_pokemon[m['name']] = []
            move_to_pokemon[m['name']].append(p_name)
    for m_name, m_info in sorted(base['moves'].items()):
        md = generate_move_page(m_name, m_info, move_to_pokemon.get(m_name, []), romhack['move_stat_changes'].get(m_name, {}))
        with open(os.path.join("docs/moves", f"{m_name}.md"), 'w') as f: f.write(md)
    with open("docs/moves/index.md", 'w') as f:
        f.write("# Moves\n\n")
        for m_name in sorted(base['moves'].keys()): f.write(f"- [{m_name.replace('-', ' ').capitalize()}]({m_name}.md)\n")
    if not os.path.exists("docs/abilities"): os.makedirs("docs/abilities")
    ability_to_pokemon = {}
    for p_name, p_data in base['pokemon'].items():
        for a in p_data['abilities']:
            if a not in ability_to_pokemon: ability_to_pokemon[a] = []
            ability_to_pokemon[a].append(p_name)
    for a_name, a_info in sorted(base['abilities'].items()):
        md = generate_ability_page(a_name, a_info, ability_to_pokemon.get(a_name, []))
        with open(os.path.join("docs/abilities", f"{a_name}.md"), 'w') as f: f.write(md)
    with open("docs/abilities/index.md", 'w') as f:
        f.write("# Abilities\n\n")
        for a_name in sorted(base['abilities'].keys()): f.write(f"- [{a_name.replace('-', ' ').capitalize()}]({a_name}.md)\n")
    if not os.path.exists("docs/routes"): os.makedirs("docs/routes")
    for r_name in all_locations:
        r_data = next((r for r in romhack['wild_pokemon'] if r['name'] == r_name), None)
        md = generate_route_page(r_name, r_data, base['pokemon'], romhack['trainers'])
        fname = normalize_name(r_name)
        with open(os.path.join("docs/routes", f"{fname}.md"), 'w') as f: f.write(md)
    with open("docs/routes/index.md", 'w') as f:
        f.write("# Routes\n\n")
        for r_name in all_locations: f.write(f"- [{r_name}]({normalize_name(r_name)}.md)\n")
    with open("mkdocs.yml", 'r') as f: lines = f.readlines()
    new_lines = []
    in_nav = False
    for line in lines:
        if line.startswith('nav:'):
            in_nav = True
            new_lines.append('nav:\n  - Home: README.md\n  - Pokemon:\n    - pokemon/index.md\n')
            gens = [("Kanto", 1, 151), ("Johto", 152, 251), ("Hoenn", 252, 386), ("Sinnoh", 387, 493), ("Unova", 494, 649)]
            for g_name, start, end in gens:
                new_lines.append(f'    - {g_name}:\n')
                for p in pkmn_list:
                    if start <= p['id'] <= end: new_lines.append(f"      - {p['name'].capitalize()}: pokemon/{normalize_name(p['name'])}.md\n")
            new_lines.append('  - Routes:\n    - routes/index.md\n')
            for r_name in all_locations: new_lines.append(f"    - {r_name}: routes/{normalize_name(r_name)}.md\n")
            new_lines.append('  - Moves:\n    - moves/index.md\n')
            for m_name in sorted(base['moves'].keys()): new_lines.append(f"    - {m_name.replace('-', ' ').capitalize()}: moves/{m_name}.md\n")
            new_lines.append('  - Abilities:\n    - abilities/index.md\n')
            for a_name in sorted(base['abilities'].keys()): new_lines.append(f"    - {a_name.replace('-', ' ').capitalize()}: abilities/{a_name}.md\n")
        elif not in_nav: new_lines.append(line)
    with open("mkdocs.yml", 'w') as f: f.writelines(new_lines)
    print("All pages generated and mkdocs.yml updated.")
