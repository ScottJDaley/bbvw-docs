import json
import os
import re
import shutil

DATA_DIR = "scripts/data"
OUTPUT_BASE = "docs"

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

CLEAN_ABILITIES = {
    'unburuden': 'unburden', 'compoundeyes': 'compound-eyes', 'lightningrod': 'lightning-rod', 'poisonpoint': 'poison-point',
    'effectspore': 'effect-spore', 'clearbody': 'clear-body', 'magmaarmor': 'magma-armor', 'naturalcure': 'natural-cure',
    'whitesmoke': 'white-smoke', 'innerfocus': 'inner-focus', 'thickfat': 'thick-fat', 'earlybird': 'early-bird',
    'flamebody': 'flame-body', 'stickyhold': 'sticky-hold', 'roughskin': 'rough-skin', 'waterveil': 'water-veil',
    'arenatrap': 'arena-trap', 'hugepower': 'huge-power', 'purepower': 'pure-power', 'shellarmor': 'shell-armor',
    'airlock': 'air-lock', 'keeneye': 'keen-eye', 'hypercutter': 'hyper-cutter', 'sandveil': 'sand-veil',
    'static': 'static', 'voltabsorb': 'volt-absorb', 'waterabsorb': 'water-absorb', 'oblivious': 'oblivious',
    'cloudnine': 'cloud-nine', 'insomnia': 'insomnia', 'colorchange': 'color-change', 'colour-change': 'color-change',
    'shielddust': 'shield-dust', 'owntempo': 'own-tempo', 'shedskin': 'shed-skin', 'battlearmor': 'battle-armor',
    'sturdy': 'sturdy', 'damp': 'damp', 'limber': 'limber', 'sandstream': 'sand-stream', 'pressure': 'pressure',
    'serenegrace': 'serene-grace', 'swiftswim': 'swift-swim', 'chlorophyll': 'chlorophyll', 'illuminate': 'illuminate',
    'trace': 'trace', 'levitate': 'levitate', 'magnetpull': 'magnet-pull', 'soundproof': 'soundproof',
    'rain-dish': 'rain-dish', 'sandforce': 'sand-force', 'sandrush': 'sand-rush', 'multiscale': 'multiscale',
    'teravolt': 'teravolt', 'turboblaze': 'turboblaze', 'tera-volt': 'teravolt', 'turbo-blaze': 'turboblaze'
}

FIX_MOVES = {
    'extremespeed': 'extreme-speed', 'grasswhistle': 'grass-whistle', 'softboiled': 'soft-boiled', 'faint-attack': 'feint-attack',
    'thundershock': 'thunder-shock', 'ice-burn': 'ice-burn', 'freeze-shock': 'freeze-shock', 'twinneedle': 'twineedle',
    'v-create': 'v-create', 'wood-horn': 'horn-leech', 'hi-jump-kick': 'high-jump-kick', 'selfdestruct': 'self-destruct',
    'featherdance': 'feather-dance', 'reflect,-light-screen': 'reflect', 'nothing': '', 'baculin': 'basculin'
}

WRITTEN_FILES = set()

def write_if_changed(file_path, content):
    WRITTEN_FILES.add(os.path.abspath(file_path))
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            if f.read() == content: return
    
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)

def normalize_name(name):
    if not name: return ""
    name = re.sub(r'([a-z])([A-Z])', r'\1-\2', name)
    name = name.lower().strip()
    if 'nidoran' in name: return 'nidoran-m' if 'm' in name or '♂' in name else 'nidoran-f'
    if 'mime jr' in name: return 'mime-jr'
    if 'mr mime' in name: return 'mr-mime'
    bases = ['basculin', 'frillish', 'jellicent', 'keldeo', 'meloetta', 'darmanitan', 'tornadus', 'thundurus', 'landorus', 'giratina', 'shaymin', 'deoxys', 'wormadam', 'rotom', 'castform', 'deerling', 'sawsbuck', 'meloetta', 'genesect', 'landorus', 'thundurus', 'tornadus']
    for b in bases:
        if name.startswith(b): return b
    res = name.replace(' ', '-').replace('.', '').replace("'", "").replace('’', '').replace('♂', '-m').replace('♀', '-f').replace('/', '-').replace('–', '-').replace('--', '-').strip('-')
    return FIX_MOVES.get(res, res)

def normalize_item_name(name):
    if not name: return ""
    name = name.lower().strip()
    tm_match = re.match(r'(tm|hm)(\d+)\s*(.*)', name)
    if tm_match:
        return f"{tm_match.group(1)}{int(tm_match.group(2)):02}"
    name = re.sub(r'\s*\*\s*\d+', '', name)
    name = name.replace('(npc)', '').strip()
    name = name.replace('poké', 'poke')
    name = name.replace(' ', '-').replace("'", "").replace('.', '').replace('/', '-')
    while '--' in name: name = name.replace('--', '-')
    return name.strip('-')

def get_display_name(name):
    if name.lower().startswith('mime-jr'): return "Mime Jr."
    if name.lower().startswith('mr-mime'): return "Mr. Mime"
    if name.lower().startswith('ho-oh'): return "Ho-Oh"
    if name.lower().startswith('porygon-z'): return "Porygon-Z"
    if name.lower().startswith('porygon2'): return "Porygon2"
    if name.lower().startswith('nidoran-m'): return "Nidoran♂"
    if name.lower().startswith('nidoran-f'): return "Nidoran♀"
    res = name.split('-')[0].capitalize()
    if name.lower().startswith('deoxys'): return "Deoxys"
    if name.lower().startswith('wormadam'): return "Wormadam"
    if name.lower().startswith('giratina'): return "Giratina"
    if name.lower().startswith('shaymin'): return "Shaymin"
    if name.lower().startswith('basculin'): return "Basculin"
    if name.lower().startswith('rotom'): return "Rotom"
    if name.lower().startswith('castform'): return "Castform"
    if name.lower().startswith('frillish'): return "Frillish"
    if name.lower().startswith('jellicent'): return "Jellicent"
    return res

