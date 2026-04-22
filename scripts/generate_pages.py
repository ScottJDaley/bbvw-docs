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
    'featherdance': 'feather-dance', 'reflect,-light-screen': 'reflect', 'nothing': '', 'basculin': 'basculin'
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
    name = re.sub(r'([a-z])([A-Z])', r'\1-\2', name); name = name.lower().strip()
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
    name = name.lower().strip(); name = re.sub(r'\(.*?\)', '', name).strip()
    tm_match = re.match(r'(tm|hm)(\d+)\s*(.*)', name)
    if tm_match: return f"{tm_match.group(1)}{int(tm_match.group(2)):02}"
    name = re.sub(r'\s*\*\s*\d+', '', name); name = name.replace('poké', 'poke'); name = name.replace(' ', '-').replace("'", "").replace('.', '').replace('/', '-')
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
    res = name.split('-')[0].replace('-', ' ').title()
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
                if inorm not in base["items"]: base["items"][inorm] = {"name": iname, "description": idata["description"], "category": idata["category"]}
                else: base["items"][inorm]["category"] = idata["category"]
            base["location_items_serebii"] = serebii["route_items"]
    return base, rom

def get_item_icon(name, move_data, base_path="../"):
    norm = normalize_item_name(name)
    if norm == "x-defend": return f"{base_path}img/items/x-defense.png"
    if norm == "x-special": return f"{base_path}img/items/x-sp-atk.png"
    if norm.startswith('tm') or norm.startswith('hm'):
        m_match = re.search(r'(?:TM|HM)\d+\s+(.*)', name, re.IGNORECASE)
        if m_match:
            m_n = normalize_name(m_match.group(1)); m_i = move_data.get(m_n)
            if m_i: return f"{base_path}img/items/tm-{m_i['type']}.png"
        tm_u = norm.upper()
        for m_i in move_data.values():
            if m_i.get('tm_num') == tm_u: return f"{base_path}img/items/tm-{m_i['type']}.png"
        return f"{base_path}img/items/tm-normal.png"
    i_p = f"img/items/{norm}.png"; return f"{base_path}{i_p}" if os.path.exists(os.path.join(OUTPUT_BASE, i_p)) else f"{base_path}img/items/unknown.png"

def get_item_display_linked(name, base_data, base_path="../"):
    if not name or name == "-": return "-"
    norm = normalize_item_name(name); icon = get_item_icon(name, base_data['moves'], base_path)
    if norm in base_data.get('items', {}): return f"![{name}]({icon}) [{name}]({base_path}items/{norm}.md)"
    return f"![{name}]({icon}) {name}"

def get_move_display(m_name, move_data, move_stat_changes, base_path="../", show_tm=False):
    def gsl(mn):
        mn_n = normalize_name(mn); info = move_data.get(mn_n)
        return f"[{mn}]({base_path}moves/{mn_n}.md)" if not info else f"[{mn.replace('-', ' ').title()}]({base_path}moves/{mn_n}.md)"
    m_l = [m.strip() for m in m_name.split('/')] if '/' in m_name else ([m.strip() for m in m_name.split(',')] if ',' in m_name and 'TM' not in m_name else [m_name])
    links = [gsl(m) for m in m_l if normalize_name(m)]; l_s = ", ".join(links); m_n = normalize_name(m_l[0]); m_i = move_data.get(m_n)
    if not m_i: return f"| {l_s} | - | - | - | - | - |"
    m_r = move_stat_changes.get(m_n, {})
    def fs(s, v):
        if s in m_r: return f'<span style="color:green; font-weight:bold;">{m_r[s]["new"]}</span> <span style="text-decoration:line-through; color:red; font-size:0.9em;">{m_r[s]["old"]}</span>'
        return str(v or '-')
    p, a, pp = fs('power', m_i['power']), fs('accuracy', m_i['accuracy']), fs('pp', m_i['pp']); t_v = m_i["type"]; t_i = f'![{t_v}]({base_path}img/types/{t_v}.png)'
    if 'type' in m_r: t_i = f'![{m_r["type"]["new"]}]({base_path}img/types/{m_r["type"]["new"]}.png) <span style="text-decoration:line-through; color:red; font-size:0.9em;">{m_i["type"]}</span>'
    c_i = f'![{m_i["damage_class"]}]({base_path}img/types/{m_i["damage_class"]}.png){{ style="vertical-align:middle; object-fit:contain;" }}'
    return f"| {m_i.get('tm_num', '-')} | {l_s} | {t_i} | {c_i} | {p} | {a} | {pp} |" if show_tm else f"| {l_s} | {t_i} | {c_i} | {p} | {a} | {pp} |"

