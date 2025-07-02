import os
import shutil
import json
import re

PRESET_MAP_PATH = os.path.join(os.path.dirname(os.path.realpath(__file__)), '../../data/preset_map.json')

# Helper to count oscillators in a Vital preset file
# Assumes .vital is a JSON (if not, will skip file)
def count_oscillators(vital_path):
    try:
        with open(vital_path, 'r') as f:
            data = json.load(f)
        # Check for Vital's oscillator keys, if value = 1.0
        osc_keys = ['osc_1_on', 'osc_2_on', 'osc_3_on']
        count = 0
        settings = data.get("settings", {})
        for k in osc_keys:
            if k in settings and settings[k] == 1.0:
                count += 1
                #print(f"Found oscillator: {k}, count: {count}")
        return count if count > 0 else 1
    except Exception as e:
        print(f"Could not parse {vital_path}: {e}")
        return None

def import_vital_presets_flat(src_dir, dest_dir, map_path=PRESET_MAP_PATH):
    """
    Recursively copy all .vital files from src_dir to syntheon/data/vital_presets/has_x_osc.
    While copying, use the idx-cleaned_name from the preset map for filenames.
    """
    # Load the preset map
    if os.path.exists(map_path):
        with open(map_path, 'r') as f:
            preset_map = json.load(f)
    else:
        print(f"Preset map not found at {map_path}. Run build_and_save_preset_map first.")
        return

    count = 0
    for idx, entry in preset_map.items():
        src_file = entry['full_path']
        cleaned_name = entry['cleaned_name']
        # Count oscillators
        osc_count = count_oscillators(src_file)
        if osc_count is None:
            print(f"Skipping {src_file} (could not determine oscillator count)")
            continue
        if osc_count == 1:
            osc_folder = 'has_1_osc'
        elif osc_count == 2:
            osc_folder = 'has_2_osc'
        elif osc_count == 3:
            osc_folder = 'has_3_osc'
        else:
            osc_folder = f'has_{osc_count}_osc'
        dest_subdir = os.path.join(dest_dir, osc_folder)
        os.makedirs(dest_subdir, exist_ok=True)
        dest_file = os.path.join(dest_subdir, cleaned_name)
        # If the string-transformed filename is already present, skip copying
        if os.path.exists(dest_file):
            print(f"Skipping {src_file} (already exists as {dest_file})")
            continue
        shutil.copy2(src_file, dest_file)
        print(f"Copied: {src_file} -> {dest_file}")
        count += 1
    print(f"Total .vital files copied: {count}")


def clean_name(filename):
    # Remove spaces, replace with '-', lowercase, and remove trailing '-' and '.'
    name = filename.replace(' ', '-').lower()
    # Remove all trailing '-' and '.'
    name = name.rstrip('-.')
    return name

def build_and_save_preset_map(src_dir, map_path=PRESET_MAP_PATH):
    """
    Scans the vital presets in src_dir, checks if they are present in the map, and if not, adds them to the end of the existing map and renames the preset. Existing entries are preserved as-is. Only new presets are renamed and added at the end. The map is not rebuilt every time.
    """
    # Load existing map if it exists
    if os.path.exists(map_path):
        with open(map_path, 'r') as f:
            preset_map = json.load(f)
    else:
        preset_map = {}

    # Build a reverse lookup: original filename (without idx prefix) -> idx
    filename_to_idx = {}
    for idx, entry in preset_map.items():
        actual_name = entry['actual_name']
        match = re.match(r"(\d+)-(.*)", actual_name)
        if match:
            orig_filename = match.group(2)
        else:
            orig_filename = actual_name
        filename_to_idx[orig_filename] = idx

    # Find the max idx used
    max_idx = max([int(idx) for idx in preset_map.keys()] or [0])
    updated = False
    # Scan files
    for root, dirs, files in os.walk(src_dir):
        for file in files:
            if file.endswith('.vital'):
                # Remove idx prefix if present
                match = re.match(r"(\d+)-(.*)", file)
                if match:
                    orig_filename = match.group(2)
                else:
                    orig_filename = file
                cleaned = clean_name(orig_filename)
                # Only add if not already in map
                if orig_filename not in filename_to_idx:
                    max_idx += 1
                    idx = str(max_idx)
                    actual_name_with_idx = f"{idx}-{orig_filename}"
                    cleaned_with_idx = f"{idx}-{cleaned}"
                    old_full_path = os.path.join(root, file)
                    new_full_path = os.path.join(root, actual_name_with_idx)
                    # Rename the file if not already renamed
                    if file != actual_name_with_idx:
                        try:
                            os.rename(old_full_path, new_full_path)
                            print(f"Renamed {old_full_path} -> {new_full_path}")
                        except Exception as e:
                            print(f"Could not rename {old_full_path} to {new_full_path}: {e}")
                    else:
                        new_full_path = old_full_path
                    # Try to extract preset_style from the .vital file (assumed JSON)
                    preset_style = ""
                    try:
                        with open(new_full_path, 'r') as f:
                            data = json.load(f)
                            if isinstance(data, dict):
                                preset_style = data.get('preset_style', "")
                    except Exception as e:
                        print(f"Could not read preset_style from {new_full_path}: {e}")
                    preset_map[idx] = {
                        'actual_name': actual_name_with_idx,
                        'cleaned_name': cleaned_with_idx,
                        'full_path': new_full_path,
                        'preset_style': preset_style
                    }
                    updated = True
    # Save updated map only if changed
    if updated:
        with open(map_path, 'w') as f:
            json.dump(preset_map, f, indent=2)
        print(f"Preset map updated with {len(preset_map)} entries saved to {map_path}")
    else:
        print(f"No new presets found. Preset map unchanged.")
    return preset_map