def extract_specific_ability(raw, target_name):
    if not raw: return ""
    if '/' in raw:
        for p in raw.split('/'):
            if f"({target_name.capitalize()})" in p or f"({target_name.lower()})" in p: return re.sub(r'\(.*?\)', '', p).strip()
        return re.sub(r'\(.*?\)', '', raw.split('/')[0]).strip()
    return raw

def load_data():
    with open(os.path.join(DATA_DIR, "base_data.json"), 'r', encoding='utf-8') as f: base = json.load(f)
    with open(os.path.join(DATA_DIR, "romhack_data.json"), 'r', encoding='utf-8') as f: rom = json.load(f)
    
    if os.path.exists(os.path.join(DATA_DIR, "base_item_locations.json")):
        with open(os.path.join(DATA_DIR, "base_item_locations.json"), "r", encoding="utf-8") as f:
            serebii = json.load(f)
            for iname, idata in serebii["items"].items():
                inorm = normalize_item_name(iname)
                if inorm not in base["items"]:
                    base["items"][inorm] = {
                        "name": iname,
                        "description": idata["description"],
                        "category": "Misc"
                    }
            base["location_items_serebii"] = serebii["route_items"]
    return base, rom

def get_item_icon(name, move_data, base_path="../"):
    norm = normalize_item_name(name)
    if norm.startswith('tm') or norm.startswith('hm'):
        m_match = re.search(r'(?:TM|HM)\d+\s+(.*)', name, re.IGNORECASE)
        if m_match:
            m_name = normalize_name(m_match.group(1))
            m_info = move_data.get(m_name)
            if m_info: return f"{base_path}img/items/tm-{m_info['type']}.png"
        return f"{base_path}img/items/tm-normal.png"
    icon_path = f"img/items/{norm}.png"
    if os.path.exists(os.path.join(OUTPUT_BASE, icon_path)): return f"{base_path}{icon_path}"
    return f"{base_path}img/items/unknown.png"

def get_item_display_linked(name, base_data, base_path="../"):
    if not name or name == "-": return "-"
    norm = normalize_item_name(name)
    icon = get_item_icon(name, base_data['moves'], base_path)
    if norm in base_data.get('items', {}): return f"![{name}]({icon}) [{name}]({base_path}items/{norm}.md)"
    return f"![{name}]({icon}) {name}"

def get_move_display(m_name, move_data, move_stat_changes, base_path="../", show_tm=False):
    def get_single_link(mn):
        mn_norm = normalize_name(mn); info = move_data.get(mn_norm)
        if not info: return f"[{mn}]({base_path}moves/{mn_norm}.md)" if mn_norm else mn
        return f"[{mn.replace('-', ' ').capitalize()}]({base_path}moves/{mn_norm}.md)"
    m_list = [m.strip() for m in m_name.split('/')] if '/' in m_name else ([m.strip() for m in m_name.split(',')] if ',' in m_name and 'TM' not in m_name else [m_name])
    links = [get_single_link(m) for m in m_list if normalize_name(m)]
    link_str = ", ".join(links)
    m_norm = normalize_name(m_list[0]); m_info = move_data.get(m_norm)
    if not m_info: return f"| {link_str} | - | - | - | - | - |"
    m_rom = move_stat_changes.get(m_norm, {})
    def format_stat(stat, val):
        if stat in m_rom: return f'<span style="color:green; font-weight:bold;">{m_rom[stat]["new"]}</span> <span style="text-decoration:line-through; color:red; font-size:0.9em;">{m_rom[stat]["old"]}</span>'
        return str(val or '-')
    p, a = format_stat('power', m_info['power']), format_stat('accuracy', m_info['accuracy'])
    pp = format_stat('pp', m_info['pp'])
    t_val = m_info["type"]; t_icon = f'![{t_val}]({base_path}img/types/{t_val}.png)'
    if 'type' in m_rom: t_icon = f'![{m_rom["type"]["new"]}]({base_path}img/types/{m_rom["type"]["new"]}.png) <span style="text-decoration:line-through; color:red; font-size:0.9em;">{m_info["type"]}</span>'
    c_icon = f'![{m_info["damage_class"]}]({base_path}img/types/{m_info["damage_class"]}.png){{ style="vertical-align:middle; object-fit:contain;" }}'
    if show_tm: return f"| {m_info.get('tm_num', '-')} | {link_str} | {t_icon} | {c_icon} | {p} | {a} | {pp} |"
    return f"| {link_str} | {t_icon} | {c_icon} | {p} | {a} | {pp} |"