def get_full_evolution_chains(p_base, all_pokemon_base):
    chain = p_base['evolution_chain']['chain']; paths = []
    def tr(node, c_p):
        name = node['species']['name']; p_id = 999; p_info = all_pokemon_base.get(normalize_name(name))
        if p_info: p_id = p_info['id']
        else:
            for pk in all_pokemon_base.values():
                if pk['name'] == name: p_id = pk['id']; break
        if p_id > 649:
            if c_p: paths.append(c_p)
            return
        m = ""
        if node['evolution_details']:
            d = node['evolution_details'][0]; mp = []
            if d['trigger']['name'] == 'level-up':
                if d['min_level']: mp.append(f"Lv. {d['min_level']}")
                if d['min_happiness']: mp.append("Happiness")
                if d['held_item']: mp.append(f"Hold {d['held_item']['name']}")
                if d['location']: mp.append(f"At {d['location']['name']}")
                if d['known_move']: mp.append(f"Know {d['known_move']['name']}")
                if d['gender']: mp.append("Male" if d['gender'] == 2 else "Female")
                if d['relative_physical_stats'] is not None: mp.append("Atk > Def" if d['relative_physical_stats'] == 1 else ("Def > Atk" if d['relative_physical_stats'] == -1 else "Atk = Def"))
                if not mp: mp.append("Level Up")
            elif d['trigger']['name'] == 'use-item': mp.append(f"Use {d['item']['name']}")
            elif d['trigger']['name'] == 'trade': mp.append(f"Trade hold {d['held_item']['name']}" if d['held_item'] else "Trade")
            m = ", ".join(mp)
        n_p = c_p + [{'name': name, 'method': m}]
        if not node['evolves_to']: paths.append(n_p)
        else:
            fc = False
            for nn in node['evolves_to']:
                cn = nn['species']['name']; ci = all_pokemon_base.get(normalize_name(cn))
                if ci and ci['id'] <= 649: tr(nn, n_p); fc = True
            if not fc: paths.append(n_p)
    tr(chain, []); return [p for p in paths if p]

