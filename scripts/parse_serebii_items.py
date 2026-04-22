import json
import os
import re

def normalize_location(loc):
    # Remove extra detail in parentheses for the mapping key, but keep it for display
    clean_loc = re.sub(r'\(.*?\)', '', loc).split(' - ')[0].split(' – ')[0].strip()
    
    mapping = {
        "Freezer Container": "Cold Storage",
        "P2 Laboratory": "P2 Laboratory",
        "Liberty Tower Basement": "Liberty Garden",
        "Pokemon League": "Pokémon League",
        "Pokémon League": "Pokémon League",
        "PokeMart": "PokéMart",
        "Department Store": "Route 9",
        "Musical Hall": "Nimbasa City",
        "Dreamyard": "Dreamyard",
        "Pinwheel Forest": "Pinwheel Forest",
        "Desert Resort": "Desert Resort",
        "Relic Castle": "Relic Castle",
        "Wellspring Cave": "Wellspring Cave",
        "Chargestone Cave": "Chargestone Cave",
        "Mistralton Cave": "Mistralton Cave",
        "Celestial Tower": "Celestial Tower",
        "Twist Mountain": "Twist Mountain",
        "Dragonspiral Tower": "Dragonspiral Tower",
        "Victory Road": "Victory Road",
        "Giant Chasm": "Giant Chasm",
        "Abundant Shrine": "Abundant Shrine",
        "Challenger's Cave": "Challenger's Cave",
        "Village Bridge": "Village Bridge",
        "Tubeline Bridge": "Tubeline Bridge",
        "Marvelous Bridge": "Marvelous Bridge",
        "Skyarrow Bridge": "Skyarrow Bridge",
        "Driftveil Drawbridge": "Driftveil Drawbridge",
    }
    
    for k, v in mapping.items():
        if k.lower() in clean_loc.lower():
            return v
            
    # Handle Route X
    m = re.search(r'Route\s+(\d+)', clean_loc, re.IGNORECASE)
    if m:
        return f"Route {m.group(1)}"
        
    return clean_loc

def fix_item_name(name):
    if not name: return ""
    name = name.strip()
    # Fix BalmMushroom -> Balm Mushroom, BlackGlasses -> Black Glasses etc
    # Matches lowercase followed by uppercase
    name = re.sub(r'([a-z])([A-Z])', r'\1 \2', name)
    return name

def parse_items_csv():
    with open("Documentation/items.csv", "r", encoding="utf-8") as f:
        content = f.read()
    
    items = {} # name -> {description, category, locations: {area: [{method, detail}]}, shops: [locations]}
    
    # Split by section headers (e.g. "Recovery Items")
    sections = re.split(r'\n(?=[A-Z][\w\s/&]+ Items)', content)
    for section in sections:
        lines = section.strip().split('\n')
        if not lines: continue
        
        category = "Misc"
        # Find category from the first line or a known header
        for line in lines:
            cat_match = re.match(r'([A-Z][\w\s/&]+) Items', line)
            if cat_match:
                category = cat_match.group(1).strip()
                break
        
        # Special case for TM header which might not say "Items"
        if "Technical Machine" in lines[0]: category = "Technical Machines"

        for i in range(len(lines)):
            l = lines[i]
            if not l.startswith('\t'): continue
            
            parts = l.split('\t')
            if len(parts) < 2: continue
            
            name = fix_item_name(parts[1].strip())
            effect = parts[2].strip() if len(parts) > 2 else ""
            loc_str = parts[3].strip() if len(parts) > 3 else ""
            
            if name not in items:
                items[name] = {"description": effect, "category": category, "locations": {}, "shops": []}
            
            # Handle locations
            shop_mode = False
            if loc_str:
                if loc_str.strip() == "Shop":
                    shop_mode = True
                else:
                    for loc in loc_str.split(', '):
                        method = "Ground"
                        detail = ""
                        
                        if "(With Dowsing Machine)" in loc:
                            method = "Hidden"
                            detail = "With Dowsing Machine"
                            loc = loc.replace("(With Dowsing Machine)", "").strip()
                        elif "Gift" in loc:
                            method = "NPC"
                        
                        # Capture parenthetical detail if it exists
                        det_match = re.search(r'\((.*?)\)', loc)
                        if det_match:
                            detail = det_match.group(1)
                        
                        norm_loc = normalize_location(loc)
                        if norm_loc not in items[name]["locations"]:
                            items[name]["locations"][norm_loc] = []
                        
                        items[name]["locations"][norm_loc].append({"method": method, "detail": detail})
            
            # Peek at next line for "Shop" or shop locations
            j = i + 1
            while j < len(lines):
                next_l = lines[j].strip()
                if not next_l: 
                    j += 1
                    continue
                if next_l.startswith('\t'): break
                
                if next_l == "Shop":
                    shop_mode = True
                    j += 1
                    continue
                
                if shop_mode:
                    # This line should be shop locations
                    shop_locs = next_l.split(', ')
                    for sl in shop_locs:
                        norm_sl = normalize_location(sl)
                        if norm_sl not in items[name]["shops"]:
                            items[name]["shops"].append(norm_sl)
                    shop_mode = False # Assume one line of shop locs for now
                    j += 1
                else:
                    # If not in shop mode and doesn't start with \t, might be a continuation of locations?
                    # Serebii items.csv seems to have shop locations on the next line often.
                    j += 1
    return items