def get_full_evolution_chains(p_base, all_pokemon_base):
    chain = p_base['evolution_chain']['chain']
    paths = []
    def traverse(node, current_path):
        name = node['species']['name']
        p_id = 999; p_info = all_pokemon_base.get(normalize_name(name))
        if p_info: p_id = p_info['id']
        else:
            for pk in all_pokemon_base.values():
                if pk['name'] == name: p_id = pk['id']; break
        if p_id > 649:
            if current_path: paths.append(current_path)
            return
        method = ""
        if node['evolution_details']:
            d = node['evolution_details'][0]; m_parts = []
            if d['trigger']['name'] == 'level-up':
                if d['min_level']: m_parts.append(f"Lv. {d['min_level']}")
                if d['min_happiness']: m_parts.append("Happiness")
                if d['held_item']: m_parts.append(f"Hold {d['held_item']['name']}")
                if d['location']: m_parts.append(f"At {d['location']['name']}")
                if d['known_move']: m_parts.append(f"Know {d['known_move']['name']}")
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
            found_valid_child = False
            for next_node in node['evolves_to']:
                c_name = next_node['species']['name']; c_id = 999; c_info = all_pokemon_base.get(normalize_name(c_name))
                if c_info: c_id = c_info['id']
                if c_id <= 649: traverse(next_node, new_path); found_valid_child = True
            if not found_valid_child: paths.append(new_path)
    traverse(chain, [])
    return [p for p in paths if p]