def generate_pokemon_page(name, base_data, rom_data, move_data, ability_data, locations, pokemon_all_base):
    p_n_k = normalize_name(name); p_base = pokemon_all_base.get(p_n_k)
    if not p_base: return None
    ubm, sbm = [], set()
    for m in p_base['moves']:
        mid = f"{m['level']}-{m['name']}-{m['method']}"; (ubm.append(m) or sbm.add(mid) if mid not in sbm else None)
    p_base['moves'] = ubm; p_rom = rom_data['pokemon_changes'].get(name.lower(), {})
    if not p_rom: p_rom = rom_data['pokemon_changes'].get(p_n_k, {})
    p_moves_rom = rom_data['move_changes'].get(name.lower(), [])
    if not p_moves_rom: p_moves_rom = rom_data['move_changes'].get(p_n_k, [])
    display_name = get_display_name(name); md = f"# {display_name}\n\n![{p_n_k}](../img/pokemon/{p_base['id']:03}.png)\n\n"; ct = p_rom.get('types') or p_base['types']
    md += "## Type\n" + (f"Original: {' '.join([f'![{t}](../img/types/{t}.png)' for t in p_base['types']])}  \nNew: {' '.join([f'![{t}](../img/types/{t}.png)' for t in p_rom['types']])}\n\n" if p_rom.get('types') and p_rom['types'] != p_base['types'] else ' '.join([f'![{t}](../img/types/{t}.png)' for t in p_base['types']]) + "\n\n")
    md += "## Evolution\n"; ps = get_full_evolution_chains(p_base, pokemon_all_base)
    if ps:
        mx = max(len(p) for p in ps); md += "|" + " | ".join(["Stage" if i%2==0 else "" for i in range(2*mx-1)]) + " |\n|" + " | ".join([":---:" for _ in range(2*mx-1)]) + " |\n"
        for p in ps:
            rp = []
            for i in range(mx):
                if i < len(p):
                    st = p[i]; sn = normalize_name(st['name']); info = pokemon_all_base.get(sn); rp.append(f"![{sn}](../img/pokemon/{info['id']:03}.png)<br>**[{get_display_name(st['name'])}]( {sn}.md)**" if info else f"**[{get_display_name(st['name'])}]( {sn}.md)**")
                    if i < mx - 1:
                        if i+1 < len(p):
                            nxt = p[i+1]; nxtn = normalize_name(nxt['name']); rmm = ""; curr_rom = rom_data['pokemon_changes'].get(st['name'].lower(), {})
                            if curr_rom.get('evolution'):
                                for rv in curr_rom['evolution']:
                                    if rv['target'] and normalize_name(rv['target']) == nxtn: rmm = rv['method']
                            rp.append(f"➡️<br>{rmm if rmm else nxt['method']}")
                        else: rp.append("")
                else: rp.append(""); (rp.append("") if i < mx-1 else None)
            md += "|" + " | ".join(rp) + " |\n"
    else: md += "No evolution.\n"
    md += "\n## Abilities\n"; a1n = extract_specific_ability(p_rom.get('abilities', {}).get('one', ''), name); a2n = extract_specific_ability(p_rom.get('abilities', {}).get('two', ''), name); orig_abs = [a.replace('-', ' ').capitalize() for a in p_base['abilities']]
    def gab(an):
        n = normalize_name(an); n = CLEAN_ABILITIES.get(n, n); d = ability_data.get(n, {}).get('description', '')
        return f"**[{an}](../abilities/{n}.md)**: {d}" if n else an
    md += f"| Slot | Original | New |\n| --- | --- | --- |\n| Ability 1 | {gab(orig_abs[0]) if len(orig_abs) > 0 else '-'} | {gab(a1n if a1n else (orig_abs[0] if len(orig_abs) > 0 else '-'))} |\n| Ability 2 | {gab(orig_abs[1]) if len(orig_abs) > 1 else '-'} | {gab(a2n if a2n else (orig_abs[1] if len(orig_abs) > 1 else '-'))} |\n\n"
    md += "## Base Happiness\n" + (f'<span style="color:green; font-weight:bold;">{p_rom["happiness"]["new"]}</span> <span style="text-decoration:line-through; color:red; font-size:0.9em;">{p_rom["happiness"].get("old", 70)}</span>\n\n' if p_rom.get('happiness') else "70\n\n")
    md += "## Held Items\n"; (md + "".join([f"- {get_item_display_linked(item, base_data)}\n" for item in p_rom['items']]) if p_rom.get('items') else md + "None\n")
    md += "\n## Type Defenses\n| 0x | 0.5x | 1x | 2x | 4x |\n| --- | --- | --- | --- | --- |\n"; eff = {t: 1.0 for t in TYPE_CHART.keys()}
    for td in ct:
        if td in TYPE_CHART:
            for ta, ch in TYPE_CHART.items():
                if td in ch: eff[ta] *= ch[td]
    c0, c05, c1, c2, c4 = [[f"![{t}](../img/types/{t}.png)" for t, v in eff.items() if v == val] for val in [0, 0.5, 1, 2, 4]]
    for i in range(max(len(c0), len(c05), len(c1), len(c2), len(c4))): md += f"| {c0[i] if i < len(c0) else ''} | {c05[i] if i < len(c05) else ''} | {c1[i] if i < len(c1) else ''} | {c2[i] if i < len(c2) else ''} | {c4[i] if i < len(c4) else ''} |\n"
    md += "\n## Base Stats\n| Stat | Value | Bar |\n| --- | --- | --- |\n"; tv = 0
    for s in ['hp', 'attack', 'defense', 'special-attack', 'special-defense', 'speed']:
        ov = p_base['stats'].get(s, 0); nd = p_rom.get('stats', {}).get(s.replace('-', '_')); nv = nd['new'] if nd else ov; tv += nv; dv = f'<span style="color:green; font-weight:bold;">{nv}</span> <span style="text-decoration:line-through; color:red; font-size:0.9em;">{ov}</span>' if nd else str(nv); cl = "#23CD5E" if nv >= 150 else ("#A0E515" if nv >= 110 else ("#FFDD57" if nv >= 70 else ("#FF7F0E" if nv >= 40 else "#F34444")))
        md += f"| {s.capitalize().replace('-', ' ')} | {dv} | <div style='background:#eee; width:300px; height:15px; border-radius:10px; overflow:hidden; border:1px solid #ddd;'><div style='height:100%; width:{min(100, (nv/200)*100)}%; background:{cl};'></div></div> |\n"
    md += f"| **Total** | **{tv}** | |\n\n## Locations\n"; (md + "| Route | Method | Rate |\n| --- | --- | --- |\n" + "".join([f"| [{l['route']}](../routes/{normalize_name(l['route'])}.md) | ![{l['method'].lower()}](../img/items/{('surf-special.png' if 'surf special' in l['method'].lower() else ('fishing-special.png' if 'fish special' in l['method'].lower() else ('cave-special.png' if 'cave special' in l['method'].lower() else ('grass-special.png' if 'special' in l['method'].lower() else ('grass-doubles.png' if 'doubles' in l['method'].lower() else ('surf-normal.png' if 'surf' in l['method'].lower() else ('fishing-normal.png' if 'fish' in l['method'].lower() else ('cave-normal.png' if 'cave' in l['method'].lower() else ('sand-normal.png' if 'sand' in l['method'].lower() else 'grass-normal.png'))))))))}) {l['method']} | {l['rate'] if '%' in l['rate'] or l['rate'] == 'Fixed' else l['rate'] + '%'} |\n" for l in locations[p_n_k]]) if p_n_k in locations else md + "No known wild location.\n")
    md += "\n## Level Up Moves\n| Level | Move | Type | Cat | Power | Acc | PP |\n| :--- | :--- | :--- | :--- | :--- | :--- | :--- |\n"; blm = [m for m in p_base['moves'] if m['method'] == 'level-up']; am, exrm, lsh = [], set(), []; [exrm.add(normalize_name(rm['name'])) if rm.get('marker') == 'REMOVED' else (lsh.extend(rm.get('level_shifts', [])) if rm.get('marker') == 'SHIFT_REMAINING' else None) for rm in p_moves_rom]
    pbi, bmbl = set(), {}
    for i, bm in enumerate(blm): (bmbl[bm['level']].append(i) if bm['level'] in bmbl else bmbl.update({bm['level']: [i]}))
    for rm in p_moves_rom:
        if rm.get('marker') in ['REMOVED', 'SHIFT_REMAINING']: continue
        if rm.get('marker') == '-':
            lv = rm['level']
            if lv in bmbl:
                for idx in bmbl[lv]:
                    if idx not in pbi: am.append({'level': lv, 'name': blm[idx]['name'], 'marker': 'REMOVED'}); pbi.add(idx); break
            am.append({'level': lv, 'name': rm['name'], 'marker': '+'})
        else: am.append(rm)
    bifs = 0
    for i, bm in enumerate(blm):
        if i in pbi: continue
        bn = normalize_name(bm['name'])
        if bn in exrm: am.append({'level': bm['level'], 'name': bm['name'], 'marker': 'REMOVED'}); continue
        if any(normalize_name(rm['name']) == bn for rm in am if rm.get('marker') != 'REMOVED'): continue
        if lsh and bifs < len(lsh) and bm['level'] >= 60: am.append({'level': lsh[bifs], 'name': bm['name'], 'marker': '='}); bifs += 1; continue
        am.append({'level': bm['level'], 'name': bm['name'], 'marker': ''})
    am.sort(key=lambda x: (x.get('level', 0), 1 if x.get('marker') == 'REMOVED' else 0, x['name']))
    for m in am:
        mn = m['name']; mnn = normalize_name(mn); rw = get_move_display(mn, move_data, rom_data['move_stat_changes']); mk = m.get('marker', ''); ct = (' <span class="pill pill-new">NEW</span>' if mk in ['+', '-'] else (' <span class="pill pill-removed">REMOVED</span>' if mk == 'REMOVED' else (' <span class="pill pill-shifted">SHIFTED</span>' if mk == '=' else "")))
        md += f"| {m['level']} {ct} {rw}\n"
    lnb = [m for m in p_base['moves'] if m['method'] != 'level-up']
    for rl in p_rom.get('tm_hm', []):
        for prf, num, mn in re.findall(r'(TM|HM)(\d+)\s*,?\s*([^,.\n]+)', rl):
            if not any(normalize_name(m['name']) == normalize_name(mn) for m in lnb): lnb.append({'name': mn, 'method': 'machine', 'rom_new': True})
    def gmt(t, ml):
        if not ml: return ""
        res = f"\n## {t}\n| No. | Move | Type | Cat | Power | Acc | PP |\n| :--- | :--- | :--- | :--- | :--- | :--- | :--- |\n"; ml.sort(key=lambda x: x['name']); prc = set()
        for m in ml:
            mn = m['name']; mnn = normalize_name(mn)
            if not mnn or mnn in prc: continue
            prc.add(mnn); rw = get_move_display(mn, move_data, rom_data['move_stat_changes'], show_tm=True)
            if m.get('rom_new'): rp = rw.split('|'); rp[1] = rp[1] + ' <span class="pill pill-new">NEW</span>'; rw = "|".join(rp)
            res += rw + "\n"
        return res
    md += gmt("TM Moves", [m for m in lnb if m['method'] == 'machine' and move_data.get(normalize_name(m['name']), {}).get('tm_num', '').startswith('TM')]) + gmt("HM Moves", [m for m in lnb if m['method'] == 'machine' and move_data.get(normalize_name(m['name']), {}).get('tm_num', '').startswith('HM')]) + gmt("Egg Moves", [m for m in lnb if m['method'] == 'egg']) + gmt("Tutor Moves", [m for m in lnb if m['method'] == 'tutor']); return md