def parse_tmhm_csv():
    with open("Documentation/tmhm.csv", "r", encoding="utf-8") as f:
        lines = f.readlines()
    
    tmhm = {}
    for l in lines:
        parts = l.strip().split('\t')
        if len(parts) < 9 or not parts[0].startswith(('TM', 'HM')): continue
        
        num = parts[0]
        move_name = parts[1]
        name = f"{num} {move_name}"
        effect = parts[7]
        loc_str = parts[8]
        
        tmhm[name] = {"description": effect, "category": "Technical Machines" if num.startswith('TM') else "Hidden Machines", "locations": {}, "shops": []}
        
        loc_parts = re.split(r' - | – ', loc_str)
        loc_name = loc_parts[0].strip()
        method = "Ground"
        detail = loc_parts[1].strip() if len(loc_parts) > 1 else ""
        
        if detail:
            low_detail = detail.lower()
            if any(x in low_detail for x in ["gift", "professor", "mokomo", "from", "reward", "after"]):
                method = "NPC"
            elif any(x in low_detail for x in ["mart", "bp", "department", "dollars"]):
                method = "Shop"
        
        norm_loc = normalize_location(loc_name)
        if method == "Shop":
            tmhm[name]["shops"].append(norm_loc)
        else:
            if norm_loc not in tmhm[name]["locations"]:
                tmhm[name]["locations"][norm_loc] = []
            tmhm[name]["locations"][norm_loc].append({"method": method, "detail": detail})
            
    return tmhm

if __name__ == "__main__":
    items = parse_items_csv()
    tmhm = parse_tmhm_csv()
    
    all_items = {**items, **tmhm}
    
    route_items = {}
    for name, data in all_items.items():
        for loc, info_list in data["locations"].items():
            if loc not in route_items: route_items[loc] = {}
            area = "General"
            if area not in route_items[loc]: route_items[loc][area] = []
            for info in info_list:
                route_items[loc][area].append({"name": name, "method": info["method"], "detail": info["detail"]})
        
        for loc in data["shops"]:
            if loc not in route_items: route_items[loc] = {}
            area = "Shop"
            if area not in route_items[loc]: route_items[loc][area] = []
            route_items[loc][area].append({"name": name, "method": "Shop", "detail": ""})

    with open("scripts/data/base_item_locations.json", "w", encoding="utf-8") as f:
        json.dump({"items": all_items, "route_items": route_items}, f, indent=2)
    print("Parsing complete.")