def generate_pokemon_page(name, base_data, rom_data, move_data, ability_data, locations, pokemon_all_base):
    p_n_k = normalize_name(name); p_base = pokemon_all_base.get(p_n_k)
    if not p_base: return None
    p_rom = rom_data['pokemon_changes'].get(name.lower(), {})
    if not p_rom: p_rom = rom_data['pokemon_changes'].get(p_n_k, {})
    p_moves_rom = rom_data['move_changes'].get(name.lower(), [])
    if not p_moves_rom: p_moves_rom = rom_data['move_changes'].get(p_n_k, [])
    display_name = get_display_name(name)
    md = f"# {display_name}\n\n![{p_n_k}](../img/pokemon/{p_base['id']:03}.png)\n\n"
    c_t = p_rom.get('types') or p_base['types']
    md += "## Type\n" + (f"Original: {' '.join([f'![{t}](../img/types/{t}.png)' for t in p_base['types']])}  \nNew: {' '.join([f'![{t}](../img/types/{t}.png)' for t in p_rom['types']])}\n\n" if p_rom.get('types') and p_rom['types'] != p_base['types'] else ' '.join([f'![{t}](../img/types/{t}.png)' for t in p_base['types']]) + "\n\n")
    md += "## Evolution\n"
    ps = get_full_evolution_chains(p_base, pokemon_all_base)
    if ps:
        mx = max(len(p) for p in ps); md += "|" + " | ".join(["Stage" if i%2==0 else "" for i in range(2*mx-1)]) + " |\n|" + " | ".join([":---:" for _ in range(2*mx-1)]) + " |\n"
        for p in ps:
            rp = []
            for i in range(mx):
                if i < len(p):
                    st = p[i]; s_n = normalize_name(st['name']); info = pokemon_all_base.get(s_n)
                    if info: rp.append(f"![{s_n}](../img/pokemon/{info['id']:03}.png)<br>**[{get_display_name(st['name'])}]( {s_n}.md)**")
                    else: rp.append(f"**[{get_display_name(st['name'])}]( {s_n}.md)**")
                    if i < mx - 1:
                        if i + 1 < len(p):
                            nxt = p[i+1]; nxt_n = normalize_name(nxt['name']); rm_m = ""
                            curr_rom = rom_data['pokemon_changes'].get(st['name'].lower(), {})
                            if curr_rom.get('evolution'):
                                for rv in curr_rom['evolution']:
                                    if rv['target'] and normalize_name(rv['target']) == nxt_n: rm_m = rv['method']
                            rp.append(f"➡️<br>{rm_m if rm_m else nxt['method']}")
                        else: rp.append("")
                else: rp.append(""); (rp.append("") if i < mx - 1 else None)
            md += "|" + " | ".join(rp) + " |\n"
    else: md += "No evolution.\n"
    md += "\n## Abilities\n"
    a1_n = extract_specific_ability(p_rom.get('abilities', {}).get('one', ''), name); a2_n = extract_specific_ability(p_rom.get('abilities', {}).get('two', ''), name)
    orig_abs = [a.replace('-', ' ').capitalize() for a in p_base['abilities']]
    def get_ab_info(a_n):
        n = normalize_name(a_n); n = CLEAN_ABILITIES.get(n, n); d = ability_data.get(n, {}).get('description', '')
        return f"**[{a_n}](../abilities/{n}.md)**: {d}" if n else a_n
    md += f"| Slot | Original | New |\n| --- | --- | --- |\n| Ability 1 | {get_ab_info(orig_abs[0]) if len(orig_abs) > 0 else '-'} | {get_ab_info(a1_n if a1_n else (orig_abs[0] if len(orig_abs) > 0 else '-'))} |\n| Ability 2 | {get_ab_info(orig_abs[1]) if len(orig_abs) > 1 else '-'} | {get_ab_info(a2_n if a2_n else (orig_abs[1] if len(orig_abs) > 1 else '-'))} |\n\n"
    md += "## Base Happiness\n"
    hap = p_rom.get('happiness')
    if hap: md += f'<span style="color:green; font-weight:bold;">{hap["new"]}</span> <span style="text-decoration:line-through; color:red; font-size:0.9em;">{hap.get("old", 70)}</span>\n\n'
    else: md += "70\n\n"
    md += "## Held Items\n"
    if p_rom.get('items'):
        for item in p_rom['items']: md += f"- {get_item_display_linked(item, base_data)}\n"
    else: md += "None\n"
    md += "\n## Type Defenses\n"
    eff = {t: 1.0 for t in TYPE_CHART.keys()}
    for t_d in c_t:
        if t_d in TYPE_CHART:
            for t_a, ch in TYPE_CHART.items():
                if t_d in ch: eff[t_a] *= ch[t_d]
    md += "| 0x | 0.5x | 1x | 2x | 4x |\n| --- | --- | --- | --- | --- |\n"
    c0, c05, c1, c2, c4 = [[f"![{t}](../img/types/{t}.png)" for t, v in eff.items() if v == val] for val in [0, 0.5, 1, 2, 4]]
    for i in range(max(len(c0), len(c05), len(c1), len(c2), len(c4))):
        md += f"| {c0[i] if i < len(c0) else ''} | {c05[i] if i < len(c05) else ''} | {c1[i] if i < len(c1) else ''} | {c2[i] if i < len(c2) else ''} | {c4[i] if i < len(c4) else ''} |\n"
    md += "\n## Base Stats\n| Stat | Value | Bar |\n| --- | --- | --- |\n"
    tv = 0
    for s in ['hp', 'attack', 'defense', 'special-attack', 'special-defense', 'speed']:
        ov = p_base['stats'].get(s, 0); nd = p_rom.get('stats', {}).get(s.replace('-', '_')); nv = nd['new'] if nd else ov; tv += nv
        dv = f'<span style="color:green; font-weight:bold;">{nv}</span> <span style="text-decoration:line-through; color:red; font-size:0.9em;">{ov}</span>' if nd else str(nv)
        cl = "#23CD5E" if nv >= 150 else ("#A0E515" if nv >= 110 else ("#FFDD57" if nv >= 70 else ("#FF7F0E" if nv >= 40 else "#F34444")))
        md += f"| {s.capitalize().replace('-', ' ')} | {dv} | <div style='background:#eee; width:300px; height:15px; border-radius:10px; overflow:hidden; border:1px solid #ddd;'><div style='height:100%; width:{min(100, (nv/200)*100)}%; background:{cl};'></div></div> |\n"
    md += f"| **Total** | **{tv}** | |\n\n"
    md += "## Locations\n"
    if p_n_k in locations:
        md += "| Route | Method | Rate |\n| --- | --- | --- |\n"
        for loc in locations[p_n_k]:
            fname = normalize_name(loc['route']); m_lower = loc['method'].lower().replace(',', ''); icon = "grass-normal.png"
            if 'surf special' in m_lower: icon = "surf-special.png"
            elif 'fish special' in m_lower: icon = "fishing-special.png"
            elif 'cave special' in m_lower: icon = "cave-special.png"
            elif 'special' in m_lower: icon = "grass-special.png"
            elif 'doubles' in m_lower: icon = "grass-doubles.png"
            elif 'surf' in m_lower: icon = "surf-normal.png"
            elif 'fish' in m_lower: icon = "fishing-normal.png"
            elif 'cave' in m_lower: icon = "cave-normal.png"
            elif 'sand' in m_lower: icon = "sand-normal.png"
            
            rate_str = loc['rate']
            if '%' not in rate_str and rate_str != 'Fixed': rate_str += "%"
            
            method_display = f"![{m_lower}](../img/items/{icon}) {loc['method']}"
            if loc['method'] == "Fixed": method_display = "Fixed"
            md += f"| [{loc['route']}](../routes/{fname}.md) | {method_display} | {rate_str} |\n"
    else: md += "No known wild location.\n"
    md += "\n## Level Up Moves\n| Level | Move | Type | Cat | Power | Acc | PP |\n| :--- | :--- | :--- | :--- | :--- | :--- | :--- |\n"
    blm = [m for m in p_base['moves'] if m['method'] == 'level-up']; am = []
    explicit_removed = set(); level_shifts = []
    for rm in p_moves_rom:
        if rm.get('marker') == 'REMOVED': explicit_removed.add(normalize_name(rm['name']))
        elif rm.get('marker') == 'SHIFT_REMAINING': level_shifts = rm.get('level_shifts', [])
        else: am.append(rm)
    base_idx_for_shift = 0
    for bm in blm:
        bn = normalize_name(bm['name'])
        if bn in explicit_removed: am.append({'level': bm['level'], 'name': bm['name'], 'marker': 'REMOVED'}); continue
        if any(normalize_name(rm['name']) == bn for rm in p_moves_rom if rm.get('marker') != 'REMOVED' and rm.get('marker') != 'SHIFT_REMAINING'): continue
        if level_shifts and base_idx_for_shift < len(level_shifts) and bm['level'] >= 60:
            new_lv = level_shifts[base_idx_for_shift]; am.append({'level': new_lv, 'name': bm['name'], 'marker': '='}); base_idx_for_shift += 1; continue
        am.append({'level': bm['level'], 'name': bm['name'], 'marker': ''})
    am.sort(key=lambda x: (x.get('level', 0), x['name']))
    for m in am:
        mn = m['name']; mnn = normalize_name(mn)
        if not mnn: continue
        rw = get_move_display(mn, move_data, rom_data['move_stat_changes'])
        mk = m.get('marker', ''); ct = (' <span class="pill pill-new">NEW</span>' if mk in ['+', '-'] else (' <span class="pill pill-removed">REMOVED</span>' if mk == 'REMOVED' else (' <span class="pill pill-shifted">SHIFTED</span>' if mk == '=' else "")))
        md += f"| {m['level']} {ct} {rw}\n"
    learnable = [m for m in p_base['moves'] if m['method'] != 'level-up']
    for rl in p_rom.get('tm_hm', []):
        for pref, num, mn in re.findall(r'(TM|HM)(\d+)\s*,?\s*([^,.\n]+)', rl):
            if not any(normalize_name(m['name']) == normalize_name(mn) for m in learnable): learnable.append({'name': mn, 'method': 'machine', 'rom_new': True})
    def gmt(title, ml):
        if not ml: return ""
        res = f"\n## {title}\n| No. | Move | Type | Cat | Power | Acc | PP |\n| :--- | :--- | :--- | :--- | :--- | :--- | :--- |\n"
        ml.sort(key=lambda x: x['name'])
        for m in ml:
            mn = m['name']; mnn = normalize_name(mn)
            if not mnn: continue
            rw = get_move_display(mn, move_data, rom_data['move_stat_changes'], show_tm=True)
            if m.get('rom_new'): rp = rw.split('|'); rp[1] = rp[1] + ' <span class="pill pill-new">NEW</span>'; rw = "|".join(rp)
            res += rw + "\n"
        return res
    md += gmt("TM Moves", [m for m in learnable if m['method'] == 'machine' and move_data.get(normalize_name(m['name']), {}).get('tm_num', '').startswith('TM')])
    md += gmt("HM Moves", [m for m in learnable if m['method'] == 'machine' and move_data.get(normalize_name(m['name']), {}).get('tm_num', '').startswith('HM')])
    md += gmt("Egg Moves", [m for m in learnable if m['method'] == 'egg']) + gmt("Tutor Moves", [m for m in learnable if m['method'] == 'tutor'])
    return md