def generate_move_page(name, info, pkmn_list, m_rom, base_data):
    md = f"# {name.replace('-', ' ').title()}\n\n"; def fs(s, v):
        if s in m_rom: return f'<span style="color:green; font-weight:bold;">{m_rom[s]["new"]}</span> <span style="text-decoration:line-through; color:red; font-size:0.9em;">{m_rom[s]["old"]}</span>'
        return str(v or '-'); ti = f'![{info["type"]}](../img/types/{info["type"]}.png)'
    if 'type' in m_rom: ti = f'![{m_rom["type"]["new"]}](../img/types/{m_rom["type"]["new"]}.png) <span style="text-decoration:line-through; color:red; font-size:0.9em;">{info["type"]}</span>'
    tml = f"**TM/HM:** [{info['tm_num']}](../items/{info['tm_num'].lower()}.md)\n\n" if info.get('tm_num') else ""; md += f"{tml}**Type:** {ti}  \n**Category:** ![{info['damage_class']}](../img/types/{info['damage_class']}.png){{ style='object-fit:contain;' }}  \n**Power:** {fs('power', info['power'])}  \n**Accuracy:** {fs('accuracy', info['accuracy'])}  \n**PP:** {fs('pp', info['pp'])}  \n\n## Description\n{info['description']}\n\n## Learned by\n| Sprite | Pokemon |\n| --- | --- |\n"; [md + f"| ![{normalize_name(p)}](../img/pokemon/{base_data['pokemon'][normalize_name(p)]['id']:03}.png) | [{get_display_name(p)}](../pokemon/{normalize_name(p)}.md) |\n" for p in sorted(pkmn_list) if normalize_name(p) in base_data['pokemon']]; return md

