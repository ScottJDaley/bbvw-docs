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

def get_display_name(name):
    if name.lower().startswith('mime-jr'): return "Mime Jr."
    if name.lower().startswith('mr-mime'): return "Mr. Mime"
    if name.lower().startswith('ho-oh'): return "Ho-Oh"
    if name.lower().startswith('porygon-z'): return "Porygon-Z"
    if name.lower().startswith('porygon2'): return "Porygon2"
    if name.lower().startswith('nidoran-m'): return "Nidoran♂"
    if name.lower().startswith('nidoran-f'): return "Nidoran♀"
    
    # Generic form removal for display
    res = name.split('-')[0].capitalize()
    # Special cases for names with dashes that aren't forms
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
    return base, rom

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
    t_icon = f'![{m_info["type"]}]({base_path}img/types/{m_info["type"]}.png)'
    c_icon = f'![{m_info["damage_class"]}]({base_path}img/types/{m_info["damage_class"]}.png){{ style="vertical-align:middle; object-fit:contain;" }}'
    
    if show_tm: return f"| {m_info.get('tm_num', '-')} | {link_str} | {t_icon} | {c_icon} | {p} | {a} | {m_info['pp']} |"
    return f"| {link_str} | {t_icon} | {c_icon} | {p} | {a} | {m_info['pp']} |"

def get_full_evolution_chains(p_base, all_pokemon_base):
    chain = p_base['evolution_chain']['chain']
    paths = []
    def traverse(node, current_path):
        name = node['species']['name']
        # Filter for Gen 5 or below (ID <= 649)
        p_id = 999
        p_info = all_pokemon_base.get(normalize_name(name))
        if p_info: p_id = p_info['id']
        else:
            for pk in all_pokemon_base.values():
                if pk['name'] == name:
                    p_id = pk['id']
                    break
        
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
                c_name = next_node['species']['name']
                c_id = 999
                c_info = all_pokemon_base.get(normalize_name(c_name))
                if c_info: c_id = c_info['id']
                if c_id <= 649:
                    traverse(next_node, new_path)
                    found_valid_child = True
            if not found_valid_child: paths.append(new_path)
            
    traverse(chain, [])
    return [p for p in paths if p]

def generate_pokemon_page(name, base_data, rom_data, move_data, ability_data, locations):
    p_n_k = normalize_name(name)
    p_base = base_data.get(p_n_k)
    if not p_base: return None
    p_rom = rom_data['pokemon_changes'].get(name.lower(), {})
    if not p_rom: # try looking up by normalized name in rom changes
        p_rom = rom_data['pokemon_changes'].get(p_n_k, {})
    p_moves_rom = rom_data['move_changes'].get(name.lower(), [])
    if not p_moves_rom:
        p_moves_rom = rom_data['move_changes'].get(p_n_k, [])
    
    display_name = get_display_name(name)

    md = f"# {display_name}\n\n![{p_n_k}](../img/pokemon/{p_base['id']:03}.png)\n\n"
    c_t = p_rom.get('types') or p_base['types']
    md += "## Type\n" + (f"Original: {' '.join([f'![{t}](../img/types/{t}.png)' for t in p_base['types']])}  \nNew: {' '.join([f'![{t}](../img/types/{t}.png)' for t in p_rom['types']])}\n\n" if p_rom.get('types') and p_rom['types'] != p_base['types'] else ' '.join([f'![{t}](../img/types/{t}.png)' for t in p_base['types']]) + "\n\n")
    
    md += "## Evolution\n"
    ps = get_full_evolution_chains(p_base, base_data)
    if ps:
        mx = max(len(p) for p in ps); md += "|" + " | ".join(["Stage" if i%2==0 else "" for i in range(2*mx-1)]) + " |\n|" + " | ".join([":---:" for _ in range(2*mx-1)]) + " |\n"
        for p in ps:
            rp = []
            for i in range(mx):
                if i < len(p):
                    st = p[i]; s_n = normalize_name(st['name']); info = base_data.get(s_n)
                    if info:
                        rp.append(f"![{s_n}](../img/pokemon/{info['id']:03}.png)<br>**[{get_display_name(st['name'])}]( {s_n}.md)**")
                    else:
                        rp.append(f"**[{get_display_name(st['name'])}]( {s_n}.md)**")
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
        for item in p_rom['items']:
            item_name = item.split('(')[0].strip(); item_norm = normalize_name(item_name)
            md += f"- ![{item_name}](../img/items/{item_norm}.png) {item}\n"
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
            md += f"| [{loc['route']}](../routes/{fname}.md) | ![{m_lower}](../img/items/{icon}) {loc['method']} | {loc['rate']}% |\n"
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
        if bn in explicit_removed:
            am.append({'level': bm['level'], 'name': bm['name'], 'marker': 'REMOVED'})
            continue
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
    
    ln = [m for m in p_base['moves'] if m['method'] != 'level-up']
    for rl in p_rom.get('tm_hm', []):
        for pref, num, mn in re.findall(r'(TM|HM)(\d+)\s*,?\s*([^,.\n]+)', rl):
            if not any(normalize_name(m['name']) == normalize_name(mn) for m in ln): ln.append({'name': mn, 'method': 'machine', 'rom_new': True})
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
    md += gmt("TM Moves", [m for m in ln if m['method'] == 'machine' and move_data.get(normalize_name(m['name']), {}).get('tm_num', '').startswith('TM')])
    md += gmt("HM Moves", [m for m in ln if m['method'] == 'machine' and move_data.get(normalize_name(m['name']), {}).get('tm_num', '').startswith('HM')])
    md += gmt("Egg Moves", [m for m in ln if m['method'] == 'egg']) + gmt("Tutor Moves", [m for m in ln if m['method'] == 'tutor'])
    return md