def generate_move_page(name, info, pkmn_list, m_rom, base_data):
    md = f"# {name.replace('-', ' ').capitalize()}\n\n"
    def format_stat(stat, val):
        if stat in m_rom: return f'<span style="color:green; font-weight:bold;">{m_rom[stat]["new"]}</span> <span style="text-decoration:line-through; color:red; font-size:0.9em;">{m_rom[stat]["old"]}</span>'
        return str(val or '-')
    t_icon = f'![{info["type"]}](../img/types/{info["type"]}.png)'
    if 'type' in m_rom: t_icon = f'![{m_rom["type"]["new"]}](../img/types/{m_rom["type"]["new"]}.png) <span style="text-decoration:line-through; color:red; font-size:0.9em;">{info["type"]}</span>'
    md += f"**TM/HM:** {info.get('tm_num', '-')}\n\n**Type:** {t_icon}  \n**Category:** ![{info['damage_class']}](../img/types/{info['damage_class']}.png){{ style='object-fit:contain;' }}  \n**Power:** {format_stat('power', info['power'])}  \n**Accuracy:** {format_stat('accuracy', info['accuracy'])}  \n**PP:** {format_stat('pp', info['pp'])}  \n\n## Description\n{info['description']}\n\n## Learned by\n| Sprite | Pokemon |\n| --- | --- |\n"
    for p in sorted(pkmn_list):
        pn = normalize_name(p); info_p = base_data['pokemon'].get(pn)
        if info_p: md += f"| ![{pn}](../img/pokemon/{info_p['id']:03}.png) | [{get_display_name(p)}](../pokemon/{pn}.md) |\n"
    return md

def generate_ability_page(name, info, pkmn_list, base_data):
    md = f"# {name.replace('-', ' ').capitalize()}\n\n## Description\n{info['description']}\n\n## Pokemon with this Ability\n| Sprite | Pokemon |\n| --- | --- |\n"
    for p in sorted(pkmn_list):
        pn = normalize_name(p); info_p = base_data['pokemon'].get(pn)
        if info_p: md += f"| ![{pn}](../img/pokemon/{info_p['id']:03}.png) | [{get_display_name(p)}](../pokemon/{pn}.md) |\n"
    return md

def get_item_display_name(norm_name, base_data):
    # Try to get the name from base_data if available
    item_info = base_data.get('items', {}).get(norm_name)
    if item_info and item_info.get('name'):
        name = item_info['name']
        # If it's a TM/HM, ensure it's upper case
        if re.match(r'^[th]m\d+', name, re.IGNORECASE):
            return name.upper()
        # If it's all lowercase, title case it (handles kebab-case and single words)
        if name.islower():
            return name.replace('-', ' ').title()
        return name
    
    # Fallback to formatting the normalized name
    if re.match(r'^(tm|hm)(\d+)', norm_name):
        return norm_name.upper()
    return norm_name.replace('-', ' ').title()

def generate_item_page(norm_name, info, route_locations, pkmn_with_item, move_data, base_data):
    display_name = get_item_display_name(norm_name, base_data)
    icon = get_item_icon(display_name, move_data)
    md = f"# ![icon]({icon}) {display_name}\n\n**Category:** {info.get('category', 'Misc').capitalize()}\n\n## Description\n{info.get('description', 'No description available.')}\n\n"
    if route_locations:
        md += "## Locations\n| Route | Type | Info |\n| --- | --- | --- |\n"
        for loc, l_type, detail in sorted(route_locations):
            md += f"| [{loc}](../routes/{normalize_name(loc)}.md) | {l_type} | {detail} |\n"
        md += "\n"
    if pkmn_with_item:
        md += "## Held by Wild Pokemon\n| Sprite | Pokemon |\n| --- | --- |\n"
        for p in sorted(pkmn_with_item):
            pn = normalize_name(p); p_info = base_data['pokemon'].get(pn)
            if p_info: md += f"| ![{pn}](../img/pokemon/{p_info['id']:03}.png) | [{get_display_name(p)}](../pokemon/{pn}.md) |\n"
    return md