def generate_ability_page(name, info, pkmn_list, base_data):
    md = f"# {name.replace('-', ' ').title()}\n\n## Description\n{info['description']}\n\n## Pokemon with this Ability\n| Sprite | Pokemon |\n| --- | --- |\n"; [md + f"| ![{normalize_name(p)}](../img/pokemon/{base_data['pokemon'][normalize_name(p)]['id']:03}.png) | [{get_display_name(p)}](../pokemon/{normalize_name(p)}.md) |\n" for p in sorted(pkmn_list) if normalize_name(p) in base_data['pokemon']]; return md

def get_item_display_name(norm_name, base_data):
    ii = base_data.get('items', {}).get(norm_name)
    if ii and ii.get('name'):
        n = ii['name']
        if re.match(r'^[th]m\d+', n, re.IGNORECASE): return n.upper()
        return n.replace('-', ' ').title() if n.islower() else n
    return norm_name.upper() if re.match(r'^(tm|hm)(\d+)', norm_name) else norm_name.replace('-', ' ').title()

def generate_item_page(norm_name, info, route_locations, pkmn_with_item, move_data, base_data):
    idn = get_item_display_name(norm_name, base_data); icon = get_item_icon(idn, move_data)
    md = f"# ![icon]({icon}) {idn}\n\n**Category:** {info.get('category', 'Misc').capitalize()}\n\n"; tmm = re.match(r'^(?:TM|HM)(\d+)', idn, re.IGNORECASE)
    if tmm:
        mp = idn.split(' ', 1)[1] if ' ' in idn else ""
        if not mp:
            tu = tmm.group(0).upper()
            for mn, mi in base_data['moves'].items():
                if mi.get('tm_num') == tu: mp = mn.replace('-', ' ').title(); break
        if mp: md += f"**Teaches Move:** [{mp}](../moves/{normalize_name(mp)}.md)\n\n"
    md += f"## Description\n{info.get('description', 'No description available.')}\n\n"; (md + "## Locations\n| Route | Type | Info |\n| --- | --- | --- |\n" + "".join([f"| [{' <span style=\"text-decoration:line-through; color:red; font-size:0.9em;\">' + l[0] + '</span>' if l[3] else l[0]}](../routes/{normalize_name(l[0].replace('<span style=\"text-decoration:line-through; color:red; font-size:0.9em;\">', '').replace('</span>', ''))}.md) | {l[1]} | {l[2]} |\n" for l in sorted(route_locations)]) + "\n" if route_locations else None)
    (md + "## Held by Wild Pokemon\n| Sprite | Pokemon |\n| --- | --- |\n" + "".join([f"| ![{normalize_name(p)}](../img/pokemon/{base_data['pokemon'][normalize_name(p)]['id']:03}.png) | [{get_display_name(p)}](../pokemon/{normalize_name(p)}.md) |\n" for p in sorted(pkmn_with_item) if normalize_name(p) in base_data['pokemon']]) if pkmn_with_item else None); return md