def select_preset_from_map(map_path=PRESET_MAP_PATH):
    """
    Load the preset map and prompt the user to select a preset by number.
    Returns (actual_name, cleaned_name, full_path) for the selected preset.
    """
    with open(map_path, 'r') as f:
        preset_map = json.load(f)
    print("Available Vital presets:")
    for num, entry in preset_map.items():
        print(f"{num}: {entry['actual_name']} (cleaned: {entry['cleaned_name']})")
    selected = input("Enter the number of the preset to use: ").strip()
    if selected in preset_map:
        entry = preset_map[selected]
        print(f"Selected: {entry['actual_name']} (cleaned: {entry['cleaned_name']})")
        return entry['actual_name'], entry['cleaned_name'], entry['full_path']
    else:
        print("Invalid selection.")
        return None, None, None

def check_unrendered_presets(map_path=PRESET_MAP_PATH, render_dir=None, output_path=None):
    """
    Checks which presets in the preset map have not been rendered yet (i.e., do not have a corresponding directory in data/vital_preset_audio).
    Stores the list of remaining preset ids in preset_render_remaining_map.json, categorized by oscillator count and preset style.
    Also checks that rendered + remaining = total presets in the map.
    """
    if render_dir is None:
        script_dir = os.path.dirname(os.path.realpath(__file__))
        project_root = os.path.abspath(os.path.join(script_dir, '../../..'))
        render_dir = os.path.join(project_root, 'syntheon', 'data', 'vital_preset_audio')
    if output_path is None:
        output_path = os.path.join(os.path.dirname(map_path), 'preset_render_remaining_map.json')

    # Load preset map
    with open(map_path, 'r') as f:
        preset_map = json.load(f)
    all_ids = set(preset_map.keys())

    # Get all rendered preset directories (assume each subdir in render_dir is a rendered preset)
    if os.path.exists(render_dir):
        rendered_dirs = set(os.listdir(render_dir))
    else:
        rendered_dirs = set()

    # Find which ids have been rendered (by matching preset_name or idx)
    rendered_ids = set()
    for idx, entry in preset_map.items():
        cleaned_name = entry.get('cleaned_name', '')
        actual_name = entry.get('actual_name', '')
        if cleaned_name in rendered_dirs or actual_name in rendered_dirs or idx in rendered_dirs:
            rendered_ids.add(idx)
        else:
            for d in rendered_dirs:
                if d.startswith(f"{idx}-"):
                    rendered_ids.add(idx)
                    break
    remaining_ids = sorted(list(all_ids - rendered_ids), key=lambda x: int(x))

    # Categorize remaining by osc count and preset style
    categorized = {}
    for idx in remaining_ids:
        entry = preset_map[idx]
        src_file = entry['full_path']
        osc_count = count_oscillators(src_file)
        if osc_count is None:
            osc_key = 'unknown_osc'
        else:
            osc_key = f'has_{osc_count}_osc'
        # Normalize style: lowercase, strip, use 'unknown_style' if empty
        preset_style = entry.get('preset_style', '')
        preset_style = preset_style.strip().lower() if preset_style.strip() else 'unknown_style'
        if osc_key not in categorized:
            categorized[osc_key] = {}
        if preset_style not in categorized[osc_key]:
            categorized[osc_key][preset_style] = []
        categorized[osc_key][preset_style].append(idx)

    # Count total unrendered
    total_unrendered = sum(len(ids) for osc in categorized.values() for ids in osc.values())
    total_rendered = len(all_ids) - total_unrendered
    summary = {
        'total_unrendered': total_unrendered,
        'total_rendered': total_rendered,
        'total_presets': len(all_ids)
    }
    # Add summary as a key in the main output JSON
    categorized['_summary'] = summary
    with open(output_path, 'w') as f:
        json.dump(categorized, f, indent=2)
    print(f"Wrote categorized unrendered preset ids and summary to {output_path}")

    # Consistency check
    total = len(all_ids)
    done = len(rendered_ids)
    remaining = len(remaining_ids)
    print(f"Total presets: {total}, Rendered: {done}, Remaining: {remaining}")
    if done + remaining != total:
        print("WARNING: Rendered + Remaining does not equal total presets! Check for naming mismatches or orphaned directories.")

if __name__ == "__main__":
    source_vital_dir = "/Users/sayantanm/Music/Vital"  
    script_dir = os.path.dirname(os.path.realpath(__file__))
    project_root = os.path.abspath(os.path.join(script_dir, '../../..'))
    dest_dir = os.path.join(project_root, 'syntheon', 'data', 'vital_presets')

    # Call build_and_save_preset_map to update the map if new entries are found
    build_and_save_preset_map(source_vital_dir, PRESET_MAP_PATH)

    # Continue with your import/copy logic as needed
    import_vital_presets_flat(source_vital_dir, dest_dir, PRESET_MAP_PATH)

    # Check which presets have not been rendered yet and write remaining IDs to file
    check_unrendered_presets(PRESET_MAP_PATH)