def generate_route_page(name, r_d, base_data, t_d, rom_item_changes):
    md = f"# {name}\n\n"
    if r_d:
        md += "## Encounters\n"
        # Track processed sections to avoid duplicates
        processed_sections = set()
        for sc in r_d['sections']:
            sec_id = f"{sc['title']}-{json.dumps(sc['encounters'])}"
            if sec_id in processed_sections: continue
            processed_sections.add(sec_id)

            md += f"### {sc['title']}\n"
            ms = {}
            for ec in sc['encounters']: ms[ec['method']] = ms.get(ec['method'], []) + [ec]
            for m, ecs in ms.items():
                ml = m.lower().replace(',', ''); icon = "grass-normal.png"
                if 'surf special' in ml: icon = "surf-special.png"
                elif 'fish special' in ml: icon = "fishing-special.png"
                elif 'cave' in ml: icon = "cave-normal.png"
                elif 'surf' in ml: icon = "surf-normal.png"
                elif 'fish' in ml: icon = "fishing-normal.png"
                elif 'sand' in ml: icon = "sand-normal.png"
                md += f"#### ![{m}](../img/items/{icon}) {m}\n| Sprite | Pokemon | Rate |\n| --- | --- | --- |\n"
                for ec in ecs:
                    pn = normalize_name(ec['pokemon']); info = base_data['pokemon'].get(pn)
                    md += f"| ![{pn}](../img/pokemon/{info['id']:03}.png) | [{ec['pokemon']}](../pokemon/{pn}.md) | {ec['rate']}% |\n" if info else f"| | {ec['pokemon']} | {ec['rate']}% |\n"
                md += "\n"
        if r_d.get('specials'):
            md += "## Special Encounters\n"
            for spec in r_d['specials']:
                p_norm = normalize_name(spec['pokemon']); p_info = base_data['pokemon'].get(p_norm)
                p_sprite = f"![{spec['pokemon']}](../img/pokemon/{p_info['id']:03}.png)" if p_info else ""
                p_link = f"[{spec['pokemon']}](../pokemon/{p_norm}.md)" if p_norm else spec['pokemon']

                m_icon = "grass-normal.png"; m_lower = spec['method'].lower()
                if 'surf' in m_lower: m_icon = "surf-special.png"
                elif 'fish' in m_lower: m_icon = "fishing-special.png"
                elif 'cave' in m_lower: m_icon = "cave-normal.png"
                elif 'sand' in m_lower: m_icon = "sand-normal.png"

                method_cell = f"![{spec['method']}](../img/items/{m_icon}) {spec['method']}"
                if spec['method'] == "Fixed": method_cell = "Fixed"

                md += f"### {p_link}\n"
                md += f"| Sprite | Level | Location | Method | Rate |\n| --- | --- | --- | --- | --- |\n"
                md += f"| {p_sprite} | {spec['level']} | {spec['location']} | {method_cell} | {spec['rate']} |\n\n"
                if spec['description']:
                    md += f"*{spec['description']}*\n\n"

    # Load base item locations
    base_item_locs = {}
    if os.path.exists("scripts/data/base_item_locations.json"):
        with open("scripts/data/base_item_locations.json", "r", encoding="utf-8") as f:
            base_item_locs = json.load(f).get("route_items", {})

    md += "## Items\n"
    route_base_items = base_item_locs.get(name, {})
    rom_loc_items = rom_item_changes.get(name, {})
    all_subareas = sorted(set(list(route_base_items.keys()) + list(rom_loc_items.keys())))

    for sub in all_subareas:
        md += f"### {sub}\n| Item |\n| --- |\n"
        sub_rom = rom_loc_items.get(sub, [])
        sub_base = route_base_items.get(sub, [])

        processed_base = set()
        # 1. Show ROM changes (replacements) inline
        for change in sub_rom:
            old_name = change['old']
            old_norm = normalize_item_name(old_name)
            item_link = get_item_display_linked(change['new'], base_data)
            md += f"| {item_link} <span style='text-decoration:line-through; color:red; font-size:0.9em;'>{old_name}</span> |\n"
            # Mark this base item as processed if it matches
            for b in sub_base:
                if normalize_item_name(b['name']) == old_norm: processed_base.add(b['name'])

        # 2. Show remaining base items
        for b in sub_base:
            if b['name'] not in processed_base:
                detail_text = f" ({b['detail']})" if b.get('detail') else ""
                md += f"| {get_item_display_linked(b['name'], base_data)}{detail_text} |\n"
        md += "\n"

    lt = t_d.get(name)

    if lt:
        md += "## Trainers\n"
        gs = {}
        for t in lt: h = t.get('group_header', ''); gs[h] = gs.get(h, []) + [t]
        for h, teams in gs.items():
            if h:
                md += f"### {h}\n"
                if teams[0].get('battle_type'): md += f"**Battle Type:** {teams[0]['battle_type']}  \n"
                if teams[0].get('reward'):
                    rw = teams[0]['reward']; tm_m = re.search(r'(TM|HM)(\d+)', rw)
                    if tm_m:
                        mn = next((mid for mid, mi in base_data['moves'].items() if mi.get('tm_num') == tm_m.group(0)), "")
                        if mn: rw = rw.replace(tm_m.group(0), f"[{tm_m.group(0)}](../moves/{mn}.md)")
                    md += f"**Reward:** {rw}  \n"
                md += "\n"
            for team in teams:
                md += f"{'####' if h else '###'} {team['name']}\n| Sprite | Pokemon | Level | Ability | Item | Moves |\n| --- | --- | --- | --- | --- | --- |\n"
                for p in team['pokemon']:
                    pn = normalize_name(p['name']); p_base = base_data['pokemon'].get(pn)
                    sprite = f'![{p["name"]}](../img/pokemon/{p_base["id"]:03}.png)' if p_base else ""
                    md += f"| {sprite} | [{get_display_name(p['name'])}](../pokemon/{pn}.md) | {p['level']} | {p['ability']} | {get_item_display_linked(p['item'], base_data) if p['item'] != '-' else '-'} | {', '.join(p['moves'])} |\n"
                md += "\n"
    return md

