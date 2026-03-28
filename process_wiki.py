import json
import re
import os
import glob

# Global data collection for support pages
all_abilities = {} # {name: [pokemon_ids]}
all_moves = {} # {name: [pokemon_ids]}
all_items = {} # {name: [locations]}
pokemon_locations = {} # {pid: [locations]}

def normalize_name(name):
    return re.sub(r'[^a-z0-9]', '', name.lower())

def clean_rtf(file_path):
    if not os.path.exists(file_path): return ""
    with open(file_path, 'r', errors='ignore') as f:
        content = f.read()
    content = re.sub(r'\{\\pict.*?\}', '', content, flags=re.DOTALL)
    content = re.sub(r'\\[a-z0-9]+', ' ', content)
    content = re.sub(r'\{|\}', ' ', content)
    content = re.sub(r'\s+', ' ', content)
    return content

def parse_item_changes(file_path):
    if not os.path.exists(file_path): return
    with open(file_path, 'r', errors='ignore') as f:
        content = f.read()
    sections = re.split(r'\n\n(?=[A-Z])', content)
    for section in sections:
        lines = section.strip().split('\n')
        if len(lines) < 3 or '---' not in lines[1]: continue
        location = lines[0].strip()
        for line in lines[2:]:
            if '->' in line:
                new_item = line.split('->')[-1].strip()
                new_item = re.sub(r'\s*\* \d+', '', new_item).strip()
                if new_item not in all_items: all_items[new_item] = []
                all_items[new_item].append(location)

def parse_pokemon_locations():
    route_files = glob.glob('routes/*/wild_encounters.md')
    for rf in route_files:
        location = os.path.basename(os.path.dirname(rf))
        with open(rf, 'r') as f:
            content = f.read()
        pokes = re.findall(r'\[[^\]]+\]\(#/pokemon/(\d+)\)', content)
        for pid in set(pokes):
            pid_int = int(pid)
            if pid_int not in pokemon_locations: pokemon_locations[pid_int] = []
            if location not in pokemon_locations[pid_int]:
                pokemon_locations[pid_int].append(location)

def parse_move_changes(text):
    pokemon_blocks = re.findall(r'#(\d{3}) ([^+#-]+?)(?=#\d{3}|$)', text)
    move_changes = {}
    for pid, name in pokemon_blocks:
        pid_int = int(pid)
        block_regex = rf'#{pid} {re.escape(name)}(.*?)(?=#\d{{3}}|$)'
        match = re.search(block_regex, text)
        if match:
            block_text = match.group(1)
            adds = re.findall(r'\+ Level (\d+) - ([^+-]+)', block_text)
            rems = re.findall(r'- Level (\d+) - ([^+-]+)', block_text)
            move_changes[pid_int] = {
                'adds': [(int(lvl), mv.strip()) for lvl, mv in adds],
                'rems': [(int(lvl), mv.strip()) for lvl, mv in rems]
            }
    return move_changes

def parse_stat_changes(text):
    pokemon_blocks = re.findall(r'#(\d{3}) ([^#]+?)(?=#\d{3}|$)', text)
    stat_changes = {}
    for pid, name in pokemon_blocks:
        pid_int = int(pid)
        block_regex = rf'#{pid} {re.escape(name)}(.*?)(?=#\d{{3}}|$)'
        match = re.search(block_regex, text)
        if match:
            block_text = match.group(1)
            stats = re.findall(r'(\w+): (\d+) \'?e0 (\d+)', block_text)
            types = re.search(r'Type: ([^A-Z]+)', block_text)
            abilities = re.findall(r'Ability (One|Two|Three): ([^A-Z]+)', block_text)
            stat_changes[pid_int] = {
                'stats': {s[0]: (s[1], s[2]) for s in stats},
                'type': types.group(1).strip() if types else None,
                'abilities': {a[0]: a[1].strip() for a in abilities},
                'item': re.search(r'Item: ([^(\n]+)', block_text)
            }
            if stat_changes[pid_int]['item']:
                stat_changes[pid_int]['item'] = stat_changes[pid_int]['item'].group(1).strip()
    return stat_changes