def generate_route_page(name, r_d, base_data, t_d, rom_item_changes):
    md = f"# {name}\n\n"; (md + "## Encounters\n" + "".join([f"### {sc['title']}\n" + "".join([f"#### ![{m.lower()}](../img/items/{('surf-special.png' if 'surf special' in m.lower() else ('fishing-special.png' if 'fish special' in m.lower() else ('cave-normal.png' if 'cave' in m.lower() else ('surf-normal.png' if 'surf' in m.lower() else ('fishing-normal.png' if 'fish' in m.lower() else ('sand-normal.png' if 'sand' in m.lower() else 'grass-normal.png'))))))}) {m}\n| Sprite | Pokemon | Rate |\n| --- | --- | --- |\n" + "".join([f"| ![{normalize_name(ec['pokemon'])}](../img/pokemon/{base_data['pokemon'][normalize_name(ec['pokemon'])]['id']:03}.png) | [{ec['pokemon']}](../pokemon/{normalize_name(ec['pokemon'])}.md) | {ec['rate']}% |\n" for ec in ecs]) + "\n" for m, ecs in {ec['method']: [e for e in sc['encounters'] if e['method'] == ec['method']] for ec in sc['encounters']}.items()]) for sc in r_d['sections']]) if r_d else None)
    (md + "## Special Encounters\n" + "".join([f"### [{spec['pokemon']}](../pokemon/{normalize_name(spec['pokemon'])}.md)\n| Sprite | Level | Location | Method | Rate |\n| --- | --- | --- | --- | --- |\n| ![{normalize_name(spec['pokemon'])}](../img/pokemon/{base_data['pokemon'][normalize_name(spec['pokemon'])]['id']:03}.png) | {spec['level']} | {spec['location']} | {spec['method'] if spec['method'] == 'Fixed' else '![' + spec['method'].lower() + '](../img/items/' + ('surf-special.png' if 'surf' in spec['method'].lower() else ('fishing-special.png' if 'fish' in spec['method'].lower() else ('cave-normal.png' if 'cave' in spec['method'].lower() else ('sand-normal.png' if 'sand' in spec['method'].lower() else 'grass-normal.png')))) + ') ' + spec['method']} | {spec['rate']} |\n\n" + (f"*{spec['description']}*\n\n" if spec['description'] else "") for spec in r_d['specials']]) if r_d and r_d.get('specials') else None)
    bil = json.load(open("scripts/data/base_item_locations.json", encoding="utf-8")).get("route_items", {}) if os.path.exists("scripts/data/base_item_locations.json") else {}; md += "## Items\n"; rbi, rli = bil.get(name, {}), rom_item_changes.get(name, {})
    for sub in sorted(set(list(rbi.keys()) + list(rli.keys()))):
        md += f"### {sub}\n| Item |\n| --- |\n"; srm, sbs = rli.get(sub, []), rbi.get(sub, []); pbi = set()
        for c in srm:
            on, o_n, il = c['old'], normalize_item_name(c['old']), get_item_display_linked(c['new'], base_data); fi = -1
            for i, b in enumerate(sbs):
                if i not in pbi and normalize_item_name(b['name']) == o_n and b['method'] != "Hidden": fi = i; break
            if fi == -1:
                for i, b in enumerate(sbs):
                    if i not in pbi and normalize_item_name(b['name']) == o_n: fi = i; break
            if fi != -1: pbi.add(fi); b = sbs[fi]; md += f"| {il} <span style='text-decoration:line-through; color:red; font-size:0.9em;'>{on}{' (' + b['detail'] + ')' if b.get('detail') else ''}</span> |\n"
            else: md += f"| {il} |\n"
        for i, b in enumerate(sbs):
            if i not in pbi: md += f"| {get_item_display_linked(b['name'], base_data)}{' (' + b['detail'] + ')' if b.get('detail') else ''} |\n"
        md += "\n"
    lt = t_d.get(name)
    if lt:
        md += "## Trainers\n"; gs = {t.get('group_header', ''): [tt for tt in lt if tt.get('group_header', '') == t.get('group_header', '')] for t in lt}
        for h, teams in gs.items():
            if h:
                md += f"### {h}\n"; (md + f"**Battle Type:** {teams[0]['battle_type']}  \n" if teams[0].get('battle_type') else None)
                if teams[0].get('reward'):
                    rw = teams[0]['reward']; tmm = re.search(r'(TM|HM)(\d+)', rw)
                    if tmm:
                        mn = next((mid for mid, mi in base_data['moves'].items() if mi.get('tm_num') == tmm.group(0)), "")
                        if mn: rw = rw.replace(tmm.group(0), f"[{tmm.group(0)}](../moves/{mn}.md)")
                    md += f"**Reward:** {rw}  \n"
                md += "\n"
            for team in teams:
                md += f"{'####' if h else '###'} {team['name']}\n| Sprite | Pokemon | Level | Ability | Item | Moves |\n| --- | --- | --- | --- | --- | --- |\n"; [md + f"| ![{p['name']}](../img/pokemon/{base_data['pokemon'][normalize_name(p['name'])]['id']:03}.png) | [{get_display_name(p['name'])}](../pokemon/{normalize_name(p['name'])}.md) | {p['level']} | {p['ability']} | {get_item_display_linked(p['item'], base_data) if p['item'] != '-' else '-'} | {', '.join(p['moves'])} |\n" for p in team['pokemon'] if normalize_name(p['name']) in base_data['pokemon']]; md += "\n"
    return md