def generate_move_page(name, info, pkmn_list, m_rom, base_data):
    md = f"# {name.replace('-', ' ').capitalize()}\n\n**Type:** ![{info['type']}](../img/types/{info['type']}.png)  \n**Category:** ![{info['damage_class']}](../img/types/{info['damage_class']}.png)  \n**Power:** {info['power']}  \n**Accuracy:** {info['accuracy']}  \n**PP:** {info['pp']}  \n\n## Description\n{info['description']}\n\n## Learned by\n| Sprite | Pokemon |\n| --- | --- |\n"
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

def generate_route_page(name, r_d, base_data, t_d):
    md = f"# {name}\n\n"
    if r_d:
        for sc in r_d['sections']:
            md += f"## {sc['title']}\n"
            ms = {}
            for ec in sc['encounters']: ms[ec['method']] = ms.get(ec['method'], []) + [ec]
            for m, ecs in ms.items():
                ml = m.lower().replace(',', ''); icon = "grass-normal.png"
                if 'surf special' in ml: icon = "surf-special.png"
                elif 'fish special' in ml: icon = "fishing-special.png"
                elif 'cave' in ml: icon = "cave-normal.png"
                elif 'surf' in ml: icon = "surf-normal.png"
                elif 'fish' in ml: icon = "fishing-normal.png"
                md += f"### ![{m}](../img/items/{icon}) {m}\n| Sprite | Pokemon | Rate |\n| --- | --- | --- |\n"
                for ec in ecs:
                    pn = normalize_name(ec['pokemon']); info = base_data['pokemon'].get(pn)
                    md += f"| ![{pn}](../img/pokemon/{info['id']:03}.png) | [{get_display_name(ec['pokemon'])}](../pokemon/{pn}.md) | {ec['rate']}% |\n" if info else f"| | {ec['pokemon']} | {ec['rate']}% |\n"
                md += "\n"
    lt = t_d.get(name)
    if lt:
        md += "\n## Trainers\n"
        gs = {}
        for t in lt:
            h = t.get('group_header', ''); gs[h] = gs.get(h, []) + [t]
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
                    md += f"| {sprite} | [{get_display_name(p['name'])}](../pokemon/{pn}.md) | {p['level']} | {p['ability']} | {p['item']} | {', '.join(p['moves'])} |\n"
                md += "\n"
    return md