def load_base_data():
    with open('pokemon-data.json-master/pokedex.json', 'r') as f:
        return json.load(f)

def update_pokemon_page(pid, base_poke, move_deltas, stat_deltas):
    file_path = f'pokemon/{pid:03d}.md'
    if not os.path.exists(file_path): return
    with open(file_path, 'r') as f:
        content = f.read()
    
    # 1. Stats
    stat_table_pattern = r'(## Base Stats.*?\| Version \| HP \| Atk \| Def \| SAtk \| SDef \| Spd \| BST \|.*?\| ------- \| -- \| --- \| --- \| ---- \| ---- \| --- \| --- \|)'
    base_stats = base_poke['base']
    bst = sum(base_stats.values())
    base_row = f"| Base Game | {base_stats['HP']} | {base_stats['Attack']} | {base_stats['Defense']} | {base_stats['Sp. Attack']} | {base_stats['Sp. Defense']} | {base_stats['Speed']} | {bst} |"
    if base_row not in content:
        content = re.sub(stat_table_pattern, rf'\1\n{base_row}', content, flags=re.DOTALL)

    # 2. Abilities
    ability_table_pattern = r'(## Abilities.*?\| Version \| Ability             \|.*?\| ------- \| ------------------- \|)'
    base_abilities = [a[0] for a in base_poke['profile']['ability']]
    base_row_abs = f"| Base Game | {' / '.join(base_abilities)} |"
    if base_row_abs not in content:
        content = re.sub(ability_table_pattern, rf'\1\n{base_row_abs}', content, flags=re.DOTALL)

    rom_abilities_match = re.search(r'## Abilities.*?\| All\s+\| ([^|]+) \|', content, flags=re.DOTALL)
    if rom_abilities_match:
        abs_text = rom_abilities_match.group(1).strip()
        for ab in re.split(r' / | , ', abs_text):
            ab = ab.strip()
            if ab not in all_abilities: all_abilities[ab] = []
            if pid not in all_abilities[ab]: all_abilities[ab].append(pid)
            # Link ability
            content = content.replace(f' {ab} ', f' [{ab}](#/abilities/{normalize_name(ab)}) ')

    # 3. Moves
    if move_deltas:
        for lvl, mv in move_deltas['adds']:
            norm_mv = normalize_name(mv)
            # Find row with this move name normalized in the second column
            pattern = rf'(\| {lvl}[\s\(\)New]*\| ([^|]+)\s+\|)'
            matches = re.finditer(pattern, content)
            for match in matches:
                md_mv = match.group(2).strip()
                if normalize_name(md_mv) == norm_mv:
                    content = content.replace(match.group(1), f'| {lvl} (New) | {md_mv} |')
        if move_deltas['rems']:
            rem_section = "\n### Removed Moves (Base Game only)\n\n| Level | Name |\n| --- | --- |\n"
            for lvl, mv in move_deltas['rems']:
                rem_section += f"| {lvl} | {mv} |\n"
            if "### Removed Moves" not in content:
                content += rem_section

    # Collect and link moves
    # Only link in the Name column of tables
    def link_move(match):
        lvl = match.group(1)
        mv = match.group(2).strip()
        rest = match.group(3)
        if mv in ["Name", "---"] or normalize_name(mv) == "":
            return match.group(0)
        if '[' in mv: return match.group(0) # Already linked
        
        if mv not in all_moves: all_moves[mv] = []
        if pid not in all_moves[mv]: all_moves[mv].append(pid)
        
        return f"| {lvl} | [{mv}](#/moves/{normalize_name(mv)}) |{rest}"

    content = re.sub(r'(?m)^\|\s*([\d\(\) New]+)\s*\|\s*([^|]+)\s*\|(.*?)\n', link_move, content)
    content = re.sub(r'(?m)^\|\s*([HT]M\d+)\s*\|\s*([^|]+)\s*\|(.*?)\n', link_move, content)

    # 4. Item
    if stat_deltas and stat_deltas.get('item'):
        item = stat_deltas['item']
        if item not in all_items: all_items[item] = []
        # Add to pokemon page (if not there)
        if item not in content:
            content = content.replace('## Base Stats', f'## Held Item\n\n- [{item}](#/items/{normalize_name(item)})\n\n## Base Stats')

    # 5. Locations
    if pid in pokemon_locations:
        loc_section = "\n## Locations\n\n"
        for loc in sorted(set(pokemon_locations[pid])):
            loc_section += f"- [{loc}](routes/{loc.replace(' ', '%20')}/index.md)\n"
        if "## Locations" not in content:
            content += loc_section

    with open(file_path, 'w') as f:
        f.write(content)