if __name__ == "__main__":
    for d in ['docs/pokemon', 'docs/moves', 'docs/abilities', 'docs/routes', 'docs/items']:
        if os.path.exists(d): shutil.rmtree(d)
        os.makedirs(d)
    base_data, rom = load_data(); base_data['pokemon']['basculin'] = base_data['pokemon'].get('basculin-red-striped', base_data['pokemon'].get('basculin'))
    priority_forms = ['-normal', '-male', '-plant', '-red-striped', '-land', '-altered', '-standard', '-ordinary', '-aria', '-incarnate', '-spring']
    normalized_pkmn = {}
    for p in sorted(base_data['pokemon'].values(), key=lambda x: x['id']):
        if p['id'] > 649: continue
        nn = normalize_name(p['name'])
        if nn not in normalized_pkmn: normalized_pkmn[nn] = p
        else:
            current_p = normalized_pkmn[nn]
            for pf in priority_forms:
                if p['name'].endswith(pf): normalized_pkmn[nn] = p; break
                if current_p['name'].endswith(pf): break
    base_data['pokemon'] = normalized_pkmn
    pkmn_to_generate = sorted(base_data['pokemon'].values(), key=lambda x: x['id'])
    fab, fmv = {}, {}
    for p in pkmn_to_generate:
        pn = p['name']; pr = rom['pokemon_changes'].get(pn, {}); pa = [extract_specific_ability(a, pn) for a in [pr.get('abilities', {}).get('one'), pr.get('abilities', {}).get('two')] if a]
        if not any(pa): pa = p['abilities']
        for ab in pa:
            an = CLEAN_ABILITIES.get(normalize_name(ab), normalize_name(ab))
            if an: (fab[an].append(pn) if an in fab else fab.update({an: [pn]}))
        learnable = set([m['name'] for m in p['moves']] + [rm['name'] for rm in rom['move_changes'].get(pn, []) if rm.get('name')])
        for rl in pr.get('tm_hm', []):
            for m in re.findall(r'(TM|HM)\d+\s*,?\s*([^,.\n]+)', rl): learnable.add(m[1])
        for tl in pr.get('tutor', []):
            for m in re.findall(r'([^,.\n]+)', tl): learnable.add(m)
        for m in learnable:
            mn = normalize_name(m)
            if mn: (fmv[mn].append(pn) if mn in fmv else fmv.update({mn: [pn]}))
    locs = {}
    for rd in rom['wild_pokemon']:
        for sc in rd['sections']:
            for ec in sc['encounters']:
                pn = normalize_name(ec['pokemon'])
                (locs[pn].append({'route': rd['name'], 'method': ec['method'], 'rate': str(ec['rate'])}) if pn in locs else locs.update({pn: [{'route': rd['name'], 'method': ec['method'], 'rate': str(ec['rate'])}]}))
        if rd.get('specials'):
            for spec in rd['specials']:
                pn = normalize_name(spec['pokemon'])
                method = spec['method'] or "Fixed"
                (locs[pn].append({'route': rd['name'], 'method': method, 'rate': str(spec['rate']) or 'Fixed'}) if pn in locs else locs.update({pn: [{'route': rd['name'], 'method': method, 'rate': str(spec['rate']) or 'Fixed'}]}))
    for p in pkmn_to_generate:
        md = generate_pokemon_page(p['name'], base_data, rom, base_data['moves'], base_data['abilities'], locs, base_data['pokemon'])
        write_if_changed(os.path.join("docs/pokemon", f"{normalize_name(p['name'])}.md"), md)
    gs = [("Kanto", 1, 151), ("Johto", 152, 251), ("Hoenn", 252, 386), ("Sinnoh", 387, 493), ("Unova", 494, 649)]
    idx_md = "# Pokemon\n\n"
    for gn, s, e in gs:
        idx_md += f"## {gn}\n\n| No. | Sprite | Pokemon |\n| --- | --- | --- |\n"
        for p in pkmn_to_generate:
            if s <= p['id'] <= e: pn = normalize_name(p['name']); idx_md += f"| {p['id']:03} | ![{pn}](../img/pokemon/{p['id']:03}.png) | [{get_display_name(p['name'])}]({pn}.md) |\n"
        idx_md += "\n"
    write_if_changed("docs/pokemon/index.md", idx_md)
    for mn, mi in sorted(base_data['moves'].items()):
        mnn = normalize_name(mn); md = generate_move_page(mn, mi, fmv.get(mnn, []), rom['move_stat_changes'].get(mnn, {}), base_data)
        write_if_changed(os.path.join("docs/moves", f"{mnn}.md"), md)
    mv_idx_md = "# Moves\n\n"
    for m in sorted(base_data['moves'].keys()): mv_idx_md += f"- [{m.replace('-', ' ').capitalize()}]({normalize_name(m)}.md)\n"
    write_if_changed("docs/moves/index.md", mv_idx_md)
    for an, ai in sorted(base_data['abilities'].items()):
        ann = CLEAN_ABILITIES.get(normalize_name(an), normalize_name(an)); md = generate_ability_page(an, ai, fab.get(ann, []), base_data)
        write_if_changed(os.path.join("docs/abilities", f"{ann}.md"), md)
    ab_idx_md = "# Abilities\n\n"
    for a in sorted(base_data['abilities'].keys()): ab_idx_md += f"- [{a.replace('-', ' ').capitalize()}]({CLEAN_ABILITIES.get(normalize_name(a), normalize_name(a))}.md)\n"
    write_if_changed("docs/abilities/index.md", ab_idx_md)
    al = rom['trainer_order']
    for r in rom['wild_pokemon']: (al.append(r['name']) if r['name'] not in al else None)
    for rn in al:
        md = generate_route_page(rn, next((r for r in rom['wild_pokemon'] if r['name'] == rn), None), base_data, rom['trainers'], rom['item_changes'])
        write_if_changed(os.path.join("docs/routes", f"{normalize_name(rn)}.md"), md)
    rt_idx_md = "# Routes\n\n"
    for rn in al: rt_idx_md += f"- [{rn}]({normalize_name(rn)}.md)\n"
    write_if_changed("docs/routes/index.md", rt_idx_md)
    
    item_route_locs, item_pkmn_locs = {}, {}
    # Item locations from romhack changes
    for r_n, subareas in rom['item_changes'].items():
        for sub_n, changes in subareas.items():
            for c in changes:
                inorm = normalize_item_name(c['new'])
                # Added empty info string for consistency
                if inorm not in item_route_locs: item_route_locs[inorm] = []
                item_route_locs[inorm].append((r_n, sub_n, ""))
                
    # Add Serebii base game locations to item pages
    if "location_items_serebii" in base_data:
        for r_n, subareas in base_data["location_items_serebii"].items():
            for sub_n, items in subareas.items():
                for it in items:
                    inorm = normalize_item_name(it["name"])
                    if inorm not in item_route_locs: item_route_locs[inorm] = []
                    item_route_locs[inorm].append((r_n, sub_n, it.get("detail", "")))

    for p_n, p_c in rom['pokemon_changes'].items():
        if p_c.get('items'):
            for i in p_c['items']:
                inorm = normalize_item_name(i)
                (item_pkmn_locs[inorm].append(p_n) if inorm in item_pkmn_locs else item_pkmn_locs.update({inorm: [p_n]}))
    for iname_norm, iinfo in base_data.get('items', {}).items():
        md = generate_item_page(iinfo["name"], iinfo, item_route_locs.get(iname_norm, []), item_pkmn_locs.get(iname_norm, []), base_data['moves'], base_data)
        write_if_changed(os.path.join("docs/items", f"{iname_norm}.md"), md)
    it_idx_md = "# Items\n\n"
    for inm in sorted(base_data.get('items', {}).keys()): it_idx_md += f"- [{base_data['items'][inm]['name']}]({inm}.md)\n"
    write_if_changed("docs/items/index.md", it_idx_md)
    for d in ['docs/pokemon', 'docs/moves', 'docs/abilities', 'docs/routes', 'docs/items']:
        if os.path.exists(d):
            for f in os.listdir(d):
                fp = os.path.abspath(os.path.join(d, f))
                if fp not in WRITTEN_FILES and os.path.isfile(fp): os.remove(fp)
    with open("mkdocs.yml", 'r', encoding='utf-8') as f: ls = f.readlines()
    nl, inav = [], False
    for l in ls:
        if l.startswith('nav:'):
            inav = True; nl.append('nav:\n  - Home: README.md\n  - Pokemon:\n    - pokemon/index.md\n')
            for gn, s, e in gs:
                nl.append(f'    - {gn}:\n')
                for p in pkmn_to_generate:
                    if s <= p['id'] <= e: pn = normalize_name(p['name']); nl.append(f"      - {get_display_name(p['name'])}: pokemon/{pn}.md\n")
            nl.append('  - Routes:\n    - routes/index.md\n'); [nl.append(f"    - {rn}: routes/{normalize_name(rn)}.md\n") for rn in al]
            nl.append('  - Items:\n    - items/index.md\n'); [nl.append(f"    - {base_data['items'][inm]['name']}: items/{inm}.md\n") for inm in sorted(base_data.get('items', {}).keys())]
            nl.append('  - Moves:\n    - moves/index.md\n'); [nl.append(f"    - {m.replace('-', ' ').capitalize()}: moves/{normalize_name(m)}.md\n") for m in sorted(base_data['moves'].keys())]
            nl.append('  - Abilities:\n    - abilities/index.md\n'); [nl.append(f"    - {a.replace('-', ' ').capitalize()}: abilities/{CLEAN_ABILITIES.get(normalize_name(a), normalize_name(a))}.md\n") for a in sorted(base_data['abilities'].keys())]
        elif not inav: nl.append(l)
    with open("mkdocs.yml", 'w', encoding='utf-8') as f: f.writelines(nl)
    print("Generation complete.")