if __name__ == "__main__":
    for d in ['docs/pokemon', 'docs/moves', 'docs/abilities', 'docs/routes', 'docs/items']: (shutil.rmtree(d) if os.path.exists(d) else None) or os.makedirs(d)
    base_data, rom = load_data(); base_data['pokemon']['basculin'] = base_data['pokemon'].get('basculin-red-striped', base_data['pokemon'].get('basculin')); priority_forms = ['-normal', '-male', '-plant', '-red-striped', '-land', '-altered', '-standard', '-ordinary', '-aria', '-incarnate', '-spring']; normalized_pkmn = {}
    for p in sorted(base_data['pokemon'].values(), key=lambda x: x['id']):
        if p['id'] > 649: continue
        nn = normalize_name(p['name'])
        if nn not in normalized_pkmn: normalized_pkmn[nn] = p
        else:
            for pf in priority_forms:
                if p['name'].endswith(pf): normalized_pkmn[nn] = p; break
                if normalized_pkmn[nn]['name'].endswith(pf): break
    base_data['pokemon'] = normalized_pkmn; ptg = sorted(base_data['pokemon'].values(), key=lambda x: x['id']); fab, fmv = {}, {}
    for p in ptg:
        pn = p['name']; pr = rom['pokemon_changes'].get(pn, {}); pa = [extract_specific_ability(a, pn) for a in [pr.get('abilities', {}).get('one'), pr.get('abilities', {}).get('two')] if a]; pa = pa if any(pa) else p['abilities']
        for ab in pa:
            an = CLEAN_ABILITIES.get(normalize_name(ab), normalize_name(ab)); (fab[an].append(pn) if an in fab else fab.update({an: [pn]}))
        lrn = set([m['name'] for m in p['moves']] + [rm['name'] for rm in rom['move_changes'].get(pn, []) if rm.get('name')])
        for rl in pr.get('tm_hm', []): [lrn.add(m[1]) for m in re.findall(r'(TM|HM)\d+\s*,?\s*([^,.\n]+)', rl)]
        for tl in pr.get('tutor', []): [lrn.add(m) for m in re.findall(r'([^,.\n]+)', tl)]
        for m in lrn:
            mn = normalize_name(m); (fmv[mn].append(pn) if mn in fmv else fmv.update({mn: [pn]}))
    locs = {}
    for rd in rom['wild_pokemon']:
        for sc in rd['sections']:
            for ec in sc['encounters']: pn = normalize_name(ec['pokemon']); (locs[pn].append({'route': rd['name'], 'method': ec['method'], 'rate': str(ec['rate'])}) if pn in locs else locs.update({pn: [{'route': rd['name'], 'method': ec['method'], 'rate': str(ec['rate'])}]}))
        if rd.get('specials'):
            for spec in rd['specials']: pn = normalize_name(spec['pokemon']); (locs[pn].append({'route': rd['name'], 'method': spec['method'] or "Fixed", 'rate': str(spec['rate']) or 'Fixed'}) if pn in locs else locs.update({pn: [{'route': rd['name'], 'method': spec['method'] or "Fixed", 'rate': str(spec['rate']) or 'Fixed'}]}))
    for p in ptg: write_if_changed(os.path.join("docs/pokemon", f"{normalize_name(p['name'])}.md"), generate_pokemon_page(p['name'], base_data, rom, base_data['moves'], base_data['abilities'], locs, base_data['pokemon']))
    idx_md = "# Pokemon\n\n"; [idx_md + f"## {gn}\n\n| No. | Sprite | Pokemon |\n| --- | --- | --- |\n" + "".join([f"| {p['id']:03} | ![{normalize_name(p['name'])}](../img/pokemon/{p['id']:03}.png) | [{get_display_name(p['name'])}]({normalize_name(p['name'])}.md) |\n" for p in ptg if s <= p['id'] <= e]) + "\n" for gn, s, e in [("Kanto", 1, 151), ("Johto", 152, 251), ("Hoenn", 252, 386), ("Sinnoh", 387, 493), ("Unova", 494, 649)]]; write_if_changed("docs/pokemon/index.md", idx_md)
    for mn, mi in sorted(base_data['moves'].items()): write_if_changed(os.path.join("docs/moves", f"{normalize_name(mn)}.md"), generate_move_page(mn, mi, fmv.get(normalize_name(mn), []), rom['move_stat_changes'].get(normalize_name(mn), {}), base_data))
    write_if_changed("docs/moves/index.md", "# Moves\n\n" + "".join([f"- [{m.replace('-', ' ').title()}]({normalize_name(m)}.md)\n" for m in sorted(base_data['moves'].keys())]))
    for an, ai in sorted(base_data['abilities'].items()): write_if_changed(os.path.join("docs/abilities", f"{CLEAN_ABILITIES.get(normalize_name(an), normalize_name(an))}.md"), generate_ability_page(an, ai, fab.get(CLEAN_ABILITIES.get(normalize_name(an), normalize_name(an)), []), base_data))
    write_if_changed("docs/abilities/index.md", "# Abilities\n\n" + "".join([f"- [{a.replace('-', ' ').title()}]({CLEAN_ABILITIES.get(normalize_name(a), normalize_name(a))}.md)\n" for a in sorted(base_data['abilities'].keys())]))
    al = rom['trainer_order']; [al.append(r['name']) for r in rom['wild_pokemon'] if r['name'] not in al]; [write_if_changed(os.path.join("docs/routes", f"{normalize_name(rn)}.md"), generate_route_page(rn, next((r for r in rom['wild_pokemon'] if r['name'] == rn), None), base_data, rom['trainers'], rom['item_changes'])) for rn in al]
    write_if_changed("docs/routes/index.md", "# Routes\n\n" + "".join([f"- [{rn}]({normalize_name(rn)}.md)\n" for rn in al]))
    irl, rmil = {}, {}
    for r_n, sas in rom['item_changes'].items():
        for s_n, chs in sas.items():
            for c in chs: on = normalize_item_name(c['old']); (rmil[on].append((r_n, s_n)) if on in rmil else rmil.update({on: [(r_n, s_n)]}))
    for r_n, sas in rom['item_changes'].items():
        for s_n, chs in sas.items():
            for c in chs: inorm = normalize_item_name(c['new']); (irl[inorm].append((r_n, s_n, "", False)) if inorm in irl else irl.update({inorm: [(r_n, s_n, "", False)]}))
    if "location_items_serebii" in base_data:
        for r_n, sas in base_data["location_items_serebii"].items():
            for s_n, its in sas.items():
                for it in its:
                    inorm = normalize_item_name(it["name"]); (irl[inorm].append((r_n, s_n, it.get("detail", ""), False)) if inorm in irl else irl.update({inorm: [(r_n, s_n, it.get("detail", ""), False)]}))
                    if inorm in rmil:
                        for idx, (remr, rems) in enumerate(rmil[inorm]):
                            if remr == r_n and (rems == s_n or rems == "General"): irl[inorm][-1] = (r_n, s_n, it.get("detail", ""), True); rmil[inorm].pop(idx); break
    ipl = {}
    for p_n, p_c in rom['pokemon_changes'].items():
        if p_c.get('items'):
            for i in p_c['items']: inorm = normalize_item_name(i); (ipl[inorm].append(p_n) if inorm in ipl else ipl.update({inorm: [p_n]}))
    cats = {}; [cats[ii.get('category', 'Misc')].append(inm) if ii.get('category', 'Misc') in cats else cats.update({ii.get('category', 'Misc'): [inm]}) for inm, ii in base_data.get('items', {}).items()]
    for inm, ii in base_data.get('items', {}).items(): write_if_changed(os.path.join("docs/items", f"{inm}.md"), generate_item_page(inm, ii, irl.get(inm, []), ipl.get(inm, []), base_data['moves'], base_data))
    itidx = "# Items\n\n"; [itidx + f"## {c}\n\n| Icon | Item | Description | Locations |\n| --- | --- | --- | --- |\n" + "".join([f"| ![{get_item_display_name(inm, base_data)}]({get_item_icon(get_item_display_name(inm, base_data), base_data['moves'])}) | [{get_item_display_name(inm, base_data)}]({inm}.md) | {base_data['items'][inm]['description']} | {', '.join([f'[{l[0]}](../routes/{normalize_name(l[0].replace(\"<span style=\'text-decoration:line-through; color:red; font-size:0.9em;\'>\", \"\").replace(\"</span>\", \"\"))}.md)' for l in irl.get(inm, []) if not l[3]])} |\n" for inm in sorted(cats[c])]) + "\n" for c in sorted(cats.keys())]; write_if_changed("docs/items/index.md", itidx)
    with open("mkdocs.yml", 'r', encoding='utf-8') as f: ls = f.readlines()
    nl, inav = [], False
    for l in ls:
        if l.startswith('nav:'):
            inav = True; nl.append('nav:\n  - Home: README.md\n  - Pokemon:\n    - pokemon/index.md\n'); [nl.append(f'    - {gn}:\n' + "".join([f"      - {get_display_name(p['name'])}: pokemon/{normalize_name(p['name'])}.md\n" for p in ptg if s <= p['id'] <= e])) for gn, s, e in [("Kanto", 1, 151), ("Johto", 152, 251), ("Hoenn", 252, 386), ("Sinnoh", 387, 493), ("Unova", 494, 649)]]; nl.append('  - Routes:\n    - routes/index.md\n'); [nl.append(f"    - {rn}: routes/{normalize_name(rn)}.md\n") for rn in al]; nl.append('  - Items:\n    - items/index.md\n'); [nl.append(f'    - {c}:\n' + "".join([f"      - {get_item_display_name(inm, base_data)}: items/{inm}.md\n" for inm in sorted(cats[c])])) for c in sorted(cats.keys())]; nl.append('  - Moves:\n    - moves/index.md\n'); [nl.append(f"    - {m.replace('-', ' ').title()}: moves/{normalize_name(m)}.md\n") for m in sorted(base_data['moves'].keys())]; nl.append('  - Abilities:\n    - abilities/index.md\n'); [nl.append(f"    - {a.replace('-', ' ').title()}: abilities/{CLEAN_ABILITIES.get(normalize_name(a), normalize_name(a))}.md\n") for a in sorted(base_data['abilities'].keys())]
        elif not inav: nl.append(l)
    with open("mkdocs.yml", 'w', encoding='utf-8') as f: f.writelines(nl)
    print("Generation complete.")