if __name__ == "__main__":
    for d in ['docs/pokemon', 'docs/moves', 'docs/abilities', 'docs/routes']:
        if os.path.exists(d): shutil.rmtree(d)
        os.makedirs(d)
    base, rom = load_data(); base['pokemon']['basculin'] = base['pokemon'].get('basculin-red-striped', base['pokemon'].get('basculin'))
    
    priority_forms = ['-normal', '-male', '-plant', '-red-striped', '-land', '-altered', '-standard', '-ordinary', '-aria', '-incarnate', '-spring']
    normalized_pkmn = {}
    pkmn_sorted = sorted(base['pokemon'].values(), key=lambda x: x['id'])
    for p in pkmn_sorted:
        if p['id'] > 649: continue
        nn = normalize_name(p['name'])
        if nn not in normalized_pkmn:
            normalized_pkmn[nn] = p
        else:
            current_p = normalized_pkmn[nn]
            for pf in priority_forms:
                if p['name'].endswith(pf):
                    normalized_pkmn[nn] = p
                    break
                if current_p['name'].endswith(pf):
                    break
    base['pokemon'] = normalized_pkmn
    pkmn_to_generate = sorted(base['pokemon'].values(), key=lambda x: x['id'])
    print(f"Generating pages for {len(pkmn_to_generate)} pokemon.")

    fab, fmv = {}, {}
    for p in pkmn_to_generate:
        pn = p['name']; pr = rom['pokemon_changes'].get(pn, {}); pa = [extract_specific_ability(a, pn) for a in [pr.get('abilities', {}).get('one'), pr.get('abilities', {}).get('two')] if a]
        if not any(pa): pa = p['abilities']
        for ab in pa:
            an = CLEAN_ABILITIES.get(normalize_name(ab), normalize_name(ab))
            if an: (fab[an].append(pn) if an in fab else fab.update({an: [pn]}))
        pms = set([m['name'] for m in p['moves']] + [rm['name'] for rm in rom['move_changes'].get(pn, []) if rm.get('name')])
        for rl in pr.get('tm_hm', []):
            for m in re.findall(r'(TM|HM)\d+\s*,?\s*([^,.\n]+)', rl): pms.add(m[1])
        for tl in pr.get('tutor', []):
            for m in re.findall(r'([^,.\n]+)', tl): pms.add(m)
        for m in pms:
            mn = normalize_name(m)
            if mn: (fmv[mn].append(pn) if mn in fmv else fmv.update({mn: [pn]}))
    locs = {}
    for rd in rom['wild_pokemon']:
        for sc in rd['sections']:
            for ec in sc['encounters']:
                pn = normalize_name(ec['pokemon'])
                (locs[pn].append({'route': rd['name'], 'method': ec['method'], 'rate': ec['rate']}) if pn in locs else locs.update({pn: [{'route': rd['name'], 'method': ec['method'], 'rate': ec['rate']}]}))
    for p in pkmn_to_generate:
        md = generate_pokemon_page(p['name'], base['pokemon'], rom, base['moves'], base['abilities'], locs)
        if md:
            with open(os.path.join("docs/pokemon", f"{normalize_name(p['name'])}.md"), 'w', encoding='utf-8') as f: f.write(md)
    
    gs = [("Kanto", 1, 151), ("Johto", 152, 251), ("Hoenn", 252, 386), ("Sinnoh", 387, 493), ("Unova", 494, 649)]
    with open("docs/pokemon/index.md", 'w', encoding='utf-8') as f:
        f.write("# Pokemon\n\n")
        for gn, s, e in gs:
            f.write(f"## {gn}\n\n| No. | Sprite | Pokemon |\n| --- | --- | --- |\n")
            for p in pkmn_to_generate:
                if s <= p['id'] <= e: pn = normalize_name(p['name']); f.write(f"| {p['id']:03} | ![{pn}](../img/pokemon/{p['id']:03}.png) | [{get_display_name(p['name'])}]({pn}.md) |\n")
            f.write("\n")
    for mn, mi in sorted(base['moves'].items()):
        mnn = normalize_name(mn); md = generate_move_page(mn, mi, fmv.get(mnn, []), rom['move_stat_changes'].get(mnn, {}), base)
        with open(os.path.join("docs/moves", f"{mnn}.md"), 'w', encoding='utf-8') as f: f.write(md)
    with open("docs/moves/index.md", 'w', encoding='utf-8') as f:
        f.write("# Moves\n\n"); [f.write(f"- [{m.replace('-', ' ').capitalize()}]({normalize_name(m)}.md)\n") for m in sorted(base['moves'].keys())]
    for an, ai in sorted(base['abilities'].items()):
        ann = CLEAN_ABILITIES.get(normalize_name(an), normalize_name(an)); md = generate_ability_page(an, ai, fab.get(ann, []), base)
        with open(os.path.join("docs/abilities", f"{ann}.md"), 'w', encoding='utf-8') as f: f.write(md)
    with open("docs/abilities/index.md", 'w', encoding='utf-8') as f:
        f.write("# Abilities\n\n"); [f.write(f"- [{a.replace('-', ' ').capitalize()}]({CLEAN_ABILITIES.get(normalize_name(a), normalize_name(a))}.md)\n") for a in sorted(base['abilities'].keys())]
    al = rom['trainer_order']
    for r in rom['wild_pokemon']: (al.append(r['name']) if r['name'] not in al else None)
    for rn in al:
        md = generate_route_page(rn, next((r for r in rom['wild_pokemon'] if r['name'] == rn), None), base, rom['trainers'])
        with open(os.path.join("docs/routes", f"{normalize_name(rn)}.md"), 'w', encoding='utf-8') as f: f.write(md)
    with open("mkdocs.yml", 'r', encoding='utf-8') as f: ls = f.readlines()
    nl, inav = [], False
    for l in ls:
        if l.startswith('nav:'):
            inav = True; nl.append('nav:\n  - Home: README.md\n  - Pokemon:\n    - pokemon/index.md\n')
            for gn, s, e in gs:
                nl.append(f'    - {gn}:\n')
                for p in pkmn_to_generate:
                    if s <= p['id'] <= e: pn = normalize_name(p['name']); nl.append(f"      - {get_display_name(p['name'])}: pokemon/{pn}.md\n")
            nl.append('  - Routes:\n')
            for rn in al: nl.append(f"    - {rn}: routes/{normalize_name(rn)}.md\n")
            nl.append('  - Moves:\n'); [nl.append(f"    - {m.replace('-', ' ').capitalize()}: moves/{normalize_name(m)}.md\n") for m in sorted(base['moves'].keys())]
            nl.append('  - Abilities:\n'); [nl.append(f"    - {a.replace('-', ' ').capitalize()}: abilities/{CLEAN_ABILITIES.get(normalize_name(a), normalize_name(a))}.md\n") for a in sorted(base['abilities'].keys())]
        elif not inav: nl.append(l)
    with open("mkdocs.yml", 'w', encoding='utf-8') as f: f.writelines(nl)
    print("Generation complete.")