def generate_support_pages():
    os.makedirs('abilities', exist_ok=True)
    for ab, pids in all_abilities.items():
        with open(f'abilities/{normalize_name(ab)}.md', 'w') as f:
            f.write(f"# Ability: {ab}\n\n## Pokemon with this ability\n\n")
            for pid in sorted(pids):
                f.write(f"- [#{pid:03d}](pokemon/{pid:03d}.md)\n")
    os.makedirs('moves', exist_ok=True)
    for mv, pids in all_moves.items():
        with open(f'moves/{normalize_name(mv)}.md', 'w') as f:
            f.write(f"# Move: {mv}\n\n## Pokemon that learn this move\n\n")
            for pid in sorted(pids):
                f.write(f"- [#{pid:03d}](pokemon/{pid:03d}.md)\n")
    os.makedirs('items', exist_ok=True)
    for item, locs in all_items.items():
        with open(f'items/{normalize_name(item)}.md', 'w') as f:
            f.write(f"# Item: {item}\n\n## Locations\n\n")
            for loc in sorted(set(locs)):
                f.write(f"- [{loc}](routes/{loc.replace(' ', '%20')}/index.md)\n")

def consolidate_routes():
    route_dirs = glob.glob('routes/*')
    for rd in route_dirs:
        if not os.path.isdir(rd): continue
        index_content = f"# {os.path.basename(rd)}\n\n"
        
        # Add Wild Encounters
        we_path = os.path.join(rd, 'wild_encounters.md')
        if os.path.exists(we_path):
            with open(we_path, 'r') as f:
                we_content = f.read()
            # Remove title if present
            we_content = re.sub(r'^# .*\n', '', we_content)
            index_content += "## Wild Encounters\n\n" + we_content + "\n"
        
        # Add Trainers
        tr_path = os.path.join(rd, 'trainers.md')
        if os.path.exists(tr_path):
            with open(tr_path, 'r') as f:
                tr_content = f.read()
            tr_content = re.sub(r'^# .*\n', '', tr_content)
            index_content += "## Trainers\n\n" + tr_content + "\n"
            
        with open(os.path.join(rd, 'index.md'), 'w') as f:
            f.write(index_content)

def generate_gen_pages(base_data):
    gens = {
        1: (1, 151),
        2: (152, 251),
        3: (252, 386),
        4: (387, 493),
        5: (494, 649)
    }
    for gen, (start, end) in gens.items():
        with open(f'pokemon/gen{gen}.md', 'w') as f:
            f.write(f"# Generation {gen}\n\n")
            for pid in range(start, end + 1):
                if pid in base_data:
                    name = base_data[pid]['name']['english']
                    f.write(f"- [#{pid:03d} - {name}](#/pokemon/{pid:03d}.md)\n")

if __name__ == "__main__":
    print("Loading base data...")
    base_data = {p['id']: p for p in load_base_data()}
    print("Parsing files...")
    move_text = clean_rtf("Documentation/Level Up Move Changes.rtf")
    stat_text = clean_rtf("Documentation/Pokemon Changes.rtf")
    parse_item_changes("Documentation/Item & Trade Changes.txt")
    parse_pokemon_locations()
    move_changes = parse_move_changes(move_text)
    stat_changes = parse_stat_changes(stat_text)
    print("Updating Pokemon pages...")
    for pid in range(1, 650):
        if pid in base_data:
            update_pokemon_page(pid, base_data[pid], move_changes.get(pid), stat_changes.get(pid))
    print("Generating support pages...")
    generate_support_pages()
    print("Consolidating routes...")
    consolidate_routes()
    print("Generating generation pages...")
    generate_gen_pages(base_data)
    print("Done!")
